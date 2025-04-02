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
        '學員自評': [],
        '教師評核': [],
        '教師複評': []
    }
    
    # 收集所有非空值
    for eval_type in ['學員自評', '教師評核', '教師複評']:
        column = item_data[eval_type]
        values = student_data[column].dropna().astype(float)
        if not values.empty:
            scores[eval_type] = values.mean()
        else:
            scores[eval_type] = None
            
    return scores

def show_ANE_R_EPA_peer_analysis_section(df):
    """顯示ANE_R同梯次分析的函數"""
    
    st.subheader("麻醉科住院醫師分析")
    
    # 在最上方顯示匯入的資料表
    st.markdown("### 匯入資料總覽")
    st.dataframe(
        df,
        use_container_width=True,
        height=300
    )
    
    # 添加分隔線
    st.markdown("---")

    # 取得所有可用的學員名稱
    students = df['學員'].unique()
    selected_student = st.selectbox(
        '請選擇要分析的學員：',
        students,
        key='ane_r_student_selector'
    )

    # 定義所有 EPA 的評量項目對應
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
                '教師複評': '6. Patient care 6 (PC6).手術室外重症病人之檢傷與處理(教師評核 [單選]'
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
                '學員自評': '2. Patient care 2 (PC2). 麻醉計劃與執行(學員自評) [單選]',
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
                '教師複評': '25. Interpersonal communication skill 3 (ICS3).團隊及領導技巧(教師評核) [單選].1'
            },
            'MK1': {
                '名稱': '生物醫學、臨床、流行病學與社會行為科學的知識',
                '學員自評': '11. Medical knowledge 1 (MK1).生物醫學、臨床、流行病學與社會行為科學的知識(學員自評) [單選]',
                '教師評核': '11. Medical knowledge 1 (MK1).生物醫學、臨床、流行病學與社會行為科學的知識(教師評核) [單選]',
                '教師複評': '11. Medical knowledge 1 (MK1).生物醫學、臨床、流行病學與社會行為科學的知識(教師評核) [單選].1'
            }
        }
    }

    # 篩選選定學員的資料
    student_data = df[df['學員'] == selected_student]
    
    # 依序分析每個EPA
    for epa_name in ['EPA 1', 'EPA 2', 'EPA 3', 'EPA 4', 'EPA 5', 'EPA 6']:
        st.markdown(f"### {epa_name}")
        
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
            # 計算當前學生的分數
            scores = calculate_average_scores(student_data, item_data)
            
            # 計算所有學生的平均分數
            all_students_scores = calculate_average_scores(df, item_data)
            
            # 只有當至少有一個評分存在時才加入該項目
            if any(score is not None for score in scores.values()) or any(score is not None for score in all_students_scores.values()):
                categories.append(f"{item_key}:<br>{item_data['名稱']}")
                
                # 第一個圖的數據
                self_eval.append(scores['學員自評'] if scores['學員自評'] is not None else 0)
                teacher_eval.append(scores['教師評核'] if scores['教師評核'] is not None else 0)
                teacher_review.append(scores['教師複評'] if scores['教師複評'] is not None else 0)
                
                # 第二個圖的數據
                student_teacher_scores = [scores['教師評核'], scores['教師複評']]
                student_teacher_scores = [s for s in student_teacher_scores if s is not None]
                student_avg.append(np.mean(student_teacher_scores) if student_teacher_scores else 0)
                
                all_teacher_scores = [all_students_scores['教師評核'], all_students_scores['教師複評']]
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
            categories.append(categories[0])
            self_eval.append(self_eval[0])
            teacher_eval.append(teacher_eval[0])
            teacher_review.append(teacher_review[0])
            student_avg.append(student_avg[0])
            all_students_avg.append(all_students_avg[0])
            
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
                            tickangle=0,
                            tickfont=dict(size=10),
                            direction="clockwise",  # 順時針方向
                            rotation=90,  # 旋轉90度
                            tickmode='array',  # 使用自定義標籤模式
                            ticktext=categories,  # 標籤文字
                            tickvals=list(range(len(categories))),  # 標籤位置
                            layer='below traces'  # 確保標籤在軌跡下層
                        )
                    ),
                    showlegend=True,
                    legend=dict(
                        yanchor="top",
                        y=1.2,
                        xanchor="right",  # 將圖例置於右側
                        x=1.1  # 調整水平位置
                    ),
                    title=dict(
                        text=f"{selected_student} - {epa_name}<br>評量雷達圖",
                        y=0.95,
                        x=0.5,  # 標題置中
                        xanchor='center',
                        yanchor='top',
                        font=dict(size=16)
                    ),
                    height=500,
                    margin=dict(
                        l=100,  # 增加左邊距
                        r=100,  # 增加右邊距
                        t=140,  # 增加上邊距
                        b=100,  # 增加下邊距
                        pad=10
                    ),
                    autosize=True
                )
                
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
                            tickangle=0,
                            tickfont=dict(size=10),
                            direction="clockwise",  # 順時針方向
                            rotation=90,  # 旋轉90度
                            tickmode='array',  # 使用自定義標籤模式
                            ticktext=categories,  # 標籤文字
                            tickvals=list(range(len(categories))),  # 標籤位置
                            layer='below traces'  # 確保標籤在軌跡下層
                        )
                    ),
                    showlegend=True,
                    legend=dict(
                        yanchor="top",
                        y=1.2,
                        xanchor="right",  # 將圖例置於右側
                        x=1.1  # 調整水平位置
                    ),
                    title=dict(
                        text=f"{selected_student} - {epa_name}<br>教師評核平均比較",
                        y=0.95,
                        x=0.5,  # 標題置中
                        xanchor='center',
                        yanchor='top',
                        font=dict(size=16)
                    ),
                    height=500,
                    margin=dict(
                        l=100,  # 增加左邊距
                        r=100,  # 增加右邊距
                        t=140,  # 增加上邊距
                        b=100,  # 增加下邊距
                        pad=10
                    ),
                    autosize=True
                )
                
                st.plotly_chart(fig2, use_container_width=True)
            
            # 在每個EPA後添加分隔線
            st.markdown("---")
        else:
            st.warning(f"所選學員在 {epa_name} 項目中沒有評核資料")
            st.markdown("---")

    # 在分析開始前先顯示完整的資料表
    st.markdown("### 完整資料表")
    st.dataframe(
        student_data,
        use_container_width=True,
        height=300
    )
    
    # 修改核心技能分析部分
    st.subheader("核心技能分析")

    # 直接使用合併後的資料
    core_skill_data = df[
        (df['學員'] == selected_student) &
        (df['檔案名稱'].str.contains('核心技能', na=False))
    ]

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

    # 取得所有學員
    students = core_skill_data['學員'].unique()
    
    # 為每個學員建立雷達圖
    for student in students:
        # 建立兩欄佈局
        col1, col2 = st.columns([1, 1])
        
        # 取得該學員的資料
        student_data = core_skill_data[core_skill_data['學員'] == student]
        
        # 取得臨床訓練計畫
        training_plan = student_data['臨床訓練計畫'].iloc[0] if '臨床訓練計畫' in student_data.columns else '未知'
        
        with col1:
            # 準備雷達圖資料
            skill_scores = {}
            for _, row in student_data.iterrows():
                filename = row['檔案名稱']
                match = re.search(r'^臨床核心技能\s*(.*?)\.xls', filename)
                match = re.search(r'^臨床核心技能\s*(.*?)\.xls', filename)
                if match:
                    skill_name = match.group(1)
                    skill_key = skill_name
                    
                    if pd.notna(row['教師評核']):
                        try:
                            score = float(row['教師評核'])
                            skill_scores[skill_key] = score
                        except (ValueError, TypeError):
                            st.warning(f"無法轉換評核分數：{row['教師評核']}")
            
            if skill_scores:
                # 建立雷達圖
                fig = go.Figure()
                
                # 計算同儕平均
                peer_averages = {}
                for filename in core_skill_data['檔案名稱'].unique():
                    match = re.search(r'^臨床核心技能\s*(.*?)\.xls', filename)
                    if match:
                        skill_name = match.group(1)
                        skill_key = skill_name
                        
                        # 計算該技能的平均分數
                        skill_scores_all = core_skill_data[
                            core_skill_data['檔案名稱'] == filename
                        ]['教師評核'].astype(float).mean()
                        
                        peer_averages[skill_key] = skill_scores_all
                
                # 確保數據點首尾相連
                skills = list(skill_scores.keys())
                scores = [skill_scores[skill] for skill in skills]
                peer_scores = [peer_averages[skill] for skill in skills]
                
                # 當只有兩個項目時，添加一個空白項目以改善可讀性
                if len(skills) == 2:
                    skills.append("空白項目")
                    scores.append(0)
                    peer_scores.append(0)
                
                skills_closed = skills + [skills[0]]
                scores_closed = scores + [scores[0]]
                peer_scores_closed = peer_scores + [peer_scores[0]]
                
                # 先畫同儕平均（黑色）
                fig.add_trace(go.Scatterpolar(
                    r=peer_scores_closed,
                    theta=skills_closed,
                    name='同儕平均',
                    line=dict(color='rgba(0, 0, 0, 1)', width=2),
                ))
                
                # 後畫學生本人（紅色）
                fig.add_trace(go.Scatterpolar(
                    r=scores_closed,
                    theta=skills_closed,
                    name=student,
                    fill='toself',
                    fillcolor='rgba(255, 0, 0, 0.2)',
                    line=dict(color='rgba(255, 0, 0, 1)', width=2),
                ))
                
                fig.update_layout(
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
                    title=f"{student} ({training_plan}) - 核心技能評核",
                    height=400,
                    width=400,
                    margin=dict(
                        l=50,  # 左邊距
                        r=50,  # 右邊距
                        t=100,  # 上邊距
                        b=50,  # 下邊距
                        pad=10
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"沒有找到 {student} 的有效評核分數")
        
        with col2:
            st.markdown("### 教師評語")
            for _, row in student_data.iterrows():
                filename = row['檔案名稱']
                match = re.search(r'^臨床核心技能\s*(.*?)\.xls', filename)
                if match:
                    skill_name = match.group(1)
                    if '教師評語與總結' in row and pd.notna(row['教師評語與總結']):
                        st.markdown(f"**{skill_name}**：{row['教師評語與總結']}")

    # EPA 分析部分
    st.subheader("EPA 評量比較")
    
    # 從選定學員的資料中找出 EPA 相關的資料
    epa_data = student_data[
        student_data['檔案名稱'].str.contains('coreEPA', na=False)
    ]

    if not epa_data.empty:
        # 找出包含 "EPA" 和 "教師評量" 的評分欄位
        score_columns = [col for col in epa_data.columns if 'EPA' in col and '教師評量' in col]
        
        # 顯示 EPA 資料表
        st.markdown("### EPA 評核資料")
        display_columns = [
            '學員', 
            '臨床訓練計畫', 
            '檔案名稱'
        ] + score_columns + [
            '初評回饋：',
            '複評回饋：',
            '教師評語與總結'
        ]
        
        st.dataframe(
            epa_data[display_columns],
            use_container_width=True,
            height=200
        )

        # 取得所有學員
        students = epa_data['學員'].unique()
        
        # 為每個學員建立雷達圖
        for student in students:
            # 建立兩欄佈局
            col1, col2 = st.columns([1, 1])
            
            # 取得該學員的資料
            student_data = epa_data[epa_data['學員'] == student]
            
            # 取得臨床訓練計畫
            training_plan = student_data['臨床訓練計畫'].iloc[0] if '臨床訓練計畫' in student_data.columns else '未知'
            
            with col1:
                # 準備雷達圖資料
                student_scores = []
                peer_scores = []
                display_labels = []
                
                # 取得當前學生的訓練計畫
                current_training_program = student_data['臨床訓練計畫'].iloc[0]
                
                # 篩選同訓練計畫的同儕資料
                peer_df = epa_data[epa_data['臨床訓練計畫'] == current_training_program]
                peer_df = peer_df[peer_df['學員'] != student]  # 排除當前學生
                
                # 使用 score_columns 取得評核分數
                for col in score_columns:
                    try:
                        # 學生分數
                        score = float(student_data[col].iloc[0])
                        student_scores.append(score)
                        
                        # 同儕平均
                        peer_score = peer_df[col].astype(float).mean()
                        peer_scores.append(peer_score)
                        
                        # 從欄位名稱提取 EPA 編號
                        epa_match = re.search(r'EPA(\d+)', col)
                        if epa_match:
                            epa_number = epa_match.group(1)
                            display_labels.append(f"EPA{epa_number}")
                    except (ValueError, TypeError):
                        st.warning(f"無法轉換評核分數：{col}")
                
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
                    
                    # 建立雷達圖
                    fig = go.Figure()
                    
                    # 先畫同儕平均（黑色）
                    fig.add_trace(go.Scatterpolar(
                        r=peer_scores_closed,
                        theta=display_labels_closed,
                        name='同儕平均',
                        line=dict(color='rgba(0, 0, 0, 1)', width=2),
                    ))
                    
                    # 後畫學生本人（紅色）
                    fig.add_trace(go.Scatterpolar(
                        r=student_scores_closed,
                        theta=display_labels_closed,
                        name=student,
                        fill='toself',
                        fillcolor='rgba(255, 0, 0, 0.2)',
                        line=dict(color='rgba(255, 0, 0, 1)', width=2),
                    ))
                    
                    fig.update_layout(
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
                        title=f"{student} ({training_plan}) - EPA評量",
                        height=400,
                        width=400,
                        margin=dict(
                            l=50,  # 左邊距
                            r=50,  # 右邊距
                            t=100,  # 上邊距
                            b=50,  # 下邊距
                            pad=10
                        )
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning(f"沒有找到 {student} 的有效評核分數")
            
            with col2:
                st.markdown("### EPA 教師評語")
                for _, row in student_data.iterrows():
                    filename = row['檔案名稱']
                    match = re.search(r'coreEPA\s+(\d+)', filename)
                    if match:
                        epa_number = match.group(1)
                        
                        st.markdown(f"**EPA{epa_number}**")
                        
                        # 顯示初評回饋
                        initial_feedback = row.get('初評回饋：', '')
                        if pd.notna(initial_feedback) and str(initial_feedback).strip() != '':
                            st.markdown(f"{initial_feedback}")
                        
                        # 顯示複評回饋
                        review_feedback = row.get('複評回饋：', '')
                        if pd.notna(review_feedback) and str(review_feedback).strip() != '':
                            st.markdown(f"{review_feedback}")
                        
                        # 加入分隔線
                        st.markdown("---")

                # 除錯用：顯示一筆資料的內容
                if not student_data.empty:
                    st.write("第一筆資料內容：")
                    sample_row = student_data.iloc[0]
                    st.write("初評回饋：", repr(sample_row.get('初評回饋：', 'Not found')))
                    st.write("複評回饋：", repr(sample_row.get('複評回饋：', 'Not found')))

    # 作業繳交狀況
    st.subheader("作業繳交狀況")
    
    # 取得所有學員和作業
    assignments = student_data['檔案名稱'].unique()
    
    # 建立作業繳交狀況表格
    submission_data = []
    
    for assignment in assignments:
        # 取得該作業的資料
        assignment_data = student_data[student_data['檔案名稱'] == assignment]
        
        # 判斷是否完成
        is_completed = False
        if not assignment_data.empty and '表單簽核流程' in assignment_data.columns:
            # 取得最後一個非空值的簽核流程
            sign_flow = assignment_data['表單簽核流程'].dropna().iloc[-1] if not assignment_data['表單簽核流程'].dropna().empty else ""
            
            if any(keyword in assignment for keyword in ["教學住診", "教學門診", "夜間學習"]):
                is_completed = sign_flow.count(")") >= 3
            elif "CEX" in assignment:
                is_completed = sign_flow.count(")") >= 2    
            elif "核心技能" in assignment:
                is_completed = sign_flow.endswith(")")
            elif "coreEPA" in assignment:
                is_completed = sign_flow.count("未指定") < 2
        
        submission_data.append({'學員': selected_student, '檔案名稱': assignment, '完成狀況': "✓" if is_completed else "✗"})
    
    # 轉換為 DataFrame 並顯示
    submission_df = pd.DataFrame(submission_data)
    
    # 設定表格樣式
    def color_status(val):
        if val in ["✓", "✗"]:
            color = 'green' if val == "✓" else 'red'
            return f'color: {color}'
        return ''
    
    # 應用樣式並顯示表格
    styled_df = submission_df.style.applymap(
        color_status, 
        subset=submission_df.columns.difference(['學員'])
    )
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        height=400
    ) 