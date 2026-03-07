"""
小兒科住院醫師評核測試資料生成器
生成符合實際格式的測試資料，用於 CCC 會議呈現和功能測試
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# 住院醫師名單（3人，使用假名，涵蓋不同訓練階段）
RESIDENTS = [
    {'name': '住院醫師A', 'level': 'R1', 'skill_rate': 0.88},  # 優秀
    {'name': '住院醫師B', 'level': 'R2', 'skill_rate': 0.50},  # 需輔導
    {'name': '住院醫師C', 'level': 'R3', 'skill_rate': 0.70},  # 需注意
]

# 評核教師名單
TEACHERS = ['主治醫師甲', '主治醫師乙', '主治醫師丙', '主治醫師丁', '主治醫師戊']

# 技能項目（來自 PEDIATRIC_SKILL_REQUIREMENTS）
SKILLS = [
    '插氣管內管', '插臍(動靜脈)導管', '腰椎穿刺', '插中心靜脈導管(CVC)',
    '肋膜液或是腹水抽取', '插胸管', '放置動脈導管', '經皮式中央靜脈導管(PICC)',
    '腦部超音波', '心臟超音波', '腹部超音波', '腎臟超音波',
    'APLS', 'NRP', 'CVVH照護', 'ECMO照護'
]

# EPA 項目（更新版）
EPA_ITEMS = ['門診表現(OPD)', '一般病人照護（WARD）', '緊急處置（ED, DR）', '重症照護（PICU, NICU）', '病歷書寫']

# 會議名稱（更新版下拉選單選項）
MEETING_NAMES = ['Staff Round', 'Journal Meeting', '晨會指導', 'EBM指導', '多專科會議', 'MM']

# 會議報告主題範例
MEETING_TOPICS = [
    '新生兒呼吸窘迫症候群處置', '兒童發燒之鑑別診斷', '川崎氏症的最新治療指引',
    '早產兒餵養策略', '兒童急性腹痛評估流程', '新生兒黃疸處置',
    '兒童氣喘急性發作處理', '腸病毒重症判斷指標', '兒童輸液治療原則',
    '新生兒敗血症抗生素選擇', '兒童癲癇急性處置', 'PICU 血行動力學監測',
]

# 會議報告評分選項（對應 5 分制）
MEETING_SCORES = ['5 卓越', '4 充分', '3 尚可', '2 稍差', '1 不符合期待']

# 可信賴程度選項（對應數值）- 兒科表單9級量表
RELIABILITY_LEVELS = {
    '允許住院醫師在旁觀察': 1.5,
    '教師在旁逐步共同操作': 2.0,
    '教師在旁必要時協助': 2.5,
    '教師可立即到場協助，事後逐項確認': 3.0,
    '教師可立即到場協助，事後重點確認': 3.3,
    '教師可稍後到場協助，必要時事後確認': 3.6,
    '教師on call提供監督': 4.0,
    '教師不需on call，事後提供回饋及監督': 4.5,
    '學員可對其他資淺的學員進行監督與教學': 5.0
}

# [Deprecated] 熟練程度改為從可信賴程度自動推導（>= 3.5 熟練 / < 3.5 不熟練）
PROFICIENCY_THRESHOLD = 3.5

def generate_test_data():
    """生成完整的測試資料集"""
    all_records = []

    # 設定評核期間：最近 6 個月
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=180)

    for resident in RESIDENTS:
        name = resident['name']
        level = resident['level']
        skill_base_rate = resident['skill_rate']  # 影響技能評核的基礎水平

        # === 1. 生成操作技術評核記錄 ===
        for skill in SKILLS:
            # 根據住院醫師的 skill_rate 決定評核次數（範圍 0-8）
            if skill_base_rate > 0.8:
                num_evals = random.randint(4, 8)
            elif skill_base_rate > 0.6:
                num_evals = random.randint(2, 5)
            else:
                num_evals = random.randint(0, 3)

            for _ in range(num_evals):
                eval_date = start_date + timedelta(days=random.randint(0, 180))

                # 可信賴程度：根據 skill_base_rate 決定傾向（兒科9級量表）
                if skill_base_rate > 0.8:
                    reliability = random.choice(list(RELIABILITY_LEVELS.keys())[6:9])   # 4.0-5.0
                elif skill_base_rate > 0.6:
                    reliability = random.choice(list(RELIABILITY_LEVELS.keys())[3:7])   # 3.0-4.0
                else:
                    reliability = random.choice(list(RELIABILITY_LEVELS.keys())[0:5])   # 1.5-3.3

                # 熟練度從可信賴程度推導
                reliability_score = RELIABILITY_LEVELS[reliability]
                proficiency = '熟練' if reliability_score >= PROFICIENCY_THRESHOLD else '不熟練'
                teacher = random.choice(TEACHERS)

                record = {
                    '時間戳記': datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
                    '評核教師': teacher,
                    '評核日期': eval_date.strftime('%Y/%m/%d'),
                    '受評核人員': name,
                    '評核時級職': level,
                    '評核項目': '操作技術',
                    '會議名稱': '',
                    '報告主題': '',
                    '內容是否充分': '',
                    '辯證資料的能力': '',
                    '口條、呈現方式是否清晰': '',
                    '是否具開創、建設性的想法': '',
                    '回答提問是否具邏輯、有條有理': '',
                    '會議報告教師回饋': '',
                    '病歷號': f'P{random.randint(100000, 999999)}',
                    '評核技術項目': skill,
                    '鎮靜藥物': random.choice(['無', 'Midazolam', 'Fentanyl', '']),
                    '可信賴程度': reliability,
                    '操作技術教師回饋': generate_technical_feedback(skill, reliability),
                    '熟練程度': proficiency,
                    'EPA項目': '',
                    'EPA可信賴程度': '',
                    'EPA質性回饋': ''
                }
                all_records.append(record)

        # === 2. 生成會議報告評核記錄 ===
        num_meetings = random.randint(8, 15)
        for _ in range(num_meetings):
            eval_date = start_date + timedelta(days=random.randint(0, 180))
            teacher = random.choice(TEACHERS)
            meeting = random.choice(MEETING_NAMES)
            topic = random.choice(MEETING_TOPICS)

            # 會議報告評分：根據 skill_base_rate 決定分數傾向
            if skill_base_rate > 0.8:
                scores = [random.choice(['5 卓越', '4 充分']) for _ in range(5)]
            elif skill_base_rate > 0.6:
                scores = [random.choice(['4 充分', '3 尚可']) for _ in range(5)]
            else:
                scores = [random.choice(['3 尚可', '2 稍差', '1 不符合期待']) for _ in range(5)]

            record = {
                '時間戳記': datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
                '評核教師': teacher,
                '評核日期': eval_date.strftime('%Y/%m/%d'),
                '受評核人員': name,
                '評核時級職': level,
                '評核項目': '會議報告',
                '會議名稱': meeting,
                '報告主題': topic,
                '內容是否充分': scores[0],
                '辯證資料的能力': scores[1],
                '口條、呈現方式是否清晰': scores[2],
                '是否具開創、建設性的想法': scores[3],
                '回答提問是否具邏輯、有條有理': scores[4],
                '會議報告教師回饋': generate_meeting_feedback(name, scores),
                '病歷號': '',
                '評核技術項目': '',
                '鎮靜藥物': '',
                '可信賴程度': '',
                '操作技術教師回饋': '',
                '熟練程度': '',
                'EPA項目': '',
                'EPA可信賴程度': '',
                'EPA質性回饋': ''
            }
            all_records.append(record)

        # === 3. 生成 EPA 評核記錄 ===
        # 每個 EPA 項目每個月 2-4 筆記錄
        for month_offset in range(6):  # 最近 6 個月
            for epa_item in EPA_ITEMS:
                num_epa_evals = random.randint(2, 4)
                for _ in range(num_epa_evals):
                    # 該月內的隨機日期
                    month_start = start_date + timedelta(days=30 * month_offset)
                    eval_date = month_start + timedelta(days=random.randint(0, 29))

                    # EPA 可信賴程度：隨時間遞增（模擬進步）
                    if skill_base_rate > 0.8:
                        base_score = 3.5 + month_offset * 0.15  # 3.5 → 4.4
                    elif skill_base_rate > 0.6:
                        base_score = 2.8 + month_offset * 0.12  # 2.8 → 3.5
                    else:
                        base_score = 2.0 + month_offset * 0.10  # 2.0 → 2.5

                    # 加上隨機波動
                    score = base_score + random.uniform(-0.3, 0.3)
                    score = max(1.5, min(5.0, score))  # 限制在 1.5-5（兒科表單範圍）

                    # 找到最接近的可信賴程度描述
                    reliability_desc = min(RELIABILITY_LEVELS.items(), key=lambda x: abs(x[1] - score))[0]

                    teacher = random.choice(TEACHERS)

                    record = {
                        '時間戳記': datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
                        '評核教師': teacher,
                        '評核日期': eval_date.strftime('%Y/%m/%d'),
                        '受評核人員': name,
                        '評核時級職': level,
                        '評核項目': 'EPA',
                        '會議名稱': '',
                        '報告主題': '',
                        '內容是否充分': '',
                        '辯證資料的能力': '',
                        '口條、呈現方式是否清晰': '',
                        '是否具開創、建設性的想法': '',
                        '回答提問是否具邏輯、有條有理': '',
                        '會議報告教師回饋': '',
                        '病歷號': '',
                        '評核技術項目': '',
                        '鎮靜藥物': '',
                        '可信賴程度': '',
                        '操作技術教師回饋': '',
                        '熟練程度': '',
                        'EPA項目': epa_item,
                        'EPA可信賴程度': reliability_desc,
                        'EPA質性回饋': generate_epa_feedback(epa_item, score)
                    }
                    all_records.append(record)

    # 轉為 DataFrame
    df = pd.DataFrame(all_records)

    # 按時間排序
    df['評核日期'] = pd.to_datetime(df['評核日期'])
    df = df.sort_values('評核日期', ascending=False)
    df['評核日期'] = df['評核日期'].dt.strftime('%Y/%m/%d')

    return df

def generate_technical_feedback(skill, reliability):
    """生成操作技術教師回饋"""
    templates = [
        f"學員對{skill}操作流程熟悉，能在指導下完成操作。建議多練習以提升熟練度。",
        f"{skill}操作技巧良好，能注意無菌技術，建議持續精進。",
        f"學員在{skill}操作中表現穩定，能獨立完成基本步驟，建議增加複雜個案經驗。",
        f"對{skill}的理論基礎扎實，實際操作仍需加強手感與速度。",
        f"學員{skill}操作表現優秀，能處理突發狀況，值得肯定。"
    ]

    if '教師on call' in reliability or '學員可對其他' in reliability:
        return random.choice(templates[3:5])
    elif '教師可稍後' in reliability or '教師可立即' in reliability:
        return random.choice(templates[2:4])
    else:
        return random.choice(templates[0:2])

def generate_meeting_feedback(name, scores):
    """生成會議報告教師回饋"""
    avg_score = sum([int(s[0]) for s in scores]) / len(scores)

    if avg_score >= 4.5:
        return f"{name}在本次會議報告中表現優異，內容充實、邏輯清晰，展現扎實的臨床思維能力。建議持續保持，未來可挑戰更複雜個案的報告。"
    elif avg_score >= 3.5:
        return f"{name}的會議報告整體良好，資料準備充分，表達清楚。建議在辯證分析部分可以更深入探討，增加批判性思考。"
    elif avg_score >= 2.5:
        return f"{name}的報告內容尚可，但在資料整合與邏輯推演上仍有進步空間。建議多參考文獻，強化臨床推理能力。"
    else:
        return f"{name}的報告需要改進，建議加強病歷資料的整理與分析，並提升口頭表達的組織性。鼓勵多觀摩資深醫師的報告方式。"

def generate_epa_feedback(epa_item, score):
    """生成 EPA 質性回饋"""
    templates = {
        '門診表現(OPD)': [
            "學員門診問診技巧良好，能有系統地進行病史詢問與身體檢查，衛教內容完整。",
            "門診看診流程尚可，但在時間掌控與病人溝通效率上仍有進步空間。",
            "門診表現需加強，建議多練習問診技巧，並學習如何有效率地完成門診工作。"
        ],
        '一般病人照護（WARD）': [
            "學員能獨立完成病房日常照護工作，包括查房、醫囑開立、病歷記錄等，表現符合期待。",
            "對病房照護流程熟悉，能主動關心病人狀況，建議持續精進溝通技巧。",
            "病房照護工作尚需加強，特別是醫囑開立的完整性與及時性，建議多向資深醫師請教。"
        ],
        '緊急處置（ED, DR）': [
            "面對緊急狀況能保持冷靜，迅速判斷並執行適當處置，表現優秀。",
            "在緊急照護中能執行基本處置，但在複雜情況下仍需教師協助，建議多參與急救訓練。",
            "緊急處置能力仍需加強，建議熟悉 APLS/NRP 流程，並增加實際操作經驗。"
        ],
        '重症照護（PICU, NICU）': [
            "重症照護表現優秀，能獨立監測生命徵象變化並適時調整治療計畫。",
            "重症照護基本能力尚可，對呼吸器設定與血行動力學監測仍需更多經驗。",
            "重症照護能力需加強，建議多參與 PICU/NICU 值班並熟悉常見重症處置流程。"
        ],
        '病歷書寫': [
            "病歷書寫完整、邏輯清晰，能準確記錄病人狀況與處置，符合醫療記錄規範。",
            "病歷書寫基本符合要求，但在診斷推理的描述上可以更詳細，建議參考優秀範例。",
            "病歷書寫需改進，特別是 SOAP 格式的完整性與專業術語使用，建議加強訓練。"
        ]
    }

    if score >= 4.0:
        return templates[epa_item][0]
    elif score >= 2.5:
        return templates[epa_item][1]
    else:
        return templates[epa_item][2]

if __name__ == '__main__':
    print("=" * 60)
    print("小兒科住院醫師評核測試資料生成器")
    print("=" * 60)

    # 生成資料
    print("\n正在生成測試資料...")
    df = generate_test_data()

    # 統計資訊
    print(f"\n✅ 生成完成！")
    print(f"   總記錄數：{len(df)}")
    print(f"   住院醫師數：{df['受評核人員'].nunique()}")
    print(f"   評核項目分布：")
    for item, count in df['評核項目'].value_counts().items():
        print(f"      - {item}: {count} 筆")

    # 儲存檔案
    output_path = 'pages/pediatric/test_data_pediatric_evaluations.csv'
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n💾 已儲存至：{output_path}")

    # 顯示各住院醫師的狀態預覽
    print("\n" + "=" * 60)
    print("住院醫師狀態預覽（預期結果）")
    print("=" * 60)
    for resident in RESIDENTS:
        if resident['skill_rate'] >= 0.8:
            status = "🟢 進度良好"
        elif resident['skill_rate'] >= 0.6:
            status = "🟡 需注意"
        else:
            status = "🔴 需輔導"
        print(f"   {resident['name']} ({resident['level']}): {status} (基礎水平 {resident['skill_rate']*100:.0f}%)")

    print("\n" + "=" * 60)
    print("測試資料生成完成，可用於以下測試：")
    print("  1. CCC 總覽頁面的警報橫帶分類")
    print("  2. 摘要卡片的三維度指標計算")
    print("  3. 技能熱圖矩陣的顏色映射")
    print("  4. 個別分析的三欄儀表盤")
    print("  5. EPA 趨勢圖的時間序列展示")
    print("=" * 60)
