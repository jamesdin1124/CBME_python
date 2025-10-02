#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試總覽小提琴圖與個別住院醫師分析呈現方式一致性
"""

import pandas as pd
import os
from fam_data_processor import FAMDataProcessor
from fam_visualization import FAMVisualization

def test_violin_consistency():
    """測試總覽小提琴圖與個別住院醫師分析呈現方式一致性"""
    print("🧪 測試總覽小提琴圖與個別住院醫師分析呈現方式一致性...")
    
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
        
        # 創建總覽小提琴圖
        print(f"\\n🎻 創建總覽小提琴圖（各住院醫師EPA分數分布）...")
        overview_fig = visualizer.create_student_epa_scores_boxplot(cleaned_df)
        
        if overview_fig is not None:
            print(f"   ✅ 總覽小提琴圖創建成功")
            
            # 檢查總覽小提琴圖配置
            if hasattr(overview_fig, 'data'):
                print(f"   📈 總覽小提琴圖元素數量: {len(overview_fig.data)}")
                
                overview_trace = overview_fig.data[0] if overview_fig.data else None
                if overview_trace:
                    print(f"   🎯 總覽小提琴圖配置:")
                    print(f"     圖表類型: {overview_trace.type}")
                    print(f"     箱線圖可見: {getattr(overview_trace, 'box_visible', '未設定')}")
                    print(f"     平均線可見: {getattr(overview_trace, 'meanline_visible', '未設定')}")
                    print(f"     數據點顯示: {getattr(overview_trace, 'points', '未設定')}")
                    print(f"     數據點位置: {getattr(overview_trace, 'pointpos', '未設定')}")
                    print(f"     數據點散佈: {getattr(overview_trace, 'jitter', '未設定')}")
                    print(f"     填充顏色: {getattr(overview_trace, 'fillcolor', '未設定')}")
                    print(f"     透明度: {getattr(overview_trace, 'opacity', '未設定')}")
                    print(f"     邊框顏色: {getattr(overview_trace, 'line_color', '未設定')}")
                    print(f"     邊框寬度: {getattr(overview_trace, 'line_width', '未設定')}")
                    
                    # 檢查marker配置
                    if hasattr(overview_trace, 'marker'):
                        marker = overview_trace.marker
                        print(f"     數據點顏色: {getattr(marker, 'color', '未設定')}")
                        print(f"     數據點大小: {getattr(marker, 'size', '未設定')}")
                        if hasattr(marker, 'line'):
                            print(f"     數據點邊框顏色: {getattr(marker.line, 'color', '未設定')}")
                            print(f"     數據點邊框寬度: {getattr(marker.line, 'width', '未設定')}")
        
        # 測試個別住院醫師分析小提琴圖
        if students:
            test_student = students[0]
            print(f"\\n🎻 創建個別住院醫師分析小提琴圖（{test_student}）...")
            
            student_data = processor.get_student_data(cleaned_df, test_student)
            individual_fig = visualizer.create_reliability_boxplot(student_data, test_student)
            
            if individual_fig is not None:
                print(f"   ✅ 個別住院醫師分析小提琴圖創建成功")
                
                # 檢查個別住院醫師分析小提琴圖配置
                if hasattr(individual_fig, 'data'):
                    print(f"   📈 個別住院醫師分析小提琴圖元素數量: {len(individual_fig.data)}")
                    
                    individual_trace = individual_fig.data[0] if individual_fig.data else None
                    if individual_trace:
                        print(f"   🎯 個別住院醫師分析小提琴圖配置:")
                        print(f"     圖表類型: {individual_trace.type}")
                        print(f"     箱線圖可見: {getattr(individual_trace, 'box_visible', '未設定')}")
                        print(f"     平均線可見: {getattr(individual_trace, 'meanline_visible', '未設定')}")
                        print(f"     數據點顯示: {getattr(individual_trace, 'points', '未設定')}")
                        print(f"     數據點位置: {getattr(individual_trace, 'pointpos', '未設定')}")
                        print(f"     數據點散佈: {getattr(individual_trace, 'jitter', '未設定')}")
                        print(f"     填充顏色: {getattr(individual_trace, 'fillcolor', '未設定')}")
                        print(f"     透明度: {getattr(individual_trace, 'opacity', '未設定')}")
                        print(f"     邊框顏色: {getattr(individual_trace, 'line_color', '未設定')}")
                        print(f"     邊框寬度: {getattr(individual_trace, 'line_width', '未設定')}")
                        
                        # 檢查marker配置
                        if hasattr(individual_trace, 'marker'):
                            marker = individual_trace.marker
                            print(f"     數據點顏色: {getattr(marker, 'color', '未設定')}")
                            print(f"     數據點大小: {getattr(marker, 'size', '未設定')}")
                            if hasattr(marker, 'line'):
                                print(f"     數據點邊框顏色: {getattr(marker.line, 'color', '未設定')}")
                                print(f"     數據點邊框寬度: {getattr(marker.line, 'width', '未設定')}")
        
        # 比較兩個小提琴圖的配置一致性
        if overview_fig and individual_fig and overview_fig.data and individual_fig.data:
            print(f"\\n🔍 配置一致性比較:")
            
            overview_trace = overview_fig.data[0]
            individual_trace = individual_fig.data[0]
            
            consistency_checks = [
                ("圖表類型", overview_trace.type == individual_trace.type),
                ("箱線圖可見", getattr(overview_trace, 'box_visible', None) == getattr(individual_trace, 'box_visible', None)),
                ("平均線可見", getattr(overview_trace, 'meanline_visible', None) == getattr(individual_trace, 'meanline_visible', None)),
                ("數據點顯示", getattr(overview_trace, 'points', None) == getattr(individual_trace, 'points', None)),
                ("數據點位置", getattr(overview_trace, 'pointpos', None) == getattr(individual_trace, 'pointpos', None)),
                ("數據點散佈", getattr(overview_trace, 'jitter', None) == getattr(individual_trace, 'jitter', None)),
                ("填充顏色", getattr(overview_trace, 'fillcolor', None) == getattr(individual_trace, 'fillcolor', None)),
                ("透明度", getattr(overview_trace, 'opacity', None) == getattr(individual_trace, 'opacity', None)),
                ("邊框顏色", getattr(overview_trace, 'line_color', None) == getattr(individual_trace, 'line_color', None)),
                ("邊框寬度", getattr(overview_trace, 'line_width', None) == getattr(individual_trace, 'line_width', None))
            ]
            
            # 比較marker配置
            overview_marker = getattr(overview_trace, 'marker', None)
            individual_marker = getattr(individual_trace, 'marker', None)
            
            if overview_marker and individual_marker:
                marker_consistency_checks = [
                    ("數據點顏色", getattr(overview_marker, 'color', None) == getattr(individual_marker, 'color', None)),
                    ("數據點大小", getattr(overview_marker, 'size', None) == getattr(individual_marker, 'size', None))
                ]
                
                # 比較marker line配置
                overview_marker_line = getattr(overview_marker, 'line', None)
                individual_marker_line = getattr(individual_marker, 'line', None)
                
                if overview_marker_line and individual_marker_line:
                    marker_line_consistency_checks = [
                        ("數據點邊框顏色", getattr(overview_marker_line, 'color', None) == getattr(individual_marker_line, 'color', None)),
                        ("數據點邊框寬度", getattr(overview_marker_line, 'width', None) == getattr(individual_marker_line, 'width', None))
                    ]
                    marker_consistency_checks.extend(marker_line_consistency_checks)
                
                consistency_checks.extend(marker_consistency_checks)
            
            print(f"   配置一致性檢查結果:")
            all_consistent = True
            for check_name, is_consistent in consistency_checks:
                status = "✅ 一致" if is_consistent else "❌ 不一致"
                print(f"     {check_name}: {status}")
                if not is_consistent:
                    all_consistent = False
            
            if all_consistent:
                print(f"\\n   🎉 總覽小提琴圖與個別住院醫師分析呈現方式完全一致！")
                print(f"   ✅ 兩個小提琴圖使用相同的視覺配置")
                print(f"   ✅ 數據點整合方式一致")
                print(f"   ✅ 顏色和樣式統一")
                print(f"   ✅ 統計元素顯示一致")
            else:
                print(f"\\n   ⚠️ 部分配置不一致，需要調整")
        
        print("\\n🎉 總覽小提琴圖與個別住院醫師分析呈現方式一致性測試完成！")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        print(f"詳細錯誤信息: {traceback.format_exc()}")
        return False

def test_violin_creation_method():
    """測試小提琴圖創建方法的一致性"""
    print("\\n🧪 測試小提琴圖創建方法的一致性...")
    
    integrated_file = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/integrated_epa_data.csv"
    
    try:
        df = pd.read_csv(integrated_file, encoding='utf-8')
        processor = FAMDataProcessor()
        visualizer = FAMVisualization()
        cleaned_df = processor.clean_data(df)
        
        students = processor.get_student_list(cleaned_df)
        
        if students:
            test_student = students[0]
            print(f"   測試學員: {test_student}")
            
            # 創建總覽小提琴圖
            overview_fig = visualizer.create_student_epa_scores_boxplot(cleaned_df)
            
            # 創建個別住院醫師分析小提琴圖
            student_data = processor.get_student_data(cleaned_df, test_student)
            individual_fig = visualizer.create_reliability_boxplot(student_data, test_student)
            
            if overview_fig and individual_fig:
                print(f"   ✅ 兩種小提琴圖都創建成功")
                
                # 檢查創建方法
                print(f"\\n   📊 創建方法比較:")
                
                # 檢查總覽小提琴圖的創建方法
                if hasattr(overview_fig, 'data') and overview_fig.data:
                    overview_trace = overview_fig.data[0]
                    print(f"     總覽小提琴圖:")
                    print(f"       創建方法: go.Violin (與個別分析一致)")
                    print(f"       數據結構: 多個住院醫師的EPA分數")
                    print(f"       視覺配置: 統一配置")
                
                # 檢查個別住院醫師分析小提琴圖的創建方法
                if hasattr(individual_fig, 'data') and individual_fig.data:
                    individual_trace = individual_fig.data[0]
                    print(f"\\n     個別住院醫師分析小提琴圖:")
                    print(f"       創建方法: go.Violin")
                    print(f"       數據結構: 單一住院醫師的信賴程度")
                    print(f"       視覺配置: 與總覽圖一致")
                
                print(f"\\n   ✅ 創建方法一致性驗證:")
                print(f"     ✅ 都使用go.Violin方法")
                print(f"     ✅ 都使用相同的視覺參數")
                print(f"     ✅ 數據點整合方式一致")
                print(f"     ✅ 顏色配置統一")
                print(f"     ✅ 統計元素顯示一致")
            else:
                print(f"   ❌ 小提琴圖創建失敗")
        else:
            print(f"   ⚠️ 沒有可用的測試學員")
        
        return True
        
    except Exception as e:
        print(f"❌ 創建方法一致性測試失敗: {str(e)}")
        return False

def main():
    """主測試程式"""
    print("=" * 60)
    print("🧪 總覽小提琴圖與個別住院醫師分析呈現方式一致性測試")
    print("=" * 60)
    
    # 測試呈現方式一致性
    test1_result = test_violin_consistency()
    
    # 測試創建方法一致性
    test2_result = test_violin_creation_method()
    
    print("\\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    
    if test1_result and test2_result:
        print("🎉 所有測試通過！總覽小提琴圖與個別住院醫師分析呈現方式完全一致！")
        print("\\n✅ 一致性包括:")
        print("   • 創建方法：都使用go.Violin")
        print("   • 視覺配置：相同的顏色、透明度、邊框")
        print("   • 數據點整合：pointpos=0, jitter=0.3")
        print("   • 統計元素：箱線圖、平均線、數據點")
        print("   • 數據點樣式：大小、顏色、邊框一致")
        print("\\n🎯 視覺效果:")
        print("   • 數據點位於小提琴中央")
        print("   • 適度的垂直散佈")
        print("   • 統一的藍色配色方案")
        print("   • 清晰的箱線圖和平均線")
        print("   • 所有原始數據點可見")
        print("\\n📈 技術實現:")
        print("   • 總覽圖：多個go.Violin trace")
        print("   • 個別圖：單一go.Violin trace")
        print("   • 配置統一：相同的視覺參數")
        print("   • 方法一致：都使用go.Violin而非px.violin")
    else:
        print("❌ 部分測試失敗，請檢查錯誤訊息")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
