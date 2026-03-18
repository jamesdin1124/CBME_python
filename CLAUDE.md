# CBME_python 專案開發規則

## 修改系統 UI 或功能時，必須同步更新使用手冊

每次對系統介面、功能、流程做出變更時，**必須同步更新**以下兩份使用手冊：

- `pages/pediatric/PED CCC/兒科主治醫師使用手冊.docx`
- `pages/pediatric/PED CCC/兒科住院醫師使用手冊.docx`

### 手冊更新規則

1. **版本號遞增**：更新日期改為當日日期，版本號遞增（例如 1.1 → 1.2）
2. **文字說明同步**：任何新功能或流程變更，需在手冊對應章節更新說明文字
3. **截圖更新**：若 UI 有明顯改變，需更新對應的截圖（PNG 截圖存放於 `pages/pediatric/PED CCC/*.pdf`，可用 sips 轉換為 PNG）
4. **手冊使用 docx-js** 以 Node.js 建立，截圖嵌入為 ImageRun

### 各章節對應關係

| 系統功能 | 主治醫師手冊章節 | 住院醫師手冊章節 |
|--------|------------|------------|
| 登入/帳號申請 | 第 2 章 | 第 2 章 |
| 修改密碼 | 第 2.3 節 | 第 2.3 節 |
| 評核表單（操作技術/會議/EPA） | 第 3 章 | 無（由主治填寫） |
| CCC 總覽 | 第 4.1 節 | — |
| 個別深入分析 | 第 4.2 節 | 第 4 章 |
| 合資標準 | 第 6 章 | 第 5 章 |
| 帳號管理 | 第 7 章 | — |

### 截圖檔案位置
- `/tmp/form1.png` → 操作技術評核表單
- `/tmp/form2.png` → 會議報告評核表單
- `/tmp/form3.png` → EPA 評估表單
- `/tmp/ccc_overview.png` → CCC 總覽頁面
- `/tmp/individual.png` → 個別深入分析頁面

（截圖由 `pages/pediatric/PED CCC/*.pdf` 透過 `sips -s format png` 轉換）

---

## Git Push 規則

每次 `git push origin master` 後，同步執行：
```bash
git push origin master:main --force
```
這樣 Streamlit Cloud（部署自 `main` 分支）才會收到最新更新。

或使用已設定的 alias：
```bash
git pushall
```

---

## 分支說明

- `master`：主要開發分支，所有修改在此進行
- `main`：Streamlit Cloud 部署分支，需與 master 保持同步

---

## 可信賴程度量表規範

**必須使用五分制小數點顯示，符合學會規範。**

- 量表範圍：1.5 — 5.0（9 個等級，每級以小數點標示）
- 表單選項格式：`"分數 — 描述"`，例如 `"2.5 — 教師在旁必要時協助"`
- 定義於 `pages/pediatric/pediatric_forms.py` 的 `RELIABILITY_OPTIONS`
- 分析程式 `convert_reliability_to_numeric`（`pediatric_analysis.py`）需同時支援新舊格式（向後相容）

| 分數 | 描述 |
|------|------|
| 1.5 | 允許住院醫師在旁觀察 |
| 2.0 | 教師在旁逐步共同操作 |
| 2.5 | 教師在旁必要時協助 |
| 3.0 | 教師可立即到場協助，事後逐項確認 |
| 3.3 | 教師可立即到場協助，事後重點確認 |
| 3.6 | 教師可稍後到場協助，必要時事後確認 |
| 4.0 | 教師 on call 提供監督 |
| 4.5 | 教師不需 on call，事後提供回饋及監督 |
| 5.0 | 學員可對其他資淺的學員進行監督與教學 |

---

## 帳號說明

- 所有主治醫師與住院醫師帳號由管理員預先建立
- **預設密碼為使用者 DOC 編號（大寫）**，例如帳號 `DOC31024`，初始密碼即為 `DOC31024`
- 手冊路徑已更新至 `pages/pediatric/PED CCC/` 資料夾
