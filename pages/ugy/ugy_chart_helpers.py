"""
UGY EPA 共用圖表工具
提供統一的 EPA 等級轉換、同儕比較雷達圖、趨勢圖。
設計核心：所有圖表都呈現「自己 vs 同儕」的比較。
"""

import re
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from config.epa_constants import EPA_LEVEL_MAPPING


# ═══════════════════════════════════════════════════════
# 共用工具
# ═══════════════════════════════════════════════════════

def convert_level_to_score(value) -> float | None:
    """將 EPA 等級文字轉為數值（統一版本，取代 3 份重複）"""
    if pd.isna(value) or value is None:
        return None
    val = str(value).strip()
    if not val:
        return None
    score = EPA_LEVEL_MAPPING.get(val)
    if score is not None:
        return float(score)
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def natural_sort_key(s):
    """自然排序 key（如 C1, C2, C10 → 正確排序）"""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', str(s))]


# ═══════════════════════════════════════════════════════
# 同儕比較雷達圖
# ═══════════════════════════════════════════════════════

def create_peer_comparison_radar(
    student_df: pd.DataFrame,
    all_data_df: pd.DataFrame,
    student_name: str,
    epa_col: str = 'EPA評核項目',
    score_col: str = '教師評核EPA等級_數值',
    layer_col: str = '階層',
) -> go.Figure:
    """
    建立個人 vs 同階層同儕的 EPA 雷達圖。

    - 個人：藍色實線
    - 同階層平均：灰色虛線 + 淡色填充
    """
    fig = go.Figure()

    # EPA 項目（取所有資料的項目聯集）
    all_items = sorted(all_data_df[epa_col].dropna().unique().tolist())
    if not all_items:
        fig.add_annotation(text="無 EPA 評核項目資料", showarrow=False,
                           xref="paper", yref="paper", x=0.5, y=0.5)
        return fig

    # 該學生的階層
    student_layer = None
    if layer_col in student_df.columns and not student_df.empty:
        student_layer = student_df[layer_col].mode().iloc[0] if not student_df[layer_col].mode().empty else None

    # ── 同階層同儕平均 ──
    if student_layer and layer_col in all_data_df.columns:
        peer_df = all_data_df[all_data_df[layer_col] == student_layer]
    else:
        peer_df = all_data_df

    peer_avg = peer_df.groupby(epa_col)[score_col].mean()
    peer_values = [peer_avg.get(item, 0) for item in all_items]
    peer_values_closed = peer_values + [peer_values[0]]  # 閉合

    fig.add_trace(go.Scatterpolar(
        r=peer_values_closed,
        theta=all_items + [all_items[0]],
        fill='toself',
        fillcolor='rgba(180, 180, 180, 0.15)',
        line=dict(color='rgba(150, 150, 150, 0.6)', dash='dash'),
        name=f'同儕平均 ({student_layer or "全體"})',
    ))

    # ── 個人平均 ──
    student_avg = student_df.groupby(epa_col)[score_col].mean()
    student_values = [student_avg.get(item, 0) for item in all_items]
    student_values_closed = student_values + [student_values[0]]

    fig.add_trace(go.Scatterpolar(
        r=student_values_closed,
        theta=all_items + [all_items[0]],
        fill='toself',
        fillcolor='rgba(54, 162, 235, 0.2)',
        line=dict(color='rgb(54, 162, 235)', width=2.5),
        name=f'{student_name}',
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 5.5], tickvals=[1, 2, 3, 4, 5]),
        ),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
        height=400,
        margin=dict(t=30, b=60, l=60, r=60),
    )

    return fig


# ═══════════════════════════════════════════════════════
# 同儕比較趨勢圖
# ═══════════════════════════════════════════════════════

def create_peer_comparison_trend(
    student_df: pd.DataFrame,
    all_data_df: pd.DataFrame,
    student_name: str,
    batch_col: str = '梯次',
    score_col: str = '教師評核EPA等級_數值',
    layer_col: str = '階層',
    epa_col: str = 'EPA評核項目',
) -> go.Figure:
    """
    建立個人 vs 同階層同儕的 EPA 趨勢圖。

    - 個人各 EPA 項目：彩色折線
    - 同階層平均：灰色帶狀區間（mean ± std）
    """
    fig = go.Figure()

    # 過濾有效梯次
    valid_mask = (
        student_df[batch_col].notna() &
        (student_df[batch_col] != '未知梯次') &
        (student_df[batch_col] != '')
    )
    student_df = student_df[valid_mask].copy()

    if student_df.empty or batch_col not in student_df.columns:
        fig.add_annotation(text="無有效梯次資料", showarrow=False,
                           xref="paper", yref="paper", x=0.5, y=0.5)
        return fig

    # 排序梯次
    all_batches = sorted(student_df[batch_col].dropna().unique().tolist())
    if not all_batches:
        return fig

    # 該學生的階層
    student_layer = None
    if layer_col in student_df.columns:
        student_layer = student_df[layer_col].mode().iloc[0] if not student_df[layer_col].mode().empty else None

    # ── 同階層同儕帶狀區間 ──
    if student_layer and layer_col in all_data_df.columns:
        peer_df = all_data_df[
            (all_data_df[layer_col] == student_layer) &
            (all_data_df[batch_col].isin(all_batches))
        ]
    else:
        peer_df = all_data_df[all_data_df[batch_col].isin(all_batches)]

    if not peer_df.empty:
        peer_stats = peer_df.groupby(batch_col)[score_col].agg(['mean', 'std']).reindex(all_batches)
        peer_stats['std'] = peer_stats['std'].fillna(0)
        upper = (peer_stats['mean'] + peer_stats['std']).tolist()
        lower = (peer_stats['mean'] - peer_stats['std']).clip(lower=0).tolist()
        mean_vals = peer_stats['mean'].tolist()

        # 帶狀區間
        fig.add_trace(go.Scatter(
            x=all_batches + all_batches[::-1],
            y=upper + lower[::-1],
            fill='toself',
            fillcolor='rgba(180, 180, 180, 0.2)',
            line=dict(color='rgba(180, 180, 180, 0)'),
            showlegend=True,
            name=f'同儕 ±1SD ({student_layer or "全體"})',
        ))
        # 平均線
        fig.add_trace(go.Scatter(
            x=all_batches, y=mean_vals,
            mode='lines',
            line=dict(color='rgba(150, 150, 150, 0.5)', dash='dash', width=1.5),
            name=f'同儕平均',
        ))

    # ── 個人各 EPA 項目折線 ──
    epa_colors = {
        '病歷紀錄': '#EF553B',
        '當班處置': '#00CC96',
        '住院接診': '#636EFA',
    }

    epa_items = sorted(student_df[epa_col].dropna().unique().tolist())
    for item in epa_items:
        item_df = student_df[student_df[epa_col] == item]
        item_avg = item_df.groupby(batch_col)[score_col].mean().reindex(all_batches)

        fig.add_trace(go.Scatter(
            x=all_batches,
            y=item_avg.tolist(),
            mode='lines+markers',
            line=dict(color=epa_colors.get(item, '#AB63FA'), width=2.5),
            marker=dict(size=7),
            name=f'{student_name} - {item}',
            connectgaps=True,
        ))

    fig.update_layout(
        xaxis_title='梯次',
        yaxis_title='教師評核EPA等級',
        yaxis=dict(range=[0, 5.5], tickvals=[1, 2, 3, 4, 5]),
        height=400,
        margin=dict(t=30, b=60),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
    )

    return fig
