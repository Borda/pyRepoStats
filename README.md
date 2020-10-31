# Repository Stats

![CI testing](https://github.com/Borda/pyRepoStats/workflows/CI%20testing/badge.svg?event=push)

This simple tool aims on open-source projects providing simple repository stats which are a bit out of scope of base Git and need some more information about issues and PRs.

## Installation

Simple install with setuptools/pip as 
```bash
pipp install https://github.com/Borda/pyRepoStats/archive/main.zip
```
or after cloning the repository
```bash
python setup.py install
```

## Sample usage

Lets show how to pull data from Github repository
```bash
python repostats/cli.py -gh PyTorchLightning/pytorch-lightning-bolts -t <your-personal-token>
```

With your personal GitHub token you have significantly increased [request limit](https://developer.github.com/v3/#rate-limiting) per hour.

The call results with
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