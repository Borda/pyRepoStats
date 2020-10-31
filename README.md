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

