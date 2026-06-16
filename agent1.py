import requests
import os
import csv
from datetime import datetime
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()

CLIMATE_KEYWORDS = [
    "climate", "temperature", "hurricane", "wildfire",
    "flood", "drought", "emissions", "carbon", "storm",
    "rainfall", "sea level", "tornado", "heat wave",
    "renewable", "solar", "wind energy", "glacier"
]

def get_kalshi_markets():
    url = "https://api.elections.kalshi.com/trade-api/v2/markets"
    params = {"limit": 100, "status": "open"}
    response = requests.get(url, params=params)
    return response.json().get("markets", [])

def is_climate_market(title):
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in CLIMATE_KEYWORDS)

def get_full_title(market):
    title = market.get("title", "")
    subtitle = market.get("subtitle", "")
    if subtitle:
        return f"{title} - {subtitle}"
    return title

def analyze_market(title, market_odds):
    prompt = f"""Prediction market: "{title}"
Market odds: {market_odds}% chance of YES.
Reply in this exact format:
PROBABILITY: [your estimated 0-100]
EDGE: [your probability minus {market_odds}]
RECOMMENDATION: [BET_YES or BET_NO or SKIP]
REASON: [one sentence]"""
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def parse_response(response):
    lines = response.strip().split("\n")
    result = {}
    for line in lines:
        if "PROBABILITY:" in line:
            try:
                result["probability"] = float(line.split(":")[1].strip())
            except:
                result["probability"] = None
        if "EDGE:" in line:
            try:
                result["edge"] = float(line.split(":")[1].strip())
            except:
                result["edge"] = None
        if "RECOMMENDATION:" in line:
            result["recommendation"] = line.split(":")[1].strip()
        if "REASON:" in line:
            result["reason"] = line.split(":")[1].strip()
    return result

def log_result(title, odds, analysis):
    with open("results.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            title,
            odds,
            analysis.get("probability"),
            analysis.get("edge"),
            analysis.get("recommendation"),
            analysis.get("reason")
        ])

def main():
    print("Fetching markets from Kalshi...")
    markets = get_kalshi_markets()

    climate_markets = []
    for market in markets:
        title = get_full_title(market)
        if is_climate_market(title):
            climate_markets.append((title, market))

    print(f"Found {len(climate_markets)} climate-related markets")

    if len(climate_markets) == 0:
        print("No climate markets found. Try running again later.")
        print("Showing all markets instead...")
        climate_markets = [(get_full_title(m), m) for m in markets[:10]]

    actionable = 0
    for title, market in climate_markets:
        odds = market.get("yes_ask", 50)
        response = analyze_market(title, odds)
        analysis = parse_response(response)
        edge = analysis.get("edge", 0) or 0
        recommendation = analysis.get("recommendation", "SKIP")
        if recommendation == "SKIP" or abs(edge) < 10:
            continue
        actionable += 1
        print("\n==================================================")
        print(f"Market: {title}")
        print(f"Market odds: {odds}%")
        print(f"Claude odds: {analysis.get('probability')}%")
        print(f"Edge: {edge}%")
        print(f"Recommendation: {recommendation}")
        print(f"Reason: {analysis.get('reason')}")
        log_result(title, odds, analysis)

    if actionable == 0:
        print("\nNo actionable climate bets found today.")
    else:
        print(f"\n{actionable} actionable bets logged to results.csv")

if __name__ == "__main__":
    main()
