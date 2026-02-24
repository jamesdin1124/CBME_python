#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試EPA項目箱線圖功能
"""

import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_boxplot():
    """測試EPA項目箱線圖功能"""
    try:
        from pages.FAM.fam_data_processor import FAMDataProcessor
        from pages.FAM.fam_visualization import FAMVisualization
        
        print("🚀 開始測試EPA項目箱線圖功能...")
        
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
                test_epa = epa_items[0]  # EPA03.預防注射
                
                print(f"\n🎯 測試學員: {test_student}")
                print(f"🎯 測試EPA項目: {test_epa}")
                
                # 獲取學員資料
                student_data = processor.get_student_data(cleaned_df, test_student)
                epa_data = student_data[student_data['EPA項目'] == test_epa]
                
                print(f"📊 學員總資料: {len(student_data)}")
                print(f"📊 EPA項目資料: {len(epa_data)}")
                
                if not epa_data.empty:
                    # 計算月度趨勢
                    print(f"\n🧮 計算月度趨勢...")
                    monthly_trend_data = processor.calculate_monthly_epa_trend(epa_data, test_epa)
                    
                    if monthly_trend_data is not None and not monthly_trend_data.empty:
                        print(f"✅ 月度趨勢計算成功: {monthly_trend_data.shape}")
                        print(f"📅 月度數據:")
                        print(monthly_trend_data)
                        
                        # 創建箱線圖
                        print(f"\n📦 創建箱線圖...")
                        visualizer = FAMVisualization()
                        
                        try:
                            boxplot_fig = visualizer.create_simple_monthly_trend_chart(
                                monthly_trend_data,
                                test_epa,
                                test_student,
                                epa_data  # 傳入原始數據
                            )
                            
                            if boxplot_fig:
                                print(f"✅ 箱線圖創建成功")
                                print(f"📊 圖表類型: {type(boxplot_fig)}")
                                
                                # 檢查圖表屬性
                                if hasattr(boxplot_fig, 'data'):
                                    print(f"📦 數據軌跡數量: {len(boxplot_fig.data)}")
                                    for i, trace in enumerate(boxplot_fig.data):
                                        print(f"  軌跡 {i+1}: {trace.name}")
                                        if hasattr(trace, 'x') and hasattr(trace, 'y'):
                                            print(f"    X軸數據點: {len(trace.x)}")
                                            print(f"    Y軸數據點: {len(trace.y)}")
                                
                                if hasattr(boxplot_fig, 'layout'):
                                    layout = boxplot_fig.layout
                                    if hasattr(layout, 'title'):
                                        print(f"📊 圖表標題: {layout.title.text}")
                                
                                print(f"\n🎉 箱線圖創建完全成功！")
                                return True
                            else:
                                print(f"❌ 箱線圖創建失敗，返回None")
                                return False
                                
                        except Exception as e:
                            print(f"❌ 箱線圖創建時發生異常: {e}")
                            import traceback
                            traceback.print_exc()
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
    result = test_boxplot()
    print("=" * 70)
    
    if result:
        print("🎉 EPA項目箱線圖功能測試成功！")
    else:
        print("❌ EPA項目箱線圖功能測試失敗！")
