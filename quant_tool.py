import pandas as pd
from pyxirr import xirr
import logging

def calculate_portfolio_performance(df):
    try:
        df.columns = df.columns.str.strip()
        if 'Date' not in df.columns or 'Amount' not in df.columns:
            return {"status": "error", "message": "Missing 'Date' or 'Amount' columns"}
            
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['Date', 'Amount'])
        
        has_positive = (df['Amount'] > 0).any()
        has_negative = (df['Amount'] < 0).any()
        
        rate = None
        if has_positive and has_negative:
            try:
                rate = xirr(df['Date'], df['Amount'])
            except Exception as e:
                logging.warning(f"XIRR calculation failed: {e}")
                
        xirr_val = round(rate * 100, 2) if rate is not None else 0.0
        
        invested = abs(df[df['Amount'] < 0]['Amount'].sum())
        current = df[df['Amount'] > 0]['Amount'].sum()
        
        return {
            "status": "success",
            "xirr_percentage": float(xirr_val),
            "total_invested": float(invested),
            "current_valuation": float(current),
            "absolute_return": float(round(((current - invested) / invested * 100), 2)) if invested > 0 else 0.0
        }
    except Exception as e:
        logging.error(f"Quant Tool Error: {e}")
        return {"status": "error", "message": f"Calculation Error: {str(e)}"}