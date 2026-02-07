# AI-Powered Learning Feed Curator

A personal content curation system that ingests from Twitter, newsletters (RSS), and GitHub Trending, scores content against your learning goals using GPT-4o, and delivers a daily email digest with feedback tracking.

## How It Works

```
GitHub Actions (daily 6 AM UTC)
  -> Load your Learning Context from Supabase
  -> Ingest from Twitter (Apify) + RSS feeds + GitHub Trending
  -> Deduplicate by URL
  -> Score each item 0-10 with GPT-4o against your goals
  -> Build HTML email: Top 3 Must-Reads + remaining (score >= 5.0)
  -> Send via Resend
  -> Track precision from previous feedback
```

Each email includes **Useful / Not Useful** buttons per item. Clicking them records feedback to Supabase via the FastAPI feedback API, which is used to calculate precision and trigger alerts if recommendations degrade.

## Architecture

| Component | Tech | Deployment |
|-----------|------|------------|
| Pipeline | Python + GitHub Actions cron | GitHub Actions |
| Feedback API | FastAPI | Render (free tier) |
| Learning Context UI | Streamlit | Streamlit Community Cloud |
| Database | PostgreSQL | Supabase (free tier) |
| Email | Resend | API (free 3K/month) |
| LLM Scoring | GPT-4o | OpenAI API |
| Twitter Scraping | Apify `tweet-scraper` | Apify (free $5/month) |
| Newsletters | RSS via `feedparser` | Built-in |

## Project Structure

```
src/
  config.py              # Pydantic settings, env vars
  models.py              # ContentItem, ScoredItem, LearningContext
  db.py                  # Supabase CRUD helpers
  pipeline.py            # Main daily orchestrator
  ingestion/
    newsletters.py       # RSS feed parsing (feedparser)
    twitter.py           # Apify tweet-scraper (lists + handles)
    youtube.py           # YouTube Data API v3 (optional)
  scoring/
    scorer.py            # GPT-4o batch scoring (12 items/batch)
  digest/
    builder.py           # HTML email builder
    templates/
      digest.html        # Jinja2 email template
  delivery/
    emailer.py           # Resend wrapper
  feedback/
    api.py               # FastAPI: /feedback, /health, /stats
  monitoring/
    precision.py         # Precision tracking + low-precision alerts
streamlit_app/
  app.py                 # Learning Context web form
scripts/
  init_db.sql            # Supabase table creation
  seed_context.py        # Seed default learning context
tests/
  test_ingestion.py
  test_scoring.py
  test_digest.py
  test_pipeline.py
.github/workflows/
  daily_digest.yml       # Daily cron + manual trigger
```

## Setup

### 1. Clone and install

```bash
git clone https://github.com/Siddhant-Goswami/MVP-c6-test.git
cd MVP-c6-test
pip install -r requirements.txt
```

### 2. Create Supabase tables

Go to your Supabase project -> SQL Editor -> run the contents of `scripts/init_db.sql`.

This creates 5 tables: `learning_context`, `learning_context_history`, `digest_items`, `feedback`, `digest_log`.

### 3. Configure environment

```bash
cp .env.example .env
```

Fill in your keys:

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key (bypasses RLS) |
| `SUPABASE_ANON_KEY` | Supabase anon key (for Streamlit) |
| `OPENAI_API_KEY` | OpenAI API key |
| `APIFY_API_TOKEN` | Apify API token |
| `RESEND_API_KEY` | Resend API key |
| `DIGEST_RECIPIENT_EMAIL` | Your email address |
| `DIGEST_FROM_EMAIL` | Sender email (e.g. `onboarding@resend.dev`) |
| `FEEDBACK_API_URL` | Public URL of the feedback API |
| `TWITTER_LIST_URLS` | Comma-separated Twitter/X list URLs |
| `TWITTER_HANDLES` | Comma-separated Twitter handles (no @) |
| `RSS_FEED_URLS` | Comma-separated RSS feed URLs |
| `YOUTUBE_CHANNEL_IDS` | Comma-separated YouTube channel IDs (optional) |
| `STREAMLIT_APP_URL` | Deployed Streamlit app URL |

### 4. Seed learning context

```bash
python scripts/seed_context.py
```

### 5. Run locally

```bash
# Run the full pipeline
python -m src.pipeline

# Start the feedback API
uvicorn src.feedback.api:app --reload

# Start the Streamlit UI
streamlit run streamlit_app/app.py
```

## Deployment

### Feedback API (Render)

1. Create a new **Web Service** on [render.com](https://render.com)
2. Connect this GitHub repo
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `uvicorn src.feedback.api:app --host 0.0.0.0 --port $PORT`
5. Add all environment variables from `.env`

### Streamlit UI (Streamlit Community Cloud)

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Deploy from this repo, main file: `streamlit_app/app.py`
3. Add secrets in TOML format:
   ```toml
   SUPABASE_URL = "your-url"
   SUPABASE_ANON_KEY = "your-anon-key"
   ```

### GitHub Actions (daily cron)

Add all env vars as **repository secrets** under Settings -> Secrets -> Actions. The workflow runs daily at 6 AM UTC and can be triggered manually via Actions -> Daily Learning Digest -> Run workflow.

## Database Schema

| Table | Purpose |
|-------|---------|
| `learning_context` | Single row with your goals, skills, methodology |
| `learning_context_history` | Snapshots on every update |
| `digest_items` | Scored items per digest (unique on url + date) |
| `feedback` | User responses (useful / not_useful) |
| `digest_log` | Pipeline run tracking, precision rates |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/feedback/{item_id}?response=useful\|not_useful` | Record feedback, return thank-you page |
| `GET` | `/health` | Health check |
| `GET` | `/stats?days=7` | Recent precision rates |
| `POST` | `/trigger` | Manual pipeline trigger |

## Key Design Decisions

- **Feedback via GET requests** — email clients block POST/JS, so feedback links are simple GET URLs
- **Graceful degradation** — if any source fails, the pipeline continues with remaining sources
- **Batch scoring** — 12 items per GPT-4o call to reduce API costs (~$0.02-0.05/day)
- **Lazy config loading** — `get_settings()` with `@lru_cache` so tests run without env vars
- **RT filtering** — retweets are excluded from scoring to reduce noise
- **Precision monitoring** — alerts via email if precision drops below 60% for 3 consecutive days

## Running Tests

```bash
python -m pytest tests/ -v
```
