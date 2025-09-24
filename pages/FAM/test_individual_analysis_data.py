#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試個別住院醫師評核分析使用的資料大表
"""

import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_individual_analysis_data():
    """測試個別住院醫師評核分析使用的資料大表"""
    try:
        from pages.FAM.fam_data_processor import FAMDataProcessor
        
        print("🚀 開始展示個別住院醫師評核分析使用的資料大表...")
        
        # 讀取原始EPA匯出檔案
        original_csv_path = os.path.join(os.path.dirname(__file__), 'EPA匯出原始檔_1140923.csv')
        
        if os.path.exists(original_csv_path):
            print(f"✅ 找到原始EPA匯出檔案")
            df_original = pd.read_csv(original_csv_path, encoding='utf-8')
            print(f"📊 原始檔案形狀: {df_original.shape}")
            
            # 初始化處理器
            processor = FAMDataProcessor()
            
            # 清理資料
            cleaned_df = processor.clean_data(df_original, debug=True)
            print(f"\n✅ 資料清理完成: {cleaned_df.shape}")
            
            # 顯示所有學員清單
            if '學員' in cleaned_df.columns:
                students = cleaned_df['學員'].unique()
                students = [s for s in students if s and s != '學員']  # 過濾空值和標題行
                print(f"\n👥 可分析的學員清單 ({len(students)}位):")
                for i, student in enumerate(students, 1):
                    student_count = len(cleaned_df[cleaned_df['學員'] == student])
                    print(f"  {i:2d}. {student} ({student_count} 筆記錄)")
            
            # 選擇鄧祖嶸作為示例
            selected_student = '鄧祖嶸'
            student_data = cleaned_df[cleaned_df['學員'] == selected_student].copy()
            
            print(f"\n🎯 個別住院醫師評核分析資料大表 - {selected_student}")
            print("=" * 80)
            
            if not student_data.empty:
                # 轉換日期格式
                if '日期' in student_data.columns:
                    student_data['日期'] = pd.to_datetime(student_data['日期'], errors='coerce')
                
                print(f"📊 基本統計資訊:")
                print(f"  • 總記錄數: {len(student_data)}")
                print(f"  • 資料欄位數: {len(student_data.columns)}")
                print(f"  • 時間範圍: {student_data['日期'].min()} ~ {student_data['日期'].max()}")
                
                # 顯示所有欄位
                print(f"\n📋 資料表欄位清單:")
                for i, col in enumerate(student_data.columns, 1):
                    non_null_count = student_data[col].notna().sum()
                    print(f"  {i:2d}. {col} ({non_null_count}/{len(student_data)} 筆有資料)")
                
                # 顯示完整資料大表
                print(f"\n📊 完整資料大表內容:")
                print("=" * 120)
                
                # 選擇要顯示的欄位
                display_columns = [
                    '日期', 'EPA項目', '病歷號碼', '個案姓名', '診斷', 
                    '複雜程度', '觀察場域', '信賴程度(教師評量)', '信賴程度(教師評量)_數值'
                ]
                
                # 確保所有欄位都存在
                available_columns = [col for col in display_columns if col in student_data.columns]
                missing_columns = [col for col in display_columns if col not in student_data.columns]
                
                if missing_columns:
                    print(f"⚠️ 缺少的欄位: {missing_columns}")
                
                if available_columns:
                    # 顯示資料表
                    display_data = student_data[available_columns].copy()
                    
                    # 格式化顯示
                    for idx, (_, row) in enumerate(display_data.iterrows(), 1):
                        print(f"\n📝 記錄 {idx:2d}:")
                        for col in available_columns:
                            value = row[col]
                            if pd.isna(value):
                                value_str = "N/A"
                            elif isinstance(value, str) and len(value) > 50:
                                value_str = f"{value[:47]}..."
                            else:
                                value_str = str(value)
                            
                            # 特殊處理某些欄位
                            if col == '診斷' and isinstance(value, str):
                                # 診斷欄位可能很長，分行顯示
                                if len(value) > 80:
                                    lines = [value[i:i+80] for i in range(0, len(value), 80)]
                                    value_str = "\n      " + "\n      ".join(lines)
                                else:
                                    value_str = value
                            
                            print(f"  {col:20s}: {value_str}")
                        
                        print("-" * 80)
                
                # 顯示EPA項目分析
                print(f"\n📈 EPA項目分析:")
                if 'EPA項目' in student_data.columns:
                    epa_counts = student_data['EPA項目'].value_counts()
                    print(f"  EPA項目分佈:")
                    for epa, count in epa_counts.items():
                        if epa and epa != '':
                            print(f"    ✅ {epa}: {count} 筆")
                        else:
                            print(f"    📝 空EPA項目: {count} 筆")
                
                # 顯示信賴程度分析
                print(f"\n📊 信賴程度分析:")
                if '信賴程度(教師評量)' in student_data.columns:
                    reliability_counts = student_data['信賴程度(教師評量)'].value_counts()
                    print(f"  信賴程度分佈:")
                    for level, count in reliability_counts.items():
                        if pd.notna(level) and str(level).strip():
                            print(f"    • {level}: {count} 筆")
                
                # 顯示數值化信賴程度分析
                if '信賴程度(教師評量)_數值' in student_data.columns:
                    numeric_reliability = student_data['信賴程度(教師評量)_數值'].dropna()
                    if not numeric_reliability.empty:
                        print(f"  數值化信賴程度統計:")
                        print(f"    • 平均分數: {numeric_reliability.mean():.2f}")
                        print(f"    • 最高分數: {numeric_reliability.max():.2f}")
                        print(f"    • 最低分數: {numeric_reliability.min():.2f}")
                        print(f"    • 標準差: {numeric_reliability.std():.2f}")
                
                # 顯示時間趨勢分析
                print(f"\n📅 時間趨勢分析:")
                if '日期' in student_data.columns:
                    valid_dates = student_data.dropna(subset=['日期'])
                    if not valid_dates.empty:
                        monthly_counts = valid_dates.groupby(valid_dates['日期'].dt.to_period('M')).size()
                        print(f"  月度記錄分佈:")
                        for period, count in monthly_counts.items():
                            print(f"    • {period}: {count} 筆記錄")
                
                # 顯示診斷分析
                print(f"\n🏥 診斷分析:")
                if '診斷' in student_data.columns:
                    valid_diagnosis = student_data.dropna(subset=['診斷'])
                    if not valid_diagnosis.empty:
                        print(f"  有診斷記錄: {len(valid_diagnosis)} 筆")
                        
                        # 顯示前5個診斷
                        print(f"  診斷示例:")
                        for idx, (_, row) in enumerate(valid_diagnosis.head(5).iterrows(), 1):
                            diagnosis = row['診斷']
                            if isinstance(diagnosis, str) and len(diagnosis) > 100:
                                diagnosis = diagnosis[:97] + "..."
                            print(f"    {idx}. {diagnosis}")
            
            print(f"\n🎉 個別住院醫師評核分析資料大表展示完成！")
            return True
        else:
            print(f"❌ 找不到原始EPA匯出檔案")
            return False
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 80)
    result = test_individual_analysis_data()
    print("=" * 80)
    
    if result:
        print("🎉 個別住院醫師評核分析資料大表展示成功！")
        print("\n💡 資料大表說明:")
        print("- 包含所有原始記錄和處理後的資料")
        print("- 顯示完整的EPA項目、診斷、信賴程度等資訊")
        print("- 提供詳細的統計分析和趨勢分析")
        print("- 支援個別住院醫師的完整評核分析")
    else:
        print("❌ 個別住院醫師評核分析資料大表展示失敗！")
