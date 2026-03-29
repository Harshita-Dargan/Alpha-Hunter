import requests
import xml.etree.ElementTree as ET
from functools import lru_cache
import logging
import google.generativeai as genai
import json

@lru_cache(maxsize=32)
def fetch_et_news(company, api_key):
    import urllib.parse
    query = urllib.parse.quote(f"{company} stock news india")
    rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(rss_url, headers=headers, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        
        raw_news = []
        for item in root.findall('.//channel/item')[:5]:
            title = item.find('title')
            link = item.find('link')
            if title is not None and link is not None:
                raw_news.append({"title": title.text or "", "link": link.text})
            
        if not raw_news:
             return {
                 "status": "NO DATA",
                 "insight": "No direct news signals detected for this asset today.",
                 "articles": []
             }
        
        # Use LLM to evaluate comprehensive stock impact
        genai.configure(api_key=api_key)
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = available[0] if available else 'gemini-1.5-flash'
        model = genai.GenerativeModel(model_name)
        
        prompt = f"""You are an elite financial analyst. Read these recent news headlines for '{company}'.
        Provide a very concise insight into how this news might broadly affect the stock and categorize the overall outlook.
        News: {json.dumps(raw_news)}
        Return ONLY valid JSON structure:
        {{
          "status": "BULLISH",
          "insight": "A robust, one-sentence punchy analysis of the broader impact of the news.",
          "articles": {json.dumps(raw_news)}
        }}
        """
        import time
        import re
        for attempt in range(4):
            try:
                response = model.generate_content(prompt)
                text = response.text.strip()
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
                    
        if text.startswith("```json"): text = text[7:]
        elif text.startswith("```"): text = text[3:]
        if text.endswith("```"): text = text[:-3]
        
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            import re
            status_match = re.search(r'"status"\s*:\s*"([^"]+)"', text, re.IGNORECASE)
            # Try to grab insight between "insight": " and either "articles" or }
            insight_match = re.search(r'"insight"\s*:\s*"(.*?)"\s*(?:,\s*"articles"|\n*\})', text, flags=re.DOTALL)
            
            status_val = status_match.group(1).upper() if status_match else "UNKNOWN"
            insight_val = insight_match.group(1) if insight_match else "Valid insight retrieved but LLM dropped formatting."
            
            return {
                "status": status_val,
                "insight": insight_val.strip().replace('\n', ' ').replace('\\"', '"'),
                "articles": raw_news
            }
    except Exception as e:
        error_msg = str(e)
        logging.error(f"News fetch/analysis failed for {company}: {error_msg}")
        return {
            "status": "ERROR",
            "insight": f"Analysis Failed: {error_msg}",
            "articles": []
        }