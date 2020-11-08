"""
Copyright (C) 2020-2020 Jiri Borovec <...>
"""
from typing import Tuple

import matplotlib.pyplot as plt
import pandas as pd
from mpl_toolkits.axes_grid1 import make_axes_locatable


def draw_comments_timeline(df_comments: pd.DataFrame, figsize: Tuple[int] = (18, 14), title: str = '') -> plt.Figure:
    """Draw a figure with two charts, one as cumulative date/contribution and user/time heatmap

    :param df_comments: table with aggregated comments
    :param figsize: output figure size
    :param title: optional figure title
    :return: Figure

    >>> import pandas as pd
    >>> comments = [dict(Date='2020-10', me=5, you=3), dict(Date='2020-11', me=2, you=4)]
    >>> df = pd.DataFrame(comments).set_index('Date')
    >>> fig = draw_comments_timeline(df)
    """
    fig, axarr = plt.subplots(figsize=figsize, nrows=2)
    fig.gca().set_title(title)

    # show the cumulative chart
    df_comments.plot(ax=axarr[0], kind='area', stacked=True, grid=True, xlabel='DateTime', legend=False, cmap='gist_ncar')
    axarr[0].set_xticklabels(axarr[0].get_xticklabels(), rotation=70, ha='center')
    axarr[0].set_xlim(0, max([t._x for t in axarr[0].get_xticklabels() if t._text]))
    axarr[0].legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=8, fancybox=True, shadow=True)

    # see: https://matplotlib.org/3.3.2/gallery/images_contours_and_fields/image_annotated_heatmap.html#sphx-glr-gallery-images-contours-and-fields-image-annotated-heatmap-py
    # im = ax.imshow(df_comments.values, vmin=0, interpolation='nearest', cmap='YlGn')
    df_comments.sort_index(ascending=False, inplace=True)
    im = axarr[1].pcolormesh(df_comments.values, vmin=0, cmap='YlGn', edgecolors='w', linewidth=1)
    # axes descriptions
    axarr[1].set_ylabel('Aggregated dates')
    axarr[1].set_yticks([i + 0.5 for i, _ in enumerate(df_comments.index)])
    axarr[1].set_yticklabels(df_comments.index, va='center')
    axarr[1].set_xlabel('Users')
    axarr[1].set_xticks([i + 0.5 for i, _ in enumerate(df_comments.columns)])
    axarr[1].set_xticklabels(df_comments.columns, rotation=90, ha='center')
    # Create colorbar
    cax = make_axes_locatable(axarr[1]).append_axes("right", size="3%", pad=0.1)
    cbar = plt.colorbar(im, cax=cax)
    cbar.ax.set_ylabel('Contributions', rotation=90, va="center")
    cbar.minorticks_on()

    return fig
