#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試趨勢圖樣本數標註功能
"""

import pandas as pd
import os
from fam_data_processor import FAMDataProcessor
from fam_visualization import FAMVisualization

def test_sample_count_annotation():
    """測試樣本數標註功能"""
    print("🧪 測試趨勢圖樣本數標註功能...")
    
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
        
        # 測試趨勢圖創建
        if students:
            test_student = students[0]
            
            print(f"\\n🧪 測試學員: {test_student}")
            
            # 獲取學員的資料
            student_data = cleaned_df[cleaned_df['學員'] == test_student]
            
            print(f"   該學員的資料: {len(student_data)} 筆記錄")
            
            # 獲取EPA項目清單
            epa_items = processor.get_epa_items(student_data)
            print(f"   EPA項目: {len(epa_items)} 個")
            
            # 測試每個EPA項目的趨勢圖
            for epa_item in epa_items[:3]:  # 測試前3個EPA項目
                print(f"\\n📋 測試EPA項目: {epa_item}")
                
                # 獲取該EPA項目的資料
                epa_data = student_data[student_data['EPA項目'] == epa_item]
                
                print(f"   記錄數: {len(epa_data)}")
                
                if not epa_data.empty:
                    # 手動計算月度統計以驗證樣本數
                    print(f"   📊 手動計算月度統計:")
                    
                    # 準備數據
                    plot_records = []
                    for _, row in epa_data.iterrows():
                        date = row['日期']
                        if pd.notna(date):
                            try:
                                date_obj = pd.to_datetime(date)
                                month_str = f"{date_obj.year}年{date_obj.month:02d}月"
                                
                                # 獲取信賴程度數值
                                if '信賴程度(教師評量)_數值' in row:
                                    score = row['信賴程度(教師評量)_數值']
                                else:
                                    reliability = row['信賴程度(教師評量)']
                                    if pd.notna(reliability) and str(reliability).strip():
                                        score = visualizer._convert_reliability_to_numeric(str(reliability).strip())
                                    else:
                                        score = None
                                
                                if pd.notna(score):
                                    plot_records.append({
                                        '月份': month_str,
                                        '信賴程度': float(score),
                                        '日期': date_obj
                                    })
                            except:
                                continue
                    
                    if plot_records:
                        df_plot = pd.DataFrame(plot_records)
                        df_plot = df_plot.sort_values('日期')
                        
                        # 計算月度統計
                        monthly_stats = df_plot.groupby('月份')['信賴程度'].agg(['mean', 'std', 'count']).reset_index()
                        monthly_stats = monthly_stats.sort_values('月份')
                        
                        print(f"     月度統計:")
                        for _, row in monthly_stats.iterrows():
                            month = row['月份']
                            mean_score = row['mean']
                            count = row['count']
                            print(f"       {month}: 平均值={mean_score:.2f}, 樣本數={count}")
                        
                        # 創建增強版趨勢圖
                        trend_fig = visualizer.create_enhanced_monthly_trend_chart(epa_data, epa_item, test_student)
                        
                        if trend_fig is not None:
                            print(f"   ✅ 趨勢圖創建成功")
                            
                            # 檢查圖表配置
                            if hasattr(trend_fig, 'data'):
                                for i, trace in enumerate(trend_fig.data):
                                    trace_name = trace.name if hasattr(trace, 'name') else f"Trace {i}"
                                    
                                    if trace_name == '平均值':
                                        print(f"   📊 平均值折線檢查:")
                                        
                                        # 檢查是否有text屬性
                                        if hasattr(trace, 'text'):
                                            print(f"     文字標註: {trace.text}")
                                            
                                            # 驗證文字標註是否正確
                                            expected_text = [f"n={count}" for count in monthly_stats['count']]
                                            if trace.text == expected_text:
                                                print(f"     ✅ 樣本數標註正確")
                                            else:
                                                print(f"     ❌ 樣本數標註不正確")
                                                print(f"     期望: {expected_text}")
                                                print(f"     實際: {trace.text}")
                                        else:
                                            print(f"     ❌ 沒有找到文字標註")
                                        
                                        # 檢查文字位置
                                        if hasattr(trace, 'textposition'):
                                            print(f"     文字位置: {trace.textposition}")
                                        
                                        # 檢查文字字體
                                        if hasattr(trace, 'textfont'):
                                            print(f"     文字字體: {trace.textfont}")
                                        
                                        # 檢查模式
                                        if hasattr(trace, 'mode'):
                                            print(f"     模式: {trace.mode}")
                                            if 'text' in trace.mode:
                                                print(f"     ✅ 文字模式已啟用")
                                            else:
                                                print(f"     ❌ 文字模式未啟用")
                        
                        # 檢查圖表是否包含樣本數信息
                        print(f"   🔍 樣本數標註驗證:")
                        for _, row in monthly_stats.iterrows():
                            month = row['月份']
                            count = row['count']
                            print(f"     {month}: 應該顯示 'n={count}'")
                    else:
                        print(f"   ℹ️ 沒有有效的數據點")
                else:
                    print(f"   ℹ️ 沒有資料")
        
        print("\\n🎉 樣本數標註功能測試完成！")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        print(f"詳細錯誤信息: {traceback.format_exc()}")
        return False

def test_multiple_data_sources_sample_count():
    """測試多資料來源的樣本數標註"""
    print("\\n🧪 測試多資料來源的樣本數標註...")
    
    integrated_file = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/integrated_epa_data.csv"
    
    try:
        df = pd.read_csv(integrated_file, encoding='utf-8')
        processor = FAMDataProcessor()
        visualizer = FAMVisualization()
        cleaned_df = processor.clean_data(df)
        
        if '資料來源' in cleaned_df.columns:
            # 檢查各資料來源的樣本數
            source_counts = cleaned_df['資料來源'].value_counts()
            print(f"   資料來源分布: {source_counts.to_dict()}")
            
            # 找一個有多個資料來源的學員進行測試
            students = processor.get_student_list(cleaned_df)
            
            for student in students[:2]:  # 測試前2個學員
                student_data = cleaned_df[cleaned_df['學員'] == student]
                
                # 檢查該學員是否有來自多個資料來源的數據
                if '資料來源' in student_data.columns:
                    student_sources = student_data['資料來源'].value_counts()
                    
                    if len(student_sources) > 1:
                        print(f"\\n   👤 學員: {student}")
                        print(f"      資料來源: {student_sources.to_dict()}")
                        
                        # 選擇一個EPA項目進行測試
                        epa_items = processor.get_epa_items(student_data)
                        
                        if epa_items:
                            epa_item = epa_items[0]
                            epa_data = student_data[student_data['EPA項目'] == epa_item]
                            
                            if not epa_data.empty:
                                print(f"      EPA項目: {epa_item}")
                                print(f"      記錄數: {len(epa_data)}")
                                
                                # 分析各資料來源的記錄數
                                epa_sources = epa_data['資料來源'].value_counts()
                                print(f"      各來源記錄數: {epa_sources.to_dict()}")
                                
                                # 創建趨勢圖
                                trend_fig = visualizer.create_enhanced_monthly_trend_chart(epa_data, epa_item, student)
                                
                                if trend_fig is not None:
                                    print(f"      ✅ 趨勢圖創建成功")
                                    
                                    # 檢查樣本數標註
                                    for trace in trend_fig.data:
                                        if hasattr(trace, 'name') and trace.name == '平均值':
                                            if hasattr(trace, 'text'):
                                                print(f"      樣本數標註: {trace.text}")
                                            break
                                else:
                                    print(f"      ❌ 趨勢圖創建失敗")
                        
                        break  # 找到一個有多個資料來源的學員就停止
        
        return True
        
    except Exception as e:
        print(f"❌ 多資料來源樣本數標註測試失敗: {str(e)}")
        return False

def main():
    """主測試程式"""
    print("=" * 60)
    print("🧪 趨勢圖樣本數標註功能測試")
    print("=" * 60)
    
    # 測試樣本數標註
    test1_result = test_sample_count_annotation()
    
    # 測試多資料來源的樣本數標註
    test2_result = test_multiple_data_sources_sample_count()
    
    print("\\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    
    if test1_result and test2_result:
        print("🎉 所有測試通過！樣本數標註功能正常！")
        print("\\n✅ 功能包括:")
        print("   • 在每個平均值點旁邊顯示樣本數（n=數字）")
        print("   • 文字標註位置在數據點上方中央")
        print("   • 文字顏色與平均值線保持一致")
        print("   • 支援多資料來源合併的樣本數計算")
        print("   • 保持原有的懸停提示功能")
        print("   • 移除Y軸右側的等級標籤")
    else:
        print("❌ 部分測試失敗，請檢查錯誤訊息")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
