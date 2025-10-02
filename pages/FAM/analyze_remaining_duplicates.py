#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析剩餘的重複記錄
"""

import pandas as pd
import os

def analyze_remaining_duplicates():
    """分析剩餘的重複記錄"""
    print("🔍 分析剩餘的重複記錄...")
    
    # 載入清理後的資料
    file_path = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/integrated_epa_data.csv"
    
    if not os.path.exists(file_path):
        print("❌ 整合資料檔案不存在")
        return False
    
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
        print(f"✅ 成功載入資料: {len(df)} 筆記錄")
        
        # 標準化病歷號碼
        df['病歷號碼_標準化'] = df['病歷號碼'].astype(str).str.replace('.0', '')
        
        # 創建合併鍵
        key_columns = ['日期', 'EPA項目', '病歷號碼_標準化', '個案姓名', '診斷', '觀察場域']
        df['merge_key'] = df[key_columns].astype(str).agg('|'.join, axis=1)
        
        # 找出重複
        key_duplicates = df.duplicated(subset=['merge_key'], keep=False)
        key_dup_count = key_duplicates.sum()
        
        print(f"🔍 基於關鍵欄位的重複記錄: {key_dup_count} 筆")
        
        if key_dup_count > 0:
            print("\n📋 重複記錄詳細分析:")
            dup_records = df[key_duplicates].sort_values('merge_key')
            
            # 按合併鍵分組
            for key, group in dup_records.groupby('merge_key'):
                print(f"\n🔸 重複群組: {key}")
                for i, (_, row) in enumerate(group.iterrows()):
                    print(f"  {i+1}. 資料來源: {row.get('資料來源', 'N/A')}")
                    print(f"     日期: {row.get('日期', 'N/A')}")
                    print(f"     EPA項目: {row.get('EPA項目', 'N/A')}")
                    print(f"     病歷號碼: {row.get('病歷號碼', 'N/A')}")
                    print(f"     個案姓名: {row.get('個案姓名', 'N/A')}")
                    print(f"     診斷: {row.get('診斷', 'N/A')}")
                    print(f"     觀察場域: {row.get('觀察場域', 'N/A')}")
                    print(f"     複雜程度: {row.get('複雜程度', 'N/A')}")
                    print(f"     信賴程度: {row.get('信賴程度(教師評量)', 'N/A')}")
                    print()
        
        return True
        
    except Exception as e:
        print(f"❌ 分析失敗: {str(e)}")
        import traceback
        print(f"詳細錯誤信息: {traceback.format_exc()}")
        return False

def main():
    """主程式"""
    print("=" * 60)
    print("🔍 剩餘重複記錄分析工具")
    print("=" * 60)
    
    # 分析剩餘的重複記錄
    analyze_remaining_duplicates()
    
    print("=" * 60)

if __name__ == "__main__":
    main()
