#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理導出檔案中的重複資料
"""

import pandas as pd
import os
from datetime import datetime

class ExportDataCleaner:
    def __init__(self, file_path):
        self.file_path = file_path
        self.df = None
        
    def load_data(self):
        """載入資料"""
        try:
            self.df = pd.read_csv(self.file_path, encoding='utf-8')
            print(f"✅ 成功載入資料: {len(self.df)} 筆記錄")
            return True
        except Exception as e:
            print(f"❌ 載入資料失敗: {e}")
            return False
    
    def analyze_duplicates(self):
        """分析重複資料"""
        if self.df is None:
            print("❌ 請先載入資料")
            return
        
        print("\n🔍 分析重複資料...")
        
        # 1. 完全重複的記錄
        print("\n1. 完全重複的記錄:")
        complete_duplicates = self.df.duplicated()
        complete_dup_count = complete_duplicates.sum()
        print(f"   完全重複記錄: {complete_dup_count} 筆")
        
        if complete_dup_count > 0:
            print("   完全重複記錄範例:")
            dup_records = self.df[complete_duplicates].head(3)
            for i, (_, row) in enumerate(dup_records.iterrows()):
                print(f"     {i+1}. {row.get('日期', 'N/A')} - {row.get('EPA項目', 'N/A')} - {row.get('個案姓名', 'N/A')}")
        
        # 2. 基於關鍵欄位的重複（除了資料來源）
        print("\n2. 基於關鍵欄位的重複記錄:")
        key_columns = ['日期', 'EPA項目', '病歷號碼', '個案姓名', '診斷']
        
        # 標準化病歷號碼（移除.0後綴）
        df_temp = self.df.copy()
        df_temp['病歷號碼_標準化'] = df_temp['病歷號碼'].astype(str).str.replace('.0', '')
        
        # 創建合併鍵
        df_temp['merge_key'] = df_temp[['日期', 'EPA項目', '病歷號碼_標準化', '個案姓名', '診斷']].astype(str).agg('|'.join, axis=1)
        
        # 找出重複
        key_duplicates = df_temp.duplicated(subset=['merge_key'], keep=False)
        key_dup_count = key_duplicates.sum()
        print(f"   關鍵欄位重複記錄: {key_dup_count} 筆")
        
        if key_dup_count > 0:
            print("   關鍵欄位重複記錄範例:")
            key_dup_records = df_temp[key_duplicates].head(6)
            for i, (_, row) in enumerate(key_dup_records.iterrows()):
                print(f"     {i+1}. {row.get('日期', 'N/A')} - {row.get('EPA項目', 'N/A')} - {row.get('個案姓名', 'N/A')} - {row.get('資料來源', 'N/A')}")
        
        # 3. 資料來源分布
        print("\n3. 資料來源分布:")
        if '資料來源' in self.df.columns:
            source_counts = self.df['資料來源'].value_counts()
            for source, count in source_counts.items():
                percentage = (count / len(self.df)) * 100
                print(f"   {source}: {count} 筆 ({percentage:.1f}%)")
        
        return complete_dup_count, key_dup_count
    
    def clean_data(self):
        """清理重複資料"""
        if self.df is None:
            print("❌ 請先載入資料")
            return None
        
        print("\n🧹 開始清理重複資料...")
        
        # 記錄原始數量
        original_count = len(self.df)
        
        # 1. 移除完全重複的記錄
        print("1. 移除完全重複的記錄...")
        complete_duplicates = self.df.duplicated()
        complete_dup_count = complete_duplicates.sum()
        self.df = self.df[~complete_duplicates]
        print(f"   移除 {complete_dup_count} 筆完全重複記錄")
        
        # 2. 處理基於關鍵欄位的重複
        print("2. 處理基於關鍵欄位的重複記錄...")
        
        # 標準化病歷號碼
        self.df['病歷號碼_標準化'] = self.df['病歷號碼'].astype(str).str.replace('.0', '')
        
        # 創建合併鍵
        self.df['merge_key'] = self.df[['日期', 'EPA項目', '病歷號碼_標準化', '個案姓名', '診斷']].astype(str).agg('|'.join, axis=1)
        
        # 找出重複記錄
        key_duplicates = self.df.duplicated(subset=['merge_key'], keep=False)
        key_dup_count = key_duplicates.sum()
        
        if key_dup_count > 0:
            print(f"   發現 {key_dup_count} 筆基於關鍵欄位的重複記錄")
            
            # 優先保留現有系統的資料
            duplicate_groups = self.df[key_duplicates].groupby('merge_key')
            
            records_to_remove = []
            for key, group in duplicate_groups:
                if len(group) > 1:
                    # 檢查是否有現有系統的資料
                    current_system_records = group[group['資料來源'] == '現有系統']
                    
                    if not current_system_records.empty:
                        # 如果有現有系統的資料，移除EMYWAY歷史資料
                        emway_records = group[group['資料來源'] == 'EMYWAY歷史資料']
                        if not emway_records.empty:
                            records_to_remove.extend(emway_records.index.tolist())
                            print(f"     保留現有系統記錄，移除EMYWAY記錄: {key[:50]}...")
                    else:
                        # 如果只有EMYWAY資料，保留第一筆
                        keep_record = group.index[0]
                        remove_records = group.index[1:].tolist()
                        records_to_remove.extend(remove_records)
                        print(f"     只保留第一筆EMYWAY記錄: {key[:50]}...")
            
            # 移除重複記錄
            self.df = self.df.drop(records_to_remove)
            print(f"   移除 {len(records_to_remove)} 筆重複記錄")
        
        # 3. 清理臨時欄位
        self.df = self.df.drop(['病歷號碼_標準化', 'merge_key'], axis=1)
        
        # 4. 統計清理結果
        final_count = len(self.df)
        removed_count = original_count - final_count
        
        print(f"\n📊 清理結果:")
        print(f"   原始記錄數: {original_count} 筆")
        print(f"   清理後記錄數: {final_count} 筆")
        print(f"   移除記錄數: {removed_count} 筆")
        print(f"   清理率: {(removed_count / original_count * 100):.1f}%")
        
        return self.df
    
    def save_cleaned_data(self, output_path=None):
        """儲存清理後的資料"""
        if self.df is None:
            print("❌ 沒有資料可儲存")
            return
        
        if output_path is None:
            # 生成輸出檔案名稱
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(os.path.basename(self.file_path))[0]
            output_path = os.path.join(os.path.dirname(self.file_path), f"{base_name}_cleaned_{timestamp}.csv")
        
        try:
            self.df.to_csv(output_path, index=False, encoding='utf-8')
            print(f"✅ 清理後的資料已儲存至: {output_path}")
            return output_path
        except Exception as e:
            print(f"❌ 儲存失敗: {e}")
            return None
    
    def backup_original(self):
        """備份原始檔案"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.file_path}.backup_{timestamp}"
            
            # 複製原始檔案
            import shutil
            shutil.copy2(self.file_path, backup_path)
            print(f"✅ 原始檔案已備份至: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"❌ 備份失敗: {e}")
            return None

def main():
    """主程式"""
    print("=" * 60)
    print("🧹 導出資料重複清理工具")
    print("=" * 60)
    
    # 檔案路徑
    file_path = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/2025-10-02T10-29_export.csv"
    
    if not os.path.exists(file_path):
        print(f"❌ 檔案不存在: {file_path}")
        return
    
    # 初始化清理器
    cleaner = ExportDataCleaner(file_path)
    
    # 載入資料
    if not cleaner.load_data():
        return
    
    # 分析重複資料
    complete_dup, key_dup = cleaner.analyze_duplicates()
    
    # 備份原始檔案
    cleaner.backup_original()
    
    # 清理資料
    cleaned_df = cleaner.clean_data()
    
    if cleaned_df is not None:
        # 儲存清理後的資料
        output_path = cleaner.save_cleaned_data()
        
        # 顯示最終統計
        print(f"\n🎉 資料清理完成！")
        print(f"📁 清理後的檔案: {output_path}")
        
        # 最終資料來源分布
        if '資料來源' in cleaned_df.columns:
            print(f"\n📊 最終資料來源分布:")
            source_counts = cleaned_df['資料來源'].value_counts()
            for source, count in source_counts.items():
                percentage = (count / len(cleaned_df)) * 100
                print(f"   {source}: {count} 筆 ({percentage:.1f}%)")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
