__version__ = "0.1.1"
__author__ = "Jiri Borovec"
__author_email__ = "j.borovec@...cz"
__license__ = "MIT"
__homepage__ = "https://borda.github.io/pyRepoStats",
__copyright__ = "Copyright (c) 2020-2020, %s." % __author__
__doc__ = 'Repository Statistics'
__long_doc__ = "# %s" % __doc__ + """

This simple tool aims on open-source projects providing simple repository stats
 which are a bit out of scope of base Git and need some more information about issues and PRs.
"""

try:
    import pandas as pd
except ImportError:
    print('Package `pandas` which shall be configured are missing...')  # pragma: no-cover
else:
    # default display size was changed in pandas v0.23
    pd.set_option('display.max_columns', 20)
