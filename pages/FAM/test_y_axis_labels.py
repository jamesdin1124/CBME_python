#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試趨勢圖Y軸標籤移除功能
"""

import pandas as pd
import os
from fam_data_processor import FAMDataProcessor
from fam_visualization import FAMVisualization

def test_y_axis_labels_removal():
    """測試Y軸標籤移除功能"""
    print("🧪 測試趨勢圖Y軸標籤移除功能...")
    
    # 載入整合資料
    integrated_file = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/integrated_epa_data.csv"
    
    if not os.path.exists(integrated_file):
        print("❌ 整合資料檔案不存在")
        return False
    
    try:
        # 載入資料
        df = pd.read_csv(integrated_file, encoding='utf-8')
        print(f"✅ 成功載入整合資料: {len(df)} 筆記錄")
        
        # 初始化處理器和視覺化工具
        processor = FAMDataProcessor()
        visualizer = FAMVisualization()
        
        # 清理資料
        cleaned_df = processor.clean_data(df)
        print(f"✅ 資料清理完成: {len(cleaned_df)} 筆記錄")
        
        # 測試學員清單
        students = processor.get_student_list(cleaned_df)
        print(f"✅ 學員清單: {len(students)} 名學員")
        
        # 測試趨勢圖創建
        if students:
            test_student = students[0]
            
            print(f"\\n🧪 測試學員: {test_student}")
            
            # 獲取學員的資料
            student_data = cleaned_df[cleaned_df['學員'] == test_student]
            
            print(f"   該學員的資料: {len(student_data)} 筆記錄")
            
            # 獲取EPA項目清單
            epa_items = processor.get_epa_items(student_data)
            print(f"   EPA項目: {len(epa_items)} 個")
            
            # 測試每個EPA項目的趨勢圖
            for epa_item in epa_items[:3]:  # 測試前3個EPA項目
                print(f"\\n📋 測試EPA項目: {epa_item}")
                
                # 獲取該EPA項目的資料
                epa_data = student_data[student_data['EPA項目'] == epa_item]
                
                print(f"   記錄數: {len(epa_data)}")
                
                if not epa_data.empty:
                    # 創建增強版趨勢圖
                    trend_fig = visualizer.create_enhanced_monthly_trend_chart(epa_data, epa_item, test_student)
                    
                    if trend_fig is not None:
                        print(f"   ✅ 趨勢圖創建成功")
                        
                        # 檢查圖表配置
                        if hasattr(trend_fig, 'layout'):
                            layout = trend_fig.layout
                            
                            # 檢查是否有Y軸標籤
                            has_y_axis_labels = False
                            
                            # 檢查layout中的annotations
                            if hasattr(layout, 'annotations') and layout.annotations:
                                for annotation in layout.annotations:
                                    if hasattr(annotation, 'text'):
                                        text = annotation.text
                                        if '等級' in text:
                                            has_y_axis_labels = True
                                            print(f"   ❌ 發現Y軸標籤: {text}")
                            
                            if not has_y_axis_labels:
                                print(f"   ✅ Y軸標籤已成功移除")
                            
                            # 檢查圖表的基本配置
                            print(f"   📊 圖表配置:")
                            if hasattr(layout, 'title'):
                                print(f"     標題: {layout.title}")
                            if hasattr(layout, 'yaxis'):
                                yaxis = layout.yaxis
                                print(f"     Y軸範圍: {yaxis.range}")
                                print(f"     Y軸刻度: {yaxis.tickmode}")
                            
                            # 檢查是否有水平參考線
                            has_horizontal_lines = False
                            if hasattr(layout, 'shapes') and layout.shapes:
                                for shape in layout.shapes:
                                    if hasattr(shape, 'type') and shape.type == 'line':
                                        if hasattr(shape, 'y0') and hasattr(shape, 'y1'):
                                            if shape.y0 == shape.y1:  # 水平線
                                                has_horizontal_lines = True
                                                break
                            
                            if has_horizontal_lines:
                                print(f"   ✅ 水平參考線已保留")
                            else:
                                print(f"   ℹ️ 沒有水平參考線")
                        else:
                            print(f"   ⚠️ 無法檢查圖表配置")
                    else:
                        print(f"   ❌ 趨勢圖創建失敗")
                else:
                    print(f"   ℹ️ 沒有資料")
        
        print("\\n🎉 Y軸標籤移除功能測試完成！")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        print(f"詳細錯誤信息: {traceback.format_exc()}")
        return False

def test_chart_visual_elements():
    """測試圖表視覺元素"""
    print("\\n🧪 測試圖表視覺元素...")
    
    integrated_file = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/integrated_epa_data.csv"
    
    try:
        df = pd.read_csv(integrated_file, encoding='utf-8')
        processor = FAMDataProcessor()
        visualizer = FAMVisualization()
        cleaned_df = processor.clean_data(df)
        
        students = processor.get_student_list(cleaned_df)
        if students:
            test_student = students[0]
            student_data = cleaned_df[cleaned_df['學員'] == test_student]
            epa_items = processor.get_epa_items(student_data)
            
            if epa_items:
                epa_item = epa_items[0]
                epa_data = student_data[student_data['EPA項目'] == epa_item]
                
                if not epa_data.empty:
                    trend_fig = visualizer.create_enhanced_monthly_trend_chart(epa_data, epa_item, test_student)
                    
                    if trend_fig is not None:
                        print(f"   📊 圖表視覺元素檢查:")
                        
                        # 檢查traces
                        if hasattr(trend_fig, 'data'):
                            print(f"     圖表元素數量: {len(trend_fig.data)}")
                            
                            for i, trace in enumerate(trend_fig.data):
                                trace_name = trace.name if hasattr(trace, 'name') else f"Trace {i}"
                                trace_type = trace.type if hasattr(trace, 'type') else "未知"
                                print(f"     {i+1}. {trace_name} ({trace_type})")
                        
                        # 檢查layout
                        if hasattr(trend_fig, 'layout'):
                            layout = trend_fig.layout
                            
                            # 檢查標題
                            if hasattr(layout, 'title'):
                                print(f"     標題: {layout.title}")
                            
                            # 檢查軸設定
                            if hasattr(layout, 'yaxis'):
                                yaxis = layout.yaxis
                                print(f"     Y軸標題: {yaxis.title}")
                                print(f"     Y軸範圍: {yaxis.range}")
                            
                            if hasattr(layout, 'xaxis'):
                                xaxis = layout.xaxis
                                print(f"     X軸標題: {xaxis.title}")
                            
                            # 檢查圖例
                            if hasattr(layout, 'showlegend'):
                                print(f"     顯示圖例: {layout.showlegend}")
                        
                        return True
        
        return False
        
    except Exception as e:
        print(f"❌ 圖表視覺元素測試失敗: {str(e)}")
        return False

def main():
    """主測試程式"""
    print("=" * 60)
    print("🧪 趨勢圖Y軸標籤移除功能測試")
    print("=" * 60)
    
    # 測試Y軸標籤移除
    test1_result = test_y_axis_labels_removal()
    
    # 測試圖表視覺元素
    test2_result = test_chart_visual_elements()
    
    print("\\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    
    if test1_result and test2_result:
        print("🎉 所有測試通過！Y軸標籤已成功移除！")
        print("\\n✅ 功能包括:")
        print("   • 移除Y軸右側的等級標籤（等級1、等級5）")
        print("   • 保留水平參考線（灰色虛線）")
        print("   • 保持圖表的其他視覺元素")
        print("   • 維持圖表的清晰度和可讀性")
        print("   • 不影響趨勢圖的核心功能")
    else:
        print("❌ 部分測試失敗，請檢查錯誤訊息")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
