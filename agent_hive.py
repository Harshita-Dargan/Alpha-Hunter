import yfinance as yf
import pandas as pd
import logging
from concurrent.futures import ThreadPoolExecutor
import google.generativeai as genai
import json

def fetch_ticker_data(s, ticker):
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5d")
        if not hist.empty:
            price = float(hist['Close'].iloc[-1])
            change = float(hist['Close'].pct_change().iloc[-1] * 100)
            import math
            if math.isnan(change):
                change = 0.0
                
            return s, {
                "price": round(price, 2),
                "day_change": round(change, 2)
            }
    except Exception as e:
        logging.warning(f"Failed to fetch {ticker}: {e}")
    return s, None

def resolve_tickers_with_llm(symbols, api_key):
    try:
        genai.configure(api_key=api_key)
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = available[0] if available else 'gemini-1.5-flash'
        model = genai.GenerativeModel(model_name)
        prompt = f"""Map these Indian stock/mutual fund names to their exact Yahoo Finance ticker symbol (e.g., RELIANCE.NS, TCS.NS). 
        If it's an Indian stock, it typically ends in .NS or .BO. If it's a mutual fund, find the closest ETF or index if needed, or return null.
        Symbols to map: {symbols}. Return ONLY valid JSON in format {{"Fund Name": "TICKER.NS"}}. Do not return markdown blocks."""
        import time
        import re
        for attempt in range(4):
            try:
                response = model.generate_content(prompt)
                return json.loads(response.text)
            except Exception as e:
                err_str = str(e)
                if ('429' in err_str or 'Quota' in err_str) and attempt < 3:
                    match = re.search(r'retry in (\d+\.?\d*)s', err_str)
                    wait_time = float(match.group(1)) + 1 if match else 15
                    logging.warning(f"Rate limit hit. Waiting {wait_time}s before retry {attempt+1}")
                    time.sleep(wait_time)
                else:
                    raise e
    except Exception as e:
        logging.error(f"Ticker resolution failed: {e}")
        return {}

def get_portfolio_context(df, api_key):
    df.columns = df.columns.str.strip()
    symbols = [str(s).upper().strip() for s in df['Fund Name'].unique() if pd.notna(s) and s != 'Valuation']
    
    ticker_map = resolve_tickers_with_llm(symbols, api_key)
    
    context = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for s in symbols:
            # Fallback to .NS approximation if LLM failed
            ticker = ticker_map.get(s) or ticker_map.get(s.title()) or f"{s.replace(' ', '')}.NS"
            futures.append(executor.submit(fetch_ticker_data, s, ticker))
        
        for future in futures:
            s, data = future.result()
            if data:
                context[s] = data
                
    return context