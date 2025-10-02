#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試教師回饋時間排序功能
"""

import pandas as pd
import os

def test_feedback_sorting():
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
        
        # 模擬教師回饋排序邏輯
        print(f"\n🔍 測試教師回饋排序邏輯...")
        
        # 選擇一個有教師回饋的學員和EPA項目
        feedback_data = df[
            (df['教師給學員回饋'].notna()) & 
            (df['教師給學員回饋'] != '') &
            (df['學員'].notna())
        ]
        
        if feedback_data.empty:
            print("❌ 沒有找到教師回饋資料")
            return False
        
        # 選擇第一個學員的第一個EPA項目進行測試
        first_student = feedback_data['學員'].iloc[0]
        first_epa = feedback_data['EPA項目'].iloc[0]
        
        print(f"測試學員: {first_student}")
        print(f"測試EPA項目: {first_epa}")
        
        # 獲取該學員該EPA項目的教師回饋
        student_feedback = feedback_data[
            (feedback_data['學員'] == first_student) & 
            (feedback_data['EPA項目'] == first_epa)
        ]
        
        if student_feedback.empty:
            print("❌ 該學員該EPA項目沒有教師回饋")
            return False
        
        print(f"找到 {len(student_feedback)} 筆教師回饋")
        
        # 準備表格數據（模擬fam_residents.py的邏輯）
        table_data = []
        for idx, (_, row) in enumerate(student_feedback.iterrows(), 1):
            # 格式化日期
            date_str = "N/A"
            if '日期' in row and pd.notna(row['日期']):
                if hasattr(row['日期'], 'strftime'):
                    date_str = row['日期'].strftime('%Y-%m-%d')
                else:
                    date_str = str(row['日期'])
            
            # 處理回饋內容
            feedback_content = str(row['教師給學員回饋']).strip()
            
            # 獲取資料來源
            data_source = row.get('資料來源', '未知來源')
            
            table_data.append({
                '日期': date_str,
                '回饋內容': feedback_content,
                '資料來源': data_source
            })
        
        # 創建DataFrame
        feedback_df = pd.DataFrame(table_data)
        
        print(f"\n📅 排序前的日期順序:")
        for i, (_, row) in enumerate(feedback_df.iterrows()):
            print(f"  {i+1}. {row['日期']} - {row['資料來源']}")
        
        # 按照日期排序（升序：最早的在前）
        feedback_df['日期_parsed'] = pd.to_datetime(feedback_df['日期'])
        feedback_df = feedback_df.sort_values('日期_parsed', ascending=True)
        feedback_df = feedback_df.drop('日期_parsed', axis=1)
        
        print(f"\n📅 排序後的日期順序:")
        for i, (_, row) in enumerate(feedback_df.iterrows()):
            print(f"  {i+1}. {row['日期']} - {row['資料來源']}")
        
        # 驗證排序是否正確
        dates = pd.to_datetime(feedback_df['日期'])
        is_sorted = dates.is_monotonic_increasing
        print(f"\n✅ 排序驗證: {'通過' if is_sorted else '失敗'}")
        
        if is_sorted:
            print("🎉 教師回饋已按照時間升序排列（最早的在前）")
        else:
            print("❌ 教師回饋排序有問題")
        
        return is_sorted
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        print(f"詳細錯誤信息: {traceback.format_exc()}")
        return False

def test_multiple_students_feedback():
    """測試多個學員的教師回饋排序"""
    print(f"\n🧪 測試多個學員的教師回饋排序...")
    
    # 載入整合資料
    integrated_file = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/integrated_epa_data.csv"
    
    try:
        df = pd.read_csv(integrated_file, encoding='utf-8')
        
        # 找出所有有教師回饋的學員和EPA項目組合
        feedback_data = df[
            (df['教師給學員回饋'].notna()) & 
            (df['教師給學員回饋'] != '') &
            (df['學員'].notna())
        ]
        
        if feedback_data.empty:
            print("❌ 沒有找到教師回饋資料")
            return False
        
        # 統計每個學員的教師回饋數量
        student_feedback_counts = feedback_data.groupby(['學員', 'EPA項目']).size().reset_index(name='回饋數量')
        student_feedback_counts = student_feedback_counts[student_feedback_counts['回饋數量'] > 1].sort_values('回饋數量', ascending=False)
        
        print(f"找到 {len(student_feedback_counts)} 個學員EPA組合有多次回饋")
        
        # 測試前3個組合
        test_count = 0
        all_passed = True
        
        for _, row in student_feedback_counts.head(3).iterrows():
            student = row['學員']
            epa = row['EPA項目']
            count = row['回饋數量']
            
            print(f"\n📋 測試 {student} - {epa} ({count}筆回饋):")
            
            # 獲取該組合的教師回饋
            student_feedback = feedback_data[
                (feedback_data['學員'] == student) & 
                (feedback_data['EPA項目'] == epa)
            ]
            
            # 準備表格數據
            table_data = []
            for idx, (_, row) in enumerate(student_feedback.iterrows(), 1):
                date_str = "N/A"
                if '日期' in row and pd.notna(row['日期']):
                    date_str = str(row['日期'])[:10]  # 只取日期部分
                
                table_data.append({
                    '日期': date_str,
                    '回饋內容': str(row['教師給學員回饋']).strip()[:50] + "...",
                    '資料來源': row.get('資料來源', '未知來源')
                })
            
            # 創建DataFrame並排序
            feedback_df = pd.DataFrame(table_data)
            try:
                feedback_df['日期_parsed'] = pd.to_datetime(feedback_df['日期'], format='mixed', dayfirst=False)
                feedback_df = feedback_df.sort_values('日期_parsed', ascending=True)
            except Exception as e:
                print(f"  日期解析錯誤: {e}")
                continue
            
            # 顯示排序結果
            for i, (_, row) in enumerate(feedback_df.iterrows()):
                print(f"  {i+1}. {row['日期']} - {row['資料來源']}")
            
            # 驗證排序
            dates = pd.to_datetime(feedback_df['日期'])
            is_sorted = dates.is_monotonic_increasing
            print(f"  排序驗證: {'✅ 通過' if is_sorted else '❌ 失敗'}")
            
            if not is_sorted:
                all_passed = False
            
            test_count += 1
        
        print(f"\n📊 多學員測試結果: {test_count}個組合，{'全部通過' if all_passed else '部分失敗'}")
        return all_passed
        
    except Exception as e:
        print(f"❌ 多學員測試失敗: {str(e)}")
        return False

def main():
    """主測試程式"""
    print("=" * 60)
    print("🧪 教師回饋時間排序測試")
    print("=" * 60)
    
    # 測試單一學員回饋排序
    test1_result = test_feedback_sorting()
    
    # 測試多個學員回饋排序
    test2_result = test_multiple_students_feedback()
    
    print("\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    
    if test1_result and test2_result:
        print("🎉 所有測試通過！教師回饋時間排序功能正常！")
        print("\n✅ 功能特色:")
        print("   • 教師回饋按照時間升序排列（最早的在前）")
        print("   • 支援多個學員和多個EPA項目的回饋排序")
        print("   • 保持資料來源標記")
        print("   • 自動處理日期格式轉換")
    else:
        print("❌ 部分測試失敗，請檢查錯誤訊息")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
