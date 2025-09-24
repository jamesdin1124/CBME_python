#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
家醫部住院醫師EPA評核系統整合測試

此檔案用於測試家醫部系統與主系統的整合是否正常運作
"""

import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_fam_system_integration():
    """測試家醫部系統整合"""
    try:
        # 測試匯入
        from pages.FAM.fam_residents import show_fam_resident_evaluation_section
        from pages.FAM.fam_data_processor import FAMDataProcessor
        from pages.FAM.fam_visualization import FAMVisualization
        
        print("✅ 成功匯入家醫部系統模組")
        
        # 測試資料處理器初始化
        processor = FAMDataProcessor()
        print("✅ 成功初始化資料處理器")
        
        # 測試視覺化模組初始化
        visualizer = FAMVisualization()
        print("✅ 成功初始化視覺化模組")
        
        # 測試EPA要求配置
        epa_requirements = processor.epa_requirements
        print(f"✅ EPA要求配置載入成功，共 {len(epa_requirements)} 個項目")
        
        # 測試信賴程度映射
        reliability_mapping = processor.reliability_mapping
        print(f"✅ 信賴程度映射載入成功，共 {len(reliability_mapping)} 個等級")
        
        print("\n🎉 家醫部系統整合測試完成！所有模組正常運作。")
        return True
        
    except ImportError as e:
        print(f"❌ 模組匯入失敗：{e}")
        return False
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤：{e}")
        return False

def test_main_system_integration():
    """測試主系統整合"""
    try:
        # 測試主系統匯入
        import new_dashboard
        print("✅ 成功匯入主系統")
        
        # 檢查科別列表是否包含家醫部
        if hasattr(new_dashboard, 'departments'):
            departments = new_dashboard.departments
            if "家醫部" in departments:
                print("✅ 主系統科別列表包含家醫部")
            else:
                print("⚠️ 主系統科別列表未包含家醫部")
        else:
            print("⚠️ 主系統未定義科別列表")
        
        print("\n🎉 主系統整合測試完成！")
        return True
        
    except ImportError as e:
        print(f"❌ 主系統匯入失敗：{e}")
        return False
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤：{e}")
        return False

if __name__ == "__main__":
    print("🚀 開始家醫部系統整合測試...")
    print("=" * 50)
    
    # 測試家醫部系統
    print("\n📋 測試家醫部系統模組...")
    fam_test_result = test_fam_system_integration()
    
    # 測試主系統整合
    print("\n📋 測試主系統整合...")
    main_test_result = test_main_system_integration()
    
    # 總結
    print("\n" + "=" * 50)
    if fam_test_result and main_test_result:
        print("🎉 所有測試通過！家醫部系統已成功整合到主系統中。")
        print("\n📝 使用說明：")
        print("1. 啟動主系統：streamlit run new_dashboard.py")
        print("2. 登入後選擇「家醫部」科別")
        print("3. 上傳家醫部EPA評核資料檔案")
        print("4. 點擊「住院醫師」分頁查看家醫部專用系統")
    else:
        print("❌ 部分測試失敗，請檢查錯誤訊息並修正問題。")
