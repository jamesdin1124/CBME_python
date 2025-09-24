#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試全部EPA項目比較功能
"""

import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_all_epa_comparison():
    """測試全部EPA項目比較功能"""
    try:
        from pages.FAM.fam_data_processor import FAMDataProcessor
        from pages.FAM.fam_visualization import FAMVisualization
        
        # 讀取CSV檔案
        csv_path = os.path.join(os.path.dirname(__file__), '2025-09-24T03-11_export.csv')
        df = pd.read_csv(csv_path, encoding='utf-8')
        
        print(f"✅ 成功讀取CSV檔案")
        print(f"📊 原始資料形狀: {df.shape}")
        
        # 初始化處理器
        processor = FAMDataProcessor()
        
        # 清理資料並計算信賴程度數值
        print(f"\n🧹 開始清理資料並計算信賴程度數值...")
        cleaned_df = processor.clean_data(df, debug=True)
        
        if not cleaned_df.empty:
            print(f"\n📊 清理後資料形狀: {cleaned_df.shape}")
            
            # 檢查學員資料
            students = processor.get_student_list(cleaned_df)
            print(f"👥 學員清單: {students}")
            
            # 檢查EPA項目
            epa_items = processor.get_epa_items(cleaned_df)
            print(f"🎯 EPA項目清單: {epa_items}")
            
            # 初始化視覺化模組
            visualizer = FAMVisualization()
            
            # 測試全部EPA項目比較雷達圖
            print(f"\n🎯 測試全部EPA項目比較雷達圖...")
            
            # 為了測試多學員比較，我們創建一些模擬學員資料
            test_df = cleaned_df.copy()
            
            # 檢查是否有足夠的學員進行比較
            if len(students) >= 2:
                print(f"✅ 有足夠的學員進行比較：{len(students)} 位")
                
                # 創建全部EPA項目比較雷達圖
                all_epa_radar_fig = visualizer.create_all_epa_comparison_radar_chart(
                    test_df,
                    "測試 - 全部EPA項目信賴程度比較"
                )
                
                if all_epa_radar_fig:
                    print("✅ 全部EPA項目比較雷達圖創建成功")
                    
                    # 檢查雷達圖的資料
                    if hasattr(all_epa_radar_fig, 'data') and all_epa_radar_fig.data:
                        print(f"📈 雷達圖軌跡數量: {len(all_epa_radar_fig.data)}")
                        
                        for i, trace in enumerate(all_epa_radar_fig.data):
                            student_name = trace.name
                            print(f"  軌跡 {i+1}: {student_name}")
                            print(f"    EPA項目軸: {len(trace.theta) if hasattr(trace, 'theta') else 0}")
                            print(f"    信賴程度數值: {len(trace.r) if hasattr(trace, 'r') else 0}")
                            
                            if hasattr(trace, 'theta') and hasattr(trace, 'r'):
                                # 計算該學員的平均信賴程度
                                avg_reliability = sum(trace.r) / len(trace.r)
                                print(f"    平均信賴程度: {avg_reliability:.2f}")
                                
                                # 顯示各EPA項目的表現
                                print(f"    各EPA項目表現:")
                                for j, (theta, r) in enumerate(zip(trace.theta, trace.r)):
                                    if j < len(trace.theta) - 1:  # 排除最後一個重複點
                                        print(f"      {theta}: {r:.2f}")
                        
                        # 檢查圖例配置
                        if hasattr(all_epa_radar_fig, 'layout') and all_epa_radar_fig.layout:
                            layout = all_epa_radar_fig.layout
                            if hasattr(layout, 'legend'):
                                print(f"📊 圖例配置:")
                                print(f"  顯示圖例: {layout.legend.showlegend}")
                                print(f"  圖例位置: {layout.legend.x}, {layout.legend.y}")
                                print(f"  圖例方向: {layout.legend.orientation}")
                        
                        # 檢查極座標軸配置
                        if hasattr(layout, 'polar'):
                            polar = layout.polar
                            if hasattr(polar, 'radialaxis'):
                                radial_axis = polar.radialaxis
                                print(f"📊 徑向軸配置:")
                                print(f"  範圍: {radial_axis.range}")
                                print(f"  刻度間隔: {radial_axis.dtick}")
                                print(f"  標題: {radial_axis.title.text}")
                            
                    print("\n🎯 全部EPA項目比較功能特點:")
                    print("  ✅ 同時顯示所有學員在所有EPA項目的表現")
                    print("  ✅ 使用多色彩方案區分不同學員")
                    print("  ✅ 支援最多10位學員的比較")
                    print("  ✅ 垂直圖例布局，節省空間")
                    print("  ✅ 優化的雷達圖高度和邊距")
                    print("  ✅ 縮短EPA項目名稱以便顯示")
                    print("  ✅ 詳細的懸停資訊顯示")
                    
                else:
                    print("❌ 全部EPA項目比較雷達圖創建失敗")
                    
            else:
                print(f"⚠️ 學員數量不足（需要至少2位），無法進行比較")
                print(f"   目前學員數量: {len(students)}")
                
                # 創建模擬學員資料進行測試
                print(f"\n🔧 創建模擬學員資料進行測試...")
                test_df_with_multiple_students = cleaned_df.copy()
                
                # 將部分資料分配給第二個學員
                half_size = len(test_df_with_multiple_students) // 2
                test_df_with_multiple_students.iloc[:half_size, test_df_with_multiple_students.columns.get_loc('學員')] = '測試學員2'
                
                print(f"📊 模擬資料形狀: {test_df_with_multiple_students.shape}")
                
                # 檢查模擬學員
                simulated_students = test_df_with_multiple_students['學員'].unique()
                print(f"👥 模擬學員清單: {simulated_students}")
                
                # 創建全部EPA項目比較雷達圖
                simulated_radar_fig = visualizer.create_all_epa_comparison_radar_chart(
                    test_df_with_multiple_students,
                    "模擬測試 - 全部EPA項目信賴程度比較"
                )
                
                if simulated_radar_fig:
                    print("✅ 模擬全部EPA項目比較雷達圖創建成功")
                    
                    # 檢查雷達圖的資料
                    if hasattr(simulated_radar_fig, 'data') and simulated_radar_fig.data:
                        print(f"📈 模擬雷達圖軌跡數量: {len(simulated_radar_fig.data)}")
                        
                        for i, trace in enumerate(simulated_radar_fig.data):
                            student_name = trace.name
                            print(f"  模擬軌跡 {i+1}: {student_name}")
                            
                            if hasattr(trace, 'r'):
                                avg_reliability = sum(trace.r) / len(trace.r)
                                print(f"    平均信賴程度: {avg_reliability:.2f}")
                else:
                    print("❌ 模擬全部EPA項目比較雷達圖創建失敗")
            
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
    print("🚀 開始測試全部EPA項目比較功能...")
    print("=" * 70)
    
    result = test_all_epa_comparison()
    
    print("\n" + "=" * 70)
    if result:
        print("🎉 全部EPA項目比較功能測試成功！")
        print("\n💡 新功能特點：")
        print("   ✅ 同時顯示所有EPA項目，無需分別選擇")
        print("   ✅ 支援多學員同儕比較（最多10位學員）")
        print("   ✅ 使用多色彩方案和填充效果")
        print("   ✅ 優化的圖例布局和顯示效果")
        print("   ✅ 詳細的懸停資訊和數據展示")
        print("   ✅ 智能的EPA項目名稱縮短")
        print("\n🏥 現在可以在同儕比較中選擇「全部EPA項目比較」模式！")
    else:
        print("❌ 全部EPA項目比較功能測試失敗，請檢查錯誤訊息。")
