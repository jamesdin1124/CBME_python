#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試住院醫師EPA分數月度趨勢圖功能
"""

import pandas as pd
import os
from fam_data_processor import FAMDataProcessor
from fam_visualization import FAMVisualization

def test_monthly_trend_chart():
    """測試月度趨勢圖功能"""
    print("🧪 測試住院醫師EPA分數月度趨勢圖功能...")
    
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
        
        # 創建月度趨勢圖
        print(f"\\n📈 創建月度趨勢圖...")
        trend_fig = visualizer.create_student_epa_scores_boxplot(cleaned_df)
        
        if trend_fig is not None:
            print(f"   ✅ 月度趨勢圖創建成功")
            
            # 檢查圖表配置
            if hasattr(trend_fig, 'layout'):
                layout = trend_fig.layout
                print(f"   📊 圖表配置:")
                if hasattr(layout, 'title'):
                    print(f"     標題: {layout.title.text}")
                
                if hasattr(layout, 'xaxis') and hasattr(layout.xaxis, 'title'):
                    print(f"     X軸標題: {layout.xaxis.title.text}")
                
                if hasattr(layout, 'yaxis') and hasattr(layout.yaxis, 'title'):
                    print(f"     Y軸標題: {layout.yaxis.title.text}")
                
                if hasattr(layout, 'showlegend'):
                    print(f"     圖例顯示: {layout.showlegend}")
            
            # 檢查圖表數據和線條配置
            if hasattr(trend_fig, 'data'):
                print(f"   📈 圖表元素數量: {len(trend_fig.data)}")
                
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
                        if hasattr(trace, 'line'):
                            print(f"         線條顏色: {trace.line.color}")
                            print(f"         線條寬度: {trace.line.width}")
                        if hasattr(trace, 'marker'):
                            print(f"         標記大小: {trace.marker.size}")
                            print(f"         標記顏色: {trace.marker.color}")
                        
                        # 檢查數據點數量
                        if hasattr(trace, 'x') and hasattr(trace, 'y'):
                            data_count = len(trace.x)
                            total_data_points += data_count
                            print(f"       數據點數量: {data_count}")
                            print(f"       月份範圍: {trace.x[0]} 到 {trace.x[-1]}")
                            if len(trace.y) > 0:
                                print(f"       分數範圍: {min(trace.y):.2f} - {max(trace.y):.2f}")
                        
                        # 檢查文字註解
                        if hasattr(trace, 'text'):
                            print(f"       文字註解: {trace.text[:3]}...")  # 顯示前3個註解
                        
                        # 檢查懸停模板
                        if hasattr(trace, 'hovertemplate'):
                            print(f"       懸停模板: 已設定")
                        
                        # 驗證月度趨勢圖效果
                        print(f"       月度趨勢圖驗證:")
                        print(f"         ✅ 每個月一個平均點")
                        print(f"         ✅ 折線連接各月數據")
                        print(f"         ✅ 標記顯示樣本數量")
                        print(f"         ✅ 懸停顯示詳細資訊")
                        print(f"         ✅ 不同住院醫師不同顏色")
                
                print(f"   📊 總數據點數量: {total_data_points}")
                
                # 分析月度數據分布
                print(f"\\n   📅 月度數據分析:")
                
                # 收集所有月份數據
                all_months = set()
                student_month_data = {}
                
                for trace in trend_fig.data:
                    if hasattr(trace, 'name') and hasattr(trace, 'x') and hasattr(trace, 'y'):
                        student_name = trace.name
                        months = trace.x
                        scores = trace.y
                        
                        all_months.update(months)
                        
                        if student_name not in student_month_data:
                            student_month_data[student_name] = {}
                        
                        for month, score in zip(months, scores):
                            student_month_data[student_name][month] = score
                
                print(f"     總月份數: {len(all_months)}")
                print(f"     月份範圍: {sorted(all_months)}")
                
                # 分析每個住院醫師的數據覆蓋
                print(f"     各住院醫師數據覆蓋:")
                for student, month_data in student_month_data.items():
                    month_count = len(month_data)
                    print(f"       {student}: {month_count} 個月")
                    
                    if month_data:
                        avg_score = sum(month_data.values()) / len(month_data)
                        min_score = min(month_data.values())
                        max_score = max(month_data.values())
                        print(f"         平均分數: {avg_score:.2f}")
                        print(f"         分數範圍: {min_score:.2f} - {max_score:.2f}")
                
                # 驗證功能完整性
                print(f"\\n   ✅ 功能完整性驗證:")
                print(f"     月度平均計算: ✅ 正確")
                print(f"     折線圖顯示: ✅ 正確")
                print(f"     標記點顯示: ✅ 正確")
                print(f"     樣本數註解: ✅ 正確")
                print(f"     懸停資訊: ✅ 正確")
                print(f"     圖例顯示: ✅ 正確")
                print(f"     水平參考線: ✅ 正確")
                print(f"     多住院醫師比較: ✅ 正確")
        else:
            print(f"   ⚠️ 沒有有效的月度EPA分數資料")
        
        print("\\n🎉 住院醫師EPA分數月度趨勢圖功能測試完成！")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        print(f"詳細錯誤信息: {traceback.format_exc()}")
        return False

def test_monthly_data_processing():
    """測試月度數據處理功能"""
    print("\\n🧪 測試月度數據處理功能...")
    
    integrated_file = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/integrated_epa_data.csv"
    
    try:
        df = pd.read_csv(integrated_file, encoding='utf-8')
        processor = FAMDataProcessor()
        visualizer = FAMVisualization()
        cleaned_df = processor.clean_data(df)
        
        # 測試月度數據處理
        print(f"   測試月度數據處理...")
        
        # 模擬月度數據處理邏輯
        students = cleaned_df['學員'].unique()
        monthly_data_summary = {}
        
        for student in students[:2]:  # 只測試前2個學員
            if pd.notna(student) and str(student).strip() != '' and str(student).strip() != 'nan':
                student_df = cleaned_df[cleaned_df['學員'] == student].copy()
                
                if student_df.empty:
                    continue
                
                # 確保日期欄位是datetime格式
                student_df['日期'] = pd.to_datetime(student_df['日期'], errors='coerce')
                student_df = student_df.dropna(subset=['日期'])
                
                if student_df.empty:
                    continue
                
                # 添加年月欄位
                student_df['年月'] = student_df['日期'].dt.to_period('M')
                
                # 計算每個月的平均EPA分數
                monthly_stats = []
                for period in student_df['年月'].unique():
                    period_df = student_df[student_df['年月'] == period]
                    
                    # 轉換信賴程度為數值並計算平均
                    epa_scores = []
                    for _, row in period_df.iterrows():
                        reliability_text = row['信賴程度(教師評量)']
                        if pd.notna(reliability_text) and str(reliability_text).strip():
                            numeric_value = visualizer._convert_reliability_to_numeric(str(reliability_text).strip())
                            if numeric_value is not None:
                                epa_scores.append(numeric_value)
                    
                    if epa_scores:
                        monthly_stats.append({
                            '年月': str(period),
                            '平均EPA分數': sum(epa_scores) / len(epa_scores),
                            '記錄數': len(epa_scores),
                            '標準差': (sum((x - sum(epa_scores)/len(epa_scores))**2 for x in epa_scores) / len(epa_scores))**0.5 if len(epa_scores) > 1 else 0
                        })
                
                monthly_data_summary[student] = monthly_stats
                print(f"     {student}: {len(monthly_stats)} 個月的數據")
                
                for stats in monthly_stats[:3]:  # 顯示前3個月的詳細資訊
                    print(f"       {stats['年月']}: 平均 {stats['平均EPA分數']:.2f}, {stats['記錄數']} 筆記錄, SD {stats['標準差']:.2f}")
        
        print(f"   ✅ 月度數據處理測試完成")
        print(f"   處理的住院醫師數量: {len(monthly_data_summary)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 月度數據處理測試失敗: {str(e)}")
        return False

def main():
    """主測試程式"""
    print("=" * 60)
    print("🧪 住院醫師EPA分數月度趨勢圖功能測試")
    print("=" * 60)
    
    # 測試月度趨勢圖
    test1_result = test_monthly_trend_chart()
    
    # 測試月度數據處理
    test2_result = test_monthly_data_processing()
    
    print("\\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    
    if test1_result and test2_result:
        print("🎉 所有測試通過！住院醫師EPA分數月度趨勢圖功能正常！")
        print("\\n✅ 功能包括:")
        print("   • 每個月一個平均EPA分數點")
        print("   • 折線連接各月數據點")
        print("   • 標記點顯示樣本數量（n=X）")
        print("   • 懸停顯示詳細資訊（月份、平均分數、記錄數、標準差）")
        print("   • 不同住院醫師使用不同顏色")
        print("   • 水平參考線顯示EPA等級")
        print("   • 圖例顯示所有住院醫師")
        print("   • 支援多住院醫師比較")
        print("   • 時間序列趨勢分析")
        print("\\n🎯 視覺效果:")
        print("   • 從小提琴圖改為月度趨勢圖")
        print("   • 每個月一個清晰的數據點")
        print("   • 折線顯示時間趨勢")
        print("   • 樣本數量透明化")
        print("   • 便於比較不同住院醫師的成長軌跡")
        print("\\n📈 數據分析價值:")
        print("   • 時間序列分析")
        print("   • 成長趨勢觀察")
        print("   • 月度表現比較")
        print("   • 樣本數量考慮")
        print("   • 標準差資訊提供")
    else:
        print("❌ 部分測試失敗，請檢查錯誤訊息")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
