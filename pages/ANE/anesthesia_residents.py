import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import plotly.express as px
import numpy as np


def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    """用於自然排序的鍵函數"""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(_nsre, s)]


def convert_level_to_score(value):
    """將 LEVEL 轉換為數值分數"""
    if pd.isna(value):
        return 0
    
    # 轉換為大寫並移除空白
    value = str(value).upper().strip()
    
    # 定義轉換對照表
    level_map = {
        'LEVEL I': 1,
        'LEVEL II': 2,
        'LEVEL III': 3,
        'LEVEL IV': 4,
        'LEVEL V': 5,
        'I': 1,
        'II': 2,
        'III': 3,
        'IV': 4,
        'V': 5,
        'LEVEL 1': 1,
        'LEVEL 2': 2,
        'LEVEL 3': 3,
        'LEVEL 4': 4,
        'LEVEL 5': 5,
        '1': 1,
        '2': 2,
        '3': 3,
        '4': 4,
        '5': 5
    }
    
    return level_map.get(value, 0)


def calculate_average_scores(student_data, item_data):
    """計算特定評量項目的平均分數"""
    scores = {
        '學員自評': None,  # 初始化為 None
        '教師評核': None,
        '教師複評': None
    }
    
    # 收集所有非空值
    for eval_type in ['學員自評', '教師評核', '教師複評']:
        # 從 item_data 安全地獲取欄位名稱
        column = item_data.get(eval_type)
        
        # 檢查欄位名稱是否存在且該欄位確實存在於 student_data DataFrame 中
        if column and column in student_data.columns:
            # 嘗試獲取數據，移除 NaN
            values = student_data[column].dropna()
            # 嘗試轉換為數值型態，無法轉換的設為 NaN，再移除 NaN
            numeric_values = pd.to_numeric(values, errors='coerce').dropna()
            
            if not numeric_values.empty:
                scores[eval_type] = numeric_values.mean()
            # 如果 numeric_values 為空 (例如欄位存在但都是文字或 NaN)，則 scores[eval_type] 保持為 None
        # 如果欄位名稱不存在於 item_data 或 DataFrame 中，則 scores[eval_type] 保持為 None
            
    return scores


def get_epa_from_filename(filename):
    """從檔案名稱提取 EPA 編號 (例如 'EPA 3')"""
    if not isinstance(filename, str):
        return None
    match = re.search(r'EPA\s*(\d+)', filename, re.IGNORECASE)
    if match:
        return f"EPA {match.group(1)}"
    # 檢查是否為 coreEPA 格式
    match_core = re.search(r'coreEPA\s*(\d+)', filename, re.IGNORECASE)
    if match_core:
         return f"EPA {match_core.group(1)}"
    return None


def show_ANE_R_EPA_peer_analysis_section(df):
    """顯示ANE_R同梯次分析的函數"""
    
    st.subheader("麻醉科住院醫師分析")
    
    # 檢查是否從 new_dashboard.py 獲取資料
    if 'merged_data' not in st.session_state:
        st.warning("請先在側邊欄合併 Excel 檔案")
        return
        
    # 使用 new_dashboard.py 中的合併資料
    # 確保複製一份資料，避免修改原始 session state
    df = st.session_state.merged_data.copy()
    
    # --- 新增步驟：從檔案名稱提取 EPA Group ---
    if '檔案名稱' in df.columns:
        df['EPA_Group'] = df['檔案名稱'].apply(get_epa_from_filename)
    else:
        st.error("合併資料中缺少 '檔案名稱' 欄位，無法進行 EPA 分組分析。")
        return
    # -----------------------------------------

    # 在最上方顯示匯入的資料表 (包含 EPA_Group)
    st.markdown("### 匯入資料總覽 (含 EPA 分組)")
    st.dataframe(
        df,
        use_container_width=True,
        height=300
    )
    
    # 添加分隔線
    st.markdown("---")

    # 取得所有可用的學員名稱
    students = sorted(df['學員'].unique(), key=natural_sort_key) # 自然排序
    selected_student = st.selectbox(
        '請選擇要分析的學員：',
        students,
        key='ane_r_student_selector'
    )

    # 定義所有 EPA 的評量項目對應 (保持不變)
    epa_items = {
        'EPA 1': {
            'PC1': {
                '名稱': '麻醉前病人評估、診斷與前置作業',
                '學員自評': '1.Patient Care 1(PC1). 麻醉前病人評估、診斷與前置作業 (學員自評)[單選]',
                '教師評核': '1.Patient Care 1(PC1). 麻醉前病人評估、診斷與前置作業 (教師評核)[單選]',
                '教師複評': '1.Patient Care 1(PC1). 麻醉前病人評估、診斷與前置作業 (教師評核)[單選].1'
            },
            'SBP2': {
                '名稱': '病人安全及照護品質提升',
                '學員自評': '13.System-based Practice 2 (SBP2). 病人安全及照護品質提升(學員自評) [單選]',
                '教師評核': '13.System-based Practice 2 (SBP2). 病人安全及照護品質提升(教師評核) [單選]',
                '教師複評': '13.System-based Practice 2 (SBP2). 病人安全及照護品質提升(教師評核) [單選].1'
            },
            'ICS1': {
                '名稱': '與病患及家屬溝通',
                '學員自評': '23. Interpersonal communication skill 1 (ICS1). 與病患及家屬溝通(學員自評) [單選]',
                '教師評核': '23. Interpersonal communication skill 1 (ICS1). 與病患及家屬溝通(教師評核) [單選]',
                '教師複評': '23. Interpersonal communication skill 1 (ICS1). 與病患及家屬溝通(教師評核) [單選].1'
            },
            'ICS2': {
                '名稱': '與其他專業人員溝通',
                '學員自評': '24. Interpersonal communication skill 2 (ICS2). 與其他專業人員溝通(學員自評) [單選]',
                '教師評核': '24. Interpersonal communication skill 2 (ICS2). 與其他專業人員溝通(教師評核) [單選]',
                '教師複評': '24. Interpersonal communication skill 2 (ICS2). 與其他專業人員溝通(教師評核) [單選].1'
            }
        },
        'EPA 2': {
            'PC2': {
                '名稱': '麻醉計劃與執行',
                '學員自評': '2. Patient care 2 (PC2). 麻醉計劃與執行(學員自評) [單選]',
                '教師評核': '2. Patient care 2 (PC2). 麻醉計劃與執行(教師評核) [單選]',
                '教師複評': '2. Patient care 2 (PC2). 麻醉計劃與執行(教師評核) [單選].1'
            },
            'PC5': {
                '名稱': '危機處理',
                '學員自評': '5. Patient care 5 (PC5).危機處理 (學員自評)[單選]',
                '教師評核': '5. Patient care 5 (PC5).危機處理 (教師評核)[單選]',
                '教師複評': '5. Patient care 5 (PC5).危機處理 (教師評核)[單選].1'
            },
            'PC6': {
                '名稱': '手術室外重症病人之檢傷與處理',
                '學員自評': '6. Patient care 6 (PC6).手術室外重症病人之檢傷與處理(學員自評) [單選]',
                '教師評核': '6. Patient care 6 (PC6).手術室外重症病人之檢傷與處理(教師評核) [單選]',
                '教師複評': '6. Patient care 6 (PC6).手術室外重症病人之檢傷與處理(教師評核 [單選]' # 注意這裡結尾可能不完整
            },
            'PC9': {
                '名稱': '技術技能：監測設備的使用和判讀',
                '學員自評': '9. Patient care 9 (PC9).技術技能：監測設備的使用和判讀(學員自評) [單選]',
                '教師評核': '9. Patient care 9 (PC9).技術技能：監測設備的使用和判讀(教師評核) [單選]',
                '教師複評': '9. Patient care 9 (PC9).技術技能：監測設備的使用和判讀(教師評核) [單選].1'
            },
            'SBP1': {
                '名稱': '實際病人照護與醫療照護體系結合',
                '學員自評': '12. System based practice (SBP1). 實際病人照護與醫療照護體系結合(學員自評) [單選]',
                '教師評核': '12. System based practice (SBP1). 實際病人照護與醫療照護體系結合(教師評核) [單選]',
                '教師複評': '12. System based practice (SBP1). 實際病人照護與醫療照護體系結合(教師評核) [單選].1'
            },
            'PROF1': {
                '名稱': '對病人，家人及社會的責任',
                '學員自評': '18. Professionalism 1(PROF1). 對病人，家人及社會的責任(學員自評) [單選]',
                '教師評核': '18. Professionalism 1(PROF1). 對病人，家人及社會的責任(教師評核) [單選]',
                '教師複評': '18. Professionalism 1(PROF1). 對病人，家人及社會的責任(教師評核) [單選].1'
            },
            'ICS3': {
                '名稱': '團隊及領導技巧',
                '學員自評': '25. Interpersonal communication skill (ICS3).團隊及領導技巧 (學員自評)[單選]',
                '教師評核': '25. Interpersonal communication skill (ICS3).團隊及領導技巧 (教師評核)[單選]',
                '教師複評': '25. Interpersonal communication skill (ICS3).團隊及領導技巧 (教師評核)[單選].1'
            }
        },
        'EPA 3': {
            'PC3': {
                '名稱': '手術中的疼痛處理',
                '學員自評': '3. Patient care 3 (PC3). 手術中的疼痛處理(學員自評) [單選]',
                '教師評核': '3. Patient care 3 (PC3). 手術中的疼痛處理(教師評核) [單選]',
                '教師複評': '3. Patient care 3 (PC3). 手術中的疼痛處理(教師評核) [單選].1'
            },
            'PC7': {
                '名稱': '急性、慢性以及癌症相關疼痛的照會和處置',
                '學員自評': '7. Patient care 7 (PC7).急性、慢性以及癌症相關疼痛的照會和處置(學員自評) [單選]',
                '教師評核': '7. Patient care 7 (PC7).急性、慢性以及癌症相關疼痛的照會和處置(教師評核) [單選]',
                '教師複評': '7. Patient care 7 (PC7).急性、慢性以及癌症相關疼痛的照會和處置(教師評核) [單選].1'
            },
            'PC10': {
                '名稱': '技術技能：區域麻醉',
                '學員自評': '10. Patient care 10 (PC10).技術技能：區域麻醉 (學員自評)[單選]',
                '教師評核': '10. Patient care 10 (PC10).技術技能：區域麻醉(教師評核) [單選]',
                '教師複評': '10. Patient care 10 (PC10).技術技能：區域麻醉(教師評核) [單選].1'
            },
            'SBP1': {
                '名稱': '實際病人照護與醫療照護體系結合',
                '學員自評': '12. System based practice (SBP1). 實際病人照護與醫療照護體系結合(學員自評) [單選]',
                '教師評核': '12. System based practice (SBP1). 實際病人照護與醫療照護體系結合(教師評核) [單選]',
                '教師複評': '12. System based practice (SBP1). 實際病人照護與醫療照護體系結合(教師評核) [單選].1'
            },
            'SBP2': {
                '名稱': '病人安全及照護品質提升',
                '學員自評': '13.System-based Practice 2 (SBP2). 病人安全及照護品質提升(學員自評) [單選]',
                '教師評核': '13.System-based Practice 2 (SBP2). 病人安全及照護品質提升(教師評核) [單選]',
                '教師複評': '13.System-based Practice 2 (SBP2). 病人安全及照護品質提升(教師評核) [單選].1'
            },
            'PROF2': {
                '名稱': '誠實，廉正和倫理的行為',
                '學員自評': '19. Professionalism 2(PROF2). 誠實，廉正和倫理的行為(學員自評) [單選]',
                '教師評核': '19. Professionalism 2(PROF2). 誠實，廉正和倫理的行為(教師評核) [單選]',
                '教師複評': '19. Professionalism 2(PROF2). 誠實，廉正和倫理的行為(教師評核) [單選].1'
            },
            'ICS1': {
                '名稱': '與病患及家屬溝通',
                '學員自評': '23. Interpersonal communication skill 1 (ICS1). 與病患及家屬溝通(學員自評) [單選]',
                '教師評核': '23. Interpersonal communication skill 1 (ICS1). 與病患及家屬溝通(教師評核) [單選]',
                '教師複評': '23. Interpersonal communication skill 1 (ICS1). 與病患及家屬溝通(教師評核) [單選].1'
            },
            'ICS2': {
                '名稱': '與其他專業人員溝通',
                '學員自評': '24. Interpersonal communication skill 2 (ICS2). 與其他專業人員溝通(學員自評) [單選]',
                '教師評核': '24. Interpersonal communication skill 2 (ICS2). 與其他專業人員溝通(教師評核) [單選]',
                '教師複評': '24. Interpersonal communication skill 2 (ICS2). 與其他專業人員溝通(教師評核) [單選].1'
            }
        },
        'EPA 4': {
            'PC1': {
                '名稱': '麻醉前病人評估、診斷與前置作業',
                '學員自評': '1.Patient Care 1(PC1). 麻醉前病人評估、診斷與前置作業 (學員自評)[單選]',
                '教師評核': '1.Patient Care 1(PC1). 麻醉前病人評估、診斷與前置作業 (教師評核)[單選]',
                '教師複評': '1.Patient Care 1(PC1). 麻醉前病人評估、診斷與前置作業 (教師評核)[單選].1'
            },
            'PC2': {
                '名稱': '麻醉計劃與執行',
                '學員自評': '2. Patient care 2 (PC2). 麻醉計劃與執行(學員自評)[單選]',
                '教師評核': '2. Patient care 2 (PC2). 麻醉計劃與執行(教師評核) [單選]',
                '教師複評': '2. Patient care 2 (PC2). 麻醉計劃與執行(教師評核) [單選].1'
            },
            'PC8': {
                '名稱': '技術技能：呼吸道處置',
                '學員自評': '8. Patient care 8(PC8).技術技能：呼吸道處置(學員自評) [單選]',
                '教師評核': '8. Patient care 8(PC8).技術技能：呼吸道處置(教師評核) [單選]',
                '教師複評': '8. Patient care 8(PC8).技術技能：呼吸道處置(教師評核) [單選].1'
            },
            'PBLI4': {
                '名稱': '對病人、家屬、學生、大眾和其他醫事人員的教育',
                '學員自評': '17. Practice based learning and improving 4 (PBLI4). 對病人、家屬、學生、大眾和其他醫事人員的教育(學員自評) [單選]',
                '教師評核': '17. Practice based learning and improving 4 (PBLI4). 對病人、家屬、學生、大眾和其他醫事人員的教育 (教師評核)[單選]',
                '教師複評': '17. Practice based learning and improving 4 (PBLI4). 對病人、家屬、學生、大眾和其他醫事人員的教育 (教師評核)[單選].1'
            },
            'PROF3': {
                '名稱': '對醫療機構，科部以及同事的委身',
                '學員自評': '20. Professionalism 3(PROF 3). 對醫療機構，科部以及同事的委身(學員自評) [單選]',
                '教師評核': '20. Professionalism 3(PROF 3). 對醫療機構，科部以及同事的委身(教師評核) [單選]',
                '教師複評': '20. Professionalism 3(PROF 3). 對醫療機構，科部以及同事的委身(教師評核) [單選].1'
            },
            'ICS1': {
                '名稱': '與病患及家屬溝通',
                '學員自評': '23. Interpersonal communication skill 1 (ICS1). 與病患及家屬溝通(學員自評) [單選]',
                '教師評核': '23. Interpersonal communication skill 1 (ICS1). 與病患及家屬溝通(教師評核) [單選]',
                '教師複評': '23. Interpersonal communication skill 1 (ICS1). 與病患及家屬溝通(教師評核) [單選].1'
            },
            'ICS2': {
                '名稱': '與其他專業人員溝通',
                '學員自評': '24. Interpersonal communication skill 2 (ICS2). 與其他專業人員溝通(學員自評) [單選]',
                '教師評核': '24. Interpersonal communication skill 2 (ICS2). 與其他專業人員溝通(教師評核) [單選]',
                '教師複評': '24. Interpersonal communication skill 2 (ICS2). 與其他專業人員溝通(教師評核) [單選].1'
            }
        },
        'EPA 5': {
            'PC4': {
                '名稱': '圍術期併發症的處理',
                '學員自評': '1.Patient Care 4(PC4). 圍術期併發症的處理(學員自評) [單選]',
                '教師評核': '1.Patient Care 4(PC4). 圍術期併發症的處理(教師評核) [單選]',
                '教師複評': '1.Patient Care 4(PC4). 圍術期併發症的處理(教師評核) [單選].1'
            },
            'PBLI1': {
                '名稱': '將品質改進及病人安全納入個人工作之中',
                '學員自評': '14. Practice based learning and improving 1 (PBLI1).將品質改進及病人安全納入個人工作之中(學員自評) [單選]',
                '教師評核': '14. Practice based learning and improving 1 (PBLI1).將品質改進及病人安全納入個人工作之中(教師評核) [單選]',
                '教師複評': '14. Practice based learning and improving 1 (PBLI1).將品質改進及病人安全納入個人工作之中(教師評核) [單選].1'
            },
            'PBLI2': {
                '名稱': '實踐分析找出需要改進的地方',
                '學員自評': '15. Practice based learning and improving 2 (PBLI2).實踐分析找出需要改進的地方(學員自評) [單選]',
                '教師評核': '15. Practice based learning and improving 2 (PBLI2).實踐分析找出需要改進的地方(教師評核) [單選]',
                '教師複評': '15. Practice based learning and improving 2 (PBLI2).實踐分析找出需要改進的地方(教師評核) [單選].1'
            },
            'ICS1': {
                '名稱': '與病患及家屬溝通',
                '學員自評': '23. Interpersonal communication skill 1 (ICS1). 與病患及家屬溝通(學員自評) [單選]',
                '教師評核': '23. Interpersonal communication skill 1 (ICS1). 與病患及家屬溝通(教師評核) [單選]',
                '教師複評': '23. Interpersonal communication skill 1 (ICS1). 與病患及家屬溝通(教師評核) [單選].1'
            },
            'ICS2': {
                '名稱': '與其他專業人員溝通',
                '學員自評': '24. Interpersonal communication skill 2 (ICS2). 與其他專業人員溝通(學員自評) [單選]',
                '教師評核': '24. Interpersonal communication skill 2 (ICS2). 與其他專業人員溝通(教師評核) [單選]',
                '教師複評': '24. Interpersonal communication skill 2 (ICS2). 與其他專業人員溝通(教師評核) [單選].1'
            }
        },
        'EPA 6': {
            'SBP2': {
                '名稱': '病人安全及照護品質提升',
                '學員自評': '13.System-based Practice 2 (SBP2). 病人安全及照護品質提升(學員自評) [單選]',
                '教師評核': '13.System-based Practice 2 (SBP2). 病人安全及照護品質提升(教師評核) [單選]',
                '教師複評': '13.System-based Practice 2 (SBP2). 病人安全及照護品質提升(教師評核) [單選].1'
            },
            'PBLI1': {
                '名稱': '將品質改進及病人安全納入個人工作之中',
                '學員自評': '14. Practice based learning and improving 1 (PBLI1).將品質改進及病人安全納入個人工作之中(學員自評) [單選]',
                '教師評核': '14. Practice based learning and improving 1 (PBLI1).將品質改進及病人安全納入個人工作之中(教師評核) [單選]',
                '教師複評': '14. Practice based learning and improving 1 (PBLI1).將品質改進及病人安全納入個人工作之中(教師評核) [單選].1'
            },
            'PBLI2': {
                '名稱': '實踐分析找出需要改進的地方',
                '學員自評': '15. Practice based learning and improving 2 (PBLI2).實踐分析找出需要改進的地方(學員自評) [單選]',
                '教師評核': '15. Practice based learning and improving 2 (PBLI2).實踐分析找出需要改進的地方(教師評核) [單選]',
                '教師複評': '15. Practice based learning and improving 2 (PBLI2).實踐分析找出需要改進的地方(教師評核) [單選].1'
            },
            'PBLI3': {
                '名稱': '自主學習',
                '學員自評': '16. Practice based learning and improving 3 (PBLI3).自主學習 (學員自評)[單選]',
                '教師評核': '16. Practice based learning and improving 3 (PBLI3).自主學習 (教師評核)[單選]',
                '教師複評': '16. Practice based learning and improving 3 (PBLI3).自主學習 (教師評核)[單選].1'
            },
            'PROF4': {
                '名稱': '接受和提供回饋',
                '學員自評': '21. Professionalism 4 (PROF4). 接受和提供回饋(學員自評) [單選]',
                '教師評核': '21. Professionalism 4 (PROF4). 接受和提供回饋(教師評核) [單選]',
                '教師複評': '21. Professionalism 4 (PROF4). 接受和提供回饋(教師評核) [單選].1'
            },
            'PROF5': {
                '名稱': '維護個人情緒，身體和精神健康的責任',
                '學員自評': '22. Professionalism 5 (PROF5). 維護個人情緒，身體和精神健康的責任 (學員自評)[單選]',
                '教師評核': '22. Professionalism 5 (PROF5). 維護個人情緒，身體和精神健康的責任 (教師評核)[單選]',
                '教師複評': '22. Professionalism 5 (PROF5). 維護個人情緒，身體和精神健康的責任 (教師評核)[單選].1'
            },
            'ICS3': {
                '名稱': '團隊及領導技巧',
                '學員自評': '25. Interpersonal communication skill 3 (ICS3).團隊及領導技巧(學員自評) [單選]',
                '教師評核': '25. Interpersonal communication skill 3 (ICS3).團隊及領導技巧(教師評核) [單選]',
                '教師複評': '25. Interpersonal communication skill 3 (ICS3).團隊及領導技巧(教師評核) [單選].1' # 注意這裡的 EPA 編號
            },
            'MK1': {
                '名稱': '生物醫學、臨床、流行病學與社會行為科學的知識',
                '學員自評': '11. Medical knowledge 1 (MK1).生物醫學、臨床、流行病學與社會行為科學的知識(學員自評) [單選]',
                '教師評核': '11. Medical knowledge 1 (MK1).生物醫學、臨床、流行病學與社會行為科學的知識(教師評核) [單選]',
                '教師複評': '11. Medical knowledge 1 (MK1).生物醫學、臨床、流行病學與社會行為科學的知識(教師評核) [單選].1'
            }
        }
    }

    # 篩選選定學員的資料 (已包含 EPA_Group)
    student_data = df[df['學員'] == selected_student]
    
    # 依序分析每個EPA (從預定義列表)
    for epa_name in ['EPA 1', 'EPA 2', 'EPA 3', 'EPA 4', 'EPA 5', 'EPA 6']:
        st.markdown(f"### {epa_name}")
        
        # --- 修改：篩選特定 EPA 的資料 ---
        epa_specific_student_data = student_data[student_data['EPA_Group'] == epa_name]
        epa_specific_all_data = df[df['EPA_Group'] == epa_name]
        # ------------------------------------
        
        # --- 新增：檢查是否有該 EPA 的資料 ---
        if epa_specific_student_data.empty:
            st.info(f"學員 {selected_student} 在 {epa_name} 項目中沒有有效的評核資料。")
            st.markdown("---")
            continue # 跳到下一個 EPA
        # ------------------------------------

        # 取得該EPA的評量項目
        selected_items = epa_items.get(epa_name, {})
        
        # 準備雷達圖數據
        categories = []
        self_eval = []
        teacher_eval = []
        teacher_review = []
        student_avg = []
        all_students_avg = []
        
        # 處理每個評量項目
        for item_key, item_data in selected_items.items():
            # --- 修改：使用篩選後的資料計算分數 ---
            scores = calculate_average_scores(epa_specific_student_data, item_data)
            all_students_scores = calculate_average_scores(epa_specific_all_data, item_data)
            # ----------------------------------------
            
            # 只有當至少有一個評分存在時才加入該項目
            # 確保欄位存在於 item_data 中
            self_eval_col = item_data.get('學員自評')
            teacher_eval_col = item_data.get('教師評核')
            teacher_review_col = item_data.get('教師複評')

            # 檢查該評量項目對應的欄位是否存在於 *篩選後的* 資料中
            item_present_in_student_data = (
                (self_eval_col and self_eval_col in epa_specific_student_data.columns) or
                (teacher_eval_col and teacher_eval_col in epa_specific_student_data.columns) or
                (teacher_review_col and teacher_review_col in epa_specific_student_data.columns)
            )
            
            # 只有當該項目欄位存在於當前 EPA 的資料中，才將其加入雷達圖
            if item_present_in_student_data:
                 # 檢查分數是否有效 (至少有一個不是 None)
                 if any(score is not None for score in scores.values()) or any(score is not None for score in all_students_scores.values()):
                    categories.append(f"{item_key}:<br>{item_data['名稱']}")
                    
                    # 第一個圖的數據 (使用計算結果，若為 None 則為 0)
                    self_eval.append(scores.get('學員自評', 0) if scores.get('學員自評') is not None else 0)
                    teacher_eval.append(scores.get('教師評核', 0) if scores.get('教師評核') is not None else 0)
                    teacher_review.append(scores.get('教師複評', 0) if scores.get('教師複評') is not None else 0)
                    
                    # 第二個圖的數據
                    student_teacher_scores = [scores.get('教師評核'), scores.get('教師複評')]
                    student_teacher_scores = [s for s in student_teacher_scores if s is not None]
                    student_avg.append(np.mean(student_teacher_scores) if student_teacher_scores else 0)
                    
                    all_teacher_scores = [all_students_scores.get('教師評核'), all_students_scores.get('教師複評')]
                    all_teacher_scores = [s for s in all_teacher_scores if s is not None]
                    all_students_avg.append(np.mean(all_teacher_scores) if all_teacher_scores else 0)

        # 確保有資料才繪製雷達圖
        if categories:
            # 當只有兩個項目時，添加一個空白項目以改善可讀性
            if len(categories) == 2:
                categories.append("空白項目")
                self_eval.append(0)
                teacher_eval.append(0)
                teacher_review.append(0)
                student_avg.append(0)
                all_students_avg.append(0)
            
            # 確保資料首尾相連
            # 檢查 categories 是否為空，避免索引錯誤
            if categories:
                categories.append(categories[0])
                self_eval.append(self_eval[0])
                teacher_eval.append(teacher_eval[0])
                teacher_review.append(teacher_review[0])
                student_avg.append(student_avg[0])
                all_students_avg.append(all_students_avg[0])
            else:
                st.warning(f"在 {epa_name} 中沒有找到有效的評量項目資料可供繪圖。")
                st.markdown("---")
                continue # 跳到下一個 EPA
            
            # 建立兩欄布局來並排顯示圖表
            left_col, right_col = st.columns(2)
            
            with left_col:
                # 第一個雷達圖（自評與教師評核）
                fig1 = go.Figure()
                
                fig1.add_trace(go.Scatterpolar(
                    r=self_eval,
                    theta=categories,
                    name='學員自評',
                    line=dict(color='blue', width=2, dash='solid'),
                    opacity=0.8
                ))
                
                fig1.add_trace(go.Scatterpolar(
                    r=teacher_eval,
                    theta=categories,
                    name='教師評核',
                    line=dict(color='red', width=2, dash='dash'),
                    opacity=0.8
                ))
                
                fig1.add_trace(go.Scatterpolar(
                    r=teacher_review,
                    theta=categories,
                    name='教師複評',
                    line=dict(color='green', width=2, dash='dot'),
                    opacity=0.8
                ))
                
                # 更新第一個圖的布局
                fig1.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True, 
                            range=[0, 5],
                            tickfont=dict(color='black')
                        ),
                        angularaxis=dict(
                            tickfont=dict(size=9) # 縮小字體
                        )
                    ),
                    showlegend=True,
                    legend=dict(
                        yanchor="top",
                        y=1.2,
                        xanchor="right",  # 將圖例置於右側
                        x=1.1  # 調整水平位置
                    ),
                    title=f"{selected_student} - {epa_name}<br>評量雷達圖",
                    height=400,
                    width=400
                )
                 # 更新 ticktext 以避免重複顯示第一個標籤
                fig1.update_polars(angularaxis_ticktext=categories[:-1])
                
                st.plotly_chart(fig1, use_container_width=True)
            
            with right_col:
                # 第二個雷達圖（個人平均與全體平均）
                fig2 = go.Figure()
                
                fig2.add_trace(go.Scatterpolar(
                    r=student_avg,
                    theta=categories,
                    name='個人教師評核平均',
                    line=dict(color='red', width=2),
                    fill='toself',
                    fillcolor='rgba(255, 0, 0, 0.2)'
                ))
                
                fig2.add_trace(go.Scatterpolar(
                    r=all_students_avg,
                    theta=categories,
                    name='全體教師評核平均',
                    line=dict(color='black', width=2)
                ))
                
                # 更新第二個圖的布局
                fig2.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True, 
                            range=[0, 5],
                            tickfont=dict(color='black')
                        ),
                        angularaxis=dict(
                            tickfont=dict(size=9) # 縮小字體
                        )
                    ),
                    showlegend=True,
                    legend=dict(
                        yanchor="top",
                        y=1.2,
                        xanchor="right",  # 將圖例置於右側
                        x=1.1  # 調整水平位置
                    ),
                    title=f"{selected_student} - {epa_name}<br>教師評核平均比較",
                    height=400,
                    width=400
                )
                 # 更新 ticktext 以避免重複顯示第一個標籤
                fig2.update_polars(angularaxis_ticktext=categories[:-1])
                
                st.plotly_chart(fig2, use_container_width=True)
            
            # 在每個EPA後添加分隔線
            st.markdown("---")
        else:
             # 即使 epa_specific_student_data 不為空，也可能沒有任何欄位實際存在於這些資料中
            st.info(f"學員 {selected_student} 在 {epa_name} 項目中，沒有找到對應 {epa_items[epa_name].keys()} 的有效評核資料欄位。")
            st.markdown("---")


    # --- 以下的核心技能、EPA評量比較、作業繳交等部分邏輯不變 ---
    # --- 確保這些部分也使用原始 student_data 或 df (未按EPA_Group篩選) ---
    
    # 篩選選定學員的資料 (原始，未按 EPA Group 過濾)
    original_student_data = df[df['學員'] == selected_student]

    # 在分析開始前先顯示完整的資料表
    st.markdown("### 選定學員完整資料表")
    st.dataframe(
        original_student_data,
        use_container_width=True,
        height=300
    )
    
    # 修改核心技能分析部分
    st.subheader("核心技能分析")

    # 使用原始 df 資料進行篩選
    core_skill_data = df[
        (df['學員'] == selected_student) &
        (df['檔案名稱'].str.contains('核心技能', na=False))
    ]
    # ... (核心技能後續代碼不變)
    # 加入除錯資訊
    st.write(f"找到的核心技能資料筆數：{len(core_skill_data)}")

    if not core_skill_data.empty:
        # 顯示核心技能資料表
        st.markdown("### 核心技能評核資料")
        
        # 顯示資料表
        st.dataframe(
            core_skill_data,
            use_container_width=True,
            height=200
        )
    else:
        st.warning("未找到核心技能相關資料")

    # 取得所有學員 (應為核心技能的學員)
    core_skill_students = core_skill_data['學員'].unique()
    
    # 為每個學員建立雷達圖
    for student in core_skill_students:
        # 建立兩欄佈局
        col1, col2 = st.columns([1, 1])
        
        # 取得該學員的資料
        student_core_data = core_skill_data[core_skill_data['學員'] == student]
        
        # 取得臨床訓練計畫
        training_plan = student_core_data['臨床訓練計畫'].iloc[0] if '臨床訓練計畫' in student_core_data.columns and not student_core_data.empty else '未知'
        
        with col1:
            # 準備雷達圖資料
            skill_scores = {}
            # 計算同儕平均需要的完整核心技能資料
            all_core_skill_data = df[df['檔案名稱'].str.contains('核心技能', na=False)]

            for _, row in student_core_data.iterrows():
                filename = row['檔案名稱']
                # 修改正則表達式以匹配 '臨床核心技能' 後的任何字符直到 '.xls'
                match = re.search(r'^臨床核心技能\s*(.*?)(?:\s*\([0-9]+\))?\.xls', filename, re.IGNORECASE)
                if match:
                    skill_name = match.group(1).strip()
                    skill_key = skill_name
                    
                    # 確保 '教師評核' 欄位存在且值有效
                    if '教師評核' in row and pd.notna(row['教師評核']):
                        try:
                            score = float(row['教師評核'])
                            skill_scores[skill_key] = score
                        except (ValueError, TypeError):
                            st.warning(f"無法轉換核心技能評核分數：{row['教師評核']} (技能: {skill_name})")
            
            if skill_scores:
                # 建立雷達圖
                fig_core = go.Figure()
                
                # 計算同儕平均
                peer_averages = {}
                unique_core_skills = list(skill_scores.keys()) # 以當前學生有的技能為準

                for skill_key in unique_core_skills:
                     # 篩選出所有學生關於這個特定技能的資料
                     # 需要反向查找包含此 skill_key 的檔案名稱模式
                     # 注意：這假設 skill_key 能唯一對應到檔案名稱中的模式
                     # 這一步可能需要更精確的匹配邏輯，暫時使用字串包含
                    skill_files_data = all_core_skill_data[
                         all_core_skill_data['檔案名稱'].str.contains(re.escape(skill_key), case=False, na=False) & 
                         all_core_skill_data['檔案名稱'].str.contains('核心技能', case=False, na=False)
                    ]
                    
                    if not skill_files_data.empty and '教師評核' in skill_files_data.columns:
                        valid_peer_scores = pd.to_numeric(skill_files_data['教師評核'], errors='coerce').dropna()
                        if not valid_peer_scores.empty:
                            peer_averages[skill_key] = valid_peer_scores.mean()
                        else:
                            peer_averages[skill_key] = 0 # 或 None
                    else:
                        peer_averages[skill_key] = 0 # 或 None
                
                # 確保數據點首尾相連
                skills = list(skill_scores.keys())
                scores = [skill_scores.get(skill, 0) for skill in skills] # 使用 get 以防萬一
                peer_scores = [peer_averages.get(skill, 0) for skill in skills]
                
                # 當只有兩個項目時，添加一個空白項目以改善可讀性
                if len(skills) == 2:
                    skills.append("空白項目")
                    scores.append(0)
                    peer_scores.append(0)
                
                skills_closed = skills + [skills[0]] if skills else []
                scores_closed = scores + [scores[0]] if scores else []
                peer_scores_closed = peer_scores + [peer_scores[0]] if peer_scores else []
                
                if skills_closed:
                    # 先畫同儕平均（黑色）
                    fig_core.add_trace(go.Scatterpolar(
                        r=peer_scores_closed,
                        theta=skills_closed,
                        name='同儕平均',
                        line=dict(color='rgba(0, 0, 0, 1)', width=2),
                    ))
                    
                    # 後畫學生本人（紅色）
                    fig_core.add_trace(go.Scatterpolar(
                        r=scores_closed,
                        theta=skills_closed,
                        name=student,
                        fill='toself',
                        fillcolor='rgba(255, 0, 0, 0.2)',
                        line=dict(color='rgba(255, 0, 0, 1)', width=2),
                    ))
                    
                    fig_core.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 5]
                            ),
                            angularaxis=dict(
                                tickfont=dict(size=9) # 縮小字體
                            )
                        ),
                        showlegend=True,
                        legend=dict(
                            yanchor="top",
                            y=1.2,
                            xanchor="right",  # 將圖例置於右側
                            x=1.1  # 調整水平位置
                        ),
                        title=f"{student} ({training_plan}) - 核心技能評核",
                        height=400,
                        width=400
                    )
                     # 更新 ticktext 以避免重複顯示第一個標籤
                    fig_core.update_polars(angularaxis_ticktext=skills_closed[:-1])
                    
                    st.plotly_chart(fig_core, use_container_width=True)
                else:
                    st.warning(f"無法為 {student} 繪製核心技能雷達圖 (無有效標籤數據)。")
            else:
                st.warning(f"沒有找到 {student} 的有效核心技能評核分數")
        
        with col2:
            st.markdown("### 教師評語")
            if not student_core_data.empty:
                for _, row in student_core_data.iterrows():
                    filename = row['檔案名稱']
                    match = re.search(r'^臨床核心技能\s*(.*?)(?:\s*\([0-9]+\))?\.xls', filename, re.IGNORECASE)
                    if match:
                        skill_name = match.group(1).strip()
                        if '教師評語與總結' in row and pd.notna(row['教師評語與總結']) and str(row['教師評語與總結']).strip():
                            st.markdown(f"**{skill_name}**：{row['教師評語與總結']}")
            else:
                 st.write("無核心技能評語資料。")

    # EPA 評量比較部分 (這部分似乎是重複的，但來自舊的 coreEPA 檔案)
    st.subheader("EPA 評量比較 (舊 CoreEPA 檔案)")
    
    # 從選定學員的資料中找出 EPA 相關的資料 (使用原始 student_data)
    epa_comparison_data = original_student_data[
        original_student_data['檔案名稱'].str.contains('coreEPA', na=False)
    ]

    if not epa_comparison_data.empty:
        # 找出包含 "EPA" 和 "教師評量" 的評分欄位
        # 需要排除 'EPA_Group' 欄位
        score_columns = [col for col in epa_comparison_data.columns 
                         if 'EPA' in col and '教師評量' in col and col != 'EPA_Group']
        
        # 顯示 EPA 資料表
        st.markdown("### EPA 評核資料 (舊 CoreEPA)")
        display_columns = [
            '學員', 
            '臨床訓練計畫', 
            '檔案名稱'
        ]
        # 確保要顯示的欄位存在
        display_columns.extend([col for col in score_columns if col in epa_comparison_data.columns])
        display_columns.extend([col for col in [
            '初評回饋：',
            '複評回饋：',
            '教師評語與總結'
        ] if col in epa_comparison_data.columns])
        
        st.dataframe(
            epa_comparison_data[display_columns],
            use_container_width=True,
            height=200
        )

        # 取得所有學員 (應為舊 CoreEPA 的學員)
        epa_comparison_students = epa_comparison_data['學員'].unique()
        
        # 為每個學員建立雷達圖
        for student in epa_comparison_students:
            # 建立兩欄佈局
            col1, col2 = st.columns([1, 1])
            
            # 取得該學員的資料
            student_epa_comp_data = epa_comparison_data[epa_comparison_data['學員'] == student]
            
            # 取得臨床訓練計畫
            training_plan = student_epa_comp_data['臨床訓練計畫'].iloc[0] if '臨床訓練計畫' in student_epa_comp_data.columns and not student_epa_comp_data.empty else '未知'
            
            with col1:
                # 準備雷達圖資料
                student_scores = []
                peer_scores = []
                display_labels = []
                
                # 取得當前學生的訓練計畫
                current_training_program = student_epa_comp_data['臨床訓練計畫'].iloc[0] if '臨床訓練計畫' in student_epa_comp_data.columns and not student_epa_comp_data.empty else None
                
                # 篩選同訓練計畫的同儕資料
                # 需要使用包含 coreEPA 的完整資料 df
                all_core_epa_data = df[df['檔案名稱'].str.contains('coreEPA', na=False)]
                peer_df = pd.DataFrame() # 初始化空的 DataFrame
                if current_training_program:
                     peer_df = all_core_epa_data[
                         (all_core_epa_data['臨床訓練計畫'] == current_training_program) & 
                         (all_core_epa_data['學員'] != student)
                     ]
                
                # 使用 score_columns 取得評核分數
                valid_score_columns = [col for col in score_columns if col in student_epa_comp_data.columns]
                for col in valid_score_columns:
                    try:
                        # 學生分數 (確保只有一筆資料或取第一筆)
                        if not student_epa_comp_data[col].empty:
                            score = pd.to_numeric(student_epa_comp_data[col].iloc[0], errors='coerce')
                            if pd.notna(score):
                                student_scores.append(score)
                            else:
                                student_scores.append(0) # 或 None
                        else:
                            student_scores.append(0) # 或 None

                        # 同儕平均
                        if not peer_df.empty and col in peer_df.columns:
                            valid_peer_scores = pd.to_numeric(peer_df[col], errors='coerce').dropna()
                            if not valid_peer_scores.empty:
                                peer_score = valid_peer_scores.mean()
                                peer_scores.append(peer_score)
                            else:
                                peer_scores.append(0) # 或 None
                        else:
                            peer_scores.append(0) # 或 None
                        
                        # 從欄位名稱提取 EPA 編號
                        epa_match = re.search(r'EPA(\d+)', col)
                        if epa_match:
                            epa_number = epa_match.group(1)
                            display_labels.append(f"EPA{epa_number}")
                        else:
                            display_labels.append(col) # 如果沒有匹配，使用原始欄位名

                    except (ValueError, TypeError, IndexError) as e:
                        st.warning(f"處理欄位 '{col}' 時發生錯誤: {e}")
                        # 發生錯誤時也添加佔位符，以保持列表長度一致
                        if len(student_scores) < len(valid_score_columns):
                             student_scores.append(0) # 或 None
                        if len(peer_scores) < len(valid_score_columns):
                             peer_scores.append(0) # 或 None
                        if len(display_labels) < len(valid_score_columns):
                             display_labels.append(f"{col}(錯誤)")
                
                # 確保列表長度一致
                min_len = min(len(student_scores), len(peer_scores), len(display_labels))
                student_scores = student_scores[:min_len]
                peer_scores = peer_scores[:min_len]
                display_labels = display_labels[:min_len]

                if student_scores and peer_scores and display_labels:
                    # 當只有兩個項目時，添加一個空白項目以改善可讀性
                    if len(display_labels) == 2:
                        display_labels.append("空白項目")
                        student_scores.append(0)
                        peer_scores.append(0)
                    
                    # 確保數據點首尾相連
                    display_labels_closed = display_labels + [display_labels[0]]
                    student_scores_closed = student_scores + [student_scores[0]]
                    peer_scores_closed = peer_scores + [peer_scores[0]]
                    
                    if display_labels_closed:
                        # 建立雷達圖
                        fig_epa_comp = go.Figure()
                        
                        # 先畫同儕平均（黑色）
                        fig_epa_comp.add_trace(go.Scatterpolar(
                            r=peer_scores_closed,
                            theta=display_labels_closed,
                            name='同儕平均',
                            line=dict(color='rgba(0, 0, 0, 1)', width=2),
                        ))
                        
                        # 後畫學生本人（紅色）
                        fig_epa_comp.add_trace(go.Scatterpolar(
                            r=student_scores_closed,
                            theta=display_labels_closed,
                            name=student,
                            fill='toself',
                            fillcolor='rgba(255, 0, 0, 0.2)',
                            line=dict(color='rgba(255, 0, 0, 1)', width=2),
                        ))
                        
                        fig_epa_comp.update_layout(
                            polar=dict(
                                radialaxis=dict(
                                    visible=True,
                                    range=[0, 5]
                                )
                            ),
                            showlegend=True,
                            legend=dict(
                                yanchor="top",
                                y=1.2,
                                xanchor="right",  # 將圖例置於右側
                                x=1.1  # 調整水平位置
                            ),
                            title=f"{student} ({training_plan}) - EPA評量 (舊 CoreEPA)",
                            height=400,
                            width=400
                        )
                         # 更新 ticktext 以避免重複顯示第一個標籤
                        fig_epa_comp.update_polars(angularaxis_ticktext=display_labels_closed[:-1])
                        
                        st.plotly_chart(fig_epa_comp, use_container_width=True)
                    else:
                         st.warning(f"無法為 {student} 繪製舊 CoreEPA 雷達圖 (無有效標籤數據)。")
                else:
                    st.warning(f"沒有找到 {student} 的有效舊 CoreEPA 評核分數")
            
            with col2:
                st.markdown("### EPA 教師評語 (舊 CoreEPA)")
                if not student_epa_comp_data.empty:
                    # 顯示評語 (假設評語欄位固定)
                    feedback_cols = { # 映射可能的欄位名稱到 EPA 編號
                        '初評回饋：': 'EPA?', # 需要確定如何從這裡知道 EPA 編號
                        '複評回饋：': 'EPA?',
                        '教師評語與總結': '總結'
                    }
                     # 由於 coreEPA 檔案格式不確定，暫時顯示所有找到的評語欄位
                    for col_name in ['初評回饋：', '複評回饋：', '教師評語與總結']:
                        if col_name in student_epa_comp_data.columns:
                            feedback = student_epa_comp_data[col_name].iloc[0]
                            if pd.notna(feedback) and str(feedback).strip():
                                st.markdown(f"**{col_name}**: {feedback}")
                                st.markdown("---")
                else:
                    st.write("無舊 CoreEPA 評語資料。")

    # 作業繳交狀況
    st.subheader("作業繳交狀況")
    
    # 取得所有學員和作業 (使用原始 student_data)
    assignments = original_student_data['檔案名稱'].unique()
    
    # 建立作業繳交狀況表格
    submission_data = []
    
    for assignment in assignments:
        # 取得該作業的資料
        assignment_data = original_student_data[original_student_data['檔案名稱'] == assignment]
        
        # 判斷是否完成
        is_completed = False
        if not assignment_data.empty and '表單簽核流程' in assignment_data.columns:
            # 取得最後一個非空值的簽核流程
            sign_flow_series = assignment_data['表單簽核流程'].dropna()
            sign_flow = sign_flow_series.iloc[-1] if not sign_flow_series.empty else ""
            
            # 確保 sign_flow 是字串
            sign_flow = str(sign_flow)

            if any(keyword in assignment for keyword in ["教學住診", "教學門診", "夜間學習"]):
                is_completed = sign_flow.count(")") >= 3
            elif "CEX" in assignment:
                is_completed = sign_flow.count(")") >= 2    
            elif "核心技能" in assignment:
                # 核心技能的完成條件可能需要調整，目前假設只要有簽核就算
                 is_completed = sign_flow.strip() != "" and not sign_flow.startswith("未指定")
            elif "coreEPA" in assignment:
                 # coreEPA 的完成條件，假設少於 2 個"未指定"就算完成
                is_completed = sign_flow.count("未指定") < 2
            elif re.search(r'EPA\s*\d+', assignment, re.IGNORECASE):
                 # 新的 EPA 檔案格式，完成條件可能同 coreEPA: 少於 2 個"未指定"
                is_completed = sign_flow.count("未指定") < 2
            else:
                # 其他未知檔案格式，暫不判斷完成狀態
                is_completed = False # 或者 None
        
        submission_data.append({'學員': selected_student, '檔案名稱': assignment, '完成狀況': "✓" if is_completed else ("✗" if is_completed is False else "?")})
    
    # 轉換為 DataFrame 並顯示
    submission_df = pd.DataFrame(submission_data)
    
    # 設定表格樣式
    def color_status(val):
        if val == "✓":
            return 'color: green'
        elif val == "✗":
            return 'color: red'
        elif val == "?":
             return 'color: orange' # 未知狀態用橘色
        return ''
    
    # 應用樣式並顯示表格
    styled_df = submission_df.style.applymap(
        color_status, 
        subset=['完成狀況'] # 只應用於完成狀況欄
    )
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        height=400,
        column_config={
             "完成狀況": st.column_config.TextColumn(
                 "完成狀況",
                 help="✓: 完成, ✗: 未完成, ?: 未知或不適用"
            )
        }
    )

