"""
縱向追蹤圖表模組

提供 EPA 分數隨時間變化的趨勢圖，支援：
- 個人趨勢線
- 群組平均趨勢（含 95% CI / SD 帶狀區域）
- 個人 vs 群組比較
- 箱型圖/小提琴圖分佈

所有圖表回傳 plotly.graph_objects.Figure。
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ═══════════════════════════════════════════════════════
# 色盤
# ═══════════════════════════════════════════════════════

DEFAULT_COLORS = [
    '#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A',
    '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52',
]

CI_FILL_ALPHA = 0.15
REFERENCE_LINE_COLOR = 'rgba(150, 150, 150, 0.4)'


class LongitudinalChart:
    """
    縱向追蹤圖表引擎。

    使用方式：
        chart = LongitudinalChart()
        fig = chart.create_individual_trend(df, time_col='梯次', score_cols=['EPA1','EPA2'])
        st.plotly_chart(fig, use_container_width=True)
    """

    def __init__(self, y_range=(0, 5.5), height=500):
        self.y_range = y_range
        self.height = height

    # ─── 個人趨勢 ───

    def create_individual_trend(self, student_data, time_col, score_col,
                                group_col=None, title=None, student_name=None):
        """
        個人 EPA 分數趨勢線（可多 EPA 項目分色）。

        Args:
            student_data (DataFrame): 個人資料
            time_col (str): 時間軸欄位名（如 '梯次', '月份', 'evaluation_date'）
            score_col (str): 分數欄位名
            group_col (str, optional): 分組欄位（如 'EPA評核項目'），若有則每組一條線
            title (str, optional): 圖表標題
            student_name (str, optional): 學員姓名（用於標題）

        Returns:
            go.Figure
        """
        if student_data is None or student_data.empty:
            return self._empty_figure("無個人資料")

        df = student_data.dropna(subset=[score_col]).copy()
        if df.empty:
            return self._empty_figure("個人資料中無有效分數")

        _title = title or f"{student_name or '個人'} EPA 分數趨勢"

        if group_col and group_col in df.columns:
            fig = px.line(
                df, x=time_col, y=score_col, color=group_col,
                markers=True, title=_title,
                color_discrete_sequence=DEFAULT_COLORS,
            )
        else:
            fig = px.line(
                df, x=time_col, y=score_col,
                markers=True, title=_title,
            )

        fig.update_layout(
            yaxis=dict(range=self.y_range, title='信賴等級分數'),
            xaxis=dict(title=time_col),
            height=self.height,
            hovermode='x unified',
        )

        # 加上參考線
        for level in [2, 3, 4]:
            fig.add_hline(y=level, line_dash='dot',
                          line_color=REFERENCE_LINE_COLOR, line_width=1)

        return fig

    # ─── 群組趨勢 ───

    def create_group_trend(self, group_data, time_col, score_col,
                           group_col=None, ci_type='95%', title=None):
        """
        群組平均趨勢 + 信賴區間帶狀區域。

        Args:
            group_data (DataFrame): 群組資料
            time_col (str): 時間軸欄位
            score_col (str): 分數欄位
            group_col (str, optional): 分組欄位（如 'EPA評核項目'），None 則為單一趨勢
            ci_type (str): '95%' | 'sd' | 'none'
            title (str, optional): 圖表標題

        Returns:
            go.Figure
        """
        if group_data is None or group_data.empty:
            return self._empty_figure("無群組資料")

        df = group_data.dropna(subset=[score_col]).copy()
        _title = title or "群組 EPA 分數趨勢"

        if group_col and group_col in df.columns:
            groups = df[group_col].unique()
        else:
            df['_group'] = '全體'
            group_col = '_group'
            groups = ['全體']

        fig = go.Figure()

        for i, grp in enumerate(groups):
            color = DEFAULT_COLORS[i % len(DEFAULT_COLORS)]
            grp_df = df[df[group_col] == grp]

            # 依時間聚合
            agg = grp_df.groupby(time_col).agg(
                mean=(score_col, 'mean'),
                std=(score_col, 'std'),
                count=(score_col, 'count'),
            ).reset_index()
            agg = agg.sort_values(time_col)

            # 平均線
            fig.add_trace(go.Scatter(
                x=agg[time_col], y=agg['mean'],
                mode='lines+markers',
                name=str(grp),
                line=dict(color=color, width=2),
                marker=dict(size=8),
                hovertemplate=f'<b>{grp}</b><br>'
                              f'{time_col}: %{{x}}<br>'
                              f'平均: %{{y:.2f}}<br>'
                              '<extra></extra>',
            ))

            # 信賴區間帶
            if ci_type != 'none' and len(agg) > 1:
                upper, lower = self._calc_ci(agg, ci_type)
                fill_color = color.replace('rgb', 'rgba').replace(')', f', {CI_FILL_ALPHA})') \
                    if 'rgb' in color else f'rgba(100,100,200,{CI_FILL_ALPHA})'
                # Hex to rgba
                if color.startswith('#'):
                    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
                    fill_color = f'rgba({r},{g},{b},{CI_FILL_ALPHA})'

                fig.add_trace(go.Scatter(
                    x=np.concatenate([agg[time_col].values, agg[time_col].values[::-1]]),
                    y=np.concatenate([upper, lower[::-1]]),
                    fill='toself',
                    fillcolor=fill_color,
                    line=dict(color='rgba(0,0,0,0)'),
                    showlegend=False,
                    hoverinfo='skip',
                ))

        fig.update_layout(
            title=_title,
            yaxis=dict(range=self.y_range, title='信賴等級分數'),
            xaxis=dict(title=time_col),
            height=self.height,
            hovermode='x unified',
        )

        for level in [2, 3, 4]:
            fig.add_hline(y=level, line_dash='dot',
                          line_color=REFERENCE_LINE_COLOR, line_width=1)

        return fig

    # ─── 個人 vs 群組 ───

    def create_individual_vs_group(self, student_data, group_data,
                                   time_col, score_col,
                                   group_col=None, student_name=None,
                                   ci_type='95%', title=None):
        """
        個人趨勢疊加群組平均（核心功能）。

        個人以粗實線 + 大標記顯示，
        群組平均以細虛線 + CI 帶狀區域顯示。

        Args:
            student_data (DataFrame): 個人資料
            group_data (DataFrame): 群組資料
            time_col, score_col, group_col: 欄位名
            student_name (str): 學員姓名
            ci_type (str): '95%' | 'sd' | 'none'
            title (str): 圖表標題

        Returns:
            go.Figure
        """
        if (student_data is None or student_data.empty) and (group_data is None or group_data.empty):
            return self._empty_figure("無資料可顯示")

        _title = title or f"{student_name or '個人'} vs 群組平均 EPA 趨勢"
        fig = go.Figure()

        # 群組平均（背景）
        if group_data is not None and not group_data.empty:
            grp_df = group_data.dropna(subset=[score_col]).copy()
            agg = grp_df.groupby(time_col).agg(
                mean=(score_col, 'mean'),
                std=(score_col, 'std'),
                count=(score_col, 'count'),
            ).reset_index().sort_values(time_col)

            # CI 帶
            if ci_type != 'none' and len(agg) > 1:
                upper, lower = self._calc_ci(agg, ci_type)
                fig.add_trace(go.Scatter(
                    x=np.concatenate([agg[time_col].values, agg[time_col].values[::-1]]),
                    y=np.concatenate([upper, lower[::-1]]),
                    fill='toself',
                    fillcolor=f'rgba(150, 150, 150, {CI_FILL_ALPHA})',
                    line=dict(color='rgba(0,0,0,0)'),
                    showlegend=False,
                    hoverinfo='skip',
                ))

            # 群組平均線
            fig.add_trace(go.Scatter(
                x=agg[time_col], y=agg['mean'],
                mode='lines+markers',
                name='群組平均',
                line=dict(color='rgba(150,150,150,0.8)', width=2, dash='dash'),
                marker=dict(size=6, symbol='diamond'),
            ))

        # 個人趨勢（前景）
        if student_data is not None and not student_data.empty:
            std_df = student_data.dropna(subset=[score_col]).copy()

            if group_col and group_col in std_df.columns:
                for i, epa in enumerate(std_df[group_col].unique()):
                    epa_df = std_df[std_df[group_col] == epa].sort_values(time_col)
                    color = DEFAULT_COLORS[i % len(DEFAULT_COLORS)]
                    fig.add_trace(go.Scatter(
                        x=epa_df[time_col], y=epa_df[score_col],
                        mode='lines+markers',
                        name=f'{student_name or "個人"} — {epa}',
                        line=dict(color=color, width=3),
                        marker=dict(size=10),
                    ))
            else:
                std_df = std_df.sort_values(time_col)
                fig.add_trace(go.Scatter(
                    x=std_df[time_col], y=std_df[score_col],
                    mode='lines+markers',
                    name=student_name or '個人',
                    line=dict(color=DEFAULT_COLORS[0], width=3),
                    marker=dict(size=10),
                ))

        fig.update_layout(
            title=_title,
            yaxis=dict(range=self.y_range, title='信賴等級分數'),
            xaxis=dict(title=time_col),
            height=self.height,
            hovermode='x unified',
        )

        for level in [2, 3, 4]:
            fig.add_hline(y=level, line_dash='dot',
                          line_color=REFERENCE_LINE_COLOR, line_width=1)

        return fig

    # ─── 箱型圖 ───

    def create_boxplot_trend(self, data, time_col, score_col,
                             group_col=None, title=None):
        """
        箱型圖 + 個人資料點（分佈視圖）。

        Args:
            data (DataFrame): 資料
            time_col (str): 時間欄位
            score_col (str): 分數欄位
            group_col (str, optional): 分組欄位
            title (str): 標題

        Returns:
            go.Figure
        """
        if data is None or data.empty:
            return self._empty_figure("無資料")

        _title = title or "EPA 分數分佈趨勢"

        if group_col and group_col in data.columns:
            fig = px.box(
                data, x=time_col, y=score_col, color=group_col,
                points='all', title=_title,
                color_discrete_sequence=DEFAULT_COLORS,
            )
        else:
            fig = px.box(
                data, x=time_col, y=score_col,
                points='all', title=_title,
            )

        fig.update_layout(
            yaxis=dict(range=self.y_range, title='信賴等級分數'),
            height=self.height,
        )

        return fig

    # ─── 小提琴圖 + 統計表 ───

    def create_violin_with_stats(self, data, category_col, score_col,
                                  title=None):
        """
        小提琴圖 + 右側統計摘要表。

        Args:
            data (DataFrame): 資料
            category_col (str): 類別欄位（X 軸）
            score_col (str): 分數欄位
            title (str): 標題

        Returns:
            go.Figure
        """
        if data is None or data.empty:
            return self._empty_figure("無資料")

        _title = title or "分數分佈分析"

        categories = data[category_col].unique()
        fig = make_subplots(
            rows=1, cols=2, column_widths=[0.65, 0.35],
            specs=[[{'type': 'violin'}, {'type': 'table'}]],
        )

        # 小提琴圖
        for i, cat in enumerate(categories):
            cat_data = data[data[category_col] == cat][score_col].dropna()
            fig.add_trace(go.Violin(
                y=cat_data, name=str(cat),
                box_visible=True, meanline_visible=True,
                fillcolor=DEFAULT_COLORS[i % len(DEFAULT_COLORS)],
                opacity=0.6,
            ), row=1, col=1)

        # 統計表
        stats_rows = []
        for cat in categories:
            cat_data = data[data[category_col] == cat][score_col].dropna()
            stats_rows.append({
                '項目': str(cat),
                '平均': f'{cat_data.mean():.2f}',
                '中位數': f'{cat_data.median():.2f}',
                'SD': f'{cat_data.std():.2f}',
                '筆數': str(len(cat_data)),
            })

        stats_df = pd.DataFrame(stats_rows)
        fig.add_trace(go.Table(
            header=dict(values=list(stats_df.columns), fill_color='paleturquoise', align='center'),
            cells=dict(values=[stats_df[col] for col in stats_df.columns],
                       fill_color='lavender', align='center'),
        ), row=1, col=2)

        fig.update_layout(title=_title, height=self.height, showlegend=False)
        return fig

    # ─── 工具方法 ───

    @staticmethod
    def _calc_ci(agg_df, ci_type='95%'):
        """
        計算信賴區間上下界。

        Args:
            agg_df: 含 mean, std, count 欄位的 DataFrame
            ci_type: '95%' | 'sd'

        Returns:
            tuple: (upper_array, lower_array) clipped to [0, 5]
        """
        means = agg_df['mean'].values
        stds = agg_df['std'].fillna(0).values
        counts = agg_df['count'].values

        if ci_type == '95%':
            try:
                from scipy.stats import t as t_dist
                sems = stds / np.sqrt(np.maximum(counts, 1))
                dfs = np.maximum(counts - 1, 1)
                t_crits = np.array([t_dist.ppf(0.975, df) for df in dfs])
                widths = t_crits * sems
            except ImportError:
                # Fallback to 1.96 if scipy not available
                sems = stds / np.sqrt(np.maximum(counts, 1))
                widths = 1.96 * sems
        else:  # sd
            widths = stds

        upper = np.clip(means + widths, 0, 5)
        lower = np.clip(means - widths, 0, 5)
        return upper, lower

    @staticmethod
    def _empty_figure(message="無資料"):
        """建立空白圖表並顯示訊息"""
        fig = go.Figure()
        fig.update_layout(
            annotations=[dict(
                text=message, xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=18, color="gray"),
            )],
            height=300,
        )
        return fig
