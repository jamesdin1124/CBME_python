"""
小兒部住院醫師評核 — 寫入 Supabase demo 資料
涵蓋：操作技術、會議報告、EPA、研究進度、學習反思
"""
import sys, os, random
from datetime import datetime, timedelta, date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()

from modules.supabase_connection import SupabaseConnection

# ─── 測試住院醫師（6人，涵蓋 R1~R3 + 不同表現）───
RESIDENTS = [
    {'name': 'PEDR',   'level': 'R3', 'skill_rate': 0.90, 'profile': 'excellent'},
    {'name': '張美玲', 'level': 'R2', 'skill_rate': 0.72, 'profile': 'good'},
    {'name': '李大華', 'level': 'R2', 'skill_rate': 0.55, 'profile': 'average'},
    {'name': '王小明', 'level': 'R1', 'skill_rate': 0.40, 'profile': 'needs_guidance'},
    {'name': '陳志偉', 'level': 'R3', 'skill_rate': 0.82, 'profile': 'good'},
    {'name': '林雅婷', 'level': 'R3', 'skill_rate': 0.65, 'profile': 'average'},
]

# ─── 評核教師（使用真實已建帳的主治醫師名）───
TEACHERS = ['林建銘', '王志堅', '朱德明', '陳錫洲', '王富民',
            '胡智棻', '謝國祥', '周雅玲', '徐萬夫', '張佳寧']

# ─── 16 項技能 + 需求次數 ───
SKILLS = {
    '插氣管內管': 3, '插臍(動靜脈)導管': 1, '腰椎穿刺': 3,
    '插中心靜脈導管(CVC)': 3, '肋膜液或是腹水抽取': 1,
    '插胸管': 2, '放置動脈導管': 2, '經皮式中央靜脈導管(PICC)': 3,
    '腦部超音波': 5, '心臟超音波': 5, '腹部超音波': 5, '腎臟超音波': 5,
    'APLS': 3, 'NRP': 5, 'CVVH照護': 1, 'ECMO照護': 1,
}

EPA_ITEMS = ['門診表現(OPD)', '一般病人照護（WARD）', '緊急處置（ED, DR）',
             '重症照護（PICU, NICU）', '病歷書寫']

MEETING_NAMES = ['Staff Round', 'Journal Meeting', '晨會指導', 'EBM指導', '多專科會議', 'MM']

MEETING_TOPICS = [
    '新生兒呼吸窘迫症候群處置', '兒童發燒之鑑別診斷', '川崎氏症的最新治療指引',
    '早產兒餵養策略', '兒童急性腹痛評估流程', '新生兒黃疸處置',
    '兒童氣喘急性發作處理', '腸病毒重症判斷指標', '兒童輸液治療原則',
    '新生兒敗血症抗生素選擇', '兒童癲癇急性處置', 'PICU血行動力學監測',
]

RELIABILITY_MAP = {
    1.5: '允許住院醫師在旁觀察',
    2.0: '教師在旁逐步共同操作',
    2.5: '教師在旁必要時協助',
    3.0: '教師可立即到場協助，事後逐項確認',
    3.3: '教師可立即到場協助，事後重點確認',
    3.6: '教師可稍後到場協助，必要時事後確認',
    4.0: '教師on call提供監督',
    4.5: '教師不需on call，事後提供回饋及監督',
    5.0: '學員可對其他資淺的學員進行監督與教學',
}

def rand_date(start, end):
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, max(delta, 1)))

def pick_reliability(profile, month_offset=0):
    """根據表現等級 + 月份進步產生可信賴分數"""
    base = {'excellent': 4.0, 'good': 3.3, 'average': 2.5, 'needs_guidance': 2.0}[profile]
    score = base + month_offset * 0.12 + random.uniform(-0.3, 0.3)
    score = max(1.5, min(5.0, round(score * 2) / 2))  # snap to 0.5
    # 找最近的 key
    closest = min(RELIABILITY_MAP.keys(), key=lambda k: abs(k - score))
    return closest

def tech_feedback(skill, score):
    if score >= 4.0:
        return f"學員{skill}操作表現優秀，能獨立處理突發狀況，值得肯定。"
    elif score >= 3.0:
        return f"學員對{skill}操作流程熟悉，能在指導下完成操作。建議多練習以提升熟練度。"
    else:
        return f"對{skill}的理論基礎尚可，實際操作仍需加強手感與速度。建議增加練習次數。"

def meeting_feedback(name, avg):
    if avg >= 4.0:
        return f"{name}在本次會議報告中表現優異，內容充實、邏輯清晰，展現扎實的臨床思維能力。"
    elif avg >= 3.0:
        return f"{name}的會議報告整體良好，資料準備充分。建議在辯證分析部分可以更深入探討。"
    else:
        return f"{name}的報告內容尚可，但在資料整合與邏輯推演上仍有進步空間。"

def epa_feedback(epa_item, score):
    tpl = {
        '門診表現(OPD)': ["門診問診技巧良好，衛教內容完整。", "門診看診流程尚可，時間掌控可加強。", "門診表現需加強問診技巧。"],
        '一般病人照護（WARD）': ["能獨立完成病房日常照護，表現符合期待。", "對病房照護流程熟悉，建議精進溝通技巧。", "病房照護需加強醫囑開立完整性。"],
        '緊急處置（ED, DR）': ["面對緊急狀況能保持冷靜，處置得當。", "能執行基本急救處置，複雜情況仍需協助。", "緊急處置能力需加強，建議多參與訓練。"],
        '重症照護（PICU, NICU）': ["重症照護表現優秀，能獨立監測。", "重症照護基本能力尚可，需更多經驗。", "重症照護能力需加強。"],
        '病歷書寫': ["病歷書寫完整、邏輯清晰。", "病歷基本符合要求，診斷推理可更詳細。", "病歷書寫需改進 SOAP 完整性。"],
    }
    idx = 0 if score >= 4.0 else (1 if score >= 2.5 else 2)
    return tpl[epa_item][idx]

# ═══════════════════════════════════════════
def main():
    conn = SupabaseConnection()
    end_date = date.today()
    start_date = end_date - timedelta(days=180)

    eval_records = []
    research_records = []
    reflection_records = []

    for r in RESIDENTS:
        name, level, sr, profile = r['name'], r['level'], r['skill_rate'], r['profile']

        # ══ 1. 操作技術 ══
        for skill, req in SKILLS.items():
            n = int(req * sr * random.uniform(0.8, 1.5))
            n = max(0, min(n, req + 3))
            for _ in range(n):
                d = rand_date(start_date, end_date)
                rel = pick_reliability(profile)
                eval_records.append({
                    'evaluation_type': 'technical_skill',
                    'evaluation_item': '操作技術',
                    'evaluator_teacher': random.choice(TEACHERS),
                    'evaluation_date': d.isoformat(),
                    'evaluated_resident': name,
                    'resident_level': level,
                    'department': '小兒部',
                    'patient_id': f'P{random.randint(100000,999999)}',
                    'technical_skill_item': skill,
                    'sedation_medication': random.choice(['無', 'Midazolam', 'Fentanyl', '']),
                    'reliability_level': rel,
                    'technical_feedback': tech_feedback(skill, rel),
                    'proficiency_level': 4 if rel >= 4.0 else (3 if rel >= 3.5 else (2 if rel >= 3.0 else 1)),
                    'form_version': 'demo',
                    'is_deleted': False,
                })

        # ══ 2. 會議報告 ══
        n_meetings = random.randint(6, 12)
        for _ in range(n_meetings):
            d = rand_date(start_date, end_date)
            base_score = {'excellent': 4.2, 'good': 3.6, 'average': 3.0, 'needs_guidance': 2.3}[profile]
            scores = [max(1, min(5, int(base_score + random.uniform(-0.8, 0.8)))) for _ in range(5)]
            avg = sum(scores) / 5
            eval_records.append({
                'evaluation_type': 'meeting_report',
                'evaluation_item': '會議報告',
                'evaluator_teacher': random.choice(TEACHERS),
                'evaluation_date': d.isoformat(),
                'evaluated_resident': name,
                'resident_level': level,
                'department': '小兒部',
                'evaluation_item': random.choice(MEETING_TOPICS),
                'meeting_name': random.choice(MEETING_NAMES),
                'content_sufficient': scores[0],
                'data_analysis_ability': scores[1],
                'presentation_clarity': scores[2],
                'innovative_ideas': scores[3],
                'logical_response': scores[4],
                'meeting_feedback': meeting_feedback(name, avg),
                'form_version': 'demo',
                'is_deleted': False,
            })

        # ══ 3. EPA ══
        for month_offset in range(6):
            for epa_item in EPA_ITEMS:
                n_epa = random.randint(1, 3)
                for _ in range(n_epa):
                    month_start = start_date + timedelta(days=30 * month_offset)
                    d = month_start + timedelta(days=random.randint(0, 29))
                    if d > end_date:
                        d = end_date
                    rel = pick_reliability(profile, month_offset)
                    eval_records.append({
                        'evaluation_type': 'epa',
                    'evaluation_item': 'EPA',
                        'evaluator_teacher': random.choice(TEACHERS),
                        'evaluation_date': d.isoformat(),
                        'evaluated_resident': name,
                        'resident_level': level,
                        'department': '小兒部',
                        'epa_item': epa_item,
                        'epa_reliability_level': rel,
                        'epa_qualitative_feedback': epa_feedback(epa_item, rel),
                        'form_version': 'demo',
                        'is_deleted': False,
                    })

        # ══ 4. 研究進度 ══
        research_types = ['個案報告', '原著論文', '系統性回顧', '文獻回顧']
        statuses = ['構思中', '撰寫中', '投稿中', '接受']
        n_research = {'excellent': 2, 'good': 2, 'average': 1, 'needs_guidance': 1}[profile]
        for i in range(n_research):
            status_idx = min(len(statuses)-1, {'excellent': 3, 'good': 2, 'average': 1, 'needs_guidance': 0}[profile] - i)
            status_idx = max(0, status_idx)
            research_records.append({
                'resident_name': name,
                'resident_level': level,
                'department': '小兒部',
                'research_title': random.choice([
                    f'兒童{random.choice(["急性","慢性"])}腎臟病之{random.choice(["預後分析","治療策略"])}',
                    f'新生兒{random.choice(["敗血症","黃疸","呼吸窘迫"])}之{random.choice(["個案報告","文獻回顧"])}',
                    f'{random.choice(["川崎氏症","腸病毒","過敏性紫斑"])}合併{random.choice(["腎炎","心肌炎","腦炎"])}',
                    f'早產兒{random.choice(["餵養策略","腦室出血","視網膜病變"])}分析',
                ]),
                'research_type': random.choice(research_types),
                'supervisor_name': random.choice(TEACHERS[:5]),
                'current_status': statuses[status_idx],
                'research_topic': '兒科臨床研究',
                'target_journal': random.choice(['Pediatrics & Neonatology', 'Journal of Pediatrics', 'Pediatric Research', 'BMC Pediatrics']),
                'progress_notes': f'第{i+1}篇研究，目前{statuses[status_idx]}階段',
                'is_deleted': False,
                'submitted_by': 'demo_seed',
            })

        # ══ 5. 學習反思 ══
        reflection_types = ['臨床反思', '學習心得', '個案討論', '技能學習']
        n_reflections = {'excellent': 4, 'good': 3, 'average': 2, 'needs_guidance': 1}[profile]
        for i in range(n_reflections):
            d = rand_date(start_date, end_date)
            rtype = random.choice(reflection_types)
            reflection_records.append({
                'resident_name': name,
                'resident_level': level,
                'department': '小兒部',
                'reflection_date': d.isoformat(),
                'reflection_title': random.choice([
                    '急診處理嬰兒發燒案例的反思',
                    'NICU早產兒照護學習心得',
                    '兒童氣喘急性發作處置經驗',
                    '腰椎穿刺操作技術精進',
                    '與家屬溝通困難個案之反思',
                    'Journal Club文獻評讀心得',
                    '值班夜間急救經驗分享',
                    'PICU血行動力學監測學習',
                ]),
                'reflection_type': rtype,
                'situation_description': f'在{random.choice(["急診","病房","NICU","PICU","門診"])}遇到{random.choice(["複雜個案","緊急狀況","特殊疾病"])}',
                'thoughts_and_feelings': '當下感到緊張但也學到很多，指導老師的即時回饋讓我更有信心。',
                'evaluation': '整體而言處理得當，但仍有改進空間。',
                'action_plan': '加強相關文獻閱讀，並在下次遇到類似情況時更快做出判斷。',
                'learning_outcomes': '提升了臨床判斷力與處置信心。',
                'related_epa': random.choice(EPA_ITEMS),
                'supervising_teacher': random.choice(TEACHERS[:5]),
                'is_private': False,
                'is_deleted': False,
                'submitted_by': 'demo_seed',
            })

    # ═══ 寫入 Supabase ═══
    print(f"生成 {len(eval_records)} 筆評核記錄")
    print(f"生成 {len(research_records)} 筆研究進度")
    print(f"生成 {len(reflection_records)} 筆學習反思")

    # 先清除舊 demo 資料
    print("\n清除舊 demo 資料...")
    try:
        conn.client.table('pediatric_evaluations').delete().eq('form_version', 'demo').execute()
        print("  ✅ 舊評核 demo 資料已清除")
    except Exception as e:
        print(f"  ⚠️ 清除評核資料: {e}")

    try:
        # research 表沒有 form_version，用 department + 測試名字清除
        for r in RESIDENTS:
            conn.client.table('pediatric_research_progress').delete().eq('resident_name', r['name']).execute()
        print("  ✅ 舊研究進度 demo 資料已清除")
    except Exception as e:
        print(f"  ⚠️ 清除研究進度: {e}")

    try:
        for r in RESIDENTS:
            conn.client.table('pediatric_learning_reflections').delete().eq('resident_name', r['name']).execute()
        print("  ✅ 舊學習反思 demo 資料已清除")
    except Exception as e:
        print(f"  ⚠️ 清除學習反思: {e}")

    # 批次寫入（每次 50 筆）
    print("\n寫入評核記錄...")
    batch_size = 50
    for i in range(0, len(eval_records), batch_size):
        batch = eval_records[i:i+batch_size]
        conn.client.table('pediatric_evaluations').insert(batch).execute()
        print(f"  已寫入 {min(i+batch_size, len(eval_records))}/{len(eval_records)}")

    print("\n寫入研究進度...")
    for rec in research_records:
        conn.client.table('pediatric_research_progress').insert(rec).execute()
    print(f"  ✅ 已寫入 {len(research_records)} 筆")

    print("\n寫入學習反思...")
    for rec in reflection_records:
        conn.client.table('pediatric_learning_reflections').insert(rec).execute()
    print(f"  ✅ 已寫入 {len(reflection_records)} 筆")

    # ═══ 統計摘要 ═══
    print("\n" + "=" * 60)
    print("📊 Demo 資料統計")
    print("=" * 60)
    for r in RESIDENTS:
        n_eval = sum(1 for e in eval_records if e['evaluated_resident'] == r['name'])
        n_tech = sum(1 for e in eval_records if e['evaluated_resident'] == r['name'] and e['evaluation_type'] == 'technical_skill')
        n_meet = sum(1 for e in eval_records if e['evaluated_resident'] == r['name'] and e['evaluation_type'] == 'meeting_report')
        n_epa  = sum(1 for e in eval_records if e['evaluated_resident'] == r['name'] and e['evaluation_type'] == 'epa')
        n_res  = sum(1 for e in research_records if e['resident_name'] == r['name'])
        n_ref  = sum(1 for e in reflection_records if e['resident_name'] == r['name'])
        emoji = {'excellent': '🟢', 'good': '🟡', 'average': '🟠', 'needs_guidance': '🔴'}[r['profile']]
        print(f"  {emoji} {r['name']} ({r['level']}): 技術{n_tech} + 會議{n_meet} + EPA{n_epa} = {n_eval}筆 | 研究{n_res} | 反思{n_ref}")
    print("=" * 60)
    print("✅ 全部完成！請重新整理頁面查看。")

if __name__ == '__main__':
    main()
