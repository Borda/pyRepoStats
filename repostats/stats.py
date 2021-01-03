"""
Copyright (C) 2020-2020 Jiri Borovec <...>
"""
from typing import List, Optional

import pandas as pd
from tqdm import tqdm

# see: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
#: define conversion for frequency grouping
from repostats.data_io import is_in_time_period

DATETIME_FREQ = {
    'D': "%Y-%m-%d",
    'W': "%Y-w%W",
    'M': "%Y-%m",
    'Y': "%Y",
}


def compute_users_summary(items: List[dict], datetime_from: str = None, datetime_to: str = None) -> pd.DataFrame:
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
            df_self_author = df[df['author'] == user]
            # add selection if it is in range
            for c_in, c_out in [('created', 'created_at'), ('closed', 'closed_at')]:
                df_self_author[c_in] = [
                    is_in_time_period(dt, datetime_from=datetime_from, datetime_to=datetime_to)
                    for dt in df_self_author[c_out]
                ]
            df_merged = df_self_author[df_self_author['state'] == 'merged']
            df_not_author = df[df['author'] != user]
            user_stat.update({
                # count only opened cases in such time
                f'opened {tp}s': sum(df_self_author['created']),
                # count only closed/merged cases in such time
                f'merged {tp}s': sum(df_merged['closed']),
                # in this time all comments shall be already filtered and we need all issues
                #  as they can be created before time window and commented in given period...
                f'commented {tp}s': sum(df_not_author['commenters'].apply(lambda l: user in l)),
            })
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

    >>> items = [dict(created_at='2020-10-05', parent_idx=1, parent_type='issue', author='me'),
    ...          dict(created_at='2020-10-17', parent_idx=2, parent_type='PR', author='me'),
    ...          dict(created_at='2020-10-17', parent_idx=1, parent_type='issue', author='me'),
    ...          dict(created_at='2020-10-29', parent_idx=3, parent_type='issue', author='me'),
    ...          dict(created_at='2020-11-15', parent_idx=3, parent_type='issue', author='you')]
    >>> compute_user_comment_timeline(items, freq='M', parent_type='issue')  # doctest: +NORMALIZE_WHITESPACE
    author      me  you
    created_at
    2020-10      2    0
    2020-11      0    1
    """
    assert freq in DATETIME_FREQ, 'unsupported freq format, allowed: %r' % DATETIME_FREQ.keys()

    def _reformat(dt):
        return pd.to_datetime(dt).strftime(DATETIME_FREQ[freq])

    if parent_type:
        # filter issue/PR type aka comment parent
        items = [i for i in items if parent_type.lower() in i['parent_type'].lower()]

    df_comments = pd.DataFrame(items)
    # convert to date according to the freq.
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
