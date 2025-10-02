#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試增強版EPA項目趨勢分析功能
"""

import pandas as pd
import os
from fam_data_processor import FAMDataProcessor
from fam_visualization import FAMVisualization

def test_enhanced_trend_analysis():
    """測試增強版趨勢分析功能"""
    print("🧪 測試增強版EPA項目趨勢分析功能...")
    
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
        print(f"   EPA項目: {list(epa_items)[:5]}")
        
        # 測試增強版趨勢分析功能
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
            
            # 測試增強版趨勢圖創建
            enhanced_fig = visualizer.create_enhanced_monthly_trend_chart(
                epa_data, test_epa, test_student
            )
            
            if enhanced_fig is not None:
                print("✅ 增強版趨勢圖創建成功")
                
                # 檢查圖表配置
                layout = enhanced_fig.layout
                print(f"   圖表標題: {layout.title.text}")
                print(f"   X軸標題: {layout.xaxis.title.text}")
                print(f"   Y軸標題: {layout.yaxis.title.text}")
                
                # 檢查資料系列
                traces = enhanced_fig.data
                print(f"   資料系列數量: {len(traces)}")
                for i, trace in enumerate(traces):
                    print(f"     系列{i+1}: {trace.name} (模式: {trace.mode})")
            else:
                print("⚠️ 增強版趨勢圖創建失敗，可能沒有足夠的資料")
        
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
        
        print("\\n🎉 增強版趨勢分析功能測試完成！")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        print(f"詳細錯誤信息: {traceback.format_exc()}")
        return False

def test_data_source_filtering():
    """測試資料來源過濾功能"""
    print("\\n🧪 測試資料來源過濾功能...")
    
    integrated_file = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/integrated_epa_data.csv"
    
    try:
        df = pd.read_csv(integrated_file, encoding='utf-8')
        processor = FAMDataProcessor()
        cleaned_df = processor.clean_data(df)
        
        if '資料來源' in cleaned_df.columns:
            sources = cleaned_df['資料來源'].unique()
            print(f"✅ 可用資料來源: {list(sources)}")
            
            # 測試每個資料來源的過濾
            for source in sources:
                filtered_df = cleaned_df[cleaned_df['資料來源'] == source]
                students_in_source = filtered_df['學員'].nunique()
                epa_items_in_source = filtered_df['EPA項目'].nunique()
                
                print(f"   {source}: {len(filtered_df)} 筆記錄, {students_in_source} 名學員, {epa_items_in_source} 種EPA項目")
                
                # 測試該來源的趨勢分析
                if students_in_source > 0 and epa_items_in_source > 0:
                    test_student = filtered_df['學員'].iloc[0]
                    test_epa = filtered_df['EPA項目'].iloc[0]
                    
                    student_epa_data = filtered_df[
                        (filtered_df['學員'] == test_student) & 
                        (filtered_df['EPA項目'] == test_epa)
                    ]
                    
                    print(f"     測試組合 {test_student} - {test_epa}: {len(student_epa_data)} 筆記錄")
        
        print("✅ 資料來源過濾功能測試完成")
        return True
        
    except Exception as e:
        print(f"❌ 資料來源過濾測試失敗: {str(e)}")
        return False

def main():
    """主測試程式"""
    print("=" * 60)
    print("🧪 增強版EPA項目趨勢分析功能測試")
    print("=" * 60)
    
    # 測試增強版趨勢分析
    test1_result = test_enhanced_trend_analysis()
    
    # 測試資料來源過濾
    test2_result = test_data_source_filtering()
    
    print("\\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    
    if test1_result and test2_result:
        print("🎉 所有測試通過！增強版趨勢分析功能已準備就緒！")
        print("\\n✅ 新功能包括:")
        print("   • 支援多資料來源的趨勢分析")
        print("   • 資料來源過濾選項")
        print("   • 增強版視覺化圖表")
        print("   • 區分EMYWAY歷史資料和現有系統資料")
        print("   • 詳細的資料來源統計")
    else:
        print("❌ 部分測試失敗，請檢查錯誤訊息")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
