import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, date
from modules.google_connection import fetch_google_form_data, setup_google_connection
import gspread
from google.oauth2.service_account import Credentials
import re

# ─── Supabase 整合（可選，無 .env 設定時自動回退到 Google Sheets）───
_supabase_conn = None

def _get_supabase_conn():
    """取得全域 Supabase 連線（懶載入，失敗回傳 None）"""
    global _supabase_conn
    if _supabase_conn is not None:
        return _supabase_conn
    try:
        from modules.supabase_connection import SupabaseConnection
        _supabase_conn = SupabaseConnection()
        return _supabase_conn
    except Exception:
        return None


def load_threshold_settings():
    """已棄用：門檻改為依年級分級（LEVEL_THRESHOLDS），保留函式以向後相容。"""
    return LEVEL_THRESHOLDS

# 小兒部住院醫師評核表單欄位對應
PEDIATRIC_FORM_FIELDS = {
    '時間戳記': 'timestamp',
    '評核教師': 'evaluator_teacher', 
    '評核日期': 'evaluation_date',
    '受評核人員': 'evaluated_person',
    '評核時級職': 'evaluation_level',
    '評核項目': 'evaluation_item',
    '會議名稱': 'meeting_name',
    '內容是否充分': 'content_sufficient',
    '辯證資料的能力': 'data_analysis_ability',
    '口條、呈現方式是否清晰': 'presentation_clarity',
    '是否具開創、建設性的想法': 'innovative_ideas',
    '回答提問是否具邏輯、有條有理': 'logical_response',
    '會議報告教師回饋': 'teacher_feedback',
    '病歷號': 'patient_id',
    '評核技術項目': 'technical_evaluation_item',
    '鎮靜藥物': 'sedation_medication',
    '可信賴程度': 'reliability_level',
    '操作技術教師回饋': 'technical_teacher_feedback',
    '熟練程度': 'proficiency_level',
    # EPA 信賴等級評估
    'EPA項目': 'epa_item',
    'EPA可信賴程度': 'epa_reliability_level',
    'EPA質性回饋': 'epa_qualitative_feedback',
}

# 小兒科住院醫師技能基本要求次數
PEDIATRIC_SKILL_REQUIREMENTS = {
    '插氣管內管': {'minimum': 3, 'description': '訓練期間最少3次'},
    '插臍(動靜脈)導管': {'minimum': 1, 'description': '訓練期間最少1次'},
    '腰椎穿刺': {'minimum': 3, 'description': 'PGY2/R1 訓練期間最少3次'},
    '插中心靜脈導管(CVC)': {'minimum': 3, 'description': '訓練期間最少3次'},
    '肋膜液或是腹水抽取': {'minimum': 1, 'description': '訓練期間最少1次'},
    '插胸管': {'minimum': 2, 'description': '訓練期間最少2次'},
    '放置動脈導管': {'minimum': 2, 'description': '訓練期間最少2次'},
    '經皮式中央靜脈導管(PICC)': {'minimum': 3, 'description': '訓練期間最少3次'},
    '腦部超音波': {'minimum': 5, 'description': '訓練期間最少5次'},
    '心臟超音波': {'minimum': 5, 'description': '訓練期間最少5次'},
    '腹部超音波': {'minimum': 5, 'description': '訓練期間最少5次'},
    '腎臟超音波': {'minimum': 5, 'description': '訓練期間最少5次'},
    'APLS': {'minimum': 1, 'description': '訓練期間最少1次（可信賴程度≥2.5）'},
    'NRP': {'minimum': 1, 'description': '訓練期間最少1次（可信賴程度≥2.5）'},
}

# 兒科 EPA 信賴等級評估項目（表單 Q18）
PEDIATRIC_EPA_ITEMS = ['門診表現(OPD)', '一般病人照護（WARD）', '緊急處置（ED, DR）', '重症照護（PICU, NICU）', '病歷書寫']

def _normalize_paren(s):
    """統一全形/半形括號，方便比對 EPA 項目名稱"""
    return str(s).replace('（', '(').replace('）', ')').replace('︵', '(').replace('︶', ')')

def _match_epa_item(series, item):
    """比對 EPA 項目，容許全形/半形括號差異"""
    norm_item = _normalize_paren(item)
    return series.astype(str).apply(lambda x: norm_item in _normalize_paren(x))

# ─── 技能分組（用於 CCC 總覽和個別分析的分類進度顯示）───
SKILL_GROUPS = {
    '導管與插管類': ['插氣管內管', '插臍(動靜脈)導管', '腰椎穿刺',
                    '插中心靜脈導管(CVC)', '肋膜液或是腹水抽取',
                    '插胸管', '放置動脈導管', '經皮式中央靜脈導管(PICC)'],
    '超音波類':    ['腦部超音波', '心臟超音波', '腹部超音波', '腎臟超音波'],
    '急救類': ['APLS', 'NRP']
}

# ─── CCC 門檻標準（依年級分級）───
# score_threshold: EPA 均分 & 會議報告均分的達標門檻
# skill_pass_rate: 16 項技能中達標項目佔比的門檻（%）
LEVEL_THRESHOLDS = {
    'PGY2': {'score_threshold': 2.5, 'skill_pass_rate': 30},
    'R1':   {'score_threshold': 2.5, 'skill_pass_rate': 30},
    'R2':   {'score_threshold': 3.0, 'skill_pass_rate': 60},
    'R3':   {'score_threshold': 3.5, 'skill_pass_rate': 100},
}

def _get_level_thresholds(level):
    """取得年級對應的門檻，不認識的年級 fallback 到 R1"""
    return LEVEL_THRESHOLDS.get(str(level), LEVEL_THRESHOLDS['R1'])

def _filter_recent_6_months(data):
    """過濾資料，僅保留近半年（180天）的記錄"""
    if data.empty or '評核日期' not in data.columns:
        return data
    try:
        from datetime import date, timedelta
        cutoff = date.today() - timedelta(days=180)
        dates = pd.to_datetime(data['評核日期'], errors='coerce').dt.date
        return data[dates >= cutoff].copy()
    except Exception:
        return data

def show_pediatric_evaluation_section():
    """顯示小兒部住院醫師評核分頁"""
    st.title("🏥 小兒部住院醫師評核系統")
    st.markdown("---")

    # 顯示表單連結 + 資料來源（預設小兒部，不需科別過濾）
    st.session_state['selected_department'] = '小兒部'

    col1, col2 = st.columns([2, 1])
    with col1:
        # 資料來源選擇（Google Sheets 暫時隱藏）
        data_source = st.radio(
            "資料來源",
            options=['supabase', 'test'],
            format_func=lambda x: {'supabase': '☁️ Supabase', 'test': '🧪 測試資料'}[x],
            horizontal=True,
            index=0 if _get_supabase_conn() else 0,
            help="選擇資料來源：Supabase 或測試資料"
        )
        st.session_state['pediatric_data_source'] = data_source
        st.session_state['use_pediatric_test_data'] = (data_source == 'test')
    with col2:
        st.checkbox(
            "包含展示資料",
            value=True,
            key="include_demo_data",
            help="勾選後會載入展示用的範例資料（5位虛擬住院醫師、81筆評核紀錄）"
        )

    # 判斷是否為教師/管理員（可使用表單與帳號管理）
    from modules.auth import check_permission
    user_role = st.session_state.get('role', 'resident')
    can_submit_forms = check_permission(user_role, 'can_upload_files')
    can_manage_users = check_permission(user_role, 'can_manage_users')
    is_resident = (user_role == 'resident')

    # 動態建立 tabs（住院醫師只顯示「個別深入分析」和「我的表單」）
    if is_resident:
        tab_labels = ["📋 個別深入分析", "📝 我的表單"]
        tabs = st.tabs(tab_labels)

        with tabs[0]:
            show_individual_analysis()

        with tabs[1]:
            conn = _get_supabase_conn()
            if conn:
                from pages.pediatric.pediatric_resident_forms import show_resident_forms_tab
                current_user = st.session_state.get('user_name', st.session_state.get('username', '未知'))
                show_resident_forms_tab(conn, current_user)
            else:
                st.error("❌ 無法連線 Supabase，請檢查 `.env` 中的 `SUPABASE_URL` 和 `SUPABASE_KEY` 設定。")
    else:
        # 非住院醫師（教師/管理員）：完整 tabs，評核表單放第一
        tab_labels = []
        if can_submit_forms:
            tab_labels.append("✏️ 評核表單")
        tab_labels += ["🏆 CCC 總覽", "📋 個別深入分析"]
        # tab_labels += ["📊 資料概覽", "⚙️ 資料管理"]  # 暫時隱藏
        if can_manage_users:
            tab_labels.append("👥 帳號管理")

        tabs = st.tabs(tab_labels)
        idx = 0

        # 評核表單（教師/管理員限定）— 第一個 tab
        if can_submit_forms:
            with tabs[idx]:
                conn = _get_supabase_conn()
                if conn:
                    from pages.pediatric.pediatric_forms import show_evaluation_forms_tab
                    current_user = st.session_state.get('user_name', st.session_state.get('username', '未知'))
                    show_evaluation_forms_tab(conn, current_user)
                else:
                    st.error("❌ 無法連線 Supabase，請檢查 `.env` 中的 `SUPABASE_URL` 和 `SUPABASE_KEY` 設定。")
                    st.info("評核表單需要 Supabase 資料庫連線才能使用。")
            idx += 1

        with tabs[idx]:
            show_ccc_overview()
        idx += 1

        with tabs[idx]:
            show_individual_analysis()
        idx += 1

        # 資料概覽與資料管理暫時隱藏
        # with tabs[idx]:
        #     show_data_overview()
        # idx += 1
        # with tabs[idx]:
        #     show_data_management()
        # idx += 1

        # 帳號管理（管理員限定）
        if can_manage_users:
            with tabs[idx]:
                conn = _get_supabase_conn()
                if conn:
                    from pages.pediatric.pediatric_user_management import show_pediatric_user_management
                    show_pediatric_user_management(conn)
                else:
                    st.error("❌ 無法連線 Supabase，請檢查 `.env` 設定。")

def load_pediatric_data(department=None):
    """
    載入小兒部評核資料（混合資料來源）。
    優先順序：測試資料 > Supabase > Google Sheets

    Args:
        department (str, optional): 科別過濾，僅在 Supabase 模式下生效
    """
    try:
        data_source = st.session_state.get('pediatric_data_source', 'supabase')

        # ── 測試資料模式 ──
        if data_source == 'test' or st.session_state.get('use_pediatric_test_data', False):
            import os
            test_data_path = 'pages/pediatric/test_data_pediatric_evaluations.csv'
            if os.path.exists(test_data_path):
                df = pd.read_csv(test_data_path, encoding='utf-8-sig')
                sheet_titles = ['測試資料']
                st.success("✅ 已載入測試資料（5位虛擬住院醫師，628筆評核記錄）")
            else:
                st.error(f"❌ 測試資料檔案不存在：{test_data_path}")
                return None, None

        # ── Supabase 模式（預設）──
        else:
            df, sheet_titles = _load_from_supabase(department=department)
            if df is None or df.empty:
                st.warning("⚠️ Supabase 無資料或連線失敗")

        if df is not None and not df.empty:
            processed_df = process_pediatric_data(df)
            return processed_df, sheet_titles
        else:
            st.warning("無法載入小兒部評核資料")
            return None, None

    except Exception as e:
        st.error(f"載入資料時發生錯誤：{str(e)}")
        return None, None


def _load_from_google_sheets():
    """從 Google Sheets 載入資料"""
    spreadsheet_url = "https://docs.google.com/spreadsheets/d/1n4kc2d3Z-x9SvIDApPCCz2HSDO0wSrrk9Y5jReMhr-M/edit?usp=sharing"
    df, sheet_titles = fetch_google_form_data(spreadsheet_url=spreadsheet_url)
    if df is not None and not df.empty:
        st.success(f"✅ 已從 Google Sheets 載入 {len(df)} 筆資料")
    return df, sheet_titles


def _load_from_supabase(department=None):
    """
    從 Supabase 載入資料並轉換為與 Google Sheets 相容的 DataFrame 格式。
    確保後續 process_pediatric_data() 能正常運作。

    Args:
        department (str, optional): 科別過濾
    """
    conn = _get_supabase_conn()
    if not conn:
        return None, None

    try:
        filters = {'department': department} if department else None
        records = conn.fetch_pediatric_evaluations(filters=filters)
        if not records:
            return None, None

        df = pd.DataFrame(records)

        # 依「包含展示資料」勾選狀態過濾 demo 資料
        if not st.session_state.get('include_demo_data', True):
            if 'form_version' in df.columns:
                df = df[df['form_version'] != 'demo']
                if df.empty:
                    return None, None

        # 將 Supabase 欄位名映射回中文欄位（與 Google Sheets 格式一致）
        col_map = {
            'evaluator_teacher': '評核教師',
            'evaluation_date': '評核日期',
            'evaluated_resident': '受評核人員',
            'resident_level': '評核時級職',
            'evaluation_item': '評核項目',
            'meeting_name': '會議名稱',
            'content_sufficient': '內容是否充分',
            'data_analysis_ability': '辯證資料的能力',
            'presentation_clarity': '口條、呈現方式是否清晰',
            'innovative_ideas': '是否具開創、建設性的想法',
            'logical_response': '回答提問是否具邏輯、有條有理',
            'meeting_feedback': '會議報告教師回饋',
            'patient_id': '病歷號',
            'technical_skill_item': '評核技術項目',
            'sedation_medication': '鎮靜藥物',
            'reliability_level': '可信賴程度',
            'technical_feedback': '操作技術教師回饋',
            'proficiency_level': '熟練程度',
            'epa_item': 'EPA項目',
            'epa_reliability_level': 'EPA可信賴程度',
            'epa_qualitative_feedback': 'EPA質性回饋',
        }
        df = df.rename(columns=col_map)

        # Supabase 存的是數值，process_pediatric_data 裡 convert_*
        # 函數預期文字輸入，所以對數值欄位先建立 _數值 後綴欄位，
        # 跳過文字→數值轉換。
        # 但更穩妥的做法是讓 process_pediatric_data 處理，
        # 因為 Supabase 的數值欄位已是 float/int，
        # convert_* 函數遇到非字串會回傳 None，
        # 所以我們需要預建 _數值 欄位。

        # 會議報告分數（Supabase 已是 int）
        score_cols_map = {
            '內容是否充分': '內容是否充分_數值',
            '辯證資料的能力': '辯證資料的能力_數值',
            '口條、呈現方式是否清晰': '口條、呈現方式是否清晰_數值',
            '是否具開創、建設性的想法': '是否具開創、建設性的想法_數值',
            '回答提問是否具邏輯、有條有理': '回答提問是否具邏輯、有條有理_數值',
        }

        for src, dst in score_cols_map.items():
            if src in df.columns:
                df[dst] = pd.to_numeric(df[src], errors='coerce')

        # 可信賴程度 / EPA 可信賴程度（Supabase 已是 float）
        if '可信賴程度' in df.columns:
            df['可信賴程度_數值'] = pd.to_numeric(df['可信賴程度'], errors='coerce')
        if 'EPA可信賴程度' in df.columns:
            df['EPA可信賴程度_數值'] = pd.to_numeric(df['EPA可信賴程度'], errors='coerce')
        if '熟練程度' in df.columns:
            df['熟練程度_數值'] = pd.to_numeric(df['熟練程度'], errors='coerce')

        # 從可信賴程度推導熟練度
        if '可信賴程度_數值' in df.columns:
            df['熟練程度(自動判定)'] = df['可信賴程度_數值'].apply(derive_proficiency_from_reliability)

        st.success(f"✅ 已從 Supabase 載入 {len(df)} 筆資料")
        return df, ['Supabase']

    except Exception as e:
        st.warning(f"⚠️ 從 Supabase 載入失敗：{str(e)}")
        return None, None

def process_pediatric_data(df):
    """處理小兒部評核資料"""
    try:
        # 複製資料框
        processed_df = df.copy()
        # 正規化欄位名稱：去除前後空白（Google 表單匯出可能帶尾端空格）
        processed_df.columns = [str(c).strip() if c is not None else '' for c in processed_df.columns]
        
        # 處理評核日期
        if '評核日期' in processed_df.columns:
            # 如果評核日期已經是日期格式，直接使用
            if processed_df['評核日期'].dtype == 'object':
                # 嘗試將字串轉換為日期
                try:
                    processed_df['評核日期'] = pd.to_datetime(processed_df['評核日期'], errors='coerce').dt.date
                except Exception as e:
                    st.warning(f"⚠️ 評核日期轉換錯誤: {str(e)}")
        
        # 如果沒有評核日期欄位，嘗試從時間戳記解析
        elif '時間戳記' in processed_df.columns:
            # 創建評核日期欄位
            processed_df['評核日期'] = None
            
            # 嘗試解析時間戳記中的日期部分
            for idx, timestamp in processed_df['時間戳記'].items():
                if pd.notna(timestamp):
                    timestamp_str = str(timestamp).strip()
                    
                    # 提取日期部分（在空格之前的部分）
                    date_part = timestamp_str.split(' ')[0] if ' ' in timestamp_str else timestamp_str
                    
                    # 嘗試解析日期
                    try:
                        parsed_date = pd.to_datetime(date_part, format='%Y/%m/%d').date()
                        processed_df.at[idx, '評核日期'] = parsed_date
                    except:
                        pass
        
        # 處理數值評分欄位
        score_columns = ['內容是否充分', '辯證資料的能力', '口條、呈現方式是否清晰', 
                        '是否具開創、建設性的想法', '回答提問是否具邏輯、有條有理']
        
        for col in score_columns:
            if col in processed_df.columns:
                # 將文字評分轉換為數值
                processed_df[f'{col}_數值'] = processed_df[col].apply(convert_score_to_numeric)
        
        # 處理可信賴程度
        if '可信賴程度' in processed_df.columns:
            processed_df['可信賴程度_數值'] = processed_df['可信賴程度'].apply(convert_reliability_to_numeric)
        
        # 處理熟練程度（向後相容舊資料）
        if '熟練程度' in processed_df.columns:
            processed_df['熟練程度_數值'] = processed_df['熟練程度'].apply(convert_proficiency_to_numeric)

        # 從可信賴程度推導熟練度（統一判定標準）
        if '可信賴程度_數值' in processed_df.columns:
            processed_df['熟練程度(自動判定)'] = processed_df['可信賴程度_數值'].apply(derive_proficiency_from_reliability)
        
        # 處理 EPA 可信賴程度（沿用兒科 convert_reliability_to_numeric 對照表）
        if 'EPA可信賴程度' in processed_df.columns:
            processed_df['EPA可信賴程度_數值'] = processed_df['EPA可信賴程度'].apply(convert_reliability_to_numeric)
        
        return processed_df
        
    except Exception as e:
        st.error(f"處理資料時發生錯誤：{str(e)}")
        return df

def convert_score_to_numeric(score_text):
    """將評分文字轉換為數值"""
    if pd.isna(score_text) or score_text == '':
        return None

    # 如果已經是數字（例如從 Supabase 載入的整數），直接返回
    try:
        num_value = float(score_text)
        if 1 <= num_value <= 5:
            return num_value
    except (ValueError, TypeError):
        pass

    score_text = str(score_text).strip()
    
    # 定義評分對應（含表單「5 卓越～1 不符合期待」）
    score_mapping = {
        '非常同意': 5,
        '同意': 4,
        '普通': 3,
        '不同意': 2,
        '非常不同意': 1,
        '優秀': 5,
        '良好': 4,
        '待改進': 2,
        '需加強': 1,
        # 會議報告表單用語（有空格）
        '5 卓越': 5,
        '4 充分': 4,
        '3 尚可': 3,
        '2 稍差': 2,
        '1 不符合期待': 1,
        # 會議報告表單用語（數字與文字連在一起，如表格匯出）
        '5卓越': 5,
        '4充分': 4,
        '3尚可': 3,
        '2稍差': 2,
        '1不符合期待': 1,
        '卓越': 5,
        '充分': 4,
        '尚可': 3,
        '稍差': 2,
        '不符合期待': 1,
    }
    
    return score_mapping.get(score_text, None)

def convert_reliability_to_numeric(reliability_text):
    """將可信賴程度轉換為數值（兒科專用，9級量表 → 1.5-5.0分）"""
    if pd.isna(reliability_text) or reliability_text == '':
        return None

    reliability_text = str(reliability_text).strip()

    # 如果已經是數字，直接返回
    try:
        num_value = float(reliability_text)
        if 1 <= num_value <= 5:
            return num_value
    except (ValueError, TypeError):
        pass

    # 兒科評核表單對應（主要）
    reliability_mapping = {
        # 新格式：五分制小數點顯示（符合學會規範）
        '1.5 — 允許住院醫師在旁觀察': 1.5,
        '2.0 — 教師在旁逐步共同操作': 2.0,
        '2.5 — 教師在旁必要時協助': 2.5,
        '3.0 — 教師可立即到場協助，事後逐項確認': 3.0,
        '3.3 — 教師可立即到場協助，事後重點確認': 3.3,
        '3.6 — 教師可稍後到場協助，必要時事後確認': 3.6,
        '4.0 — 教師on call提供監督': 4.0,
        '4.5 — 教師不需on call，事後提供回饋及監督': 4.5,
        '5.0 — 學員可對其他資淺的學員進行監督與教學': 5.0,
        # 舊格式向後相容
        '允許住院醫師在旁觀察': 1.5,
        '教師在旁逐步共同操作': 2.0,
        '教師在旁必要時協助': 2.5,
        '教師可立即到場協助，事後逐項確認': 3.0,
        '教師可立即到場協助，事後重點確認': 3.3,
        '教師可稍後到場協助，必要時事後確認': 3.6,
        '教師on call提供監督': 4.0,
        '教師不需on call，事後提供回饋及監督': 4.5,
        '學員可對其他資淺的學員進行監督與教學': 5.0,

        # 向下相容：舊資料可能的格式變體
        '不允許學員觀察': 1.0,  # 舊資料（兒科表單已無此選項）
        '學員在旁觀察': 1.5,
        '允許學員在旁觀察': 1.5,
        '教師在旁必要時協助 ': 2.5,  # 尾部空格
        '教師可立即到場協助，事後須再確認': 3.0,
        '教師可稍後到場協助，重點須再確認': 4.0,
        '我可獨立執行': 5.0,
    }

    return reliability_mapping.get(reliability_text, None)

def derive_proficiency_from_reliability(reliability_score):
    """
    從可信賴程度分數推導熟練度標籤。
    >= 3.5 → 熟練 / < 3.5 → 不熟練
    """
    if pd.isna(reliability_score):
        return None
    return '熟練' if float(reliability_score) >= 3.5 else '不熟練'


def convert_proficiency_to_numeric(proficiency_text):
    """[Deprecated] 將熟練程度轉換為數值 — 僅供向後相容舊資料"""
    if pd.isna(proficiency_text) or proficiency_text == '':
        return None
    
    proficiency_text = str(proficiency_text).strip()
    
    # 定義熟練程度對應
    proficiency_mapping = {
        '熟練': 5,
        '基本熟練': 4,
        '部分熟練': 3,
        '初學': 2,
        '不熟練': 1,
        '一兩次內完成': 5,
        '協助下完成': 3,
        '需指導完成': 2
    }
    
    return proficiency_mapping.get(proficiency_text, None)

def show_skill_completion_overview(df):
    """顯示所有住院醫師技能項目完成比例概覽"""
    st.subheader("🎯 各技能項目完成比例概覽")
    
    # 篩選操作技術評核資料
    technical_data = df[df['評核項目'] == '操作技術'].copy()
    
    if technical_data.empty:
        st.info("目前沒有操作技術評核資料")
        return
    
    # 獲取所有住院醫師
    all_residents = df['受評核人員'].unique()
    
    # 計算每個住院醫師的技能完成狀況
    resident_skill_summary = []
    
    for resident in all_residents:
        resident_data = technical_data[technical_data['受評核人員'] == resident]
        skill_counts = calculate_skill_counts(resident_data)
        
        # 獲取該住院醫師的階層資訊
        resident_level = "未知"
        if '評核時級職' in df.columns:
            level_data = df[df['受評核人員'] == resident]['評核時級職'].dropna()
            if not level_data.empty:
                # 取最常見的階層
                resident_level = level_data.mode().iloc[0] if not level_data.empty else "未知"
        
        resident_summary = {
            '住院醫師': resident,
            '評核時級職': resident_level,
            '總技能數': len(skill_counts),
            '已完成技能數': 0,
            '完成率': 0.0
        }
        
        # 計算完成狀況（minimum=0 的項目需至少有1筆記錄才算完成）
        completed_skills = 0
        for skill, data in skill_counts.items():
            if data['required'] > 0 and data['completed'] >= data['required']:
                completed_skills += 1
            elif data['required'] == 0 and data['completed'] > 0:
                completed_skills += 1
        
        resident_summary['已完成技能數'] = completed_skills
        if len(skill_counts) > 0:
            resident_summary['完成率'] = (completed_skills / len(skill_counts)) * 100
        
        resident_skill_summary.append(resident_summary)
    
    if resident_skill_summary:
        # 顯示住院醫師技能完成狀況摘要
        summary_df = pd.DataFrame(resident_skill_summary)
        
        # 按完成率排序
        summary_df = summary_df.sort_values('完成率', ascending=False)
        
        # 準備技能列表用於個別分析
        skills = list(PEDIATRIC_SKILL_REQUIREMENTS.keys())
        
        # 每個技能項目的獨立長條圖
        st.write("**各技能項目個別分析**")
        st.info("💡 **完成標準**：只有「可信賴程度」在3以上（3=教師可立即到場協助，事後逐項確認、4=教師on call提供監督、5=學員可對其他資淺的學員進行監督與教學）的評核記錄才會計入完成次數")
        
        # 計算需要的行數和列數
        num_skills = len(skills)
        cols_per_row = 3  # 每行3個圖表
        rows = (num_skills + cols_per_row - 1) // cols_per_row
        
        # 創建子圖
        # 動態計算垂直間距，確保不超過Plotly的限制，並設定更小的間距
        max_vertical_spacing = 1 / (rows - 1) if rows > 1 else 0.1
        vertical_spacing = min(0.05, max_vertical_spacing * 0.3)  # 使用更小的間距，30%的最大值
        
        fig_individual = make_subplots(
            rows=rows, 
            cols=cols_per_row,
            subplot_titles=skills,
            vertical_spacing=vertical_spacing,
            horizontal_spacing=0.1
        )
        
        # 為每個技能創建長條圖
        for i, skill in enumerate(skills):
            row = (i // cols_per_row) + 1
            col = (i % cols_per_row) + 1
            
            # 收集該技能的所有住院醫師完成次數
            skill_data = []
            resident_names = []
            
            for resident in all_residents:
                resident_data = technical_data[technical_data['受評核人員'] == resident]
                skill_counts = calculate_skill_counts(resident_data)
                
                if skill in skill_counts:
                    completed_count = skill_counts[skill]['completed']
                    skill_data.append(completed_count)
                    resident_names.append(resident)
            
            # 添加長條圖
            if skill_data:
                fig_individual.add_trace(
                    go.Bar(
                        x=resident_names,
                        y=skill_data,
                        name=skill,
                        showlegend=False,
                        marker_color=['lightgreen' if count >= PEDIATRIC_SKILL_REQUIREMENTS[skill]['minimum'] 
                                    else 'lightcoral' for count in skill_data],
                        text=[f"{count}/{PEDIATRIC_SKILL_REQUIREMENTS[skill]['minimum']}" for count in skill_data],
                        textposition='auto'
                    ),
                    row=row, col=col
                )
                
                # 添加及格線
                required_count = PEDIATRIC_SKILL_REQUIREMENTS[skill]['minimum']
                fig_individual.add_hline(
                    y=required_count,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"及格線 ({required_count}次)",
                    annotation_position="top right",
                    row=row, col=col
                )
            
            # 設定Y軸範圍
            max_value = max(skill_data) if skill_data else 0
            y_max = max(max_value + 1, PEDIATRIC_SKILL_REQUIREMENTS[skill]['minimum'] + 1)
            fig_individual.update_yaxes(range=[0, y_max], row=row, col=col)
        
        # 更新整體佈局
        fig_individual.update_layout(
            title="各技能項目個別分析 - 住院醫師完成次數",
            height=400 * rows,  # 高度調整為一半 (800 / 2 = 400)
            showlegend=False
        )
        
        # 更新X軸標籤角度
        fig_individual.update_xaxes(tickangle=-45)
        
        st.plotly_chart(fig_individual, width="stretch")


def show_epa_overview(df):
    """顯示 EPA 信賴等級評估概覽（評核項目為 EPA 時）"""
    if '評核項目' not in df.columns:
        return
    epa_data = df[df['評核項目'].astype(str).str.contains('EPA', na=False)].copy()
    if epa_data.empty:
        return
    st.subheader("📋 EPA 信賴等級評估概覽")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("EPA 評核筆數", len(epa_data))
    with col2:
        unique_residents_epa = epa_data['受評核人員'].nunique() if '受評核人員' in epa_data.columns else 0
        st.metric("受評核人員數", unique_residents_epa)
    with col3:
        if 'EPA可信賴程度_數值' in epa_data.columns:
            avg = epa_data['EPA可信賴程度_數值'].dropna().mean()
            st.metric("平均可信賴程度", f"{avg:.2f}" if pd.notna(avg) else "—")
        else:
            st.metric("平均可信賴程度", "—")
    if 'EPA項目' in epa_data.columns:
        epa_counts = epa_data['EPA項目'].value_counts()
        fig = px.bar(
            x=epa_counts.index,
            y=epa_counts.values,
            title="EPA 項目分布",
            labels={'x': 'EPA 項目', 'y': '評核次數'}
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, width="stretch")


# ═══════════════════════════════════════════════════════
# CCC 總覽模組（Tab 1）
# ═══════════════════════════════════════════════════════

def _get_resident_level(df, resident_name):
    """取得住院醫師的級職（取最常見值）"""
    if '評核時級職' not in df.columns:
        return '未知'
    lvs = df[df['受評核人員'] == resident_name]['評核時級職'].dropna()
    return lvs.mode().iloc[0] if len(lvs) > 0 else '未知'

def _status_emoji(status):
    return {'PASS': '✅', 'FAIL': '❌', 'GREEN': '🟢', 'YELLOW': '🟡', 'RED': '🔴'}.get(status, '⚪')

def _status_label(status):
    return {'PASS': '達標', 'FAIL': '未達標', 'GREEN': '進度良好', 'YELLOW': '需注意', 'RED': '需輔導'}.get(status, '未知')

def show_ccc_overview():
    """Tab 1：CCC 總覽頁面主函數"""
    st.subheader("🏆 CCC 會議 — 小兒部住院醫師訓練進度總覽")

    # ── 達標標準說明 ──
    with st.expander("📋 各年級達標標準"):
        std_col1, std_col2 = st.columns(2)
        with std_col1:
            st.markdown("**會議報告 & EPA（均分門檻）**")
            st.markdown(
                "| 年級 | 達標門檻 |\n|------|--------|\n"
                "| PGY2 / R1 | ≥ 2.5 分 |\n"
                "| R2 | ≥ 3.0 分 |\n"
                "| R3 | ≥ 3.5 分 |"
            )
        with std_col2:
            st.markdown("**操作技術（達標項目佔比，≥2.5 分算完成）**")
            st.markdown(
                "| 年級 | 達標比例 |\n|------|--------|\n"
                "| PGY2 / R1 | ≥ 30% |\n"
                "| R2 | ≥ 60% |\n"
                "| R3 | ≥ 100% |"
            )

    # 獲取選擇的科別（僅在 Supabase 模式下生效）
    selected_dept = st.session_state.get('selected_department')
    data_source = st.session_state.get('pediatric_data_source', 'google_sheets')
    department_filter = selected_dept if data_source == 'supabase' else None

    if st.button("🔄 重新載入 Supabase 資料", key="reload_ccc"):
        st.session_state.pop('pediatric_data', None)
        st.rerun()

    df, _ = load_pediatric_data(department=department_filter)
    if df is None or df.empty:
        st.warning("無法載入資料，請檢查 Google 表單連接")
        return

    # 緩存資料至 session_state
    st.session_state['pediatric_data'] = df

    # ── 根據使用者角色過濾住院醫師列表 ──
    user_role = st.session_state.get('role', 'resident')
    user_name = st.session_state.get('user_name')

    if user_role == 'resident':
        # 住院醫師只能看自己的資料
        residents = [user_name] if user_name in df['受評核人員'].unique() else []
        if not residents:
            st.warning(f"找不到 {user_name} 的評核資料")
            return
    else:
        # 其他角色（admin, department_admin, teacher）可以看所有人
        residents = sorted(df['受評核人員'].unique()) if '受評核人員' in df.columns else []
        if not residents:
            st.warning("資料中沒有找到受評核人員")
            return

    # 預先批次查詢所有人的研究記錄（R3 判斷用）
    conn_ccc = _get_supabase_conn()
    research_published_map = {}
    if conn_ccc:
        try:
            all_research = conn_ccc.fetch_research_progress()
            for rec in (all_research or []):
                rname = rec.get('resident_name', '')
                if rec.get('current_status') in ('接受', '發表'):
                    research_published_map[rname] = research_published_map.get(rname, 0) + 1
        except Exception:
            pass

    all_status = {}  # {姓名: status_dict}
    for name in residents:
        res_df = df[df['受評核人員'] == name]
        level = _get_resident_level(df, name)
        pub_count = research_published_map.get(name, 0)
        all_status[name] = calculate_resident_status(res_df, df, resident_level=level,
                                                      research_published=pub_count)
        all_status[name]['level'] = level

    # ── Section C：三大主視圖（EPA / 技能 / 會議報告）──
    ccc_tab_epa, ccc_tab_skill, ccc_tab_meeting = st.tabs([
        "📈 EPA 趨勢", "🎯 技能完成度", "📑 會議報告"
    ])

    with ccc_tab_epa:
        show_ccc_epa_by_item(df)

    with ccc_tab_skill:
        show_skill_heatmap(df)

    with ccc_tab_meeting:
        show_ccc_meeting_comparison(df)

    st.divider()

    # ── Section D：研究進度總覽（若有 Supabase 連線）──
    conn = _get_supabase_conn()
    if conn:
        show_research_progress_overview(conn, residents)


def show_alert_banner(all_status):
    """警報橫帶：達標/未達標分類顯示姓名"""
    groups = {'PASS': [], 'FAIL': []}
    for name, info in all_status.items():
        groups[info['overall']].append(name)

    banner_parts = []
    if groups['FAIL']:
        banner_parts.append(
            f'<span style="background:#ffe0e0;color:#c0392b;padding:6px 12px;border-radius:6px;font-weight:bold;">❌ 未達標：{" ・ ".join(groups["FAIL"])}</span>'
        )
    if groups['PASS']:
        banner_parts.append(
            f'<span style="background:#d4edda;color:#155724;padding:6px 12px;border-radius:6px;font-weight:bold;">✅ 達標：{" ・ ".join(groups["PASS"])}</span>'
        )

    st.markdown(' &nbsp;&nbsp; '.join(banner_parts), unsafe_allow_html=True)


def show_resident_cards(all_status, df):
    """摘要卡片列表：每行 3 張卡片，含年級門檻與達標狀態"""
    residents = list(all_status.keys())
    n_cols = min(3, len(residents))
    cols = st.columns(n_cols)

    for i, name in enumerate(residents):
        info = all_status[name]
        th = info.get('thresholds', _get_level_thresholds(info['level']))
        col = cols[i % n_cols]

        with col:
            with st.container(border=True):
                # 標題行：姓名 + 級職 + 整體狀態
                overall_icon = _status_emoji(info['overall'])
                st.markdown(
                    f"**{name}** &nbsp; {info['level']} &nbsp; {overall_icon} {_status_label(info['overall'])}",
                    unsafe_allow_html=True
                )
                st.divider()

                # 三個指標並排
                c1, c2, c3 = st.columns(3)
                with c1:
                    epa_val = info['epa']['avg_score']
                    st.metric("EPA均分", f"{epa_val:.1f}" if epa_val is not None else "—")
                    epa_icon = _status_emoji(info['epa']['status'])
                    epa_item_counts = info['epa'].get('item_counts', {})
                    epa_item_min = info['epa'].get('item_min', 3)
                    min_cnt = min(epa_item_counts.values()) if epa_item_counts else 0
                    st.caption(f"{epa_icon} 均分≥{th['score_threshold']}，各項≥{epa_item_min}次（最少{min_cnt}次）")
                with c2:
                    tech_rate = info['technical']['pass_rate']
                    done = info['technical']['completed_skills']
                    total = info['technical']['total_skills']
                    st.metric("技能完成進度", f"{tech_rate:.0f}%" if tech_rate is not None else "—")
                    tech_icon = _status_emoji(info['technical']['status'])
                    st.caption(f"{tech_icon} 門檻 ≥{th['skill_pass_rate']}%")
                    sess_done = info['technical'].get('completed_sessions', done)
                    sess_total = info['technical'].get('total_required_sessions', 40)
                    st.caption(f"({sess_done}/40 次，{done}/{total} 項完成)")
                with c3:
                    mtg_val = info['meeting']['avg_score']
                    st.metric("會議報告均分", f"{mtg_val:.1f}" if mtg_val is not None else "—")
                    mtg_icon = _status_emoji(info['meeting']['status'])
                    st.caption(f"{mtg_icon} 門檻 ≥{th['score_threshold']}")

                # R3 文章發表狀態
                research_info = info.get('research', {})
                if research_info.get('status') is not None:  # 僅 R3
                    st.divider()
                    pub_n = research_info.get('published_count', 0)
                    res_icon = _status_emoji(research_info['status'])
                    st.caption(f"📄 文章發表 {res_icon} {pub_n} 篇（R3 需 ≥1 篇）")
                else:
                    # 非 R3 顯示研究進度筆數
                    conn = _get_supabase_conn()
                    if conn:
                        try:
                            research_records = conn.fetch_research_progress(filters={'resident_name': name})
                            if research_records:
                                st.divider()
                                st.caption(f"📚 研究進度：{len(research_records)} 項")
                                latest = research_records[0]
                                status_emoji_map = {'構思中': '💡', '撰寫中': '✍️', '投稿中': '📤', '接受': '✅'}
                                st.caption(f"{status_emoji_map.get(latest['current_status'], '📝')} {latest['research_title']} — {latest['current_status']}")
                        except Exception:
                            pass


def show_comparison_bar_chart(all_status):
    """並排長條圖：三維度百分化後對比（含年級門檻標註）"""
    st.subheader("📊 訓練完成度並排比較")
    st.caption("技能完成進度 = 有效次數÷40次×100%（每技能上限為最低要求次數）｜ EPA/會議 = 均分÷5×100%。門檻依年級：PGY2/R1→2.5分/30%, R2→3.0分/60%, R3→3.5分/100%")

    names = list(all_status.keys())
    tech_rates  = []
    epa_rates   = []
    mtg_rates   = []

    for name in names:
        info = all_status[name]
        tech_rates.append(info['technical']['pass_rate'] if info['technical']['pass_rate'] is not None else 0)
        epa_rates.append(info['epa']['avg_score'] / 5 * 100 if info['epa']['avg_score'] is not None else 0)
        mtg_rates.append(info['meeting']['avg_score'] / 5 * 100 if info['meeting']['avg_score'] is not None else 0)

    fig = go.Figure()
    fig.add_trace(go.Bar(name='技能完成進度 (%)',   x=names, y=tech_rates, marker_color='#4A90D9'))
    fig.add_trace(go.Bar(name='EPA均分 (%)',    x=names, y=epa_rates,  marker_color='#50C878'))
    fig.add_trace(go.Bar(name='會議報告均分 (%)', x=names, y=mtg_rates,  marker_color='#F5A623'))

    fig.update_layout(
        barmode='group',
        yaxis_title='百分比 (%)',
        yaxis=dict(range=[0, 110]),
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig, width="stretch")


def show_skill_heatmap(df):
    """技能熱圖矩陣：住院醫師 × 16項技能"""
    st.subheader("🎯 技能完成度熱圖矩陣")
    st.caption("單元格顯示 已完成/需完成 次數。綠色 = 達標、黃色 = 進行中、紅色 = 不足")

    technical_data = df[df['評核項目'] == '操作技術'].copy() if '評核項目' in df.columns else pd.DataFrame()
    if technical_data.empty:
        st.info("目前沒有操作技術評核資料")
        return

    residents = sorted(df['受評核人員'].unique()) if '受評核人員' in df.columns else []
    skills = list(PEDIATRIC_SKILL_REQUIREMENTS.keys())

    # 計算每人每項技能的 completed / required
    z_matrix   = []   # 比值 (0-1+)
    text_matrix = []  # 標記文字 "X/Y"
    resident_rates = []  # 總完成率（用於排序）

    for name in residents:
        res_tech = technical_data[technical_data['受評核人員'] == name]
        counts = calculate_skill_counts(res_tech)
        row_z    = []
        row_text = []
        completed_n = 0
        for skill in skills:
            c = counts.get(skill, {}).get('completed', 0)
            r = counts.get(skill, {}).get('required', PEDIATRIC_SKILL_REQUIREMENTS[skill]['minimum'])
            if r == 0:
                # 僅記錄項目（APLS/NRP）：有紀錄就算達標（綠色）
                row_z.append(1.0 if c > 0 else 0.5)
                row_text.append(f"{c}/記錄")
                if c > 0:
                    completed_n += 1  # 僅記錄項目：有記錄才算達標
            else:
                row_z.append(min(c / r, 1.5))  # cap at 1.5 for color
                row_text.append(f"{c}/{r}")
                if c >= r:
                    completed_n += 1
        z_matrix.append(row_z)
        text_matrix.append(row_text)
        resident_rates.append(completed_n / len(skills) * 100 if skills else 0)

    # 按完成率從低到高排序（進度慢的在上面，先看見）
    order = sorted(range(len(residents)), key=lambda i: resident_rates[i])
    sorted_residents   = [residents[i] for i in order]
    sorted_z_matrix    = [z_matrix[i] for i in order]
    sorted_text_matrix = [text_matrix[i] for i in order]

    # 自定義顏色映射：z 值範圍 0-1.5，映射到 0-1 的 colorscale
    # <0.5 紅, 0.5-0.99 黃, >=1.0 綠
    colorscale = [
        [0.0,   '#FF6B6B'],   # 紅（z=0）
        [0.33,  '#FF9999'],   # 淺紅（z=0.5）
        [0.34,  '#FFD93D'],   # 黃（z=0.5+）
        [0.66,  '#FFE66D'],   # 淺黃（z=1.0-）
        [0.67,  '#4CAF50'],   # 綠（z=1.0）
        [1.0,   '#2E7D32']    # 深綠（z=1.5）
    ]

    fig = go.Figure(data=go.Heatmap(
        z=sorted_z_matrix,
        x=skills,
        y=sorted_residents,
        text=sorted_text_matrix,
        texttemplate='%{text}',
        textfont={"size": 12, "color": "black"},
        colorscale=colorscale,
        zmin=0,
        zmax=1.5,
        showscale=False,   # 顏色圖例由 caption 說明即可
        hovertemplate='住院醫師：%{y}<br>技能：%{x}<br>完成：%{text}<extra></extra>'
    ))

    fig.update_layout(
        height=max(250, 60 * len(residents)),
        xaxis=dict(tickangle=-35, tickfont=dict(size=11)),
        yaxis=dict(tickfont=dict(size=13)),
        margin=dict(l=100, r=30, t=30, b=100)
    )
    st.plotly_chart(fig, width="stretch")


def show_ccc_epa_by_item(df):
    """CCC EPA 總覽：各 EPA 項目獨立分頁，每頁顯示所有住院醫師近半年月度趨勢折線圖"""
    st.subheader("📈 EPA 各項目 — 近半年趨勢（所有住院醫師）")

    epa_raw = df[df['評核項目'].astype(str).str.contains('EPA', na=False)].copy() if '評核項目' in df.columns else pd.DataFrame()
    if epa_raw.empty or 'EPA可信賴程度_數值' not in epa_raw.columns:
        st.info("目前沒有 EPA 評核資料")
        return

    epa_data = _filter_recent_6_months(epa_raw)
    if epa_data.empty:
        st.info("近半年內沒有 EPA 評核資料")
        return

    epa_data['評核日期'] = pd.to_datetime(epa_data['評核日期'], errors='coerce')
    epa_data = epa_data.dropna(subset=['評核日期'])
    epa_data['年月'] = epa_data['評核日期'].dt.to_period('M').astype(str)

    residents_list = sorted(epa_data['受評核人員'].unique()) if '受評核人員' in epa_data.columns else []
    colors = ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd',
              '#8c564b','#e377c2','#7f7f7f','#bcbd22','#17becf']

    short_labels = {
        '門診表現(OPD)':      'OPD',
        '一般病人照護（WARD）': 'WARD',
        '緊急處置（ED, DR）':  'ED/DR',
        '重症照護（PICU, NICU）': 'PICU/NICU',
        '病歷書寫':           '病歷書寫',
    }

    # 計算各項目的全體近半年均分，用於 tab 標籤
    item_tabs_labels = []
    for epa_item in PEDIATRIC_EPA_ITEMS:
        item_mask = _match_epa_item(epa_data['EPA項目'], epa_item) if 'EPA項目' in epa_data.columns else pd.Series(False, index=epa_data.index)
        item_cnt = int(item_mask.sum())
        lbl = short_labels.get(epa_item, epa_item)
        item_tabs_labels.append(f"{lbl} ({item_cnt})")

    epa_item_tabs = st.tabs(item_tabs_labels)

    for tab_ei, epa_item in zip(epa_item_tabs, PEDIATRIC_EPA_ITEMS):
        with tab_ei:
            if 'EPA項目' not in epa_data.columns:
                st.info("資料缺少 EPA項目 欄位")
                continue

            item_mask = _match_epa_item(epa_data['EPA項目'], epa_item)
            item_df = epa_data[item_mask].copy()

            if item_df.empty:
                st.caption("近半年無此項目評核記錄")
                continue

            # 各住院醫師月度平均
            monthly = item_df.groupby(['受評核人員', '年月'])['EPA可信賴程度_數值'].mean().reset_index()
            monthly.rename(columns={'EPA可信賴程度_數值': '月均分'}, inplace=True)

            fig = go.Figure()
            for i, resident in enumerate(residents_list):
                res_data = monthly[monthly['受評核人員'] == resident].sort_values('年月')
                if res_data.empty:
                    continue
                fig.add_trace(go.Scatter(
                    x=res_data['年月'],
                    y=res_data['月均分'],
                    mode='lines+markers',
                    name=resident,
                    line=dict(width=2.5, color=colors[i % len(colors)]),
                    marker=dict(size=8),
                    hovertemplate=f'{resident}<br>%{{x}}<br>均分 %{{y:.2f}}<extra></extra>'
                ))

            # 年級門檻線
            fig.add_hline(y=3.5, line_dash='dot', line_color='#c0392b', line_width=1.2,
                          annotation_text='R3 ≥3.5', annotation_position='top left',
                          annotation_font_size=11)
            fig.add_hline(y=3.0, line_dash='dot', line_color='#e67e22', line_width=1.2,
                          annotation_text='R2 ≥3.0', annotation_position='top left',
                          annotation_font_size=11)
            fig.add_hline(y=2.5, line_dash='dot', line_color='#27ae60', line_width=1.2,
                          annotation_text='R1 ≥2.5', annotation_position='bottom left',
                          annotation_font_size=11)

            fig.update_layout(
                height=380,
                margin=dict(l=10, r=10, t=30, b=10),
                xaxis=dict(title='', tickangle=-30),
                yaxis=dict(range=[0, 5.5], title='EPA 月均分', dtick=1),
                hovermode='x unified',
                legend=dict(orientation='v', yanchor='top', y=1, xanchor='left', x=1.02,
                            bgcolor='rgba(255,255,255,0.8)', bordercolor='rgba(0,0,0,0.15)',
                            borderwidth=1),
                margin_r=140
            )
            st.plotly_chart(fig, width="stretch", key=f"ccc_epa_trend_{epa_item}")


def show_ccc_meeting_comparison(df):
    """CCC 會議報告：各住院醫師五維度近半年平均分 — 熱圖矩陣"""
    st.subheader("📑 會議報告 — 各維度近半年平均分")

    mtg_raw = df[df['評核項目'].astype(str).str.contains('會議報告', na=False)].copy() if '評核項目' in df.columns else pd.DataFrame()
    if mtg_raw.empty:
        st.info("目前沒有會議報告評核資料")
        return

    mtg_data = _filter_recent_6_months(mtg_raw)
    if mtg_data.empty:
        st.info("近半年內沒有會議報告評核資料")
        return

    dim_cols = [
        ('內容是否充分_數值',           '內容充分'),
        ('辯證資料的能力_數值',         '辯證資料'),
        ('口條、呈現方式是否清晰_數值', '口條清晰'),
        ('是否具開創、建設性的想法_數值','開創想法'),
        ('回答提問是否具邏輯、有條有理_數值','邏輯回答'),
    ]
    avail_dims = [(col, lbl) for col, lbl in dim_cols if col in mtg_data.columns]

    if not avail_dims:
        # 嘗試未轉換的原始欄位
        dim_raw = [
            ('內容是否充分', '內容充分'), ('辯證資料的能力', '辯證資料'),
            ('口條、呈現方式是否清晰', '口條清晰'), ('是否具開創、建設性的想法', '開創想法'),
            ('回答提問是否具邏輯、有條有理', '邏輯回答'),
        ]
        for col, lbl in dim_raw:
            if col in mtg_data.columns:
                mtg_data[f'{col}_數值'] = mtg_data[col].apply(convert_score_to_numeric)
        avail_dims = [(f'{col}_數值', lbl) for col, lbl in dim_raw if f'{col}_數值' in mtg_data.columns]

    if not avail_dims:
        st.info("找不到會議報告評分欄位")
        return

    residents_sorted = sorted(mtg_data['受評核人員'].unique()) if '受評核人員' in mtg_data.columns else []
    dim_labels = [lbl for _, lbl in avail_dims]

    # 計算各住院醫師各維度平均（Z 矩陣，行=住院醫師，列=維度）
    z_matrix   = []
    text_matrix = []
    overall_avgs = []

    for name in residents_sorted:
        res_df = mtg_data[mtg_data['受評核人員'] == name]
        row_z, row_text = [], []
        for col, _ in avail_dims:
            vals = res_df[col].dropna()
            avg = float(vals.mean()) if len(vals) > 0 else None
            row_z.append(avg if avg is not None else 0)
            row_text.append(f"{avg:.1f}" if avg is not None else "—")
        z_matrix.append(row_z)
        text_matrix.append(row_text)
        overall_avgs.append(sum(v for v in row_z if v > 0) / max(len([v for v in row_z if v > 0]), 1))

    # 按整體均分由低到高排列（進度慢的在上）
    order = sorted(range(len(residents_sorted)), key=lambda i: overall_avgs[i])
    residents_sorted = [residents_sorted[i] for i in order]
    z_matrix   = [z_matrix[i] for i in order]
    text_matrix = [text_matrix[i] for i in order]

    colorscale = [
        [0.0,   '#FF6B6B'],   # 紅（0分）
        [0.4,   '#FFD93D'],   # 黃（2.0分）
        [0.6,   '#FFF3B0'],   # 淺黃（3.0分）
        [0.8,   '#90EE90'],   # 淺綠（4.0分）
        [1.0,   '#27ae60'],   # 綠（5.0分）
    ]

    fig = go.Figure(data=go.Heatmap(
        z=z_matrix,
        x=dim_labels,
        y=residents_sorted,
        text=text_matrix,
        texttemplate='%{text}',
        textfont={"size": 13, "color": "black"},
        colorscale=colorscale,
        zmin=0, zmax=5,
        showscale=True,
        colorbar=dict(title='分數', thickness=14, tickvals=[1,2,3,4,5]),
        hovertemplate='住院醫師：%{y}<br>維度：%{x}<br>均分：%{text}<extra></extra>'
    ))

    fig.update_layout(
        height=max(250, 60 * len(residents_sorted)),
        xaxis=dict(tickfont=dict(size=12), side='top'),
        yaxis=dict(tickfont=dict(size=13)),
        margin=dict(l=100, r=60, t=60, b=30)
    )
    st.plotly_chart(fig, width="stretch", key="ccc_meeting_heatmap")

    # 補充：各住院醫師整體均分排名
    st.caption("📊 各住院醫師會議報告五維度整體均分（近半年）")
    ranking_data = []
    for i, name in enumerate(reversed(residents_sorted)):  # 由高到低
        orig_idx = len(residents_sorted) - 1 - i
        ov = sum(float(v) for v in z_matrix[orig_idx] if v > 0)
        cnt = len([v for v in z_matrix[orig_idx] if v > 0])
        ranking_data.append({'姓名': name, '五維度均分': round(ov / cnt, 2) if cnt else 0})
    st.dataframe(pd.DataFrame(ranking_data), hide_index=True, use_container_width=True)


def show_overall_epa_trend(df):
    """EPA 整體趨勢圖：所有住院醫師的 EPA 月度平均趨勢（每人一條線）"""
    st.subheader("📈 EPA 整體趨勢分析")
    st.caption("各住院醫師的 EPA 可信賴程度月度平均變化（三項EPA平均值）")

    # 篩選 EPA 資料
    epa_data = df[df['評核項目'].astype(str).str.contains('EPA', na=False)].copy() if '評核項目' in df.columns else pd.DataFrame()

    if epa_data.empty or 'EPA可信賴程度_數值' not in epa_data.columns:
        st.info("目前沒有 EPA 評核資料")
        return

    if '受評核人員' not in epa_data.columns or '評核日期' not in epa_data.columns:
        st.info("EPA 資料缺少必要欄位（受評核人員或評核日期）")
        return

    # 將評核日期轉為 datetime 並提取年月
    epa_data['評核日期'] = pd.to_datetime(epa_data['評核日期'], errors='coerce')
    epa_data = epa_data.dropna(subset=['評核日期'])
    epa_data['年月'] = epa_data['評核日期'].dt.to_period('M')

    # 按住院醫師和年月分組，計算該月所有 EPA 項目的平均分（整體平均）
    monthly_avg = epa_data.groupby(['受評核人員', '年月'])['EPA可信賴程度_數值'].mean().reset_index()
    monthly_avg.rename(columns={'EPA可信賴程度_數值': 'EPA整體平均'}, inplace=True)
    monthly_avg['年月'] = monthly_avg['年月'].astype(str)

    if monthly_avg.empty:
        st.info("無足夠的 EPA 時間序列資料")
        return

    # 為每位住院醫師創建一條折線
    fig = go.Figure()
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

    residents = sorted(monthly_avg['受評核人員'].unique())
    for i, resident in enumerate(residents):
        resident_data = monthly_avg[monthly_avg['受評核人員'] == resident].sort_values('年月')
        fig.add_trace(go.Scatter(
            x=resident_data['年月'],
            y=resident_data['EPA整體平均'],
            mode='lines+markers',
            name=resident,
            line=dict(width=2.5, color=colors[i % len(colors)]),
            marker=dict(size=7)
        ))

    # 添加各年級門檻線
    fig.add_hline(y=3.5, line_dash="dash", line_color="red",
                  annotation_text="R3 門檻 (3.5)", annotation_position="top right")
    fig.add_hline(y=3.0, line_dash="dash", line_color="orange",
                  annotation_text="R2 門檻 (3.0)", annotation_position="top right")
    fig.add_hline(y=2.5, line_dash="dash", line_color="green",
                  annotation_text="PGY2/R1 門檻 (2.5)", annotation_position="bottom right")

    fig.update_layout(
        title="所有住院醫師 EPA 整體趨勢比較",
        xaxis_title="時間（年月）",
        yaxis_title="EPA 可信賴程度整體平均（1-5分）",
        yaxis=dict(range=[0, 5.5]),
        height=500,
        hovermode='x unified',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="rgba(0,0,0,0.2)",
            borderwidth=1
        ),
        margin=dict(r=150)  # 為圖例留出右側空間
    )
    st.plotly_chart(fig, width="stretch")


# ═══════════════════════════════════════════════════════
# 原有：資料概覽
# ═══════════════════════════════════════════════════════

def show_data_overview():
    """顯示資料概覽"""
    st.subheader("📊 小兒部住院醫師評核資料概覽")

    # 獲取選擇的科別（僅在 Supabase 模式下生效）
    selected_dept = st.session_state.get('selected_department')
    data_source = st.session_state.get('pediatric_data_source', 'google_sheets')
    department_filter = selected_dept if data_source == 'supabase' else None

    if st.button("🔄 重新載入 Supabase 資料", key="reload_overview"):
        st.session_state.pop('pediatric_data', None)
        st.rerun()

    # 載入資料
    df, sheet_titles = load_pediatric_data(department=department_filter)
    
    if df is not None and not df.empty:
        # 基本統計資訊
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("總評核數", len(df))
        
        with col2:
            unique_patients = len(df['病歷號'].unique()) if '病歷號' in df.columns else 0
            st.metric("評核病歷數", unique_patients)
        
        with col3:
            unique_evaluators = len(df['評核教師'].unique()) if '評核教師' in df.columns else 0
            st.metric("評核教師數", unique_evaluators)
        
        with col4:
            unique_residents = len(df['受評核人員'].unique()) if '受評核人員' in df.columns else 0
            st.metric("受評核人員數", unique_residents)
        
        # 顯示原始資料
        with st.expander("原始資料預覽", expanded=False):
            st.dataframe(df, width="stretch")
        
        # 技能項目完成比例分析已移動至「CCC 總覽」tab 的熱圖矩陣
        st.info("💡 詳細技能完成度分析請見「🏆 CCC 總覽」tab 的技能熱圖矩陣")
        
        # EPA 信賴等級評估概覽（僅當有 EPA 資料時顯示）
        show_epa_overview(df)
    
    else:
        st.warning("無法載入資料，請檢查Google表單連接")

def show_individual_analysis():
    """個別深入分析（Tab 2）：三欄並排儀表盤 → 技能分組進度 → 會議報告回饋 → 詳細記錄"""
    st.subheader("📋 個別住院醫師深入分析")

    # 獲取選擇的科別（僅在 Supabase 模式下生效）
    selected_dept = st.session_state.get('selected_department')
    data_source = st.session_state.get('pediatric_data_source', 'google_sheets')
    department_filter = selected_dept if data_source == 'supabase' else None

    # 讀取資料（優先從 session_state，避免重複 API 調用）
    if 'pediatric_data' in st.session_state and st.session_state['pediatric_data'] is not None:
        df = st.session_state['pediatric_data']
    else:
        df, _ = load_pediatric_data(department=department_filter)
        if df is not None:
            st.session_state['pediatric_data'] = df

    if df is None or df.empty:
        st.warning("無法載入資料")
        return

    if '受評核人員' not in df.columns:
        st.warning("資料中沒有「受評核人員」欄位")
        return

    residents = sorted(df['受評核人員'].unique())

    # ── 根據使用者角色決定可選擇的住院醫師 ──
    user_role = st.session_state.get('role', 'resident')
    user_name = st.session_state.get('user_name')

    if user_role == 'resident':
        # 住院醫師只能選擇自己
        available_residents = [user_name] if user_name in residents else []
        if not available_residents:
            st.warning(f"找不到 {user_name} 的評核資料")
            return
    else:
        # 其他角色可以選擇所有人
        available_residents = residents

    # 從 CCC 總覽卡片點進時的預設值
    default_resident = st.session_state.pop('selected_resident_from_overview', None)
    if default_resident and default_resident in available_residents:
        default_index = available_residents.index(default_resident)
    else:
        default_index = 0

    # 選人 + 重新載入同排
    sel_col, reload_col = st.columns([4, 1])
    with sel_col:
        selected_resident = st.selectbox("選擇受評核人員", available_residents,
                                         index=default_index, label_visibility="collapsed")
    with reload_col:
        if st.button("🔄 重新載入", key="reload_individual", use_container_width=True):
            st.session_state.pop('pediatric_data', None)
            st.rerun()

    if not selected_resident:
        return

    resident_data = df[df['受評核人員'] == selected_resident].copy()

    # ── 基本統計：單行 caption ──
    total_evals = len(resident_data)
    unique_teachers = len(resident_data['評核教師'].unique()) if '評核教師' in resident_data.columns else 0
    date_range = ""
    if '評核日期' in resident_data.columns and not resident_data.empty:
        date_range = f"　{resident_data['評核日期'].min()} ～ {resident_data['評核日期'].max()}"
    st.caption(f"共 {total_evals} 筆評核　教師 {unique_teachers} 位{date_range}")

    # 預先分離三類資料（EPA 與會議報告僅取近半年）
    technical_data = resident_data[resident_data['評核項目'] == '操作技術'].copy() if '評核項目' in resident_data.columns else pd.DataFrame()
    meeting_data   = _filter_recent_6_months(
        resident_data[resident_data['評核項目'] == '會議報告'].copy() if '評核項目' in resident_data.columns else pd.DataFrame()
    )
    epa_data       = _filter_recent_6_months(
        resident_data[resident_data['評核項目'].astype(str).str.contains('EPA', na=False)].copy() if '評核項目' in resident_data.columns else pd.DataFrame()
    )

    # ── 計算達標狀態（供後續各區塊使用）──
    resident_level = _get_resident_level(df, selected_resident)
    th = _get_level_thresholds(resident_level)
    _conn_ind = _get_supabase_conn()
    _pub_count = 0
    if _conn_ind and str(resident_level) == 'R3':
        try:
            _recs = _conn_ind.fetch_research_progress(filters={'resident_name': selected_resident})
            _pub_count = sum(1 for r in (_recs or []) if r.get('current_status') in ('接受', '發表'))
        except Exception:
            pass
    status = calculate_resident_status(resident_data, df, resident_level=resident_level,
                                        research_published=_pub_count)

    # ── 年級 + 整體達標狀態（單行）──
    overall_emoji = _status_emoji(status['overall'])
    overall_label = _status_label(status['overall'])
    st.markdown(f"**`{resident_level}`　{overall_emoji} {overall_label}**")
    st.caption("📅 EPA 及會議報告均分以近半年（180天）資料計算；技能完成進度累計全期記錄")

    # ═══ Section 2：EPA 評核分析 ═══
    st.markdown("### EPA 評核分析")
    st.caption("📅 以近半年（180天）資料為準；各項目需 ≥3 次且均分達標")

    if not epa_data.empty and 'EPA項目' in epa_data.columns:
        epa_display_cols = ['評核日期', '評核教師', 'EPA可信賴程度', 'EPA質性回饋']
        _item_min_disp = status['epa'].get('item_min', 3)
        _item_counts_disp = status['epa'].get('item_counts', {})

        # 短標籤（tab 用）
        short_labels = {
            '門診表現(OPD)':      'OPD',
            '一般病人照護（WARD）': 'WARD',
            '緊急處置（ED, DR）':  'ED/DR',
            '重症照護（PICU, NICU）': 'PICU/NICU',
            '病歷書寫':           '病歷書寫',
        }
        tab_titles = []
        for epa_item in PEDIATRIC_EPA_ITEMS:
            cnt = _item_counts_disp.get(epa_item, 0)
            warn = '' if cnt >= _item_min_disp else ' ⚠️'
            tab_titles.append(f"{short_labels.get(epa_item, epa_item)} ({cnt}){warn}")

        epa_tabs = st.tabs(tab_titles)
        for tab, epa_item in zip(epa_tabs, PEDIATRIC_EPA_ITEMS):
            with tab:
                item_mask = _match_epa_item(epa_data['EPA項目'], epa_item)
                item_df = epa_data[item_mask].copy()
                cnt = len(item_df)
                score_col_epa = 'EPA可信賴程度_數值'
                # 強調顯示均分與次數
                m1, m2, m3 = st.columns([1, 1, 4])
                if not item_df.empty and score_col_epa in item_df.columns:
                    avg_score_epa = item_df[score_col_epa].dropna().mean()
                    threshold_epa = _get_level_thresholds(resident_level)['score_threshold']
                    delta_epa = round(avg_score_epa - threshold_epa, 2) if pd.notna(avg_score_epa) else None
                    m1.metric("均分", f"{avg_score_epa:.2f}", delta=f"{delta_epa:+.2f}" if delta_epa is not None else None)
                else:
                    m1.metric("均分", "—")
                warn_cnt = '' if cnt >= _item_min_disp else ' ⚠️'
                m2.metric("評核次數", f"{cnt} 次{warn_cnt}", help=f"近半年需 ≥{_item_min_disp} 次")
                col_left, col_right = st.columns([1.2, 0.8])
                with col_left:
                    show_epa_item_bar(item_df, epa_item, resident_level)
                with col_right:
                    avail_epa = [c for c in epa_display_cols if c in item_df.columns]
                    if avail_epa and not item_df.empty:
                        st.dataframe(
                            item_df[avail_epa].sort_values('評核日期', ascending=False),
                            width="stretch", hide_index=True, height=280
                        )
                    else:
                        st.caption("尚無此項目評核記錄")

        with st.expander("📈 月度趨勢折線圖（各項目平均）"):
            if '評核日期' in epa_data.columns:
                show_epa_trend_chart(epa_data, selected_resident, resident_level)
            else:
                st.info("缺少日期欄位，無法繪製趨勢圖")
    else:
        st.info("無 EPA 評核記錄")

    # ═══ Section 3：技能分類進度（左右兩欄）═══
    st.markdown("### 技能分類進度")
    with st.expander("📖 可信賴程度分數說明（9 級制，1.5–5.0 分）"):
        st.markdown("""
| 分數 | 可信賴程度 |
|:---:|:---|
| **5.0** | 🟢 學員可對其他資淺的學員進行監督與教學 |
| **4.5** | 🟢 教師不需 on call，事後提供回饋及監督 |
| **4.0** | 🟢 教師 on call 提供監督 |
| **3.6** | 🟢 教師可稍後到場協助，必要時事後確認 |
| **3.3** | 🟡 教師可立即到場協助，事後重點確認 |
| **3.0** | 🟡 教師可立即到場協助，事後逐項確認 |
| **2.5** | 🟡 教師在旁必要時協助 |
| **2.0** | 🔴 教師在旁逐步共同操作 |
| **1.5** | 🔴 允許住院醫師在旁觀察 |

> ≥ 2.5 分（黃燈以上）= 計入技能完成次數 ｜ 綠燈固定 ≥ 3.5 分，黃燈 ≥ 2.5 分
""")
    # 準備技能計數資料
    _sk_data = skill_counts if skill_counts else (
        calculate_skill_counts(technical_data) if not technical_data.empty else {}
    )
    display_cols = ['評核日期', '評核教師', '評核技術項目', '可信賴程度', '操作技術教師回饋']
    avail = [c for c in display_cols if c in technical_data.columns] if not technical_data.empty else []

    # 技能分組用 tabs
    skill_group_names = list(SKILL_GROUPS.keys())
    skill_group_tab_labels = []
    for gname, gskills in SKILL_GROUPS.items():
        if avail and not technical_data.empty and '評核技術項目' in technical_data.columns:
            gmask = technical_data['評核技術項目'].apply(lambda x: any(s in str(x) for s in gskills))
            cnt_g = int(gmask.sum())
        else:
            cnt_g = 0
        skill_group_tab_labels.append(f"{gname} ({cnt_g}筆)")
    skill_group_tabs = st.tabs(skill_group_tab_labels)
    # 以最大分組項目數為基準，固定所有分組圖表高度（與導管插管類對齊）
    _max_skill_items = max(len(g) for g in SKILL_GROUPS.values())
    _fixed_chart_h = max(_max_skill_items * 50, 160)

    for tab_g, (group_name, group_skills) in zip(skill_group_tabs, SKILL_GROUPS.items()):
        with tab_g:
            col_left, col_right = st.columns([1.2, 0.8])
            with col_left:
                if _sk_data:
                    show_grouped_skill_progress(_sk_data, technical_data, resident_level,
                                                target_group=group_name,
                                                chart_height=_fixed_chart_h)
                else:
                    st.info("無操作技術評核記錄")
            with col_right:
                if avail and not technical_data.empty:
                    group_mask = technical_data['評核技術項目'].apply(
                        lambda x: any(skill in str(x) for skill in group_skills)
                    ) if '評核技術項目' in technical_data.columns else pd.Series(False, index=technical_data.index)
                    group_df = technical_data[group_mask][avail].sort_values('評核日期', ascending=False)
                    st.markdown(f"**{group_name} 詳細記錄**（{len(group_df)} 筆）")
                    if not group_df.empty:
                        st.dataframe(group_df, width="stretch", hide_index=True)
                    else:
                        st.caption("尚無此類別評核記錄")
                else:
                    st.markdown(f"**{group_name} 詳細記錄**")
                    st.info("無操作技術評核記錄")

    # ═══ Section 4：會議報告分析（分頁，各會議類型）═══
    st.markdown("### 會議報告分析")
    # 查詢同儕資料（全局）
    resident_level = _get_resident_level(df, selected_resident)
    all_meeting = df[df['評核項目'].astype(str).str.contains('會議報告', na=False)].copy() if '評核項目' in df.columns else pd.DataFrame()
    peer_meeting = all_meeting[
        (all_meeting['受評核人員'] != selected_resident) &
        (all_meeting['評核時級職'].astype(str) == str(resident_level))
    ] if not all_meeting.empty and '受評核人員' in all_meeting.columns and '評核時級職' in all_meeting.columns else pd.DataFrame()

    # 取得所有會議類型
    mtg_types_list = []
    if not meeting_data.empty and '會議名稱' in meeting_data.columns:
        mtg_types_list = sorted(meeting_data['會議名稱'].dropna().unique().tolist())

    # 建立 tab 標籤（全部 + 各類型）
    mtg_all_types = ['全部'] + mtg_types_list
    mtg_tab_labels = []
    for mt in mtg_all_types:
        if mt == '全部':
            mtg_tab_labels.append(f"全部 ({len(meeting_data)})")
        else:
            cnt_mt = int((meeting_data['會議名稱'] == mt).sum()) if not meeting_data.empty and '會議名稱' in meeting_data.columns else 0
            mtg_tab_labels.append(f"{mt} ({cnt_mt})")

    mtg_tabs_list = st.tabs(mtg_tab_labels)
    feedback_col = '會議報告教師回饋'
    mtg_display_cols = ['評核日期', '評核教師', '會議名稱',
                        '內容是否充分', '辯證資料的能力', '口條、呈現方式是否清晰',
                        '是否具開創、建設性的想法', '回答提問是否具邏輯、有條有理',
                        '會議報告教師回饋']

    for mtg_tab, mt in zip(mtg_tabs_list, mtg_all_types):
        with mtg_tab:
            if mt == '全部':
                mt_data = meeting_data
                # 同儕：同一年級、所有會議類型
                mt_peer = peer_meeting
            else:
                mt_data = meeting_data[meeting_data['會議名稱'] == mt].copy() if not meeting_data.empty and '會議名稱' in meeting_data.columns else pd.DataFrame()
                # 同儕：同一年級 & 同一會議類型
                mt_peer = peer_meeting[peer_meeting['會議名稱'] == mt].copy() if not peer_meeting.empty and '會議名稱' in peer_meeting.columns else pd.DataFrame()

            col_left, col_right = st.columns([1.2, 0.8])
            with col_left:
                _mt_safe = re.sub(r'[^A-Za-z0-9\u4e00-\u9fff]', '_', str(mt))
                show_meeting_radar_large(mt_data, mt_peer, selected_resident, resident_level,
                                         chart_key=f"mtg_radar_{_mt_safe}_{selected_resident}")

            with col_right:
                st.markdown("**教師回饋**")
                if not mt_data.empty and feedback_col in mt_data.columns:
                    feedback_rows = mt_data[mt_data[feedback_col].notna() &
                                           (mt_data[feedback_col].astype(str).str.strip() != '')]
                    if '評核日期' in feedback_rows.columns:
                        feedback_rows = feedback_rows.sort_values('評核日期', ascending=False)
                    if not feedback_rows.empty:
                        for _, row in feedback_rows.head(3).iterrows():
                            with st.container(border=True):
                                d = row.get('評核日期', '')
                                if hasattr(d, 'strftime'):
                                    d = d.strftime('%Y-%m-%d')
                                teacher = row.get('評核教師', '')
                                st.caption(f"{d} | {teacher}")
                                st.write(str(row.get(feedback_col, '')))
                        if len(feedback_rows) > 3:
                            with st.expander(f"查看全部回饋（共 {len(feedback_rows)} 筆）"):
                                for _, row in feedback_rows.iloc[3:].iterrows():
                                    with st.container(border=True):
                                        d = row.get('評核日期', '')
                                        if hasattr(d, 'strftime'):
                                            d = d.strftime('%Y-%m-%d')
                                        teacher = row.get('評核教師', '')
                                        st.caption(f"{d} | {teacher}")
                                        st.write(str(row.get(feedback_col, '')))
                    else:
                        st.caption("尚無教師回饋")
                else:
                    st.info("無會議報告評核記錄")

                # 完整記錄表格
                st.caption("**完整評核記錄**")
                if not mt_data.empty:
                    avail_mtg = [c for c in mtg_display_cols if c in mt_data.columns]
                    if avail_mtg:
                        with st.container(border=True, height=250):
                            st.dataframe(
                                mt_data[avail_mtg].sort_values('評核日期', ascending=False),
                                width="stretch", hide_index=True
                            )
                else:
                    st.info("無會議報告評核記錄")

    # ═══ Section 5：研究進度（若有 Supabase 連線）═══
    conn = _get_supabase_conn()
    if conn:
        st.markdown("### 📚 研究進度")
        show_resident_research_progress(conn, selected_resident)


def show_epa_item_bar(item_df, epa_item, resident_level='R1'):
    """單一 EPA 項目：時間折線圖，點以分數著色（紅/黃/綠），顯示趨勢"""
    import plotly.graph_objects as go

    th = _get_level_thresholds(resident_level)
    score_col = 'EPA可信賴程度_數值'

    if item_df.empty or score_col not in item_df.columns or '評核日期' not in item_df.columns:
        st.caption("尚無此項目評核記錄")
        return

    plot_df = item_df[['評核日期', score_col, '評核教師']].dropna(subset=[score_col]).copy()
    plot_df['評核日期'] = pd.to_datetime(plot_df['評核日期'], errors='coerce')
    plot_df = plot_df.dropna(subset=['評核日期']).sort_values('評核日期')

    if plot_df.empty:
        st.caption("尚無此項目評核記錄")
        return

    scores = plot_df[score_col].tolist()
    dates  = plot_df['評核日期'].tolist()
    teachers = plot_df['評核教師'].tolist() if '評核教師' in plot_df.columns else [''] * len(scores)

    # 點的顏色依分數
    point_colors = ['#27ae60' if s >= 3.5 else ('#f39c12' if s >= 2.5 else '#e74c3c') for s in scores]

    avg = sum(scores) / len(scores)
    total = len(scores)

    fig = go.Figure()

    # 連線（淺灰，僅連接趨勢）
    fig.add_trace(go.Scatter(
        x=dates, y=scores,
        mode='lines',
        line=dict(color='#222222', width=1.5),
        showlegend=False,
        hoverinfo='skip',
    ))

    # 個別評分散點（依分數著色）
    for color, label_text in [('#e74c3c', '< 2.5'), ('#f39c12', '2.5~<3.5'), ('#27ae60', '≥ 3.5')]:
        mask = [c == color for c in point_colors]
        if any(mask):
            fig.add_trace(go.Scatter(
                x=[d for d, m in zip(dates, mask) if m],
                y=[s for s, m in zip(scores, mask) if m],
                mode='markers',
                name=label_text,
                marker=dict(color=color, size=11, line=dict(color='white', width=1.5)),
                customdata=[[t] for t, m in zip(teachers, mask) if m],
                hovertemplate='%{x|%Y-%m-%d}　%{y} 分　評核：%{customdata[0]}<extra></extra>',
            ))

    # 門檻水平線
    fig.add_hline(y=th['score_threshold'], line_dash='dash', line_color='red',
                  annotation_text=f"門檻 {th['score_threshold']}",
                  annotation_position='top right')

    fig.update_layout(
        height=280,
        margin=dict(l=5, r=5, t=30, b=5),
        xaxis=dict(title='', tickformat='%m/%d'),
        yaxis=dict(range=[1, 5.3], dtick=1, title=''),
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0,
                    font=dict(size=11)),
    )
    st.plotly_chart(fig, width="stretch", key=f"epa_line_{epa_item}_{resident_level}")


def show_epa_trend_chart(epa_data, resident_name, resident_level='R1'):
    """EPA 信賴程度趨勢圖：X軸=時間（月份），Y軸=各EPA項目的月均分"""
    if 'EPA可信賴程度_數值' not in epa_data.columns:
        st.info("無 EPA 可信賴程度數值資料")
        return

    # 將評核日期轉為 datetime 並提取年月
    epa_data_copy = epa_data.copy()
    epa_data_copy['評核日期'] = pd.to_datetime(epa_data_copy['評核日期'], errors='coerce')
    epa_data_copy = epa_data_copy.dropna(subset=['評核日期'])
    epa_data_copy['年月'] = epa_data_copy['評核日期'].dt.to_period('M')

    # 按年月和EPA項目分組計算平均
    monthly_avg = epa_data_copy.groupby(['年月', 'EPA項目'])['EPA可信賴程度_數值'].mean().reset_index()
    monthly_avg['年月'] = monthly_avg['年月'].astype(str)

    if monthly_avg.empty:
        st.info("無足夠的 EPA 時間序列資料")
        return

    # 為每個 EPA 項目創建一條折線
    fig = go.Figure()
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']  # 最多 6 種顏色

    for i, epa_item in enumerate(PEDIATRIC_EPA_ITEMS):
        item_data = monthly_avg[_match_epa_item(monthly_avg['EPA項目'], epa_item)]
        if not item_data.empty:
            fig.add_trace(go.Scatter(
                x=item_data['年月'],
                y=item_data['EPA可信賴程度_數值'],
                mode='lines+markers',
                name=epa_item,
                line=dict(width=3, color=colors[i % len(colors)]),
                marker=dict(size=8)
            ))

    # 添加該住院醫師年級的門檻線
    th = _get_level_thresholds(resident_level)
    fig.add_hline(y=th['score_threshold'], line_dash="dash", line_color="red",
                  annotation_text=f"{resident_level} 門檻 ({th['score_threshold']})",
                  annotation_position="top right")

    fig.update_layout(
        title=f"{resident_name} EPA 信賴程度月度趨勢（{resident_level}）",
        xaxis_title="時間（年月）",
        yaxis_title="可信賴程度（1-5分）",
        yaxis=dict(range=[0, 5.5]),
        height=450,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig, width="stretch", key=f"epa_trend_{resident_name}")


def show_meeting_radar_large(meeting_data, peer_meeting, resident_name, resident_level, chart_key=None):
    """
    放大版會議報告雷達圖（用於左右兩欄版面的左欄）

    Args:
        meeting_data: 該住院醫師的會議報告資料
        peer_meeting: 同級職同儕的會議報告資料
        resident_name: 住院醫師姓名
        resident_level: 住院醫師級職
        chart_key: plotly_chart 的唯一 key（多次呼叫時需傳入不同值避免 duplicate key）
    """
    radar_text_cols = [
        ('內容是否充分',           '內容充分'),
        ('辯證資料的能力',         '辯證資料'),
        ('口條、呈現方式是否清晰', '口條清晰'),
        ('是否具開創、建設性的想法','開創想法'),
        ('回答提問是否具邏輯、有條有理','邏輯回答'),
    ]

    labels_radar = []
    means_self = []
    means_peer = []

    for text_col, short_label in radar_text_cols:
        num_col = f'{text_col}_數值'
        if num_col in meeting_data.columns:
            m_self = meeting_data[num_col].dropna().mean()
            means_self.append(float(m_self) if pd.notna(m_self) else 0)
            if not peer_meeting.empty and num_col in peer_meeting.columns:
                m_peer = peer_meeting[num_col].dropna().mean()
                means_peer.append(float(m_peer) if pd.notna(m_peer) else 0)
            else:
                means_peer.append(0)
            labels_radar.append(short_label)
        elif text_col in meeting_data.columns:
            s_self = meeting_data[text_col].apply(convert_score_to_numeric).dropna()
            means_self.append(float(s_self.mean()) if len(s_self) > 0 else 0)
            if not peer_meeting.empty and text_col in peer_meeting.columns:
                s_peer = peer_meeting[text_col].apply(convert_score_to_numeric).dropna()
                means_peer.append(float(s_peer.mean()) if len(s_peer) > 0 else 0)
            else:
                means_peer.append(0)
            labels_radar.append(short_label)

    if labels_radar:
        labels_closed = labels_radar + [labels_radar[0]]
        means_self_closed = means_self + [means_self[0]]

        fig_mtg = go.Figure()

        # 同儕平均（灰色）
        if means_peer and any(m > 0 for m in means_peer):
            means_peer_closed = means_peer + [means_peer[0]]
            fig_mtg.add_trace(go.Scatterpolar(
                r=means_peer_closed, theta=labels_closed,
                fill='toself', name=f'同儕平均（{resident_level}）',
                line=dict(color='rgba(128,128,128,1)', width=2),
                fillcolor='rgba(128,128,128,0.12)'
            ))

        # 個人（藍色）
        fig_mtg.add_trace(go.Scatterpolar(
            r=means_self_closed, theta=labels_closed,
            fill='toself', name=resident_name,
            line=dict(color='rgba(65,105,225,1)', width=3),
            fillcolor='rgba(65,105,225,0.25)'
        ))

        fig_mtg.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
            height=450,  # 比儀表板版本更高
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5),
            margin=dict(l=30, r=30, t=30, b=50)
        )

        _chart_key = chart_key if chart_key else f"mtg_radar_large_{resident_name}"
        st.plotly_chart(fig_mtg, width="stretch", key=_chart_key)
    else:
        st.info("無會議報告評核記錄")


def show_statistical_analysis():
    """顯示統計分析"""
    st.subheader("📈 統計分析")
    
    df, _ = load_pediatric_data()
    
    if df is not None and not df.empty:
        # 評分統計分析
        score_columns = ['內容是否充分_數值', '辯證資料的能力_數值', '口條、呈現方式是否清晰_數值',
                        '是否具開創、建設性的想法_數值', '回答提問是否具邏輯、有條有理_數值']
        
        available_scores = [col for col in score_columns if col in df.columns]
        
        if available_scores:
            st.subheader("整體評分統計")
            
            # 計算統計資料
            stats_data = []
            for col in available_scores:
                scores = df[col].dropna()
                if not scores.empty:
                    stats_data.append({
                        '評分項目': col.replace('_數值', ''),
                        '平均分數': scores.mean(),
                        '標準差': scores.std(),
                        '最高分': scores.max(),
                        '最低分': scores.min(),
                        '評分次數': len(scores)
                    })
            
            if stats_data:
                stats_df = pd.DataFrame(stats_data)
                st.dataframe(stats_df, width="stretch")
                
                # 評分分布圖
                fig = go.Figure()
                
                for col in available_scores:
                    scores = df[col].dropna()
                    if not scores.empty:
                        fig.add_trace(go.Box(
                            y=scores,
                            name=col.replace('_數值', ''),
                            boxpoints='all',
                            jitter=0.3,
                            pointpos=-1.8
                        ))
                
                fig.update_layout(
                    title="各項評分分布箱線圖",
                    yaxis_title="評分",
                    xaxis_title="評分項目"
                )
                st.plotly_chart(fig, width="stretch")
        
        # 評核教師分析
        if '評核教師' in df.columns:
            st.subheader("評核教師分析")
            
            teacher_stats = []
            for teacher in df['評核教師'].unique():
                teacher_data = df[df['評核教師'] == teacher]
                
                teacher_stat = {
                    '評核教師': teacher,
                    '評核次數': len(teacher_data)
                }
                
                # 計算平均評分
                for col in available_scores:
                    if col in teacher_data.columns:
                        scores = teacher_data[col].dropna()
                        if not scores.empty:
                            teacher_stat[f'{col.replace("_數值", "")}_平均'] = scores.mean()
                
                teacher_stats.append(teacher_stat)
            
            if teacher_stats:
                teacher_df = pd.DataFrame(teacher_stats)
                st.dataframe(teacher_df, width="stretch")
        
        # 時間分析
        if '評核日期' in df.columns:
            st.subheader("時間分析")
            
            # 每月評核次數
            df['評核月份'] = pd.to_datetime(df['評核日期']).dt.to_period('M')
            monthly_counts = df.groupby('評核月份').size().reset_index(name='評核次數')
            monthly_counts['評核月份'] = monthly_counts['評核月份'].astype(str)
            
            fig = px.bar(
                monthly_counts,
                x='評核月份',
                y='評核次數',
                title="每月評核次數"
            )
            st.plotly_chart(fig, width="stretch")
    
    else:
        st.warning("無法載入資料")


def _show_threshold_settings_ui():
    """CCC 門檻標準（依年級分級，唯讀展示）"""
    st.markdown("#### 各年級達標標準")
    st.markdown("判定方式：**二級制（達標 / 未達標）**，三維度中任一未達標即為整體未達標。")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**會議報告 & EPA（均分門檻）**")
        st.markdown(
            "| 年級 | 達標門檻 |\n|------|--------|\n"
            "| PGY2 / R1 | ≥ 2.5 分 |\n"
            "| R2 | ≥ 3.0 分 |\n"
            "| R3 | ≥ 3.5 分 |"
        )
    with col2:
        st.markdown("**操作技術（達標項目佔比，≥2.5 分算完成）**")
        st.markdown(
            "| 年級 | 達標比例 |\n|------|--------|\n"
            "| PGY2 / R1 | ≥ 30% |\n"
            "| R2 | ≥ 60% |\n"
            "| R3 | ≥ 100% |"
        )

    st.info("門檻標準定義於程式碼中（LEVEL_THRESHOLDS），如需調整請聯繫系統管理員。")


def show_data_management():
    """顯示資料管理（含門檻設定 UI）"""
    st.subheader("⚙️ 資料管理")

    if st.button("🔄 重新載入 Supabase 資料", key="reload_management"):
        st.session_state.pop('pediatric_data', None)
        st.rerun()

    # ─── 門檻設定 UI（管理員專用）───
    from modules.auth import check_permission
    user_role = st.session_state.get('role', 'resident')
    if check_permission(user_role, 'can_manage_users'):
        with st.expander("🎯 CCC 門檻設定", expanded=False):
            _show_threshold_settings_ui()
        st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📥 資料匯入")
        if st.button("重新載入Google表單資料", type="primary"):
            with st.spinner("正在載入資料..."):
                # 獲取選擇的科別（僅在 Supabase 模式下生效）
                selected_dept = st.session_state.get('selected_department')
                data_source = st.session_state.get('pediatric_data_source', 'google_sheets')
                department_filter = selected_dept if data_source == 'supabase' else None

                df, sheet_titles = load_pediatric_data(department=department_filter)
                if df is not None:
                    st.info("資料載入成功！")
                    st.session_state['pediatric_data'] = df
                else:
                    st.error("資料載入失敗")
    
    with col2:
        st.markdown("### 📤 資料匯出")
        if 'pediatric_data' in st.session_state:
            df = st.session_state['pediatric_data']
            
            # 轉換為CSV
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            
            st.download_button(
                label="下載CSV檔案",
                data=csv,
                file_name=f"小兒部評核資料_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("請先載入資料")
    
    # 資料驗證
    st.markdown("### 🔍 資料驗證")
    if 'pediatric_data' in st.session_state:
        df = st.session_state['pediatric_data']
        
        # 檢查缺失值
        missing_data = df.isnull().sum()
        missing_data = missing_data[missing_data > 0]
        
        if not missing_data.empty:
            st.warning("發現缺失資料：")
            st.dataframe(missing_data.to_frame('缺失數量'))
        else:
            st.info("沒有發現缺失資料")
        
        # 檢查重複資料
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            st.warning(f"發現 {duplicates} 筆重複資料")
        else:
            st.info("沒有發現重複資料")
    
    # 資料統計摘要
    st.markdown("### 📊 資料統計摘要")
    if 'pediatric_data' in st.session_state:
        df = st.session_state['pediatric_data']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("總記錄數", len(df))
        
        with col2:
            st.metric("欄位數", len(df.columns))
        
        with col3:
            if '評核日期' in df.columns:
                date_range = (pd.to_datetime(df['評核日期']).max() - pd.to_datetime(df['評核日期']).min()).days
                st.metric("資料時間跨度", f"{date_range} 天")
            else:
                st.metric("資料時間跨度", "N/A")

def show_skill_tracking():
    """顯示技能追蹤功能"""
    st.subheader("🎯 小兒科住院醫師技能追蹤")

    # 獲取選擇的科別（僅在 Supabase 模式下生效）
    selected_dept = st.session_state.get('selected_department')
    data_source = st.session_state.get('pediatric_data_source', 'google_sheets')
    department_filter = selected_dept if data_source == 'supabase' else None

    # 載入資料
    df, _ = load_pediatric_data(department=department_filter)
    
    if df is not None and not df.empty:
        # 選擇受評核人員
        if '受評核人員' in df.columns:
            residents = sorted(df['受評核人員'].unique())
            selected_resident = st.selectbox("選擇受評核人員", residents, key="skill_tracking_resident")
            
            if selected_resident:
                # 篩選該人員的資料
                resident_data = df[df['受評核人員'] == selected_resident]
                
                st.subheader(f"技能追蹤 - {selected_resident}")
                
                # 計算技能完成次數
                skill_counts = calculate_skill_counts(resident_data)
                
                # 顯示技能完成狀況
                show_skill_progress(skill_counts, selected_resident)
                
                # 顯示詳細技能記錄
                show_skill_details(resident_data, selected_resident)
                
                # 技能完成度統計
                show_skill_completion_stats(skill_counts)
    
    else:
        st.warning("無法載入資料")

def calculate_skill_counts(resident_data):
    """計算住院醫師各項技能完成次數（可信賴程度 ≥2.5 才列入完成）"""
    skill_counts = {}

    # 從評核技術項目欄位中提取技能資訊
    if '評核技術項目' in resident_data.columns:
        technical_items = resident_data['評核技術項目'].dropna()

        for skill in PEDIATRIC_SKILL_REQUIREMENTS.keys():
            # 計算該技能出現的次數（只計算可信賴程度 ≥2.5 的記錄）
            count = 0
            for idx, item in technical_items.items():
                if skill in str(item):
                    # 檢查該記錄的可信賴程度
                    if '可信賴程度_數值' in resident_data.columns:
                        reliability_score = resident_data.loc[idx, '可信賴程度_數值']
                        # 可信賴程度 ≥2.5（黃燈以上）才計入完成
                        if pd.notna(reliability_score) and reliability_score >= 2.5:
                            count += 1
                    else:
                        count += 1
            
            req = PEDIATRIC_SKILL_REQUIREMENTS[skill]['minimum']
            skill_counts[skill] = {
                'completed': count,
                'required': req,
                'capped': min(count, req) if req > 0 else (1 if count > 0 else 0),
                'description': PEDIATRIC_SKILL_REQUIREMENTS[skill]['description'],
                'progress': min(count / req * 100, 100) if req > 0 else (100.0 if count > 0 else 0.0)
            }
    
    return skill_counts

def calculate_resident_status(resident_data, full_df, resident_level='R1', research_published=0):
    """計算住院醫師的達標狀態（依年級分級門檻）
    判定維度：技能完成進度、EPA均分、會議報告均分
    R3 額外加入：文章發表（≥1篇）
    取所有維度中最差者為 overall 狀態（二級制：PASS / FAIL）
    無資料的維度視為 FAIL
    """
    th = _get_level_thresholds(resident_level)
    score_threshold = th['score_threshold']
    skill_pass_rate = th['skill_pass_rate']

    def _pass_fail(value, threshold):
        if value is None:
            return 'FAIL'
        return 'PASS' if value >= threshold else 'FAIL'

    # ── 維度 1：技能完成進度（各技能有效次數 / 固定分母40次）──
    # 每技能有效次數上限為該技能最低要求次數（超過不重複計算）
    TOTAL_REQUIRED_SESSIONS = 40  # 所有技能最低次數加總固定值
    technical_data = resident_data[resident_data['評核項目'] == '操作技術'] if '評核項目' in resident_data.columns else pd.DataFrame()
    skill_counts = calculate_skill_counts(technical_data) if not technical_data.empty else {}
    total_skills = len(PEDIATRIC_SKILL_REQUIREMENTS)
    completed_skills = sum(
        1 for d in skill_counts.values()
        if (d['required'] > 0 and d['completed'] >= d['required'])
        or (d['required'] == 0 and d['completed'] > 0)
    )
    total_required_sessions = TOTAL_REQUIRED_SESSIONS
    completed_sessions = sum(d['capped'] for d in skill_counts.values()) if skill_counts else 0
    tech_rate = completed_sessions / TOTAL_REQUIRED_SESSIONS * 100
    tech_status = _pass_fail(tech_rate, skill_pass_rate)

    # ── 維度 2：EPA 均分（近半年）+ 各項目次數（各 ≥3 次）──
    EPA_ITEM_MIN = 3  # 每項目近半年最低評核次數
    epa_data_all = resident_data[resident_data['評核項目'].astype(str).str.contains('EPA', na=False)] if '評核項目' in resident_data.columns else pd.DataFrame()
    epa_data = _filter_recent_6_months(epa_data_all)
    if not epa_data.empty and 'EPA可信賴程度_數值' in epa_data.columns:
        epa_avg = epa_data['EPA可信賴程度_數值'].dropna().mean()
        epa_avg = float(epa_avg) if pd.notna(epa_avg) else None
    else:
        epa_avg = None
    # 計算各項目近半年次數
    epa_item_counts = {}
    if not epa_data.empty and 'EPA項目' in epa_data.columns:
        for item in PEDIATRIC_EPA_ITEMS:
            epa_item_counts[item] = int(epa_data[_match_epa_item(epa_data['EPA項目'], item)].shape[0])
    else:
        epa_item_counts = {item: 0 for item in PEDIATRIC_EPA_ITEMS}
    all_items_enough = all(c >= EPA_ITEM_MIN for c in epa_item_counts.values())
    # 均分達標 且 所有項目各 ≥3 次，才算 EPA PASS
    if epa_avg is not None and epa_avg >= score_threshold and all_items_enough:
        epa_status = 'PASS'
    else:
        epa_status = 'FAIL'

    # ── 維度 3：會議報告均分（近半年）──
    meeting_data = _filter_recent_6_months(
        resident_data[resident_data['評核項目'] == '會議報告'] if '評核項目' in resident_data.columns else pd.DataFrame()
    )
    meeting_score_cols = ['內容是否充分_數值', '辯證資料的能力_數值', '口條、呈現方式是否清晰_數值',
                          '是否具開創、建設性的想法_數值', '回答提問是否具邏輯、有條有理_數值']
    available_score_cols = [c for c in meeting_score_cols if c in meeting_data.columns] if not meeting_data.empty else []
    if available_score_cols:
        all_meeting_scores = meeting_data[available_score_cols].values.flatten()
        valid = all_meeting_scores[~pd.isna(all_meeting_scores)]
        meeting_avg = float(valid.mean()) if len(valid) > 0 else None
    else:
        meeting_avg = None
    meeting_status = _pass_fail(meeting_avg, score_threshold)

    # ── 維度 4（R3 專屬）：文章發表（至少 1 篇接受/發表）──
    if str(resident_level) == 'R3':
        research_status = 'PASS' if research_published >= 1 else 'FAIL'
    else:
        research_status = None  # 非 R3 不列入判斷

    # ── overall：所有適用維度中有任一 FAIL 則 FAIL ──
    dimensions = [tech_status, epa_status, meeting_status]
    if research_status is not None:
        dimensions.append(research_status)
    overall = 'PASS' if all(s == 'PASS' for s in dimensions) else 'FAIL'

    return {
        'overall': overall,
        'thresholds': th,
        'technical': {'status': tech_status, 'pass_rate': tech_rate,
                      'completed_skills': completed_skills, 'total_skills': total_skills,
                      'completed_sessions': completed_sessions, 'total_required_sessions': total_required_sessions},
        'epa':       {'status': epa_status, 'avg_score': epa_avg,
                      'item_counts': epa_item_counts, 'item_min': EPA_ITEM_MIN},
        'meeting':   {'status': meeting_status, 'avg_score': meeting_avg},
        'research':  {'status': research_status, 'published_count': research_published},
    }

def show_skill_progress(skill_counts, resident_name):
    """顯示技能進度條"""
    st.subheader("技能完成進度")
    
    # 創建進度條
    for skill, data in skill_counts.items():
        # 技能標題區域
        st.markdown(f"### {skill}")
        st.caption(data['description'])
        
        # 完成度顯示區域
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            # 進度條
            progress = data['progress'] / 100
            st.progress(progress)
            
            # 狀態指示
            if data['completed'] >= data['required']:
                st.success(f"✅ 已完成 ({data['completed']}/{data['required']})")
            else:
                remaining = data['required'] - data['completed']
                st.warning(f"⚠️ 還需 {remaining} 次 ({data['completed']}/{data['required']})")
        
        with col2:
            st.metric("已完成", data['completed'])
        
        with col3:
            st.metric("需完成", data['required'])
        
        # 添加分隔線
        st.markdown("---")

def show_grouped_skill_progress(skill_counts, technical_data=None, resident_level='R1', target_group=None, chart_height=None):
    """技能分組堆疊長條圖：固定著色（綠≥3.5 / 黃≥2.5 / 紅<2.5），按三組呈現
    target_group: 若指定，只渲染該分組名稱（用於左右對齊佈局）
    chart_height:  指定固定圖表高度（用於跨分頁對齊）"""
    import plotly.graph_objects as go
    green_threshold = 3.5  # 固定門檻，不隨年級變動

    # 從 technical_data 統計每項技能的分數分佈
    def _score_distribution(skill_name):
        """回傳 (red_count, yellow_count, green_count, no_score_count)"""
        red = yellow = green = no_score = 0
        if technical_data is None or technical_data.empty:
            return red, yellow, green, no_score
        if '評核技術項目' not in technical_data.columns:
            return red, yellow, green, no_score

        for idx, item in technical_data['評核技術項目'].dropna().items():
            if skill_name in str(item):
                score = None
                if '可信賴程度_數值' in technical_data.columns:
                    score = technical_data.loc[idx, '可信賴程度_數值']
                if pd.notna(score):
                    if score >= green_threshold:
                        green += 1
                    elif score >= 2.5:
                        yellow += 1
                    else:
                        red += 1
                else:
                    no_score += 1
        return red, yellow, green, no_score

    for group_name, group_skills in SKILL_GROUPS.items():
        if target_group is not None and group_name != target_group:
            continue
        st.markdown(f"**{group_name}**")

        skills_list = []
        red_vals = []
        yellow_vals = []
        green_vals = []
        required_vals = []

        for skill in group_skills:
            data = skill_counts.get(skill)
            required = data['required'] if data else PEDIATRIC_SKILL_REQUIREMENTS.get(skill, {}).get('minimum', 1)

            r, y, g, ns = _score_distribution(skill)
            total = r + y + g + ns

            skills_list.append(skill)
            red_vals.append(r)
            yellow_vals.append(y)
            green_vals.append(g)
            required_vals.append(required)

        # 反轉使第一項在最上方
        skills_list = skills_list[::-1]
        red_vals = red_vals[::-1]
        yellow_vals = yellow_vals[::-1]
        green_vals = green_vals[::-1]
        required_vals = required_vals[::-1]

        # 產生標籤文字（技能名稱 + 完成/需求，黃燈以上才算完成）
        text_labels = []
        for i, skill in enumerate(skills_list):
            completed = yellow_vals[i] + green_vals[i]  # ≥2.5 才算完成
            req = required_vals[i]
            if req == 0:
                # 僅記錄項目（APLS/NRP）
                done = "✅ 已記錄" if completed > 0 else "僅記錄"
                text_labels.append(f"{skill}  ({completed}次) {done}")
            else:
                done = "✅" if completed >= req else f"還需{req - completed}次"
                text_labels.append(f"{skill}  ({completed}/{req}) {done}")

        fig = go.Figure()

        # 紅色：< 2.5 分（未達標，不計入完成）
        fig.add_trace(go.Bar(
            y=text_labels, x=red_vals, name='< 2.5 分',
            orientation='h',
            marker_color='#e74c3c',
            hovertemplate='%{y}<br><2.5分: %{x}次<extra></extra>'
        ))
        # 黃色：≥2.5 但 <3.5
        fig.add_trace(go.Bar(
            y=text_labels, x=yellow_vals, name='2.5~<3.5 分',
            orientation='h',
            marker_color='#f39c12',
            hovertemplate='%{y}<br>黃燈: %{x}次<extra></extra>'
        ))
        # 綠色：≥ 3.5
        fig.add_trace(go.Bar(
            y=text_labels, x=green_vals, name='≥ 3.5 分',
            orientation='h',
            marker_color='#27ae60',
            hovertemplate='%{y}<br>綠燈: %{x}次<extra></extra>'
        ))

        # X 軸上限
        max_total = max((r + y + g for r, y, g in zip(red_vals, yellow_vals, green_vals)), default=0)
        max_req = max(required_vals) if required_vals else 1
        x_max = max(max_total, max_req) + 1

        _h = chart_height if chart_height is not None else max(len(skills_list) * 45, 150)
        fig.update_layout(
            barmode='stack',
            height=_h,
            margin=dict(l=10, r=10, t=5, b=5),
            xaxis=dict(title='評核次數', dtick=1, range=[0, x_max]),
            yaxis=dict(automargin=True),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
            showlegend=True,
        )

        st.plotly_chart(fig, width="stretch", key=f"skill_bar_{group_name}")
        st.divider()

def show_skill_details(resident_data, resident_name):
    """顯示詳細技能記錄"""
    st.subheader("詳細技能記錄")
    
    # 篩選包含技能評核的記錄
    skill_records = resident_data[resident_data['評核技術項目'].notna()].copy()
    
    if not skill_records.empty:
        # 選擇要顯示的欄位
        display_columns = ['評核日期', '評核教師', '評核技術項目', '可信賴程度', '操作技術教師回饋']
        
        # 確保所有欄位都存在
        available_columns = [col for col in display_columns if col in skill_records.columns]
        
        if available_columns:
            # 按日期排序
            if '評核日期' in available_columns:
                skill_records = skill_records.sort_values('評核日期', ascending=False)
            
            st.dataframe(skill_records[available_columns], width="stretch")
        else:
            st.warning("沒有可用的技能記錄欄位")
    else:
        st.info("該住院醫師目前沒有技能評核記錄")

def show_skill_completion_stats(skill_counts):
    """顯示技能完成度統計"""
    st.subheader("技能完成度統計")
    
    # 計算統計資料（minimum=0 的項目需至少1筆記錄才算完成）
    total_skills = len(skill_counts)
    completed_skills = sum(
        1 for data in skill_counts.values()
        if (data['required'] > 0 and data['completed'] >= data['required'])
        or (data['required'] == 0 and data['completed'] > 0)
    )
    in_progress_skills = total_skills - completed_skills
    
    # 顯示統計卡片
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("總技能數", total_skills)
    
    with col2:
        st.metric("已完成技能", completed_skills)
    
    with col3:
        st.metric("進行中技能", in_progress_skills)
    
    with col4:
        completion_rate = (completed_skills / total_skills * 100) if total_skills > 0 else 0
        st.metric("完成率", f"{completion_rate:.1f}%")
    
    # 技能完成度圖表
    if skill_counts:
        # 準備圖表資料
        skills = list(skill_counts.keys())
        completed = [data['completed'] for data in skill_counts.values()]
        required = [data['required'] for data in skill_counts.values()]
        
        # 創建長條圖
        fig = go.Figure()
        
        # 已完成次數
        fig.add_trace(go.Bar(
            name='已完成',
            x=skills,
            y=completed,
            marker_color='lightgreen'
        ))
        
        # 需要完成次數
        fig.add_trace(go.Bar(
            name='需要完成',
            x=skills,
            y=required,
            marker_color='lightcoral',
            opacity=0.7
        ))
        
        fig.update_layout(
            title="技能完成次數對比",
            xaxis_title="技能項目",
            yaxis_title="次數",
            barmode='group',
            height=500,
            xaxis_tickangle=-45
        )
        
        st.plotly_chart(fig, width="stretch")
        
        # 技能完成度圓餅圖
        fig_pie = go.Figure(data=[go.Pie(
            labels=['已完成', '進行中'],
            values=[completed_skills, in_progress_skills],
            marker_colors=['lightgreen', 'lightcoral']
        )])
        
        fig_pie.update_layout(
            title="技能完成狀況分布",
            height=400
        )
        
        st.plotly_chart(fig_pie, width="stretch")

def show_skill_requirements():
    """顯示技能要求清單"""
    st.subheader("小兒科住院醫師技能基本要求")
    
    # 創建技能要求表格
    skill_data = []
    for skill, data in PEDIATRIC_SKILL_REQUIREMENTS.items():
        skill_data.append({
            '技能項目': skill,
            '最少次數': data['minimum'],
            '說明': data['description']
        })
    
    skill_df = pd.DataFrame(skill_data)
    st.dataframe(skill_df, width="stretch")
    
    # 技能分類統計
    st.subheader("技能分類統計")
    
    # 按最少次數分類
    category_stats = skill_df.groupby('最少次數').size().reset_index(name='技能數量')
    category_stats['分類'] = category_stats['最少次數'].apply(
        lambda x: f"需要{x}次" if x == 1 else f"需要{x}次"
    )
    
    fig = px.pie(
        category_stats,
        values='技能數量',
        names='分類',
        title="技能要求次數分布"
    )
    
    st.plotly_chart(fig, width="stretch")

def create_individual_radar_chart(resident_data, resident_name, full_df):
    """創建個別住院醫師評核分數雷達圖"""
    try:
        # 檢查是否有評核技術項目資料
        if '評核技術項目' not in resident_data.columns:
            st.info("該住院醫師目前沒有評核技術項目資料")
            return
        
        # 獲取住院醫師的級職
        resident_level = None
        if '評核時級職' in resident_data.columns:
            level_values = resident_data['評核時級職'].dropna().unique()
            if len(level_values) > 0:
                resident_level = level_values[0]  # 取第一個級職
        
        # 獲取所有技能項目
        all_skills = list(PEDIATRIC_SKILL_REQUIREMENTS.keys())
        
        # 計算自己的技能分數（基於可信賴程度）
        own_scores = {}
        for skill in all_skills:
            # 篩選該技能的評核記錄
            skill_data = resident_data[resident_data['評核技術項目'].str.contains(skill, na=False)]
            
            if not skill_data.empty and '可信賴程度_數值' in skill_data.columns:
                # 計算該技能的平均可信賴程度
                scores = skill_data['可信賴程度_數值'].dropna()
                if not scores.empty:
                    own_scores[skill] = scores.mean()
                else:
                    own_scores[skill] = 1.0  # 預設1分
            else:
                own_scores[skill] = 1.0  # 預設1分
        
        # 計算同級職的平均分數
        level_avg_scores = {}
        if resident_level and '評核時級職' in full_df.columns:
            level_data = full_df[full_df['評核時級職'] == resident_level]
            
            for skill in all_skills:
                # 篩選該技能的評核記錄
                skill_data = level_data[level_data['評核技術項目'].str.contains(skill, na=False)]
                
                if not skill_data.empty and '可信賴程度_數值' in skill_data.columns:
                    # 計算該技能的平均可信賴程度
                    scores = skill_data['可信賴程度_數值'].dropna()
                    if not scores.empty:
                        level_avg_scores[skill] = scores.mean()
                    else:
                        level_avg_scores[skill] = 1.0  # 預設1分
                else:
                    level_avg_scores[skill] = 1.0  # 預設1分
        
        # 準備雷達圖資料
        categories = all_skills
        own_values = [own_scores[skill] for skill in all_skills]
        level_values = [level_avg_scores.get(skill, 1.0) for skill in all_skills]
        
        # 確保資料是閉合的
        categories_closed = categories + [categories[0]]
        own_values_closed = own_values + [own_values[0]]
        level_values_closed = level_values + [level_values[0]]
        
        # 創建雷達圖
        fig = go.Figure()
        
        # 先畫同級職平均（深灰色）
        if level_avg_scores:
            fig.add_trace(go.Scatterpolar(
                r=level_values_closed,
                theta=categories_closed,
                name=f'{resident_level}級職平均',
                line=dict(color='rgba(128, 128, 128, 1)', width=2),
                fill='none'
            ))
        
        # 後畫住院醫師本人（紅色）
        fig.add_trace(go.Scatterpolar(
            r=own_values_closed,
            theta=categories_closed,
            name=resident_name,
            fill='toself',
            fillcolor='rgba(255, 0, 0, 0.2)',
            line=dict(color='rgba(255, 0, 0, 1)', width=2)
        ))
        
        # 更新布局
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 5]  # 使用5分制
                )
            ),
            title=f"{resident_name} 評核分數雷達圖",
            height=500,
            showlegend=True,
            legend=dict(
                orientation="v",  # 垂直排列
                yanchor="top",
                y=1.0,
                xanchor="left",
                x=1.02,  # 放在右邊
                bgcolor="rgba(255,255,255,0.8)",  # 半透明白色背景
                bordercolor="rgba(0,0,0,0.2)",
                borderwidth=1
            ),
            margin=dict(r=120)  # 增加右邊距，為圖例留出空間
        )
        
        # 顯示雷達圖
        st.plotly_chart(fig, width="stretch")
        
        # 顯示分數對比表格（預設收起）
        if level_avg_scores:
            with st.expander("📊 技能分數對比表", expanded=False):
                comparison_data = []
                for skill in categories:
                    comparison_data.append({
                        '技能項目': skill,
                        f'{resident_name}分數': f"{own_scores[skill]:.2f}",
                        f'{resident_level}級職平均': f"{level_avg_scores[skill]:.2f}",
                        '差異': f"{own_scores[skill] - level_avg_scores[skill]:+.2f}"
                    })
                
                comparison_df = pd.DataFrame(comparison_data)
                st.dataframe(comparison_df, width="stretch")
        
    except Exception as e:
        st.error(f"創建雷達圖時發生錯誤：{str(e)}")


def show_resident_research_progress(conn, resident_name):
    """
    顯示個別住院醫師的研究進度（個人分析頁面）
    """
    try:
        research_records = conn.fetch_research_progress(filters={'resident_name': resident_name})

        if not research_records:
            st.info(f"**{resident_name}** 尚未登記研究進度")
            return

        # 統計
        status_counts = {}
        for rec in research_records:
            status = rec.get('current_status', '構思中')
            status_counts[status] = status_counts.get(status, 0) + 1

        # 第一排：統計卡片
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💡 構思中", status_counts.get('構思中', 0))
        with col2:
            st.metric("✍️ 撰寫中", status_counts.get('撰寫中', 0))
        with col3:
            st.metric("📤 投稿中", status_counts.get('投稿中', 0))
        with col4:
            st.metric("✅ 接受", status_counts.get('接受', 0))

        # 第二排：研究清單（表格）
        display_data = []
        for rec in research_records:
            status_emoji = {'構思中': '💡', '撰寫中': '✍️', '投稿中': '📤', '接受': '✅'}
            display_data.append({
                '研究名稱': rec.get('research_title', ''),
                '類型': rec.get('research_type', ''),
                '指導老師': rec.get('supervisor_name', '—'),
                '進度': f"{status_emoji.get(rec.get('current_status', ''), '📝')} {rec.get('current_status', '')}",
                '更新時間': rec.get('updated_at', '')[:10] if rec.get('updated_at') else ''
            })

        if display_data:
            df = pd.DataFrame(display_data)
            st.dataframe(df, width="stretch", hide_index=True)

            # 詳細檢視（可展開）
            with st.expander("📝 詳細進度說明", expanded=False):
                for i, rec in enumerate(research_records):
                    st.markdown(f"**{i+1}. {rec.get('research_title', '')}**")
                    st.caption(f"類型：{rec.get('research_type', '')} ｜ 指導老師：{rec.get('supervisor_name', '—')}")
                    if rec.get('progress_notes'):
                        st.text_area("進度說明", rec['progress_notes'], height=80, key=f"progress_{i}", disabled=True)
                    if rec.get('challenges'):
                        st.text_area("遭遇困難", rec['challenges'], height=60, key=f"challenges_{i}", disabled=True)
                    if rec.get('next_steps'):
                        st.text_area("下一步計畫", rec['next_steps'], height=60, key=f"next_{i}", disabled=True)
                    st.divider()

    except Exception as e:
        st.warning(f"載入研究進度時發生錯誤：{str(e)}")


def show_resident_learning_reflections(conn, resident_name):
    """
    顯示個別住院醫師的學習反思記錄（個人分析頁面）
    """
    try:
        # 只載入非私人記錄（若要顯示本人的私人記錄，需判斷當前使用者）
        reflections = conn.fetch_learning_reflections(
            filters={'resident_name': resident_name, 'include_private': False}
        )

        if not reflections:
            st.info(f"**{resident_name}** 尚未記錄學習反思")
            return

        # 統計
        type_counts = {}
        for rec in reflections:
            rtype = rec.get('reflection_type', '其他')
            type_counts[rtype] = type_counts.get(rtype, 0) + 1

        # 第一排：類型統計
        st.caption(f"共 **{len(reflections)}** 筆反思記錄")
        cols = st.columns(min(5, len(type_counts)))
        for i, (rtype, count) in enumerate(type_counts.items()):
            with cols[i % len(cols)]:
                st.metric(rtype, count)

        st.markdown("---")

        # 第二排：反思清單（最新 10 筆）
        st.caption("最新 10 筆反思記錄")
        recent = reflections[:10]

        display_data = []
        for rec in recent:
            display_data.append({
                '日期': rec.get('reflection_date', ''),
                '標題': rec.get('reflection_title', ''),
                '類型': rec.get('reflection_type', ''),
                '相關 EPA': rec.get('related_epa', '—'),
                '相關技能': rec.get('related_skill', '—'),
            })

        if display_data:
            df = pd.DataFrame(display_data)
            st.dataframe(df, width="stretch", hide_index=True)

            # 詳細檢視（Gibbs 反思循環內容）
            with st.expander("📖 詳細反思內容", expanded=False):
                for i, rec in enumerate(recent):
                    st.markdown(f"### {i+1}. {rec.get('reflection_title', '')}")
                    st.caption(f"日期：{rec.get('reflection_date', '')} ｜ 類型：{rec.get('reflection_type', '')}")

                    if rec.get('situation_description'):
                        st.markdown("**1️⃣ 情境描述**")
                        st.write(rec['situation_description'])
                    if rec.get('thoughts_and_feelings'):
                        st.markdown("**2️⃣ 想法與感受**")
                        st.write(rec['thoughts_and_feelings'])
                    if rec.get('evaluation'):
                        st.markdown("**3️⃣ 評估與分析**")
                        st.write(rec['evaluation'])
                    if rec.get('action_plan'):
                        st.markdown("**4️⃣ 行動計畫**")
                        st.write(rec['action_plan'])
                    if rec.get('learning_outcomes'):
                        st.markdown("**5️⃣ 學習成果**")
                        st.write(rec['learning_outcomes'])

                    if rec.get('tags'):
                        st.caption(f"🏷️ 標籤：{', '.join(rec['tags'])}")

                    st.divider()

    except Exception as e:
        st.warning(f"載入學習反思時發生錯誤：{str(e)}")


def show_research_progress_overview(conn, residents):
    """
    研究進度總覽區塊（CCC 總覽頁面）：泳道圖呈現所有住院醫師的研究進度
    """
    st.subheader("📚 住院醫師研究進度泳道圖")

    STAGES = ['構思中', '撰寫中', '投稿中', '接受', '發表']
    STAGE_POS = {s: i for i, s in enumerate(STAGES)}
    STAGE_COLORS = {
        '構思中': '#74B9FF',
        '撰寫中': '#A29BFE',
        '投稿中': '#FDCB6E',
        '接受':   '#55EFC4',
        '發表':   '#27AE60',
    }
    STATUS_EMOJI = {'構思中': '💡', '撰寫中': '✍️', '投稿中': '📤', '接受': '✅', '發表': '🏆'}

    try:
        all_research = conn.fetch_research_progress()
        if not all_research:
            st.info("目前尚無住院醫師登記研究進度")
            return

        # 統計摘要
        status_counts = {s: 0 for s in STAGES}
        for rec in all_research:
            s = rec.get('current_status', '構思中')
            if s in status_counts:
                status_counts[s] += 1

        summary_cols = st.columns(len(STAGES))
        for i, s in enumerate(STAGES):
            summary_cols[i].metric(f"{STATUS_EMOJI[s]} {s}", status_counts[s])

        st.markdown("---")

        # 整理每位住院醫師的研究項目
        resident_papers = {}
        for rec in all_research:
            name = rec.get('resident_name', '未知')
            resident_papers.setdefault(name, []).append(rec)

        sorted_residents = sorted(resident_papers.keys())

        # ── 泳道圖（Plotly Scatter，橫向進度條樣式）──
        fig = go.Figure()

        # X 軸網格線（每個 stage 位置）
        for i in range(len(STAGES)):
            fig.add_vline(x=i, line_dash='dot',
                          line_color='rgba(180,180,180,0.5)', line_width=1)

        # 為每個圖例項目只加一次（legend 去重）
        added_legend = set()

        # 逐住院醫師、逐研究項目建立泳道
        total_rows = sum(len(papers) for papers in resident_papers.values())
        y_tick_vals = []
        y_tick_texts = []
        y_separator_positions = []

        y = total_rows - 1  # 從上往下畫
        for resident in sorted_residents:
            papers = resident_papers[resident]
            resident_start_y = y

            for j, paper in enumerate(papers):
                status = paper.get('current_status', '構思中')
                stage_x = STAGE_POS.get(status, 0)
                color = STAGE_COLORS.get(status, '#95A5A6')
                title = paper.get('research_title', '未命名')
                title_short = title[:20] + '…' if len(title) > 20 else title
                supervisor = paper.get('supervisor_name', '—')
                res_type = paper.get('research_type', '—')

                # 底部灰色完整進度條背景
                fig.add_trace(go.Scatter(
                    x=[-0.4, len(STAGES) - 0.6],
                    y=[y, y],
                    mode='lines',
                    line=dict(color='rgba(220,220,220,0.6)', width=18),
                    showlegend=False, hoverinfo='skip'
                ))

                # 進度條（從 0 到目前 stage）
                if stage_x >= 0:
                    fig.add_trace(go.Scatter(
                        x=[-0.4, stage_x],
                        y=[y, y],
                        mode='lines',
                        line=dict(color=color, width=18),
                        showlegend=False, hoverinfo='skip',
                        opacity=0.65
                    ))

                # 目前 stage 的標記圓點
                show_in_legend = status not in added_legend
                if show_in_legend:
                    added_legend.add(status)
                fig.add_trace(go.Scatter(
                    x=[stage_x],
                    y=[y],
                    mode='markers',
                    name=f"{STATUS_EMOJI[status]} {status}",
                    marker=dict(size=18, color=color,
                                symbol='circle',
                                line=dict(color='white', width=2)),
                    showlegend=show_in_legend,
                    hovertemplate=(
                        f"<b>{resident}</b><br>"
                        f"📄 {title}<br>"
                        f"狀態：{STATUS_EMOJI[status]} {status}<br>"
                        f"類型：{res_type}<br>"
                        f"指導老師：{supervisor}"
                        "<extra></extra>"
                    )
                ))

                # 研究題目標籤（圓點右側）
                fig.add_annotation(
                    x=stage_x + 0.35, y=y,
                    text=title_short,
                    showarrow=False,
                    xanchor='left', yanchor='middle',
                    font=dict(size=11, color='#2C3E50'),
                    bgcolor='rgba(255,255,255,0.7)',
                )

                # Y 軸標籤（只在每位住院醫師的第一筆顯示姓名）
                y_tick_vals.append(y)
                y_tick_texts.append(f"<b>{resident}</b>" if j == 0 else "　└")

                y -= 1

            # 住院醫師之間的分隔線
            if resident != sorted_residents[-1]:
                y_separator_positions.append(y + 0.5)

        for sep_y in y_separator_positions:
            fig.add_hline(y=sep_y, line_color='rgba(100,100,100,0.25)', line_width=1)

        fig.update_layout(
            height=max(320, 52 * total_rows + 100),
            xaxis=dict(
                tickvals=list(range(len(STAGES))),
                ticktext=[f"<b>{s}</b>" for s in STAGES],
                range=[-0.6, len(STAGES) - 0.4],
                tickfont=dict(size=13),
                side='top',
                showgrid=False,
                zeroline=False,
            ),
            yaxis=dict(
                tickvals=y_tick_vals,
                ticktext=y_tick_texts,
                tickfont=dict(size=12),
                showgrid=False,
                zeroline=False,
                range=[-0.7, total_rows - 0.3],
            ),
            plot_bgcolor='rgba(248,249,250,1)',
            paper_bgcolor='white',
            showlegend=True,
            legend=dict(
                orientation='h', yanchor='bottom', y=-0.08,
                xanchor='center', x=0.5,
                bgcolor='rgba(255,255,255,0.9)',
                bordercolor='rgba(0,0,0,0.15)', borderwidth=1,
                font=dict(size=12)
            ),
            margin=dict(l=90, r=30, t=60, b=60),
        )

        st.plotly_chart(fig, width="stretch", key="ccc_research_swimlane")

        # 詳細清單（expander）
        with st.expander("📋 詳細研究清單"):
            display_data = []
            for rec in all_research:
                s = rec.get('current_status', '')
                display_data.append({
                    '住院醫師': rec.get('resident_name', ''),
                    '研究名稱': rec.get('research_title', ''),
                    '類型': rec.get('research_type', ''),
                    '指導老師': rec.get('supervisor_name', '—'),
                    '進度': f"{STATUS_EMOJI.get(s, '📝')} {s}",
                    '更新時間': rec.get('updated_at', '')[:10] if rec.get('updated_at') else '',
                })
            if display_data:
                st.dataframe(pd.DataFrame(display_data), hide_index=True, use_container_width=True)

    except Exception as e:
        st.warning(f"載入研究進度總覽時發生錯誤：{str(e)}")


if __name__ == "__main__":
    show_pediatric_evaluation_section()
