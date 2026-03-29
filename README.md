# 🏹 ALPHA-HUNTER: Autonomous Portfolio Intelligence Engine

**Participant:** HARSHITA DARGAN  
**Event:** ET AI HACKATHON

> A Multi-Agent AI System transforming static brokerage PDFs and CSVs into real-time, institutional-grade actionable intelligence.

---

## 🚀 The Vision

Retail investors typically get their data in static, backwards-looking formats: clunky CSV ledgers and long PDF statements from their brokers. Calculating accurate performance, auditing concentration risks, tracking tax exposure, and correlating news impact across an entire portfolio is typically a manual, arduous process reserved for institutional quants.

**Alpha-Hunter** fixes this by unleashing a swarm of autonomous cognitive agents—powered by Google's Gemini 1.5 Pro and an asynchronous Python/FastAPI backend—onto your raw portfolio data.

## 🧠 Core Features

1. **📄 NLP Document Intelligence (Zero-Shot)**
   Upload any messy broker PDF. The engine uses LLM-powered OCR logic to intelligently parse unstructured tables, detecting named assets and invested capital automatically.
2. **🕸️ Multi-Agent Analysis Grid (CSV)**
   Upload your transaction ledger to wake up a decentralized team of cognitive agents:
   - **Quant Agent**: Dynamically reconciles XIRR and absolute returns.
   - **Risk Auditor**: Detects concentration risks and flags unhealthy asset overlaps.
   - **Tax Strategist**: Audits the short/long term capital gains landscape.
3. **🌐 The News Oracle**
   A live, automated pipeline that fetches ET stock news, synthesizes the core themes, and outputs hyper-concise bullish/bearish directives for your holdings.
4. **🛡️ Built-in API Quota Protection**
   To ensure stability, the backend natively features a smart disk-based caching layer and exponential back-off protocols. It shields the system from `429 Too Many Requests` errors when rapidly refreshing your intelligence dashboard.

## 🛠️ Technology Stack

- **AI Engine:** Google Gemini 1.5 Flash/Pro (Generative AI API)
- **Backend:** Python 3, FastAPI, Uvicorn, Pandas, PyXIRR
- **Frontend:** HTML5, CSS3 Glassmorphism, Vanilla JS, Chart.js

---

## ⚡ Quickstart Guide (For Judges)

### 1. Requirements Installation
Ensure you have Python 3.9+ installed. Clone this repository and run:
```bash
pip install -r requirements.txt
```

### 2. Configure the Environment
Look for the `.env.example` file in the root directory. Rename it to `.env` (or create a new `.env` file) and insert your live Gemini API key:
```ini
GEMINI_API_KEY=your_actual_api_key_here
```

### 3. Launch the Intelligence Server
Start the asynchronous engine using Uvicorn:
```bash
uvicorn backend.main:app --reload
```

### 4. Open the Interface
Navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000) in your modern browser.

> [!TIP]
> **Testing Data Provided!**  
> We've included two mock datasets in the root directory for evaluation:
> - `test_ledger.csv` (Drop into the Quant Engine)
> - `test_statement.pdf` (Drop into the NLP Scanner)

---

## 🔮 Future Roadmap

- Integration with direct broker API bridges (Zerodha/Upstox).
- RAG-based SEC/NSE filing database for the scenario agents to pull historical financial statements directly.
- Expanded Tax Agent modules supporting global capital gains calculations.

*Built with ❤️ for the ET AI Hackathon.*
