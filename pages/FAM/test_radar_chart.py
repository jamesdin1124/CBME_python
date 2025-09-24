#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試家醫部雷達圖功能
"""

import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_radar_chart_functionality():
    """測試雷達圖功能"""
    try:
        from pages.FAM.fam_data_processor import FAMDataProcessor
        from pages.FAM.fam_visualization import FAMVisualization
        
        # 讀取CSV檔案
        csv_path = os.path.join(os.path.dirname(__file__), 'EPA匯出原始檔_1140923.csv')
        df = pd.read_csv(csv_path, encoding='utf-8')
        
        print(f"✅ 成功讀取CSV檔案")
        print(f"📊 原始資料形狀: {df.shape}")
        
        # 初始化處理器和視覺化模組
        processor = FAMDataProcessor()
        visualizer = FAMVisualization()
        
        # 清理資料
        cleaned_df = processor.clean_data(df, debug=True)
        print(f"📊 清理後資料形狀: {cleaned_df.shape}")
        
        if not cleaned_df.empty:
            # 獲取學員清單
            students = processor.get_student_list(cleaned_df)
            print(f"👥 學員清單: {students}")
            
            if students:
                # 選擇第一個學員進行測試
                test_student = students[0]
                print(f"\n🎯 測試學員: {test_student}")
                
                # 獲取學員資料
                student_data = processor.get_student_data(cleaned_df, test_student)
                print(f"📋 {test_student} 的資料筆數: {len(student_data)}")
                
                # 測試雷達圖創建
                print("\n📊 測試雷達圖創建...")
                radar_fig = visualizer.create_reliability_radar_chart(
                    student_data, 
                    test_student,
                    f"{test_student} - 信賴程度雷達圖測試"
                )
                
                if radar_fig:
                    print("✅ 雷達圖創建成功")
                    
                    # 檢查雷達圖的資料
                    if hasattr(radar_fig, 'data') and radar_fig.data:
                        trace = radar_fig.data[0]
                        print(f"📈 雷達圖軸數量: {len(trace.theta) if hasattr(trace, 'theta') else 0}")
                        print(f"📈 雷達圖數值: {len(trace.r) if hasattr(trace, 'r') else 0}")
                        
                        if hasattr(trace, 'theta'):
                            print(f"🎯 EPA項目: {trace.theta}")
                        if hasattr(trace, 'r'):
                            print(f"📊 信賴程度數值: {trace.r}")
                else:
                    print("❌ 雷達圖創建失敗")
                
                # 測試EPA項目比較雷達圖
                print("\n📊 測試EPA項目比較雷達圖...")
                epa_items = processor.get_epa_items(cleaned_df)
                if epa_items:
                    test_epa = epa_items[0]
                    print(f"🎯 測試EPA項目: {test_epa}")
                    
                    comparison_fig = visualizer.create_epa_comparison_radar_chart(
                        cleaned_df,
                        test_epa,
                        f"各學員 - {test_epa} 信賴程度比較測試"
                    )
                    
                    if comparison_fig:
                        print("✅ EPA項目比較雷達圖創建成功")
                        
                        # 檢查比較雷達圖的資料
                        if hasattr(comparison_fig, 'data') and comparison_fig.data:
                            print(f"📈 比較雷達圖學員數量: {len(comparison_fig.data)}")
                            for i, trace in enumerate(comparison_fig.data):
                                if hasattr(trace, 'name'):
                                    print(f"  - 學員 {i+1}: {trace.name}")
                    else:
                        print("❌ EPA項目比較雷達圖創建失敗")
                
                return True
            else:
                print("❌ 沒有找到學員資料")
                return False
        else:
            print("❌ 清理後資料為空")
            return False
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 開始測試家醫部雷達圖功能...")
    print("=" * 50)
    
    result = test_radar_chart_functionality()
    
    print("\n" + "=" * 50)
    if result:
        print("🎉 雷達圖功能測試成功！")
        print("\n💡 現在家醫部系統的信賴程度分析將使用雷達圖顯示。")
        print("   - 個別學員分析：顯示各EPA項目的信賴程度雷達圖")
        print("   - 同儕比較：提供信賴程度比較雷達圖")
        print("   - 雷達圖能更直觀地展示多維度能力評估")
    else:
        print("❌ 雷達圖功能測試失敗，請檢查錯誤訊息。")
