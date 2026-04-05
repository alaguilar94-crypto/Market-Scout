# Market Scout — Automated AI Opportunity Scanner

Runs every Monday at 8 AM CT via GitHub Actions.
Uses Claude (claude-sonnet-4-6) + web search to find overlooked ETF,
commodity, defense, and geopolitical investment opportunities.

## Setup (One-Time, ~10 Minutes)

### 1. Create the GitHub Repo
- Go to github.com → New repository
- Name it: `market-scout`
- Set to **Public** (required for free GitHub Pages)
- Do NOT initialize with README

### 2. Upload These Files
Drag and drop all files into the repo via the GitHub web interface:
```
index.html
scan.py
reports/index.json
.github/workflows/market_scan.yml
```

### 3. Add Your Anthropic API Key
- Go to your repo → Settings → Secrets and variables → Actions
- Click "New repository secret"
- Name: `ANTHROPIC_API_KEY`
- Value: your key from console.anthropic.com

### 4. Enable GitHub Pages
- Go to repo → Settings → Pages
- Source: Deploy from a branch
- Branch: `main` / `/ (root)`
- Save

### 5. Run the First Scan Manually
- Go to repo → Actions tab
- Click "Weekly Market Opportunity Scan"
- Click "Run workflow" → "Run workflow"
- Wait ~60 seconds for it to complete

### 6. View Your Dashboard
- Visit: `https://YOUR-USERNAME.github.io/market-scout/`

## Schedule
Runs automatically every **Monday at 8:00 AM Central Time**.
You can also trigger it manually anytime from the Actions tab.

## Cost
- GitHub Actions: Free (well within free tier limits)
- Anthropic API: ~$0.10–$0.50 per weekly scan
