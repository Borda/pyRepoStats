"""
Copyright (C) 2020-2020 Jiri Borovec <...>
"""
from typing import List, Optional

import pandas as pd
from tqdm import tqdm

# see: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
#: define conversion for frequency grouping
DATETIME_FREQ = {
    'D': "%Y-%m-%d",
    'W': "%Y-%W",
    'M': "%Y-%m",
    'Y': "%Y",
}


def compute_users_summary(items: List[dict]) -> pd.DataFrame:
    """Aggregate issue/PR affiliations and summary counts.

    >>> items = [dict(type='PR', state='closed', author='me', commenters=['me', 'you']),
    ...          dict(type='PR', state='open', author='me', commenters=['me', 'you']),
    ...          dict(type='issue', state='closed', author='me', commenters=['me', 'you']),
    ...          dict(type='PR', state='merged', author='you', commenters=['me', 'you']),
    ...          dict(type='issue', state='open', author='you', commenters=['me', 'you'])]
    >>> df = compute_users_summary(items)
    >>> df.columns = [c.replace('opened', 'o/').replace('merged', 'm/').replace('commented', 'c/') for c in df.columns]
    >>> df  # doctest: +NORMALIZE_WHITESPACE
          o/ PRs  m/ PRs  c/ PRs  o/ issues  m/ issues  c/ issues  all o/
    user
    me         2       0       1          1          0          1       3
    you        1       1       2          1          0          1       2
    """
    assert items, 'nothing to do...'
    df_items = pd.DataFrame(items)

    users_stat = []
    for user in tqdm(df_items['author'].unique(), desc='Processing users'):
        user_stat = {'user': user}
        # parse particular user stats
        for tp, df in df_items.groupby('type'):
            df_auth = df[df['author'] == user]
            user_stat[f'opened {tp}s'] = len(df_auth)
            user_stat[f'merged {tp}s'] = sum(df_auth['state'] == 'merged')
            df_na = df[df['author'] != user]
            user_stat[f'commented {tp}s'] = sum(df_na['commenters'].apply(lambda l: user in l))
        users_stat.append(user_stat)

    # transform to pandas table
    df_users = pd.DataFrame(users_stat).set_index(['user'])
    df_users['all opened'] = df_users['opened PRs'] + df_users['opened issues']
    df_users.sort_values(['all opened'], ascending=False, inplace=True)

    return df_users


def compute_user_comment_timeline(
        items: List[dict],
        freq: str = 'W',
        parent_type: Optional[str] = None,
) -> pd.DataFrame:
    """Aggregate comments from all issues/PRs.

    >>> items = [dict(created_at='2020-10-05', parent_idx=1, author='me'),
    ...          dict(created_at='2020-10-17', parent_idx=1, author='me'),
    ...          dict(created_at='2020-10-29', parent_idx=2, author='me'),
    ...          dict(created_at='2020-11-15', parent_idx=2, author='you')]
    >>> compute_user_comment_timeline(items, freq='M')  # doctest: +NORMALIZE_WHITESPACE
    author      me  you
    created_at
    2020-10      2    0
    2020-11      0    1
    """
    assert freq in DATETIME_FREQ, 'unsupported freq format, allowed: %r' % DATETIME_FREQ.keys()

    df_comments = pd.DataFrame(items)
    if parent_type:
        df_comments = df_comments[df_comments['parent_type'] == parent_type]

    def _reformat(dt):
        return pd.to_datetime(dt).strftime(DATETIME_FREQ[freq])

    df_comments['created_at'] = df_comments['created_at'].apply(_reformat)

    # keep only single sample per user-time-issue
    df_comments.drop_duplicates(ignore_index=True, inplace=True)

    df_comments['count'] = 1
    # compute cross table with uniques dates as index and uniques users as columns
    df_counts = pd.pivot_table(
        df_comments,
        index='created_at',
        columns='author',
        values='count',
        aggfunc=sum,
        fill_value=0,
    )

    return df_counts
