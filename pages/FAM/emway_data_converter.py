#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMYWAY資料格式轉換工具
將舊格式的EMYWAY資料轉換為新系統格式
"""

import pandas as pd
import os
import glob
from datetime import datetime
import re

class EmwayDataConverter:
    def __init__(self):
        """初始化轉換器"""
        # EPA項目對應表
        self.epa_mapping = {
            'EPA1': '01門診戒菸',
            'EPA2': '02門診/社區衛教',
            'EPA3': '03健康檢查',
            'EPA4': '04預防接種',
            'EPA5': '05門診診療',
            'EPA6': '06急診診療',
            'EPA7': '07住院診療',
            'EPA8': '08急重症照護',
            'EPA9': '09手術',
            'EPA10': '10出院準備/照護轉銜',
            'EPA11': '11末病照護/安寧緩和',
            'EPA12': '12社區照護'
        }
        
        # 新格式欄位對應
        self.new_format_columns = [
            '臨床訓練計畫',
            '組別', 
            '階段/子階段',
            '訓練階段科部',
            '訓練階段期間',
            '學員',
            '學員帳號',
            '表單簽核流程',
            '表單派送日期',
            '應完成日期',
            '日期',
            'EPA項目',
            '受評醫師',
            '病歷號碼',
            '個案姓名',
            '診斷',
            '複雜程度',
            '觀察場域',
            '信賴程度(學員自評)',
            '信賴程度(教師評量)',
            '教師給學員回饋',
            '教師簽名',
            '教師給CCC回饋(僅CCC委員可讀，對學員隱藏)'
        ]
    
    def extract_student_name(self, folder_name):
        """從資料夾名稱提取學員姓名"""
        # 從 "CEPO併Emyway EPA統計分析(含統計圖)_張玄穎" 提取 "張玄穎"（最後三個字符）
        match = re.search(r'_([^/]+)/?$', folder_name)
        if match:
            full_name = match.group(1)
            # 提取最後三個字符作為學員姓名
            if len(full_name) >= 3:
                return full_name[-3:]
            else:
                return full_name
        return "未知學員"
    
    def extract_epa_number(self, filename):
        """從檔案名稱提取EPA編號"""
        # 從 "EPA1-表格 1.csv" 提取 "EPA1"
        match = re.search(r'(EPA\d+)', filename)
        if match:
            return match.group(1)
        return None
    
    def parse_signature_flow(self, signature_text):
        """解析表單簽核流程"""
        if pd.isna(signature_text) or signature_text == '':
            return "", "", ""
        
        # 解析格式: "張玄穎/DOC12013(2025-03-07 18:34) → 孫于珊/DOC10685(2025-03-10 13:44)"
        pattern = r'([^/]+)/([^(]+)\(([^)]+)\)\s*→\s*([^/]+)/([^(]+)\(([^)]+)\)'
        match = re.search(pattern, signature_text)
        
        if match:
            student_name = match.group(1).strip()
            student_id = match.group(2).strip()
            teacher_name = match.group(4).strip()
            return student_name, student_id, teacher_name
        else:
            # 簡單格式: "楊惠芳"
            return signature_text.strip(), "", ""
    
    def convert_reliability_score(self, score):
        """轉換信賴程度分數"""
        if pd.isna(score) or score == '' or score == 'X':
            return ""
        
        # 將分數轉換為描述
        score_mapping = {
            1: '教師在旁逐步共同操作',
            2: '教師在旁必要時協助',
            3: '教師事後重點確認',
            4: '必要時知會教師確認',
            5: '獨立執行'
        }
        
        try:
            score_int = int(float(score))
            return score_mapping.get(score_int, str(score_int))
        except (ValueError, TypeError):
            return str(score) if score else ""
    
    def determine_complexity(self, diagnosis):
        """根據診斷判斷複雜程度"""
        if pd.isna(diagnosis) or diagnosis == '':
            return ""
        
        # 簡單的複雜程度判斷邏輯
        high_complexity_keywords = ['OHCA', 'STEMI', 'cancer', 'carcinoma', 'hypertension']
        medium_complexity_keywords = ['GERD', 'polyp', 'diabetes']
        
        diagnosis_lower = str(diagnosis).lower()
        
        for keyword in high_complexity_keywords:
            if keyword.lower() in diagnosis_lower:
                return '高'
        
        for keyword in medium_complexity_keywords:
            if keyword.lower() in diagnosis_lower:
                return '中'
        
        return '低'
    
    def determine_observation_field(self, epa_number, diagnosis):
        """判斷觀察場域"""
        if pd.isna(diagnosis) or diagnosis == '':
            return ""
        
        # 根據EPA項目和診斷判斷場域
        if epa_number in ['EPA1', 'EPA2', 'EPA3', 'EPA4', 'EPA5']:
            return '門診'
        elif epa_number in ['EPA6', 'EPA7', 'EPA8', 'EPA9']:
            return '住院'
        elif epa_number in ['EPA10', 'EPA11', 'EPA12']:
            return '社區'
        else:
            return '門診'
    
    def convert_csv_file(self, file_path, student_name):
        """轉換單一CSV檔案"""
        try:
            # 讀取CSV檔案
            df = pd.read_csv(file_path, encoding='utf-8')
            
            if df.empty:
                return pd.DataFrame()
            
            # 提取EPA編號
            filename = os.path.basename(file_path)
            epa_number = self.extract_epa_number(filename)
            epa_name = self.epa_mapping.get(epa_number, f'{epa_number}')
            
            # 創建新格式的DataFrame
            converted_data = []
            
            for _, row in df.iterrows():
                # 跳過標題行
                if row.iloc[0] == '表單簽核流程':
                    continue
                
                # 解析表單簽核流程
                signature_flow = row.iloc[0] if len(row) > 0 else ""
                student_name_parsed, student_id, teacher_name = self.parse_signature_flow(signature_flow)
                
                # 優先使用資料夾名稱中的學員姓名，確保一致性
                student_name_parsed = student_name
                
                # 提取各欄位資料
                date = row.iloc[1] if len(row) > 1 else ""
                epa = row.iloc[2] if len(row) > 2 else epa_name
                patient_id = row.iloc[3] if len(row) > 3 else ""
                patient_name = row.iloc[4] if len(row) > 4 else ""
                diagnosis = row.iloc[5] if len(row) > 5 else ""
                student_self_eval = row.iloc[6] if len(row) > 6 else ""
                teacher_eval = row.iloc[7] if len(row) > 7 else ""
                teacher_feedback = row.iloc[8] if len(row) > 8 else ""
                teacher_ccc_feedback = row.iloc[9] if len(row) > 9 else ""
                
                # 轉換資料格式
                converted_row = {
                    '臨床訓練計畫': '2024家庭醫學專科醫師EPA訓練計畫',
                    '組別': '',
                    '階段/子階段': '',
                    '訓練階段科部': '家庭暨社區醫學部',
                    '訓練階段期間': '2024-01-01 ~ 2024-12-31',
                    '學員': student_name_parsed,
                    '學員帳號': student_id,
                    '表單簽核流程': signature_flow,
                    '表單派送日期': date,
                    '應完成日期': date,
                    '日期': date,
                    'EPA項目': epa,
                    '受評醫師': student_name_parsed,
                    '病歷號碼': patient_id,
                    '個案姓名': patient_name,
                    '診斷': diagnosis,
                    '複雜程度': self.determine_complexity(diagnosis),
                    '觀察場域': self.determine_observation_field(epa_number, diagnosis),
                    '信賴程度(學員自評)': self.convert_reliability_score(student_self_eval),
                    '信賴程度(教師評量)': self.convert_reliability_score(teacher_eval),
                    '教師給學員回饋': teacher_feedback,
                    '教師簽名': teacher_name,
                    '教師給CCC回饋(僅CCC委員可讀，對學員隱藏)': teacher_ccc_feedback
                }
                
                converted_data.append(converted_row)
            
            return pd.DataFrame(converted_data)
            
        except Exception as e:
            print(f"轉換檔案 {file_path} 時發生錯誤: {str(e)}")
            return pd.DataFrame()
    
    def convert_student_folder(self, folder_path):
        """轉換單一學員資料夾"""
        student_name = self.extract_student_name(os.path.basename(folder_path))
        print(f"正在轉換學員: {student_name}")
        
        all_converted_data = []
        
        # 找到所有EPA CSV檔案
        csv_files = glob.glob(os.path.join(folder_path, "EPA*.csv"))
        csv_files.sort()  # 按EPA編號排序
        
        for csv_file in csv_files:
            print(f"  處理檔案: {os.path.basename(csv_file)}")
            converted_df = self.convert_csv_file(csv_file, student_name)
            if not converted_df.empty:
                all_converted_data.append(converted_df)
        
        if all_converted_data:
            return pd.concat(all_converted_data, ignore_index=True)
        else:
            return pd.DataFrame()
    
    def convert_all_data(self, emway_folder_path):
        """轉換所有EMYWAY資料"""
        print("開始轉換EMYWAY資料...")
        
        all_data = []
        
        # 找到所有學員資料夾
        student_folders = glob.glob(os.path.join(emway_folder_path, "CEPO併Emyway EPA統計分析(含統計圖)_*"))
        
        for folder in student_folders:
            converted_df = self.convert_student_folder(folder)
            if not converted_df.empty:
                all_data.append(converted_df)
        
        if all_data:
            final_df = pd.concat(all_data, ignore_index=True)
            print(f"轉換完成！共處理 {len(final_df)} 筆資料")
            return final_df
        else:
            print("沒有找到可轉換的資料")
            return pd.DataFrame()
    
    def save_converted_data(self, df, output_path):
        """儲存轉換後的資料"""
        if df.empty:
            print("沒有資料可儲存")
            return
        
        # 確保輸出目錄存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 儲存為CSV
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"轉換後的資料已儲存至: {output_path}")
        
        # 顯示統計資訊
        print(f"\n轉換統計:")
        print(f"- 總筆數: {len(df)}")
        print(f"- 學員數: {df['學員'].nunique()}")
        print(f"- EPA項目數: {df['EPA項目'].nunique()}")
        # 過濾有效日期並顯示範圍
        valid_dates = df[df['日期'].notna() & (df['日期'] != '')]['日期']
        if not valid_dates.empty:
            print(f"- 日期範圍: {valid_dates.min()} ~ {valid_dates.max()}")
        else:
            print("- 日期範圍: 無有效日期")

def main():
    """主程式"""
    converter = EmwayDataConverter()
    
    # 設定路徑
    emway_folder = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/EMYWAY資料"
    output_file = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/emway_converted_data.csv"
    
    # 轉換資料
    converted_df = converter.convert_all_data(emway_folder)
    
    # 儲存結果
    if not converted_df.empty:
        converter.save_converted_data(converted_df, output_file)
        
        # 顯示前幾筆資料作為預覽
        print(f"\n資料預覽 (前5筆):")
        print(converted_df[['學員', 'EPA項目', '日期', '診斷', '信賴程度(教師評量)']].head())
    else:
        print("轉換失敗或沒有資料")

if __name__ == "__main__":
    main()
