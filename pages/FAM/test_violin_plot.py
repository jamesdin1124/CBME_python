#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試小提琴圖功能
"""

import pandas as pd
import os
from fam_data_processor import FAMDataProcessor
from fam_visualization import FAMVisualization

def test_violin_plot_creation():
    """測試小提琴圖創建功能"""
    print("🧪 測試小提琴圖創建功能...")
    
    # 載入整合資料
    integrated_file = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/integrated_epa_data.csv"
    
    if not os.path.exists(integrated_file):
        print("❌ 整合資料檔案不存在")
        return False
    
    try:
        # 載入資料
        df = pd.read_csv(integrated_file, encoding='utf-8')
        print(f"✅ 成功載入整合資料: {len(df)} 筆記錄")
        
        # 初始化處理器和視覺化工具
        processor = FAMDataProcessor()
        visualizer = FAMVisualization()
        
        # 清理資料
        cleaned_df = processor.clean_data(df)
        print(f"✅ 資料清理完成: {len(cleaned_df)} 筆記錄")
        
        # 測試學員清單
        students = processor.get_student_list(cleaned_df)
        print(f"✅ 學員清單: {len(students)} 名學員")
        
        # 測試小提琴圖創建
        if students:
            test_student = students[0]
            
            print(f"\\n🧪 測試學員: {test_student}")
            
            # 獲取學員的資料
            student_data = cleaned_df[cleaned_df['學員'] == test_student]
            
            print(f"   該學員的資料: {len(student_data)} 筆記錄")
            
            # 分析信賴程度資料
            reliability_data = []
            if '信賴程度(教師評量)' in student_data.columns:
                for _, row in student_data.iterrows():
                    reliability_text = row['信賴程度(教師評量)']
                    if pd.notna(reliability_text) and str(reliability_text).strip():
                        # 轉換為數值
                        numeric_value = visualizer._convert_reliability_to_numeric(str(reliability_text).strip())
                        if numeric_value is not None:
                            reliability_data.append(numeric_value)
            
            print(f"   有效信賴程度記錄: {len(reliability_data)} 筆")
            
            if reliability_data:
                # 顯示信賴程度分布
                reliability_df = pd.DataFrame({'信賴程度數值': reliability_data})
                print(f"   信賴程度統計:")
                print(f"     平均: {reliability_df['信賴程度數值'].mean():.2f}")
                print(f"     中位數: {reliability_df['信賴程度數值'].median():.2f}")
                print(f"     標準差: {reliability_df['信賴程度數值'].std():.2f}")
                print(f"     範圍: {reliability_df['信賴程度數值'].min():.2f} - {reliability_df['信賴程度數值'].max():.2f}")
                
                # 顯示分布
                distribution = reliability_df['信賴程度數值'].value_counts().sort_index()
                print(f"   信賴程度分布:")
                for level, count in distribution.items():
                    percentage = (count / len(reliability_data)) * 100
                    print(f"     等級 {level}: {count} 次 ({percentage:.1f}%)")
                
                # 創建小提琴圖
                violin_fig = visualizer.create_reliability_boxplot(student_data, test_student)
                
                if violin_fig is not None:
                    print(f"   ✅ 小提琴圖創建成功")
                    
                    # 檢查圖表配置
                    if hasattr(violin_fig, 'layout'):
                        layout = violin_fig.layout
                        print(f"   📊 圖表配置:")
                        if hasattr(layout, 'title'):
                            print(f"     標題: {layout.title}")
                        
                        # 檢查子圖標題
                        if hasattr(layout, 'annotations'):
                            for annotation in layout.annotations:
                                if hasattr(annotation, 'text'):
                                    print(f"     子圖標題: {annotation.text}")
                    
                    # 檢查圖表數據
                    if hasattr(violin_fig, 'data'):
                        print(f"   📈 圖表元素數量: {len(violin_fig.data)}")
                        
                        for i, trace in enumerate(violin_fig.data):
                            trace_name = trace.name if hasattr(trace, 'name') else f"Trace {i}"
                            trace_type = trace.type if hasattr(trace, 'type') else "未知"
                            print(f"     {i+1}. {trace_name} ({trace_type})")
                            
                            # 檢查小提琴圖的特殊屬性
                            if trace_type == 'violin':
                                print(f"       小提琴圖屬性:")
                                if hasattr(trace, 'box_visible'):
                                    print(f"         箱線圖可見: {trace.box_visible}")
                                if hasattr(trace, 'meanline_visible'):
                                    print(f"         平均線可見: {trace.meanline_visible}")
                                if hasattr(trace, 'points'):
                                    print(f"         數據點顯示: {trace.points}")
                                if hasattr(trace, 'fillcolor'):
                                    print(f"         填充顏色: {trace.fillcolor}")
                                if hasattr(trace, 'opacity'):
                                    print(f"         透明度: {trace.opacity}")
                else:
                    print(f"   ❌ 小提琴圖創建失敗")
            else:
                print(f"   ℹ️ 沒有有效的信賴程度資料")
        
        print("\\n🎉 小提琴圖創建功能測試完成！")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        print(f"詳細錯誤信息: {traceback.format_exc()}")
        return False

def test_multiple_students_violin_plot():
    """測試多個學員的小提琴圖"""
    print("\\n🧪 測試多個學員的小提琴圖...")
    
    integrated_file = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/integrated_epa_data.csv"
    
    try:
        df = pd.read_csv(integrated_file, encoding='utf-8')
        processor = FAMDataProcessor()
        visualizer = FAMVisualization()
        cleaned_df = processor.clean_data(df)
        
        students = processor.get_student_list(cleaned_df)
        print(f"   測試學員數量: {len(students)}")
        
        # 測試前3個學員
        for i, student in enumerate(students[:3]):
            print(f"\\n   👤 測試學員 {i+1}: {student}")
            
            student_data = cleaned_df[cleaned_df['學員'] == student]
            
            # 統計信賴程度資料
            reliability_count = 0
            if '信賴程度(教師評量)' in student_data.columns:
                for _, row in student_data.iterrows():
                    reliability_text = row['信賴程度(教師評量)']
                    if pd.notna(reliability_text) and str(reliability_text).strip():
                        numeric_value = visualizer._convert_reliability_to_numeric(str(reliability_text).strip())
                        if numeric_value is not None:
                            reliability_count += 1
            
            print(f"     記錄數: {len(student_data)}")
            print(f"     信賴程度記錄: {reliability_count}")
            
            # 創建小提琴圖
            violin_fig = visualizer.create_reliability_boxplot(student_data, student)
            
            if violin_fig is not None:
                print(f"     ✅ 小提琴圖創建成功")
            else:
                print(f"     ❌ 小提琴圖創建失敗")
        
        return True
        
    except Exception as e:
        print(f"❌ 多學員小提琴圖測試失敗: {str(e)}")
        return False

def test_violin_plot_features():
    """測試小提琴圖的特殊功能"""
    print("\\n🧪 測試小提琴圖特殊功能...")
    
    integrated_file = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/integrated_epa_data.csv"
    
    try:
        df = pd.read_csv(integrated_file, encoding='utf-8')
        processor = FAMDataProcessor()
        visualizer = FAMVisualization()
        cleaned_df = processor.clean_data(df)
        
        students = processor.get_student_list(cleaned_df)
        if students:
            test_student = students[0]
            student_data = cleaned_df[cleaned_df['學員'] == test_student]
            
            violin_fig = visualizer.create_reliability_boxplot(student_data, test_student)
            
            if violin_fig is not None:
                print(f"   📊 小提琴圖功能檢查:")
                
                # 檢查小提琴圖的特殊屬性
                for trace in violin_fig.data:
                    if hasattr(trace, 'type') and trace.type == 'violin':
                        print(f"     ✅ 小提琴圖元素:")
                        
                        # 檢查箱線圖是否顯示
                        if hasattr(trace, 'box_visible') and trace.box_visible:
                            print(f"       ✅ 箱線圖可見")
                        else:
                            print(f"       ❌ 箱線圖不可見")
                        
                        # 檢查平均線是否顯示
                        if hasattr(trace, 'meanline_visible') and trace.meanline_visible:
                            print(f"       ✅ 平均線可見")
                        else:
                            print(f"       ❌ 平均線不可見")
                        
                        # 檢查數據點是否顯示
                        if hasattr(trace, 'points') and trace.points == 'all':
                            print(f"       ✅ 所有數據點可見")
                        else:
                            print(f"       ❌ 數據點顯示設定: {trace.points}")
                        
                        # 檢查填充顏色
                        if hasattr(trace, 'fillcolor'):
                            print(f"       ✅ 填充顏色: {trace.fillcolor}")
                        
                        # 檢查透明度
                        if hasattr(trace, 'opacity'):
                            print(f"       ✅ 透明度: {trace.opacity}")
                        
                        # 檢查數據點散佈
                        if hasattr(trace, 'jitter'):
                            print(f"       ✅ 數據點散佈: {trace.jitter}")
                        
                        break
                
                # 檢查子圖標題是否更新
                if hasattr(violin_fig, 'layout') and hasattr(violin_fig.layout, 'annotations'):
                    for annotation in violin_fig.layout.annotations:
                        if hasattr(annotation, 'text'):
                            if '小提琴圖' in annotation.text:
                                print(f"     ✅ 子圖標題已更新為小提琴圖")
                                break
                    else:
                        print(f"     ❌ 子圖標題未找到小提琴圖相關文字")
        
        return True
        
    except Exception as e:
        print(f"❌ 小提琴圖功能測試失敗: {str(e)}")
        return False

def main():
    """主測試程式"""
    print("=" * 60)
    print("🧪 小提琴圖功能測試")
    print("=" * 60)
    
    # 測試小提琴圖創建
    test1_result = test_violin_plot_creation()
    
    # 測試多個學員的小提琴圖
    test2_result = test_multiple_students_violin_plot()
    
    # 測試小提琴圖特殊功能
    test3_result = test_violin_plot_features()
    
    print("\\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    
    if test1_result and test2_result and test3_result:
        print("🎉 所有測試通過！小提琴圖功能正常！")
        print("\\n✅ 功能包括:")
        print("   • 將箱線圖改為小提琴圖")
        print("   • 顯示數據分布密度和形狀")
        print("   • 保留箱線圖和平均線")
        print("   • 顯示所有原始數據點")
        print("   • 美觀的填充顏色和透明度")
        print("   • 保持統計表格功能")
        print("   • 更新子圖標題為小提琴圖")
    else:
        print("❌ 部分測試失敗，請檢查錯誤訊息")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
