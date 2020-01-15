# Tippecanews
[![github actions](https://github.com/fatcat2/tippecanews/workflows/Python%20application/badge.svg)](https://github.com/fatcat2/tippecanews)
[![codecov](https://codecov.io/gh/fatcat2/tippecanews/branch/master/graph/badge.svg)](https://codecov.io/gh/fatcat2/tippecanews)

This is a Cloud Run function that checks a certain list of RSS feeds and stores them in a Firestore database if there are no duplicates.

Tippecanews also sends new Purdue News articles to a specified Slack channel

You can find a full list of tippecanews functions at https://tippecanews.ryanjchen.com.

## Instructions
Create a `.env` file that has a line setting the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the filepath to you auth JSON file. The `.env` file should also include the `SLACK_TOKEN` and `SLACK_CHANNEL` environment variables.

## TODO
* Add Google Sheets integration
