#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMYWAY資料整合工具
將轉換後的EMYWAY資料整合到現有系統中
"""

import pandas as pd
import os
from datetime import datetime

class EmwayDataIntegration:
    def __init__(self):
        """初始化整合工具"""
        self.current_data_file = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/EPA匯出原始檔_1140923.csv"
        self.emway_data_file = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/emway_converted_data.csv"
        self.integrated_data_file = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/integrated_epa_data.csv"
    
    def load_current_data(self):
        """載入現有系統資料"""
        try:
            df = pd.read_csv(self.current_data_file, encoding='utf-8')
            print(f"載入現有資料: {len(df)} 筆")
            return df
        except Exception as e:
            print(f"載入現有資料失敗: {str(e)}")
            return pd.DataFrame()
    
    def load_emway_data(self):
        """載入轉換後的EMYWAY資料"""
        try:
            df = pd.read_csv(self.emway_data_file, encoding='utf-8')
            print(f"載入EMYWAY資料: {len(df)} 筆")
            return df
        except Exception as e:
            print(f"載入EMYWAY資料失敗: {str(e)}")
            return pd.DataFrame()
    
    def clean_data(self, df):
        """清理資料"""
        # 移除完全空白的行
        df = df.dropna(how='all')
        
        # 移除沒有學員名稱的行
        df = df[df['學員'].notna() & (df['學員'] != '')]
        
        # 移除沒有EPA項目的行
        df = df[df['EPA項目'].notna() & (df['EPA項目'] != '')]
        
        return df
    
    def standardize_epa_names(self, df):
        """標準化EPA項目名稱，合併相同數字的EPA項目"""
        epa_mapping = {
            # EPA01 - 門診戒菸
            'EPA01.門診戒菸': '01門診戒菸',
            '01門診戒菸': '01門診戒菸',
            
            # EPA02 - 門診/社區衛教
            'EPA02.門診/社區衛教': '02門診/社區衛教',
            'EPA02.門診/社區衛教、': '02門診/社區衛教',
            '02門診/社區衛教': '02門診/社區衛教',
            '02.門診/社區衛教': '02門診/社區衛教',
            '02. 門診/社區衛教': '02門診/社區衛教',
            
            # EPA03 - 預防注射
            'EPA03.預防注射': '03預防注射',
            '03預防注射': '03預防注射',
            '03.預防注射': '03預防注射',
            
            # EPA04 - 旅遊門診
            'EPA04.旅遊門診': '04旅遊門診',
            '04旅遊門診': '04旅遊門診',
            '04.旅遊門診': '04旅遊門診',
            
            # EPA05 - 健康檢查
            'EPA05.健康檢查': '05健康檢查',
            '05健康檢查': '05健康檢查',
            '05.健康檢查': '05健康檢查',
            
            # EPA06 - 社區篩檢
            'EPA06.社區篩檢': '06社區篩檢',
            '06社區篩檢': '06社區篩檢',
            '06.社區篩檢': '06社區篩檢',
            
            # EPA07 - 慢病照護
            'EPA07.慢病照護': '07慢病照護',
            '07慢病照護': '07慢病照護',
            '07.慢病照護': '07慢病照護',
            '07慢病照護': '07慢病照護',
            
            # EPA08 - 急症照護/急症診療
            'EPA08.急症診療': '08急症照護',
            'EPA08.急症照護': '08急症照護',
            '08急症照護': '08急症照護',
            '08急症診療': '08急症照護',
            '08.急症診療': '08急症照護',
            '08.急症照護': '08急症照護',
            
            # EPA09 - 居家整合醫療
            'EPA09.居家整合醫療': '09居家整合醫療',
            '09居家整合醫療': '09居家整合醫療',
            '09.居家整合醫療': '09居家整合醫療',
            
            # EPA10 - 出院準備/照護轉銜
            'EPA10.出院準備/照護轉銜': '10出院準備/照護轉銜',
            '10出院準備/照護轉銜': '10出院準備/照護轉銜',
            '10.出院準備/照護轉銜': '10出院準備/照護轉銜',
            '10.出院準備': '10出院準備/照護轉銜',
            
            # EPA11 - 末病照護/安寧緩和
            'EPA11.末病照護/安寧緩和': '11末病照護/安寧緩和',
            '11末病照護/安寧緩和': '11末病照護/安寧緩和',
            '11.末病照護/安寧緩和': '11末病照護/安寧緩和',
            
            # EPA12 - 悲傷支持/社區照護
            'EPA12.悲傷支持': '12悲傷支持',
            '12悲傷支持': '12悲傷支持',
            '12.悲傷支持': '12悲傷支持',
            '12社區照護': '12社區照護',
            '12.社區照護': '12社區照護'
        }
        
        df['EPA項目'] = df['EPA項目'].map(epa_mapping).fillna(df['EPA項目'])
        return df
    
    def standardize_reliability_scores(self, df):
        """標準化信賴程度評分"""
        reliability_mapping = {
            '教師在旁逐步共同操作': 1,
            '教師在旁必要時協助': 2,
            '教師事後重點確認': 3,
            '必要時知會教師確認': 4,
            '獨立執行': 5,
            '1': 1,
            '2': 2,
            '3': 3,
            '4': 4,
            '5': 5
        }
        
        # 轉換學員自評
        df['信賴程度(學員自評)_數值'] = df['信賴程度(學員自評)'].map(reliability_mapping)
        
        # 轉換教師評量
        df['信賴程度(教師評量)_數值'] = df['信賴程度(教師評量)'].map(reliability_mapping)
        
        return df
    
    def add_data_source_column(self, df, source):
        """新增資料來源欄位"""
        df['資料來源'] = source
        return df
    
    def merge_data(self):
        """合併現有資料和EMYWAY資料"""
        print("開始整合資料...")
        
        # 載入資料
        current_df = self.load_current_data()
        emway_df = self.load_emway_data()
        
        if current_df.empty and emway_df.empty:
            print("沒有資料可整合")
            return pd.DataFrame()
        
        if current_df.empty:
            print("只有EMYWAY資料，直接使用")
            integrated_df = emway_df.copy()
        elif emway_df.empty:
            print("只有現有資料，直接使用")
            integrated_df = current_df.copy()
        else:
            # 合併資料
            print("合併現有資料和EMYWAY資料...")
            integrated_df = pd.concat([current_df, emway_df], ignore_index=True)
        
        # 新增資料來源標記
        if not current_df.empty and not emway_df.empty:
            # 為現有資料標記來源
            current_df['資料來源'] = '現有系統'
            emway_df['資料來源'] = 'EMYWAY歷史資料'
            
            # 重新合併
            integrated_df = pd.concat([current_df, emway_df], ignore_index=True)
        elif not current_df.empty:
            integrated_df['資料來源'] = '現有系統'
        elif not emway_df.empty:
            integrated_df['資料來源'] = 'EMYWAY歷史資料'
        
        # 標準化EPA項目名稱
        print("標準化EPA項目名稱...")
        integrated_df = self.standardize_epa_names(integrated_df)
        
        # 標準化信賴程度評分
        print("標準化信賴程度評分...")
        integrated_df = self.standardize_reliability_scores(integrated_df)
        
        # 清理資料
        print("清理資料...")
        integrated_df = self.clean_data(integrated_df)
        
        # 顯示標準化後的EPA項目統計
        if not integrated_df.empty:
            epa_counts = integrated_df['EPA項目'].value_counts()
            print(f"標準化後EPA項目數: {len(epa_counts)}")
            print("前10個EPA項目:")
            for epa, count in epa_counts.head(10).items():
                print(f"  {epa}: {count} 筆")
        
        print(f"整合完成！總共 {len(integrated_df)} 筆資料")
        return integrated_df
    
    def save_integrated_data(self, df):
        """儲存整合後的資料"""
        if df.empty:
            print("沒有資料可儲存")
            return
        
        # 備份現有檔案
        if os.path.exists(self.integrated_data_file):
            backup_file = f"{self.integrated_data_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename(self.integrated_data_file, backup_file)
            print(f"已備份原檔案至: {backup_file}")
        
        # 儲存整合後的資料
        df.to_csv(self.integrated_data_file, index=False, encoding='utf-8-sig')
        print(f"整合後的資料已儲存至: {self.integrated_data_file}")
        
        # 顯示統計資訊
        self.print_statistics(df)
    
    def print_statistics(self, df):
        """顯示統計資訊"""
        print(f"\n=== 整合資料統計 ===")
        print(f"總筆數: {len(df)}")
        
        if '資料來源' in df.columns:
            print(f"\n資料來源分布:")
            source_counts = df['資料來源'].value_counts()
            for source, count in source_counts.items():
                print(f"  {source}: {count} 筆")
        
        print(f"\n學員統計:")
        student_counts = df['學員'].value_counts()
        print(f"  總學員數: {len(student_counts)}")
        print(f"  前5名學員:")
        for student, count in student_counts.head().items():
            print(f"    {student}: {count} 筆")
        
        print(f"\nEPA項目統計:")
        epa_counts = df['EPA項目'].value_counts()
        print(f"  EPA項目數: {len(epa_counts)}")
        for epa, count in epa_counts.items():
            print(f"    {epa}: {count} 筆")
        
        # 日期統計
        valid_dates = df[df['日期'].notna() & (df['日期'] != '')]['日期']
        if not valid_dates.empty:
            print(f"\n日期範圍: {valid_dates.min()} ~ {valid_dates.max()}")
        
        # 信賴程度統計
        if '信賴程度(教師評量)_數值' in df.columns:
            reliability_stats = df['信賴程度(教師評量)_數值'].dropna()
            if not reliability_stats.empty:
                print(f"\n教師評量信賴程度統計:")
                print(f"  平均: {reliability_stats.mean():.2f}")
                print(f"  中位數: {reliability_stats.median():.2f}")
                print(f"  分數分布:")
                score_counts = reliability_stats.value_counts().sort_index()
                for score, count in score_counts.items():
                    print(f"    {score}分: {count} 筆")

def main():
    """主程式"""
    integrator = EmwayDataIntegration()
    
    # 整合資料
    integrated_df = integrator.merge_data()
    
    # 儲存結果
    if not integrated_df.empty:
        integrator.save_integrated_data(integrated_df)
        
        # 顯示前幾筆資料作為預覽
        print(f"\n=== 資料預覽 (前5筆) ===")
        preview_columns = ['學員', 'EPA項目', '日期', '診斷', '信賴程度(教師評量)', '資料來源']
        available_columns = [col for col in preview_columns if col in integrated_df.columns]
        print(integrated_df[available_columns].head())
    else:
        print("整合失敗")

if __name__ == "__main__":
    main()
