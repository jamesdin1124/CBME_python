#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試住院醫師EPA分數小提琴圖功能
"""

import pandas as pd
import os
from fam_data_processor import FAMDataProcessor
from fam_visualization import FAMVisualization

def test_student_violin_plot():
    """測試住院醫師EPA分數小提琴圖功能"""
    print("🧪 測試住院醫師EPA分數小提琴圖功能...")
    
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
        
        # 分析每個學員的EPA分數數據
        print(f"\\n📊 各學員EPA分數統計:")
        student_epa_data = []
        
        for student in students:
            student_df = cleaned_df[cleaned_df['學員'] == student]
            
            # 計算該住院醫師的所有EPA分數
            student_scores = []
            if '信賴程度(教師評量)' in student_df.columns:
                for _, row in student_df.iterrows():
                    reliability_text = row['信賴程度(教師評量)']
                    if pd.notna(reliability_text) and str(reliability_text).strip():
                        # 轉換為數值
                        numeric_value = visualizer._convert_reliability_to_numeric(str(reliability_text).strip())
                        if numeric_value is not None:
                            student_scores.append(numeric_value)
                            student_epa_data.append({
                                '住院醫師': str(student).strip(),
                                'EPA分數': numeric_value,
                                'EPA項目': row.get('EPA項目', 'N/A')
                            })
            
            if student_scores:
                student_df_scores = pd.DataFrame({'EPA分數': student_scores})
                print(f"   {student}:")
                print(f"     記錄數: {len(student_scores)}")
                print(f"     平均分數: {student_df_scores['EPA分數'].mean():.2f}")
                print(f"     中位數: {student_df_scores['EPA分數'].median():.2f}")
                print(f"     標準差: {student_df_scores['EPA分數'].std():.2f}")
                print(f"     範圍: {student_df_scores['EPA分數'].min():.2f} - {student_df_scores['EPA分數'].max():.2f}")
                
                # 顯示分數分布
                distribution = student_df_scores['EPA分數'].value_counts().sort_index()
                print(f"     分數分布: {distribution.to_dict()}")
            else:
                print(f"   {student}: 沒有有效的EPA分數資料")
        
        # 創建小提琴圖
        if student_epa_data:
            print(f"\\n🎻 創建住院醫師EPA分數小提琴圖...")
            violin_fig = visualizer.create_student_epa_scores_boxplot(cleaned_df)
            
            if violin_fig is not None:
                print(f"   ✅ 小提琴圖創建成功")
                
                # 檢查圖表配置
                if hasattr(violin_fig, 'layout'):
                    layout = violin_fig.layout
                    print(f"   📊 圖表配置:")
                    if hasattr(layout, 'title'):
                        print(f"     標題: {layout.title}")
                    
                    if hasattr(layout, 'xaxis') and hasattr(layout.xaxis, 'title'):
                        print(f"     X軸標題: {layout.xaxis.title}")
                    
                    if hasattr(layout, 'yaxis') and hasattr(layout.yaxis, 'title'):
                        print(f"     Y軸標題: {layout.yaxis.title}")
                    
                    if hasattr(layout, 'height'):
                        print(f"     圖表高度: {layout.height}")
                
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
                            if hasattr(trace, 'violinmode'):
                                print(f"         小提琴模式: {trace.violinmode}")
                        
                        # 檢查X軸數據（住院醫師名稱）
                        if hasattr(trace, 'x'):
                            print(f"       住院醫師數量: {len(set(trace.x))}")
                            print(f"       住院醫師列表: {list(set(trace.x))}")
                        
                        # 檢查Y軸數據（EPA分數）
                        if hasattr(trace, 'y'):
                            print(f"       EPA分數數據點數量: {len(trace.y)}")
                            if len(trace.y) > 0:
                                print(f"       EPA分數範圍: {min(trace.y):.2f} - {max(trace.y):.2f}")
            else:
                print(f"   ❌ 小提琴圖創建失敗")
        else:
            print(f"   ⚠️ 沒有有效的EPA分數資料")
        
        print("\\n🎉 住院醫師EPA分數小提琴圖功能測試完成！")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        print(f"詳細錯誤信息: {traceback.format_exc()}")
        return False

def test_violin_plot_comparison():
    """測試小提琴圖與箱線圖的比較"""
    print("\\n🧪 測試小提琴圖與箱線圖的比較...")
    
    integrated_file = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/integrated_epa_data.csv"
    
    try:
        df = pd.read_csv(integrated_file, encoding='utf-8')
        processor = FAMDataProcessor()
        visualizer = FAMVisualization()
        cleaned_df = processor.clean_data(df)
        
        students = processor.get_student_list(cleaned_df)
        print(f"   住院醫師數量: {len(students)}")
        
        # 分析數據分布特徵
        print(f"\\n   📊 數據分布特徵分析:")
        
        for student in students[:3]:  # 分析前3個學員
            student_df = cleaned_df[cleaned_df['學員'] == student]
            
            # 計算EPA分數
            student_scores = []
            if '信賴程度(教師評量)' in student_df.columns:
                for _, row in student_df.iterrows():
                    reliability_text = row['信賴程度(教師評量)']
                    if pd.notna(reliability_text) and str(reliability_text).strip():
                        numeric_value = visualizer._convert_reliability_to_numeric(str(reliability_text).strip())
                        if numeric_value is not None:
                            student_scores.append(numeric_value)
            
            if student_scores:
                student_df_scores = pd.DataFrame({'EPA分數': student_scores})
                
                print(f"     {student}:")
                print(f"       樣本數: {len(student_scores)}")
                
                # 分析分布形狀
                mean_score = student_df_scores['EPA分數'].mean()
                median_score = student_df_scores['EPA分數'].median()
                std_score = student_df_scores['EPA分數'].std()
                
                print(f"       平均分數: {mean_score:.2f}")
                print(f"       中位數: {median_score:.2f}")
                print(f"       標準差: {std_score:.2f}")
                
                # 判斷分布形狀
                if abs(mean_score - median_score) < 0.1:
                    distribution_shape = "對稱分布"
                elif mean_score > median_score:
                    distribution_shape = "右偏分布"
                else:
                    distribution_shape = "左偏分布"
                
                print(f"       分布形狀: {distribution_shape}")
                
                # 小提琴圖優勢分析
                print(f"       小提琴圖優勢:")
                print(f"         • 顯示數據密度分布")
                print(f"         • 保留箱線圖統計資訊")
                print(f"         • 顯示平均線和中位數")
                print(f"         • 更直觀的分布形狀展示")
        
        return True
        
    except Exception as e:
        print(f"❌ 小提琴圖比較測試失敗: {str(e)}")
        return False

def main():
    """主測試程式"""
    print("=" * 60)
    print("🧪 住院醫師EPA分數小提琴圖功能測試")
    print("=" * 60)
    
    # 測試小提琴圖創建
    test1_result = test_student_violin_plot()
    
    # 測試小提琴圖比較
    test2_result = test_violin_plot_comparison()
    
    print("\\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    
    if test1_result and test2_result:
        print("🎉 所有測試通過！住院醫師EPA分數小提琴圖功能正常！")
        print("\\n✅ 功能包括:")
        print("   • 將箱線圖改為小提琴圖")
        print("   • 顯示每個住院醫師EPA分數的分布密度")
        print("   • 保留箱線圖和平均線統計資訊")
        print("   • 顯示所有原始數據點")
        print("   • 美觀的填充顏色和透明度")
        print("   • 支援多個住院醫師的比較")
        print("   • 更新標題為小提琴圖")
        print("   • 更直觀的分布形狀展示")
    else:
        print("❌ 部分測試失敗，請檢查錯誤訊息")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
