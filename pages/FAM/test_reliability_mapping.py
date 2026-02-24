#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試EPA信賴程度分數轉換功能
"""

import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_reliability_mapping():
    """測試EPA信賴程度分數轉換功能"""
    try:
        from pages.FAM.fam_data_processor import FAMDataProcessor
        
        print("🚀 開始測試EPA信賴程度分數轉換功能...")
        
        # 初始化處理器
        processor = FAMDataProcessor()
        
        # 測試各種信賴程度文字轉換
        test_cases = [
            "教師在旁逐步共同操作",  # 應該是 1.0
            "教師在旁必要時協助",     # 應該是 2.0
            "教師事後重點確認",       # 應該是 3.0
            "必要時知會教師確認",     # 應該是 4.0
            "獨立執行",              # 應該是 5.0
            "學員在旁觀察",          # 應該是 0.0
            "不允許學員觀察",        # 應該是 0.0
            "請選擇",               # 應該是 0.0
            "4",                   # 已經是數字，應該是 4.0
            "3.5",                 # 已經是數字，應該是 3.5
            "無效文字",             # 應該是 None
            "",                    # 空字串，應該是 None
            "   ",                 # 空白字串，應該是 None
        ]
        
        expected_results = [
            1.0,   # 教師在旁逐步共同操作
            2.0,   # 教師在旁必要時協助
            3.0,   # 教師事後重點確認
            4.0,   # 必要時知會教師確認
            5.0,   # 獨立執行
            0.0,   # 學員在旁觀察
            0.0,   # 不允許學員觀察
            0.0,   # 請選擇
            4.0,   # 4
            3.5,   # 3.5
            None,  # 無效文字
            None,  # 空字串
            None,  # 空白字串
        ]
        
        print("\n📊 測試信賴程度分數轉換:")
        print("=" * 70)
        
        all_passed = True
        
        for i, (test_text, expected) in enumerate(zip(test_cases, expected_results)):
            result = processor._convert_reliability_to_numeric(test_text)
            
            status = "✅ 通過" if result == expected else "❌ 失敗"
            
            # 處理None值的顯示
            result_str = str(result) if result is not None else "None"
            expected_str = str(expected) if expected is not None else "None"
            
            print(f"{i+1:2d}. {test_text:15s} → {result_str:6s} (期望: {expected_str:6s}) {status}")
            
            if result != expected:
                all_passed = False
        
        print("=" * 70)
        
        # 測試實際CSV資料
        print("\n📁 測試實際CSV資料轉換:")
        csv_path = os.path.join(os.path.dirname(__file__), '2025-09-24T03-11_export.csv')
        
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path, encoding='utf-8')
            print(f"✅ 成功讀取CSV檔案: {df.shape}")
            
            # 檢查信賴程度欄位
            if '信賴程度(教師評量)' in df.columns:
                reliability_values = df['信賴程度(教師評量)'].value_counts()
                print(f"\n📊 原始信賴程度分布:")
                for value, count in reliability_values.items():
                    numeric_value = processor._convert_reliability_to_numeric(value)
                    print(f"  {value:20s} ({count:2d}筆) → {numeric_value}")
            else:
                print("❌ 找不到信賴程度(教師評量)欄位")
        else:
            print("❌ 找不到CSV檔案")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 70)
    result = test_reliability_mapping()
    print("=" * 70)
    
    if result:
        print("🎉 EPA信賴程度分數轉換功能測試成功！")
    else:
        print("❌ EPA信賴程度分數轉換功能測試失敗！")
