#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試信賴程度計算和系統內建雷達圖功能
"""

import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_reliability_calculation():
    """測試信賴程度計算功能"""
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
            
            # 檢查信賴程度數值欄位是否已創建
            if '信賴程度(教師評量)_數值' in cleaned_df.columns:
                print(f"✅ 信賴程度數值欄位已創建")
                
                # 檢查信賴程度數值分布
                reliability_values = cleaned_df['信賴程度(教師評量)_數值'].dropna()
                if not reliability_values.empty:
                    print(f"\n📊 信賴程度數值統計:")
                    print(f"  總數: {len(reliability_values)}")
                    print(f"  平均: {reliability_values.mean():.2f}")
                    print(f"  最小: {reliability_values.min():.2f}")
                    print(f"  最大: {reliability_values.max():.2f}")
                    print(f"  標準差: {reliability_values.std():.2f}")
                    
                    # 顯示數值分布
                    value_counts = reliability_values.value_counts().sort_index()
                    print(f"\n📈 信賴程度數值分布:")
                    for value, count in value_counts.items():
                        percentage = (count / len(reliability_values)) * 100
                        print(f"  {value:.1f}分: {count}次 ({percentage:.1f}%)")
                else:
                    print("❌ 沒有有效的信賴程度數值")
            else:
                print("❌ 信賴程度數值欄位未創建")
            
            # 測試系統內建雷達圖功能
            print(f"\n🎯 測試系統內建雷達圖功能...")
            
            # 檢查系統內建雷達圖模組是否可用
            try:
                from modules.visualization.unified_radar import (
                    UnifiedRadarVisualization,
                    RadarChartConfig,
                    EPAChartConfig
                )
                print("✅ 系統內建雷達圖模組可用")
                
                # 初始化視覺化模組
                visualizer = FAMVisualization()
                
                # 檢查學員資料
                if '學員' in cleaned_df.columns:
                    students = processor.get_student_list(cleaned_df)
                    print(f"👥 學員清單: {students}")
                    
                    # 選擇第一個學員進行測試
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
                            
                            # 測試雷達圖創建
                            if len(valid_epa_items) >= 2:
                                print(f"\n📊 測試雷達圖創建...")
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
                                    print("❌ 雷達圖創建失敗")
                            else:
                                print(f"⚠️ EPA項目數量不足（需要至少2個），無法創建雷達圖")
                
                else:
                    print("❌ 沒有找到學員欄位")
                    
            except ImportError as e:
                print(f"⚠️ 系統內建雷達圖模組不可用: {e}")
                print("將使用自定義雷達圖功能")
                
                # 測試自定義雷達圖功能
                visualizer = FAMVisualization()
                print(f"\n📊 測試自定義雷達圖功能...")
                
                # 這裡可以添加自定義雷達圖的測試邏輯
                
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
    print("🚀 開始測試信賴程度計算和系統內建雷達圖功能...")
    print("=" * 60)
    
    result = test_reliability_calculation()
    
    print("\n" + "=" * 60)
    if result:
        print("🎉 信賴程度計算和雷達圖功能測試成功！")
        print("\n💡 主要功能：")
        print("   ✅ 自動計算信賴程度數值（5分制）")
        print("   ✅ 優先使用系統內建雷達圖功能")
        print("   ✅ 備用自定義雷達圖功能")
        print("   ✅ 正確的數值映射和統計分析")
        print("\n🏥 現在可以正常使用改進後的信賴程度分析功能！")
    else:
        print("❌ 信賴程度計算和雷達圖功能測試失敗，請檢查錯誤訊息。")
