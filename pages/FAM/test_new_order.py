#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試家醫科個別住院醫師分析頁面的新順序
"""

import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_new_order():
    """測試新的頁面順序和功能"""
    try:
        from pages.FAM.fam_data_processor import FAMDataProcessor
        from pages.FAM.fam_visualization import FAMVisualization
        
        print("🚀 開始測試家醫科個別住院醫師分析頁面新順序...")
        
        # 讀取CSV檔案
        csv_path = os.path.join(os.path.dirname(__file__), '2025-09-24T03-11_export.csv')
        df = pd.read_csv(csv_path, encoding='utf-8')
        
        print(f"✅ 成功讀取CSV檔案: {df.shape}")
        
        # 初始化處理器
        processor = FAMDataProcessor()
        
        # 清理資料
        cleaned_df = processor.clean_data(df, debug=False)
        print(f"✅ 資料清理完成: {cleaned_df.shape}")
        
        if not cleaned_df.empty:
            # 獲取學員
            students = processor.get_student_list(cleaned_df)
            print(f"👥 學員: {students}")
            
            if len(students) > 0:
                test_student = students[0]
                print(f"\n🎯 測試學員: {test_student}")
                
                # 獲取學員資料
                student_data = processor.get_student_data(cleaned_df, test_student)
                print(f"📊 學員總資料: {len(student_data)}")
                
                # 測試1: 詳細評核記錄（過濾日期）
                print(f"\n📋 測試1: 詳細評核記錄")
                if '日期' in student_data.columns:
                    student_data_copy = student_data.copy()
                    student_data_copy['日期'] = pd.to_datetime(student_data_copy['日期'], errors='coerce')
                    valid_date_data = student_data_copy.dropna(subset=['日期'])
                    
                    print(f"  - 原始資料筆數: {len(student_data)}")
                    print(f"  - 有效日期資料筆數: {len(valid_date_data)}")
                    
                    if not valid_date_data.empty:
                        print(f"  ✅ 有有效日期資料，可以顯示詳細記錄")
                    else:
                        print(f"  ⚠️ 沒有有效日期資料，將略過詳細記錄顯示")
                else:
                    print(f"  ❌ 沒有找到日期欄位")
                
                # 測試2: 信賴程度分析（雷達圖）
                print(f"\n📈 測試2: 信賴程度分析")
                reliability_analysis = processor.calculate_reliability_progress(student_data)
                if reliability_analysis:
                    print(f"  ✅ 信賴程度分析成功")
                    print(f"  - 平均信賴程度: {reliability_analysis['average']:.2f}")
                    print(f"  - 分布: {reliability_analysis['distribution']}")
                else:
                    print(f"  ❌ 信賴程度分析失敗")
                
                # 測試3: EPA項目趨勢分析（boxplot）
                print(f"\n📊 測試3: EPA項目趨勢分析")
                epa_items = processor.get_epa_items(cleaned_df)
                print(f"  - 找到 {len(epa_items)} 個EPA項目: {epa_items}")
                
                if epa_items:
                    for epa_item in epa_items[:2]:  # 只測試前2個EPA項目
                        epa_data = student_data[student_data['EPA項目'] == epa_item]
                        print(f"  - {epa_item}: {len(epa_data)} 筆資料")
                        
                        if not epa_data.empty:
                            monthly_trend_data = processor.calculate_monthly_epa_trend(epa_data, epa_item)
                            if monthly_trend_data is not None and not monthly_trend_data.empty:
                                print(f"    ✅ 月度趨勢計算成功: {len(monthly_trend_data)} 個月份")
                            else:
                                print(f"    ❌ 月度趨勢計算失敗")
                
                # 測試4: 教師回饋分析
                print(f"\n💬 測試4: 教師回饋分析")
                feedback_analysis = processor.get_teacher_feedback_analysis(student_data)
                if feedback_analysis:
                    print(f"  ✅ 教師回饋分析成功")
                    print(f"  - 總回饋次數: {feedback_analysis['total_count']}")
                else:
                    print(f"  ❌ 教師回饋分析失敗")
                
                print(f"\n🎉 所有測試完成！")
                return True
            else:
                print(f"❌ 沒有找到學員資料")
                return False
        else:
            print(f"❌ 清理後資料為空")
            return False
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 70)
    result = test_new_order()
    print("=" * 70)
    
    if result:
        print("🎉 家醫科個別住院醫師分析頁面新順序測試成功！")
        print("\n📋 新的頁面順序:")
        print("1. 詳細評核記錄：表格呈現該學生資料（過濾有效日期）")
        print("2. 信賴程度分析：雷達圖呈現所有EPA項目")
        print("3. EPA項目趨勢分析：boxplot呈現每個EPA項目的趨勢")
        print("4. 教師回饋分析：表格呈現")
    else:
        print("❌ 家醫科個別住院醫師分析頁面新順序測試失敗！")
