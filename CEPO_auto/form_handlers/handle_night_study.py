from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import sys


def handle_night_study(driver):
    """
    處理『夜間學習紀錄_縱貫組』相關表單（含W1、W2...），自動搜尋所有分頁並點擊。
    :param driver: Selenium WebDriver 實例
    """
    print("開始搜尋『夜間學習紀錄_縱貫組』表單...")
    found = False
    page_count = 0  # 分頁計數器，最多搜尋 10 頁
    while page_count < 10:
        # 取得所有表單列
        rows = driver.find_elements(By.CSS_SELECTOR, '#todoFormTable tbody tr')
        for row in rows:
            try:
                # 取得表單名稱連結
                form_link = row.find_element(By.CSS_SELECTOR, 'td:nth-child(1) a')
                form_name = form_link.text.strip()
                # 判斷是否為夜間學習紀錄_縱貫組開頭
                if form_name.startswith('夜間學習紀錄_縱貫組'):
                    print(f"找到表單：{form_name}，自動點擊...")
                    original_window = driver.current_window_handle  # 記錄原本分頁
                    before_windows = driver.window_handles
                    form_link.click()
                    found = True
                    time.sleep(2)  # 可依實際情況調整
                    # 等待新分頁開啟並切換
                    WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > len(before_windows))
                    new_windows = driver.window_handles
                    for handle in new_windows:
                        if handle not in before_windows:
                            driver.switch_to.window(handle)
                            break
                    # 進入新分頁後，先滾動到網頁底部，再等待並點擊指定按鈕
                    try:
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(1)
                        submit_btn = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, '//*[@id=\"btnDiv\"]/div[1]/div/input[4]'))
                        )
                        submit_btn.click()
                        print("已自動滾動並點擊表單內指定按鈕（如儲存/送出）")
                        time.sleep(2)
                    except Exception as btn_error:
                        print("自動點擊表單內按鈕失敗：", str(btn_error))
                    # 關閉新分頁並切回原本分頁
                    
                    driver.switch_to.window(original_window)
                    time.sleep(4)
                    # 切回清單分頁後，自動點擊表單提交完成訊息的確認按鈕
                    try:
                        print("等待『表單提交完成!』訊息彈窗出現...", file=sys.stderr)
                        # 先等彈窗可見，再等按鈕可點擊
                        WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located((By.XPATH, '//*[@id="body-container"]/div[14]/div[2]/div/div/div/div/div[4]/button'))
                        )
                        confirm_btn = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, '//*[@id="body-container"]/div[14]/div[2]/div/div/div/div/div[4]/button'))
                        )
                        confirm_btn.click()
                        print("已自動點擊『表單提交完成!』訊息的確認按鈕")
                        time.sleep(1)
                    except Exception as confirm_error:
                        print("自動點擊提交完成確認按鈕失敗：", str(confirm_error))
                    # 重新取得表單列表
                    break
            except Exception as e:
                continue
        page_count += 1  # 每循環一次分頁就加一
        # 若本頁沒找到或已處理完畢，檢查是否有下一頁
        try:
            next_btn = driver.find_element(By.LINK_TEXT, '下一頁')
            # 檢查按鈕是否可點擊（未 disabled）
            if 'disabled' in next_btn.get_attribute('class'):
                break  # 已到最後一頁
            else:
                next_btn.click()
                time.sleep(2)
        except Exception:
            break  # 沒有下一頁按鈕，結束
    if page_count >= 10:
        print("已達到最多搜尋 10 頁的限制，自動結束分頁搜尋。")
    if not found:
        print("未找到任何『夜間學習紀錄_縱貫組』表單。")
    else:
        print("所有『夜間學習紀錄_縱貫組』表單已處理完畢。") 