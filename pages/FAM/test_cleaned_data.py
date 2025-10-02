#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試清理後的資料
"""

import pandas as pd
import os

def test_cleaned_data():
    """測試清理後的資料"""
    print("🧪 測試清理後的資料...")
    
    # 載入清理後的資料
    file_path = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/integrated_epa_data.csv"
    
    if not os.path.exists(file_path):
        print("❌ 整合資料檔案不存在")
        return False
    
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
        print(f"✅ 成功載入清理後的資料: {len(df)} 筆記錄")
        
        # 1. 檢查完全重複記錄
        print(f"\n🔍 檢查完全重複記錄...")
        complete_duplicates = df.duplicated()
        complete_dup_count = complete_duplicates.sum()
        print(f"完全重複記錄: {complete_dup_count} 筆")
        
        if complete_dup_count == 0:
            print("✅ 沒有完全重複的記錄")
        else:
            print("❌ 仍有完全重複的記錄")
            return False
        
        # 2. 檢查基於關鍵欄位的重複記錄
        print(f"\n🔍 檢查基於關鍵欄位的重複記錄...")
        
        # 標準化病歷號碼
        df['病歷號碼_標準化'] = df['病歷號碼'].astype(str).str.replace('.0', '')
        
        # 創建合併鍵
        key_columns = ['日期', 'EPA項目', '病歷號碼_標準化', '個案姓名', '診斷', '觀察場域']
        df['merge_key'] = df[key_columns].astype(str).agg('|'.join, axis=1)
        
        # 找出重複
        key_duplicates = df.duplicated(subset=['merge_key'], keep=False)
        key_dup_count = key_duplicates.sum()
        print(f"關鍵欄位重複記錄: {key_dup_count} 筆")
        
        # 調試：顯示所有記錄的合併鍵
        if key_dup_count > 0:
            print(f"調試：所有記錄的合併鍵:")
            for i, (_, row) in enumerate(df.iterrows()):
                print(f"  {i+1}. {row['merge_key']} | 來源: {row.get('資料來源', 'N/A')}")
        
        if key_dup_count == 0:
            print("✅ 沒有基於關鍵欄位的重複記錄")
        else:
            print("❌ 仍有基於關鍵欄位的重複記錄")
            dup_records = df[key_duplicates]
            print("重複記錄範例:")
            for i, (_, row) in enumerate(dup_records.head(6).iterrows()):
                print(f"  {i+1}. {row.get('日期', 'N/A')} - {row.get('EPA項目', 'N/A')} - {row.get('個案姓名', 'N/A')} - {row.get('資料來源', 'N/A')}")
            return False
        
        # 3. 檢查資料來源分布
        print(f"\n📊 資料來源分布:")
        if '資料來源' in df.columns:
            source_counts = df['資料來源'].value_counts()
            for source, count in source_counts.items():
                percentage = (count / len(df)) * 100
                print(f"  {source}: {count} 筆 ({percentage:.1f}%)")
        
        # 4. 檢查學員統計
        print(f"\n👥 學員統計:")
        if '學員' in df.columns:
            student_counts = df['學員'].value_counts()
            print(f"  總學員數: {len(student_counts)}")
            print(f"  前5名學員:")
            for student, count in student_counts.head(5).items():
                print(f"    {student}: {count} 筆")
        
        # 5. 檢查EPA項目統計
        print(f"\n📋 EPA項目統計:")
        if 'EPA項目' in df.columns:
            epa_counts = df['EPA項目'].value_counts()
            print(f"  EPA項目數: {len(epa_counts)}")
            print(f"  前5個EPA項目:")
            for epa, count in epa_counts.head(5).items():
                print(f"    {epa}: {count} 筆")
        
        # 6. 檢查日期範圍
        print(f"\n📅 日期範圍:")
        if '日期' in df.columns:
            try:
                df['日期_parsed'] = pd.to_datetime(df['日期'])
                min_date = df['日期_parsed'].min()
                max_date = df['日期_parsed'].max()
                print(f"  最早日期: {min_date.strftime('%Y-%m-%d')}")
                print(f"  最晚日期: {max_date.strftime('%Y-%m-%d')}")
            except Exception as e:
                print(f"  日期解析錯誤: {e}")
        
        print(f"\n🎉 所有測試通過！資料清理成功！")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        print(f"詳細錯誤信息: {traceback.format_exc()}")
        return False

def main():
    """主測試程式"""
    print("=" * 60)
    print("🧪 清理後資料測試")
    print("=" * 60)
    
    # 測試清理後的資料
    test_result = test_cleaned_data()
    
    print("\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    
    if test_result:
        print("🎉 所有測試通過！資料清理成功！")
        print("\n✅ 清理成果:")
        print("   • 移除完全重複記錄")
        print("   • 移除基於關鍵欄位的重複記錄")
        print("   • 優先保留現有系統的資料")
        print("   • 保持資料完整性")
        print("   • 提供詳細的統計資訊")
    else:
        print("❌ 測試失敗，請檢查錯誤訊息")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
