import pandas as pd
import logging

def check_portfolio_risk(df, top_n=3):
    try:
        investments = df[df['Amount'] < 0].groupby('Fund Name')['Amount'].sum().abs()
        total_value = investments.sum()
        
        if total_value == 0:
            return "🛡️ Risk Agent: No investments found to analyze risk."
            
        top_investments = investments.nlargest(top_n)
        
        risk_msgs = []
        for fund, val in top_investments.items():
            concentration = (val / total_value) * 100
            if concentration > 35:
                risk_msgs.append(f"⚠️ **High Risk:** {fund} is {concentration:.1f}%")
            else:
                risk_msgs.append(f"✅ Healthy: {fund} is {concentration:.1f}%")
                
        return "\n".join(risk_msgs)
    except Exception as e:
        logging.error(f"Risk Agent Error: {e}")
        return "🛡️ Risk Agent: Analyzing data..."