"""
Copyright (C) 2020-2020 Jiri Borovec <...>
"""
from typing import Tuple

import matplotlib.pyplot as plt
import pandas as pd


def draw_comments_timeline(df_comments: pd.DataFrame, figsize: Tuple[int] = (18, 7)) -> plt.Figure:
    fig, ax = plt.subplots(figsize=figsize)

    df_comments.plot(ax=ax, grid=True, xlabel='DateTime', legend=False)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=70, ha='center')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=8, fancybox=True, shadow=True)

    return fig
