"""
科別 EPA 配置

定義各科別的 EPA 項目、評核類型、技能項目與最低要求。
所有科別共用統一的 9 級可信賴程度量表（1.5-5.0）。
"""

# ═══════════════════════════════════════════════════════
# 統一可信賴程度量表（9 級 1.5-5.0）— 全科別共用
# ═══════════════════════════════════════════════════════

RELIABILITY_OPTIONS = {
    '允許住院醫師在旁觀察': 1.5,
    '教師在旁逐步共同操作': 2.0,
    '教師在旁必要時協助': 2.5,
    '教師可立即到場協助，事後逐項確認': 3.0,
    '教師可立即到場協助，事後重點確認': 3.3,
    '教師可稍後到場協助，必要時事後確認': 3.6,
    '教師on call提供監督': 4.0,
    '教師不需on call，事後提供回饋及監督': 4.5,
    '學員可對其他資淺的學員進行監督與教學': 5.0,
}

# 熟練度門檻 — >= 此分數判定為「熟練」
PROFICIENCY_THRESHOLD = 3.5

# 會議報告 5 分制選項
MEETING_SCORE_OPTIONS = [
    '5 卓越', '4 充分', '3 尚可', '2 稍差', '1 不符合期待',
]
MEETING_SCORE_MAP = {
    '5 卓越': 5, '4 充分': 4, '3 尚可': 3,
    '2 稍差': 2, '1 不符合期待': 1,
}


# ═══════════════════════════════════════════════════════
# 科別配置
# ═══════════════════════════════════════════════════════

DEPARTMENT_EPA_CONFIG = {

    # ─── 小兒部 ───
    '小兒部': {
        'evaluation_types': ['technical_skill', 'meeting_report', 'epa'],
        'epa_items': ['門診表現(OPD)', '一般病人照護（WARD）', '緊急處置（ED, DR）', '重症照護（PICU, NICU）', '病歷書寫'],
        'skill_items': {
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
            'ECMO照護': {'minimum': 1, 'description': '訓練期間最少1次'},
        },
        'has_dual_assessment': False,
    },

    # ─── 家醫部 ───
    '家醫部': {
        'evaluation_types': ['epa'],
        'epa_items': [
            '02門診/社區衛教',
            '03預防注射',
            '05健康篩檢',
            '07慢性疾病管理',
            '08急性照護',
            '09居家整合醫學',
            '11安寧緩和醫療',
            '12家醫住院照護',
            '13家醫門診照護',
            '14社區醫學實務',
            '15預防醫學/健康促進',
            '16家醫急診照護',
            '17長期照護',
            '18家庭醫學科研習',
        ],
        'epa_min_requirements': {
            '02門診/社區衛教': 10,
            '03預防注射': 15,
            '05健康篩檢': 20,
            '07慢性疾病管理': 25,
            '08急性照護': 15,
            '09居家整合醫學': 10,
            '11安寧緩和醫療': 5,
            '12家醫住院照護': 30,
            '13家醫門診照護': 40,
            '14社區醫學實務': 8,
            '15預防醫學/健康促進': 10,
            '16家醫急診照護': 20,
            '17長期照護': 5,
            '18家庭醫學科研習': 15,
        },
        'has_dual_assessment': True,
    },

    # ─── 麻醉部 ───
    '麻醉部': {
        'evaluation_types': ['epa'],
        'epa_items': [
            'EPA 1', 'EPA 2', 'EPA 3',
            'EPA 4', 'EPA 5', 'EPA 6',
        ],
        'has_dual_assessment': True,
    },

    # ─── 內科部 ───
    '內科部': {
        'evaluation_types': ['epa', 'meeting_report'],
        'epa_items': ['病歷紀錄', '當班處置', '住院接診', '門診照護', '病人轉介'],
        'has_dual_assessment': True,
    },

    # ─── 外科部 ───
    '外科部': {
        'evaluation_types': ['epa', 'technical_skill'],
        'epa_items': ['術前評估', '手術操作', '術後照護', '急診處置'],
        'skill_items': {
            '傷口縫合': {'minimum': 10, 'description': '訓練期間最少10次'},
            '清創手術': {'minimum': 5, 'description': '訓練期間最少5次'},
            '引流管置放': {'minimum': 3, 'description': '訓練期間最少3次'},
            '石膏固定': {'minimum': 5, 'description': '訓練期間最少5次'},
        },
        'has_dual_assessment': False,
    },

    # ─── 婦產部 ───
    '婦產部': {
        'evaluation_types': ['epa'],
        'epa_items': ['產前照護', '分娩處置', '婦科手術', '產後照護', '門診照護'],
        'has_dual_assessment': True,
    },

    # ─── 預設模板（其他科別適用）───
    '_default': {
        'evaluation_types': ['epa'],
        'epa_items': ['病歷紀錄', '當班處置', '住院接診'],
        'has_dual_assessment': True,
    },
}


def get_department_config(department):
    """
    取得科別配置。若找不到則回傳預設模板。

    Args:
        department (str): 科別名稱

    Returns:
        dict: 科別 EPA 配置
    """
    return DEPARTMENT_EPA_CONFIG.get(department, DEPARTMENT_EPA_CONFIG['_default'])


# 全部科別列表（供下拉選單使用）
ALL_DEPARTMENTS = [
    "小兒部", "內科部", "外科部", "婦產部", "神經科", "精神部",
    "家醫部", "急診醫學部", "麻醉部", "放射部", "病理部",
    "復健部", "皮膚部", "眼科", "耳鼻喉部", "泌尿部", "骨部", "其他科別",
]
