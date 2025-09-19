#!/usr/bin/env python3
"""
測試評核時間趨勢功能
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta

def create_sample_data():
    """創建模擬的評核資料"""
    # 創建包含昨日和今日的資料
    today = date.today()
    yesterday = today - timedelta(days=1)
    day_before = today - timedelta(days=2)
    
    sample_data = {
        '時間戳記': [
            f"{today} 09:30:00",
            f"{today} 14:15:00", 
            f"{today} 16:45:00",
            f"{yesterday} 10:20:00",
            f"{yesterday} 15:30:00",
            f"{day_before} 11:00:00",
            f"{day_before} 13:45:00",
            f"{day_before} 16:20:00"
        ],
        '評核教師': [
            '丁肇壯', '林盈秀', '王小明', '丁肇壯', '林盈秀', 
            '王小明', '丁肇壯', '林盈秀'
        ],
        '受評核人員': [
            'R1張三', 'R2李四', 'R3王五', 'R1張三', 'R2李四',
            'R3王五', 'R1張三', 'R2李四'
        ],
        '評核項目': [
            '操作技術', '會議報告', '操作技術', '會議報告', '操作技術',
            '會議報告', '操作技術', '會議報告'
        ],
        '評核技術項目': [
            '插氣管內管（訓練期間最少3次）',
            '腎臟超音波（訓練期間最少5次）',
            '腰椎穿刺（PGY2/R1 訓練期間最少3次）',
            '插中心靜脈導管(CVC)（訓練期間最少3次）',
            '插氣管內管（訓練期間最少3次）',
            '心臟超音波（訓練期間最少5次）',
            '腰椎穿刺（PGY2/R1 訓練期間最少3次）',
            '插中心靜脈導管(CVC)（訓練期間最少3次）'
        ]
    }
    
    return pd.DataFrame(sample_data)

def process_time_data(df):
    """處理時間資料"""
    processed_df = df.copy()
    
    # 處理時間戳記
    if '時間戳記' in processed_df.columns:
        try:
            processed_df['評核日期'] = pd.to_datetime(processed_df['時間戳記'], errors='coerce')
            processed_df['評核日期'] = processed_df['評核日期'].dt.date
        except Exception as e:
            st.warning(f"時間處理警告: {str(e)}")
            processed_df['評核日期'] = pd.to_datetime(processed_df['時間戳記'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
            processed_df['評核日期'] = processed_df['評核日期'].dt.date
    
    return processed_df

def test_time_trend():
    """測試時間趨勢功能"""
    st.title("🧪 評核時間趨勢測試")
    
    st.subheader("測試說明")
    st.write("""
    此測試展示評核時間趨勢功能，包含：
    - 今日評核資料 (3筆)
    - 昨日評核資料 (2筆)  
    - 前日評核資料 (3筆)
    """)
    
    # 創建模擬資料
    df = create_sample_data()
    processed_df = process_time_data(df)
    
    st.subheader("原始資料")
    st.dataframe(df, use_container_width=True)
    
    st.subheader("處理後的資料")
    st.dataframe(processed_df, use_container_width=True)
    
    # 時間趨勢分析
    if '評核日期' in processed_df.columns:
        st.subheader("評核時間趨勢")
        
        # 檢查評核日期資料
        st.write(f"**資料檢查**: 總共有 {len(processed_df)} 筆記錄")
        st.write(f"**評核日期欄位**: {processed_df['評核日期'].dtype}")
        st.write(f"**非空評核日期**: {processed_df['評核日期'].notna().sum()} 筆")
        
        # 顯示評核日期範圍
        if processed_df['評核日期'].notna().any():
            date_range = f"{processed_df['評核日期'].min()} 至 {processed_df['評核日期'].max()}"
            st.write(f"**日期範圍**: {date_range}")
            
            # 顯示最近的評核記錄
            recent_dates = processed_df['評核日期'].dropna().sort_values(ascending=False).head(5)
            st.write("**最近5筆評核日期**:")
            for date in recent_dates:
                st.write(f"- {date}")
        
        # 計算每日評核次數
        daily_counts = processed_df.groupby('評核日期').size().reset_index(name='評核次數')
        
        if not daily_counts.empty:
            st.write(f"**每日統計**: 共有 {len(daily_counts)} 個不同日期")
            
            # 顯示每日統計表格
            with st.expander("每日評核次數詳情", expanded=True):
                st.dataframe(daily_counts, use_container_width=True)
            
            # 創建趨勢圖
            fig = px.line(
                daily_counts,
                x='評核日期',
                y='評核次數',
                title="每日評核次數趨勢",
                markers=True
            )
            
            # 添加今日和昨日的標記
            today = date.today()
            yesterday = today - timedelta(days=1)
            
            # 添加今日標記
            today_count = daily_counts[daily_counts['評核日期'] == today]['評核次數'].iloc[0] if today in daily_counts['評核日期'].values else 0
            fig.add_annotation(
                x=today,
                y=today_count,
                text=f"今日: {today_count}次",
                showarrow=True,
                arrowhead=2,
                arrowcolor="red",
                bgcolor="yellow"
            )
            
            # 添加昨日標記
            yesterday_count = daily_counts[daily_counts['評核日期'] == yesterday]['評核次數'].iloc[0] if yesterday in daily_counts['評核日期'].values else 0
            fig.add_annotation(
                x=yesterday,
                y=yesterday_count,
                text=f"昨日: {yesterday_count}次",
                showarrow=True,
                arrowhead=2,
                arrowcolor="blue",
                bgcolor="lightblue"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("沒有找到有效的評核日期資料")
    else:
        st.warning("資料中沒有找到「評核日期」欄位")

def main():
    """主函數"""
    st.set_page_config(
        page_title="時間趨勢測試",
        layout="wide"
    )
    
    test_time_trend()

if __name__ == "__main__":
    main()
