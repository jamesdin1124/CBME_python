import streamlit as st
import re
import pandas as pd
from ugy_epa.modules.google_connection import fetch_google_form_data
from ugy_epa.modules.data_processing import (
    process_epa_level, 
    convert_date_to_batch, 
    convert_tw_time
)
from ugy_epa.modules.visualization import plot_radar_chart, plot_trend_chart
# 暫時註解掉不需要的導入
# from ugy_epa.modules.data_analysis import analyze_epa_data

def load_sheet_data(sheet_title=None):
    """載入Google表單資料
    
    Args:
        sheet_title (str, optional): 工作表名稱
        
    Returns:
        tuple: (DataFrame, sheet_titles list)
    """
    df, sheet_titles = fetch_google_form_data(sheet_title=sheet_title)
    return df, sheet_titles

def process_data(df):
    """處理EPA資料
    
    Args:
        df (DataFrame): 原始資料框
        
    Returns:
        DataFrame: 處理後的資料框
    """
    # 預覽df
    st.subheader("資料預覽")
    st.dataframe(df.head(10))
    
    if df is not None:
        # 移除重複欄位
        df = df.loc[:, ~df.columns.duplicated()]
        
        # EPA等級轉換
        df['學員自評EPA等級'] = df['學員自評EPA等級'].apply(process_epa_level)
        df['教師評核EPA等級'] = df['教師評核EPA等級'].apply(process_epa_level)
        
        # 日期轉換和梯次處理
        try:
            # 檢查是否有時間戳記欄位
            if '時間戳記' in df.columns:
                df['評核日期'] = df['時間戳記'].apply(convert_tw_time)
                df['評核日期'] = df['評核日期'].dt.date
            elif '評核日期' in df.columns:
                # 如果已經是日期格式，直接轉換
                df['評核日期'] = pd.to_datetime(df['評核日期']).dt.date
            
            # 將日期轉換為字串格式再轉換梯次
            df['梯次'] = df['評核日期'].astype(str).apply(convert_date_to_batch)
            
            # 顯示除錯信息
            st.write("日期轉換範例：")
            st.write(df[['評核日期', '梯次']].head())
            
        except Exception as e:
            st.error(f"處理時間戳記時發生錯誤：{str(e)}")
            st.write("目前可用的欄位：", df.columns.tolist())
            st.write("評核日期範例：", df['評核日期'].head())
            
    return df

def display_data_preview(df):
    """顯示資料預覽
    
    Args:
        df (DataFrame): 處理後的資料框
    """
    st.subheader("資料預覽")
    st.dataframe(df.head(10))
    
    st.subheader("欄位資訊")
    st.write(f"資料欄位：{', '.join(df.columns.tolist())}")

def display_epa_statistics(df):
    """顯示EPA統計資訊
    
    Args:
        df (DataFrame): 處理後的資料框
    """
    st.subheader("EPA 等級統計")
    st.write("學員自評 EPA 等級分布：")
    st.write(df['學員自評EPA等級'].value_counts().sort_index())
    st.write("教師評核 EPA 等級分布：")
    st.write(df['教師評核EPA等級'].value_counts().sort_index())

def display_visualizations(df):
    """顯示視覺化圖表
    
    Args:
        df (DataFrame): 處理後的資料框
    """
    st.subheader("EPA 評核雷達圖")
    radar_fig = plot_radar_chart(df)
    st.plotly_chart(radar_fig)
    
    st.subheader("EPA 評核趨勢圖")
    trend_fig = plot_trend_chart(df)
    st.plotly_chart(trend_fig)

def show_google_form_import_section():
    """主要應用程式流程"""
    st.title("UGY EPA分析")
    
    try:
        # 載入資料
        df, sheet_titles = load_sheet_data()
        
        if sheet_titles:
            # 工作表選擇
            selected_sheet = st.selectbox(
                "選擇工作表",
                options=sheet_titles,
                key='sheet_selector'
            )
            
            # 重新載入選擇的工作表資料
            df, _ = load_sheet_data(sheet_title=selected_sheet)
            
            if df is not None:
                # 資料處理
                df = process_data(df)
                st.success(f"成功載入並處理 {len(df)} 筆資料！")
                
                # 顯示各項資訊
                display_data_preview(df)
                display_epa_statistics(df)
                display_visualizations(df)
            else:
                st.warning("無法載入所選工作表的資料")
        else:
            st.error("無法獲取工作表列表")
            
    except Exception as e:
        st.error(f"載入資料時發生錯誤：{str(e)}")
        st.exception(e)

if __name__ == "__main__":
    show_google_form_import_section() 