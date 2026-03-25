# Tech News Summarizer

Fetches recent **tech-only** news from RSS feeds, summarizes with AI, and sends the digest via **email** and/or **ntfy** (self-hosted push). Uses the **original article** for summaries when the feed links to it (e.g. Reddit post → linked article).

## Project structure

```
tech-news-summarizer/
├── README.md
├── requirements.txt
├── .gitea/
│   └── workflows/
│       └── tech_news_summarizer.yaml   # Deploy: build compose with repo secrets
├── app/                                # Python application
│   ├── main.py                         # Entry: fetch → summarize → send
│   ├── config.py                       # Env vars + optional Docker /run/secrets
│   ├── get_infisical_token.sh          # Optional: local Infisical universal-auth helper
│   ├── news_fetcher.py
│   ├── url_resolver.py
│   ├── article_fetcher.py
│   ├── summarizer.py
│   ├── email_sender.py
│   └── ntfy_sender.py
├── docker/
│   ├── Dockerfile                      # Infisical CLI + infisical run → python
│   └── docker-compose.yml              # ntfy + summarizer (Infisical + compose env)
└── ntfy/
    └── server.yml                      # Copy to your ntfy config dir
```

## Features

- **Tech-only**: Keeps only articles whose title/summary match tech keywords (software, AI, programming, etc.).
- **Original article for summaries**: When a feed item points to Reddit (or similar), the app resolves the **linked article URL** from the feed and uses it for fetching and summarization instead of the Reddit page.
- **Email**: Full AI digest (all articles, one summary) sent via SMTP.
- **ntfy**: Single notification with headline + 2–3 sentence summary per article (from the original article when possible), and three “Article 1/2/3” buttons that open the article. Reddit metadata is never shown as summary.

## Secrets overview

| What | Where it lives |
|------|----------------|
| **OpenAI, SMTP password, ntfy token** | [Infisical](https://infisical.com/) project (injected at container start via `infisical run`), *or* plain env vars / Docker secrets for local runs |
| **Infisical Universal Auth** | Gitea **repository secrets** (or your shell) as `CLIENT_ID`, `CLIENT_SECRET`, and the Infisical **project id** as `PROJECT_ID` |

The Docker image does **not** rely on files under `docker/secrets/` anymore. The Dockerfile logs into Infisical with Universal Auth and runs the app inside `infisical run`, so those application secrets must exist in your Infisical project for the configured environment.

### Infisical: secret names → app

[`app/config.py`](app/config.py) reads:

- **OpenAI**: Docker secret `OPENAI_API_KEY`, or env `openai_api_key`, or env `API_KEY`
- **SMTP password**: Docker secret `SMTP_PASSWORD`, or env `smtp_password`
- **ntfy Bearer token**: Docker secret `NTFY_TOKEN`, or env `ntfy_token` (optional if your ntfy server allows anonymous publish)

Create Infisical secrets whose names match those env keys (e.g. `openai_api_key`, `smtp_password`, `ntfy_token`) for the environment you set in `INF_ENV` (see `docker/docker-compose.yml`).

### Docker Compose: Infisical-related env vars

The **summarizer** service passes:

- `INFISICAL_API_URL` – your Infisical instance URL (passed to the CLI as `--domain`)
- `INFISICAL_UNIVERSAL_AUTH_CLIENT_ID` / `INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET` – from host env `${CLIENT_ID}` / `${CLIENT_SECRET}`
- `INF_PROJECT_ID` – from host `${PROJECT_ID}` (same value as the Infisical project id)
- `INF_ENV` – Infisical environment slug (e.g. `synology`; change to match your project)

Before `docker compose up`, export on the host (or provide via CI):

```bash
export CLIENT_ID=...        # Infisical Universal Auth client id
export CLIENT_SECRET=...    # Infisical Universal Auth client secret
export PROJECT_ID=...       # Infisical project id
```

### Gitea Actions

Workflow: [`.gitea/workflows/tech_news_summarizer.yaml`](.gitea/workflows/tech_news_summarizer.yaml).

Configure these **repository secrets** in Gitea (Settings → Secrets):

| Secret | Purpose |
|--------|---------|
| `CLIENT_ID` | Infisical Universal Auth client id |
| `CLIENT_SECRET` | Infisical Universal Auth client secret |
| `PROJECT_ID` | Infisical project id (wired to `INF_PROJECT_ID` in compose) |

The job sets `CLIENT_ID`, `CLIENT_SECRET`, and `PROJECT_ID` in its environment, then runs `docker compose` from the `docker/` project directory. The runner must be able to run Docker and reach your host layout (the sample workflow uses paths such as `/volume1/docker/ntfy`—adjust for your NAS or runner).

### Optional: local Infisical token helper

[`app/get_infisical_token.sh`](app/get_infisical_token.sh) performs universal auth using:

- `INF_DOMAIN`, `INF_CLIENT_ID`, `INF_CLIENT_SECRET`, `INF_PROJECT_ID`

(useful for debugging the CLI outside the container).

## Step-by-step setup

### 1. Install dependencies

```bash
cd /path/to/tech-news-summarizer
pip install -r requirements.txt
```

### 2. Configure environment

**Running with Docker (recommended path in this repo)**

1. In Infisical, add the application secrets for the environment matching `INF_ENV`.
2. Create a Universal Auth identity and note client id, client secret, and project id.
3. Set `CLIENT_ID`, `CLIENT_SECRET`, and `PROJECT_ID` on the host (or in Gitea secrets for CI).
4. Edit `docker/docker-compose.yml` for non-secret settings (`SMTP_*`, `EMAIL_*`, `NTFY_*`, `INFISICAL_API_URL`, `INF_ENV`, time zone, etc.).

**Running locally without Docker / Infisical**

Set secrets via environment variables (names as in `config.py`, e.g. `openai_api_key`, `smtp_password`, `ntfy_token`) or, if you use Docker Swarm-style secrets, mount files under `/run/secrets/` named `OPENAI_API_KEY`, `SMTP_PASSWORD`, `NTFY_TOKEN`.

**Non-secret env vars** (also set in compose `environment:` for the summarizer):

- `SMTP_HOST` (default `smtp.gmail.com`)
- `SMTP_PORT` (default `587`)
- `SMTP_USER`
- `EMAIL_TO`
- `EMAIL_FROM` (defaults to `SMTP_USER` if unset)
- `NTFY_BASE_URL` (e.g. internal URL if ntfy is another service on the same host)
- `NTFY_TOPIC` (default `tech-news-digest`)
- `MAX_ARTICLES` (default `3`)
- `OPENAI_MODEL` (default `gpt-4o-mini`)

For ntfy: copy `ntfy/server.yml` to your ntfy config directory so the server loads it on start.

### 3. Run

You must pass at least one of `--email` or `--ntfy` when not using `--dry-run`:

```bash
# From repo root
# Fetch and summarize only (no send)
python app/main.py --dry-run

# Send by email only
python app/main.py --email

# Send to ntfy only
python app/main.py --ntfy

# Send to both
python app/main.py --email --ntfy
```

### 4. Run every day

**Cron (recommended for bare-metal Python):**

```bash
crontab -e
```

Add (example: 8:00 AM, email + ntfy):

```
0 8 * * * cd /path/to/tech-news-summarizer && python3 app/main.py --email --ntfy
```

**Built-in scheduler (used by the Docker image):**

```bash
python app/main.py --schedule --email --ntfy
```

Runs the digest three times a day at 08:00, 15:00 and 22:00 (local time). The Docker container’s default command uses `--schedule` with Infisical-wrapped execution.

## Flow summary

1. **news_fetcher** – Fetches from Hacker News, TechCrunch, Ars Technica, The Verge, Wired, NYT Technology, Reddit r/technology and r/programming. For Reddit entries, resolves the **original article URL** from the feed (summary HTML or `entry.links`). Filters to **tech-only** (keyword match). Sorts by date and returns up to `MAX_ARTICLES` (default **3**).
2. **summarizer** – Builds one **full digest** for email (all articles, one AI summary). For ntfy, fetches each article’s page (skips Reddit URLs), extracts text, and gets a **2–3 sentence brief** per article from OpenAI.
3. **email_sender** – Sends the full digest in one email.
4. **ntfy_sender** – Sends one notification: intro line, then for each article a bold+italic headline, blank line, brief summary (or “Summary unavailable” when we can’t get the original article), and three “Article 1/2/3” buttons that open the article. Reddit metadata is never used as summary.

## Optional env vars

| Variable         | Default     | Description                              |
|------------------|-------------|------------------------------------------|
| `MAX_ARTICLES`   | 3           | Number of articles to fetch and send     |
| `OPENAI_MODEL`  | gpt-4o-mini | Model for summarization                  |
| `EMAIL_FROM`    | SMTP_USER   | Sender address in email                  |
| `NTFY_BASE_URL` | —           | ntfy server URL (e.g. https://ntfy.example.com) |
| `NTFY_TOPIC`    | tech-news-digest | ntfy topic                          |
| `NTFY_TOKEN`    | —           | Bearer token for ntfy auth (or Infisical `ntfy_token`) |

After setup, run with `--email` and/or `--ntfy`, or use cron / `--schedule` for repeated runs.
