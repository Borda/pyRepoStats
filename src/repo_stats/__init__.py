from repo_stats.__about__ import *  # noqa: F403

try:
    import pandas as pd
except ImportError:
    print("Package `pandas` which shall be configured are missing...")  # pragma: no-cover
else:
    # default display size was changed in pandas v0.23
    pd.set_option("display.max_columns", 20)
