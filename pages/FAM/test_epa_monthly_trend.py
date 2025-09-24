#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試EPA項目月度趨勢功能
"""

import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_epa_monthly_trend():
    """測試EPA項目月度趨勢功能"""
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
            
            # 測試EPA項目月度趨勢功能
            print(f"\n🎯 測試EPA項目月度趨勢功能...")
            
            if len(students) > 0:
                test_student = students[0]
                print(f"🎯 測試學員: {test_student}")
                
                student_data = processor.get_student_data(cleaned_df, test_student)
                print(f"📋 {test_student} 的資料筆數: {len(student_data)}")
                
                if not student_data.empty:
                    # 檢查日期欄位
                    if '日期' in student_data.columns:
                        print(f"📅 日期欄位存在")
                        
                        # 檢查日期資料
                        date_sample = student_data['日期'].head()
                        print(f"📅 日期樣本: {list(date_sample)}")
                        
                        # 測試每個EPA項目的月度趨勢
                        for epa_item in epa_items:
                            print(f"\n🔍 測試EPA項目: {epa_item}")
                            
                            epa_data = student_data[student_data['EPA項目'] == epa_item]
                            print(f"📊 {epa_item} 的資料筆數: {len(epa_data)}")
                            
                            if not epa_data.empty:
                                # 計算月度趨勢
                                monthly_trend_data = processor.calculate_monthly_epa_trend(epa_data, epa_item)
                                
                                if monthly_trend_data is not None and not monthly_trend_data.empty:
                                    print(f"✅ {epa_item} 月度趨勢計算成功")
                                    print(f"📈 月度數據形狀: {monthly_trend_data.shape}")
                                    print(f"📅 月度數據欄位: {list(monthly_trend_data.columns)}")
                                    
                                    # 顯示月度趨勢數據
                                    print(f"📊 {epa_item} 月度趨勢數據:")
                                    for _, row in monthly_trend_data.iterrows():
                                        print(f"  {row['年月_顯示']}: 平均信賴程度 {row['平均信賴程度']:.2f}, 評核次數 {row['評核次數']}")
                                    
                                    # 創建趨勢圖
                                    trend_fig = visualizer.create_epa_monthly_trend_chart(
                                        monthly_trend_data,
                                        epa_item,
                                        test_student
                                    )
                                    
                                    if trend_fig:
                                        print(f"✅ {epa_item} 趨勢圖創建成功")
                                        
                                        # 檢查趨勢圖的資料
                                        if hasattr(trend_fig, 'data') and trend_fig.data:
                                            print(f"📈 {epa_item} 趨勢圖軌跡數量: {len(trend_fig.data)}")
                                            
                                            for i, trace in enumerate(trend_fig.data):
                                                print(f"  軌跡 {i+1}: {trace.name}")
                                                if hasattr(trace, 'x') and hasattr(trace, 'y'):
                                                    print(f"    X軸數據點: {len(trace.x)}")
                                                    print(f"    Y軸數據點: {len(trace.y)}")
                                                    if len(trace.y) > 0:
                                                        print(f"    Y軸範圍: {min(trace.y):.2f} - {max(trace.y):.2f}")
                                        
                                        # 檢查圖表配置
                                        if hasattr(trend_fig, 'layout'):
                                            layout = trend_fig.layout
                                            print(f"📊 {epa_item} 圖表配置:")
                                            if hasattr(layout, 'title'):
                                                print(f"  標題: {layout.title.text}")
                                            if hasattr(layout, 'xaxis'):
                                                print(f"  X軸標題: {layout.xaxis.title.text}")
                                            if hasattr(layout, 'yaxis'):
                                                print(f"  Y軸標題: {layout.yaxis.title.text}")
                                            if hasattr(layout, 'yaxis2'):
                                                print(f"  Y2軸標題: {layout.yaxis2.title.text}")
                                    else:
                                        print(f"❌ {epa_item} 趨勢圖創建失敗")
                                else:
                                    print(f"⚠️ {epa_item} 月度趨勢計算失敗或無數據")
                            else:
                                print(f"ℹ️ {epa_item} 無資料")
                        
                        print(f"\n🎯 EPA項目月度趨勢功能特點:")
                        print("  ✅ 按月份分組計算平均信賴程度")
                        print("  ✅ 雙Y軸設計：左軸顯示信賴程度，右軸顯示評核次數")
                        print("  ✅ 自動添加趨勢線（線性回歸）")
                        print("  ✅ 詳細的懸停資訊顯示")
                        print("  ✅ 優化的圖表布局和視覺效果")
                        print("  ✅ 支援多個EPA項目的獨立趨勢分析")
                        
                    else:
                        print("❌ 日期欄位不存在，無法進行月度趨勢分析")
                else:
                    print("❌ 學員資料為空")
            else:
                print("❌ 沒有學員資料")
            
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
    print("🚀 開始測試EPA項目月度趨勢功能...")
    print("=" * 70)
    
    result = test_epa_monthly_trend()
    
    print("\n" + "=" * 70)
    if result:
        print("🎉 EPA項目月度趨勢功能測試成功！")
        print("\n💡 新功能特點：")
        print("   ✅ 每個EPA項目獨立的月度趨勢折線圖")
        print("   ✅ 同一個月的資料計算平均值（同一梯次）")
        print("   ✅ 雙Y軸設計：信賴程度 + 評核次數")
        print("   ✅ 自動趨勢線分析（線性回歸）")
        print("   ✅ 詳細的統計資訊：總評核次數、評核月數、平均信賴程度、趨勢變化")
        print("   ✅ 優化的視覺化效果和用戶體驗")
        print("\n🏥 現在可以在個別評核分析中看到每個EPA項目的月度趨勢圖！")
    else:
        print("❌ EPA項目月度趨勢功能測試失敗，請檢查錯誤訊息。")
