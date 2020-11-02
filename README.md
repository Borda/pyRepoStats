# Repository Stats

![CI testing](https://github.com/Borda/pyRepoStats/workflows/CI%20testing/badge.svg?event=push)
[![codecov](https://codecov.io/gh/Borda/pyRepoStats/branch/main/graph/badge.svg?token=09H9MDJMXG)](https://codecov.io/gh/Borda/pyRepoStats)
[![CodeFactor](https://www.codefactor.io/repository/github/borda/pyrepostats/badge)](https://www.codefactor.io/repository/github/borda/pyrepostats)

This simple tool aims on open-source projects providing simple repository stats which are a bit out of scope of base Git and need some more information about issues and PRs.

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

Lets show how to pull data from Github repository, use of the following calls
* if you just clone this repo without installation, you need to install dependencies and call script
    ```bash
    pip install -r requirements.txt
    python repostats/cli.py -gh PyTorchLightning/pytorch-lightning-bolts -t <your-personal-token>
    ```
* if you have already installed the package with `pip` or with `setup.py` you can call executable
    ```bash
    repostat -gh PyTorchLightning/pytorch-lightning-bolts -t <your-personal-token>
    ```
  or package with a pythonic way
    ```bash
    python -m repostats.cli -gh PyTorchLightning/pytorch-lightning-bolts
    ```
  just note that with this way usage should also consider passing `-o` argument for output path, otherwise all caches and results will be saved in installation folder, most likely _site-packages_

### Github use-case

For GitHub users we recommend using your personal GitHub token which significantly increases [request limit](https://developer.github.com/v3/#rate-limiting) per hour.

### Extra options

The calls above just pull the data, to get/show some results check available options `python -m repostats.cli --help`

To see following summary table use `--users_summary`
```
| user          |   merged PRs |   commented PRs |   opened issues |   commented issues |   all opened |
|:--------------|-------------:|----------------:|----------------:|-------------------:|-------------:|
| williamFalcon |           74 |              21 |              14 |                  8 |           95 |
| Borda         |           39 |              26 |               4 |                 17 |           44 |
| akihironitta  |           15 |               0 |               3 |                  4 |           23 |
| ananyahjha93  |           11 |               1 |               5 |                 10 |           21 |
| djbyrne       |           11 |               2 |               4 |                  4 |           19 |
| nateraw       |            9 |               1 |               6 |                  8 |           17 |
| annikabrundyn |           12 |               0 |               0 |                  2 |           12 |
| oke-aditya    |            1 |               1 |               5 |                  2 |            8 |
| HenryJia      |            1 |               0 |               3 |                  0 |            5 |
| edenlightning |            0 |               2 |               3 |                  2 |            4 |
| teddykoker    |            3 |               2 |               0 |                  0 |            3 |
```

## Contribution

Any help or suggestions are welcome, pls use Issues :]
