import PyPDF2
import io
import logging
import google.generativeai as genai
import json

def extract_portfolio_from_pdf(uploaded_file, api_key):
    """Uses LLM to smartly extract Tickers and Amounts from PDF statements"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
        text = ""
        for page in pdf_reader.pages:
            extracted = page.extract_text()
            if extracted: text += extracted + "\n"
        
        genai.configure(api_key=api_key)
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = available[0] if available else 'gemini-1.5-flash'
        model = genai.GenerativeModel(model_name)
        prompt = f"""You are a financial analyst OCR expert. Extract the core portfolio holdings, their asset names, and the associated invested amounts from the following broken PDF text.
        Text: {text[:8000]}
        Return ONLY valid JSON with this structure:
        {{
            "detected_assets": ["Asset Name 1", "Asset Name 2"],
            "extracted_amounts": ["10,000", "5,000.50"]
        }}
        """
        import time
        import re
        for attempt in range(4):
            try:
                response = model.generate_content(prompt)
                data = json.loads(response.text)
                break
            except Exception as e:
                err_str = str(e)
                if ('429' in err_str or 'Quota' in err_str) and attempt < 3:
                    match = re.search(r'retry in (\d+\.?\d*)s', err_str)
                    wait_time = float(match.group(1)) + 1 if match else 15
                    logging.warning(f"Rate limit hit. Waiting {wait_time}s before retry {attempt+1}")
                    time.sleep(wait_time)
                else:
                    raise e
        
        return {
            "status": "success",
            "detected_assets": data.get("detected_assets", []),
            "raw_summary": f"Analyzed {len(pdf_reader.pages)} pages using AI Reader.",
            "extracted_amounts": data.get("extracted_amounts", [])
        }
    except Exception as e:
        logging.error(f"PDF AI Parsing Error: {e}")
        return {"status": "error", "message": str(e)}