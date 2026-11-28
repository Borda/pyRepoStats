# How it works

## Scraping is incremental

The `scrape` command first asks GitHub for the cheap listing of all issues and PRs, then compares the `updated_at` stamp of each item with the cache. Only new or changed items get a detailed request for comments and reviews. The cache is written as `dump-github_<owner>-<repo>.json` in the output folder after fetching and preprocessing. An interrupted run can lose its unsaved progress or leave an incomplete cache if interrupted during the write.

![Incremental cache: only new or changed items are fetched](images/incremental-cache.svg)

If GitHub rate-limits the initial issue and PR listing, the scrape exits before saving any new progress. If the limit is reached while fetching details and the cache save completes, the next `scrape` can reuse the saved work and retry unfinished items.

## Analysis filters out the noise

By default, `analyze` reads the cache without contacting GitHub. Set `--offline false` to refresh the cache from GitHub before computing the results. Comments from bots (for example `dependabot[bot]`, `codecov`, `stale`), low-value messages such as "LGTM" or "Thanks", and anything outside the `--date_from` / `--date_to` window are dropped before the numbers are computed.

![Analyze flow: bot, spam and time filters feed per-user bars and a heatmap](images/analyze-flow.svg)
