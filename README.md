# SC Scout Reddit Connector

This repository contains the **read-only Reddit Data API connector** used by the non-commercial SC Scout prototype.

SC Scout is a consumer-monitoring application intended to identify emerging reports of changes in pricing, product or service value, subscription terms, fees, access restrictions, cancellation friction, reduced functionality, deteriorating service and similar commercial practices.

This public repository intentionally contains only the Reddit-facing connector. It does **not** contain the wider SC Scout detection pipeline, model prompts, private project logic, API credentials, or personal data.

## What the connector does

The connector:

- reads newly published **public posts** from a limited list of selected public subreddits;
- retrieves the public post title and body text;
- retrieves basic public metadata such as subreddit, publication time, score and comment count;
- stores the Reddit post ID and URL for deduplication and later manual review;
- writes the retrieved records to a local JSONL file for further analysis outside Reddit.

The connector is **read-only**. It does not:

- post or comment;
- vote;
- send messages;
- moderate communities;
- access private messages;
- access private subreddits;
- alter Reddit content.

Reddit content is not used to train an AI or machine-learning model. In the wider private SC Scout prototype, automated language-model analysis may classify individual public posts for relevance to consumer issues. Relevant posts are treated as signals for manual review, not as verified evidence.

## Example use cases

The downstream SC Scout pipeline may surface posts describing situations such as:

- a subscription price increase accompanied by removal or restriction of features;
- a new or increased consumer fee;
- a retailer or travel provider making refunds or cancellation materially more difficult;
- a loyalty programme providing less value for the same level of spending;
- a product or service becoming materially worse, more restrictive or more expensive following a recent commercial change.

Basic public engagement information such as scores and comment counts may be used to help identify issues attracting unusually high attention within a subreddit.

## Configuration

The connector expects three environment variables:

```text
SCOUT_REDDIT_CLIENT_ID
SCOUT_REDDIT_CLIENT_SECRET
SCOUT_REDDIT_USER_AGENT
```

See `.env.example` for placeholder names only. **Never commit real credentials.**

Subreddits are configured in a JSON file. `example_config.json` contains illustrative placeholders and should be replaced with the approved communities for the application.

## Installation

```bash
python -m venv .venv
```

On Windows:

```cmd
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```cmd
python reddit_connector.py --config example_config.json --output reddit_posts.jsonl --limit 25
```

The output is line-delimited JSON containing only the public fields retrieved for this purpose.

## Data minimisation

The connector requests only the data needed to identify and review relevant public posts. It does not intentionally collect private Reddit data. Production use should comply with Reddit's current Data API terms, rate limits, deletion requirements and any conditions attached to the application's approval.

## Status

This repository represents an early-stage, non-commercial prototype prepared for Reddit API review.
