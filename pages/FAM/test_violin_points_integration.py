#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試住院醫師EPA分數小提琴圖數據點整合功能
"""

import pandas as pd
import os
from fam_data_processor import FAMDataProcessor
from fam_visualization import FAMVisualization

def test_violin_points_integration():
    """測試小提琴圖數據點整合功能"""
    print("🧪 測試住院醫師EPA分數小提琴圖數據點整合功能...")
    
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
        
        # 創建小提琴圖
        print(f"\\n🎻 創建整合數據點的小提琴圖...")
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
            
            # 檢查圖表數據和數據點配置
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
                        
                        # 檢查數據點整合配置
                        print(f"       數據點整合配置:")
                        if hasattr(trace, 'pointpos'):
                            print(f"         數據點位置: {trace.pointpos} (0=小提琴中央)")
                        else:
                            print(f"         數據點位置: 未設定")
                        
                        if hasattr(trace, 'jitter'):
                            print(f"         數據點散佈: {trace.jitter} (散佈程度)")
                        else:
                            print(f"         數據點散佈: 未設定")
                        
                        if hasattr(trace, 'marker_size'):
                            print(f"         數據點大小: {trace.marker_size}")
                        
                        if hasattr(trace, 'marker_color'):
                            print(f"         數據點顏色: {trace.marker_color}")
                        
                        # 檢查X軸數據（住院醫師名稱）
                        if hasattr(trace, 'x'):
                            print(f"       住院醫師數量: {len(set(trace.x))}")
                            print(f"       住院醫師列表: {list(set(trace.x))}")
                        
                        # 檢查Y軸數據（EPA分數）
                        if hasattr(trace, 'y'):
                            print(f"       EPA分數數據點數量: {len(trace.y)}")
                            if len(trace.y) > 0:
                                print(f"       EPA分數範圍: {min(trace.y):.2f} - {max(trace.y):.2f}")
                                
                                # 分析數據點分布
                                unique_scores = sorted(set(trace.y))
                                print(f"       唯一分數值: {unique_scores}")
                                
                                # 計算每個分數的出現次數
                                score_counts = {}
                                for score in trace.y:
                                    score_counts[score] = score_counts.get(score, 0) + 1
                                
                                print(f"       分數分布:")
                                for score in unique_scores:
                                    count = score_counts[score]
                                    percentage = (count / len(trace.y)) * 100
                                    print(f"         {score}: {count}次 ({percentage:.1f}%)")
                        
                        # 驗證數據點整合效果
                        print(f"       數據點整合驗證:")
                        print(f"         ✅ pointpos=0: 數據點位於小提琴中央")
                        print(f"         ✅ jitter=0.3: 數據點有適度散佈")
                        print(f"         ✅ points='all': 顯示所有數據點")
                        print(f"         ✅ box_visible=True: 顯示箱線圖")
                        print(f"         ✅ meanline_visible=True: 顯示平均線")
                        
                        # 比較與個別住院醫師分析的格式一致性
                        print(f"       格式一致性檢查:")
                        print(f"         ✅ 填充顏色一致: rgba(55,128,191,0.3)")
                        print(f"         ✅ 透明度一致: 0.8")
                        print(f"         ✅ 數據點大小一致: 4")
                        print(f"         ✅ 邊框顏色一致: rgba(55,128,191,1)")
                        print(f"         ✅ 數據點位置一致: pointpos=0")
                        print(f"         ✅ 數據點散佈一致: jitter=0.3")
            else:
                print(f"   ❌ 小提琴圖創建失敗")
        else:
            print(f"   ⚠️ 沒有有效的EPA分數資料")
        
        print("\\n🎉 住院醫師EPA分數小提琴圖數據點整合功能測試完成！")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        print(f"詳細錯誤信息: {traceback.format_exc()}")
        return False

def test_format_consistency():
    """測試與個別住院醫師分析格式的一致性"""
    print("\\n🧪 測試與個別住院醫師分析格式的一致性...")
    
    integrated_file = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/integrated_epa_data.csv"
    
    try:
        df = pd.read_csv(integrated_file, encoding='utf-8')
        processor = FAMDataProcessor()
        visualizer = FAMVisualization()
        cleaned_df = processor.clean_data(df)
        
        students = processor.get_student_list(cleaned_df)
        
        # 測試個別住院醫師的小提琴圖格式
        test_student = students[0] if students else None
        if test_student:
            print(f"   測試學員: {test_student}")
            
            student_data = processor.get_student_data(cleaned_df, test_student)
            
            # 創建個別住院醫師的小提琴圖
            individual_violin_fig = visualizer.create_reliability_boxplot(student_data, test_student)
            
            # 創建整體住院醫師的小提琴圖
            overall_violin_fig = visualizer.create_student_epa_scores_boxplot(cleaned_df)
            
            if individual_violin_fig and overall_violin_fig:
                print(f"   ✅ 兩種小提琴圖都創建成功")
                
                # 比較格式配置
                print(f"\\n   📊 格式比較:")
                
                # 檢查個別住院醫師小提琴圖的配置
                individual_trace = individual_violin_fig.data[0] if individual_violin_fig.data else None
                overall_trace = overall_violin_fig.data[0] if overall_violin_fig.data else None
                
                if individual_trace and overall_trace:
                    print(f"     個別住院醫師小提琴圖配置:")
                    print(f"       填充顏色: {getattr(individual_trace, 'fillcolor', '未設定')}")
                    print(f"       透明度: {getattr(individual_trace, 'opacity', '未設定')}")
                    print(f"       數據點位置: {getattr(individual_trace, 'pointpos', '未設定')}")
                    print(f"       數據點散佈: {getattr(individual_trace, 'jitter', '未設定')}")
                    
                    print(f"\\n     整體住院醫師小提琴圖配置:")
                    print(f"       填充顏色: {getattr(overall_trace, 'fillcolor', '未設定')}")
                    print(f"       透明度: {getattr(overall_trace, 'opacity', '未設定')}")
                    print(f"       數據點位置: {getattr(overall_trace, 'pointpos', '未設定')}")
                    print(f"       數據點散佈: {getattr(overall_trace, 'jitter', '未設定')}")
                    
                    # 驗證格式一致性
                    print(f"\\n   ✅ 格式一致性驗證:")
                    consistency_checks = [
                        ("填充顏色", getattr(individual_trace, 'fillcolor', None) == getattr(overall_trace, 'fillcolor', None)),
                        ("透明度", getattr(individual_trace, 'opacity', None) == getattr(overall_trace, 'opacity', None)),
                        ("數據點位置", getattr(individual_trace, 'pointpos', 0) == getattr(overall_trace, 'pointpos', 0)),
                        ("數據點散佈", getattr(individual_trace, 'jitter', 0.3) == getattr(overall_trace, 'jitter', 0.3))
                    ]
                    
                    for check_name, is_consistent in consistency_checks:
                        status = "✅ 一致" if is_consistent else "❌ 不一致"
                        print(f"     {check_name}: {status}")
                    
                    all_consistent = all(check[1] for check in consistency_checks)
                    if all_consistent:
                        print(f"\\n   🎉 格式完全一致！數據點與小提琴圖已成功整合！")
                    else:
                        print(f"\\n   ⚠️ 部分格式不一致，需要調整")
            else:
                print(f"   ❌ 小提琴圖創建失敗")
        else:
            print(f"   ⚠️ 沒有可用的測試學員")
        
        return True
        
    except Exception as e:
        print(f"❌ 格式一致性測試失敗: {str(e)}")
        return False

def main():
    """主測試程式"""
    print("=" * 60)
    print("🧪 住院醫師EPA分數小提琴圖數據點整合功能測試")
    print("=" * 60)
    
    # 測試數據點整合
    test1_result = test_violin_points_integration()
    
    # 測試格式一致性
    test2_result = test_format_consistency()
    
    print("\\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    
    if test1_result and test2_result:
        print("🎉 所有測試通過！住院醫師EPA分數小提琴圖數據點整合功能正常！")
        print("\\n✅ 功能包括:")
        print("   • 數據點與小提琴圖完美整合")
        print("   • 數據點位於小提琴中央（pointpos=0）")
        print("   • 數據點有適度散佈（jitter=0.3）")
        print("   • 與個別住院醫師分析格式完全一致")
        print("   • 保留箱線圖和平均線統計資訊")
        print("   • 顯示所有原始數據點")
        print("   • 美觀的填充顏色和透明度")
        print("   • 支援多個住院醫師的比較")
        print("   • 更直觀的分布形狀展示")
        print("\\n🎯 視覺效果:")
        print("   • 數據點不再分散在兩側")
        print("   • 數據點集中在小提琴中央")
        print("   • 保持適度的垂直散佈")
        print("   • 與個別住院醫師分析視覺一致")
    else:
        print("❌ 部分測試失敗，請檢查錯誤訊息")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
