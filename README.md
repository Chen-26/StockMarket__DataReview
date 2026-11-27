# StockMarket Data Review

A compact A-share and US-market review page with daily notes saved in the browser.

## Features

- A-share and US market index cards, watchlist table, daily market/decision/trade notes.
- GitHub Actions fetches a market snapshot every five minutes on weekdays and deploys the page to GitHub Pages.
- The page checks for a newer snapshot once per minute. Notes stay in the current browser's local storage and are not committed to the repository.

## Publish

The workflow is in `.github/workflows/pages.yml`. After pushing this repository to the `main` branch, check **Actions** for the `Publish market review` run. In **Settings �� Pages**, choose **GitHub Actions** as the build and deployment source if it is not configured automatically. GitHub Pages for a private repository requires an eligible GitHub plan. Once the first deployment succeeds, the run summary/environment contains the site URL.

The first deployment is triggered by the initial push. The scheduled refresh is set to every five minutes on weekdays (UTC); GitHub may delay scheduled runs during high load. GitHub Actions schedules have a five-minute minimum interval.

## Watchlist

Edit `WATCHLIST` in `scripts/fetch_quotes.py` to change the default markets and symbols. Yahoo Finance symbols commonly use `.SS` for Shanghai listings and `.SZ` for Shenzhen listings. Push the change to redeploy.

## Data notes

The page uses Yahoo Finance's chart endpoint, which is an undocumented interface rather than a supported public market-data API. Quotes can be delayed, rate-limited, incomplete, or unavailable. The page is for review and reference, not trading or investment advice. For guaranteed real-time data, connect a licensed provider and configure its credentials as GitHub Actions secrets.

