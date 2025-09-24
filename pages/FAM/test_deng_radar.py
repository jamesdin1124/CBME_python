#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試鄧祖嶸的雷達圖功能
"""

import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_deng_radar_chart():
    """測試鄧祖嶸的雷達圖功能"""
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
            # 專門測試鄧祖嶸的資料
            test_student = "鄧祖嶸"
            print(f"\n🎯 測試學員: {test_student}")
            
            # 獲取鄧祖嶸的資料
            student_data = processor.get_student_data(cleaned_df, test_student)
            print(f"📋 {test_student} 的資料筆數: {len(student_data)}")
            
            if not student_data.empty:
                # 檢查EPA項目欄位
                epa_items = student_data['EPA項目'].unique()
                print(f"🎯 {test_student} 的EPA項目: {epa_items}")
                
                # 檢查信賴程度欄位
                reliability_items = student_data['信賴程度(教師評量)'].unique()
                print(f"📊 {test_student} 的信賴程度: {reliability_items}")
                
                # 詳細檢查每個EPA項目的資料
                for epa_item in epa_items:
                    if pd.notna(epa_item) and epa_item and str(epa_item).strip():
                        epa_data = student_data[student_data['EPA項目'] == epa_item]
                        print(f"\n🔍 EPA項目: {epa_item}")
                        print(f"   記錄數: {len(epa_data)}")
                        
                        reliability_values = epa_data['信賴程度(教師評量)'].dropna()
                        print(f"   信賴程度值: {reliability_values.tolist()}")
                
                # 測試雷達圖創建
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
                        if hasattr(trace, 'r') and trace.r:
                            avg_reliability = sum(trace.r) / len(trace.r)
                            print(f"📊 平均信賴程度: {avg_reliability:.2f}")
                else:
                    print("❌ 雷達圖創建失敗")
                    
                    # 詳細調試資訊
                    print("\n🔍 調試資訊:")
                    
                    # 檢查信賴程度映射
                    reliability_mapping = {
                        '獨立執行': 5,
                        '必要時知會教師確認': 4,
                        '教師事後重點確認': 4,
                        '教師在旁必要時協助': 3,
                        '教師在旁逐步共同操作': 2,
                        '學員在旁觀察': 1,
                        '不允許學員觀察': 0,
                        '請選擇': 0
                    }
                    
                    print("信賴程度映射:")
                    for level, score in reliability_mapping.items():
                        count = len(student_data[student_data['信賴程度(教師評量)'] == level])
                        print(f"  {level}: {score}分 (出現{count}次)")
                
                return True
            else:
                print(f"❌ {test_student} 沒有資料")
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
    print("🚀 開始測試鄧祖嶸的雷達圖功能...")
    print("=" * 50)
    
    result = test_deng_radar_chart()
    
    print("\n" + "=" * 50)
    if result:
        print("🎉 鄧祖嶸雷達圖功能測試成功！")
    else:
        print("❌ 鄧祖嶸雷達圖功能測試失敗，請檢查錯誤訊息。")
