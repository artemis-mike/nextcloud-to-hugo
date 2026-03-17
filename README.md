# nextcloud-to-hugo
Creates MRs for hugo blogs if findings new files on a nextcloud directory


# Usage
## Configuration
| Variable                  | Description | Default |
|---------------------------|-------------|---------|
| NEXTCLOUD_URL             | URL to your Nextcloud | "" |
| NEXTCLOUD_USERNAME        | User for authentication | "" |
| NEXTCLOUD_PASSWORD        | Password for authentication (app-password recommended) | "" |
| WATCH_DIRECTORY           | Directory on nextcloud to watch for changes | `Öffentlichkeitsarbeit` |
| GITHUB_REPO_NAME          | User-Repo-name-combination of the hugo blog repository (<user>/<repo>) | "" |
| HUGO_REPO_URL             | URL of the repository of GITHUB_REPO_NAME | "" |
| GITHUB_TOKEN              | Token with `read/write` permission on the hugo-blog repository | "" |
| GITHUB_BRANCH             | The blog branch to use as target | `main` |
| LOGLEVEL                  | Python log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |  `INFO` |
| INTERVAL                  | How long to wait between checks on nextcloud in seconds | `3600` |