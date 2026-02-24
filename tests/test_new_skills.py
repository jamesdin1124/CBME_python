#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試新增技能項目功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis_pediatric import PEDIATRIC_SKILL_REQUIREMENTS

def test_new_skills():
    """測試新增的技能項目"""
    print("🔍 測試新增技能項目功能")
    print("=" * 50)
    
    # 檢查技能要求字典
    print("📋 所有技能要求：")
    for skill, details in PEDIATRIC_SKILL_REQUIREMENTS.items():
        print(f"  • {skill}: {details['description']}")
    
    print("\n" + "=" * 50)
    
    # 檢查新增的技能
    new_skills = ['病歷書寫', 'NRP']
    print("🆕 新增技能項目：")
    for skill in new_skills:
        if skill in PEDIATRIC_SKILL_REQUIREMENTS:
            details = PEDIATRIC_SKILL_REQUIREMENTS[skill]
            print(f"  ✅ {skill}: {details['description']}")
            print(f"     最少次數: {details['minimum']}")
        else:
            print(f"  ❌ {skill}: 未找到")
    
    print("\n" + "=" * 50)
    
    # 統計技能總數
    total_skills = len(PEDIATRIC_SKILL_REQUIREMENTS)
    print(f"📊 技能總數: {total_skills}")
    
    # 按最少次數分組統計
    skill_groups = {}
    for skill, details in PEDIATRIC_SKILL_REQUIREMENTS.items():
        minimum = details['minimum']
        if minimum not in skill_groups:
            skill_groups[minimum] = []
        skill_groups[minimum].append(skill)
    
    print("\n📈 按最少次數分組：")
    for minimum in sorted(skill_groups.keys()):
        skills = skill_groups[minimum]
        print(f"  {minimum}次: {len(skills)}個技能")
        for skill in skills:
            print(f"    - {skill}")
    
    print("\n" + "=" * 50)
    print("✅ 測試完成！")

if __name__ == "__main__":
    test_new_skills()
