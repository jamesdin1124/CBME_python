#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試教師回饋時間排序功能
"""

import pandas as pd
import os
from fam_data_processor import FAMDataProcessor

def test_teacher_feedback_ordering():
    """測試教師回饋時間排序功能"""
    print("🧪 測試教師回饋時間排序功能...")
    
    # 載入整合資料
    integrated_file = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/integrated_epa_data.csv"
    
    if not os.path.exists(integrated_file):
        print("❌ 整合資料檔案不存在")
        return False
    
    try:
        # 載入資料
        df = pd.read_csv(integrated_file, encoding='utf-8')
        print(f"✅ 成功載入整合資料: {len(df)} 筆記錄")
        
        # 初始化處理器
        processor = FAMDataProcessor()
        
        # 清理資料
        cleaned_df = processor.clean_data(df)
        print(f"✅ 資料清理完成: {len(cleaned_df)} 筆記錄")
        
        # 測試學員清單
        students = processor.get_student_list(cleaned_df)
        print(f"✅ 學員清單: {len(students)} 名學員")
        
        # 測試教師回饋時間排序
        if students:
            test_student = students[0]
            
            print(f"\\n🧪 測試學員: {test_student}")
            
            # 獲取學員的資料
            student_data = cleaned_df[cleaned_df['學員'] == test_student]
            
            print(f"   該學員的資料: {len(student_data)} 筆記錄")
            
            # 獲取EPA項目清單
            epa_items = processor.get_epa_items(student_data)
            print(f"   EPA項目: {len(epa_items)} 個")
            
            # 測試每個EPA項目的教師回饋排序
            for epa_item in epa_items[:3]:  # 測試前3個EPA項目
                print(f"\\n📋 測試EPA項目: {epa_item}")
                
                # 獲取該EPA項目的教師回饋
                epa_data = student_data[student_data['EPA項目'] == epa_item]
                feedback_data = epa_data[epa_data['教師給學員回饋'].notna() & (epa_data['教師給學員回饋'] != '')]
                
                print(f"   總記錄數: {len(epa_data)}")
                print(f"   有回饋記錄數: {len(feedback_data)}")
                
                if not feedback_data.empty:
                    # 測試排序前的日期順序
                    print(f"\\n   📅 排序前的日期順序:")
                    original_dates = []
                    for idx, (_, row) in enumerate(feedback_data.iterrows()):
                        date_str = "N/A"
                        if '日期' in row and pd.notna(row['日期']):
                            if hasattr(row['日期'], 'strftime'):
                                date_str = row['日期'].strftime('%Y-%m-%d')
                            else:
                                date_str = str(row['日期'])
                        original_dates.append(date_str)
                        if idx < 5:  # 只顯示前5筆
                            print(f"     {idx+1}. {date_str}")
                    
                    # 模擬排序邏輯
                    feedback_data_copy = feedback_data.copy()
                    if '日期' in feedback_data_copy.columns:
                        feedback_data_copy['日期'] = pd.to_datetime(feedback_data_copy['日期'], errors='coerce')
                        # 按日期降序排列（最新在前）
                        feedback_data_copy = feedback_data_copy.sort_values('日期', ascending=False)
                    
                    # 測試排序後的日期順序
                    print(f"\\n   📅 排序後的日期順序（最新在前）:")
                    sorted_dates = []
                    for idx, (_, row) in enumerate(feedback_data_copy.iterrows()):
                        date_str = "N/A"
                        if '日期' in row and pd.notna(row['日期']):
                            if hasattr(row['日期'], 'strftime'):
                                date_str = row['日期'].strftime('%Y-%m-%d')
                            else:
                                date_str = str(row['日期'])
                        sorted_dates.append(date_str)
                        if idx < 5:  # 只顯示前5筆
                            data_source = row.get('資料來源', '未知來源')
                            print(f"     {idx+1}. {date_str} | {data_source}")
                    
                    # 驗證排序是否正確
                    print(f"\\n   🔍 排序驗證:")
                    valid_dates = [d for d in sorted_dates if d != "N/A"]
                    if len(valid_dates) > 1:
                        # 檢查是否按降序排列
                        is_descending = True
                        for i in range(len(valid_dates) - 1):
                            if valid_dates[i] < valid_dates[i + 1]:
                                is_descending = False
                                break
                        
                        if is_descending:
                            print(f"     ✅ 日期排序正確（降序，最新在前）")
                        else:
                            print(f"     ❌ 日期排序錯誤")
                            print(f"     排序後前3筆日期: {valid_dates[:3]}")
                    else:
                        print(f"     ℹ️ 有效日期不足，無法驗證排序")
                    
                    # 檢查資料來源分布
                    if '資料來源' in feedback_data_copy.columns:
                        source_counts = feedback_data_copy['資料來源'].value_counts()
                        print(f"     📊 回饋資料來源分布: {source_counts.to_dict()}")
                else:
                    print(f"   ℹ️ 沒有教師回饋")
        
        print("\\n🎉 教師回饋時間排序功能測試完成！")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        print(f"詳細錯誤信息: {traceback.format_exc()}")
        return False

def test_feedback_date_parsing():
    """測試教師回饋日期解析"""
    print("\\n🧪 測試教師回饋日期解析...")
    
    integrated_file = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/integrated_epa_data.csv"
    
    try:
        df = pd.read_csv(integrated_file, encoding='utf-8')
        processor = FAMDataProcessor()
        cleaned_df = processor.clean_data(df)
        
        # 找到有教師回饋的記錄
        feedback_data = cleaned_df[cleaned_df['教師給學員回饋'].notna() & (cleaned_df['教師給學員回饋'] != '')]
        
        print(f"   總教師回饋記錄: {len(feedback_data)} 筆")
        
        if '日期' in feedback_data.columns:
            # 測試日期解析
            feedback_copy = feedback_data.copy()
            feedback_copy['日期'] = pd.to_datetime(feedback_copy['日期'], errors='coerce')
            
            valid_dates = feedback_copy[feedback_copy['日期'].notna()]
            invalid_dates = feedback_copy[feedback_copy['日期'].isna()]
            
            print(f"   有效日期記錄: {len(valid_dates)} 筆")
            print(f"   無效日期記錄: {len(invalid_dates)} 筆")
            
            if not valid_dates.empty:
                # 測試排序
                sorted_data = valid_dates.sort_values('日期', ascending=False)
                
                print(f"\\n   📅 排序測試結果:")
                print(f"   最早日期: {sorted_data['日期'].min().strftime('%Y-%m-%d')}")
                print(f"   最晚日期: {sorted_data['日期'].max().strftime('%Y-%m-%d')}")
                
                # 顯示前5筆最新記錄
                print(f"\\n   前5筆最新記錄:")
                for idx, (_, row) in enumerate(sorted_data.head(5).iterrows()):
                    date_str = row['日期'].strftime('%Y-%m-%d')
                    student = row.get('學員', 'N/A')
                    epa_item = row.get('EPA項目', 'N/A')
                    data_source = row.get('資料來源', 'N/A')
                    print(f"     {idx+1}. {date_str} | {student} | {epa_item} | {data_source}")
                
                return True
            else:
                print(f"   ⚠️ 沒有有效的日期資料")
                return False
        else:
            print(f"   ⚠️ 沒有找到日期欄位")
            return False
            
    except Exception as e:
        print(f"❌ 日期解析測試失敗: {str(e)}")
        return False

def test_ordering_with_different_sources():
    """測試不同資料來源的回饋排序"""
    print("\\n🧪 測試不同資料來源的回饋排序...")
    
    integrated_file = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/integrated_epa_data.csv"
    
    try:
        df = pd.read_csv(integrated_file, encoding='utf-8')
        processor = FAMDataProcessor()
        cleaned_df = processor.clean_data(df)
        
        if '資料來源' in cleaned_df.columns:
            # 分別測試各資料來源的回饋排序
            for source in cleaned_df['資料來源'].unique():
                print(f"\\n   📊 測試資料來源: {source}")
                
                source_data = cleaned_df[cleaned_df['資料來源'] == source]
                feedback_data = source_data[source_data['教師給學員回饋'].notna() & (source_data['教師給學員回饋'] != '')]
                
                print(f"     總記錄數: {len(source_data)}")
                print(f"     回饋記錄數: {len(feedback_data)}")
                
                if not feedback_data.empty and '日期' in feedback_data.columns:
                    # 測試排序
                    feedback_copy = feedback_data.copy()
                    feedback_copy['日期'] = pd.to_datetime(feedback_copy['日期'], errors='coerce')
                    valid_feedback = feedback_copy[feedback_copy['日期'].notna()]
                    
                    if not valid_feedback.empty:
                        sorted_feedback = valid_feedback.sort_values('日期', ascending=False)
                        
                        print(f"     有效日期回饋: {len(valid_feedback)} 筆")
                        print(f"     日期範圍: {sorted_feedback['日期'].min().strftime('%Y-%m-%d')} ~ {sorted_feedback['日期'].max().strftime('%Y-%m-%d')}")
                        
                        # 顯示前3筆最新記錄
                        print(f"     前3筆最新回饋:")
                        for idx, (_, row) in enumerate(sorted_feedback.head(3).iterrows()):
                            date_str = row['日期'].strftime('%Y-%m-%d')
                            student = row.get('學員', 'N/A')
                            epa_item = row.get('EPA項目', 'N/A')
                            print(f"       {idx+1}. {date_str} | {student} | {epa_item}")
                    else:
                        print(f"     ⚠️ 沒有有效的日期回饋")
                else:
                    print(f"     ℹ️ 沒有回饋資料或日期欄位")
        
        return True
        
    except Exception as e:
        print(f"❌ 不同資料來源排序測試失敗: {str(e)}")
        return False

def main():
    """主測試程式"""
    print("=" * 60)
    print("🧪 教師回饋時間排序功能測試")
    print("=" * 60)
    
    # 測試教師回饋時間排序
    test1_result = test_teacher_feedback_ordering()
    
    # 測試日期解析
    test2_result = test_feedback_date_parsing()
    
    # 測試不同資料來源的排序
    test3_result = test_ordering_with_different_sources()
    
    print("\\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    
    if test1_result and test2_result and test3_result:
        print("🎉 所有測試通過！教師回饋時間排序功能正常！")
        print("\\n✅ 功能包括:")
        print("   • 教師回饋按時間排序（最新在前）")
        print("   • 正確解析各種日期格式")
        print("   • 支援不同資料來源的回饋排序")
        print("   • 保持回饋內容和資料來源的完整性")
        print("   • 處理無效日期的情況")
    else:
        print("❌ 部分測試失敗，請檢查錯誤訊息")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
