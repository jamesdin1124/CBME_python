#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化測試EPA項目趨勢圖顯示
"""

import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_simple_trend():
    """簡化測試EPA項目趨勢圖"""
    try:
        from pages.FAM.fam_data_processor import FAMDataProcessor
        from pages.FAM.fam_visualization import FAMVisualization
        
        print("🚀 開始簡化測試EPA項目趨勢圖...")
        
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
            # 獲取學員和EPA項目
            students = processor.get_student_list(cleaned_df)
            epa_items = processor.get_epa_items(cleaned_df)
            
            print(f"👥 學員: {students}")
            print(f"🎯 EPA項目: {epa_items}")
            
            if len(students) > 0 and len(epa_items) > 0:
                test_student = students[0]
                test_epa = epa_items[0]  # 選擇第一個EPA項目
                
                print(f"\n🎯 測試學員: {test_student}")
                print(f"🎯 測試EPA項目: {test_epa}")
                
                # 獲取學員資料
                student_data = processor.get_student_data(cleaned_df, test_student)
                epa_data = student_data[student_data['EPA項目'] == test_epa]
                
                print(f"📊 學員總資料: {len(student_data)}")
                print(f"📊 EPA項目資料: {len(epa_data)}")
                
                if not epa_data.empty:
                    # 計算月度趨勢
                    monthly_trend_data = processor.calculate_monthly_epa_trend(epa_data, test_epa)
                    
                    if monthly_trend_data is not None and not monthly_trend_data.empty:
                        print(f"✅ 月度趨勢計算成功: {monthly_trend_data.shape}")
                        print(f"📅 月度數據:")
                        for _, row in monthly_trend_data.iterrows():
                            print(f"  {row['年月_顯示']}: 平均信賴程度 {row['平均信賴程度']:.2f}")
                        
                        # 創建趨勢圖
                        visualizer = FAMVisualization()
                        trend_fig = visualizer.create_epa_monthly_trend_chart(
                            monthly_trend_data,
                            test_epa,
                            test_student
                        )
                        
                        if trend_fig:
                            print(f"✅ 趨勢圖創建成功")
                            
                            # 檢查圖表標題
                            if hasattr(trend_fig, 'layout') and hasattr(trend_fig.layout, 'title'):
                                title = trend_fig.layout.title.text
                                print(f"📊 圖表標題: {title}")
                            
                            # 檢查數據軌跡
                            if hasattr(trend_fig, 'data') and trend_fig.data:
                                print(f"📈 數據軌跡數量: {len(trend_fig.data)}")
                                for i, trace in enumerate(trend_fig.data):
                                    print(f"  軌跡 {i+1}: {trace.name}")
                            
                            print(f"\n🎉 趨勢圖功能完全正常！")
                            print(f"💡 如果網頁上沒有看到趨勢圖，請嘗試:")
                            print(f"  1. 重新整理瀏覽器頁面 (Ctrl+F5 或 Cmd+Shift+R)")
                            print(f"  2. 清除瀏覽器緩存")
                            print(f"  3. 重新啟動Streamlit應用")
                            print(f"  4. 檢查是否在正確的頁面 (個別評核分析)")
                            
                            return True
                        else:
                            print(f"❌ 趨勢圖創建失敗")
                            return False
                    else:
                        print(f"❌ 月度趨勢計算失敗")
                        return False
                else:
                    print(f"❌ EPA項目資料為空")
                    return False
            else:
                print(f"❌ 缺少學員或EPA項目資料")
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
    result = test_simple_trend()
    print("=" * 70)
    
    if result:
        print("🎉 EPA項目趨勢圖功能測試成功！")
        print("\n🏥 趨勢圖應該能在個別評核分析頁面中看到！")
    else:
        print("❌ EPA項目趨勢圖功能測試失敗！")
