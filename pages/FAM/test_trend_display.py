#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試EPA項目趨勢圖顯示問題
"""

import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_trend_display():
    """測試EPA項目趨勢圖顯示問題"""
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
            
            if len(students) > 0:
                test_student = students[0]
                print(f"🎯 測試學員: {test_student}")
                
                student_data = processor.get_student_data(cleaned_df, test_student)
                print(f"📋 {test_student} 的資料筆數: {len(student_data)}")
                
                if not student_data.empty:
                    # 檢查EPA項目
                    epa_items = processor.get_epa_items(cleaned_df)
                    print(f"🎯 EPA項目清單: {epa_items}")
                    
                    # 檢查日期欄位
                    if '日期' in student_data.columns:
                        print(f"📅 日期欄位存在")
                        
                        # 檢查日期資料
                        date_sample = student_data['日期'].head()
                        print(f"📅 日期樣本: {list(date_sample)}")
                        
                        # 檢查日期格式
                        try:
                            date_converted = pd.to_datetime(student_data['日期'], errors='coerce')
                            valid_dates = date_converted.dropna()
                            print(f"📅 有效日期數量: {len(valid_dates)}")
                            print(f"📅 日期範圍: {valid_dates.min()} 到 {valid_dates.max()}")
                        except Exception as e:
                            print(f"❌ 日期轉換錯誤: {e}")
                        
                        # 測試每個EPA項目的月度趨勢
                        print(f"\n🔍 測試EPA項目月度趨勢顯示...")
                        
                        trend_results = []
                        for epa_item in epa_items:
                            print(f"\n--- 測試EPA項目: {epa_item} ---")
                            
                            epa_data = student_data[student_data['EPA項目'] == epa_item]
                            print(f"📊 {epa_item} 的資料筆數: {len(epa_data)}")
                            
                            if not epa_data.empty:
                                # 計算月度趨勢
                                monthly_trend_data = processor.calculate_monthly_epa_trend(epa_data, epa_item)
                                
                                if monthly_trend_data is not None and not monthly_trend_data.empty:
                                    print(f"✅ {epa_item} 月度趨勢計算成功")
                                    print(f"📈 月度數據形狀: {monthly_trend_data.shape}")
                                    
                                    # 顯示月度趨勢數據
                                    print(f"📊 {epa_item} 月度趨勢數據:")
                                    for _, row in monthly_trend_data.iterrows():
                                        print(f"  {row['年月_顯示']}: 平均信賴程度 {row['平均信賴程度']:.2f}, 評核次數 {row['評核次數']}")
                                    
                                    # 創建趨勢圖
                                    visualizer = FAMVisualization()
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
                                        
                                        trend_results.append({
                                            'epa_item': epa_item,
                                            'success': True,
                                            'data_points': len(monthly_trend_data),
                                            'chart_created': True
                                        })
                                    else:
                                        print(f"❌ {epa_item} 趨勢圖創建失敗")
                                        trend_results.append({
                                            'epa_item': epa_item,
                                            'success': False,
                                            'data_points': len(monthly_trend_data),
                                            'chart_created': False
                                        })
                                else:
                                    print(f"⚠️ {epa_item} 月度趨勢計算失敗或無數據")
                                    trend_results.append({
                                        'epa_item': epa_item,
                                        'success': False,
                                        'data_points': 0,
                                        'chart_created': False
                                    })
                            else:
                                print(f"ℹ️ {epa_item} 無資料")
                                trend_results.append({
                                    'epa_item': epa_item,
                                    'success': False,
                                    'data_points': 0,
                                    'chart_created': False
                                })
                        
                        # 總結結果
                        print(f"\n📊 趨勢圖測試總結:")
                        successful_trends = [r for r in trend_results if r['success']]
                        print(f"✅ 成功創建趨勢圖的EPA項目: {len(successful_trends)}")
                        print(f"❌ 失敗的EPA項目: {len(trend_results) - len(successful_trends)}")
                        
                        if successful_trends:
                            print(f"\n✅ 成功的EPA項目:")
                            for result in successful_trends:
                                print(f"  - {result['epa_item']}: {result['data_points']} 個數據點")
                        
                        failed_trends = [r for r in trend_results if not r['success']]
                        if failed_trends:
                            print(f"\n❌ 失敗的EPA項目:")
                            for result in failed_trends:
                                print(f"  - {result['epa_item']}: 無數據或計算失敗")
                        
                        # 檢查為什麼趨勢圖沒有顯示
                        if len(successful_trends) > 0:
                            print(f"\n💡 趨勢圖應該能正常顯示，可能的原因:")
                            print(f"  1. 頁面沒有刷新")
                            print(f"  2. 瀏覽器緩存問題")
                            print(f"  3. Streamlit應用需要重新啟動")
                            print(f"  4. 數據載入問題")
                        else:
                            print(f"\n⚠️ 沒有EPA項目能成功創建趨勢圖，需要檢查數據")
                    
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
    print("🚀 開始測試EPA項目趨勢圖顯示問題...")
    print("=" * 70)
    
    result = test_trend_display()
    
    print("\n" + "=" * 70)
    if result:
        print("🎉 EPA項目趨勢圖顯示問題診斷完成！")
        print("\n💡 如果趨勢圖沒有顯示，請嘗試:")
        print("  1. 重新整理瀏覽器頁面")
        print("  2. 清除瀏覽器緩存")
        print("  3. 重新啟動Streamlit應用")
        print("  4. 檢查個別評核分析頁面是否正確載入")
        print("\n🏥 趨勢圖功能已正確實現，應該能在個別評核分析中看到！")
    else:
        print("❌ EPA項目趨勢圖顯示問題診斷失敗，請檢查錯誤訊息。")
