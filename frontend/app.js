document.addEventListener('DOMContentLoaded', () => {

    const pdfDrop = document.getElementById('pdf-drop-area');
    const pdfUpload = document.getElementById('pdf-upload');
    const csvDrop = document.getElementById('csv-drop-area');
    const csvUpload = document.getElementById('csv-upload');
    
    // UI Elements
    const loadingOverlay = document.getElementById('loading-overlay');
    const agentGrid = document.getElementById('agent-grid');
    const bottomRow = document.getElementById('bottom-row');
    const marketTickers = document.getElementById('market-tickers');
    const pdfResults = document.getElementById('pdf-results');
    const pdfSummary = document.getElementById('pdf-summary');
    
    // Scenarios
    const btnBulk = document.getElementById('btn-scenario-bulk');
    const btnTech = document.getElementById('btn-scenario-tech');
    const btnMacro = document.getElementById('btn-scenario-macro');
    const scenarioPanel = document.getElementById('scenario-panel');
    const scenarioContent = document.getElementById('scenario-content');
    const scenarioTitle = document.getElementById('scenario-title');

    // Values
    const valXirr = document.getElementById('val-xirr');
    const valFlows = document.getElementById('val-flows');
    const valAbs = document.getElementById('val-abs');
    const valRisk = document.getElementById('val-risk');
    const valTax = document.getElementById('val-tax');
    const valNews = document.getElementById('val-news');

    let portfolioChartInst = null;
    let tickerInterval = null;

    // --- Drag and Drop Logic ---
    function setupDropzone(dropzone, input, handler) {
        dropzone.addEventListener('click', () => input.click());
        dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.style.borderColor = 'var(--neon-pink)'; });
        dropzone.addEventListener('dragleave', () => { dropzone.style.borderColor = ''; });
        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.style.borderColor = '';
            if (e.dataTransfer.files.length) {
                input.files = e.dataTransfer.files;
                handler(input.files[0]);
            }
        });
        input.addEventListener('change', () => {
            if (input.files.length) handler(input.files[0]);
        });
    }

    setupDropzone(pdfDrop, pdfUpload, handlePDF);
    setupDropzone(csvDrop, csvUpload, handleCSV);

    // --- Typewriter Effect ---
    function typeWriter(element, text, speed = 10) {
        element.innerHTML = '';
        let i = 0;
        function type() {
            if (i < text.length) {
                element.innerHTML += text.charAt(i) === '\n' ? '<br>' : text.charAt(i);
                i++;
                setTimeout(type, speed);
            }
        }
        type();
    }

    // --- API Handlers ---
    async function handlePDF(file) {
        if (!file.name.endsWith('.pdf')) return alert('Please upload a PDF.');
        
        loadingOverlay.classList.remove('hidden');
        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch('/api/analyze-pdf', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            
            if (!res.ok) throw new Error(data.detail || 'Analysis failed');

            pdfResults.classList.remove('hidden');
            let txt = `Status: ${data.status}\n`;
            txt += `Entities:\n- ${data.detected_assets.join('\n- ')}\n`;
            txt += `Values:\n- ${data.extracted_amounts.join('\n- ')}\n`;
            typeWriter(pdfSummary, txt, 20);

        } catch (err) {
            alert('Error parsing PDF: ' + err.message);
        } finally {
            loadingOverlay.classList.add('hidden');
        }
    }

    async function handleCSV(file) {
        if (!file.name.endsWith('.csv')) return alert('Please upload a CSV.');
        
        loadingOverlay.classList.remove('hidden');
        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch('/api/analyze-csv', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            
            if (!res.ok) throw new Error(data.detail || 'Analysis failed');

            populateDashboard(data);

        } catch (err) {
            alert('Error analyzing portfolio: ' + err.message);
        } finally {
            loadingOverlay.classList.add('hidden');
        }
    }

    // --- Dashboard population ---
    function populateDashboard(data) {
        agentGrid.classList.remove('hidden');
        bottomRow.classList.remove('hidden');

        // Quant
        if (data.performance.status === 'success') {
            valXirr.innerText = data.performance.xirr_percentage + '%';
            valFlows.innerText = '₹' + parseInt(data.performance.total_invested).toLocaleString('en-IN');
            valAbs.innerText = data.performance.absolute_return + '%';
        } else {
            valXirr.innerText = 'ERR';
        }

        // Risk & Tax Terminals
        typeWriter(valRisk, data.risk_analysis.text || 'No data', 15);
        typeWriter(valTax, data.tax_feedback.text || 'No data', 15);

        // Tickers
        updateTickers(data.market_data);

        // Chart
        renderChart(data.distribution);

        // Fetch news for the top 3 tickers asynchronously
        valNews.innerHTML = '';
        const symbols = Object.keys(data.market_data).slice(0, 3);
        symbols.forEach(sym => {
            fetchNews(sym);
        });
    }

    function updateTickers(marketData) {
        marketTickers.innerHTML = '';
        const items = Object.entries(marketData).map(([sym, d]) => {
            const cClass = d.day_change >= 0 ? 'ticker-pos' : 'ticker-neg';
            const sign = d.day_change >= 0 ? '+' : '';
            return `<div class="ticker-item">${sym}: ₹${d.price} <span class="${cClass}">[${sign}${d.day_change}%]</span></div>`;
        });
        // Duplicate for infinite scroll effect
        marketTickers.innerHTML = [...items, ...items, ...items].join('');
        
        // Simple CSS animation via js calculation
        let pos = 0;
        if (tickerInterval) clearInterval(tickerInterval);
        tickerInterval = setInterval(() => {
            pos -= 1;
            if (pos < -500) pos = 0;
            marketTickers.style.transform = `translateX(${pos}px)`;
        }, 50);
    }

    async function fetchNews(company) {
        try {
            const res = await fetch('/api/market-news', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ company: company })
            });
            const data = await res.json();
            if (data.status) {
                const links = data.articles.map(a => `<a href="${a.link}" target="_blank">🔹 ${a.title}</a>`).join('');
                const html = `
                    <div class="news-item">
                        <div class="news-insight">[${company}] ${data.status}: ${data.insight}</div>
                        <div class="news-links">${links}</div>
                    </div>
                `;
                valNews.innerHTML += html;
            }
        } catch (e) {
            console.error("Failed news fetch", e);
        }
    }

    function renderChart(distribution) {
        const ctx = document.getElementById('portfolioChart').getContext('2d');
        if (portfolioChartInst) portfolioChartInst.destroy();

        if (!distribution || !distribution.length) {
            return;
        }

        const labels = distribution.map(d => d['Fund Name']);
        const data = distribution.map(d => d['Amount']);

        portfolioChartInst = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: [
                        '#00f3ff', '#bc13fe', '#ff007f', '#39ff14', '#fbab7e'
                    ],
                    borderWidth: 0,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: '#e0f7fa', font: { family: 'Rajdhani', size: 14 } }
                    }
                },
                cutout: '70%',
                animation: { animateScale: true, animateRotate: true }
            }
        });
    }

    // --- Scenarios ---
    
    async function runScenario(endpoint, titleTitle, needsCsv = false) {
        scenarioPanel.classList.remove('hidden');
        scenarioTitle.innerText = titleTitle;
        scenarioContent.innerText = "Deploying cognitive agents... Please wait.";
        
        let options = { method: 'POST' };
        
        if (needsCsv) {
            if (!csvUpload.files.length) {
                scenarioContent.innerText = "Error: Please upload a Broker Ledger CSV first to run Portfolio Macro Analysis.";
                return;
            }
            const formData = new FormData();
            formData.append('file', csvUpload.files[0]);
            options.body = formData;
        }

        try {
            const res = await fetch(`/api/scenario/${endpoint}`, options);
            const data = await res.json();
            if(!res.ok) throw new Error(data.detail || 'Scenario failed');
            
            // Basic markdown to HTML
            let md = data.markdown
                .replace(/\\*(.*?)\\*/g, '<em>$1</em>')
                .replace(/\\n/g, '<br>');
                
            scenarioContent.innerHTML = md;
        } catch (err) {
            scenarioContent.innerHTML = "Agent Error: " + err.message;
        }
    }

    btnBulk.addEventListener('click', () => runScenario('bulk-deal', 'BULK DEAL INTELLIGENCE'));
    btnTech.addEventListener('click', () => runScenario('technical', 'TECHNICAL BREAKOUT ANALYSIS'));
    btnMacro.addEventListener('click', () => runScenario('macro', 'MACRO PORTFOLIO PRIORITIZATION', true));

});
