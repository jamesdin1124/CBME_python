import pandas as pd
import numpy as np
from datetime import datetime, date
import re

class FAMDataProcessor:
    """家醫部EPA資料處理器"""
    
    def __init__(self):
        self.epa_requirements = {
            '02門診/社區衛教': {'minimum': 10, 'description': '訓練期間最少10次'},
            '03預防注射': {'minimum': 15, 'description': '訓練期間最少15次'},
            '05健康檢查': {'minimum': 20, 'description': '訓練期間最少20次'},
            '07慢病照護': {'minimum': 25, 'description': '訓練期間最少25次'},
            '08急症照護': {'minimum': 15, 'description': '訓練期間最少15次'},
            '09居家整合醫療': {'minimum': 10, 'description': '訓練期間最少10次'},
            '11末病照護/安寧緩和': {'minimum': 5, 'description': '訓練期間最少5次'},
            '12家庭醫學科住院照護': {'minimum': 30, 'description': '訓練期間最少30次'},
            '13家庭醫學科門診照護': {'minimum': 40, 'description': '訓練期間最少40次'},
            '14社區醫學實習': {'minimum': 8, 'description': '訓練期間最少8次'},
            '15預防醫學與健康促進': {'minimum': 10, 'description': '訓練期間最少10次'},
            '16家庭醫學科急診照護': {'minimum': 20, 'description': '訓練期間最少20次'},
            '17長期照護': {'minimum': 5, 'description': '訓練期間最少5次'},
            '18家庭醫學科研習': {'minimum': 15, 'description': '訓練期間最少15次'}
        }
        
        # 信賴程度對應表
        self.reliability_mapping = {
            '獨立執行': 5,
            '必要時知會教師確認': 4,
            '教師在旁必要時協助': 3,
            '教師在旁逐步共同操作': 2,
            '學員在旁觀察': 1,
            '不允許學員觀察': 0
        }
        
        # 複雜程度對應表
        self.complexity_mapping = {
            '高': 3,
            '中': 2,
            '低': 1
        }
    
    def apply_default_filters(self, df, debug=False):
        """應用家醫部住院醫師的預設過濾條件"""
        if debug:
            print(f"🔍 過濾前資料形狀: {df.shape}")
        
        # 創建資料副本
        filtered_df = df.copy()
        
        # 第一步：過濾日期為空白的記錄
        if '日期' in filtered_df.columns:
            filtered_df['日期'] = pd.to_datetime(filtered_df['日期'], errors='coerce')
            before_date_filter = len(filtered_df)
            filtered_df = filtered_df.dropna(subset=['日期'])
            after_date_filter = len(filtered_df)
            if debug:
                print(f"  日期過濾: {before_date_filter} → {after_date_filter} (過濾掉 {before_date_filter - after_date_filter} 筆)")
        
        # 第二步：過濾EPA項目為空白的記錄
        if not filtered_df.empty and 'EPA項目' in filtered_df.columns:
            before_epa_filter = len(filtered_df)
            filtered_df = filtered_df[
                filtered_df['EPA項目'].notna() & 
                (filtered_df['EPA項目'] != '') & 
                (filtered_df['EPA項目'] != 'nan')
            ].copy()
            after_epa_filter = len(filtered_df)
            if debug:
                print(f"  EPA項目過濾: {before_epa_filter} → {after_epa_filter} (過濾掉 {before_epa_filter - after_epa_filter} 筆)")
        
        # 第三步：過濾信賴程度(教師評量)為無效值的記錄
        if not filtered_df.empty and '信賴程度(教師評量)' in filtered_df.columns:
            before_reliability_filter = len(filtered_df)
            filtered_df = filtered_df[
                filtered_df['信賴程度(教師評量)'].notna() & 
                (filtered_df['信賴程度(教師評量)'] != '') & 
                (filtered_df['信賴程度(教師評量)'] != 'nan') &
                (filtered_df['信賴程度(教師評量)'] != '請選擇') &
                (filtered_df['信賴程度(教師評量)'] != '信賴程度(教師評量)') &
                (filtered_df['信賴程度(教師評量)'] != '信賴程度（教師評量）')
            ].copy()
            after_reliability_filter = len(filtered_df)
            if debug:
                print(f"  信賴程度過濾: {before_reliability_filter} → {after_reliability_filter} (過濾掉 {before_reliability_filter - after_reliability_filter} 筆)")
        
        # 第四步：過濾學員欄位為"學員"的記錄
        if not filtered_df.empty and '學員' in filtered_df.columns:
            before_student_filter = len(filtered_df)
            filtered_df = filtered_df[
                filtered_df['學員'].notna() & 
                (filtered_df['學員'] != '') & 
                (filtered_df['學員'] != 'nan') &
                (filtered_df['學員'] != '學員')
            ].copy()
            after_student_filter = len(filtered_df)
            if debug:
                print(f"  學員欄位過濾: {before_student_filter} → {after_student_filter} (過濾掉 {before_student_filter - after_student_filter} 筆)")
        
        if debug:
            print(f"✅ 過濾完成，最終資料形狀: {filtered_df.shape}")
        
        return filtered_df

    def clean_data(self, df, debug=False):
        """清理原始資料"""
        if debug:
            print(f"🔍 清理前資料形狀: {df.shape}")

        # 創建資料副本以避免SettingWithCopyWarning
        df = df.copy()
        
        # 移除完全空白的行
        df = df.dropna(how='all')
        if debug:
            print(f"🧹 移除空白行後: {df.shape}")
        
        # 處理日期欄位
        date_columns = ['表單派送日期', '應完成日期', '日期']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # 清理EPA項目欄位 - 保留所有記錄，只清理格式
        if 'EPA項目' in df.columns:
            original_count = len(df)
            
            # 檢查是否有 EPA項目 [原始] 欄位，如果有則合併兩個欄位的資料
            if 'EPA項目 [原始]' in df.columns:
                if debug:
                    print(f"🔧 發現 EPA項目 [原始] 欄位，開始合併EPA項目資料")
                
                # 合併EPA項目和EPA項目 [原始]的資料
                for idx, row in df.iterrows():
                    epa_main = str(row['EPA項目']).strip()
                    epa_original = str(row['EPA項目 [原始]']).strip()
                    
                    # 如果主要EPA項目為空或無效，使用原始EPA項目
                    if epa_main in ['nan', 'None', ''] and epa_original not in ['nan', 'None', '']:
                        df.at[idx, 'EPA項目'] = str(epa_original)  # 確保是字符串類型
                        if debug:
                            print(f"  記錄 {idx}: 使用原始EPA項目 '{epa_original}'")
                    
                    # 如果原始EPA項目有資料但主要EPA項目為空，也使用原始EPA項目
                    elif epa_original not in ['nan', 'None', ''] and epa_main in ['nan', 'None', '']:
                        df.at[idx, 'EPA項目'] = str(epa_original)  # 確保是字符串類型
                        if debug:
                            print(f"  記錄 {idx}: 使用原始EPA項目 '{epa_original}'")
                
                # 保存原始EPA項目資料
                df['EPA項目_原始'] = df['EPA項目'].copy()
            else:
                # 先保存原始EPA項目資料
                df['EPA項目_原始'] = df['EPA項目'].copy()
            
            # 清理格式但不移除任何記錄
            df['EPA項目'] = df['EPA項目'].astype(str).str.strip()
            df['EPA項目'] = df['EPA項目'].replace(['nan', 'None'], '')
            
            # 標準化EPA項目格式
            df = self._standardize_epa_format(df, debug)
            
            # 如果EPA項目欄位為空，嘗試從診斷內容推斷EPA項目
            if '診斷' in df.columns:
                df = self._infer_epa_items_from_diagnosis(df, debug)

            # 檢查EPA項目的分佈
            if debug:
                epa_counts = df['EPA項目'].value_counts()
                print(f"🎯 EPA項目分佈 (前10個): {epa_counts.head(10).to_dict()}")
                print(f"🎯 空EPA項目的記錄數: {len(df[df['EPA項目'] == ''])}")

            # 不過濾任何記錄，保留所有資料
            if debug:
                print(f"🎯 EPA項目清理後: {len(df)} 筆記錄 (保留所有記錄)")
        
        # 清理學員姓名 - 保留所有記錄，只清理格式
        if '學員' in df.columns:
            original_count = len(df)
            df['學員'] = df['學員'].astype(str).str.strip()
            df['學員'] = df['學員'].replace(['nan', 'None'], '')

            # 檢查學員的分佈
            if debug:
                student_counts = df['學員'].value_counts()
                print(f"👥 學員分佈: {student_counts.head(10).to_dict()}")
                print(f"👥 空學員姓名的記錄數: {len(df[df['學員'] == ''])}")

            # 不過濾任何記錄，保留所有資料
            if debug:
                print(f"👥 學員清理後: {len(df)} 筆記錄 (保留所有記錄)")
        else:
            # 如果沒有學員欄位，為測試目的創建一個虛擬學員欄位
            if debug:
                print("⚠️ 沒有找到學員欄位，創建虛擬學員欄位用於測試")
            df['學員'] = '測試學員'  # 為所有記錄添加相同的學員名稱
        
        # 清理教師簽名
        if '教師簽名' in df.columns:
            df['教師簽名'] = df['教師簽名'].astype(str).str.strip()
            df['教師簽名'] = df['教師簽名'].replace(['nan', ''], np.nan)
        
        # 清理信賴程度欄位
        reliability_columns = ['信賴程度(學員自評)', '信賴程度(教師評量)']
        for col in reliability_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace(['nan', ''], np.nan)
                
                # 為信賴程度欄位添加數值版本
                if col == '信賴程度(教師評量)':
                    df['信賴程度(教師評量)_數值'] = df[col].apply(self._convert_reliability_to_numeric)
        
        # 清理複雜程度欄位
        if '複雜程度' in df.columns:
            df['複雜程度'] = df['複雜程度'].astype(str).str.strip()
            df['複雜程度'] = df['複雜程度'].replace(['nan', ''], np.nan)
        
        # 計算EPA分數（信賴程度數值）
        if '信賴程度(教師評量)' in df.columns:
            df['信賴程度(教師評量)_數值'] = df['信賴程度(教師評量)'].apply(self._convert_reliability_to_numeric)
            if debug:
                numeric_count = df['信賴程度(教師評量)_數值'].notna().sum()
                print(f"🔢 EPA分數計算完成: {numeric_count} 筆記錄有數值分數")
        
        if debug:
            print(f"✅ 資料清理完成，最終資料形狀: {df.shape}")
        
        # 應用預設過濾條件
        filtered_df = self.apply_default_filters(df, debug)
        
        return filtered_df
    
    def _convert_reliability_to_numeric(self, reliability_text):
        """將信賴程度文字轉換為數值（5分制）"""
        if pd.isna(reliability_text) or reliability_text == '':
            return None
        
        reliability_text = str(reliability_text).strip()
        
        # 如果已經是數字，直接返回
        try:
            num_value = float(reliability_text)
            if 1 <= num_value <= 5:
                return num_value
        except (ValueError, TypeError):
            pass
        
        # 信賴程度數值映射（5分制）
        reliability_mapping = {
            '獨立執行': 5.0,
            '必要時知會教師確認': 4.0,
            '教師事後重點確認': 3.0,
            '教師在旁必要時協助': 2.0,
            '教師在旁逐步共同操作': 1.0,
            '學員在旁觀察': 0.0,
            '不允許學員觀察': 0.0,
            '請選擇': 0.0
        }
        
        return reliability_mapping.get(reliability_text, None)
    
    def get_student_list(self, df):
        """取得住院醫師清單"""
        if '學員' in df.columns:
            return sorted(df['學員'].unique())
        return []
    
    def get_epa_items(self, df):
        """取得EPA項目清單"""
        if 'EPA項目' in df.columns:
            epa_items = df['EPA項目'].unique()
            # 過濾掉空值和空字串
            valid_epa_items = [item for item in epa_items if pd.notna(item) and str(item).strip() and str(item).strip() != '']
            return sorted(valid_epa_items)
        return []
    
    def calculate_monthly_epa_trend(self, epa_data, epa_item):
        """計算EPA項目的月度趨勢數據
        
        Args:
            epa_data: 單一EPA項目的資料
            epa_item: EPA項目名稱
            
        Returns:
            pd.DataFrame: 包含月份和平均信賴程度的趨勢數據
        """
        try:
            if epa_data.empty or '日期' not in epa_data.columns:
                return None
            
            # 複製資料並處理日期
            trend_df = epa_data.copy()
            
            # 轉換日期格式
            trend_df['日期'] = pd.to_datetime(trend_df['日期'], errors='coerce')
            
            # 移除無效日期
            trend_df = trend_df.dropna(subset=['日期'])
            
            if trend_df.empty:
                return None
            
            # 創建年月欄位（YYYY-MM格式）
            trend_df['年月'] = trend_df['日期'].dt.to_period('M')
            
            # 按年月分組計算平均信賴程度
            monthly_stats = []
            
            for period in trend_df['年月'].unique():
                period_data = trend_df[trend_df['年月'] == period]
                
                # 計算該月的平均信賴程度
                reliability_scores = []
                for _, row in period_data.iterrows():
                    # 優先使用已計算的數值欄位
                    if '信賴程度(教師評量)_數值' in row:
                        score = row['信賴程度(教師評量)_數值']
                        if pd.notna(score):
                            reliability_scores.append(score)
                    else:
                        # 如果沒有數值欄位，使用文字轉換
                        reliability = row['信賴程度(教師評量)']
                        if pd.notna(reliability) and str(reliability).strip():
                            score = self._convert_reliability_to_numeric(str(reliability).strip())
                            if score is not None:
                                reliability_scores.append(score)
                
                if reliability_scores:
                    monthly_stats.append({
                        '年月': str(period),
                        '年月_顯示': f"{period.year}年{period.month:02d}月",
                        '平均信賴程度': sum(reliability_scores) / len(reliability_scores),
                        '評核次數': len(period_data),
                        'EPA項目': epa_item
                    })
            
            if not monthly_stats:
                return None
            
            # 轉換為DataFrame並排序
            monthly_df = pd.DataFrame(monthly_stats)
            monthly_df = monthly_df.sort_values('年月')
            
            # 重置索引
            monthly_df = monthly_df.reset_index(drop=True)
            
            return monthly_df
            
        except Exception as e:
            print(f"計算月度EPA趨勢時發生錯誤: {e}")
            return None
    
    def get_student_data(self, df, student_name):
        """取得特定住院醫師的資料"""
        if '學員' in df.columns:
            return df[df['學員'] == student_name].copy()
        return pd.DataFrame()
    
    def calculate_epa_progress(self, student_data):
        """計算EPA項目完成進度"""
        progress_data = []
        
        for epa_item, requirements in self.epa_requirements.items():
            epa_records = student_data[student_data['EPA項目'] == epa_item]
            completed_count = len(epa_records)
            required_count = requirements['minimum']
            completion_rate = (completed_count / required_count * 100) if required_count > 0 else 0
            
            progress_data.append({
                'EPA項目': epa_item,
                '已完成次數': completed_count,
                '要求次數': required_count,
                '完成率(%)': completion_rate,
                '狀態': '✅ 已完成' if completed_count >= required_count else '⚠️ 未完成',
                '描述': requirements['description']
            })
        
        return pd.DataFrame(progress_data)
    
    def calculate_reliability_progress(self, student_data):
        """計算信賴程度進度"""
        if '信賴程度(教師評量)' not in student_data.columns:
            return None
        
        reliability_data = student_data['信賴程度(教師評量)'].dropna()
        reliability_data = reliability_data[reliability_data != '']
        
        if reliability_data.empty:
            return None
        
        # 統計各信賴程度次數
        reliability_counts = reliability_data.value_counts()
        
        # 計算平均信賴程度
        reliability_scores = [self.reliability_mapping.get(level, 0) for level in reliability_data]
        avg_reliability = np.mean(reliability_scores) if reliability_scores else 0
        
        return {
            'counts': reliability_counts,
            'average': avg_reliability,
            'distribution': reliability_counts.to_dict()
        }
    
    def get_complexity_analysis(self, student_data):
        """分析複雜度分布"""
        if '複雜程度' not in student_data.columns:
            return None
        
        complexity_data = student_data['複雜程度'].dropna()
        complexity_data = complexity_data[complexity_data != '']
        
        if complexity_data.empty:
            return None
        
        complexity_counts = complexity_data.value_counts()
        
        # 計算平均複雜度
        complexity_scores = [self.complexity_mapping.get(level, 0) for level in complexity_data]
        avg_complexity = np.mean(complexity_scores) if complexity_scores else 0
        
        return {
            'counts': complexity_counts,
            'average': avg_complexity,
            'distribution': complexity_counts.to_dict()
        }
    
    def get_temporal_progress(self, student_data):
        """取得時間序列進度"""
        if '日期' not in student_data.columns:
            return None
        
        # 清理日期資料
        student_data = student_data.copy()
        student_data['日期'] = pd.to_datetime(student_data['日期'], errors='coerce')
        student_data = student_data.dropna(subset=['日期'])
        
        if student_data.empty:
            return None
        
        # 按月統計
        student_data['月份'] = student_data['日期'].dt.to_period('M')
        monthly_stats = student_data.groupby('月份').agg({
            'EPA項目': 'count',
            '複雜程度': lambda x: x.value_counts().to_dict() if not x.empty else {}
        }).rename(columns={'EPA項目': '評核次數'})
        
        # 計算累積進度
        monthly_stats['累積次數'] = monthly_stats['評核次數'].cumsum()
        
        return monthly_stats.reset_index()
    
    def get_epa_temporal_progress(self, student_data, epa_item):
        """取得特定EPA項目的時間進度"""
        if 'EPA項目' not in student_data.columns or '日期' not in student_data.columns:
            return None
        
        epa_data = student_data[student_data['EPA項目'] == epa_item].copy()
        
        if epa_data.empty:
            return None
        
        # 清理日期資料
        epa_data['日期'] = pd.to_datetime(epa_data['日期'], errors='coerce')
        epa_data = epa_data.dropna(subset=['日期'])
        epa_data = epa_data.sort_values('日期')
        
        if epa_data.empty:
            return None
        
        # 計算累積完成次數
        epa_data['累積次數'] = range(1, len(epa_data) + 1)
        
        # 如果有信賴程度資料，計算信賴程度變化
        if '信賴程度(教師評量)' in epa_data.columns:
            reliability_scores = []
            for _, row in epa_data.iterrows():
                reliability = row['信賴程度(教師評量)']
                score = self.reliability_mapping.get(reliability, 0)
                reliability_scores.append(score)
            epa_data['信賴程度數值'] = reliability_scores
        
        return epa_data
    
    def get_teacher_feedback_analysis(self, student_data):
        """分析教師回饋"""
        if '教師給學員回饋' not in student_data.columns:
            return None
        
        feedback_data = student_data['教師給學員回饋'].dropna()
        feedback_data = feedback_data[feedback_data != '']
        
        if feedback_data.empty:
            return None
        
        # 分析回饋內容
        feedback_stats = {
            'total_count': len(feedback_data),
            'recent_feedbacks': feedback_data.tail(5).tolist(),
            'all_feedbacks': feedback_data.tolist()
        }
        
        # 如果有日期資料，按時間排序
        if '日期' in student_data.columns:
            feedback_with_date = student_data[student_data['教師給學員回饋'].notna()].copy()
            feedback_with_date = feedback_with_date[feedback_with_date['教師給學員回饋'] != '']
            
            if not feedback_with_date.empty:
                feedback_with_date['日期'] = pd.to_datetime(feedback_with_date['日期'], errors='coerce')
                feedback_with_date = feedback_with_date.dropna(subset=['日期'])
                feedback_with_date = feedback_with_date.sort_values('日期', ascending=False)
                
                feedback_stats['recent_feedbacks_with_date'] = feedback_with_date[['日期', '教師給學員回饋']].head(5).to_dict('records')
        
        return feedback_stats
    
    def get_overall_statistics(self, df):
        """取得整體統計資料"""
        stats = {
            'total_records': len(df),
            'unique_students': df['學員'].nunique() if '學員' in df.columns else 0,
            'unique_epa_items': df['EPA項目'].nunique() if 'EPA項目' in df.columns else 0,
            'unique_teachers': df['教師簽名'].nunique() if '教師簽名' in df.columns else 0,
            'date_range': None
        }
        
        # 計算日期範圍
        if '日期' in df.columns:
            date_range = df['日期'].dropna()
            if not date_range.empty:
                stats['date_range'] = {
                    'start': date_range.min(),
                    'end': date_range.max(),
                    'span_days': (date_range.max() - date_range.min()).days
                }
        
        return stats
    
    def get_epa_distribution(self, df):
        """取得EPA項目分布"""
        if 'EPA項目' not in df.columns:
            return None
        
        epa_counts = df['EPA項目'].value_counts()
        return epa_counts
    
    def get_student_distribution(self, df):
        """取得住院醫師分布"""
        if '學員' not in df.columns:
            return None
        
        student_counts = df['學員'].value_counts()
        return student_counts
    
    def get_complexity_distribution(self, df):
        """取得複雜度分布"""
        if '複雜程度' not in df.columns:
            return None
        
        complexity_counts = df['複雜程度'].value_counts()
        return complexity_counts
    
    def export_student_report(self, student_data, student_name):
        """匯出住院醫師報告"""
        report = {
            'student_name': student_name,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'basic_stats': {
                'total_evaluations': len(student_data),
                'unique_epa_items': student_data['EPA項目'].nunique() if 'EPA項目' in student_data.columns else 0,
                'date_range': None
            },
            'epa_progress': None,
            'reliability_analysis': None,
            'complexity_analysis': None,
            'temporal_progress': None
        }
        
        # EPA進度
        report['epa_progress'] = self.calculate_epa_progress(student_data).to_dict('records')
        
        # 信賴程度分析
        report['reliability_analysis'] = self.calculate_reliability_progress(student_data)
        
        # 複雜度分析
        report['complexity_analysis'] = self.get_complexity_analysis(student_data)
        
        # 時間進度
        report['temporal_progress'] = self.get_temporal_progress(student_data)
        
        # 日期範圍
        if '日期' in student_data.columns:
            date_range = student_data['日期'].dropna()
            if not date_range.empty:
                report['basic_stats']['date_range'] = {
                    'start': date_range.min().strftime('%Y-%m-%d'),
                    'end': date_range.max().strftime('%Y-%m-%d')
                }
        
        return report
    
    def _standardize_epa_format(self, df, debug=False):
        """標準化EPA項目格式"""
        # EPA項目格式對應表（支援多種格式）
        epa_format_mapping = {
            # 數字開頭格式（根據您提供的清單）
            '01門診戒菸': 'EPA01.門診戒菸',
            '02門診/社區衛教': 'EPA02.門診/社區衛教',
            '03預防注射': 'EPA03.預防注射',
            '04旅遊門診': 'EPA04.旅遊門診',
            '05健康檢查': 'EPA05.健康檢查',
            '07慢病照護': 'EPA07.慢病照護',
            '08急症照護': 'EPA08.急症診療',
            '08急症診療': 'EPA08.急症診療',
            '09居家整合醫療': 'EPA09.居家整合醫療',
            '10出院準備/照護轉銜': 'EPA10.出院準備/照護轉銜',
            '11末病照護/安寧緩和': 'EPA11.末病照護/安寧緩和',
            '12悲傷支持': 'EPA12.悲傷支持',
            # 已經有EPA開頭的保持不變
            'EPA01.門診戒菸': 'EPA01.門診戒菸',
            'EPA02.門診/社區衛教': 'EPA02.門診/社區衛教',
            'EPA03.預防注射': 'EPA03.預防注射',
            'EPA04.旅遊門診': 'EPA04.旅遊門診',
            'EPA05.健康檢查': 'EPA05.健康檢查',
            'EPA07.慢病照護': 'EPA07.慢病照護',
            'EPA08.急症診療': 'EPA08.急症診療',
            'EPA09.居家整合醫療': 'EPA09.居家整合醫療',
            'EPA10.出院準備/照護轉銜': 'EPA10.出院準備/照護轉銜',
            'EPA11.末病照護/安寧緩和': 'EPA11.末病照護/安寧緩和',
            'EPA12.悲傷支持': 'EPA12.悲傷支持'
        }
        
        # 統計格式標準化結果
        standardization_stats = {}
        
        for idx, row in df.iterrows():
            epa_item = str(row['EPA項目']).strip()
            if epa_item in epa_format_mapping:
                standardized_epa = epa_format_mapping[epa_item]
                df.at[idx, 'EPA項目'] = standardized_epa
                standardization_stats[epa_item] = standardization_stats.get(epa_item, 0) + 1
        
        if debug and standardization_stats:
            print(f"🔧 EPA項目格式標準化: {standardization_stats}")
        
        return df
    
    def _infer_epa_items_from_diagnosis(self, df, debug=False):
        """從診斷內容推斷EPA項目"""
        # EPA項目推斷規則
        epa_inference_rules = {
            # 預防注射相關
            'EPA03.預防注射': [
                'vaccine', 'vaccination', 'immunization', 'influenza vaccine', 
                'HPV', 'MMR', 'PCV', 'JE', 'yellow fever', '疫苗', '注射'
            ],
            # 急症照護相關
            'EPA08.急症診療': [
                'acute', 'emergency', 'respiratory infection', 'bronchiolitis',
                'sepsis', 'stroke', 'myocardial infarction', '急症', '急性'
            ],
            # 慢病照護相關
            'EPA07.慢病照護': [
                'diabetes', 'hypertension', 'hyperlipidemia', 'dementia',
                'parkinson', 'chronic', 'DM', 'HTN', '慢病', '慢性'
            ],
            # 健康檢查相關
            'EPA05.健康檢查': [
                'health exam', 'check-up', 'screening', '健檢', '健康檢查'
            ],
            # 出院準備相關
            'EPA10.出院準備/照護轉銜': [
                'discharge', 'transition', '出院', '轉銜', 'bipolar', 'suicide'
            ],
            # 處理格式不一致的EPA10
            '10出院準備/照護轉銜': [
                'discharge', 'transition', '出院', '轉銜', 'bipolar', 'suicide'
            ],
            # 居家整合醫療
            'EPA09.居家整合醫療': [
                'home', '居家', 'home care'
            ],
            # 末病照護/安寧緩和
            'EPA11.末病照護/安寧緩和': [
                'palliative', 'hospice', 'end of life', '安寧', '緩和'
            ],
            # 悲傷支持
            'EPA12.悲傷支持': [
                'grief', 'bereavement', '悲傷', '哀傷'
            ],
            # 旅遊門診
            'EPA04.旅遊門診': [
                'travel', 'malaria', 'altitude', '旅遊', '出國'
            ]
        }
        
        # 統計推斷結果
        inference_stats = {}
        
        for idx, row in df.iterrows():
            if pd.notna(row['EPA項目']) and str(row['EPA項目']).strip():
                continue  # 如果EPA項目已有值，跳過
                
            diagnosis = str(row.get('診斷', '')).lower()
            if not diagnosis or diagnosis in ['nan', 'none']:
                continue
                
            # 嘗試匹配EPA項目
            matched_epa = None
            for epa_item, keywords in epa_inference_rules.items():
                for keyword in keywords:
                    if keyword.lower() in diagnosis:
                        matched_epa = epa_item
                        break
                if matched_epa:
                    break
            
            if matched_epa:
                df.at[idx, 'EPA項目'] = matched_epa
                inference_stats[matched_epa] = inference_stats.get(matched_epa, 0) + 1
        
        if debug and inference_stats:
            print(f"🔍 從診斷推斷EPA項目: {inference_stats}")
        
        return df
