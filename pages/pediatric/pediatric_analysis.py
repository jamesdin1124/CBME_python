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
    """
    從 Supabase 載入門檻設定。
    失敗時回退到硬碼預設值，並快取在 session_state。
    """
    cache_key = '_pediatric_thresholds'
    if cache_key in st.session_state:
        return st.session_state[cache_key]

    defaults = {
        'technical_green_threshold': THRESHOLD_TECHNICAL_GREEN,
        'technical_red_threshold': THRESHOLD_TECHNICAL_RED,
        'score_green_threshold': THRESHOLD_SCORE_GREEN,
        'score_red_threshold': THRESHOLD_SCORE_RED,
    }
    conn = _get_supabase_conn()
    if conn:
        try:
            settings = conn.get_active_thresholds()
            if settings and 'technical_green_threshold' in settings:
                st.session_state[cache_key] = settings
                return settings
        except Exception:
            pass
    st.session_state[cache_key] = defaults
    return defaults

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
    'APLS': {'minimum': 3, 'description': '訓練期間最少3次'},
    'NRP': {'minimum': 5, 'description': '訓練期間最少5次'}, 
    'CVVH照護': {'minimum': 1, 'description': '訓練期間最少1次'}, 
    'ECMO照護': {'minimum': 1, 'description': '訓練期間最少1次'}
}

# 兒科 EPA 信賴等級評估三項目（表單 Q18）
PEDIATRIC_EPA_ITEMS = ['病人日常照護', '緊急照護處置', '病歷書寫']

# ─── 技能分組（用於 CCC 總覽和個別分析的分類進度顯示）───
SKILL_GROUPS = {
    '導管與插管類': ['插氣管內管', '插臍(動靜脈)導管', '腰椎穿刺',
                    '插中心靜脈導管(CVC)', '肋膜液或是腹水抽取',
                    '插胸管', '放置動脈導管', '經皮式中央靜脈導管(PICC)'],
    '超音波類':    ['腦部超音波', '心臟超音波', '腹部超音波', '腎臟超音波'],
    '急救與特殊照護類': ['APLS', 'NRP', 'CVVH照護', 'ECMO照護']
}

# ─── CCC 門檢標準（硬碼）───
# 技能完成率門檢（百分比）
THRESHOLD_TECHNICAL_GREEN = 100   # 所有項目均完成
THRESHOLD_TECHNICAL_RED   = 60    # < 60% 為紅燈
# EPA / 會議報告均分門檢（1-5 分制）
THRESHOLD_SCORE_GREEN = 3.5
THRESHOLD_SCORE_RED   = 2.5

def show_pediatric_evaluation_section():
    """顯示小兒部住院醫師評核分頁"""
    st.title("🏥 小兒部住院醫師評核系統")
    st.markdown("---")

    # 顯示表單連結 + 資料來源 + 測試模式切換
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        # 資料來源選擇
        data_source = st.radio(
            "資料來源",
            options=['supabase', 'google_sheets', 'test'],
            format_func=lambda x: {'supabase': '☁️ Supabase', 'google_sheets': '📊 Google Sheets', 'test': '🧪 測試資料'}[x],
            horizontal=True,
            index=0 if _get_supabase_conn() else 1,
            help="選擇資料來源：Supabase（新）、Google Sheets（舊）或測試資料"
        )
        st.session_state['pediatric_data_source'] = data_source
        st.session_state['use_pediatric_test_data'] = (data_source == 'test')
    with col2:
        if data_source == 'google_sheets':
            st.info("📋 [開啟 Google 表單](https://docs.google.com/spreadsheets/d/1n4kc2d3Z-x9SvIDApPCCz2HSDO0wSrrk9Y5jReMhr-M/edit?usp=sharing)")
    with col3:
        pass  # 保留空間

    # 判斷是否為教師/管理員（可使用表單與帳號管理）
    from modules.auth import check_permission
    user_role = st.session_state.get('role', 'resident')
    can_submit_forms = check_permission(user_role, 'can_upload_files')
    can_manage_users = check_permission(user_role, 'can_manage_users')

    # 動態建立 tabs
    tab_labels = ["🏆 CCC 總覽", "📋 個別深入分析", "📊 資料概覽", "⚙️ 資料管理"]
    if can_submit_forms:
        tab_labels.append("✏️ 評核表單")
    if can_manage_users:
        tab_labels.append("👥 帳號管理")

    tabs = st.tabs(tab_labels)

    with tabs[0]:
        show_ccc_overview()

    with tabs[1]:
        show_individual_analysis()

    with tabs[2]:
        show_data_overview()

    with tabs[3]:
        show_data_management()

    # Tab 5：評核表單（教師/管理員限定）
    if can_submit_forms and len(tabs) > 4:
        with tabs[4]:
            conn = _get_supabase_conn()
            if conn:
                from pages.pediatric.pediatric_forms import show_evaluation_forms_tab
                current_user = st.session_state.get('user_name', st.session_state.get('username', '未知'))
                show_evaluation_forms_tab(conn, current_user)
            else:
                st.error("❌ 無法連線 Supabase，請檢查 `.env` 中的 `SUPABASE_URL` 和 `SUPABASE_KEY` 設定。")
                st.info("評核表單需要 Supabase 資料庫連線才能使用。")

    # Tab 6：帳號管理（管理員限定）
    if can_manage_users:
        tab_idx = 5 if can_submit_forms else 4
        if len(tabs) > tab_idx:
            with tabs[tab_idx]:
                conn = _get_supabase_conn()
                if conn:
                    from pages.pediatric.pediatric_user_management import show_pediatric_user_management
                    show_pediatric_user_management(conn)
                else:
                    st.error("❌ 無法連線 Supabase，請檢查 `.env` 設定。")

def load_pediatric_data():
    """
    載入小兒部評核資料（混合資料來源）。
    優先順序：測試資料 > Supabase > Google Sheets
    """
    try:
        data_source = st.session_state.get('pediatric_data_source', 'google_sheets')

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

        # ── Supabase 模式 ──
        elif data_source == 'supabase':
            df, sheet_titles = _load_from_supabase()
            if df is None or df.empty:
                st.warning("⚠️ Supabase 無資料或連線失敗，嘗試回退到 Google Sheets...")
                df, sheet_titles = _load_from_google_sheets()

        # ── Google Sheets 模式 ──
        else:
            df, sheet_titles = _load_from_google_sheets()

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


def _load_from_supabase():
    """
    從 Supabase 載入資料並轉換為與 Google Sheets 相容的 DataFrame 格式。
    確保後續 process_pediatric_data() 能正常運作。
    """
    conn = _get_supabase_conn()
    if not conn:
        return None, None

    try:
        records = conn.fetch_pediatric_evaluations()
        if not records:
            return None, None

        df = pd.DataFrame(records)

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
        # 9級量表（兒科表單標準選項，從1.5分開始）
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
        
        # 計算完成狀況
        completed_skills = 0
        for skill, data in skill_counts.items():
            if data['completed'] >= data['required']:
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
        
        st.plotly_chart(fig_individual, use_container_width=True)


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
        st.plotly_chart(fig, use_container_width=True)


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
    return {'GREEN': '🟢', 'YELLOW': '🟡', 'RED': '🔴'}.get(status, '⚪')

def _status_label(status):
    return {'GREEN': '進度良好', 'YELLOW': '需注意', 'RED': '需輔導'}.get(status, '未知')

def show_ccc_overview():
    """Tab 1：CCC 總覽頁面主函數"""
    st.subheader("🏆 CCC 會議 — 小兒部住院醫師訓練進度總覽")

    df, _ = load_pediatric_data()
    if df is None or df.empty:
        st.warning("無法載入資料，請檢查 Google 表單連接")
        return

    # 緩存資料至 session_state
    st.session_state['pediatric_data'] = df

    # ── 計算所有住院醫師的狀態 ──
    residents = sorted(df['受評核人員'].unique()) if '受評核人員' in df.columns else []
    if not residents:
        st.warning("資料中沒有找到受評核人員")
        return

    all_status = {}  # {姓名: status_dict}
    for name in residents:
        res_df = df[df['受評核人員'] == name]
        all_status[name] = calculate_resident_status(res_df, df)
        all_status[name]['level'] = _get_resident_level(df, name)

    # ── Section A：警報橫帶 ──
    show_alert_banner(all_status)

    st.divider()

    # ── Section B：摘要卡片 ──
    show_resident_cards(all_status, df)

    st.divider()

    # ── Section C：並排長條圖 ──
    show_comparison_bar_chart(all_status)

    st.divider()

    # ── Section D：技能熱圖矩陣 ──
    show_skill_heatmap(df)

    st.divider()

    # ── Section E：EPA 整體趨勢（所有住院醫師）──
    show_overall_epa_trend(df)


def show_alert_banner(all_status):
    """警報橫帶：紅、黃、綠分類顯示姓名"""
    groups = {'RED': [], 'YELLOW': [], 'GREEN': []}
    for name, info in all_status.items():
        groups[info['overall']].append(name)

    # 必須至少有一種狀態才顯示
    banner_parts = []
    if groups['RED']:
        banner_parts.append(
            f'<span style="background:#ffe0e0;color:#c0392b;padding:6px 12px;border-radius:6px;font-weight:bold;">🔴 需輔導：{" ・ ".join(groups["RED"])}</span>'
        )
    if groups['YELLOW']:
        banner_parts.append(
            f'<span style="background:#fff3cd;color:#856404;padding:6px 12px;border-radius:6px;font-weight:bold;">🟡 需注意：{" ・ ".join(groups["YELLOW"])}</span>'
        )
    if groups['GREEN']:
        banner_parts.append(
            f'<span style="background:#d4edda;color:#155724;padding:6px 12px;border-radius:6px;font-weight:bold;">🟢 進度良好：{" ・ ".join(groups["GREEN"])}</span>'
        )

    st.markdown(' &nbsp;&nbsp; '.join(banner_parts), unsafe_allow_html=True)


def show_resident_cards(all_status, df):
    """摘要卡片列表：每行 3 張卡片"""
    residents = list(all_status.keys())
    n_cols = min(3, len(residents))
    cols = st.columns(n_cols)

    for i, name in enumerate(residents):
        info = all_status[name]
        col = cols[i % n_cols]

        with col:
            with st.container(border=True):
                # 標題行：姓名 + 級職 + 狀態標記
                st.markdown(
                    f"**{name}** &nbsp; {info['level']} &nbsp; {_status_emoji(info['overall'])} {_status_label(info['overall'])}",
                    unsafe_allow_html=True
                )
                st.divider()

                # 三個指標並排（加上計分方式註記）
                c1, c2, c3 = st.columns(3)
                with c1:
                    epa_val = info['epa']['avg_score']
                    st.metric("EPA均分 (1-5分)", f"{epa_val:.1f}" if epa_val is not None else "—",
                              help="三項EPA可信賴程度平均值")
                with c2:
                    tech_val = info['technical']['completion_rate']
                    st.metric("技能完成率 (%)", f"{tech_val:.0f}%" if tech_val is not None else "—",
                              help="已達標技能數 ÷ 16項 × 100%")
                with c3:
                    mtg_val = info['meeting']['avg_score']
                    st.metric("會議報告均分 (1-5分)", f"{mtg_val:.1f}" if mtg_val is not None else "—",
                              help="五維度評分平均值")


def show_comparison_bar_chart(all_status):
    """並排長條圖：三維度百分化後對比"""
    st.subheader("📊 訓練完成度並排比較")
    st.caption("技能完成率 = 已達標技能數÷16×100% ｜ EPA達標率 = EPA均分÷5×100% ｜ 會議報告均分 = 五維度均分÷5×100%")

    names = list(all_status.keys())
    tech_rates  = []
    epa_rates   = []
    mtg_rates   = []

    for name in names:
        info = all_status[name]
        tech_rates.append(info['technical']['completion_rate'] if info['technical']['completion_rate'] is not None else 0)
        # EPA：均分 / 5 * 100 → 百分化
        epa_rates.append(info['epa']['avg_score'] / 5 * 100 if info['epa']['avg_score'] is not None else 0)
        # 會議報告：均分 / 5 * 100
        mtg_rates.append(info['meeting']['avg_score'] / 5 * 100 if info['meeting']['avg_score'] is not None else 0)

    fig = go.Figure()
    fig.add_trace(go.Bar(name='技能完成率',   x=names, y=tech_rates, marker_color='#4A90D9'))
    fig.add_trace(go.Bar(name='EPA達標率',    x=names, y=epa_rates,  marker_color='#50C878'))
    fig.add_trace(go.Bar(name='會議報告均分', x=names, y=mtg_rates,  marker_color='#F5A623'))

    # Y=60% 虛線
    fig.add_hline(y=60, line_dash="dash", line_color="red",
                  annotation_text="最低期望 (60%)", annotation_position="top left")

    fig.update_layout(
        barmode='group',
        yaxis_title='百分比 (%)',
        yaxis=dict(range=[0, 110]),
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig, use_container_width=True)


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
            row_z.append(min(c / r, 1.5) if r > 0 else 0)  # cap at 1.5 for color
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
    st.plotly_chart(fig, use_container_width=True)


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

    # 添加門檢線
    fig.add_hline(y=3.5, line_dash="dash", line_color="green",
                  annotation_text="優秀門檢 (3.5)", annotation_position="top right")
    fig.add_hline(y=2.5, line_dash="dash", line_color="orange",
                  annotation_text="及格門檢 (2.5)", annotation_position="bottom right")

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
    st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════
# 原有：資料概覽
# ═══════════════════════════════════════════════════════

def show_data_overview():
    """顯示資料概覽"""
    st.subheader("📊 小兒部住院醫師評核資料概覽")
    
    # 載入資料
    df, sheet_titles = load_pediatric_data()
    
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
            st.dataframe(df, use_container_width=True)
        
        # 技能項目完成比例分析已移動至「CCC 總覽」tab 的熱圖矩陣
        st.info("💡 詳細技能完成度分析請見「🏆 CCC 總覽」tab 的技能熱圖矩陣")
        
        # EPA 信賴等級評估概覽（僅當有 EPA 資料時顯示）
        show_epa_overview(df)
    
    else:
        st.warning("無法載入資料，請檢查Google表單連接")

def show_individual_analysis():
    """個別深入分析（Tab 2）：三欄並排儀表盤 → 技能分組進度 → 會議報告回饋 → 詳細記錄"""
    st.subheader("📋 個別住院醫師深入分析")

    # 讀取資料（優先從 session_state，避免重複 API 調用）
    if 'pediatric_data' in st.session_state and st.session_state['pediatric_data'] is not None:
        df = st.session_state['pediatric_data']
    else:
        df, _ = load_pediatric_data()
        if df is not None:
            st.session_state['pediatric_data'] = df

    if df is None or df.empty:
        st.warning("無法載入資料")
        return

    if '受評核人員' not in df.columns:
        st.warning("資料中沒有「受評核人員」欄位")
        return

    residents = sorted(df['受評核人員'].unique())

    # 從 CCC 總覽卡片點進時的預設值
    default_resident = st.session_state.pop('selected_resident_from_overview', None)
    if default_resident and default_resident in residents:
        default_index = residents.index(default_resident)
    else:
        default_index = 0

    selected_resident = st.selectbox("選擇受評核人員", residents, index=default_index)

    if not selected_resident:
        return

    resident_data = df[df['受評核人員'] == selected_resident].copy()

    # ── 基本統計帶（小型）──
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("總評核次數", len(resident_data))
    with col2:
        unique_items = len(resident_data['評核項目'].unique()) if '評核項目' in resident_data.columns else 0
        st.metric("評核項目種類", unique_items)
    with col3:
        if '評核日期' in resident_data.columns:
            st.metric("評核期間", f"{resident_data['評核日期'].min()} ~ {resident_data['評核日期'].max()}")
    with col4:
        status = calculate_resident_status(resident_data, df)
        st.metric("整體狀態", f"{_status_emoji(status['overall'])} {_status_label(status['overall'])}")

    # 預先分離三類資料
    technical_data = resident_data[resident_data['評核項目'] == '操作技術'].copy() if '評核項目' in resident_data.columns else pd.DataFrame()
    meeting_data   = resident_data[resident_data['評核項目'] == '會議報告'].copy() if '評核項目' in resident_data.columns else pd.DataFrame()
    epa_data       = resident_data[resident_data['評核項目'].astype(str).str.contains('EPA', na=False)].copy() if '評核項目' in resident_data.columns else pd.DataFrame()

    # ═══ Section A：能力儀表盤（三欄並排，無 expander）═══
    st.markdown("### 能力儀表盤")
    col_epa, col_tech, col_mtg = st.columns(3)

    # ── 左欄：EPA 雷達圖 ──
    with col_epa:
        st.markdown("**EPA 信賴程度**")
        if not epa_data.empty and 'EPA項目' in epa_data.columns:
            num_col_epa = 'EPA可信賴程度_數值' if 'EPA可信賴程度_數值' in epa_data.columns else None
            epa_scores = {}
            for item in PEDIATRIC_EPA_ITEMS:
                item_df = epa_data[epa_data['EPA項目'].astype(str).str.contains(item, na=False)]
                if not item_df.empty and num_col_epa and num_col_epa in item_df.columns:
                    s = item_df[num_col_epa].dropna()
                    epa_scores[item] = float(s.mean()) if len(s) > 0 else 1.0
                else:
                    epa_scores[item] = 1.0

            # 計算同儕平均
            resident_level = _get_resident_level(df, selected_resident)
            all_epa = df[df['評核項目'].astype(str).str.contains('EPA', na=False)].copy() if '評核項目' in df.columns else pd.DataFrame()
            peer_epa = all_epa[
                (all_epa['受評核人員'] != selected_resident) &
                (all_epa['評核時級職'].astype(str) == str(resident_level))
            ] if not all_epa.empty and '受評核人員' in all_epa.columns and '評核時級職' in all_epa.columns else pd.DataFrame()

            peer_scores = {}
            if not peer_epa.empty:
                for item in PEDIATRIC_EPA_ITEMS:
                    item_df = peer_epa[peer_epa['EPA項目'].astype(str).str.contains(item, na=False)]
                    if not item_df.empty and num_col_epa and num_col_epa in item_df.columns:
                        s = item_df[num_col_epa].dropna()
                        peer_scores[item] = float(s.mean()) if len(s) > 0 else 1.0
                    else:
                        peer_scores[item] = 1.0

            categories = list(epa_scores.keys())
            values_self = [epa_scores[k] for k in categories]
            categories_closed = categories + [categories[0]]
            values_self_closed = values_self + [values_self[0]]

            fig_epa = go.Figure()
            if peer_scores:
                values_peer = [peer_scores.get(k, 1.0) for k in categories]
                values_peer_closed = values_peer + [values_peer[0]]
                fig_epa.add_trace(go.Scatterpolar(
                    r=values_peer_closed, theta=categories_closed,
                    fill='toself', name=f'同儕平均（{resident_level}）',
                    line=dict(color='rgba(128,128,128,1)', width=2),
                    fillcolor='rgba(128,128,128,0.12)'
                ))
            fig_epa.add_trace(go.Scatterpolar(
                r=values_self_closed, theta=categories_closed,
                fill='toself', name=selected_resident,
                line=dict(color='rgba(32,201,151,1)', width=2),
                fillcolor='rgba(32,201,151,0.2)'
            ))
            fig_epa.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
                height=300, showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                margin=dict(l=10, r=10, t=10, b=40)
            )
            st.plotly_chart(fig_epa, use_container_width=True, key=f"epa_radar_{selected_resident}")
        else:
            st.info("無 EPA 評核記錄")

    # ── 中欄：技能完成度摘要 ──
    with col_tech:
        st.markdown("**臨床技術 完成度**")
        skill_counts = calculate_skill_counts(technical_data) if not technical_data.empty else {}
        if skill_counts:
            completed_skills = sum(1 for d in skill_counts.values() if d['completed'] >= d['required'])
            total_skills = len(skill_counts)
            rate = completed_skills / total_skills
            st.progress(min(rate, 1.0), text=f"已完成 {completed_skills} / {total_skills} 項")
            # 列出未完成項目
            unfinished = [name for name, d in skill_counts.items() if d['completed'] < d['required']]
            if unfinished:
                st.markdown("**⚠️ 未達標項目：**")
                for item in unfinished:
                    d = skill_counts[item]
                    st.markdown(f"&nbsp;&nbsp;🔶 {item}　({d['completed']}/{d['required']})", unsafe_allow_html=True)
            else:
                st.success("所有技能均已達標")
        else:
            st.info("無操作技術評核記錄")

    # ── 右欄：會議報告雷達圖 ──
    with col_mtg:
        st.markdown("**會議報告 評分**")
        radar_text_cols = [
            ('內容是否充分',           '內容充分'),
            ('辯證資料的能力',         '辯證資料'),
            ('口條、呈現方式是否清晰', '口條清晰'),
            ('是否具開創、建設性的想法','開創想法'),
            ('回答提問是否具邏輯、有條有理','邏輯回答'),
        ]
        labels_radar  = []
        means_self    = []
        means_peer    = []

        # 同儕（同級職）會議報告數據
        resident_level = _get_resident_level(df, selected_resident)
        all_meeting = df[df['評核項目'].astype(str).str.contains('會議報告', na=False)].copy() if '評核項目' in df.columns else pd.DataFrame()
        peer_meeting = all_meeting[
            (all_meeting['受評核人員'] != selected_resident) &
            (all_meeting['評核時級職'].astype(str) == str(resident_level))
        ] if not all_meeting.empty and '受評核人員' in all_meeting.columns and '評核時級職' in all_meeting.columns else pd.DataFrame()

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
            labels_closed     = labels_radar + [labels_radar[0]]
            means_self_closed = means_self + [means_self[0]]
            fig_mtg = go.Figure()
            if means_peer and any(m > 0 for m in means_peer):
                means_peer_closed = means_peer + [means_peer[0]]
                fig_mtg.add_trace(go.Scatterpolar(
                    r=means_peer_closed, theta=labels_closed,
                    fill='toself', name=f'同儕平均（{resident_level}）',
                    line=dict(color='rgba(128,128,128,1)', width=2),
                    fillcolor='rgba(128,128,128,0.12)'
                ))
            fig_mtg.add_trace(go.Scatterpolar(
                r=means_self_closed, theta=labels_closed,
                fill='toself', name=selected_resident,
                line=dict(color='rgba(65,105,225,1)', width=2),
                fillcolor='rgba(65,105,225,0.2)'
            ))
            fig_mtg.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
                height=300, showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                margin=dict(l=10, r=10, t=10, b=40)
            )
            st.plotly_chart(fig_mtg, use_container_width=True, key=f"mtg_radar_{selected_resident}")
        else:
            st.info("無會議報告評核記錄")

    # ═══ Section B：技能分組進度 ═══
    st.markdown("### 技能分類進度")
    if skill_counts:
        show_grouped_skill_progress(skill_counts)
    else:
        # skill_counts 可能在 col_tech 裡計算過但此處無法訪問，重新計算
        _sk = calculate_skill_counts(technical_data) if not technical_data.empty else {}
        if _sk:
            show_grouped_skill_progress(_sk)
        else:
            st.info("無操作技術評核記錄")

    # ═══ Section C：會議報告質性回饋（直接展開，限最近 5 筆）═══
    st.markdown("### 會議報告質性回饋")
    feedback_col = '會議報告教師回饋'
    if not meeting_data.empty and feedback_col in meeting_data.columns:
        feedback_rows = meeting_data[meeting_data[feedback_col].notna() & (meeting_data[feedback_col].astype(str).str.strip() != '')]
        if '評核日期' in feedback_rows.columns:
            feedback_rows = feedback_rows.sort_values('評核日期', ascending=False)

        if not feedback_rows.empty:
            # 最近 5 筆直接展開
            display_rows = feedback_rows.head(5)
            for _, row in display_rows.iterrows():
                with st.container(border=True):
                    d = row.get('評核日期', '')
                    if hasattr(d, 'strftime'):
                        d = d.strftime('%Y-%m-%d')
                    teacher = row.get('評核教師', '')
                    st.caption(f"日期：{d}　|　評核教師：{teacher}")
                    st.write(str(row.get(feedback_col, '')))

            # 超過 5 筆的放入 expander
            if len(feedback_rows) > 5:
                with st.expander(f"查看全部回饋（共 {len(feedback_rows)} 筆）"):
                    for _, row in feedback_rows.iloc[5:].iterrows():
                        with st.container(border=True):
                            d = row.get('評核日期', '')
                            if hasattr(d, 'strftime'):
                                d = d.strftime('%Y-%m-%d')
                            teacher = row.get('評核教師', '')
                            st.caption(f"日期：{d}　|　評核教師：{teacher}")
                            st.write(str(row.get(feedback_col, '')))
        else:
            st.info("該住院醫師目前沒有會議報告教師回饋記錄")
    else:
        st.info("無會議報告教師回饋資料")

    # ═══ Section D：詳細記錄（expander 收合）═══
    with st.expander("📋 操作技術詳細記錄", expanded=False):
        if not technical_data.empty:
            display_cols = ['評核日期', '評核教師', '評核技術項目', '可信賴程度', '熟練程度(自動判定)', '操作技術教師回饋']
            avail = [c for c in display_cols if c in technical_data.columns]
            if avail:
                st.dataframe(technical_data[avail].sort_values('評核日期', ascending=False), use_container_width=True)
        else:
            st.info("無操作技術評核記錄")

    with st.expander("📋 會議報告詳細記錄", expanded=False):
        if not meeting_data.empty:
            display_cols = ['評核日期', '評核教師', '會議名稱',
                            '內容是否充分', '辯證資料的能力', '口條、呈現方式是否清晰',
                            '是否具開創、建設性的想法', '回答提問是否具邏輯、有條有理',
                            '會議報告教師回饋', '病歷號']
            avail = [c for c in display_cols if c in meeting_data.columns]
            if avail:
                st.dataframe(meeting_data[avail].sort_values('評核日期', ascending=False), use_container_width=True)
        else:
            st.info("無會議報告評核記錄")

    with st.expander("📋 EPA 詳細記錄", expanded=False):
        if not epa_data.empty:
            display_cols = ['評核日期', '評核教師', 'EPA項目', 'EPA可信賴程度', 'EPA質性回饋']
            avail = [c for c in display_cols if c in epa_data.columns]
            if avail:
                st.dataframe(epa_data[avail].sort_values('評核日期', ascending=False), use_container_width=True)
        else:
            st.info("無 EPA 評核記錄")

    # ═══ Section E：EPA 信賴程度趨勢圖（時間序列）═══
    if not epa_data.empty and 'EPA項目' in epa_data.columns and '評核日期' in epa_data.columns:
        st.markdown("### EPA 信賴程度趨勢分析")
        st.caption("各 EPA 項目每月平均可信賴程度變化")

        show_epa_trend_chart(epa_data, selected_resident)


def show_epa_trend_chart(epa_data, resident_name):
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
        item_data = monthly_avg[monthly_avg['EPA項目'].str.contains(epa_item, na=False)]
        if not item_data.empty:
            fig.add_trace(go.Scatter(
                x=item_data['年月'],
                y=item_data['EPA可信賴程度_數值'],
                mode='lines+markers',
                name=epa_item,
                line=dict(width=3, color=colors[i % len(colors)]),
                marker=dict(size=8)
            ))

    # 添加門檢線
    fig.add_hline(y=3.5, line_dash="dash", line_color="green",
                  annotation_text="優秀門檢 (3.5)", annotation_position="top right")
    fig.add_hline(y=2.5, line_dash="dash", line_color="orange",
                  annotation_text="及格門檢 (2.5)", annotation_position="bottom right")

    fig.update_layout(
        title=f"{resident_name} EPA 信賴程度月度趨勢",
        xaxis_title="時間（年月）",
        yaxis_title="可信賴程度（1-5分）",
        yaxis=dict(range=[0, 5.5]),
        height=450,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig, use_container_width=True, key=f"epa_trend_{resident_name}")


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
                st.dataframe(stats_df, use_container_width=True)
                
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
                st.plotly_chart(fig, use_container_width=True)
        
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
                st.dataframe(teacher_df, use_container_width=True)
        
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
            st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.warning("無法載入資料")


def _show_threshold_settings_ui():
    """CCC 門檻設定介面（管理員專用）"""
    thresholds = load_threshold_settings()

    st.markdown("#### 技能完成率門檻（百分比）")
    col1, col2 = st.columns(2)
    with col1:
        tech_green = st.slider(
            "🟢 綠燈門檻（%）",
            min_value=80.0, max_value=100.0,
            value=float(thresholds.get('technical_green_threshold', 100.0)),
            step=5.0,
            help="所有項目均完成才算綠燈"
        )
    with col2:
        tech_red = st.slider(
            "🔴 紅燈門檻（%）",
            min_value=30.0, max_value=80.0,
            value=float(thresholds.get('technical_red_threshold', 60.0)),
            step=5.0,
            help="低於此值為紅燈（需輔導）"
        )

    st.markdown("#### EPA / 會議報告均分門檻（1-5 分）")
    col3, col4 = st.columns(2)
    with col3:
        score_green = st.slider(
            "🟢 綠燈門檻（分）",
            min_value=2.5, max_value=5.0,
            value=float(thresholds.get('score_green_threshold', 3.5)),
            step=0.1
        )
    with col4:
        score_red = st.slider(
            "🔴 紅燈門檻（分）",
            min_value=1.5, max_value=3.5,
            value=float(thresholds.get('score_red_threshold', 2.5)),
            step=0.1
        )

    # 驗證
    if tech_green <= tech_red:
        st.error("❌ 技能完成率：綠燈門檻必須大於紅燈門檻")
        return
    if score_green <= score_red:
        st.error("❌ 分數門檻：綠燈門檻必須大於紅燈門檻")
        return

    # 預覽
    st.markdown("**預覽門檻判定：**")
    st.write(f"- 🟢 **GREEN**：技能 ≥ {tech_green}%，分數 ≥ {score_green}")
    st.write(f"- 🟡 **YELLOW**：介於紅燈與綠燈之間")
    st.write(f"- 🔴 **RED**：技能 < {tech_red}%，分數 < {score_red}")

    notes = st.text_input("變更說明（選填）", placeholder="為什麼調整門檻？")

    if st.button("💾 儲存門檻設定", type="primary"):
        conn = _get_supabase_conn()
        if conn:
            success = conn.save_threshold_settings(
                settings={
                    'technical_green_threshold': tech_green,
                    'technical_red_threshold': tech_red,
                    'score_green_threshold': score_green,
                    'score_red_threshold': score_red,
                },
                updated_by=st.session_state.get('username', 'unknown'),
                notes=notes
            )
            if success:
                # 清除快取以強制重新載入
                if '_pediatric_thresholds' in st.session_state:
                    del st.session_state['_pediatric_thresholds']
                st.success("✅ 門檻設定已更新！CCC 狀態將重新計算。")
                st.rerun()
            else:
                st.error("❌ 儲存失敗，請檢查 Supabase 連線")
        else:
            st.error("❌ 無法連線 Supabase，門檻設定需要資料庫連線")

    # 歷史記錄
    if st.checkbox("顯示歷史門檻設定"):
        conn = _get_supabase_conn()
        if conn:
            try:
                result = conn.get_client().table('pediatric_threshold_settings') \
                    .select('*') \
                    .order('created_at', desc=True) \
                    .limit(10) \
                    .execute()
                if result.data:
                    for h in result.data:
                        active_tag = " ✅ **（作用中）**" if h.get('is_active') else ""
                        st.markdown(f"**{str(h.get('effective_from', ''))[:16]}** — {h.get('updated_by', '?')}{active_tag}")
                        st.caption(f"技能: {h.get('technical_red_threshold')}%-{h.get('technical_green_threshold')}% | "
                                   f"分數: {h.get('score_red_threshold')}-{h.get('score_green_threshold')} | "
                                   f"{h.get('notes', '')}")
                else:
                    st.info("尚無歷史記錄")
            except Exception as e:
                st.warning(f"載入歷史記錄失敗：{str(e)}")


def show_data_management():
    """顯示資料管理（含門檻設定 UI）"""
    st.subheader("⚙️ 資料管理")

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
                df, sheet_titles = load_pediatric_data()
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
    
    # 載入資料
    df, _ = load_pediatric_data()
    
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
    """計算住院醫師各項技能完成次數（可信賴程度需在3以上才列入完成）"""
    skill_counts = {}
    
    # 從評核技術項目欄位中提取技能資訊
    if '評核技術項目' in resident_data.columns:
        technical_items = resident_data['評核技術項目'].dropna()
        
        for skill in PEDIATRIC_SKILL_REQUIREMENTS.keys():
            # 計算該技能出現的次數（只計算可信賴程度3以上的記錄）
            count = 0
            for idx, item in technical_items.items():
                if skill in str(item):
                    # 檢查該記錄的可信賴程度
                    if '可信賴程度_數值' in resident_data.columns:
                        reliability_score = resident_data.loc[idx, '可信賴程度_數值']
                        # 只有可信賴程度在3以上（3、4、5）才計入完成
                        if pd.notna(reliability_score) and reliability_score >= 3:
                            count += 1
                    else:
                        # 如果沒有可信賴程度欄位，則使用原始計算方式
                        count += 1
            
            skill_counts[skill] = {
                'completed': count,
                'required': PEDIATRIC_SKILL_REQUIREMENTS[skill]['minimum'],
                'description': PEDIATRIC_SKILL_REQUIREMENTS[skill]['description'],
                'progress': min(count / PEDIATRIC_SKILL_REQUIREMENTS[skill]['minimum'] * 100, 100)
            }
    
    return skill_counts

def calculate_resident_status(resident_data, full_df):
    """計算單位住院醫師的 GREEN / YELLOW / RED 狀態
    判定維度：技能完成率、EPA均分、會議報告均分
    取三個維度中最差者為 overall 狀態
    無資料的維度視為 YELLOW
    門檻值從 Supabase 動態載入（失敗時回退到硬碼預設值）
    """
    # 動態載入門檻
    thresholds = load_threshold_settings()
    th_tech_green = float(thresholds.get('technical_green_threshold', THRESHOLD_TECHNICAL_GREEN))
    th_tech_red = float(thresholds.get('technical_red_threshold', THRESHOLD_TECHNICAL_RED))
    th_score_green = float(thresholds.get('score_green_threshold', THRESHOLD_SCORE_GREEN))
    th_score_red = float(thresholds.get('score_red_threshold', THRESHOLD_SCORE_RED))

    def _level(value, green_thresh, red_thresh):
        if value is None:
            return 'YELLOW'
        if value >= green_thresh:
            return 'GREEN'
        if value < red_thresh:
            return 'RED'
        return 'YELLOW'

    # ── 維度 1：技能完成率 ──
    technical_data = resident_data[resident_data['評核項目'] == '操作技術'] if '評核項目' in resident_data.columns else pd.DataFrame()
    skill_counts = calculate_skill_counts(technical_data) if not technical_data.empty else {}
    if skill_counts:
        completed_skills = sum(1 for d in skill_counts.values() if d['completed'] >= d['required'])
        tech_rate = completed_skills / len(skill_counts) * 100
    else:
        tech_rate = None
    tech_status = _level(tech_rate, th_tech_green, th_tech_red)

    # ── 維度 2：EPA 均分 ──
    epa_data = resident_data[resident_data['評核項目'].astype(str).str.contains('EPA', na=False)] if '評核項目' in resident_data.columns else pd.DataFrame()
    if not epa_data.empty and 'EPA可信賴程度_數值' in epa_data.columns:
        epa_avg = epa_data['EPA可信賴程度_數值'].dropna().mean()
        epa_avg = float(epa_avg) if pd.notna(epa_avg) else None
    else:
        epa_avg = None
    epa_status = _level(epa_avg, th_score_green, th_score_red)

    # ── 維度 3：會議報告均分 ──
    meeting_data = resident_data[resident_data['評核項目'] == '會議報告'] if '評核項目' in resident_data.columns else pd.DataFrame()
    meeting_score_cols = ['內容是否充分_數值', '辯證資料的能力_數值', '口條、呈現方式是否清晰_數值',
                          '是否具開創、建設性的想法_數值', '回答提問是否具邏輯、有條有理_數值']
    available_score_cols = [c for c in meeting_score_cols if c in meeting_data.columns] if not meeting_data.empty else []
    if available_score_cols:
        all_scores = meeting_data[available_score_cols].values.flatten()
        valid = all_scores[~pd.isna(all_scores)]
        meeting_avg = float(valid.mean()) if len(valid) > 0 else None
    else:
        meeting_avg = None
    meeting_status = _level(meeting_avg, th_score_green, th_score_red)

    # ── overall：取最差者（RED > YELLOW > GREEN）──
    priority = {'RED': 0, 'YELLOW': 1, 'GREEN': 2}
    overall = min([tech_status, epa_status, meeting_status], key=lambda s: priority[s])

    return {
        'overall': overall,
        'technical': {'status': tech_status, 'completion_rate': tech_rate},
        'epa':       {'status': epa_status,  'avg_score': epa_avg},
        'meeting':   {'status': meeting_status, 'avg_score': meeting_avg}
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

def show_grouped_skill_progress(skill_counts):
    """技能分組進度條：按三組呈現，每項 progress + ✓/⚠️ 標記"""
    for group_name, group_skills in SKILL_GROUPS.items():
        st.markdown(f"**{group_name}**")
        for skill in group_skills:
            data = skill_counts.get(skill)
            if data is None:
                # 該技能在 skill_counts 裡沒出現，代表 0 次
                completed = 0
                required  = PEDIATRIC_SKILL_REQUIREMENTS.get(skill, {}).get('minimum', 1)
            else:
                completed = data['completed']
                required  = data['required']

            progress_val = min(completed / required, 1.0) if required > 0 else 1.0
            done = completed >= required

            col1, col2 = st.columns([3, 1])
            with col1:
                st.progress(progress_val, text=f"{skill}　{completed}/{required}")
            with col2:
                if done:
                    st.markdown("✅", unsafe_allow_html=False)
                else:
                    st.markdown(f"⚠️ 還需 {required - completed} 次", unsafe_allow_html=False)
        st.divider()

def show_skill_details(resident_data, resident_name):
    """顯示詳細技能記錄"""
    st.subheader("詳細技能記錄")
    
    # 篩選包含技能評核的記錄
    skill_records = resident_data[resident_data['評核技術項目'].notna()].copy()
    
    if not skill_records.empty:
        # 選擇要顯示的欄位
        display_columns = ['評核日期', '評核教師', '評核技術項目', '可信賴程度', '熟練程度(自動判定)', '操作技術教師回饋']
        
        # 確保所有欄位都存在
        available_columns = [col for col in display_columns if col in skill_records.columns]
        
        if available_columns:
            # 按日期排序
            if '評核日期' in available_columns:
                skill_records = skill_records.sort_values('評核日期', ascending=False)
            
            st.dataframe(skill_records[available_columns], use_container_width=True)
        else:
            st.warning("沒有可用的技能記錄欄位")
    else:
        st.info("該住院醫師目前沒有技能評核記錄")

def show_skill_completion_stats(skill_counts):
    """顯示技能完成度統計"""
    st.subheader("技能完成度統計")
    
    # 計算統計資料
    total_skills = len(skill_counts)
    completed_skills = sum(1 for data in skill_counts.values() if data['completed'] >= data['required'])
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
        
        st.plotly_chart(fig, use_container_width=True)
        
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
        
        st.plotly_chart(fig_pie, use_container_width=True)

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
    st.dataframe(skill_df, use_container_width=True)
    
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
    
    st.plotly_chart(fig, use_container_width=True)

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
        st.plotly_chart(fig, use_container_width=True)
        
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
                st.dataframe(comparison_df, use_container_width=True)
        
    except Exception as e:
        st.error(f"創建雷達圖時發生錯誤：{str(e)}")

if __name__ == "__main__":
    show_pediatric_evaluation_section()
