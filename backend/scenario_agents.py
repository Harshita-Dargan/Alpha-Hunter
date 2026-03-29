import os
import json
import logging
import google.generativeai as genai

# ---------------------------------------------------------
# AUTONOMOUS 3-STEP PIPELINE ARCHITECTURE
# Step 1: Ingest Raw Signal
# Step 2: Enrich with External Context / History
# Step 3: Cognitive Synthesis & Alert Generation
# ---------------------------------------------------------

def configure_llm():
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model_name = available[0] if available else 'gemini-1.5-flash'
    return genai.GenerativeModel(model_name)

def _generate_with_retry(model, prompt):
    import time, re
    for attempt in range(4):
        try:
            return model.generate_content(prompt)
        except Exception as e:
            err_str = str(e)
            if ('429' in err_str or 'Quota' in err_str) and attempt < 3:
                match = re.search(r'retry in (\d+\.?\d*)s', err_str)
                wait_time = float(match.group(1)) + 1 if match else 15
                logging.warning(f"Rate limit hit. Waiting {wait_time}s before retry {attempt+1}")
                time.sleep(wait_time)
            else:
                raise e

def bulk_deal_agent(company: str, stake_sold: float, discount: float):
    # STEP 1: Signal Ingestion
    signal = {
        "event_type": "Promoter Bulk Deal",
        "company": company,
        "stake_sold_percent": stake_sold,
        "discount_to_market_percent": discount
    }
    
    # STEP 2: Enrichment (Simulating DB retrieval of transcripts & fundamentals)
    # In a fully connected build, this queries an earnings API and SEC/NSE filings DB.
    enriched_context = {
        "recent_management_commentary": "Management cited 'personal liquidity needs' and emphasized strong Q3 volume growth of 8%.",
        "earnings_trajectory": "Consistent YoY growth, net margins expanded by 120bps.",
        "historical_promoter_selling": "No major promoter selling in the last 5 years."
    }
    
    # STEP 3: Generation
    model = configure_llm()
    prompt = f"""
    You are an elite quantitative equity analyst. Analyze this bulk deal through a strict objective lens.
    Signal: {json.dumps(signal)}
    Context: {json.dumps(enriched_context)}
    
    Task: 
    1. Assess whether this is distress selling or a routine block.
    2. Cross-reference against the management commentary and earnings trajectory.
    3. Generate a risk-adjusted alert with a SPECIFIC recommended action (Buy/Hold/Trim/Sell) for a retail investor. 
    4. You MUST explicitly cite the filing details and context.
    
    Format your response in Markdown. Do not use generic warnings.
    """
    response = _generate_with_retry(model, prompt)
    return response.text

def technical_breakout_agent(company: str, rsi: float, volume_profile: str, fii_action: str):
    # STEP 1: Ingestion
    signal = {
        "event_type": "52-Week Breakout",
        "company": company,
        "rsi": rsi,
        "volume": volume_profile,
        "fii_activity": fii_action
    }
    
    # STEP 2: Enrichment (Simulating a Quantitative Backtest Engine)
    enriched_context = {
        "historical_pattern_success_rate": "38%",
        "average_drawdown_post_pattern": "-12.4%",
        "sector_momentum": "Neutral"
    }
    
    # STEP 3: Generation
    model = configure_llm()
    prompt = f"""
    You are a systematic trading algorithm. Analyze these conflicting technical and flow signals.
    Signal: {json.dumps(signal)}
    Context (Quant Backtest): {json.dumps(enriched_context)}
    
    Task:
    1. Detect and explain the breakout pattern vs the overbought RSI and negative FII flow.
    2. Quantify the risk using the historical success rate provided.
    3. Present a highly balanced, data-backed recommendation. DO NOT give a binary buy/sell call.
    4. Provide specific price levels to watch or hedging strategies.
    
    Format your response in Markdown. Oversimplified binary outputs are penalized.
    """
    response = _generate_with_retry(model, prompt)
    return response.text

def macro_portfolio_agent(portfolio_df, news_events: list):
    # STEP 1: Ingestion
    # We parse the portfolio_df to get sector exposure
    holdings = portfolio_df[['Fund Name', 'Amount']].to_dict(orient='records')
    
    # STEP 2: Enrichment (Mapping portfolio to News Impact)
    # In real life, sector mapping is done via a master database.
    enriched_context = {
        "repo_rate_exposure": "High (Rate sensitive financials/auto in portfolio)",
        "regulatory_exposure": "Moderate (Healthcare/IT specific)",
        "portfolio_snapshot": holdings
    }
    
    # STEP 3: Generation
    model = configure_llm()
    prompt = f"""
    You are a Portfolio Risk Manager. Two major news events just broke:
    Events: {json.dumps(news_events)}
    Portfolio Context: {json.dumps(enriched_context)}
    
    Task:
    1. Identify which event is MORE financially material to this SPECIFIC portfolio.
    2. Quantify the estimated qualitative P&L impact on the relevant holdings.
    3. Generate a prioritized alert. Tell the user EXACTLY what to worry about first.
    
    Format your response in Markdown.
    """
    response = _generate_with_retry(model, prompt)
    return response.text
