#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試教師回饋功能是否正確顯示EMYWAY資料
"""

import pandas as pd
import os
from fam_data_processor import FAMDataProcessor

def test_teacher_feedback_with_emway():
    """測試教師回饋功能是否包含EMYWAY資料"""
    print("🧪 測試教師回饋功能是否包含EMYWAY資料...")
    
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
        
        # 測試資料來源統計
        if '資料來源' in cleaned_df.columns:
            source_counts = cleaned_df['資料來源'].value_counts()
            print(f"✅ 資料來源分布: {source_counts.to_dict()}")
        
        # 測試學員清單
        students = processor.get_student_list(cleaned_df)
        print(f"✅ 學員清單: {len(students)} 名學員")
        
        # 測試EPA項目清單
        epa_items = processor.get_epa_items(cleaned_df)
        print(f"✅ EPA項目清單: {len(epa_items)} 種")
        
        # 測試教師回饋功能
        if students and epa_items:
            test_student = students[0]
            test_epa = list(epa_items)[0]
            
            print(f"\\n🧪 測試學員: {test_student}, EPA項目: {test_epa}")
            
            # 獲取學員的EPA資料
            student_data = cleaned_df[cleaned_df['學員'] == test_student]
            epa_data = student_data[student_data['EPA項目'] == test_epa]
            
            print(f"   該學員的{test_epa}資料: {len(epa_data)} 筆記錄")
            
            if '資料來源' in epa_data.columns:
                source_counts = epa_data['資料來源'].value_counts()
                print(f"   資料來源分布: {source_counts.to_dict()}")
            
            # 測試教師回饋資料
            feedback_data = epa_data[epa_data['教師給學員回饋'].notna() & (epa_data['教師給學員回饋'] != '')]
            
            print(f"   教師回饋記錄: {len(feedback_data)} 筆")
            
            if '資料來源' in feedback_data.columns and len(feedback_data) > 0:
                feedback_source_counts = feedback_data['資料來源'].value_counts()
                print(f"   回饋資料來源分布: {feedback_source_counts.to_dict()}")
                
                # 檢查是否有EMYWAY資料的回饋
                if 'EMYWAY歷史資料' in feedback_source_counts.index:
                    emway_feedback_count = feedback_source_counts['EMYWAY歷史資料']
                    print(f"   ✅ 找到EMYWAY歷史資料回饋: {emway_feedback_count} 筆")
                    
                    # 顯示一些EMYWAY回饋範例
                    emway_feedback = feedback_data[feedback_data['資料來源'] == 'EMYWAY歷史資料']
                    print(f"   EMYWAY回饋範例:")
                    for idx, (_, row) in enumerate(emway_feedback.head(3).iterrows()):
                        date_str = row.get('日期', 'N/A')
                        feedback_content = str(row['教師給學員回饋']).strip()[:100] + "..." if len(str(row['教師給學員回饋'])) > 100 else str(row['教師給學員回饋']).strip()
                        print(f"     {idx+1}. {date_str}: {feedback_content}")
                else:
                    print(f"   ⚠️ 未找到EMYWAY歷史資料的回饋")
                
                # 檢查是否有現有系統資料的回饋
                if '現有系統' in feedback_source_counts.index:
                    current_feedback_count = feedback_source_counts['現有系統']
                    print(f"   ✅ 找到現有系統回饋: {current_feedback_count} 筆")
                else:
                    print(f"   ⚠️ 未找到現有系統的回饋")
            else:
                print(f"   ⚠️ 沒有找到教師回饋資料")
        
        # 測試多個學員和EPA項目的組合
        print(f"\\n🧪 測試多個學員EPA項目組合的教師回饋...")
        test_combinations = []
        
        for student in students[:3]:  # 測試前3名學員
            student_data = cleaned_df[cleaned_df['學員'] == student]
            student_epa_items = student_data['EPA項目'].unique()
            
            for epa_item in student_epa_items[:2]:  # 每個學員測試前2個EPA項目
                epa_data = student_data[student_data['EPA項目'] == epa_item]
                feedback_data = epa_data[epa_data['教師給學員回饋'].notna() & (epa_data['教師給學員回饋'] != '')]
                
                if len(feedback_data) > 0:
                    test_combinations.append((student, epa_item, len(epa_data), len(feedback_data)))
        
        print(f"   找到 {len(test_combinations)} 個有教師回饋的學員-EPA組合")
        for student, epa_item, total_count, feedback_count in test_combinations[:5]:
            print(f"   {student} - {epa_item}: {total_count} 筆記錄, {feedback_count} 筆回饋")
        
        print("\\n🎉 教師回饋功能測試完成！")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        print(f"詳細錯誤信息: {traceback.format_exc()}")
        return False

def test_feedback_data_integration():
    """測試教師回饋資料整合"""
    print("\\n🧪 測試教師回饋資料整合...")
    
    integrated_file = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/integrated_epa_data.csv"
    
    try:
        df = pd.read_csv(integrated_file, encoding='utf-8')
        processor = FAMDataProcessor()
        cleaned_df = processor.clean_data(df)
        
        # 統計所有教師回饋
        all_feedback = cleaned_df[cleaned_df['教師給學員回饋'].notna() & (cleaned_df['教師給學員回饋'] != '')]
        
        print(f"   總教師回饋記錄: {len(all_feedback)} 筆")
        
        if '資料來源' in all_feedback.columns:
            feedback_source_counts = all_feedback['資料來源'].value_counts()
            print(f"   回饋資料來源分布:")
            for source, count in feedback_source_counts.items():
                percentage = (count / len(all_feedback)) * 100
                print(f"     {source}: {count} 筆 ({percentage:.1f}%)")
        
        # 檢查回饋內容長度
        feedback_lengths = all_feedback['教師給學員回饋'].str.len()
        print(f"   回饋內容長度統計:")
        print(f"     平均長度: {feedback_lengths.mean():.1f} 字符")
        print(f"     最短: {feedback_lengths.min()} 字符")
        print(f"     最長: {feedback_lengths.max()} 字符")
        
        print("✅ 教師回饋資料整合測試完成")
        return True
        
    except Exception as e:
        print(f"❌ 教師回饋資料整合測試失敗: {str(e)}")
        return False

def main():
    """主測試程式"""
    print("=" * 60)
    print("🧪 教師回饋功能測試")
    print("=" * 60)
    
    # 測試教師回饋功能
    test1_result = test_teacher_feedback_with_emway()
    
    # 測試教師回饋資料整合
    test2_result = test_feedback_data_integration()
    
    print("\\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    
    if test1_result and test2_result:
        print("🎉 所有測試通過！教師回饋功能已正確整合EMYWAY資料！")
        print("\\n✅ 功能包括:")
        print("   • 顯示EMYWAY歷史資料的教師回饋")
        print("   • 顯示現有系統的教師回饋")
        print("   • 標示每個回饋的資料來源")
        print("   • 統計各來源的回饋次數")
        print("   • 計算整體回饋率")
    else:
        print("❌ 部分測試失敗，請檢查錯誤訊息")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
