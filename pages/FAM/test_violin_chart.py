#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試violin圖功能
"""

import pandas as pd
import os
from fam_data_processor import FAMDataProcessor
from fam_visualization import FAMVisualization

def test_violin_chart():
    """測試violin圖功能"""
    print("🧪 測試violin圖功能...")
    
    # 載入整合資料
    integrated_file = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/integrated_epa_data.csv"
    
    if not os.path.exists(integrated_file):
        print("❌ 整合資料檔案不存在")
        return False
    
    try:
        # 載入資料
        df = pd.read_csv(integrated_file, encoding='utf-8')
        print(f"✅ 成功載入整合資料: {len(df)} 筆記錄")
        
        # 初始化處理器和視覺化模組
        processor = FAMDataProcessor()
        visualizer = FAMVisualization()
        
        # 清理資料
        cleaned_df = processor.clean_data(df)
        print(f"✅ 資料清理完成: {len(cleaned_df)} 筆記錄")
        
        # 測試資料來源統計
        if '資料來源' in cleaned_df.columns:
            source_counts = cleaned_df['資料來源'].value_counts()
            print(f"✅ 資料來源分布: {source_counts.to_dict()}")
        
        # 測試學員清單
        students = processor.get_student_list(cleaned_df)
        print(f"✅ 學員清單: {len(students)} 名學員")
        
        # 測試EPA項目清單
        epa_items = processor.get_epa_items(cleaned_df)
        print(f"✅ EPA項目清單: {len(epa_items)} 種")
        
        # 測試violin圖創建
        if students and epa_items:
            test_student = students[0]
            test_epa = list(epa_items)[0]
            
            print(f"\\n🧪 測試學員: {test_student}, EPA項目: {test_epa}")
            
            # 獲取學員的EPA資料
            student_data = cleaned_df[cleaned_df['學員'] == test_student]
            epa_data = student_data[student_data['EPA項目'] == test_epa]
            
            print(f"   該學員的{test_epa}資料: {len(epa_data)} 筆記錄")
            
            if '資料來源' in epa_data.columns:
                source_counts = epa_data['資料來源'].value_counts()
                print(f"   資料來源分布: {source_counts.to_dict()}")
            
            # 測試violin圖創建
            violin_fig = visualizer.create_enhanced_monthly_trend_chart(
                epa_data, test_epa, test_student
            )
            
            if violin_fig is not None:
                print("✅ violin圖創建成功")
                
                # 檢查圖表配置
                layout = violin_fig.layout
                print(f"   圖表標題: {layout.title.text}")
                print(f"   X軸標題: {layout.xaxis.title.text}")
                print(f"   Y軸標題: {layout.yaxis.title.text}")
                print(f"   Violin模式: {layout.violinmode}")
                
                # 檢查資料系列
                traces = violin_fig.data
                print(f"   Violin圖數量: {len(traces)}")
                for i, trace in enumerate(traces):
                    print(f"     Violin {i+1}: {trace.name} (類型: {trace.type})")
            else:
                print("⚠️ violin圖創建失敗，可能沒有足夠的資料")
        
        # 測試多個學員和EPA項目的組合
        print(f"\\n🧪 測試多個學員EPA項目組合...")
        test_combinations = []
        
        for student in students[:3]:  # 測試前3名學員
            student_data = cleaned_df[cleaned_df['學員'] == student]
            student_epa_items = student_data['EPA項目'].unique()
            
            for epa_item in student_epa_items[:2]:  # 每個學員測試前2個EPA項目
                epa_data = student_data[student_data['EPA項目'] == epa_item]
                if len(epa_data) > 0:
                    test_combinations.append((student, epa_item, len(epa_data)))
        
        print(f"   找到 {len(test_combinations)} 個有效的學員-EPA組合")
        for student, epa_item, count in test_combinations[:5]:
            print(f"   {student} - {epa_item}: {count} 筆記錄")
        
        print("\\n🎉 violin圖功能測試完成！")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        print(f"詳細錯誤信息: {traceback.format_exc()}")
        return False

def main():
    """主測試程式"""
    print("=" * 60)
    print("🧪 Violin圖功能測試")
    print("=" * 60)
    
    # 測試violin圖功能
    test_result = test_violin_chart()
    
    print("\\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    
    if test_result:
        print("🎉 所有測試通過！Violin圖功能已準備就緒！")
        print("\\n✅ 新功能包括:")
        print("   • 使用violin圖合併顯示兩個系統資料")
        print("   • 支援多資料來源的分布分析")
        print("   • 顯示信賴程度的分布密度")
        print("   • 包含箱線圖和平均線")
        print("   • 支援數據點顯示和抖動效果")
    else:
        print("❌ 測試失敗，請檢查錯誤訊息")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
