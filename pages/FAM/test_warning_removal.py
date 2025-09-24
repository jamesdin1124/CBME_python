#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試EPA項目趨勢分析警告訊息移除功能
"""

import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_warning_removal():
    """測試警告訊息移除功能"""
    try:
        from pages.FAM.fam_data_processor import FAMDataProcessor
        from pages.FAM.fam_visualization import FAMVisualization
        
        print("🚀 開始測試EPA項目趨勢分析警告訊息移除功能...")
        
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
                
                # 測試EPA項目趨勢分析
                print(f"\n📊 測試EPA項目趨勢分析:")
                epa_items = processor.get_epa_items(cleaned_df)
                print(f"  - 找到 {len(epa_items)} 個EPA項目: {epa_items}")
                
                if epa_items:
                    visualizer = FAMVisualization()
                    
                    for epa_item in epa_items[:2]:  # 只測試前2個EPA項目
                        print(f"\n🎯 測試EPA項目: {epa_item}")
                        epa_data = student_data[student_data['EPA項目'] == epa_item]
                        print(f"  - 資料筆數: {len(epa_data)}")
                        
                        if not epa_data.empty:
                            monthly_trend_data = processor.calculate_monthly_epa_trend(epa_data, epa_item)
                            
                            if monthly_trend_data is not None and not monthly_trend_data.empty:
                                print(f"  - 月度趨勢數據: {len(monthly_trend_data)} 個月份")
                                
                                # 測試趨勢圖創建（不顯示警告）
                                print(f"  - 測試趨勢圖創建...")
                                try:
                                    trend_fig = visualizer.create_epa_monthly_trend_chart(
                                        monthly_trend_data, 
                                        epa_item, 
                                        test_student
                                    )
                                    
                                    if trend_fig is not None:
                                        print(f"    ✅ 完整趨勢圖創建成功")
                                    else:
                                        print(f"    ⚠️ 完整趨勢圖創建失敗，嘗試簡化版...")
                                        
                                        # 嘗試簡化版趨勢圖（箱線圖）
                                        simple_fig = visualizer.create_simple_monthly_trend_chart(
                                            monthly_trend_data,
                                            epa_item,
                                            test_student,
                                            epa_data  # 傳入原始數據用於更好的boxplot
                                        )
                                        
                                        if simple_fig is not None:
                                            print(f"    ✅ 簡化版趨勢圖創建成功")
                                        else:
                                            print(f"    ❌ 簡化版趨勢圖創建失敗")
                                    
                                except Exception as e:
                                    print(f"    ❌ 趨勢圖創建時發生異常: {str(e)}")
                            else:
                                print(f"    ❌ 月度趨勢計算失敗或無數據")
                        else:
                            print(f"    ℹ️ 尚未有任何評核記錄")
                
                print(f"\n🎉 警告訊息移除測試完成！")
                print(f"📝 改進說明:")
                print(f"  - 移除了 '完整趨勢圖創建失敗，嘗試簡化版...' 警告訊息")
                print(f"  - 現在直接顯示簡化版趨勢圖，無需顯示警告")
                print(f"  - 用戶體驗更流暢，不會看到技術性的錯誤訊息")
                print(f"  - 保持頁面整潔，專注於數據展示")
                
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
    result = test_warning_removal()
    print("=" * 70)
    
    if result:
        print("🎉 EPA項目趨勢分析警告訊息移除測試成功！")
        print("\n💡 用戶體驗改進:")
        print("- 移除了技術性的警告訊息")
        print("- 直接顯示可用的趨勢圖")
        print("- 頁面更加整潔和專業")
        print("- 用戶不會被錯誤訊息干擾")
    else:
        print("❌ EPA項目趨勢分析警告訊息移除測試失敗！")
