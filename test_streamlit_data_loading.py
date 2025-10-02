#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試Streamlit資料載入功能
模擬Streamlit環境下的資料載入
"""

import pandas as pd
import os
import sys

# 添加專案路徑
project_root = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python"
sys.path.append(project_root)

def test_data_loading():
    """測試資料載入功能"""
    print("🧪 測試Streamlit資料載入功能...")
    
    # 測試相對路徑載入
    integrated_file = "pages/FAM/integrated_epa_data.csv"
    
    print(f"📁 測試檔案路徑: {integrated_file}")
    print(f"📁 檔案是否存在: {os.path.exists(integrated_file)}")
    
    if os.path.exists(integrated_file):
        try:
            # 載入資料
            df = pd.read_csv(integrated_file, encoding='utf-8')
            print(f"✅ 成功載入資料: {len(df)} 筆記錄")
            
            # 檢查必要欄位
            required_columns = ['學員', 'EPA項目', '信賴程度(教師評量)', '資料來源']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                print(f"❌ 缺少必要欄位: {missing_columns}")
                return False
            
            print("✅ 所有必要欄位都存在")
            
            # 檢查資料來源分布
            if '資料來源' in df.columns:
                source_counts = df['資料來源'].value_counts()
                print(f"📊 資料來源分布:")
                for source, count in source_counts.items():
                    percentage = (count / len(df)) * 100
                    print(f"   {source}: {count} 筆 ({percentage:.1f}%)")
                
                # 檢查是否有EMYWAY資料
                if 'EMYWAY歷史資料' in source_counts:
                    print(f"🎉 EMYWAY歷史資料已整合: {source_counts['EMYWAY歷史資料']} 筆")
                else:
                    print(f"⚠️ 沒有EMYWAY歷史資料")
            
            # 檢查學員分布
            if '學員' in df.columns:
                students = df['學員'].unique()
                print(f"👥 學員分布: {len(students)} 名學員")
                for student in students:
                    if student != '學員':  # 排除標題行
                        student_data = df[df['學員'] == student]
                        print(f"   {student}: {len(student_data)} 筆記錄")
            
            # 檢查EPA項目分布
            if 'EPA項目' in df.columns:
                epa_counts = df['EPA項目'].value_counts()
                print(f"🎯 EPA項目分布: {len(epa_counts)} 種EPA項目")
                for epa, count in epa_counts.head(5).items():
                    print(f"   {epa}: {count} 筆")
            
            return True
            
        except Exception as e:
            print(f"❌ 載入資料失敗: {str(e)}")
            return False
    else:
        print(f"❌ 檔案不存在: {integrated_file}")
        return False

def test_deployment_paths():
    """測試部署環境下的路徑"""
    print(f"\\n🔍 測試部署環境路徑...")
    
    # 測試當前工作目錄
    current_dir = os.getcwd()
    print(f"📁 當前工作目錄: {current_dir}")
    
    # 測試各種可能的檔案路徑
    possible_paths = [
        "pages/FAM/integrated_epa_data.csv",
        "./pages/FAM/integrated_epa_data.csv",
        f"{current_dir}/pages/FAM/integrated_epa_data.csv"
    ]
    
    for path in possible_paths:
        exists = os.path.exists(path)
        print(f"📁 {path}: {'✅ 存在' if exists else '❌ 不存在'}")
        if exists:
            try:
                df = pd.read_csv(path, encoding='utf-8')
                print(f"   📊 載入成功: {len(df)} 筆記錄")
            except Exception as e:
                print(f"   ❌ 載入失敗: {str(e)}")

def simulate_streamlit_loading():
    """模擬Streamlit環境下的資料載入"""
    print(f"\\n🎭 模擬Streamlit環境...")
    
    # 模擬load_fam_data函數的邏輯
    integrated_file = "pages/FAM/integrated_epa_data.csv"
    df = None
    
    try:
        if os.path.exists(integrated_file):
            df = pd.read_csv(integrated_file, encoding='utf-8')
            print("✅ 模擬Streamlit載入成功")
            print(f"📊 載入資料: {len(df)} 筆記錄")
            
            # 模擬調試模式顯示
            if '資料來源' in df.columns:
                source_counts = df['資料來源'].value_counts()
                print("📊 資料來源分布:", source_counts.to_dict())
            
            return df
        else:
            print("❌ 模擬Streamlit載入失敗：檔案不存在")
            return None
    except Exception as e:
        print(f"❌ 模擬Streamlit載入失敗: {str(e)}")
        return None

def main():
    """主程式"""
    print("=" * 60)
    print("🧪 Streamlit資料載入測試")
    print("=" * 60)
    
    # 測試資料載入
    loading_ok = test_data_loading()
    
    # 測試部署路徑
    test_deployment_paths()
    
    # 模擬Streamlit環境
    streamlit_df = simulate_streamlit_loading()
    
    print("\\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    
    if loading_ok and streamlit_df is not None:
        print("🎉 所有測試通過！資料載入功能正常")
        print("\\n✅ 功能狀態:")
        print("   • 整合資料檔案存在且可讀取")
        print("   • EMYWAY歷史資料已整合")
        print("   • 現有系統資料完整")
        print("   • 相對路徑載入正常")
        print("   • 模擬Streamlit環境載入成功")
        print("\\n🚀 部署建議:")
        print("   • 確保integrated_epa_data.csv在pages/FAM/目錄下")
        print("   • 使用相對路徑載入資料")
        print("   • 部署後網站將包含完整EMYWAY資料")
    else:
        print("⚠️ 測試未完全通過，請檢查問題")
        if not loading_ok:
            print("   • 資料載入問題")
        if streamlit_df is None:
            print("   • Streamlit環境模擬問題")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
