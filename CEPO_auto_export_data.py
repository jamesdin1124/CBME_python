from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time

# 設定 Chrome 選項
chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

# 初始化瀏覽器
driver = webdriver.Chrome(options=chrome_options)

try:
    # 前往登入頁面
    driver.get("https://cts.tsgh.ndmctsgh.edu.tw/")  # 請替換成實際的登入頁面網址
    
    # 等待帳號輸入框出現並填入帳號
    username_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "loginName"))
    )
    username_input.send_keys("DOC31024")
    
    # 等待密碼輸入框出現並填入密碼
    password_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "loginPin"))
    )
    password_input.send_keys("N124509119!")
    
    # 等待登入按鈕出現並點擊
    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-primary.block.full-width.m-b.btn-lg"))
    )
    login_button.click()
    
    # 等待確認按鈕出現並點擊
    try:
        confirm_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-default"))
        )
        confirm_button.click()
        print("已點擊確認按鈕")
    except Exception as confirm_error:
        print("沒有發現確認按鈕或點擊失敗：", str(confirm_error))
    
    # 等待並點擊學員專區
    student_area = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'nav-label') and text()='學員專區']"))
    )
    student_area.click()
    print("已點擊學員專區")
    
    # 等待選單展開（等待 2 秒）
    time.sleep(2)
    
    try:
        # 找到側邊欄
        sidebar = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "side-menu"))
        )
        
        # 移動到側邊欄
        actions = ActionChains(driver)
        actions.move_to_element(sidebar).perform()
        print("已移動到側邊欄")
        
        # 使用 JavaScript 滾動到訓練計畫表單匯出的位置
        scroll_script = """
        var targetLink = document.querySelector("a[href='report/common/planFormExport']");
        if (targetLink) {
            targetLink.scrollIntoView(true);
            var sidebar = document.getElementById('side-menu');
            sidebar.scrollTop = sidebar.scrollTop - 50;  // 往上調整一點，確保完全可見
        }
        """
        driver.execute_script(scroll_script)
        print("已滾動到目標位置")
        
        # 等待滾動完成
        time.sleep(1)
        
        # 點擊訓練計畫表單匯出
        export_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@href='report/common/planFormExport']"))
        )
        export_link.click()
        print("已點擊訓練計畫表單匯出")
        
    except Exception as submenu_error:
        print("操作失敗：", str(submenu_error))
    
    # 等待頁面載入
    time.sleep(3)
    
    try:
        # 使用字典定義每個計劃對應的表單清單
        plan_form_dict = {
            "(五年級)西醫實習醫學生(UGY)訓練計畫第一年(五年級)_M120": [
            "實習醫學生coreEPAs評量表 ",
            "迷你臨床演練評量（Mini-CEX）",
            "夜間學習紀錄",
            "臨床核心技能 1-23 新生兒的檢查",
            "臨床核心技能 1-24 接觸以及檢查兒童的能力",
            "臨床核心技能 1-25兒童發展評量",
            "臨床核心技能 1-28 身高體重的量測",
            "臨床核心技能 5-4 兒童劑量的換算",
            "三軍總醫院教學住診紀錄_W1",
            "三軍總醫院教學住診紀錄_W2",
            "三軍總醫院教學住診紀錄_W3",
            "三軍總醫院教學住診紀錄_W4", 
            "三軍總醫院教學門診紀錄"
            
            ],
            "(六年級)西醫實習醫學生(UGY)訓練計畫第二年_M119期班使用": [
            "實習醫學生coreEPAs評量表 ",
            "迷你臨床演練評量（Mini-CEX）",
            "夜間學習紀錄",
            "三軍總醫院教學住診紀錄_W1",
            "三軍總醫院教學住診紀錄_W2", 
            "三軍總醫院教學門診紀錄",
            "三軍總醫院教學門診紀錄"
            ]
        }
        
        # 對每個訓練計劃進行循環

        # 修改第一個輸入：訓練類別
        type_dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "select2-jobTypeId-container"))
        )
        type_dropdown.click()
        time.sleep(1)
        
        type_search = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input.select2-search__field"))
        )
        type_search.send_keys("西醫UGY")
        time.sleep(1)
        type_search.send_keys(Keys.ENTER)
        print("已選擇訓練類別")
        
        time.sleep(1)


        for plan_name, form_list in plan_form_dict.items():
            # 選擇訓練計劃
            plan_dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "select2-planTargetId-container"))
            )
            plan_dropdown.click()
            time.sleep(1)
            
            plan_search = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input.select2-search__field"))
            )
            plan_search.send_keys(plan_name)
            time.sleep(1)
            plan_search.send_keys(Keys.ENTER)
            print(f"已選擇訓練計劃：{plan_name}")
            
            time.sleep(2)
            
            # 選擇表單集合（每次換訓練計劃後都需要重新選擇）
            dept_dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "select2-formDepartmentId-container"))
            )
            dept_dropdown.click()
            time.sleep(1)
            
            dept_search = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input.select2-search__field"))
            )
            dept_search.send_keys("全部")
            time.sleep(1)
            dept_search.send_keys(Keys.ENTER)
            print("已選擇表單集合")
            
            time.sleep(2)
            
            # 對每個表單進行循環處理
            for form_name in form_list:
                try:
                    # 等待並點擊表單名稱下拉選單
                    form_dropdown = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "select2-formTemplateId-container"))
                    )
                    form_dropdown.click()
                    time.sleep(1)
                    
                    # 等待表單名稱輸入框出現並填入部分表單名稱
                    form_search = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input.select2-search__field"))
                    )
                    
                    # 特別處理 coreEPAs 評量表
                    if "實習醫學生coreEPAs評量表" in form_name:
                        # 先搜尋表單名稱
                        form_search.send_keys("實習醫學生coreEPAs評量表")
                        time.sleep(1)
                        # 按下向下鍵選擇正確選項
                        form_search.send_keys(Keys.ARROW_DOWN)
                        time.sleep(1)
                        # 按下 Enter 確認選擇
                        form_search.send_keys(Keys.ENTER)
                    else:
                        # 其他表單的處理保持不變
                        form_search.send_keys(form_name)
                        time.sleep(1)
                        form_search.send_keys(Keys.ENTER)
                        
                    print(f"已選擇表單名稱：{form_name}")
                    time.sleep(1)
                    
                    # 下滑頁面到按鈕位置
                    submit_button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "#searchForm > div:nth-child(15) > div > input"))
                    )
                    driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
                    time.sleep(1)
                    
                    # 點擊按鈕
                    submit_button.click()
                    print(f"已點擊送出按鈕，下載表單：{form_name}")
                    
                    # 等待下載完成
                    time.sleep(5)
                    
                except Exception as e:
                    print(f"處理表單 {form_name} 時發生錯誤：{str(e)}")
                    continue  # 繼續處理下一個表單

    except Exception as select_error:
        print("選單操作失敗：", str(select_error))
        # 嘗試使用 JavaScript 方式
        try:
            js_script = """
            // 訓練計畫
            document.querySelector("#select2-planId-container").click();
            setTimeout(() => {
                let input = document.querySelector("#body-container > span > span > span.select2-search.select2-search--dropdown > input");
                input.value = "(五年級)西醫實習醫學生(UGY)訓練計畫第一年(五年級)_M120";
                input.dispatchEvent(new Event('input', { bubbles: true }));
            }, 500);
            
            // 科別
            setTimeout(() => {
                document.querySelector("#select2-formDepartmentId-container").click();
                setTimeout(() => {
                    let input = document.querySelector("#body-container > span > span > span.select2-search.select2-search--dropdown > input");
                    input.value = "全部";
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                }, 500);
            }, 1500);
            
            // 表單
            setTimeout(() => {
                document.querySelector("#select2-formTemplateId-container").click();
                setTimeout(() => {
                    let input = document.querySelector("#body-container > span > span > span.select2-search.select2-search--dropdown > input");
                    input.value = "臨床核心技能 1-23 新生兒的檢查";
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                }, 500);
            }, 2500);
            """
            driver.execute_script(js_script)
            print("已使用 JavaScript 方式輸入所有選項")
        except Exception as js_error:
            print("JavaScript 操作失敗：", str(js_error))
    
    # 等待操作完成
    time.sleep(3)

except Exception as e:
    print(f"發生錯誤：{str(e)}")

finally:
    # 關閉瀏覽器
    driver.quit()



#（六年級）西醫實習醫學生（UGY）訓練計畫第二年_M119期班使用