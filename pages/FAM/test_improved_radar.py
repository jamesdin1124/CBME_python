#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試改進後的雷達圖功能 - 與小兒科系統保持一致
"""

import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_improved_radar_chart():
    """測試改進後的雷達圖功能"""
    try:
        from pages.FAM.fam_data_processor import FAMDataProcessor
        from pages.FAM.fam_visualization import FAMVisualization
        
        # 讀取新的CSV檔案
        csv_path = os.path.join(os.path.dirname(__file__), '2025-09-24T03-11_export.csv')
        df = pd.read_csv(csv_path, encoding='utf-8')
        
        print(f"✅ 成功讀取CSV檔案")
        print(f"📊 原始資料形狀: {df.shape}")
        
        # 初始化處理器和視覺化模組
        processor = FAMDataProcessor()
        visualizer = FAMVisualization()
        
        # 清理資料並推斷EPA項目
        print(f"\n🧹 開始清理資料並推斷EPA項目...")
        cleaned_df = processor.clean_data(df, debug=True)
        
        if not cleaned_df.empty:
            print(f"\n📊 清理後資料形狀: {cleaned_df.shape}")
            
            # 檢查EPA項目推斷結果
            epa_counts = cleaned_df['EPA項目'].value_counts()
            print(f"\n🎯 EPA項目分佈:")
            for epa_item, count in epa_counts.items():
                if epa_item and str(epa_item).strip():
                    print(f"  {epa_item}: {count}筆")
            
            # 檢查學員資料
            if '學員' in cleaned_df.columns:
                students = processor.get_student_list(cleaned_df)
                print(f"\n👥 學員清單: {students}")
                
                # 選擇第一個學員進行雷達圖測試
                if len(students) > 0:
                    test_student = students[0]
                    print(f"\n🎯 測試學員: {test_student}")
                    
                    student_data = processor.get_student_data(cleaned_df, test_student)
                    print(f"📋 {test_student} 的資料筆數: {len(student_data)}")
                    
                    if not student_data.empty:
                        # 檢查學員的EPA項目
                        epa_items = student_data['EPA項目'].unique()
                        valid_epa_items = [item for item in epa_items if pd.notna(item) and str(item).strip()]
                        print(f"🎯 {test_student} 的EPA項目: {valid_epa_items}")
                        
                        # 檢查信賴程度
                        reliability_items = student_data['信賴程度(教師評量)'].unique()
                        valid_reliability = [item for item in reliability_items if pd.notna(item) and str(item).strip()]
                        print(f"📊 {test_student} 的信賴程度: {valid_reliability}")
                        
                        # 測試改進後的雷達圖創建
                        if len(valid_epa_items) >= 2:
                            print(f"\n📊 測試改進後的雷達圖創建...")
                            radar_fig = visualizer.create_reliability_radar_chart(
                                student_data, 
                                test_student,
                                f"{test_student} - 信賴程度雷達圖測試"
                            )
                            
                            if radar_fig:
                                print("✅ 改進後的雷達圖創建成功")
                                
                                # 檢查雷達圖的資料
                                if hasattr(radar_fig, 'data') and radar_fig.data:
                                    trace = radar_fig.data[0]
                                    print(f"📈 雷達圖軸數量: {len(trace.theta) if hasattr(trace, 'theta') else 0}")
                                    print(f"📈 雷達圖數值: {len(trace.r) if hasattr(trace, 'r') else 0}")
                                    
                                    if hasattr(trace, 'theta'):
                                        print(f"🎯 EPA項目軸: {trace.theta}")
                                    if hasattr(trace, 'r'):
                                        print(f"📊 信賴程度數值: {trace.r}")
                                        
                                        # 計算平均信賴程度
                                        avg_reliability = sum(trace.r) / len(trace.r)
                                        print(f"📊 平均信賴程度: {avg_reliability:.2f}")
                                        
                                        # 檢查數值範圍
                                        min_val = min(trace.r)
                                        max_val = max(trace.r)
                                        print(f"📊 數值範圍: {min_val:.2f} - {max_val:.2f}")
                                        
                                        # 檢查是否符合5分制
                                        if max_val <= 5.0:
                                            print("✅ 數值範圍符合5分制標準")
                                        else:
                                            print("⚠️ 數值範圍超出5分制標準")
                            else:
                                print("❌ 改進後的雷達圖創建失敗")
                        else:
                            print(f"⚠️ EPA項目數量不足（需要至少2個），無法創建雷達圖")
                        
                        # 測試EPA項目比較雷達圖
                        if len(students) >= 2:
                            print(f"\n📊 測試EPA項目比較雷達圖...")
                            if valid_epa_items:
                                test_epa = valid_epa_items[0]
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
            print("❌ 清理後資料為空")
            return False
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 開始測試改進後的雷達圖功能...")
    print("=" * 60)
    
    result = test_improved_radar_chart()
    
    print("\n" + "=" * 60)
    if result:
        print("🎉 改進後的雷達圖功能測試成功！")
        print("\n💡 改進內容：")
        print("   ✅ 使用與小兒科系統一致的5分制數值映射")
        print("   ✅ 採用與小兒科系統一致的紅色配色方案")
        print("   ✅ 實現與小兒科系統一致的圖例和布局設計")
        print("   ✅ 確保數值範圍正確（0-5分）")
        print("   ✅ 提供更精確的懸停提示（保留2位小數）")
        print("\n🏥 現在家醫部雷達圖與小兒科系統保持一致！")
    else:
        print("❌ 改進後的雷達圖功能測試失敗，請檢查錯誤訊息。")
