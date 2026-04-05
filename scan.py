"""
Market Scout Agent
Runs weekly via GitHub Actions. Calls Claude with web search to find
overlooked investment opportunities across 4 sectors.
"""

import anthropic
import json
import os
from datetime import datetime, timezone

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SCAN_PROMPT = """You are a financial market intelligence analyst specializing in finding hidden and overlooked investment opportunities — particularly small ETFs, commodity plays, and geopolitical event trades that most retail investors miss before they go mainstream.

Today is {date}. Conduct a thorough web search analysis across these 4 sectors. Use multiple web searches before answering.

━━━ SECTOR 1: GEOPOLITICAL EVENTS & ETF OPPORTUNITIES ━━━
Search for: active conflicts, sanctions, trade route disruptions, maritime blockades,
supply chain crises, and the ETFs that directly benefit from them.
Target: Small or niche ETFs (<$500M AUM) with unusual volume or price action.
Reference example: BWET (tanker ETF) surged 1,000%+ when Hormuz closed — most investors
missed it because it had only $3M AUM before the war. Find the next BWET.

━━━ SECTOR 2: COMMODITY & ENERGY MARKETS ━━━
Search for: commodity supply shocks, unexpected shortages, demand surges, futures
markets in extreme backwardation (near-term scarcity premium above long-term price).
Target: Commodity ETFs or futures-tracking funds that capture physical supply disruptions.

━━━ SECTOR 3: DEFENSE & AEROSPACE ━━━
Search for: recent large defense contracts not yet widely covered, NATO/allied nation
procurement increases, new drone/missile/cyber programs being funded, defense ETFs
with upcoming earnings catalysts.
Target: Individual defense stocks or ETFs with identifiable near-term catalysts.

━━━ SECTOR 4: OVERLOOKED ETFs & SMALL FUNDS ━━━
Search for: ETFs with AUM under $100M that are experiencing unusual volume spikes,
funds covering niche industries suddenly in the news, any ETF that Bloomberg or
major financial media has not yet covered but is quietly outperforming.
Target: The fund that is already moving but hasn't been written about yet.

━━━ EVALUATION CRITERIA ━━━
For each opportunity ask:
- Is this truly overlooked, or is it already on every finance blog?
- Is there a specific, identifiable catalyst that is not yet fully priced in?
- What is the realistic exit condition — when exactly does this trade end?
- What could go wrong, and how fast could it unwind?

Search extensively. Check financial news, ETF databases, shipping/commodity trackers,
defense contract databases, and geopolitical news sources.

Respond ONLY with a valid JSON object. No markdown fences, no explanation, no preamble.
Use exactly this schema:

{{
  "scan_date": "{date}",
  "scan_timestamp": "{timestamp}",
  "market_context": "2-3 sentence summary of the current macro and geopolitical environment relevant to these sectors",
  "opportunities": [
    {{
      "rank": 1,
      "ticker": "TICKER",
      "name": "Full Fund or Company Name",
      "sector": "Geopolitical/ETF | Commodity/Energy | Defense/Aerospace | Overlooked ETF",
      "opportunity_type": "Short label e.g. Supply Shock, Geopolitical Catalyst, Contract Catalyst",
      "confidence_score": 8,
      "risk_level": "Low | Medium | High | Very High",
      "time_horizon": "e.g. 1-2 weeks | 1-3 months | 3-6 months",
      "current_price_approx": "$XX",
      "aum_approx": "$XXM or $XXB",
      "ytd_return_approx": "+XX%",
      "is_overlooked": true,
      "rationale": "2-3 sentences: what is the opportunity, why is it overlooked, what is the specific catalyst",
      "key_catalysts": ["specific catalyst 1", "specific catalyst 2"],
      "key_risks": ["specific risk 1", "specific risk 2"],
      "exit_trigger": "The specific condition that signals this trade is over — be concrete",
      "how_to_buy": "Where and how a retail investor can access this (ETF on NYSE, brokerage, etc.)",
      "sources": ["headline or URL supporting this thesis"]
    }}
  ],
  "events_to_watch": [
    "Specific upcoming event that could create or destroy opportunities — include approximate date if known"
  ],
  "sectors_to_avoid": [
    "Sector name: specific reason to avoid right now"
  ],
  "agent_notes": "Any important caveats, data limitations, or meta-observations about this scan"
}}

Requirements:
- Find 4 to 8 opportunities minimum
- Only include opportunities with confidence_score >= 6
- Rank by confidence_score descending
- Be concrete and specific — vague opportunities are useless
- If you cannot find enough real opportunities in a sector, say so in agent_notes
- Do NOT fabricate tickers or prices — only report what you found in web searches
"""


def run_scan():
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    timestamp_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    prompt = SCAN_PROMPT.format(date=date_str, timestamp=timestamp_str)

    print(f"[{timestamp_str}] Starting market scan for {date_str}...")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}]
    )

    # Extract all text blocks from response
    full_text = ""
    for block in response.content:
        if hasattr(block, "type") and block.type == "text":
            full_text += block.text

    print(f"Response received. Parsing JSON...")

    # Parse JSON — strip markdown fences if model added them
    try:
        clean = full_text.strip()
        if clean.startswith("```"):
            parts = clean.split("```")
            clean = parts[1] if len(parts) > 1 else clean
            if clean.startswith("json"):
                clean = clean[4:]
        clean = clean.strip()
        data = json.loads(clean)
        n = len(data.get("opportunities", []))
        print(f"Parsed successfully. Found {n} opportunities.")
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        data = {
            "scan_date": date_str,
            "scan_timestamp": timestamp_str,
            "market_context": "Scan failed — see agent_notes.",
            "opportunities": [],
            "events_to_watch": [],
            "sectors_to_avoid": [],
            "agent_notes": f"JSON parse failed: {str(e)}. Raw snippet: {full_text[:300]}"
        }

    # Save dated report
    os.makedirs("reports", exist_ok=True)
    report_path = f"reports/{date_str}.json"
    with open(report_path, "w") as f:
        json.dump(data, f, indent=2)

    # Overwrite latest.json
    with open("reports/latest.json", "w") as f:
        json.dump(data, f, indent=2)

    # Update index
    _update_index(date_str)

    print(f"Saved: {report_path}")
    print(f"Updated: reports/latest.json")
    return data


def _update_index(new_date):
    index_path = "reports/index.json"
    if os.path.exists(index_path):
        with open(index_path) as f:
            index = json.load(f)
    else:
        index = {"reports": []}

    if new_date not in index["reports"]:
        index["reports"].insert(0, new_date)
    index["reports"] = index["reports"][:52]  # keep one year

    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)


if __name__ == "__main__":
    run_scan()
