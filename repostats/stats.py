"""
Copyright (C) 2020-2020 Jiri Borovec <...>
"""
from typing import List

import pandas as pd
from tabulate import tabulate
from tqdm import tqdm


def compute_users_stat(
        items: List[dict],
        show: bool = True,
        min_count: int = 3,
        user_template: str = '%(user)s'
) -> pd.DataFrame:
    """Aggregate issue/PR affiliations and summary counts."""
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
    df_users = df_users[['merged PRs', 'commented PRs', 'opened issues', 'commented issues', 'all opened']]
    df_users.index = df_users.index.map(lambda u: user_template % {'user': u})

    if show:
        print(tabulate(df_users[df_users['all opened'] >= min_count], tablefmt="pipe", headers="keys"))

    return df_users
