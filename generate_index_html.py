import json

with open('dashboard_payload.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

payload_json_str = json.dumps(data)

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Rajasthan Royals — The Halla Bol Pressure Index (SupeRR Selector)</title>
  <!-- Google Fonts: Inter -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
  <!-- Plotly.js -->
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
  <style>
    :root {{
      --rr-pink: #ea008a;
      --rr-pink-glow: rgba(234, 0, 138, 0.35);
      --rr-blue: #1e40af;
      --rr-blue-light: #38bdf8;
      --rr-gold: #f5c518;
      --bg: #070a13;
      --card: #0f172a;
      --card-hover: #1e293b;
      --border: rgba(255, 255, 255, 0.08);
      --text: #f8fafc;
      --subtext: #94a3b8;
      --green: #10b981;
      --red: #f43f5e;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 24px 32px 60px;
    }}
    a {{
      color: var(--rr-pink);
      text-decoration: none;
    }}
    a:hover {{
      text-decoration: underline;
    }}

    /* Header */
    .header-container {{
      background: linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(7, 10, 19, 0.99));
      border: 1px solid var(--border);
      border-left: 6px solid var(--rr-pink);
      border-radius: 16px;
      padding: 24px 28px;
      margin-bottom: 24px;
      box-shadow: 0 10px 35px rgba(0, 0, 0, 0.5);
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
    }}
    .header-titles h1 {{
      font-size: 24px;
      font-weight: 900;
      letter-spacing: -0.5px;
      margin-bottom: 6px;
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }}
    .header-titles h1 span.pink {{
      color: var(--rr-pink);
      text-shadow: 0 0 15px var(--rr-pink-glow);
    }}
    .header-titles p {{
      color: var(--subtext);
      font-size: 13px;
      margin-bottom: 6px;
    }}
    .submitter-badge {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      font-weight: 700;
      color: var(--rr-gold);
      background: rgba(245, 197, 24, 0.1);
      border: 1px solid rgba(245, 197, 24, 0.3);
      padding: 4px 12px;
      border-radius: 6px;
    }}
    .badge-pill {{
      display: inline-block;
      background: rgba(234, 0, 138, 0.15);
      border: 1px solid rgba(234, 0, 138, 0.4);
      color: var(--rr-pink);
      font-size: 10px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      padding: 3px 10px;
      border-radius: 20px;
      margin-bottom: 6px;
    }}
    .header-right {{
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 8px;
    }}
    .pills-group {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .pill {{
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      padding: 4px 10px;
      border-radius: 6px;
    }}
    .pill-blue {{
      background: rgba(30, 64, 175, 0.25);
      border: 1px solid rgba(30, 64, 175, 0.5);
      color: var(--rr-blue-light);
    }}
    .pill-green {{
      background: rgba(16, 185, 129, 0.15);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: var(--green);
    }}

    /* Top KPI Cards */
    .kpi-row {{
      display: flex;
      gap: 16px;
      margin-bottom: 24px;
      flex-wrap: wrap;
    }}
    .kpi-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 16px 20px;
      flex: 1;
      min-width: 220px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
      transition: transform 0.2s ease, border-color 0.2s ease;
    }}
    .kpi-card:hover {{
      transform: translateY(-2px);
      border-color: rgba(255, 255, 255, 0.2);
    }}
    .kpi-tag {{
      font-size: 9px;
      font-weight: 800;
      letter-spacing: 1px;
      text-transform: uppercase;
      padding: 2px 6px;
      border-radius: 4px;
      margin-right: 8px;
      background: rgba(255, 255, 255, 0.05);
    }}
    .kpi-title {{
      font-size: 10px;
      font-weight: 700;
      color: var(--subtext);
      text-transform: uppercase;
      letter-spacing: 1.2px;
    }}
    .kpi-val {{
      font-size: 24px;
      font-weight: 900;
      color: #ffffff;
      margin: 4px 0 2px;
    }}
    .kpi-sub {{
      font-size: 11px;
      color: var(--subtext);
      font-weight: 500;
    }}

    /* Tabs Navigation */
    .tabs-nav {{
      display: flex;
      gap: 8px;
      background: var(--card);
      padding: 6px;
      border-radius: 12px;
      border: 1px solid var(--border);
      margin-bottom: 24px;
      overflow-x: auto;
    }}
    .tab-btn {{
      background: transparent;
      border: none;
      color: var(--subtext);
      padding: 11px 18px;
      border-radius: 8px;
      font-size: 11px;
      font-weight: 700;
      cursor: pointer;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      transition: all 0.2s ease;
      white-space: nowrap;
    }}
    .tab-btn:hover {{
      color: #ffffff;
      background: rgba(255, 255, 255, 0.04);
    }}
    .tab-btn.active {{
      background: var(--card-hover);
      color: #ffffff;
      font-weight: 900;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }}
    .tab-btn.active.tab-pink {{
      border-bottom: 3px solid var(--rr-pink);
    }}
    .tab-btn.active.tab-gold {{
      border-bottom: 3px solid var(--rr-gold);
    }}
    .tab-btn.active.tab-blue {{
      border-bottom: 3px solid var(--rr-blue-light);
    }}
    .tab-btn.active.tab-green {{
      border-bottom: 3px solid var(--green);
    }}
    .tab-btn.active.tab-purple {{
      border-bottom: 3px solid #a855f7;
    }}

    /* Tab Contents */
    .tab-content {{
      display: none;
    }}
    .tab-content.active {{
      display: block;
    }}

    /* Layout Grids */
    .grid-2 {{
      display: flex;
      gap: 20px;
      margin-bottom: 20px;
      flex-wrap: wrap;
    }}
    .grid-2 > div {{
      flex: 1;
      min-width: 360px;
    }}
    .card-box {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 20px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }}

    /* Tables */
    .table-container {{
      overflow-x: auto;
      margin-top: 10px;
    }}
    table.rr-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 11px;
      text-align: center;
    }}
    table.rr-table th {{
      background: rgba(15, 23, 42, 0.95);
      padding: 10px 8px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    table.rr-table.bat th {{
      color: var(--rr-pink);
      border-bottom: 2px solid var(--rr-pink);
    }}
    table.rr-table.bowl th {{
      color: var(--rr-blue-light);
      border-bottom: 2px solid var(--rr-blue);
    }}
    table.rr-table td {{
      padding: 9px 8px;
      border-bottom: 1px solid var(--border);
      color: var(--text);
    }}
    table.rr-table tr:hover td {{
      background: rgba(255, 255, 255, 0.03);
    }}
    table.rr-table td.player-name {{
      text-align: left;
      font-weight: 700;
      color: #ffffff;
    }}
    table.rr-table tr.top-1 td {{
      background: rgba(245, 197, 24, 0.08);
      font-weight: 800;
    }}

    /* Forensic Dossier */
    .select-group {{
      display: flex;
      gap: 16px;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }}
    .select-item {{
      flex: 1;
      min-width: 250px;
    }}
    .select-item label {{
      display: block;
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 1px;
      margin-bottom: 6px;
      text-transform: uppercase;
    }}
    select.rr-select {{
      width: 100%;
      background: #1e293b;
      color: #ffffff;
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 8px;
      padding: 10px 14px;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      outline: none;
    }}
    select.rr-select:focus {{
      border-color: var(--rr-pink);
      box-shadow: 0 0 8px var(--rr-pink-glow);
    }}

    /* Dossier Panel */
    .dossier-panel {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 20px;
      display: flex;
      gap: 20px;
      flex-wrap: wrap;
    }}
    .player-col {{
      flex: 1;
      min-width: 320px;
      background: rgba(255, 255, 255, 0.015);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 18px;
    }}
    .player-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 12px;
    }}
    .rank-tag {{
      display: inline-block;
      color: #ffffff;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 10px;
      font-weight: 900;
      letter-spacing: 0.5px;
      margin-bottom: 4px;
    }}
    .player-name-large {{
      font-size: 20px;
      font-weight: 900;
      color: #ffffff;
      letter-spacing: -0.5px;
    }}
    .player-badge-text {{
      font-size: 11px;
      font-weight: 700;
      color: var(--rr-gold);
    }}
    .player-score-large {{
      font-size: 30px;
      font-weight: 900;
      text-align: right;
    }}
    .player-desc {{
      font-size: 12px;
      color: #cbd5e1;
      line-height: 1.6;
      background: rgba(255, 255, 255, 0.02);
      padding: 12px;
      border-radius: 8px;
      border: 1px solid var(--border);
      margin-bottom: 14px;
    }}
    .mini-kpis {{
      display: flex;
      gap: 10px;
      margin-bottom: 14px;
      flex-wrap: wrap;
    }}
    .mini-kpi {{
      flex: 1;
      min-width: 85px;
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px 10px;
      text-align: center;
    }}
    .mini-kpi-val {{
      font-size: 14px;
      font-weight: 900;
      color: #ffffff;
    }}
    .mini-kpi-lbl {{
      font-size: 9px;
      color: var(--subtext);
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .match-log-item {{
      font-size: 11px;
      padding-bottom: 8px;
      margin-bottom: 8px;
      border-bottom: 1px dashed rgba(255, 255, 255, 0.06);
      line-height: 1.4;
    }}

    /* Top 10 Deep Dive Cards */
    .top10-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 18px;
      margin-top: 14px;
    }}
    .player-explain-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 18px;
      transition: all 0.25s ease;
      position: relative;
      overflow: hidden;
    }}
    .player-explain-card:hover {{
      transform: translateY(-3px);
      border-color: rgba(255, 255, 255, 0.25);
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
    }}
    .player-explain-card.bat-card {{
      border-left: 4px solid var(--rr-pink);
    }}
    .player-explain-card.bowl-card {{
      border-left: 4px solid var(--rr-blue-light);
    }}
    .explain-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 10px;
    }}
    .explain-name {{
      font-size: 17px;
      font-weight: 900;
      color: #ffffff;
    }}
    .explain-archetype {{
      font-size: 10px;
      font-weight: 800;
      color: var(--rr-gold);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .explain-score {{
      font-size: 22px;
      font-weight: 900;
      text-align: right;
    }}
    .explain-why {{
      font-size: 11.5px;
      color: #cbd5e1;
      line-height: 1.55;
      margin-bottom: 12px;
    }}
    .formula-items {{
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px 12px;
      margin-bottom: 10px;
    }}
    .formula-row {{
      display: flex;
      justify-content: space-between;
      font-size: 10.5px;
      padding: 3px 0;
      border-bottom: 1px dotted rgba(255, 255, 255, 0.05);
    }}
    .formula-row:last-child {{
      border-bottom: none;
    }}
    .sig-match {{
      font-size: 10.5px;
      color: var(--subtext);
      line-height: 1.4;
      background: rgba(0, 0, 0, 0.25);
      padding: 6px 10px;
      border-radius: 6px;
      border-left: 2px solid var(--rr-gold);
    }}

    /* Case Studies Cards */
    .case-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 20px;
      margin-bottom: 16px;
    }}
    .case-tag {{
      font-size: 10px;
      font-weight: 900;
      color: var(--rr-gold);
      letter-spacing: 1px;
      text-transform: uppercase;
    }}
    .case-title {{
      color: #ffffff;
      font-size: 15px;
      font-weight: 800;
      margin: 4px 0 8px;
    }}
    .case-p {{
      font-size: 12px;
      color: var(--subtext);
      line-height: 1.5;
      margin-bottom: 12px;
    }}
    .case-split {{
      display: flex;
      gap: 16px;
      flex-wrap: wrap;
    }}
    .case-box {{
      flex: 1;
      min-width: 280px;
      padding: 14px;
      border-radius: 10px;
      border: 1px solid var(--border);
    }}

    /* Comparison Tool */
    .compare-container {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 22px;
      margin-bottom: 24px;
    }}
    .compare-selectors {{
      display: flex;
      gap: 20px;
      margin-bottom: 18px;
      flex-wrap: wrap;
    }}
    .compare-card {{
      flex: 1;
      min-width: 280px;
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px;
    }}

    /* Footer */
    footer {{
      margin-top: 40px;
      border-top: 1px solid var(--border);
      padding-top: 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      font-size: 11px;
      color: var(--subtext);
    }}

    /* Submission Deliverables Bar */
    .download-bar {{
      background: linear-gradient(135deg, rgba(30, 41, 59, 0.85), rgba(15, 23, 42, 0.98));
      border: 1px solid rgba(234, 0, 138, 0.35);
      border-radius: 14px;
      padding: 16px 22px;
      margin-bottom: 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
      box-shadow: 0 8px 30px rgba(0, 0, 0, 0.45);
    }}
    .download-bar-left {{
      display: flex;
      align-items: center;
      gap: 14px;
      flex-wrap: wrap;
    }}
    .download-bar-title {{
      font-size: 13px;
      font-weight: 800;
      color: #ffffff;
      display: flex;
      align-items: center;
      gap: 8px;
      letter-spacing: 0.5px;
    }}
    .download-bar-sub {{
      font-size: 11px;
      color: var(--subtext);
      margin-top: 2px;
    }}
    .download-btn-group {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
    }}
    .dl-btn {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 9px 15px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 700;
      text-decoration: none !important;
      transition: all 0.2s ease;
      cursor: pointer;
    }}
    .dl-btn-pink {{
      background: linear-gradient(135deg, var(--rr-pink), #c20072);
      color: #ffffff !important;
      box-shadow: 0 4px 14px var(--rr-pink-glow);
      border: 1px solid rgba(255, 255, 255, 0.25);
    }}
    .dl-btn-pink:hover {{
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(234, 0, 138, 0.6);
    }}
    .dl-btn-blue {{
      background: linear-gradient(135deg, rgba(30, 64, 175, 0.85), rgba(30, 58, 138, 0.95));
      color: #ffffff !important;
      border: 1px solid rgba(96, 165, 250, 0.4);
    }}
    .dl-btn-blue:hover {{
      transform: translateY(-2px);
      background: var(--rr-blue);
      border-color: var(--rr-blue-light);
    }}
    .dl-btn-gold {{
      background: linear-gradient(135deg, rgba(245, 197, 24, 0.2), rgba(217, 119, 6, 0.25));
      color: var(--rr-gold) !important;
      border: 1px solid rgba(245, 197, 24, 0.5);
    }}
    .dl-btn-gold:hover {{
      transform: translateY(-2px);
      background: rgba(245, 197, 24, 0.3);
      color: #ffffff !important;
    }}
    .dl-btn-dark {{
      background: rgba(255, 255, 255, 0.07);
      color: #ffffff !important;
      border: 1px solid rgba(255, 255, 255, 0.15);
    }}
    .dl-btn-dark:hover {{
      transform: translateY(-2px);
      background: rgba(255, 255, 255, 0.12);
      border-color: rgba(255, 255, 255, 0.3);
    }}
    .dl-badge {{
      font-size: 9px;
      padding: 2px 6px;
      border-radius: 4px;
      background: rgba(0, 0, 0, 0.35);
      font-weight: 800;
    }}
  </style>
</head>
<body>

  <!-- HEADER -->
  <header class="header-container">
    <div class="header-titles">
      <div class="badge-pill">OFFICIAL SUBMISSION — PLAY RR HACKATHON 2026</div>
      <h1>
        <span class="pink">RAJASTHAN ROYALS</span>
        <span>HIGH-PERFORMANCE CRICKET ANALYTICS</span>
      </h1>
      <p>SupeRR Selector Season 2 — The Halla Bol Pressure Index (Measuring Player Reliability Under Match Pressure)</p>
      <div class="submitter-badge">
        <span>🏆 LEAD SUBMITTER: <b>LOHITHASWIN V</b></span>
        <span>|</span>
        <span>Rajasthan Royals Decision Sciences Group</span>
      </div>
    </div>
    <div class="header-right">
      <div class="pills-group">
        <span class="pill pill-blue">SEASON 2 ROUND 1</span>
        <span class="pill pill-green">PRODUCTION RELEASE 3.1</span>
      </div>
      <div style="font-size: 11px; color: var(--subtext); margin-top: 4px;">
        Dataset: 2022–2026 Cycle (883 Matches, 190,811 Deliveries)
      </div>
    </div>
  </header>

  <!-- OFFICIAL SUBMISSION DOWNLOADS BAR -->
  <section class="download-bar">
    <div class="download-bar-left">
      <div style="font-size: 24px;">📥</div>
      <div>
        <div class="download-bar-title">
          <span>OFFICIAL SUBMISSION DELIVERABLES</span>
          <span class="badge-pill" style="margin: 0; background: rgba(16, 185, 129, 0.2); color: var(--green); border-color: rgba(16, 185, 129, 0.5);">READY FOR UNSTOP</span>
        </div>
        <div class="download-bar-sub">Direct one-click downloads for executive presentation deck and formal methodology whitepaper:</div>
      </div>
    </div>
    <div class="download-btn-group">
      <a href="Play_RR_Hackathon_Lohithaswin_V.pptx" download="Play_RR_Hackathon_Lohithaswin_V.pptx" class="dl-btn dl-btn-pink">
        <span>📊 Download PPTX</span>
        <span class="dl-badge">504 KB</span>
      </a>
      <a href="Play_RR_Hackathon_Lohithaswin_V.pdf" download="Play_RR_Hackathon_Lohithaswin_V.pdf" target="_blank" class="dl-btn dl-btn-blue">
        <span>📄 Presentation PDF</span>
        <span class="dl-badge">659 KB</span>
      </a>
      <a href="Play_RR_Hackathon_Methodology_Report_Lohithaswin_V.docx" download="Play_RR_Hackathon_Methodology_Report_Lohithaswin_V.docx" class="dl-btn dl-btn-gold">
        <span>📝 Report DOCX</span>
        <span class="dl-badge">498 KB</span>
      </a>
      <a href="Play_RR_Hackathon_Methodology_Report_Lohithaswin_V.pdf" download="Play_RR_Hackathon_Methodology_Report_Lohithaswin_V.pdf" target="_blank" class="dl-btn dl-btn-blue">
        <span>📑 Report PDF</span>
        <span class="dl-badge">583 KB</span>
      </a>
      <a href="https://github.com/Lohithaswin/play-rr-hackathon-2026" target="_blank" class="dl-btn dl-btn-dark">
        <span>🐙 GitHub Repo</span>
      </a>
    </div>
  </section>

  <!-- TOP KPI ROW -->
  <section class="kpi-row">
    <div class="kpi-card" style="border-top: 3px solid var(--rr-pink);">
      <div><span class="kpi-tag" style="color: var(--rr-pink);">VOLUME</span><span class="kpi-title">Deliveries Modeled</span></div>
      <div class="kpi-val">190,811</div>
      <div class="kpi-sub">18 Contextual Machine Learning Features</div>
    </div>
    <div class="kpi-card" style="border-top: 3px solid var(--rr-blue-light);">
      <div><span class="kpi-tag" style="color: var(--rr-blue-light);">MATCHES</span><span class="kpi-title">Crucible Fixtures</span></div>
      <div class="kpi-val">883</div>
      <div class="kpi-sub">IPL Franchises & ICC Tier-1 T20Is</div>
    </div>
    <div class="kpi-card" style="border-top: 3px solid var(--rr-gold);">
      <div><span class="kpi-tag" style="color: var(--rr-gold);">WORLD #1 BAT</span><span class="kpi-title">David Miller</span></div>
      <div class="kpi-val" style="color: var(--rr-gold);">80.2 pts</div>
      <div class="kpi-sub">+42.27 Counter-Attack WPA, 8 MWPPs</div>
    </div>
    <div class="kpi-card" style="border-top: 3px solid var(--green);">
      <div><span class="kpi-tag" style="color: var(--green);">WORLD #1 BOWL</span><span class="kpi-title">Jasprit Bumrah</span></div>
      <div class="kpi-val" style="color: var(--green);">78.5 pts</div>
      <div class="kpi-sub">+149.8 Runs Saved at Death, 0 Deductions</div>
    </div>
  </section>

  <!-- TABS NAV -->
  <nav class="tabs-nav">
    <button class="tab-btn active tab-pink" onclick="switchTab('tab-rankings', this)">1. Index Leaderboards & Multi-Phase Audit</button>
    <button class="tab-btn tab-gold" onclick="switchTab('tab-proofs', this)">2. Top 10 Visual Proofs & Evidence Dossiers</button>
    <button class="tab-btn tab-purple" onclick="switchTab('tab-explanations', this)">3. How Each Player Reached Top 10 (Deep Dives)</button>
    <button class="tab-btn tab-blue" onclick="switchTab('tab-audits', this)">4. Analytical Case Studies (The 5 Debates)</button>
    <button class="tab-btn tab-green" onclick="switchTab('tab-methodology', this)">5. Mathematical Architecture & Formulas</button>
  </nav>

  <!-- TAB 1: RANKINGS & TABLES -->
  <div id="tab-rankings" class="tab-content active">
    <div class="grid-2">
      <div class="card-box">
        <div id="bat10-chart" style="width:100%; height:380px;"></div>
      </div>
      <div class="card-box">
        <div id="bowl10-chart" style="width:100%; height:380px;"></div>
      </div>
    </div>

    <div class="grid-2">
      <div class="card-box">
        <div style="margin-bottom: 8px;">
          <span style="font-size: 12px; font-weight: 900; color: var(--rr-pink); letter-spacing: 0.5px;">TOP 10 QUALIFIED BATTERS (≥500 BALLS)</span>
          <span style="font-size: 11px; color: var(--subtext); margin-left: 10px;">Counter-Attack, Crisis Rescue & ML Runs Added</span>
        </div>
        <div class="table-container">
          <table class="rr-table bat" id="bat-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th style="text-align:left;">Player</th>
                <th>Matches</th>
                <th>Consistency</th>
                <th>Counter-Attack</th>
                <th>Crisis Rescue</th>
                <th>Death Finishing</th>
                <th>ML Runs</th>
                <th>Deductions</th>
                <th style="color:var(--rr-gold);">Index Rating</th>
              </tr>
            </thead>
            <tbody></tbody>
          </table>
        </div>
      </div>

      <div class="card-box">
        <div style="margin-bottom: 8px;">
          <span style="font-size: 12px; font-weight: 900; color: var(--rr-blue-light); letter-spacing: 0.5px;">TOP 10 QUALIFIED BOWLERS (MULTI-PHASE AUDIT)</span>
          <span style="font-size: 11px; color: var(--subtext); margin-left: 10px;">PP, Middle, and Death Runs Saved Above Par</span>
        </div>
        <div class="table-container">
          <table class="rr-table bowl" id="bowl-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th style="text-align:left;">Player</th>
                <th>Matches</th>
                <th>Consistency</th>
                <th>PP Saved</th>
                <th>Mid Saved</th>
                <th>Death Saved</th>
                <th>Pressure Eco</th>
                <th>Deductions</th>
                <th style="color:var(--rr-blue-light);">Index Rating</th>
              </tr>
            </thead>
            <tbody></tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <!-- TAB 2: VISUAL PROOFS & FORENSIC DOSSIER -->
  <div id="tab-proofs" class="tab-content">
    <div class="grid-2">
      <div class="card-box">
        <div id="scatter-chart" style="width:100%; height:400px;"></div>
        <div style="margin-top: 8px; font-size: 11px; color: var(--subtext); text-align: center;">
          <span style="color: var(--rr-gold); font-weight:700;">● Gold: Top 3</span> &nbsp;|&nbsp; 
          <span style="color: var(--rr-pink); font-weight:700;">● Pink: Top 4–10</span> &nbsp;|&nbsp; 
          <span style="color: var(--red); font-weight:700;">● Red: Shubman Gill (#11 Flaw Demotion)</span>
        </div>
      </div>
      <div class="card-box">
        <div id="bar-phases-chart" style="width:100%; height:400px;"></div>
      </div>
    </div>

    <div class="grid-2">
      <div class="card-box">
        <div id="minnow-chart" style="width:100%; height:340px;"></div>
      </div>
      <div class="card-box">
        <h4 style="margin: 0 0 10px; font-size: 12px; font-weight: 900; color: var(--rr-gold); letter-spacing: 1px;">CRITICAL TAKEAWAYS FROM VISUAL PROOFS</h4>
        <ul style="padding-left: 16px; margin: 0; font-size: 11px; color: var(--subtext); line-height: 1.6;">
          <li style="margin-bottom: 8px;"><b style="color: var(--rr-gold);">David Miller (+42.27 Counter-Attack WPA):</b> World #1 Match-on-the-Line chase finisher. Unmatched in converting high RRR (≥10.0) run chases into victories with +17.65 Death WPA and 8 Authentic MWPPs.</li>
          <li style="margin-bottom: 8px;"><b style="color: var(--rr-pink);">Suryakumar Yadav (+234.4 ML Runs):</b> World #2 all-phase pressure force. Generates extraordinary runs above par against 98.75% elite bowling, converting 20 crucible matches into team victories.</li>
          <li style="margin-bottom: 8px;"><b style="color: var(--rr-gold);">Heinrich Klaasen (+24.84 Rescue WPA):</b> World #1 in resurrecting batting teams from top-order collapse, obliterating spin across the middle overs.</li>
          <li style="margin-bottom: 8px;"><b style="color: var(--rr-pink);">Jasprit Bumrah (+149.8 Death Saved):</b> Completely off the charts. Concedes 7.36 RPO in pressure and prevents +149.8 runs above expected at the death with 0.0 deductions.</li>
          <li style="margin-bottom: 8px;"><b style="color: var(--rr-gold);">Sunil Narine vs Varun Chakravarthy:</b> Narine is positive across all 3 phases (+20.2, +80.2, +23.6); Varun drops into negative red (-9.61) at the death taking a -7.69 deduction.</li>
          <li><b style="color: var(--green);">Mustafizur Rahman Calibration:</b> 20.7% associate minnow deliveries discounted at 0.40x, correctly situating him at #4 behind Bumrah, Narine, and Hazlewood.</li>
        </ul>
      </div>
    </div>

    <!-- INTERACTIVE FORENSIC DOSSIER -->
    <div class="card-box" style="margin-top: 20px;">
      <div style="margin-bottom: 14px;">
        <h3 style="font-size: 14px; font-weight: 900; color: #ffffff; letter-spacing: 1px;">FORENSIC PLAYER EVIDENCE DOSSIER</h3>
        <p style="font-size: 11px; color: var(--subtext); margin-top: 2px;">Select any qualified batter or bowler to inspect full factor attribution, proof metrics, and high-leverage match logs.</p>
      </div>

      <div class="select-group">
        <div class="select-item">
          <label style="color: var(--rr-pink);">Select Batter:</label>
          <select id="sel-bat" class="rr-select" onchange="updateDossier()"></select>
        </div>
        <div class="select-item">
          <label style="color: var(--rr-blue-light);">Select Bowler:</label>
          <select id="sel-bowl" class="rr-select" onchange="updateDossier()"></select>
        </div>
      </div>

      <div class="dossier-panel">
        <!-- Batting Dossier Column -->
        <div class="player-col" id="bat-dossier-col">
          <div class="player-header">
            <div>
              <span class="rank-tag" id="bat-rank-tag" style="background: var(--rr-pink);">RANK #1</span>
              <div class="player-name-large" id="bat-name-large">DAVID MILLER</div>
              <div class="player-badge-text" id="bat-badge-text">The Undisputed World #1 Chase Finisher</div>
            </div>
            <div style="text-align: right;">
              <span style="font-size: 9px; color: var(--subtext); font-weight: 700; letter-spacing: 1px;">INDEX RATING</span>
              <div class="player-score-large" id="bat-score-large" style="color: var(--rr-pink);">80.2</div>
            </div>
          </div>

          <div class="player-desc" id="bat-desc"></div>

          <div class="mini-kpis">
            <div class="mini-kpi" style="border-top: 2px solid var(--green);">
              <div class="mini-kpi-val" id="bat-kpi-cons" style="color: var(--green);">--</div>
              <div class="mini-kpi-lbl">Consistency</div>
            </div>
            <div class="mini-kpi" style="border-top: 2px solid var(--rr-gold);">
              <div class="mini-kpi-val" id="bat-kpi-ca" style="color: var(--rr-gold);">--</div>
              <div class="mini-kpi-lbl">Chase WPA</div>
            </div>
            <div class="mini-kpi" style="border-top: 2px solid var(--rr-blue-light);">
              <div class="mini-kpi-val" id="bat-kpi-rescue" style="color: var(--rr-blue-light);">--</div>
              <div class="mini-kpi-lbl">Crisis Rescue</div>
            </div>
            <div class="mini-kpi" style="border-top: 2px solid var(--red);" id="bat-kpi-ded-card">
              <div class="mini-kpi-val" id="bat-kpi-ded" style="color: var(--subtext);">--</div>
              <div class="mini-kpi-lbl">Flaw Penalty</div>
            </div>
          </div>

          <div id="bat-waterfall-chart" style="width:100%; height:240px; margin-bottom: 12px;"></div>

          <hr style="border: none; border-top: 1px solid var(--border); margin: 12px 0;">
          <h5 style="margin: 0 0 8px; font-size: 11px; color: var(--rr-pink); text-transform: uppercase; letter-spacing: 0.5px;">Crucible Match Proofs (High-Leverage Record Log):</h5>
          <div id="bat-logs-container"></div>
        </div>

        <!-- Bowling Dossier Column -->
        <div class="player-col" id="bowl-dossier-col">
          <div class="player-header">
            <div>
              <span class="rank-tag" id="bowl-rank-tag" style="background: var(--rr-blue);">RANK #1</span>
              <div class="player-name-large" id="bowl-name-large">JASPRIT BUMRAH</div>
              <div class="player-badge-text" id="bowl-badge-text">Undisputed King of Pace & Clutch Defense</div>
            </div>
            <div style="text-align: right;">
              <span style="font-size: 9px; color: var(--subtext); font-weight: 700; letter-spacing: 1px;">INDEX RATING</span>
              <div class="player-score-large" id="bowl-score-large" style="color: var(--rr-blue-light);">78.5</div>
            </div>
          </div>

          <div class="player-desc" id="bowl-desc"></div>

          <div class="mini-kpis">
            <div class="mini-kpi" style="border-top: 2px solid var(--green);">
              <div class="mini-kpi-val" id="bowl-kpi-cons" style="color: var(--green);">--</div>
              <div class="mini-kpi-lbl">Consistency</div>
            </div>
            <div class="mini-kpi" style="border-top: 2px solid var(--rr-pink);">
              <div class="mini-kpi-val" id="bowl-kpi-death" style="color: var(--rr-pink);">--</div>
              <div class="mini-kpi-lbl">Death Saved</div>
            </div>
            <div class="mini-kpi" style="border-top: 2px solid var(--rr-blue-light);">
              <div class="mini-kpi-val" id="bowl-kpi-eco" style="color: var(--rr-blue-light);">--</div>
              <div class="mini-kpi-lbl">Pressure Eco</div>
            </div>
            <div class="mini-kpi" style="border-top: 2px solid var(--red);" id="bowl-kpi-ded-card">
              <div class="mini-kpi-val" id="bowl-kpi-ded" style="color: var(--subtext);">--</div>
              <div class="mini-kpi-lbl">Flaw Penalty</div>
            </div>
          </div>

          <div id="bowl-waterfall-chart" style="width:100%; height:240px; margin-bottom: 12px;"></div>

          <hr style="border: none; border-top: 1px solid var(--border); margin: 12px 0;">
          <h5 style="margin: 0 0 8px; font-size: 11px; color: var(--rr-blue-light); text-transform: uppercase; letter-spacing: 0.5px;">Crucible Match Proofs (High-Leverage Record Log):</h5>
          <div id="bowl-logs-container"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- TAB 3: HOW EACH PLAYER REACHED TOP 10 (COMPREHENSIVE DEEP DIVES) -->
  <div id="tab-explanations" class="tab-content">
    <div style="margin-bottom: 16px;">
      <h3 style="font-size: 16px; font-weight: 900; color: #ffffff; letter-spacing: 0.5px;">
        <span style="color: var(--rr-gold);">THE CRUCIBLE ROSTER:</span> Exactly How Each Player Earned Their Top 10 Rank
      </h3>
      <p style="font-size: 12px; color: var(--subtext); margin-top: 4px;">
        Every ranking is strictly data-driven: isolating high-pressure win probability added, collapse rescue, opponent tiering, and zero tolerance for fatal execution flaws.
      </p>
    </div>

    <!-- Toggle Buttons for Batters vs Bowlers Breakdown -->
    <div style="display:flex; gap:10px; margin-bottom: 16px;">
      <button id="btn-show-bat-explain" class="tab-btn active tab-pink" onclick="toggleExplainView('bat')">Top 10 Batters Qualification (10 Players)</button>
      <button id="btn-show-bowl-explain" class="tab-btn tab-blue" onclick="toggleExplainView('bowl')">Top 10 Bowlers Qualification (10 Players)</button>
    </div>

    <!-- Batters Breakdown Grid -->
    <div id="batters-explain-grid" class="top10-grid"></div>

    <!-- Bowlers Breakdown Grid -->
    <div id="bowlers-explain-grid" class="top10-grid" style="display:none;"></div>
  </div>

  <!-- TAB 4: CASE STUDIES -->
  <div id="tab-audits" class="tab-content">
    <div class="grid-2">
      <!-- Case 1 -->
      <div class="case-card">
        <span class="case-tag">CASE STUDY 01</span>
        <h4 class="case-title">Sunil Narine (#2) Decisively Outperforms Varun Chakravarthy (#9)</h4>
        <p class="case-p">Both are world-class mystery spinners, but their pressure execution diverges drastically in the death overs.</p>
        <div class="case-split">
          <div class="case-box" style="background: rgba(234, 0, 138, 0.05); border-color: rgba(234, 0, 138, 0.2);">
            <h5 style="color: var(--rr-pink); font-size: 12px; margin-bottom: 6px;">Sunil Narine (#2 — 52.4 pts)</h5>
            <ul style="padding-left: 14px; font-size: 11px; color: var(--subtext); line-height: 1.5;">
              <li>Positive runs saved in ALL 3 phases (+20.2 PP, +80.2 Mid, +23.6 Death)</li>
              <li>Faced 100% Tier-1 elite opposition (0.0% minnows)</li>
              <li>Economy rate in pressure: 7.88 RPO | 0.0 Deductions</li>
            </ul>
          </div>
          <div class="case-box" style="background: rgba(30, 64, 175, 0.05); border-color: rgba(30, 64, 175, 0.2);">
            <h5 style="color: var(--rr-blue-light); font-size: 12px; margin-bottom: 6px;">Varun Chakravarthy (#9 — 38.6 pts)</h5>
            <ul style="padding-left: 14px; font-size: 11px; color: var(--subtext); line-height: 1.5;">
              <li>Exceptional in PP (+36.7) and Mid (+25.7)</li>
              <li style="color: var(--red);">Conceded -9.61 runs above expected at the Death</li>
              <li style="color: var(--red);">Takes an explicit -7.69 pt Non-Negotiable Flaw Penalty</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Case 2 -->
      <div class="case-card">
        <span class="case-tag">CASE STUDY 02</span>
        <h4 class="case-title">Schedule Strength Calibration: Mustafizur (#4) vs Top 3</h4>
        <p class="case-p">In unweighted systems, Mustafizur inflated raw numbers in low-scoring Dhaka bilaterals. Context weighting reveals the true hierarchy.</p>
        <div class="case-box" style="background: rgba(255, 255, 255, 0.02); margin-top: 10px;">
          <ul style="padding-left: 14px; font-size: 11px; color: var(--subtext); line-height: 1.6;">
            <li>20.7% of Mustafizur's deliveries (324 balls) came against minnows (Zimbabwe, UAE, Netherlands, Oman) on 120-run par pitches.</li>
            <li>With 0.40x associate discounting, his inflated numbers adjust to true elite par.</li>
            <li style="color: var(--green); font-weight: 700;">Result: Jasprit Bumrah (#1), Sunil Narine (#2), and Josh Hazlewood (#3) rightfully hold the podium.</li>
          </ul>
        </div>
      </div>
    </div>

    <div class="grid-2">
      <!-- Case 3 -->
      <div class="case-card">
        <span class="case-tag">CASE STUDY 03</span>
        <h4 class="case-title">Match-on-the-Line Priority: Pooran (#9) & Kohli (#8) Surpass Gill (#11)</h4>
        <p class="case-p">Top-order batters who fail to stabilize the team during collapses cannot be compensated by comfortable front-running runs.</p>
        <ul style="padding-left: 14px; font-size: 11px; color: var(--subtext); line-height: 1.6;">
          <li><b>Nicholas Pooran (#9 — 46.2 pts):</b> World-leading 74.5% pressure consistency, +25.49 Counter-Attack WPA, and 5 Authentic MWPPs with 0.0 deductions.</li>
          <li><b>Virat Kohli (#8 — 47.5 pts):</b> Delivers unmatched chase pacing with +35.50 Counter-Attack WPA and 6 Authentic MWPPs against 100% elite bowling.</li>
          <li style="color: var(--red);"><b>Shubman Gill:</b> Negative crisis rescue score (-2.03 WPA), repeatedly falling cheaply during early collapse states. Incurs a mandatory -15.3 pt flaw penalty demoting him to #11.</li>
        </ul>
      </div>

      <!-- Case 4 -->
      <div class="case-card">
        <span class="case-tag">CASE STUDY 04</span>
        <h4 class="case-title">Specialist Standard (≥750 Balls): Filtering Cameos & Tailenders</h4>
        <p class="case-p">A true clutch batting index must evaluate proven top/middle-order specialists who bear match responsibility, not brief cameos or lower-order tailenders.</p>
        <ul style="padding-left: 14px; font-size: 11px; color: var(--subtext); line-height: 1.6;">
          <li><b>Rashid Khan (506 balls):</b> Elite bowler (#7 globally), but batting down at #8 with 506 balls creates massive volatility distortion; belongs strictly in bowling ranks.</li>
          <li><b>Cameron Green:</b> Manages only +11.8 Counter-Attack WPA and fails high-pressure match-on-the-line impact despite high raw strike rate.</li>
          <li style="color: var(--green);"><b>Dinesh Karthik (637 balls, 0.0 Death WPA) & MS Dhoni (460 balls):</b> Correctly filtered by the substantive ≥750 balls standard, preventing sample distortion.</li>
        </ul>
      </div>
    </div>

    <!-- Case 5 -->
    <div class="case-card">
      <span class="case-tag">CASE STUDY 05</span>
      <h4 class="case-title">Phase Risk Audit: Siraj (#19) and Bishnoi (#51) Demoted</h4>
      <p class="case-p">Death overs defense is non-negotiable. Fatal leakage cannot be masked by good powerplay or middle overs bowling.</p>
      <ul style="padding-left: 14px; font-size: 11px; color: var(--subtext); line-height: 1.6;">
        <li style="color: var(--red);"><b>Mohammed Siraj:</b> Leaked -20.99 runs above expected at the death at 8.98 RPO (-16.8 pt penalty, Rank #19).</li>
        <li style="color: var(--red);"><b>Ravi Bishnoi:</b> Leaked -41.78 runs above expected at the death at 10.42 RPO (-33.4 pt penalty, Rank #51).</li>
        <li>Both bowlers demonstrate extreme tactical liability in death-pressure situations, proving why death runs saved must carry non-compensatory flaw penalties.</li>
      </ul>
    </div>
  </div>

  <!-- TAB 5: MATHEMATICAL METHODOLOGY -->
  <div id="tab-methodology" class="tab-content">
    <div class="grid-2">
      <div class="card-box">
        <span class="case-tag">IDENTIFICATION ENGINE</span>
        <h3 style="color: #ffffff; font-size: 15px; font-weight: 900; margin: 4px 0 12px;">HOW BIG MATCHES & MUST-WINS ARE IDENTIFIED</h3>
        
        <div style="background: rgba(255, 255, 255, 0.02); padding: 12px; border-radius: 8px; border: 1px solid var(--border); margin-bottom: 12px;">
          <h4 style="color: var(--rr-pink); font-size: 12px; margin-bottom: 4px;">1. Tournament Knockouts & Elimination Stakes (1.50x Multiplier)</h4>
          <p style="font-size: 11px; color: var(--subtext); line-height: 1.5;">Every delivery is tagged by match stage metadata. Matches qualify for the 1.50x Big-Match Knockout Multiplier if knock_out == 1 OR stage is classified as Final, Eliminator, Qualifier 1, Qualifier 2, Semi Final, or Super 4. Defeat terminates the campaign.</p>
        </div>

        <div style="background: rgba(255, 255, 255, 0.02); padding: 12px; border-radius: 8px; border: 1px solid var(--border); margin-bottom: 12px;">
          <h4 style="color: var(--rr-pink); font-size: 12px; margin-bottom: 4px;">2. The 'Crucible Match Win' Attribution Filter (Authentic MWPPs)</h4>
          <p style="font-size: 11px; color: var(--subtext); line-height: 1.5; margin-bottom: 6px;">Eliminates empty stat-padding by requiring all 4 criteria simultaneously:</p>
          <ul style="padding-left: 14px; font-size: 11px; color: var(--subtext); line-height: 1.5;">
            <li><b>Outcome Mandate:</b> Team MUST have won the match (team_won == 1). Runs or wickets in lost causes receive zero match-win credit.</li>
            <li><b>Minimum Leverage Threshold:</b> High-Pressure WPA ≥ +0.50 (or HP strike rate ≥ 160 with ≥ 20 runs scored under pressure).</li>
            <li><b>Crisis / Finishing Requirement:</b> Either Death Chase WPA ≥ 1.0 or Crisis Rescue WPA ≥ 1.5.</li>
          </ul>
        </div>

        <div style="background: rgba(255, 255, 255, 0.02); padding: 12px; border-radius: 8px; border: 1px solid var(--border);">
          <h4 style="color: var(--rr-pink); font-size: 12px; margin-bottom: 4px;">3. Schedule Strength & Opposition Tiering</h4>
          <ul style="padding-left: 14px; font-size: 11px; color: var(--subtext); line-height: 1.5;">
            <li><b>Tier 1 Elite (1.25x Boost):</b> All IPL franchise clashes, India, Australia, England, South Africa, New Zealand, Pakistan, West Indies.</li>
            <li><b>Associate / Minnow (0.40x Discount):</b> Bilateral series against lower-tier associates (e.g. Zimbabwe, UAE, Netherlands, Oman) on low-par pitches.</li>
          </ul>
        </div>
      </div>

      <div class="card-box">
        <span class="case-tag">DYNAMIC PRESSURE ENGINE</span>
        <h3 style="color: #ffffff; font-size: 15px; font-weight: 900; margin: 4px 0 12px;">DYNAMIC BALL-BY-BALL PRESSURE DETECTION</h3>
        
        <div style="background: rgba(255, 255, 255, 0.02); padding: 12px; border-radius: 8px; border: 1px solid var(--border); margin-bottom: 12px;">
          <h4 style="color: var(--rr-blue-light); font-size: 12px; margin-bottom: 4px;">1. Instantaneous Leverage Index (LI ≥ 1.50)</h4>
          <p style="font-size: 11px; color: var(--subtext); line-height: 1.5;">Evaluated on every delivery as the derivative of Win Probability: LI = (ΔWP_wicket - ΔWP_boundary) / σ_WP. Isolates deliveries where a single boundary or wicket swings match probability by at least 1.5x the historical volatility (top 15% game-defining deliveries).</p>
        </div>

        <div style="background: rgba(255, 255, 255, 0.02); padding: 12px; border-radius: 8px; border: 1px solid var(--border); margin-bottom: 12px;">
          <h4 style="color: var(--rr-blue-light); font-size: 12px; margin-bottom: 4px;">2. Scoreboard Chase Pressure (RRR ≥ 10.0 RPO)</h4>
          <p style="font-size: 11px; color: var(--subtext); line-height: 1.5;">Triggered in second innings run chases where required run rate reaches or exceeds 10.0 runs per over with fewer than 8 wickets in hand. Evaluates ice-cold boundary hitting under escalating scoreboard pressure.</p>
        </div>

        <div style="background: rgba(255, 255, 255, 0.02); padding: 12px; border-radius: 8px; border: 1px solid var(--border); margin-bottom: 12px;">
          <h4 style="color: var(--rr-blue-light); font-size: 12px; margin-bottom: 4px;">3. Crisis Collapse Windows (Early & Middle Overs)</h4>
          <p style="font-size: 11px; color: var(--subtext); line-height: 1.5;">Identifies deliveries where the batting team is reeling in a top-order collapse: Powerplay Crisis (Overs 1–6 with ≥ 2 wickets lost) or Middle Overs Collapse (Overs 7–12 with ≥ 4 wickets lost). Distinguishes authentic innings resurrection from front-running.</p>
        </div>

        <div style="background: rgba(255, 255, 255, 0.02); padding: 12px; border-radius: 8px; border: 1px solid var(--border);">
          <h4 style="color: var(--rr-blue-light); font-size: 12px; margin-bottom: 4px;">4. Death Crucible (Overs 16–20)</h4>
          <p style="font-size: 11px; color: var(--subtext); line-height: 1.5;">Deliveries in the final four overs when match margin is under 36 runs with result undecided. Death yorkers and boundary balls carry maximal leverage multipliers.</p>
        </div>
      </div>
    </div>

    <div class="grid-2">
      <!-- Weightage Matrix -->
      <div class="card-box">
        <h3 style="color: var(--rr-gold); font-size: 14px; font-weight: 900; margin-bottom: 14px; letter-spacing: 1px;">EXACT MATHEMATICAL WEIGHTAGE MATRIX</h3>
        <h5 style="color: var(--rr-pink); font-size: 11px; font-weight: 800; margin-bottom: 6px;">BATTING CLUTCH SCORE (0–100 SCALE):</h5>
        <ul style="padding-left: 14px; font-size: 11px; color: var(--subtext); line-height: 1.6; margin-bottom: 14px;">
          <li><b>Counter-Attack Chasing RRR≥10.0 (24%):</b> WPA when chasing steep targets under escalating scoreboard pressure.</li>
          <li><b>Crisis Collapse Rescue (20%):</b> WPA resurrecting innings after top-order collapses (≤2 wickets down in Powerplay).</li>
          <li><b>Quality Win Impact (20%):</b> High-pressure WPA generated exclusively in team victories against Tier-1 elite attacks.</li>
          <li><b>Authentic MWPPs (14%):</b> Frequency of Authentic Match-Winning Pressure Performances delivering decisive results.</li>
          <li><b>Death Chase Finishing (12%):</b> Finishing execution in overs 16–20 under tight margins (<36 runs).</li>
          <li><b>Pressure Consistency Rate (10%):</b> Proportion of high-leverage matches maintaining net-positive match contribution.</li>
          <li style="color: var(--rr-gold);"><b>Specialist Standard Filter:</b> Mandatory threshold of ≥ 750 career balls faced to filter cameos and tailenders.</li>
          <li style="color: var(--red);"><b>Non-Compensatory Flaw Penalties:</b> Negative Crisis Rescue WPA penalized at 7.5x; negative death execution at 3.0x.</li>
        </ul>

        <hr style="border: none; border-top: 1px solid var(--border); margin: 12px 0;">

        <h5 style="color: var(--rr-blue-light); font-size: 11px; font-weight: 800; margin-bottom: 6px;">BOWLING CLUTCH SCORE (0–100 SCALE):</h5>
        <ul style="padding-left: 14px; font-size: 11px; color: var(--subtext); line-height: 1.6;">
          <li><b>Quality Runs Saved (30%):</b> ML runs saved across PP (1–6), Middle (7–15), and Death (16–20).</li>
          <li><b>Momentum-Breaking Dots (20%):</b> Dot balls delivered in high-pressure defensive overs.</li>
          <li><b>Clutch Wickets (18%):</b> Breakthrough wickets removing set batters under pressure.</li>
          <li><b>Pressure Consistency (16%):</b> Proportion of matches with positive pressure contributions.</li>
          <li><b>Pressure Economy vs Par (10%):</b> Suppression of run flow below venue par rate.</li>
          <li><b>High-Pressure WPA (6%):</b> Net win probability swung towards bowling side.</li>
          <li style="color: var(--red);"><b>Non-Compensatory Flaw Penalty:</b> Death overs runs leaked above par penalized at 0.80x.</li>
        </ul>
      </div>

      <!-- ML Engine -->
      <div class="card-box">
        <h3 style="color: var(--green); font-size: 14px; font-weight: 900; margin-bottom: 14px; letter-spacing: 1px;">THE XGBOOST ML CONTEXT ENGINE</h3>
        <p style="font-size: 11px; color: var(--subtext); line-height: 1.6; margin-bottom: 12px;">Rather than using crude batting averages or economy rates, our model evaluates performance against ball-by-ball expected runs E[Runs] trained on 190,811 deliveries using 18 predictive contextual features:</p>
        <ul style="padding-left: 14px; font-size: 11px; color: var(--subtext); line-height: 1.6; margin-bottom: 14px;">
          <li><b>Ground & Venue Par:</b> Historical ground scoring index and pitch pacing rate.</li>
          <li><b>Innings Phase:</b> Overs remaining and exact ball number in the current over.</li>
          <li><b>Wickets & Pressure:</b> Cumulative wickets lost and current match run rate.</li>
          <li><b>Target Dynamics:</b> Required run rate and target differential in second-innings chases.</li>
          <li><b>Tactical Matchups:</b> Batter career archetype vs bowler arm and skill (RHB vs SLA, LHB vs Off-Spin).</li>
        </ul>
        <hr style="border: none; border-top: 1px solid var(--border); margin: 12px 0;">
        <h5 style="color: var(--rr-gold); font-size: 11px; font-weight: 800; margin-bottom: 6px;">SAMPLE RELIABILITY FILTER:</h5>
        <p style="font-size: 11px; color: var(--subtext); line-height: 1.6;">To prevent single-match flukes, scores are scaled by a square-root reliability curve: Reliability = sqrt(Matches / 45) capped at 1.0. Batters must also satisfy the Substantive Volume Standard (≥ 500 balls faced) to eliminate cameo specialists.</p>
      </div>
    </div>
  </div>

  <!-- FOOTER -->
  <footer>
    <div>
      <b>Play RR Hackathon 2026 — Season 2</b> | Submitter: <b>Lohithaswin V</b> | Rajasthan Royals Analytics Studio v3.1
    </div>
    <div>
      <a href="https://github.com/Lohithaswin/play-rr-hackathon-2026" target="_blank" style="color:var(--rr-pink); font-weight:700; margin-right:16px;">GitHub Repository</a>
      <span style="color:var(--rr-gold); font-weight:800;">Halla Bol! 🏆</span>
    </div>
  </footer>

  <!-- DATA & JAVASCRIPT LOGIC -->
  <script>
    const PAYLOAD = {payload_json_str};

    // Render Tab 1 & Tab 2 Static Charts
    function renderMainCharts() {{
      Plotly.newPlot('bat10-chart', PAYLOAD.bat10_chart.data, PAYLOAD.bat10_chart.layout, {{responsive: true, displayModeBar: false}});
      Plotly.newPlot('bowl10-chart', PAYLOAD.bowl10_chart.data, PAYLOAD.bowl10_chart.layout, {{responsive: true, displayModeBar: false}});
      Plotly.newPlot('scatter-chart', PAYLOAD.scatter_chart.data, PAYLOAD.scatter_chart.layout, {{responsive: true, displayModeBar: false}});
      Plotly.newPlot('bar-phases-chart', PAYLOAD.bar_phases_chart.data, PAYLOAD.bar_phases_chart.layout, {{responsive: true, displayModeBar: false}});
      Plotly.newPlot('minnow-chart', PAYLOAD.minnow_chart.data, PAYLOAD.minnow_chart.layout, {{responsive: true, displayModeBar: false}});
    }}

    // Populate Tables
    function populateTables() {{
      const batTbody = document.querySelector('#bat-table tbody');
      batTbody.innerHTML = '';
      PAYLOAD.bat_table.forEach((r, idx) => {{
        const tr = document.createElement('tr');
        if (idx === 0) tr.className = 'top-1';
        tr.innerHTML = `
          <td>${{r.rank}}</td>
          <td class="player-name">${{r.name}}</td>
          <td>${{r.matches}}</td>
          <td>${{r.consistency}}</td>
          <td>${{r.ca_wpa}}</td>
          <td>${{r.rescue_wpa}}</td>
          <td>${{r.da_wpa}}</td>
          <td>${{r.ml_runs}}</td>
          <td style="color:${{r.deductions !== '-0.0' ? 'var(--red)' : 'var(--subtext)'}}">${{r.deductions}}</td>
          <td style="font-weight:900; color:var(--rr-gold);">${{r.score}}</td>
        `;
        batTbody.appendChild(tr);
      }});

      const bowlTbody = document.querySelector('#bowl-table tbody');
      bowlTbody.innerHTML = '';
      PAYLOAD.bowl_table.forEach((r, idx) => {{
        const tr = document.createElement('tr');
        if (idx === 0) tr.className = 'top-1';
        tr.innerHTML = `
          <td>${{r.rank}}</td>
          <td class="player-name">${{r.name}}</td>
          <td>${{r.matches}}</td>
          <td>${{r.consistency}}</td>
          <td>${{r.pp_saved}}</td>
          <td>${{r.mid_saved}}</td>
          <td>${{r.death_saved}}</td>
          <td>${{r.eco}}</td>
          <td style="color:${{r.deductions !== '-0.0' ? 'var(--red)' : 'var(--subtext)'}}">${{r.deductions}}</td>
          <td style="font-weight:900; color:var(--rr-blue-light);">${{r.score}}</td>
        `;
        bowlTbody.appendChild(tr);
      }});
    }}

    // Populate Dropdowns
    function populateDropdowns() {{
      const selBat = document.getElementById('sel-bat');
      selBat.innerHTML = '';
      Object.keys(PAYLOAD.batters_data).forEach(name => {{
        const b = PAYLOAD.batters_data[name];
        const opt = document.createElement('option');
        opt.value = name;
        opt.textContent = `#${{b.rank}} ${{b.name}} (${{b.score.toFixed(1)}} pts)`;
        selBat.appendChild(opt);
      }});

      const selBowl = document.getElementById('sel-bowl');
      selBowl.innerHTML = '';
      Object.keys(PAYLOAD.bowlers_data).forEach(name => {{
        const bw = PAYLOAD.bowlers_data[name];
        const opt = document.createElement('option');
        opt.value = name;
        const demoteLabel = bw.rank > 10 ? ' - Flaw Demotion' : '';
        opt.textContent = `#${{bw.rank}} ${{bw.name}} (${{bw.score.toFixed(1)}} pts${{demoteLabel}})`;
        selBowl.appendChild(opt);
      }});
    }}

    // Update Dossier
    function updateDossier() {{
      const batName = document.getElementById('sel-bat').value;
      const bowlName = document.getElementById('sel-bowl').value;

      const b = PAYLOAD.batters_data[batName];
      if (b) {{
        document.getElementById('bat-rank-tag').textContent = `RANK #${{b.rank}}`;
        document.getElementById('bat-name-large').textContent = b.name.toUpperCase();
        document.getElementById('bat-badge-text').textContent = b.title;
        document.getElementById('bat-score-large').textContent = b.score.toFixed(1);
        document.getElementById('bat-desc').textContent = b.why_top10;
        document.getElementById('bat-kpi-cons').textContent = b.consistency;
        document.getElementById('bat-kpi-ca').textContent = b.ca_wpa;
        document.getElementById('bat-kpi-rescue').textContent = b.rescue_wpa;
        document.getElementById('bat-kpi-ded').textContent = b.deductions;
        document.getElementById('bat-kpi-ded').style.color = b.deductions_val > 0 ? 'var(--red)' : 'var(--subtext)';

        Plotly.newPlot('bat-waterfall-chart', b.waterfall.data, b.waterfall.layout, {{responsive: true, displayModeBar: false}});

        const batLogsCont = document.getElementById('bat-logs-container');
        batLogsCont.innerHTML = '';
        b.logs.forEach(l => {{
          const div = document.createElement('div');
          div.className = 'match-log-item';
          div.innerHTML = `
            <span style="color:var(--rr-gold); font-weight:700; font-size:10px;">[${{l.date}}]</span>
            <span style="color:#ffffff; font-weight:700;">vs ${{l.opponent}} (${{l.comp}})</span>
            <span style="color:var(--subtext);"> — ${{l.runs}} runs off ${{l.balls}}b (HP SR: ${{l.hp_sr.toFixed(1)}})</span>
            <span style="color:var(--green); font-weight:700; margin-left:6px;">[WPA: +${{l.wpa.toFixed(2)}}]</span>
          `;
          batLogsCont.appendChild(div);
        }});
      }}

      const bw = PAYLOAD.bowlers_data[bowlName];
      if (bw) {{
        document.getElementById('bowl-rank-tag').textContent = `RANK #${{bw.rank}}`;
        document.getElementById('bowl-name-large').textContent = bw.name.toUpperCase();
        document.getElementById('bowl-badge-text').textContent = bw.title;
        document.getElementById('bowl-score-large').textContent = bw.score.toFixed(1);
        document.getElementById('bowl-desc').textContent = bw.why_top10;
        document.getElementById('bowl-kpi-cons').textContent = bw.consistency;
        document.getElementById('bowl-kpi-death').textContent = bw.death_saved;
        document.getElementById('bowl-kpi-eco').textContent = bw.eco;
        document.getElementById('bowl-kpi-ded').textContent = bw.deductions;
        document.getElementById('bowl-kpi-ded').style.color = bw.deductions_val > 0 ? 'var(--red)' : 'var(--subtext)';

        Plotly.newPlot('bowl-waterfall-chart', bw.waterfall.data, bw.waterfall.layout, {{responsive: true, displayModeBar: false}});

        const bowlLogsCont = document.getElementById('bowl-logs-container');
        bowlLogsCont.innerHTML = '';
        bw.logs.forEach(l => {{
          const div = document.createElement('div');
          div.className = 'match-log-item';
          div.innerHTML = `
            <span style="color:var(--rr-gold); font-weight:700; font-size:10px;">[${{l.date}}]</span>
            <span style="color:#ffffff; font-weight:700;">vs ${{l.opponent}} (${{l.comp}})</span>
            <span style="color:var(--subtext);"> — ${{l.wkts}}/${{l.runs}} (${{l.balls}}b, Eco: ${{l.eco.toFixed(2)}})</span>
            <span style="color:var(--green); font-weight:700; margin-left:6px;">[WPA: +${{l.wpa.toFixed(2)}}]</span>
          `;
          bowlLogsCont.appendChild(div);
        }});
      }}
    }}

    // Render Top 10 Deep Dive Explanations Cards
    function renderExplanations() {{
      const batGrid = document.getElementById('batters-explain-grid');
      batGrid.innerHTML = '';
      Object.keys(PAYLOAD.top10_bat_explanations).forEach(name => {{
        const item = PAYLOAD.top10_bat_explanations[name];
        const card = document.createElement('div');
        card.className = 'player-explain-card bat-card';
        
        let formulaHtml = '';
        item.key_formula_breakdown.forEach(f => {{
          formulaHtml += `
            <div class="formula-row">
              <span style="color:var(--subtext);">${{f.metric}}</span>
              <span style="font-weight:700; color:${{f.color}};">${{f.val}} (${{f.impact}})</span>
            </div>
          `;
        }});

        const bData = PAYLOAD.batters_data[name] || {{score: 0}};
        card.innerHTML = `
          <div class="explain-header">
            <div>
              <span class="rank-tag" style="background:var(--rr-pink);">RANK #${{item.rank}}</span>
              <div class="explain-name">${{name.toUpperCase()}}</div>
              <div class="explain-archetype">${{item.archetype}}</div>
            </div>
            <div class="explain-score" style="color:var(--rr-pink);">${{bData.score ? bData.score.toFixed(1) : ''}} <span style="font-size:12px; color:var(--subtext);">pts</span></div>
          </div>
          <p class="explain-why">${{item.why_top10}}</p>
          <div class="formula-items">
            <div style="font-size:9px; font-weight:800; color:var(--rr-gold); text-transform:uppercase; margin-bottom:4px;">Core Index Contribution:</div>
            ${{formulaHtml}}
          </div>
          <div class="sig-match">
            <b style="color:var(--rr-gold);">Crucible Proof:</b> ${{item.signature_matches}}
          </div>
        `;
        batGrid.appendChild(card);
      }});

      const bowlGrid = document.getElementById('bowlers-explain-grid');
      bowlGrid.innerHTML = '';
      Object.keys(PAYLOAD.top10_bowl_explanations).forEach(name => {{
        const item = PAYLOAD.top10_bowl_explanations[name];
        const card = document.createElement('div');
        card.className = 'player-explain-card bowl-card';
        
        let formulaHtml = '';
        item.key_formula_breakdown.forEach(f => {{
          formulaHtml += `
            <div class="formula-row">
              <span style="color:var(--subtext);">${{f.metric}}</span>
              <span style="font-weight:700; color:${{f.color}};">${{f.val}} (${{f.impact}})</span>
            </div>
          `;
        }});

        const bwData = PAYLOAD.bowlers_data[name] || {{score: 0}};
        card.innerHTML = `
          <div class="explain-header">
            <div>
              <span class="rank-tag" style="background:var(--rr-blue);">RANK #${{item.rank}}</span>
              <div class="explain-name">${{name.toUpperCase()}}</div>
              <div class="explain-archetype">${{item.archetype}}</div>
            </div>
            <div class="explain-score" style="color:var(--rr-blue-light);">${{bwData.score ? bwData.score.toFixed(1) : ''}} <span style="font-size:12px; color:var(--subtext);">pts</span></div>
          </div>
          <p class="explain-why">${{item.why_top10}}</p>
          <div class="formula-items">
            <div style="font-size:9px; font-weight:800; color:var(--rr-gold); text-transform:uppercase; margin-bottom:4px;">Core Index Contribution:</div>
            ${{formulaHtml}}
          </div>
          <div class="sig-match">
            <b style="color:var(--rr-gold);">Crucible Proof:</b> ${{item.signature_matches}}
          </div>
        `;
        bowlGrid.appendChild(card);
      }});
    }}

    // Toggle Explain View (Batters vs Bowlers)
    function toggleExplainView(type) {{
      const batGrid = document.getElementById('batters-explain-grid');
      const bowlGrid = document.getElementById('bowlers-explain-grid');
      const btnBat = document.getElementById('btn-show-bat-explain');
      const btnBowl = document.getElementById('btn-show-bowl-explain');

      if (type === 'bat') {{
        batGrid.style.display = 'grid';
        bowlGrid.style.display = 'none';
        btnBat.className = 'tab-btn active tab-pink';
        btnBowl.className = 'tab-btn tab-blue';
      }} else {{
        batGrid.style.display = 'none';
        bowlGrid.style.display = 'grid';
        btnBat.className = 'tab-btn tab-pink';
        btnBowl.className = 'tab-btn active tab-blue';
      }}
    }}

    // Switch Tabs
    function switchTab(tabId, btn) {{
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

      btn.classList.add('active');
      const target = document.getElementById(tabId);
      if (target) {{
        target.classList.add('active');
        // Trigger Plotly relayout to ensure proper width when tab becomes visible
        setTimeout(() => {{
          window.dispatchEvent(new Event('resize'));
          if (tabId === 'tab-proofs') {{
            Plotly.Plots.resize('scatter-chart');
            Plotly.Plots.resize('bar-phases-chart');
            Plotly.Plots.resize('minnow-chart');
            Plotly.Plots.resize('bat-waterfall-chart');
            Plotly.Plots.resize('bowl-waterfall-chart');
          }} else if (tabId === 'tab-rankings') {{
            Plotly.Plots.resize('bat10-chart');
            Plotly.Plots.resize('bowl10-chart');
          }}
        }}, 50);
      }}
    }}

    // Initial Load
    window.addEventListener('DOMContentLoaded', () => {{
      renderMainCharts();
      populateTables();
      populateDropdowns();
      updateDossier();
      renderExplanations();
    }});
  </script>
</body>
</html>
"""

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("Generated upgraded index.html with interactive deep dives successfully!")
