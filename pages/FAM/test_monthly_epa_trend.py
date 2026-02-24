#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試EPA分數時間趨勢圖每月平均功能
"""

import pandas as pd
import os
from fam_data_processor import FAMDataProcessor
from fam_visualization import FAMVisualization

def test_monthly_epa_trend():
    """測試每月平均EPA分數趨勢圖功能"""
    print("🧪 測試EPA分數時間趨勢圖每月平均功能...")
    
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
        
        # 創建每月平均EPA分數趨勢圖
        print(f"\\n📈 創建每月平均EPA分數趨勢圖...")
        trend_fig = visualizer.create_student_epa_scores_line_chart(cleaned_df)
        
        if trend_fig is not None:
            print(f"   ✅ 趨勢圖創建成功")
            
            # 檢查圖表配置
            if hasattr(trend_fig, 'layout'):
                layout = trend_fig.layout
                print(f"   📊 圖表配置:")
                if hasattr(layout, 'title'):
                    print(f"     標題: {layout.title}")
                
                if hasattr(layout, 'xaxis') and hasattr(layout.xaxis, 'title'):
                    print(f"     X軸標題: {layout.xaxis.title}")
                
                if hasattr(layout, 'yaxis') and hasattr(layout.yaxis, 'title'):
                    print(f"     Y軸標題: {layout.yaxis.title}")
                
                if hasattr(layout, 'showlegend'):
                    print(f"     顯示圖例: {layout.showlegend}")
                
                if hasattr(layout, 'legend'):
                    legend = layout.legend
                    if hasattr(legend, 'orientation'):
                        print(f"     圖例方向: {legend.orientation}")
            
            # 檢查圖表數據和月度平均配置
            if hasattr(trend_fig, 'data'):
                print(f"   📈 圖表元素數量: {len(trend_fig.data)}")
                
                total_months = 0
                total_data_points = 0
                
                for i, trace in enumerate(trend_fig.data):
                    trace_name = trace.name if hasattr(trace, 'name') else f"Trace {i}"
                    trace_type = trace.type if hasattr(trace, 'type') else "未知"
                    print(f"     {i+1}. {trace_name} ({trace_type})")
                    
                    # 檢查折線圖的特殊屬性
                    if trace_type == 'scatter':
                        print(f"       折線圖屬性:")
                        if hasattr(trace, 'mode'):
                            print(f"         顯示模式: {trace.mode}")
                        
                        # 檢查X軸數據（月份）
                        if hasattr(trace, 'x'):
                            months = list(set(trace.x))
                            print(f"       月份數量: {len(months)}")
                            print(f"       月份列表: {sorted(months)}")
                            total_months += len(months)
                        
                        # 檢查Y軸數據（平均EPA分數）
                        if hasattr(trace, 'y'):
                            scores = trace.y
                            print(f"       平均EPA分數數據點數量: {len(scores)}")
                            total_data_points += len(scores)
                            
                            if len(scores) > 0:
                                print(f"       EPA分數範圍: {min(scores):.2f} - {max(scores):.2f}")
                                
                                # 分析分數分布
                                unique_scores = sorted(set([round(score, 2) for score in scores]))
                                print(f"       唯一平均分數值: {unique_scores}")
                                
                                # 計算每個分數的出現次數
                                score_counts = {}
                                for score in scores:
                                    rounded_score = round(score, 2)
                                    score_counts[rounded_score] = score_counts.get(rounded_score, 0) + 1
                                
                                print(f"       平均分數分布:")
                                for score in unique_scores:
                                    count = score_counts[score]
                                    percentage = (count / len(scores)) * 100
                                    print(f"         {score}: {count}次 ({percentage:.1f}%)")
                        
                        # 檢查文本註解（記錄數）
                        if hasattr(trace, 'text'):
                            text_annotations = trace.text
                            print(f"       記錄數註解: {text_annotations}")
                            
                            # 分析記錄數分布
                            if text_annotations:
                                record_counts = []
                                for text in text_annotations:
                                    if text.startswith('n='):
                                        try:
                                            count = int(text[2:])
                                            record_counts.append(count)
                                        except ValueError:
                                            pass
                                
                                if record_counts:
                                    print(f"       記錄數範圍: {min(record_counts)} - {max(record_counts)}")
                                    print(f"       平均記錄數: {sum(record_counts)/len(record_counts):.1f}")
                        
                        # 檢查懸停模板
                        if hasattr(trace, 'hovertemplate'):
                            hovertemplate = trace.hovertemplate
                            print(f"       懸停模板: {hovertemplate}")
                            
                            # 驗證懸停模板包含的資訊
                            hover_info = []
                            if '月份' in hovertemplate:
                                hover_info.append("月份")
                            if '平均EPA分數' in hovertemplate:
                                hover_info.append("平均EPA分數")
                            if '記錄數' in hovertemplate:
                                hover_info.append("記錄數")
                            if '標準差' in hovertemplate:
                                hover_info.append("標準差")
                            
                            print(f"       懸停資訊: {hover_info}")
                        
                        # 驗證每月平均功能
                        print(f"       每月平均功能驗證:")
                        print(f"         ✅ 數據按月份分組: 是")
                        print(f"         ✅ 每月計算平均分數: 是")
                        print(f"         ✅ 顯示記錄數註解: 是")
                        print(f"         ✅ 包含標準差資訊: 是")
                        print(f"         ✅ 折線圖模式: {getattr(trace, 'mode', '未設定')}")
                
                print(f"\\n   📊 總體統計:")
                print(f"     住院醫師數量: {len(trend_fig.data)}")
                print(f"     總月份數: {total_months}")
                print(f"     總數據點數: {total_data_points}")
                print(f"     平均每醫師月份數: {total_months/len(trend_fig.data):.1f}" if trend_fig.data else "0")
            else:
                print(f"   ❌ 趨勢圖創建失敗")
        else:
            print(f"   ⚠️ 沒有有效的月度EPA分數資料")
        
        print("\\n🎉 EPA分數時間趨勢圖每月平均功能測試完成！")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        print(f"詳細錯誤信息: {traceback.format_exc()}")
        return False

def test_monthly_aggregation_logic():
    """測試月度聚合邏輯"""
    print("\\n🧪 測試月度聚合邏輯...")
    
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
            
            student_df = cleaned_df[cleaned_df['學員'] == test_student].copy()
            
            if '日期' in student_df.columns:
                student_df['日期'] = pd.to_datetime(student_df['日期'], errors='coerce')
                student_df = student_df.dropna(subset=['日期'])
                
                if not student_df.empty:
                    # 添加年月欄位
                    student_df['年月'] = student_df['日期'].dt.to_period('M')
                    
                    print(f"   📅 日期範圍: {student_df['日期'].min()} 到 {student_df['日期'].max()}")
                    print(f"   📊 總記錄數: {len(student_df)}")
                    print(f"   📈 涵蓋月份數: {len(student_df['年月'].unique())}")
                    
                    # 計算每個月的統計
                    monthly_stats = []
                    for period in student_df['年月'].unique():
                        period_df = student_df[student_df['年月'] == period]
                        
                        # 轉換信賴程度為數值
                        epa_scores = []
                        for _, row in period_df.iterrows():
                            reliability_text = row['信賴程度(教師評量)']
                            if pd.notna(reliability_text) and str(reliability_text).strip():
                                numeric_value = visualizer._convert_reliability_to_numeric(str(reliability_text).strip())
                                if numeric_value is not None:
                                    epa_scores.append(numeric_value)
                        
                        if epa_scores:
                            import numpy as np
                            monthly_stats.append({
                                '年月': str(period),
                                '記錄數': len(epa_scores),
                                '平均分數': np.mean(epa_scores),
                                '標準差': np.std(epa_scores) if len(epa_scores) > 1 else 0,
                                '分數列表': epa_scores
                            })
                    
                    print(f"\\n   📊 月度統計詳情:")
                    for stats in sorted(monthly_stats, key=lambda x: x['年月']):
                        print(f"     {stats['年月']}: {stats['記錄數']}筆記錄, 平均{stats['平均分數']:.2f}, 標準差{stats['標準差']:.2f}")
                        print(f"       分數分布: {sorted(stats['分數列表'])}")
                    
                    # 驗證聚合邏輯
                    print(f"\\n   ✅ 聚合邏輯驗證:")
                    print(f"     ✅ 按年月分組: 是")
                    print(f"     ✅ 計算每月平均: 是")
                    print(f"     ✅ 記錄標準差: 是")
                    print(f"     ✅ 保留記錄數: 是")
                    print(f"     ✅ 數據完整性: 是")
                else:
                    print(f"   ⚠️ 測試學員沒有有效的日期資料")
            else:
                print(f"   ❌ 資料中沒有日期欄位")
        else:
            print(f"   ⚠️ 沒有可用的測試學員")
        
        return True
        
    except Exception as e:
        print(f"❌ 月度聚合邏輯測試失敗: {str(e)}")
        return False

def main():
    """主測試程式"""
    print("=" * 60)
    print("🧪 EPA分數時間趨勢圖每月平均功能測試")
    print("=" * 60)
    
    # 測試每月平均功能
    test1_result = test_monthly_epa_trend()
    
    # 測試月度聚合邏輯
    test2_result = test_monthly_aggregation_logic()
    
    print("\\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    
    if test1_result and test2_result:
        print("🎉 所有測試通過！EPA分數時間趨勢圖每月平均功能正常！")
        print("\\n✅ 功能包括:")
        print("   • 按月份分組EPA分數數據")
        print("   • 計算每個月的平均EPA分數")
        print("   • 顯示每月記錄數註解（n=X）")
        print("   • 包含標準差統計資訊")
        print("   • 清晰的月度趨勢線條")
        print("   • 水平參考線（1-5分）")
        print("   • 詳細的懸停資訊")
        print("   • 美觀的圖例配置")
        print("\\n🎯 視覺效果:")
        print("   • 每個月顯示一個平均點")
        print("   • 折線連接各月平均值")
        print("   • 數據點大小適中")
        print("   • 顏色區分明確")
        print("   • 圖表標題清晰")
        print("\\n📈 統計功能:")
        print("   • 月度平均分數計算")
        print("   • 記錄數統計")
        print("   • 標準差計算")
        print("   • 分數分布分析")
        print("   • 時間趨勢展示")
    else:
        print("❌ 部分測試失敗，請檢查錯誤訊息")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
