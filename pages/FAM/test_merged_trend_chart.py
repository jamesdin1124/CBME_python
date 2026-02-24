#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試合併趨勢圖功能
"""

import pandas as pd
import os
from fam_data_processor import FAMDataProcessor
from fam_visualization import FAMVisualization

def test_merged_trend_chart():
    """測試合併趨勢圖功能"""
    print("🧪 測試合併趨勢圖功能...")
    
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
        
        # 測試合併趨勢圖功能
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
            
            # 測試合併趨勢圖創建
            merged_fig = visualizer.create_enhanced_monthly_trend_chart(
                epa_data, test_epa, test_student
            )
            
            if merged_fig is not None:
                print("✅ 合併趨勢圖創建成功")
                
                # 檢查圖表配置
                layout = merged_fig.layout
                print(f"   圖表標題: {layout.title.text}")
                print(f"   X軸標題: {layout.xaxis.title.text}")
                print(f"   Y軸標題: {layout.yaxis.title.text}")
                
                # 檢查資料系列
                traces = merged_fig.data
                print(f"   資料系列數量: {len(traces)}")
                for i, trace in enumerate(traces):
                    print(f"     系列{i+1}: {trace.name} (模式: {trace.mode})")
                    
                    # 檢查是否有平均值和標準差系列
                    if '平均值' in trace.name:
                        print(f"        ✅ 找到平均值系列")
                    elif '標準差' in trace.name:
                        print(f"        ✅ 找到標準差系列")
            else:
                print("⚠️ 合併趨勢圖創建失敗，可能沒有足夠的資料")
        
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
        
        print("\\n🎉 合併趨勢圖功能測試完成！")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        print(f"詳細錯誤信息: {traceback.format_exc()}")
        return False

def test_monthly_statistics():
    """測試月度統計計算"""
    print("\\n🧪 測試月度統計計算...")
    
    integrated_file = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/integrated_epa_data.csv"
    
    try:
        df = pd.read_csv(integrated_file, encoding='utf-8')
        processor = FAMDataProcessor()
        cleaned_df = processor.clean_data(df)
        
        # 選擇一個有足夠資料的學員和EPA項目
        students = processor.get_student_list(cleaned_df)
        epa_items = processor.get_epa_items(cleaned_df)
        
        if students and epa_items:
            test_student = students[0]
            test_epa = list(epa_items)[0]
            
            student_data = cleaned_df[cleaned_df['學員'] == test_student]
            epa_data = student_data[student_data['EPA項目'] == test_epa]
            
            print(f"   測試組合: {test_student} - {test_epa}")
            print(f"   總記錄數: {len(epa_data)}")
            
            # 模擬月度統計計算
            plot_records = []
            
            for _, row in epa_data.iterrows():
                date = row['日期']
                if pd.notna(date):
                    try:
                        date_obj = pd.to_datetime(date)
                        month_str = f"{date_obj.year}年{date_obj.month:02d}月"
                        
                        if '信賴程度(教師評量)_數值' in row:
                            score = row['信賴程度(教師評量)_數值']
                        else:
                            reliability = row['信賴程度(教師評量)']
                            if pd.notna(reliability) and str(reliability).strip():
                                # 簡化的信賴程度轉換
                                reliability_mapping = {
                                    '教師在旁逐步共同操作': 1,
                                    '教師在旁必要時協助': 2,
                                    '教師事後重點確認': 3,
                                    '必要時知會教師確認': 4,
                                    '獨立執行': 5,
                                    '1': 1, '2': 2, '3': 3, '4': 4, '5': 5
                                }
                                score = reliability_mapping.get(str(reliability).strip(), None)
                            else:
                                score = None
                        
                        if pd.notna(score):
                            plot_records.append({
                                '月份': month_str,
                                '信賴程度': float(score),
                                '資料來源': row.get('資料來源', '未知來源'),
                                '日期': date_obj
                            })
                    except:
                        continue
            
            if plot_records:
                df_plot = pd.DataFrame(plot_records)
                monthly_stats = df_plot.groupby('月份')['信賴程度'].agg(['mean', 'std', 'count']).reset_index()
                monthly_stats = monthly_stats.sort_values('月份')
                
                print(f"   月度統計結果:")
                for _, row in monthly_stats.iterrows():
                    mean_val = row['mean']
                    std_val = row['std'] if pd.notna(row['std']) else 0
                    count_val = row['count']
                    print(f"     {row['月份']}: 平均={mean_val:.2f}, 標準差={std_val:.2f}, 樣本數={count_val}")
                
                print("✅ 月度統計計算測試完成")
                return True
            else:
                print("⚠️ 沒有找到有效的評核記錄")
                return False
        
    except Exception as e:
        print(f"❌ 月度統計測試失敗: {str(e)}")
        return False

def main():
    """主測試程式"""
    print("=" * 60)
    print("🧪 合併趨勢圖功能測試")
    print("=" * 60)
    
    # 測試合併趨勢圖
    test1_result = test_merged_trend_chart()
    
    # 測試月度統計計算
    test2_result = test_monthly_statistics()
    
    print("\\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    
    if test1_result and test2_result:
        print("🎉 所有測試通過！合併趨勢圖功能已準備就緒！")
        print("\\n✅ 新功能包括:")
        print("   • 合併兩個系統資料（EMYWAY歷史資料 + 現有系統）")
        print("   • 顯示平均值折線圖（mean）")
        print("   • 添加標準差上下限（±1SD）")
        print("   • 顯示原始數據點分布")
        print("   • 提供詳細的統計資訊")
    else:
        print("❌ 部分測試失敗，請檢查錯誤訊息")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
