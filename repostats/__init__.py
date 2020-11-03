__version__ = "0.1.0"
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

import os
import subprocess

try:
    import matplotlib
except ImportError:
    print('Package `matplotlib` which shall be configured are missing...')
else:
    CMD_TRY_MATPLOTLIB = 'python -c "from matplotlib import pyplot; pyplot.close(pyplot.figure())"'
    # in case you are running on machine without display, e.g. server
    if not os.environ.get('DISPLAY', '') and matplotlib.rcParams['backend'] != 'agg':
        print('No display found. Using non-interactive Agg backend')
        matplotlib.use('Agg')
    # _tkinter.TclError: couldn't connect to display "localhost:10.0"
    elif subprocess.call(CMD_TRY_MATPLOTLIB, stdout=None, stderr=None, shell=True):
        print('Problem with display. Using non-interactive Agg backend')
        matplotlib.use('Agg')


try:
    import pandas as pd
except ImportError:
    print('Package `pandas` which shall be configured are missing...')
else:
    # default display size was changed in pandas v0.23
    pd.set_option('display.max_columns', 20)
