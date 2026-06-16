import yfinance as yf
from dotenv import load_dotenv
from google import genai
import os

# Load API key
load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# User input
ticker = input("Enter stock ticker: ")

print(f"Fetching data for {ticker}...")

# Fetch stock data
stock = yf.Ticker(ticker)
info = stock.info

# Extract useful fields
current_price = info.get("currentPrice")
high_52 = info.get("fiftyTwoWeekHigh")
low_52 = info.get("fiftyTwoWeekLow")

# Create prompt
prompt = f"""
Stock: {ticker}

Current Price: {current_price}
52 Week High: {high_52}
52 Week Low: {low_52}

Given this data, explain in 2 sentences what it tells an investor.
"""

# Send to Gemini
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt
)

# Print analysis
print("\nAI Analysis:")
print(response.text)