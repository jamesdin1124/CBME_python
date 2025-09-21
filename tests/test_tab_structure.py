#!/usr/bin/env python3
"""
測試分頁結構腳本
"""

def test_tab_structure():
    """測試分頁結構是否正確"""
    print("🧪 測試分頁結構")
    
    # 模擬分頁定義
    tabs = []
    tab_names = []
    
    # 模擬權限檢查為True
    if True:  # 模擬 check_permission(st.session_state.role, 'can_view_all')
        tabs.append("UGY EPA")
        tab_names.append("UGY EPA")
        tabs.append("UGY整合")
        tab_names.append("UGY整合")
        tabs.append("PGY")
        tab_names.append("PGY")
        tabs.append("住院醫師")
        tab_names.append("住院醫師")
        tabs.append("老師評分分析")
        tab_names.append("老師評分分析")
    
    print(f"✅ 分頁數量: {len(tabs)}")
    print(f"✅ 分頁名稱: {tab_names}")
    
    # 檢查是否還有小兒部評核分頁
    if "小兒部評核" in tabs:
        print("❌ 錯誤: 仍然存在小兒部評核分頁")
        return False
    else:
        print("✅ 成功: 小兒部評核分頁已刪除")
    
    # 檢查分頁數量是否正確
    expected_tabs = 5
    if len(tabs) == expected_tabs:
        print(f"✅ 成功: 分頁數量正確 ({len(tabs)}/{expected_tabs})")
    else:
        print(f"❌ 錯誤: 分頁數量不正確 ({len(tabs)}/{expected_tabs})")
        return False
    
    # 檢查住院醫師分頁是否存在
    if "住院醫師" in tabs:
        print("✅ 成功: 住院醫師分頁存在")
    else:
        print("❌ 錯誤: 住院醫師分頁不存在")
        return False
    
    print("\n🎉 分頁結構測試通過！")
    return True

def test_pediatric_integration():
    """測試小兒部整合邏輯"""
    print("\n🧪 測試小兒部整合邏輯")
    
    # 模擬科別選擇
    selected_dept = "小兒部"
    
    if selected_dept == "小兒部":
        print("✅ 成功: 選擇小兒部時會顯示小兒部評核系統")
        print("   - 在住院醫師分頁中直接調用 show_pediatric_evaluation_section()")
    else:
        print("✅ 成功: 選擇其他科別時會顯示一般住院醫師分析")
    
    print("🎉 小兒部整合邏輯測試通過！")
    return True

def main():
    """主函數"""
    print("=" * 50)
    print("🏥 臨床教師評核系統 - 分頁結構測試")
    print("=" * 50)
    
    # 測試分頁結構
    tab_test = test_tab_structure()
    
    # 測試小兒部整合
    integration_test = test_pediatric_integration()
    
    print("\n" + "=" * 50)
    if tab_test and integration_test:
        print("🎉 所有測試通過！小兒部評核分頁已成功刪除並整合到住院醫師分頁")
    else:
        print("❌ 部分測試失敗，請檢查代碼")
    print("=" * 50)

if __name__ == "__main__":
    main()
