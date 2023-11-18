# Repository Stats

![CI testing](https://github.com/Borda/pyRepoStats/workflows/CI%20testing/badge.svg?event=push)
[![codecov](https://codecov.io/gh/Borda/pyRepoStats/branch/main/graph/badge.svg?token=09H9MDJMXG)](https://codecov.io/gh/Borda/pyRepoStats)
[![CodeFactor](https://www.codefactor.io/repository/github/borda/pyrepostats/badge)](https://www.codefactor.io/repository/github/borda/pyrepostats)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/Borda/pyRepoStats.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/Borda/pyRepoStats/context:python)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Borda/pyRepoStats/main.svg)](https://results.pre-commit.ci/latest/github/Borda/pyRepoStats/main)

This simple tool aims on open-source projects providing simple repository stats which are a bit out of scope of base Git and need some more information about issues and PRs.

### Highlighted features

- cumulative **caching** (no need to full download, just incremental/needed update)
- collection of **overall user contributions** to issues/PRs
- visualization of **aggregated timeline** of past contributions

## Installation

Simple install with setuptools/pip as

```bash
pip install https://github.com/Borda/pyRepoStats/archive/main.zip
```

or after cloning the repository

```bash
python setup.py install
```

## Sample usage

Let's show how to pull data from Github repository, use of the following calls

- if you just clone this repo without installation, you need to install dependencies and call script
  ```bash
  pip install -r requirements.txt
  python repo_stats/cli.py -gh PyTorchLightning/pytorch-lightning-bolts
  ```
- if you have already installed the package with `pip` or with `setup.py` you can call executable
  ```bash
  repostat -gh PyTorchLightning/pytorch-lightning-bolts -t <your-personal-token>
  ```
  or package with a pythonic way
  ```bash
  python -m repo_stats.cli -gh PyTorchLightning/pytorch-lightning-bolts
  ```
  just note that with this way usage should also consider passing `-o` argument for output path, otherwise all caches and results will be saved in installation folder, most likely _site-packages_

To simplify the token passing in each call, you can export the token to environment variables `export GH_API_TOKEN=<your-personal-token>` for Github.

### Github use-case

For GitHub users we recommend using your personal GitHub token which significantly increases [request limit](https://developer.github.com/v3/#rate-limiting) per hour.

### Extra options

The calls above just pull the data, to get/show some results check available options `python -m repostats.cli --help`

- To see following summary table use `--users_summary "merged PRs" "commented PRs" "opened issues" "commented issues"` where the fist column is used for sorting rows with users:

  | user                                              | merged PRs | commented PRs | opened issues | commented issues |
  | :------------------------------------------------ | ---------: | ------------: | ------------: | ---------------: |
  | [williamFalcon](https://github.com/williamFalcon) |         74 |            21 |            14 |                8 |
  | [Borda](https://github.com/Borda)                 |         42 |            35 |             4 |               18 |
  | [akihironitta](https://github.com/akihironitta)   |         17 |             1 |             5 |                5 |
  | [ananyahjha93](https://github.com/ananyahjha93)   |         14 |             2 |             6 |               21 |
  | [annikabrundyn](https://github.com/annikabrundyn) |         12 |             0 |             0 |                2 |
  | [djbyrne](https://github.com/djbyrne)             |         11 |             2 |             4 |                4 |
  | [nateraw](https://github.com/nateraw)             |          9 |             1 |             6 |                8 |
  | [teddykoker](https://github.com/teddykoker)       |          3 |             2 |             0 |                0 |

- With `--min_contribution N` you can a simple filter what is the minimal number of contribution to  show users in Table or Figures.

- You can also define a time frame with `--date_from` and `--date_to` for filtering events - created issues, merged PRs and comments/reviews.

- We also offer showing some contribution aggregation over time such as Day/Week/Month/Year, to do you use option `--user_comments W` which draw following double chart: (a) cumulative aggregation over all users and (b) heatmap like image with time in Y and user in X axis.
  Moreover, you can also specify type such as issue or PR; so with `--user_comments W issue pr` you can simply get two figures - one with weekly aggregation for issue and another for PRs.
  The very same way you can specify multiple time sampling `--user_comments W M` for weekly and monthly aggregations.

  ![User-comments-aggregation](./assets/user-comments-aggregation.png)

To deny showing figures set environment variable `export SHOW_FIGURES=0`.

## Contribution

Any help or suggestions are welcome, pls use Issues :\]
