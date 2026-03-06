#!/usr/bin/env python3
"""
測試小兒部評核資料格式
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta

def create_sample_pediatric_data():
    """創建模擬的小兒部評核資料，使用您提供的格式"""
    
    # 模擬您提供的資料格式
    sample_data = {
        '時間戳記': [
            '2025/9/12 上午 11:11:3',
            '2025/9/12 下午 1:26:13',
            '2025/9/11 上午 9:30:00',
            '2025/9/11 下午 2:15:00',
            '2025/9/10 上午 10:45:00'
        ],
        '評核教師': [
            '丁肇壯', '丁肇壯', '林盈秀', '王小明', '丁肇壯'
        ],
        '受評核人員': [
            'R1張三', 'R2李四', 'R1張三', 'R3王五', 'R2李四'
        ],
        '評核項目': [
            '操作技術', '會議報告', '操作技術', '會議報告', '操作技術'
        ],
        '評核技術項目': [
            '插氣管內管（訓練期間最少3次）',
            '腎臟超音波（訓練期間最少5次）',
            '腰椎穿刺（PGY2/R1 訓練期間最少3次）',
            '插中心靜脈導管(CVC)（訓練期間最少3次）',
            '插氣管內管（訓練期間最少3次）'
        ],
        '評核日期': [
            '2025/9/12',
            '2025/9/11', 
            '2025/9/11',
            '2025/9/10',
            '2025/9/10'
        ]
    }
    
    return pd.DataFrame(sample_data)

def process_pediatric_data_test(df):
    """處理小兒部評核資料（測試版本）"""
    processed_df = df.copy()
    
    # 處理評核日期
    if '評核日期' in processed_df.columns:
        st.write("**原始評核日期資料**:")
        st.write(processed_df['評核日期'].head())
        st.write(f"**評核日期資料類型**: {processed_df['評核日期'].dtype}")
        st.write(f"**評核日期非空數量**: {processed_df['評核日期'].notna().sum()}")
        
        # 如果評核日期已經是日期格式，直接使用
        if processed_df['評核日期'].dtype == 'object':
            # 嘗試將字串轉換為日期
            try:
                processed_df['評核日期'] = pd.to_datetime(processed_df['評核日期'], errors='coerce').dt.date
                st.success("✅ 成功將評核日期轉換為日期格式")
            except Exception as e:
                st.warning(f"⚠️ 評核日期轉換錯誤: {str(e)}")
        
        # 顯示處理結果
        st.write(f"**處理後評核日期非空數量**: {processed_df['評核日期'].notna().sum()}")
        if processed_df['評核日期'].notna().any():
            st.write("**成功解析的日期**:")
            st.write(processed_df['評核日期'].dropna().head())
    
    return processed_df

def test_time_trend_with_pediatric_data():
    """使用小兒部資料格式測試時間趨勢"""
    st.title("🧪 小兒部評核資料格式測試")
    
    st.subheader("測試說明")
    st.write("""
    此測試使用您提供的資料格式：
    - 時間戳記: '2025/9/12 上午 11:11:3'
    - 評核日期: '2025/9/12'
    - 包含昨日和今日的資料
    """)
    
    # 創建模擬資料
    df = create_sample_pediatric_data()
    
    st.subheader("原始資料")
    st.dataframe(df, width="stretch")
    
    # 處理資料
    processed_df = process_pediatric_data_test(df)
    
    st.subheader("處理後的資料")
    st.dataframe(processed_df, width="stretch")
    
    # 時間趨勢分析
    if '評核日期' in processed_df.columns and processed_df['評核日期'].notna().any():
        st.subheader("評核時間趨勢")
        
        # 計算每日評核次數
        daily_counts = processed_df.groupby('評核日期').size().reset_index(name='評核次數')
        
        st.write(f"**每日統計**: 共有 {len(daily_counts)} 個不同日期")
        
        # 顯示每日統計表格
        with st.expander("每日評核次數詳情", expanded=True):
            st.dataframe(daily_counts, width="stretch")
        
        # 篩選一週內的資料
        today = date.today()
        week_ago = today - timedelta(days=7)
        
        # 篩選最近一週的資料
        recent_counts = daily_counts[daily_counts['評核日期'] >= week_ago].copy()
        
        if not recent_counts.empty:
            # 確保日期按順序排列
            recent_counts = recent_counts.sort_values('評核日期')
            
            # 創建一週趨勢圖
            fig = px.line(
                recent_counts,
                x='評核日期',
                y='評核次數',
                title="最近一週評核次數趨勢",
                markers=True
            )
            
            # 添加今日標記（如果存在）
            if today in recent_counts['評核日期'].values:
                today_count = recent_counts[recent_counts['評核日期'] == today]['評核次數'].iloc[0]
                fig.add_annotation(
                    x=today,
                    y=today_count,
                    text=f"今日: {today_count}次",
                    showarrow=True,
                    arrowhead=2,
                    arrowcolor="red",
                    bgcolor="yellow"
                )
            
            # 添加昨日標記（如果存在）
            yesterday = today - timedelta(days=1)
            if yesterday in recent_counts['評核日期'].values:
                yesterday_count = recent_counts[recent_counts['評核日期'] == yesterday]['評核次數'].iloc[0]
                fig.add_annotation(
                    x=yesterday,
                    y=yesterday_count,
                    text=f"昨日: {yesterday_count}次",
                    showarrow=True,
                    arrowhead=2,
                    arrowcolor="blue",
                    bgcolor="lightblue"
                )
        else:
            # 如果一週內沒有資料，顯示所有資料
            fig = px.line(
                daily_counts,
                x='評核日期',
                y='評核次數',
                title="所有評核次數趨勢",
                markers=True
            )
        
        st.plotly_chart(fig, width="stretch")
        
        # 顯示統計摘要
        st.subheader("統計摘要")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("總評核次數", len(processed_df))
        
        with col2:
            st.metric("評核日期數", len(daily_counts))
        
        with col3:
            avg_daily = daily_counts['評核次數'].mean()
            st.metric("平均每日評核次數", f"{avg_daily:.1f}")
    
    else:
        st.warning("沒有找到有效的評核日期資料")

def main():
    """主函數"""
    st.set_page_config(
        page_title="小兒部資料格式測試",
        layout="wide"
    )
    
    test_time_trend_with_pediatric_data()

if __name__ == "__main__":
    main()
