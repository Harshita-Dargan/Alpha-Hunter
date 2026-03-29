import pandas as pd
import logging

def audit_tax_liability(df):
    """Calculates tax based on India Budget 2026 rules"""
    try:
        df = df.copy()
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
        gains_df = df[df['Amount'] > 0].copy()
        
        if gains_df.empty:
            return "🛡️ **Tax Status:** No realized gains found. No tax due."
            
        now = pd.Timestamp.now()
        gains_df['days_held'] = (now - gains_df['Date']).dt.days
        
        ltcg_gains = gains_df[gains_df['days_held'] > 365]['Amount'].sum()
        stcg_gains = gains_df[gains_df['days_held'] <= 365]['Amount'].sum()
        
        ltcg_exemption = 125000
        taxable_ltcg = max(0, ltcg_gains - ltcg_exemption)
        
        ltcg_tax = taxable_ltcg * 0.125
        stcg_tax = stcg_gains * 0.20
        total_tax = ltcg_tax + stcg_tax
        
        feedback = []
        if total_tax == 0:
            feedback.append(f"✅ **Tax Optimized:** No tax liability.")
            if ltcg_gains > 0:
                feedback.append(f"LTCG of ₹{ltcg_gains:,.0f} is within ₹1.25L exemption.")
        else:
            feedback.append(f"⚠️ **Tax Alert:** Est. Liability: **₹{total_tax:,.0f}**")
            if stcg_tax > 0:
                feedback.append(f"- STCG (20%): ₹{stcg_tax:,.0f} on ₹{stcg_gains:,.0f} gains")
            if ltcg_tax > 0:
                feedback.append(f"- LTCG (12.5%): ₹{ltcg_tax:,.0f} on taxable ₹{taxable_ltcg:,.0f}")
                
        return "\n".join(feedback)
    except Exception as e:
        logging.error(f"Tax Agent Error: {e}")
        return "⚙️ Tax Agent: Waiting for proper transaction data..."