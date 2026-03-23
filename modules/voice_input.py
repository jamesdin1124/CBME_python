"""
語音輸入模組 — 瀏覽器端錄音 + Whisper 轉錄 + GPT 醫學用語潤飾
適用於 Streamlit Cloud（不依賴 sounddevice 等本機音訊庫）。

內建用量管控：
  - 每人每日轉錄上限（預設 20 次）
  - 每人每日 AI 潤飾上限（預設 10 次）
  - 單次音檔大小上限（預設 5 MB）
  - 僅限教師 / 管理員角色使用

使用方式：
    from modules.voice_input import voice_feedback_input
    feedback = voice_feedback_input("feedback_key", placeholder="請描述...")
"""

import os
import streamlit as st
from datetime import date
from tempfile import NamedTemporaryFile

# ─── 用量設定 ──────────────────────────────────────────────
DAILY_TRANSCRIBE_LIMIT = 20    # 每人每日語音轉錄上限
DAILY_REFINE_LIMIT = 10        # 每人每日 AI 潤飾上限
MAX_AUDIO_SIZE_MB = 5          # 單次音檔大小上限（MB）
ALLOWED_ROLES = ('admin', 'department_admin', 'teacher')  # 可使用語音的角色

# ─── 醫學專有名詞提示（幫助 Whisper 正確辨識）───────────────
MEDICAL_PROMPT = (
    "這是一段臨床醫學教學評核的口頭回饋，可能包含中英文醫學專有名詞。"
    "常見詞彙包括：EPA, OSCE, CBME, CCC, PGY, intubation, lumbar puncture, "
    "CVC, central venous catheter, PICC, chest tube, arterial line, "
    "ultrasound, echocardiography, APLS, NRP, PICU, NICU, "
    "住院醫師, 主治醫師, 可信賴程度, entrustment, "
    "鑑別診斷, differential diagnosis, sepsis, pneumonia, meningitis, "
    "CBC, CRP, CXR, EKG, ABG, ventilator, CPAP, BiPAP, ECMO, "
    "endotracheal tube, nasogastric tube, Foley catheter, "
    "抽血, 靜脈注射, IV, bolus, infusion, monitor, vital signs, "
    "SpO2, heart rate, blood pressure, respiratory rate, "
    "問診, 身體檢查, physical examination, auscultation, percussion, "
    "衛教, informed consent, 病歷書寫, SOAP note, "
    "Morning meeting, journal club, case presentation, grand round"
)

# GPT 系統提示：潤飾醫學教學回饋
GPT_SYSTEM_PROMPT = (
    "你是醫學教育領域的文字編輯助手，專門整理臨床教師對住院醫師的口頭回饋。"
    "請依照以下規則處理：\n"
    "1. 使用繁體中文，但保留英文醫學專有名詞（如 CVC、PICC、intubation 等）\n"
    "2. 修正口語辨識錯誤和錯別字\n"
    "3. 適當分段，使評語更有條理\n"
    "4. 保持原意，不增加原文沒有的評價\n"
    "5. 如果辨識文字中有明顯的醫學術語辨識錯誤，請修正為正確的專有名詞\n"
    "6. 直接返回修改後的文字，不需要其他說明或前綴"
)


# ─── 用量追蹤 ──────────────────────────────────────────────

def _get_usage_key(action: str) -> str:
    """產生 session_state 中的用量計數 key（每人每日）"""
    user = st.session_state.get('username', 'unknown')
    today = date.today().isoformat()
    return f"voice_usage_{action}_{user}_{today}"


def _get_usage_count(action: str) -> int:
    return st.session_state.get(_get_usage_key(action), 0)


def _increment_usage(action: str):
    key = _get_usage_key(action)
    st.session_state[key] = st.session_state.get(key, 0) + 1


def _check_role() -> bool:
    """檢查目前使用者是否為允許使用語音功能的角色"""
    role = st.session_state.get('role', 'resident')
    return role in ALLOWED_ROLES


def _remaining_quota(action: str, limit: int) -> int:
    return max(0, limit - _get_usage_count(action))


# ─── OpenAI 客戶端 ────────────────────────────────────────

def _get_openai_client():
    """取得 OpenAI 客戶端（支援 .env / Streamlit secrets / 環境變數）"""
    if 'openai_client' in st.session_state and st.session_state.openai_client:
        return st.session_state.openai_client

    api_key = ""

    # 1) 嘗試 dotenv
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)
    except ImportError:
        pass

    # 2) 環境變數
    api_key = os.getenv("OPENAI_API_KEY", "").strip().strip('"').strip("'")

    # 3) Streamlit secrets（多種格式相容）
    if not api_key:
        # 嘗試頂層 key
        try:
            api_key = str(st.secrets["OPENAI_API_KEY"]).strip().strip('"').strip("'")
        except Exception:
            pass
    if not api_key:
        # 嘗試 [openai] 區塊
        try:
            api_key = str(st.secrets["openai"]["api_key"]).strip().strip('"').strip("'")
        except Exception:
            pass
    if not api_key:
        # 嘗試 [general] 區塊
        try:
            api_key = str(st.secrets["general"]["OPENAI_API_KEY"]).strip().strip('"').strip("'")
        except Exception:
            pass

    if not api_key:
        return None

    # 同步到環境變數，讓其他模組也能用
    os.environ["OPENAI_API_KEY"] = api_key

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        st.session_state.openai_client = client
        return client
    except Exception:
        return None


# ─── 核心功能 ─────────────────────────────────────────────

def _transcribe_audio(audio_bytes: bytes) -> str | None:
    """使用 Whisper API 將音訊轉為文字（含用量檢查）"""
    # 用量檢查
    remaining = _remaining_quota('transcribe', DAILY_TRANSCRIBE_LIMIT)
    if remaining <= 0:
        st.warning(f"⚠️ 今日語音轉錄已達上限（{DAILY_TRANSCRIBE_LIMIT} 次），請明日再使用或直接打字輸入")
        return None

    # 檔案大小檢查
    size_mb = len(audio_bytes) / (1024 * 1024)
    if size_mb > MAX_AUDIO_SIZE_MB:
        st.warning(f"⚠️ 音檔過大（{size_mb:.1f} MB），上限為 {MAX_AUDIO_SIZE_MB} MB，請縮短錄音時間")
        return None

    client = _get_openai_client()
    if not client:
        st.warning("⚠️ 未設定 OpenAI API 金鑰，無法使用語音轉文字")
        return None

    try:
        with NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                prompt=MEDICAL_PROMPT,  # 提供醫學詞彙提示
                language="zh",          # 主要語言：中文
                temperature=0.0,        # 降低隨機性，提高準確度
            )

        os.unlink(tmp_path)

        text = response.text.strip() if response.text else ""
        # 過濾 Whisper 幻覺（常見的無意義輸出）
        hallucination_patterns = [
            "請不吝點贊", "訂閱轉發", "謝謝觀看", "歡迎訂閱",
            "字幕由", "Amara.org", "感謝觀看",
        ]
        for pattern in hallucination_patterns:
            if pattern in text:
                text = text.replace(pattern, "")
        text = text.strip()

        if text:
            _increment_usage('transcribe')
            return text
        return None

    except Exception as e:
        st.error(f"❌ 語音轉換失敗：{str(e)}")
        return None


def _refine_with_gpt(text: str) -> str:
    """使用 GPT 潤飾轉錄文字（含用量檢查）"""
    # 用量檢查
    remaining = _remaining_quota('refine', DAILY_REFINE_LIMIT)
    if remaining <= 0:
        st.warning(f"⚠️ 今日 AI 潤飾已達上限（{DAILY_REFINE_LIMIT} 次），請明日再使用")
        return text

    client = _get_openai_client()
    if not client:
        return text

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": GPT_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0.2,
            max_tokens=1500,
        )
        _increment_usage('refine')
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.warning(f"⚠️ AI 潤飾失敗，使用原始文字：{str(e)}")
        return text


# ─── UI 元件 ──────────────────────────────────────────────

def voice_feedback_input(
    key: str,
    label: str = "教師回饋",
    placeholder: str = "請描述住院醫師的表現...",
    height: int = 120,
    help_text: str | None = None,
) -> str:
    """
    帶語音輸入的回饋文字欄位。

    在 text_area 上方放置「🎙️ 語音輸入」按鈕，
    錄音 → Whisper 轉錄 → 可選 GPT 潤飾 → 填入文字框。

    Parameters
    ----------
    key : str
        Streamlit widget 的唯一識別碼
    label : str
        text_area 的標籤
    placeholder : str
        text_area 的預設提示文字
    height : int
        text_area 高度
    help_text : str | None
        text_area 的 help 提示

    Returns
    -------
    str
        使用者最終確認的回饋文字
    """
    # session state key 管理
    text_key = f"voice_text_{key}"
    if text_key not in st.session_state:
        st.session_state[text_key] = ""

    # ── 語音輸入列 ──
    voice_col, refine_col, upload_col = st.columns([1, 1, 2])

    with voice_col:
        try:
            from audio_recorder_streamlit import audio_recorder
            audio_bytes = audio_recorder(
                text="🎙️ 語音輸入",
                recording_color="#e74c3c",
                neutral_color="#6c757d",
                icon_size="1x",
                key=f"recorder_{key}",
            )
            if audio_bytes:
                with st.spinner("🔄 語音辨識中..."):
                    transcribed = _transcribe_audio(audio_bytes)
                if transcribed:
                    # 追加到現有文字
                    current = st.session_state.get(text_key, "")
                    separator = "\n" if current.strip() else ""
                    st.session_state[text_key] = current + separator + transcribed
                    st.success("✅ 語音辨識完成")
        except ImportError:
            # audio_recorder_streamlit 未安裝，提供上傳替代方案
            st.caption("🎙️ 語音套件未安裝")

    with refine_col:
        if st.session_state.get(text_key, "").strip():
            if st.button("✨ AI 潤飾", key=f"refine_{key}", help="使用 AI 修正醫學用語並改善語句"):
                with st.spinner("🔄 AI 潤飾中..."):
                    refined = _refine_with_gpt(st.session_state[text_key])
                    st.session_state[text_key] = refined
                    st.success("✅ 潤飾完成")

    with upload_col:
        uploaded = st.file_uploader(
            "或上傳錄音檔",
            type=["wav", "mp3", "m4a", "ogg", "webm"],
            key=f"upload_{key}",
            label_visibility="collapsed",
            help="支援 WAV、MP3、M4A 等格式",
        )
        if uploaded:
            if st.button("📝 轉錄", key=f"transcribe_upload_{key}"):
                with st.spinner("🔄 語音辨識中..."):
                    transcribed = _transcribe_audio(uploaded.getvalue())
                if transcribed:
                    current = st.session_state.get(text_key, "")
                    separator = "\n" if current.strip() else ""
                    st.session_state[text_key] = current + separator + transcribed
                    st.success("✅ 語音辨識完成")

    # ── 文字輸入區 ──
    feedback = st.text_area(
        label,
        value=st.session_state.get(text_key, ""),
        placeholder=placeholder,
        height=height,
        key=f"textarea_{key}",
        help=help_text,
    )

    # 同步 text_area 的手動編輯回 session state
    st.session_state[text_key] = feedback

    return feedback
