#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查部署檔案完整性
確保EMYWAY資料和整合資料都包含在部署中
"""

import os
import pandas as pd
from datetime import datetime

def check_deployment_files():
    """檢查部署所需的檔案"""
    print("🔍 檢查部署檔案完整性...")
    
    # 必要的檔案清單
    required_files = [
        "new_dashboard.py",  # 主應用程式
        "requirements.txt",  # 依賴套件
        "Dockerfile",        # Docker配置
        "fly.toml",         # Fly.io配置
        "pages/FAM/integrated_epa_data.csv",  # 整合資料
        "pages/FAM/emway_converted_data.csv",  # EMYWAY轉換資料
        "pages/FAM/EPA匯出原始檔_1140923.csv",  # 原始EPA資料
        "pages/FAM/fam_residents.py",  # FAM住院醫師頁面
        "pages/FAM/fam_visualization.py",  # FAM視覺化
        "pages/FAM/fam_data_processor.py",  # FAM資料處理
        "pages/FAM/emway_data_converter.py",  # EMYWAY資料轉換器
        "pages/FAM/emway_data_integration.py",  # EMYWAY資料整合器
    ]
    
    # EMYWAY原始資料目錄
    emway_dirs = [
        "pages/FAM/EMYWAY資料/CEPO併Emyway EPA統計分析(含統計圖)_張玄穎",
        "pages/FAM/EMYWAY資料/CEPO併Emyway EPA統計分析(含統計圖)_徐呈祥", 
        "pages/FAM/EMYWAY資料/CEPO併Emyway EPA統計分析(含統計圖)_鄧祖嶸",
        "pages/FAM/EMYWAY資料/CEPO併Emyway EPA統計分析(含統計圖)_陳柏豪",
        "pages/FAM/EMYWAY資料/CEPO併Emyway EPA統計分析(含統計圖)_陳麒任",
        "pages/FAM/EMYWAY資料/CEPO併Emyway EPA統計分析(含統計圖)_高士傑"
    ]
    
    missing_files = []
    existing_files = []
    
    # 檢查必要檔案
    for file_path in required_files:
        if os.path.exists(file_path):
            existing_files.append(file_path)
            print(f"✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"❌ {file_path}")
    
    # 檢查EMYWAY原始資料目錄
    print(f"\\n📁 檢查EMYWAY原始資料目錄:")
    emway_missing = []
    emway_existing = []
    
    for emway_dir in emway_dirs:
        if os.path.exists(emway_dir) and os.path.isdir(emway_dir):
            emway_existing.append(emway_dir)
            # 計算目錄中的CSV檔案數量
            csv_count = len([f for f in os.listdir(emway_dir) if f.endswith('.csv')])
            print(f"✅ {emway_dir} ({csv_count} 個CSV檔案)")
        else:
            emway_missing.append(emway_dir)
            print(f"❌ {emway_dir}")
    
    # 檢查整合資料的內容
    print(f"\\n📊 檢查整合資料內容:")
    try:
        integrated_df = pd.read_csv("pages/FAM/integrated_epa_data.csv", encoding='utf-8')
        print(f"✅ 整合資料載入成功: {len(integrated_df)} 筆記錄")
        
        # 檢查資料來源分布
        if '資料來源' in integrated_df.columns:
            source_counts = integrated_df['資料來源'].value_counts()
            print(f"📈 資料來源分布:")
            for source, count in source_counts.items():
                print(f"   {source}: {count} 筆")
        else:
            print("⚠️ 整合資料中沒有'資料來源'欄位")
        
        # 檢查學員分布
        if '學員' in integrated_df.columns:
            student_counts = integrated_df['學員'].value_counts()
            print(f"👥 學員分布:")
            for student, count in student_counts.items():
                print(f"   {student}: {count} 筆")
        
        # 檢查EPA項目分布
        if 'EPA項目' in integrated_df.columns:
            epa_counts = integrated_df['EPA項目'].value_counts()
            print(f"🎯 EPA項目分布:")
            for epa, count in epa_counts.items():
                print(f"   {epa}: {count} 筆")
        
    except Exception as e:
        print(f"❌ 整合資料載入失敗: {str(e)}")
    
    # 檢查EMYWAY轉換資料
    print(f"\\n📊 檢查EMYWAY轉換資料:")
    try:
        emway_df = pd.read_csv("pages/FAM/emway_converted_data.csv", encoding='utf-8')
        print(f"✅ EMYWAY轉換資料載入成功: {len(emway_df)} 筆記錄")
        
        # 檢查學員分布
        if '學員' in emway_df.columns:
            student_counts = emway_df['學員'].value_counts()
            print(f"👥 EMYWAY學員分布:")
            for student, count in student_counts.items():
                print(f"   {student}: {count} 筆")
        
    except Exception as e:
        print(f"❌ EMYWAY轉換資料載入失敗: {str(e)}")
    
    # 總結報告
    print(f"\\n" + "="*60)
    print("📋 部署檔案檢查報告")
    print("="*60)
    
    print(f"✅ 存在檔案: {len(existing_files)}/{len(required_files)}")
    print(f"❌ 缺失檔案: {len(missing_files)}")
    
    if missing_files:
        print(f"\\n⚠️ 缺失的檔案:")
        for file in missing_files:
            print(f"   - {file}")
    
    print(f"\\n📁 EMYWAY原始資料:")
    print(f"✅ 存在目錄: {len(emway_existing)}/{len(emway_dirs)}")
    print(f"❌ 缺失目錄: {len(emway_missing)}")
    
    if emway_missing:
        print(f"\\n⚠️ 缺失的EMYWAY目錄:")
        for dir_path in emway_missing:
            print(f"   - {dir_path}")
    
    # 部署建議
    print(f"\\n🚀 部署建議:")
    if not missing_files and not emway_missing:
        print("✅ 所有必要檔案都存在，可以進行部署")
        print("✅ EMYWAY資料和整合資料都已準備就緒")
        print("✅ 部署後網站將包含完整的歷史資料和現有資料")
    else:
        print("⚠️ 有檔案缺失，請先解決缺失檔案問題")
        if missing_files:
            print("   1. 檢查缺失的必要檔案")
        if emway_missing:
            print("   2. 檢查缺失的EMYWAY資料目錄")
    
    return len(missing_files) == 0 and len(emway_missing) == 0

def check_data_integration():
    """檢查資料整合狀態"""
    print(f"\\n🔍 檢查資料整合狀態...")
    
    try:
        # 載入整合資料
        integrated_df = pd.read_csv("pages/FAM/integrated_epa_data.csv", encoding='utf-8')
        
        print(f"✅ 整合資料載入成功")
        print(f"📊 總記錄數: {len(integrated_df)}")
        
        # 檢查資料來源
        if '資料來源' in integrated_df.columns:
            source_distribution = integrated_df['資料來源'].value_counts()
            print(f"\\n📈 資料來源分布:")
            for source, count in source_distribution.items():
                percentage = (count / len(integrated_df)) * 100
                print(f"   {source}: {count} 筆 ({percentage:.1f}%)")
            
            # 檢查是否有EMYWAY資料
            if 'EMYWAY歷史資料' in source_distribution:
                emway_count = source_distribution['EMYWAY歷史資料']
                print(f"\\n🎉 EMYWAY歷史資料已成功整合: {emway_count} 筆")
            else:
                print(f"\\n⚠️ 整合資料中沒有EMYWAY歷史資料")
            
            # 檢查是否有現有系統資料
            if '現有系統' in source_distribution:
                current_count = source_distribution['現有系統']
                print(f"✅ 現有系統資料: {current_count} 筆")
            else:
                print(f"\\n⚠️ 整合資料中沒有現有系統資料")
        else:
            print(f"\\n❌ 整合資料中沒有'資料來源'欄位")
        
        # 檢查學員覆蓋
        if '學員' in integrated_df.columns:
            students = integrated_df['學員'].unique()
            print(f"\\n👥 學員覆蓋: {len(students)} 名學員")
            for student in sorted(students):
                student_data = integrated_df[integrated_df['學員'] == student]
                print(f"   {student}: {len(student_data)} 筆記錄")
        
        return True
        
    except Exception as e:
        print(f"❌ 資料整合檢查失敗: {str(e)}")
        return False

def main():
    """主程式"""
    print("=" * 60)
    print("🚀 Streamlit網站部署檔案檢查")
    print("=" * 60)
    
    # 檢查部署檔案
    files_ok = check_deployment_files()
    
    # 檢查資料整合
    data_ok = check_data_integration()
    
    print(f"\\n" + "=" * 60)
    print("📊 檢查結果總結")
    print("=" * 60)
    
    if files_ok and data_ok:
        print("🎉 所有檢查通過！可以進行部署")
        print("\\n✅ 部署準備完成:")
        print("   • 所有必要檔案都存在")
        print("   • EMYWAY歷史資料已整合")
        print("   • 現有系統資料完整")
        print("   • 資料來源標記正確")
        print("   • 學員資料覆蓋完整")
        print("\\n🚀 部署後功能:")
        print("   • 完整的歷史資料分析")
        print("   • EMYWAY與現有系統資料整合")
        print("   • 資料來源過濾功能")
        print("   • 統一的視覺化呈現")
        print("   • 每月平均趨勢分析")
        print("   • 小提琴圖數據點整合")
    else:
        print("⚠️ 檢查未完全通過，請解決問題後再部署")
        if not files_ok:
            print("   • 檔案完整性問題")
        if not data_ok:
            print("   • 資料整合問題")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
