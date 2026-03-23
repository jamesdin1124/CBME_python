"""
UGY EPA 統一資料服務
負責所有資料的載入、合併、處理、快取。
所有 UGY 頁面透過此模組取得資料，不直接操作 Supabase 或 Google Sheets。
"""

import pandas as pd
import streamlit as st
from datetime import datetime

from config.epa_constants import EPA_LEVEL_MAPPING
from modules.data_processing import convert_date_to_batch

# ═══════════════════════════════════════════════════════
# 快取 Key
# ═══════════════════════════════════════════════════════
_CACHE_KEY = 'ugy_epa_data'
_COMPAT_KEY = 'processed_df'  # 向後相容


# ═══════════════════════════════════════════════════════
# 底層資料來源
# ═══════════════════════════════════════════════════════

def fetch_supabase_records() -> pd.DataFrame | None:
    """從 Supabase ugy_epa_records 取得系統內 EPA 評核紀錄"""
    try:
        from modules.supabase_connection import SupabaseConnection
        conn = SupabaseConnection()
        result = conn.client.table('ugy_epa_records').select('*').order(
            '時間戳記', desc=True
        ).execute()
        if result.data:
            return pd.DataFrame(result.data)
        return None
    except Exception:
        return None


def fetch_google_sheet_data(sheet_title=None) -> pd.DataFrame | None:
    """從 Google Sheets 取得 EPA 評核資料"""
    try:
        from modules.google_connection import fetch_google_form_data
        df, _ = fetch_google_form_data(sheet_title=sheet_title)
        return df
    except Exception:
        return None


def _build_student_id_map() -> dict:
    """從 Supabase 學生名冊建立 姓名→學號 對照表"""
    try:
        from modules.supabase_connection import SupabaseConnection
        conn = SupabaseConnection()
        result = conn.client.table('pediatric_users').select(
            'username, full_name'
        ).eq('user_type', 'student').eq('is_active', True).execute()
        if result.data:
            return {r['full_name']: r['username']
                    for r in result.data if r.get('full_name')}
        return {}
    except Exception:
        return {}


# ═══════════════════════════════════════════════════════
# 資料處理
# ═══════════════════════════════════════════════════════

def _convert_epa_level(value) -> float | None:
    """將 EPA 等級文字轉為數值（使用統一 mapping）"""
    if pd.isna(value) or value is None:
        return None
    val = str(value).strip()
    if not val:
        return None
    # 直接查表
    score = EPA_LEVEL_MAPPING.get(val)
    if score is not None:
        return float(score)
    # 嘗試直接轉數字
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def fix_student_ids(df: pd.DataFrame) -> pd.DataFrame:
    """用學生名冊修正 DataFrame 中的學號欄位"""
    name_col = '學員姓名' if '學員姓名' in df.columns else (
        '姓名' if '姓名' in df.columns else None
    )
    if not name_col:
        return df
    mapping = _build_student_id_map()
    if not mapping:
        return df
    df = df.copy()
    df['學號'] = df[name_col].map(mapping).fillna(df.get('學號', ''))
    return df


def process_epa_data(df: pd.DataFrame, filter_teacher: bool = True) -> pd.DataFrame | None:
    """
    處理 EPA 評核資料：
    1. 過濾教師資料
    2. EPA 等級轉數值
    3. 日期/梯次計算
    4. 階層清理
    """
    if df is None or df.empty:
        return None

    df = df.copy()
    df = df.loc[:, ~df.columns.duplicated()]

    # 確保基本欄位存在
    if '學員自評EPA等級' not in df.columns:
        df['學員自評EPA等級'] = None
    if '教師評核EPA等級' not in df.columns:
        df['教師評核EPA等級'] = None
    # 確保姓名欄位統一
    if '學員姓名' in df.columns and '姓名' not in df.columns:
        df['姓名'] = df['學員姓名']
    elif '姓名' in df.columns and '學員姓名' not in df.columns:
        df['學員姓名'] = df['姓名']

    # ── 過濾教師資料 ──
    if filter_teacher and '教師' in df.columns:
        df = df[df['教師'].notna() & (df['教師'] != '')]

    if df.empty:
        return None

    # ── EPA 等級轉數值 ──
    if '教師評核EPA等級_數值' not in df.columns:
        df['教師評核EPA等級_數值'] = df['教師評核EPA等級'].apply(_convert_epa_level)
    else:
        # 填補 NaN
        mask = df['教師評核EPA等級_數值'].isna()
        if mask.any():
            df.loc[mask, '教師評核EPA等級_數值'] = (
                df.loc[mask, '教師評核EPA等級'].apply(_convert_epa_level)
            )
    # 確保數值型態
    df['教師評核EPA等級_數值'] = pd.to_numeric(df['教師評核EPA等級_數值'], errors='coerce')

    if '學員自評EPA等級_數值' not in df.columns:
        df['學員自評EPA等級_數值'] = df['學員自評EPA等級'].apply(_convert_epa_level)

    # ── 梯次計算（統一從日期計算，不覆蓋已有值）──
    # 優先使用 evaluation_date，其次用時間戳記
    if '梯次' not in df.columns:
        df['梯次'] = None

    mask_no_batch = df['梯次'].isna() | (df['梯次'] == '') | (df['梯次'] == '未知梯次')
    if mask_no_batch.any():
        date_col = None
        if 'evaluation_date' in df.columns:
            date_col = 'evaluation_date'
        elif '時間戳記' in df.columns:
            date_col = '時間戳記'
        if date_col:
            df.loc[mask_no_batch, '梯次'] = (
                df.loc[mask_no_batch, date_col].astype(str).apply(convert_date_to_batch)
            )

    # ── 階層清理 ──
    if '階層' in df.columns:
        df['階層'] = df['階層'].fillna('未知').astype(str).str.strip()
    else:
        df['階層'] = '未知'

    return df


# ═══════════════════════════════════════════════════════
# 主要 API
# ═══════════════════════════════════════════════════════

def load_all_data(include_google_sheets: bool = False,
                  filter_teacher: bool = True) -> pd.DataFrame | None:
    """
    載入並合併所有 UGY EPA 資料。

    Args:
        include_google_sheets: 是否同時載入 Google Sheets 歷史資料
        filter_teacher: 是否只保留有教師評核的紀錄

    Returns:
        處理後的 DataFrame，或 None
    """
    frames = []

    # 1. Supabase 系統評核
    supa_df = fetch_supabase_records()
    if supa_df is not None and not supa_df.empty:
        frames.append(supa_df)

    # 2. Google Sheets（可選）
    if include_google_sheets:
        gs_df = fetch_google_sheet_data()
        if gs_df is not None and not gs_df.empty:
            frames.append(gs_df)

    if not frames:
        return None

    # 合併
    if len(frames) == 1:
        merged = frames[0]
    else:
        merged = pd.concat(frames, ignore_index=True)

    # 處理
    processed = process_epa_data(merged, filter_teacher=filter_teacher)
    if processed is None or processed.empty:
        return None

    # 修正學號
    processed = fix_student_ids(processed)

    # 去重（學員姓名+EPA評核項目+教師+梯次）
    dedup_cols = [c for c in ['學員姓名', 'EPA評核項目', '教師', '梯次']
                  if c in processed.columns]
    if dedup_cols:
        processed = processed.drop_duplicates(subset=dedup_cols, keep='first')

    # 存入快取
    st.session_state[_CACHE_KEY] = processed
    st.session_state[_COMPAT_KEY] = processed  # 向後相容

    return processed


def get_data(filter_teacher: bool = True) -> pd.DataFrame | None:
    """
    取得快取資料，若無則自動從 Supabase 載入。
    每次呼叫都會合併最新的 Supabase 資料。
    """
    cached = st.session_state.get(_CACHE_KEY)

    if cached is None:
        # 首次：自動載入
        return load_all_data(include_google_sheets=False,
                             filter_teacher=filter_teacher)

    # 已有快取：合併最新 Supabase 資料（確保新提交的表單可見）
    supa_df = fetch_supabase_records()
    if supa_df is not None and not supa_df.empty:
        supa_df = fix_student_ids(supa_df)
        # 確保梯次存在
        if '梯次' not in supa_df.columns:
            supa_df['梯次'] = None
        date_col = 'evaluation_date' if 'evaluation_date' in supa_df.columns else '時間戳記'
        if date_col in supa_df.columns:
            mask = supa_df['梯次'].isna() | (supa_df['梯次'] == '')
            if mask.any():
                supa_df.loc[mask, '梯次'] = supa_df.loc[mask, date_col].astype(str).apply(convert_date_to_batch)

        combined = pd.concat([cached, supa_df], ignore_index=True)
        dedup_cols = [c for c in ['學員姓名', 'EPA評核項目', '教師', '梯次']
                      if c in combined.columns]
        if dedup_cols:
            combined = combined.drop_duplicates(subset=dedup_cols, keep='first')

        st.session_state[_CACHE_KEY] = combined
        st.session_state[_COMPAT_KEY] = combined
        return combined

    return cached


def refresh(include_google_sheets: bool = True,
            filter_teacher: bool = True) -> pd.DataFrame | None:
    """清除快取並重新載入所有資料"""
    st.session_state.pop(_CACHE_KEY, None)
    st.session_state.pop(_COMPAT_KEY, None)
    return load_all_data(include_google_sheets=include_google_sheets,
                         filter_teacher=filter_teacher)
