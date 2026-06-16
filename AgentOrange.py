import requests
import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()

def get_kalshi_markets():
    url = "https://api.elections.kalshi.com/trade-api/v2/markets"
    params = {"limit": 10, "status": "open"}
    response = requests.get(url)
    return response.json().get("markets", [])

def research_market(title, yes_price):
    prompt = f"""
    Prediction market: "{title}"
    Current YES price: {yes_price}% implied probability
    
    Research this market and give me:
    1. Your estimated probability (0-100)
    2. Key factors affecting the outcome
    3. Recommendation: bet_yes, bet_no, or skip
    Keep it brief.
    """
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def main():
    print("Fetching markets from Kalshi...")
    markets = get_kalshi_markets()
    
    for market in markets[:5]:
        title = market.get("title", "Unknown")
        yes_price = market.get("yes_ask", 50)
        print(f"\n{'='*50}")
        print(f"Market: {title}")
        print(f"Current odds: {yes_price}%")
        print(f"Analysis:")
        print(research_market(title, yes_price))

if __name__ == "__main__":
    main()
