# 雷達圖功能整合指南

## 📊 整合概述

本指南說明如何將分散在各個檔案中的雷達圖功能整合到統一的 `modules/unified_radar_visualization.py` 模組中。

## 🔍 現狀分析

### 重複的雷達圖實現

1. **`utils.py`** (693行)
   - `create_radar_chart()` - 簡單雷達圖
   - `display_radar_chart()` - 單一雷達圖顯示
   - `display_comparison_radar_charts()` - 比較雷達圖
   - `radar_chart_component()` - 互動式雷達圖元件
   - `display_student_epa_radar_matplotlib()` - Matplotlib版本
   - `display_all_students_epa_radar()` - 所有學生雷達圖

2. **`modules/visualization.py`** (922行)
   - `plot_radar_chart()` - 複雜EPA雷達圖（支援多種模式）
   - `plot_epa_trend_px()` - EPA趨勢圖

3. **`modules/radar_trend_visualization.py`** (331行)
   - `create_layer_radar_chart()` - 階層雷達圖
   - `create_epa_trend_charts()` - EPA趨勢圖
   - `create_simple_layer_radar_chart()` - 簡化階層雷達圖

### 各分析模組中的雷達圖使用

- `analysis_ugy_individual.py` - UGY個別學生雷達圖
- `analysis_ugy_overview.py` - UGY學生總覽雷達圖
- `analysis_pgy_students.py` - PGY學生雷達圖
- `analysis_anesthesia_residents.py` - 麻醉科住院醫師雷達圖
- `ugy_epa/ugy_epa_google_sheets.py` - UGY EPA雷達圖

## 🎯 整合方案

### 新的統一架構

```
modules/
├── unified_radar_visualization.py    # 統一的雷達圖模組
│   ├── UnifiedRadarVisualization     # 主要雷達圖類別
│   ├── RadarChartConfig             # 雷達圖配置類別
│   ├── EPAChartConfig               # EPA雷達圖配置類別
│   ├── RadarChartComponent          # Streamlit元件類別
│   └── 便利函數                      # 向後相容的便利函數
```

### 核心類別說明

#### 1. `UnifiedRadarVisualization`
- **功能**: 統一的雷達圖創建和管理
- **方法**:
  - `create_simple_radar_chart()` - 簡單雷達圖
  - `create_epa_radar_chart()` - EPA專用雷達圖
  - `create_comparison_radar_chart()` - 比較雷達圖
  - `create_matplotlib_radar_chart()` - Matplotlib版本

#### 2. `RadarChartConfig`
- **功能**: 雷達圖配置管理
- **屬性**: title, scale, fill, color, opacity, show_legend, height, width

#### 3. `EPAChartConfig`
- **功能**: EPA雷達圖專用配置
- **繼承**: RadarChartConfig
- **額外屬性**: plot_types, student_id, standard_categories, labels

#### 4. `RadarChartComponent`
- **功能**: Streamlit互動元件
- **方法**:
  - `display_simple_radar()` - 簡單雷達圖元件
  - `display_comparison_radar()` - 比較雷達圖元件

## 🔄 遷移步驟

### 步驟1: 更新Import語句

將所有檔案中的雷達圖import更新為：

```python
# 舊的import
from utils import create_radar_chart, display_radar_chart
from modules.visualization import plot_radar_chart
from modules.radar_trend_visualization import create_layer_radar_chart

# 新的import
from modules.unified_radar_visualization import (
    UnifiedRadarVisualization,
    RadarChartConfig,
    EPAChartConfig,
    RadarChartComponent,
    create_radar_chart,
    create_epa_radar_chart,
    create_comparison_radar_chart
)
```

### 步驟2: 更新函數調用

#### 簡單雷達圖
```python
# 舊的調用
fig = create_radar_chart(categories, values, title="雷達圖", scale=5)

# 新的調用（向後相容）
fig = create_radar_chart(categories, values, title="雷達圖", scale=5)

# 或使用類別方式
radar_viz = UnifiedRadarVisualization()
config = RadarChartConfig(title="雷達圖", scale=5)
fig = radar_viz.create_simple_radar_chart(categories, values, config)
```

#### EPA雷達圖
```python
# 舊的調用
fig = plot_radar_chart(df=df, plot_types=['layers'], title="EPA 雷達圖")

# 新的調用
fig = create_epa_radar_chart(df, plot_types=['layers'], title="EPA 雷達圖")

# 或使用類別方式
radar_viz = UnifiedRadarVisualization()
config = EPAChartConfig(title="EPA 雷達圖", plot_types=['layers'])
fig = radar_viz.create_epa_radar_chart(df, config)
```

#### 比較雷達圖
```python
# 舊的調用
display_comparison_radar_charts(df, value_columns, group_column, title="比較雷達圖")

# 新的調用
fig = create_comparison_radar_chart(df, value_columns, group_column, title="比較雷達圖")
st.plotly_chart(fig, use_container_width=True)

# 或使用元件方式
radar_viz = UnifiedRadarVisualization()
component = RadarChartComponent(radar_viz)
component.display_comparison_radar(df, title="比較雷達圖")
```

### 步驟3: 更新Streamlit元件

```python
# 舊的元件
radar_chart_component(data, title="能力評估", key_prefix="radar")

# 新的元件
radar_viz = UnifiedRadarVisualization()
component = RadarChartComponent(radar_viz)
component.display_simple_radar(data, title="能力評估", key_prefix="radar")
```

## 📋 需要更新的檔案清單

### 高優先級（核心模組）
- [ ] `utils.py` - 移除重複的雷達圖函數
- [ ] `modules/visualization.py` - 移除重複的雷達圖函數
- [ ] `modules/radar_trend_visualization.py` - 移除重複的雷達圖函數

### 中優先級（分析模組）
- [ ] `analysis_ugy_individual.py`
- [ ] `analysis_ugy_overview.py`
- [ ] `analysis_pgy_students.py`
- [ ] `analysis_anesthesia_residents.py`
- [ ] `ugy_epa/ugy_epa_google_sheets.py`

### 低優先級（其他檔案）
- [ ] `main_dashboard.py`
- [ ] `main_login_dashboard.py`
- [ ] `forms/test_form.py`

## 🚀 整合優勢

### 1. 代碼減少
- **整合前**: 3個主要雷達圖模組，共計約1,946行代碼
- **整合後**: 1個統一模組，約600行代碼
- **減少**: 約70%的代碼重複

### 2. 維護性提升
- 統一的API介面
- 集中的錯誤處理
- 一致的配置管理
- 易於擴展新功能

### 3. 效能改善
- 減少重複的import
- 統一的記憶體管理
- 更好的快取機制

### 4. 功能增強
- 支援多種圖表類型
- 統一的配置系統
- 更好的錯誤處理
- 向後相容性

## ⚠️ 注意事項

### 1. 向後相容性
- 提供便利函數保持舊API相容
- 逐步遷移，不強制一次性更新

### 2. 測試建議
- 在整合前備份現有檔案
- 逐步測試每個模組的功能
- 確保所有雷達圖正常顯示

### 3. 效能考量
- 大型DataFrame可能需要優化
- 考慮添加快取機制
- 監控記憶體使用情況

## 📝 實施建議

### 階段1: 準備工作
1. 備份現有檔案
2. 創建測試環境
3. 準備回滾方案

### 階段2: 核心整合
1. 更新 `utils.py` 移除重複函數
2. 更新 `modules/visualization.py` 移除重複函數
3. 更新 `modules/radar_trend_visualization.py` 移除重複函數

### 階段3: 模組更新
1. 更新各分析模組的import和調用
2. 測試每個模組的功能
3. 修復任何相容性問題

### 階段4: 清理和優化
1. 移除未使用的函數
2. 優化效能
3. 更新文檔

## 🔧 故障排除

### 常見問題

1. **Import錯誤**
   ```python
   # 確保路徑正確
   from modules.unified_radar_visualization import UnifiedRadarVisualization
   ```

2. **配置錯誤**
   ```python
   # 使用正確的配置類別
   config = EPAChartConfig(title="EPA 雷達圖", plot_types=['layers'])
   ```

3. **資料格式錯誤**
   ```python
   # 確保DataFrame包含必要欄位
   required_columns = ['EPA評核項目', '教師評核EPA等級_數值', '階層']
   ```

### 調試技巧

1. **啟用詳細錯誤訊息**
   ```python
   import traceback
   try:
       fig = radar_viz.create_epa_radar_chart(df, config)
   except Exception as e:
       st.error(f"錯誤: {str(e)}")
       st.error(traceback.format_exc())
   ```

2. **檢查資料格式**
   ```python
   st.write("DataFrame形狀:", df.shape)
   st.write("欄位:", df.columns.tolist())
   st.write("前5行:", df.head())
   ```

3. **測試簡單案例**
   ```python
   # 先測試簡單雷達圖
   categories = ['項目1', '項目2', '項目3']
   values = [3, 4, 2]
   fig = create_radar_chart(categories, values)
   st.plotly_chart(fig)
   ```

---

**整合完成後，您的雷達圖功能將更加統一、高效且易於維護！**
