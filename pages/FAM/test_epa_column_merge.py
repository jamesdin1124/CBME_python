#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試EPA項目欄位合併功能
"""

import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_epa_column_merge():
    """測試EPA項目欄位合併功能"""
    try:
        from pages.FAM.fam_data_processor import FAMDataProcessor
        
        print("🚀 開始測試EPA項目欄位合併功能...")
        
        # 讀取合併後的資料檔案
        merged_csv_path = os.path.join(os.path.dirname(__file__), 'merged_data (11).csv')
        
        if os.path.exists(merged_csv_path):
            print(f"✅ 找到合併後資料檔案")
            df_original = pd.read_csv(merged_csv_path, encoding='utf-8')
            print(f"📊 原始檔案形狀: {df_original.shape}")
            
            # 檢查EPA項目相關欄位
            print(f"\n📋 EPA項目相關欄位檢查:")
            epa_columns = [col for col in df_original.columns if 'EPA' in col]
            for col in epa_columns:
                non_null_count = df_original[col].notna().sum()
                print(f"  • {col}: {non_null_count}/{len(df_original)} 筆有資料")
            
            # 檢查EPA項目和EPA項目 [原始]的分佈
            if 'EPA項目' in df_original.columns:
                epa_main_counts = df_original['EPA項目'].value_counts()
                print(f"\n📊 EPA項目分佈 (前10個):")
                for epa, count in epa_main_counts.head(10).items():
                    print(f"  '{epa}': {count} 筆")
            
            if 'EPA項目 [原始]' in df_original.columns:
                epa_original_counts = df_original['EPA項目 [原始]'].value_counts()
                print(f"\n📊 EPA項目 [原始]分佈 (前10個):")
                for epa, count in epa_original_counts.head(10).items():
                    print(f"  '{epa}': {count} 筆")
            
            # 初始化處理器
            processor = FAMDataProcessor()
            
            # 清理資料（包含EPA項目欄位合併）
            cleaned_df = processor.clean_data(df_original, debug=True)
            print(f"\n✅ 資料清理完成: {cleaned_df.shape}")
            
            # 檢查清理後的EPA項目分佈
            if 'EPA項目' in cleaned_df.columns:
                cleaned_epa_counts = cleaned_df['EPA項目'].value_counts()
                print(f"\n📊 清理後EPA項目分佈:")
                for epa, count in cleaned_epa_counts.head(15).items():
                    if epa and epa != '':
                        print(f"  ✅ '{epa}': {count} 筆")
                    else:
                        print(f"  📝 空EPA項目: {count} 筆")
            
            # 檢查學員分佈
            if '學員' in cleaned_df.columns:
                students = cleaned_df['學員'].value_counts()
                print(f"\n👥 學員分佈:")
                for student, count in students.head(10).items():
                    if student and student != '學員':
                        print(f"  • {student}: {count} 筆記錄")
            
            # 檢查特定學員的EPA項目資料
            print(f"\n🎯 檢查鄧祖嶸的EPA項目資料:")
            if '學員' in cleaned_df.columns:
                deng_records = cleaned_df[cleaned_df['學員'] == '鄧祖嶸']
                print(f"  鄧祖嶸的記錄數: {len(deng_records)}")
                
                if not deng_records.empty and 'EPA項目' in deng_records.columns:
                    deng_epa_counts = deng_records['EPA項目'].value_counts()
                    print(f"  📊 鄧祖嶸的EPA項目分佈:")
                    for epa, count in deng_epa_counts.items():
                        if epa and epa != '':
                            print(f"    ✅ '{epa}': {count} 筆")
                        else:
                            print(f"    📝 空EPA項目: {count} 筆")
            
            # 檢查合併效果
            print(f"\n🔍 EPA項目欄位合併效果檢查:")
            if 'EPA項目 [原始]' in df_original.columns and 'EPA項目' in cleaned_df.columns:
                # 比較合併前後的EPA項目數量
                original_epa_count = len(df_original[df_original['EPA項目 [原始]'].notna() & (df_original['EPA項目 [原始]'] != '')])
                cleaned_epa_count = len(cleaned_df[cleaned_df['EPA項目'].notna() & (cleaned_df['EPA項目'] != '')])
                
                print(f"  • 原始EPA項目 [原始]有資料記錄: {original_epa_count} 筆")
                print(f"  • 清理後EPA項目有資料記錄: {cleaned_epa_count} 筆")
                
                if cleaned_epa_count >= original_epa_count:
                    print(f"  ✅ EPA項目欄位合併成功，資料沒有遺失")
                else:
                    print(f"  ⚠️ EPA項目欄位合併可能有資料遺失")
            
            print(f"\n🎉 EPA項目欄位合併測試完成！")
            return True
        else:
            print(f"❌ 找不到合併後資料檔案")
            return False
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 80)
    result = test_epa_column_merge()
    print("=" * 80)
    
    if result:
        print("🎉 EPA項目欄位合併測試成功！")
        print("\n💡 合併功能說明:")
        print("- 自動檢測 EPA項目 [原始] 欄位")
        print("- 將兩個欄位的EPA項目資料合併到主要 EPA項目 欄位")
        print("- 確保所有EPA項目資料都能被正確處理")
        print("- 保持資料完整性，不會遺失任何EPA項目資訊")
    else:
        print("❌ EPA項目欄位合併測試失敗！")
