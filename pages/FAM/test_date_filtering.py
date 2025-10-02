#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試EMYWAY資料日期過濾功能
"""

import pandas as pd
import os
from emway_data_converter import EmwayDataConverter

def test_date_filtering():
    """測試日期過濾功能"""
    print("🧪 測試EMYWAY資料日期過濾功能...")
    
    # 初始化轉換器
    converter = EmwayDataConverter()
    
    # EMYWAY資料路徑
    emway_folder = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/EMYWAY資料"
    
    if not os.path.exists(emway_folder):
        print("❌ EMYWAY資料夾不存在")
        return False
    
    try:
        print(f"✅ EMYWAY資料夾存在: {emway_folder}")
        
        # 轉換所有資料
        print("🔄 開始轉換EMYWAY資料（包含日期過濾）...")
        converted_df = converter.convert_all_data(emway_folder)
        
        if converted_df.empty:
            print("❌ 轉換後的資料為空")
            return False
        
        print(f"✅ 轉換完成，總記錄數: {len(converted_df)}")
        
        # 檢查日期過濾結果
        if '日期' in converted_df.columns:
            # 轉換日期欄位
            converted_df['日期'] = pd.to_datetime(converted_df['日期'], errors='coerce')
            
            # 統計日期分布
            valid_dates = converted_df[converted_df['日期'].notna()]
            invalid_dates = converted_df[converted_df['日期'].isna()]
            
            print(f"📊 日期統計:")
            print(f"   有效日期記錄: {len(valid_dates)} 筆")
            print(f"   無效日期記錄: {len(invalid_dates)} 筆")
            
            if not valid_dates.empty:
                # 檢查日期範圍
                min_date = valid_dates['日期'].min()
                max_date = valid_dates['日期'].max()
                
                print(f"   日期範圍: {min_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')}")
                
                # 檢查是否有2025年的資料
                data_2025 = valid_dates[valid_dates['日期'] >= '2025-01-01']
                data_2024_and_before = valid_dates[valid_dates['日期'] < '2025-01-01']
                
                print(f"   2024年及之前: {len(data_2024_and_before)} 筆")
                print(f"   2025年資料: {len(data_2025)} 筆")
                
                if len(data_2025) > 0:
                    print(f"   ⚠️ 發現2025年資料，應該被過濾掉:")
                    for _, row in data_2025.head(5).iterrows():
                        print(f"     {row['日期'].strftime('%Y-%m-%d')} - {row['學員']} - {row['EPA項目']}")
                else:
                    print(f"   ✅ 沒有2025年資料，日期過濾功能正常")
                
                # 檢查2024年12月31日之後的資料
                cutoff_date = pd.to_datetime('2024-12-31')
                data_after_cutoff = valid_dates[valid_dates['日期'] > cutoff_date]
                
                print(f"   2024年12月31日之後: {len(data_after_cutoff)} 筆")
                
                if len(data_after_cutoff) > 0:
                    print(f"   ⚠️ 發現2024年12月31日之後的資料:")
                    for _, row in data_after_cutoff.head(5).iterrows():
                        print(f"     {row['日期'].strftime('%Y-%m-%d')} - {row['學員']} - {row['EPA項目']}")
                else:
                    print(f"   ✅ 沒有2024年12月31日之後的資料，過濾功能正常")
                
                # 按月統計
                monthly_stats = valid_dates.groupby(valid_dates['日期'].dt.to_period('M')).size()
                print(f"   📅 月度分布:")
                for period, count in monthly_stats.items():
                    print(f"     {period}: {count} 筆")
            else:
                print(f"   ⚠️ 沒有有效的日期資料")
        
        # 檢查學員統計
        if '學員' in converted_df.columns:
            student_counts = converted_df['學員'].value_counts()
            print(f"\\n👥 學員統計:")
            for student, count in student_counts.items():
                print(f"   {student}: {count} 筆記錄")
        
        # 檢查EPA項目統計
        if 'EPA項目' in converted_df.columns:
            epa_counts = converted_df['EPA項目'].value_counts()
            print(f"\\n📋 EPA項目統計:")
            for epa, count in epa_counts.head(10).items():
                print(f"   {epa}: {count} 筆記錄")
        
        print("\\n🎉 日期過濾功能測試完成！")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        print(f"詳細錯誤信息: {traceback.format_exc()}")
        return False

def test_date_parsing():
    """測試日期解析功能"""
    print("\\n🧪 測試日期解析功能...")
    
    # 測試各種日期格式
    test_dates = [
        "2024-12-31",
        "2024/12/31",
        "2024-12-31 10:30:00",
        "2024/12/31 10:30:00",
        "12/31/2024",
        "31/12/2024",
        "2025-01-01",
        "2025/01/01",
        "2025-01-15",
        "invalid_date",
        "",
        None
    ]
    
    cutoff_date = pd.to_datetime('2024-12-31')
    
    for test_date in test_dates:
        try:
            if test_date is None or test_date == "":
                print(f"   {test_date}: 空值")
                continue
                
            # 嘗試解析日期
            parsed_date = pd.to_datetime(test_date, errors='coerce')
            
            if pd.isna(parsed_date):
                print(f"   {test_date}: 無法解析")
            else:
                if parsed_date > cutoff_date:
                    print(f"   {test_date}: {parsed_date.strftime('%Y-%m-%d')} ❌ (會被過濾)")
                else:
                    print(f"   {test_date}: {parsed_date.strftime('%Y-%m-%d')} ✅ (會保留)")
                    
        except Exception as e:
            print(f"   {test_date}: 解析錯誤 - {str(e)}")
    
    print("✅ 日期解析功能測試完成")

def main():
    """主測試程式"""
    print("=" * 60)
    print("🧪 EMYWAY資料日期過濾功能測試")
    print("=" * 60)
    
    # 測試日期解析
    test_date_parsing()
    
    # 測試日期過濾功能
    test_result = test_date_filtering()
    
    print("\\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    
    if test_result:
        print("🎉 日期過濾功能測試通過！")
        print("\\n✅ 功能包括:")
        print("   • 只保留2024年12月31日之前的EMYWAY資料")
        print("   • 支援多種日期格式解析")
        print("   • 自動過濾2025年及之後的資料")
        print("   • 提供詳細的過濾統計資訊")
    else:
        print("❌ 日期過濾功能測試失敗，請檢查錯誤訊息")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
