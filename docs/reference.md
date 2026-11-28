# Reference

## Output files

Everything lands in `--output_path`:

| File                                                          | Content                               |
| :------------------------------------------------------------ | :------------------------------------ |
| `dump-github_<owner>-<repo>.json`                             | the cache written by `scrape`         |
| `github_<owner>-<repo>_users-summary.csv`                     | per-user table                        |
| `github_<owner>-<repo>_user-comments_freq_<F>_type_<T>.csv`   | timeline table                        |
| `github_<owner>-<repo>_user-comments_freq_<F>_type_<T>.<ext>` | timeline figure (`pdf`, `png`, `svg`) |

## Environment variables

| Variable                   | Effect                                                                        |
| :------------------------- | :---------------------------------------------------------------------------- |
| `GH_API_TOKEN`             | GitHub token, takes priority over the variables below                         |
| `GITHUB_TOKEN`, `GH_TOKEN` | GitHub token, as used by GitHub Actions and `gh`                              |
| `SHOW_FIGURE`              | set `SHOW_FIGURE=0` to skip opening figure windows, e.g. on a server or in CI |
