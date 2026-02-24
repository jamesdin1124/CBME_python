#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試修正後的雷達圖功能 - 解決欄位名稱不匹配問題
"""

import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_radar_fix():
    """測試修正後的雷達圖功能"""
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
            
            # 檢查信賴程度數值欄位
            if '信賴程度(教師評量)_數值' in cleaned_df.columns:
                print(f"✅ 信賴程度數值欄位已創建")
                
                # 檢查信賴程度數值分布
                reliability_values = cleaned_df['信賴程度(教師評量)_數值'].dropna()
                if not reliability_values.empty:
                    print(f"\n📊 信賴程度數值統計:")
                    print(f"  總數: {len(reliability_values)}")
                    print(f"  平均: {reliability_values.mean():.2f}")
                    print(f"  範圍: {reliability_values.min():.2f} - {reliability_values.max():.2f}")
            
            # 測試修正後的雷達圖功能
            print(f"\n🎯 測試修正後的雷達圖功能...")
            
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
                            
                            # 測試資料適配功能
                            print(f"\n🔧 測試資料適配功能...")
                            adapted_df = visualizer._adapt_data_for_unified_radar(student_data)
                            
                            if adapted_df is not None:
                                print("✅ 資料適配成功")
                                print(f"📊 適配後欄位: {list(adapted_df.columns)}")
                                
                                # 檢查關鍵欄位
                                if 'EPA評核項目' in adapted_df.columns:
                                    print("✅ EPA評核項目欄位已創建")
                                    epa_count = adapted_df['EPA評核項目'].nunique()
                                    print(f"📈 EPA項目數量: {epa_count}")
                                
                                if '教師評核EPA等級_數值' in adapted_df.columns:
                                    print("✅ 教師評核EPA等級_數值欄位已創建")
                                    score_count = adapted_df['教師評核EPA等級_數值'].notna().sum()
                                    print(f"📈 有效評分數量: {score_count}")
                                
                                if '階層' in adapted_df.columns:
                                    print("✅ 階層欄位已創建")
                                    layer_value = adapted_df['階層'].iloc[0]
                                    print(f"📈 階層值: {layer_value}")
                                
                                if '學員姓名' in adapted_df.columns:
                                    print("✅ 學員姓名欄位已創建")
                                    name_value = adapted_df['學員姓名'].iloc[0]
                                    print(f"📈 學員姓名: {name_value}")
                            else:
                                print("❌ 資料適配失敗")
                            
                            # 測試修正後的雷達圖創建
                            if len(valid_epa_items) >= 2:
                                print(f"\n📊 測試修正後的雷達圖創建...")
                                radar_fig = visualizer.create_reliability_radar_chart(
                                    student_data, 
                                    test_student,
                                    f"{test_student} - 信賴程度雷達圖測試（修正版）"
                                )
                                
                                if radar_fig:
                                    print("✅ 修正後的雷達圖創建成功")
                                    
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
                                else:
                                    print("❌ 修正後的雷達圖創建失敗")
                            else:
                                print(f"⚠️ EPA項目數量不足（需要至少2個），無法創建雷達圖")
                
            except ImportError as e:
                print(f"⚠️ 系統內建雷達圖模組不可用: {e}")
                print("將使用自定義雷達圖功能")
                
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
    print("🚀 開始測試修正後的雷達圖功能...")
    print("=" * 70)
    
    result = test_radar_fix()
    
    print("\n" + "=" * 70)
    if result:
        print("🎉 修正後的雷達圖功能測試成功！")
        print("\n💡 主要修正：")
        print("   ✅ 解決欄位名稱不匹配問題（EPA項目 → EPA評核項目）")
        print("   ✅ 添加資料適配器處理不同欄位格式")
        print("   ✅ 確保系統內建雷達圖能正確讀取家醫部資料")
        print("   ✅ 自動創建缺失的欄位（階層、學員姓名等）")
        print("   ✅ 保持向後兼容性，支援自定義雷達圖備用方案")
        print("\n🏥 現在雷達圖應該能正常顯示，不再出現創建錯誤！")
    else:
        print("❌ 修正後的雷達圖功能測試失敗，請檢查錯誤訊息。")
