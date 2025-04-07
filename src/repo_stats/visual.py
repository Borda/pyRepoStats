"""
Copyright (C) 2020-2021 Jiri Borovec <...>
"""

import logging
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mpl_toolkits.axes_grid1 import make_axes_locatable


def draw_comments_timeline(
    df_comments: pd.DataFrame, title: str = "User contribution aggregation"
) -> Tuple[plt.Figure, dict]:
    """Draw a figure with two charts, one as cumulative date/contribution and user/time heatmap

    Args:
        df_comments: table with aggregated comments
        fig_size: output figure size
        title: optional figure title

    Returns:
        Figure and extras

    >>> import pandas as pd
    >>> comments = [dict(Date='2020-10', me=5, you=3), dict(Date='2020-11', me=2, you=4)]
    >>> df = pd.DataFrame(comments).set_index('Date')
    >>> fig, extras = draw_comments_timeline(df)
    """
    # take the offset plus max from time-steps in area-bar and users in heatmap
    fig_width = 2 + max(len(df_comments.columns) * 0.3, len(df_comments.index) * 0.2)
    # define legend grid for are-bar
    leg_cols = int(fig_width / 1.8)
    leg_rows = np.ceil(len(df_comments.columns) / leg_cols)
    # compose from offset plus nb legend lines
    fig_height_top = 4 + leg_rows * 0.3
    fig_height_bottom = 1 + len(df_comments.index) * 0.3

    # create the main figure
    fig, axarr = plt.subplots(
        figsize=(fig_width, fig_height_top + fig_height_bottom),
        nrows=2,
        gridspec_kw={"height_ratios": [1, fig_height_bottom / fig_height_top]},
        tight_layout=True,
    )
    fig.gca().set_title(title)
    ax_abar, ax_hmap = axarr

    if df_comments.empty:
        logging.error("You have passed empty DataFrame, so also empty Figure is returned.")
        return fig

    # show the cumulative chart
    df_comments.plot(
        ax=ax_abar,
        kind="area",
        stacked=True,
        grid=True,
        ylabel="Contributions / commented",
        xlabel="Aggregated time",
        legend=False,
        cmap="gist_ncar",
    )
    times, x_step = list(df_comments.index), 2
    ax_abar.set_xticks(range(len(times))[::x_step])
    ax_abar.set_xticklabels(times[::2], rotation=70, ha="center")
    ax_abar.set_xlim(0, len(times) - 1)
    ax_abar.set_ylim(0, max(np.sum(df_comments.values, axis=1)) * 1.05)
    lgd = ax_abar.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.0 + (leg_rows * 0.25 / fig_height_top)),
        ncol=leg_cols,
        fancybox=True,
        shadow=True,
    )

    # im = ax.imshow(df_comments.values, vmin=0, interpolation='nearest', cmap='YlGn')
    # see: https://matplotlib.org/3.3.2/gallery/images_contours_and_fields/image_annotated_heatmap.html
    df_comments = df_comments.sort_index(ascending=False)
    im = ax_hmap.pcolormesh(
        df_comments.values,
        vmin=0,
        cmap="YlGn",
        edgecolors="w",
        linewidth=1,
    )
    # axes descriptions
    ax_hmap.set_ylabel("Aggregated dates")
    ax_hmap.set_yticks([i + 0.5 for i, _ in enumerate(df_comments.index)])
    ax_hmap.set_yticklabels(df_comments.index, va="center")
    ax_hmap.set_xlabel("Users")
    ax_hmap.set_xticks([i + 0.5 for i, _ in enumerate(df_comments.columns)])
    ax_hmap.set_xticklabels(df_comments.columns, rotation=-90, ha="center")
    # Create colorbar
    cax = make_axes_locatable(ax_hmap).append_axes("right", size=0.3, pad=0.1)
    cbar = plt.colorbar(im, cax=cax)
    cbar.ax.set_ylabel("Contributions", rotation=90, va="center")
    cbar.minorticks_on()

    # fig.tight_layout(pad=0.1)
    return fig, {"legend": lgd, "colorbar": cax}
