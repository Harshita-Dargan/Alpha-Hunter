import os
import io
import json
import logging
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import google.generativeai as genai
import hashlib

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".gemini_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

original_generate_content = genai.GenerativeModel.generate_content

def cached_generate_content(self, *args, **kwargs):
    prompt = args[0] if args else kwargs.get("contents", "")
    cache_key = hashlib.md5(str(prompt).encode()).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    if os.path.exists(cache_path):
        with open(cache_path, "r") as f:
            data = json.load(f)
            class MockResponse:
                def __init__(self, text):
                    self.text = text
            return MockResponse(data["text"])
            
    response = original_generate_content(self, *args, **kwargs)
    try:
        with open(cache_path, "w") as f:
            json.dump({"text": response.text}, f)
    except Exception as e:
        logging.warning(f"Failed to cache response: {e}")
    return response

genai.GenerativeModel.generate_content = cached_generate_content

from agent_hive import get_portfolio_context
from quant_tool import calculate_portfolio_performance
from news_oracle import fetch_et_news
from audit_logic import check_portfolio_risk
from tax_agent import audit_tax_liability
from pdf_analyst import extract_portfolio_from_pdf
from backend import scenario_agents

load_dotenv()

app = FastAPI(title="Alpha-Hunter Multi-Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def process_portfolio_dataframe(df: pd.DataFrame, use_api_key: str):
    market_data = get_portfolio_context(df, use_api_key)
    perf = calculate_portfolio_performance(df)
    risk_text = check_portfolio_risk(df, top_n=3)
    tax_feedback = audit_tax_liability(df)
    
    investments = df[df['Amount'] < 0].groupby('Fund Name')['Amount'].sum().abs().reset_index()
    distribution = json.loads(investments.to_json(orient='records'))
    
    return {
        "status": "success",
        "market_data": json.loads(json.dumps(market_data)),
        "performance": json.loads(json.dumps(perf)),
        "risk_analysis": {"text": str(risk_text)},
        "tax_feedback": {"text": str(tax_feedback)},
        "distribution": distribution
    }

class NewsRequest(BaseModel):
    company: str
    api_key: str = None

@app.post("/api/analyze-csv")
async def analyze_csv(file: UploadFile = File(...)):
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Must be a CSV file")
            
        use_api_key = os.getenv("GEMINI_API_KEY")
        if not use_api_key or use_api_key == "your_api_key_here":
            raise HTTPException(status_code=400, detail="GEMINI_API_KEY required in .env")

        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        return process_portfolio_dataframe(df, use_api_key)
    except Exception as e:
        import traceback
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_log.txt")
        with open(log_path, "w") as f:
            traceback.print_exc(file=f)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-pdf")
async def analyze_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Must be a PDF file")
        
    use_api_key = os.getenv("GEMINI_API_KEY")
    if not use_api_key or use_api_key == "your_api_key_here":
        raise HTTPException(status_code=400, detail="GEMINI_API_KEY required in .env")

    contents = await file.read()
    file_like = io.BytesIO(contents)
    result = extract_portfolio_from_pdf(file_like, use_api_key)
    
    if result.get('status') == 'success' and result.get('detected_assets'):
        import datetime
        import re
        
        def clean_amount(val):
            cleaned = re.sub(r'[^\d.]', '', str(val))
            try:
                return -float(cleaned) if cleaned else -1000.0
            except:
                return -1000.0
                
        df = pd.DataFrame({
            'Date': [datetime.date.today().strftime('%d-%m-%Y')] * len(result['detected_assets']),
            'Fund Name': result['detected_assets'],
            'Amount': [clean_amount(a) for a in result.get('extracted_amounts', [])],
            'Type': ['Buy'] * len(result['detected_assets'])
        })
        
        # Ensure lengths match in case extracted_amounts was shorter
        min_len = min(len(df['Fund Name']), len(df['Amount']))
        df = df.head(min_len)
        
        dashboard_data = process_portfolio_dataframe(df, use_api_key)
        dashboard_data["pdf_summary"] = result.get("raw_summary", "")
        dashboard_data["detected_assets"] = result.get("detected_assets", [])
        dashboard_data["extracted_amounts"] = result.get("extracted_amounts", [])
        return dashboard_data
        
    return result

@app.post("/api/market-news")
async def get_market_news(req: NewsRequest):
    use_api_key = os.getenv("GEMINI_API_KEY")
    if not use_api_key or use_api_key == "your_api_key_here":
        raise HTTPException(status_code=400, detail="GEMINI_API_KEY required in .env")
        
    result = fetch_et_news(req.company, use_api_key)
    return result

# ----------------- SCENARIO ROUTES -------------------

@app.post("/api/scenario/bulk-deal")
async def scenario_bulk_deal():
    res = scenario_agents.bulk_deal_agent("FMCG Mid-Cap Co", 4.2, 6.0)
    return {"status": "success", "markdown": res}

@app.post("/api/scenario/technical")
async def scenario_technical():
    res = scenario_agents.technical_breakout_agent("Large-Cap IT Stock", 78.0, "Above Average", "Reduced Exposure")
    return {"status": "success", "markdown": res}

@app.post("/api/scenario/macro")
async def scenario_macro(file: UploadFile = File(...)):
    # Requires portfolio context, we use the uploaded CSV
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))
    events = ["RBI repo rate cut", "Sector-specific regulatory change"]
    res = scenario_agents.macro_portfolio_agent(df, events)
    return {"status": "success", "markdown": res}

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if not os.path.exists(FRONTEND_DIR):
    os.makedirs(FRONTEND_DIR, exist_ok=True)

app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
