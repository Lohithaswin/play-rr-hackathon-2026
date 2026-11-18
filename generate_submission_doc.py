import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import win32com.client

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'''
        <w:tcMar {nsdecls("w")}>
            <w:top w:w="{top}" w:type="dxa"/>
            <w:bottom w:w="{bottom}" w:type="dxa"/>
            <w:left w:w="{left}" w:type="dxa"/>
            <w:right w:w="{right}" w:type="dxa"/>
        </w:tcMar>
    ''')
    tcPr.append(tcMar)

def create_callout_box(doc, title, text_paragraphs, border_color="EA008A", bg_color="F8FAFC"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, bg_color)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    
    # Border: left thick colored border, none for others
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>
            <w:left w:val="single" w:sz="36" w:space="0" w:color="{border_color}"/>
            <w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>
            <w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>
        </w:tcBorders>
    ''')
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(4)
    run_t = p.add_run(title.upper())
    run_t.bold = True
    run_t.font.name = 'Segoe UI'
    run_t.font.size = Pt(10.5)
    run_t.font.color.rgb = RGBColor.from_string(border_color)
    
    for t in text_paragraphs:
        p2 = cell.add_paragraph()
        p2.paragraph_format.space_before = Pt(2)
        p2.paragraph_format.space_after = Pt(4)
        r = p2.add_run(t)
        r.font.name = 'Segoe UI'
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(51, 65, 85)
        
    doc.add_paragraph().paragraph_format.space_after = Pt(6)

def build_methodology_document():
    doc = docx.Document()
    
    # Page setup: Normal Margins (1 inch)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
        # Header & Footer
        header = section.header
        hp = header.paragraphs[0]
        hp.text = "RAJASTHAN ROYALS HIGH-PERFORMANCE ANALYTICS  |  SUPERR SELECTOR SEASON 2"
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hp.runs[0].font.name = 'Segoe UI'
        hp.runs[0].font.size = Pt(8.5)
        hp.runs[0].font.color.rgb = RGBColor(148, 163, 184)
        
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.text = "Official Submission Report  •  Submitted by: Lohithaswin V  •  The Halla Bol Pressure Index"
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        fp.runs[0].font.name = 'Segoe UI'
        fp.runs[0].font.size = Pt(8.5)
        fp.runs[0].font.color.rgb = RGBColor(148, 163, 184)

    # Styles setup
    style_normal = doc.styles['Normal']
    style_normal.font.name = 'Segoe UI'
    style_normal.font.size = Pt(10)
    style_normal.font.color.rgb = RGBColor(30, 41, 59) # Slate 800

    # ─────────────────────────────────────────────────────────────────────────
    # COVER PAGE
    # ─────────────────────────────────────────────────────────────────────────
    p_pre = doc.add_paragraph()
    p_pre.paragraph_format.space_before = Pt(36)
    p_pre.paragraph_format.space_after = Pt(4)
    run_pre = p_pre.add_run("PLAY RR HACKATHON 2026 — SUPERR SELECTOR SEASON 2")
    run_pre.font.size = Pt(11)
    run_pre.font.bold = True
    run_pre.font.color.rgb = RGBColor(234, 0, 138) # RR Pink

    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(8)
    run_title = p_title.add_run("The Halla Bol Pressure Index")
    run_title.font.size = Pt(28)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(15, 23, 42) # Dark Navy

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(24)
    run_sub = p_sub.add_run("Context-Aware Multi-Phase Leverage, Machine Learning Attribution & Win Probability Added Framework for Player Reliability Under Match Pressure")
    run_sub.font.size = Pt(13)
    run_sub.font.color.rgb = RGBColor(30, 64, 175) # Royal Blue

    # Metadata Card Table
    meta_tbl = doc.add_table(rows=5, cols=2)
    meta_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_tbl.autofit = False
    meta_tbl.columns[0].width = Inches(2.2)
    meta_tbl.columns[1].width = Inches(4.3)
    
    meta_data = [
        ("Submitted by:", "LOHITHASWIN V"),
        ("Target Organization:", "Rajasthan Royals (RR) Analytics & High-Performance Decision Sciences"),
        ("Competition Domain:", "Round 1 Problem Statement: Identify Most Reliable Players Under Pressure"),
        ("Dataset Scope & Horizon:", "IPL & T20 Internationals (2022–2026 Cycle) | 883 Matches | 190,811 Deliveries"),
        ("Software Deliverables:", "Live Production Web Studio, Dash Dashboard, Clean Datasets, PPTX Deck")
    ]
    for idx, (label, val) in enumerate(meta_data):
        c1, c2 = meta_tbl.cell(idx, 0), meta_tbl.cell(idx, 1)
        set_cell_background(c1, "F1F5F9")
        set_cell_background(c2, "FFFFFF")
        set_cell_margins(c1, top=80, bottom=80, left=100, right=100)
        set_cell_margins(c2, top=80, bottom=80, left=100, right=100)
        
        p1 = c1.paragraphs[0]
        r1 = p1.add_run(label)
        r1.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = RGBColor(71, 85, 105)
        
        p2 = c2.paragraphs[0]
        r2 = p2.add_run(val)
        r2.bold = (idx == 0)
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph().paragraph_format.space_after = Pt(20)

    create_callout_box(
        doc,
        "Executive Repository & Live Deployment Links",
        [
            "Live Interactive Web Dashboard: https://lohithaswin.github.io/play-rr-hackathon-2026/",
            "Official GitHub Repository: https://github.com/Lohithaswin/play-rr-hackathon-2026",
            "Executive PowerPoint Deck: Play_RR_Hackathon_Lohithaswin_V.pptx",
            "Local Python Studio: python dashboard_play_rr.py (Port 8050)"
        ],
        border_color="EA008A",
        bg_color="FDF2F8"
    )

    doc.add_page_break()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 1: EXECUTIVE SUMMARY & PROBLEM STATEMENT
    # ─────────────────────────────────────────────────────────────────────────
    h1 = doc.add_heading(level=1)
    r = h1.add_run("1. Executive Summary & Problem Formulation")
    r.font.color.rgb = RGBColor(15, 23, 42)
    h1.paragraph_format.space_before = Pt(12)
    h1.paragraph_format.space_after = Pt(6)

    doc.add_paragraph(
        "Traditional cricket analytics relies heavily on aggregate metrics: Batting Average, Strike Rate, Economy Rate, and Bowling Average. "
        "In modern elite franchise cricket—and specifically within the Indian Premier League (IPL)—these metrics suffer from catastrophic context blindness. "
        "A boundary struck in the 3rd over of an inconsequential group match against a low-tier opponent carries identical statistical weight to a boundary hit when needing "
        "14 runs off the final over of an IPL Eliminator. Consequently, standard leaderboards routinely elevate 'front-runners'—players who accumulate comfortable volume "
        "in low-leverage situations—while penalizing or obscuring authentic match-winners who absorb immense pressure when the game is on the line."
    )

    doc.add_paragraph(
        "The Rajasthan Royals SupeRR Selector Round 1 challenge tasks us with establishing a rigorous, reproducible, data-driven system to identify and rank the most reliable "
        "batters and bowlers under pressure across the historical 2022–2026 cycle. In response, we engineered The Halla Bol Pressure Index. Built upon 190,811 delivery records "
        "across 883 matches, the system synthesizes three core technical innovations:"
    )

    bullets = [
        ("The 3-Tier Identification Architecture: ", "Isolates true crucible situations across Big Matches (knockouts and playoffs), Must-Win attribution filters (eliminating empty runs in lost causes), and Dynamic Leverage ($LI \ge 1.50$, steep chases with $\\text{RRR} \\ge 10.0$, top-order collapse windows, and death overs)."),
        ("XGBoost Expected Par Valuation Engine: ", "Trained on 18 contextual delivery features, generating a predictive baseline of expected runs $E[\\text{Runs}]$ per delivery to measure performance against precise venue and match context par rather than arbitrary league averages."),
        ("Non-Compensatory Flaw Penalization: ", "Enforces strict accountability where fatal liabilities (such as death overs run leakage or repeated failures during top-order batting collapses) incur severe, non-compensable deductions, preventing players from masking fatal weaknesses with volume elsewhere.")
    ]
    for b_title, b_desc in bullets:
        bp = doc.add_paragraph(style='List Bullet')
        bp.paragraph_format.space_after = Pt(3)
        r_b1 = bp.add_run(b_title)
        r_b1.bold = True
        r_b1.font.color.rgb = RGBColor(30, 64, 175)
        r_b2 = bp.add_run(b_desc)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 2: PRESSURE DEFINITION & THE 3-TIER ARCHITECTURE
    # ─────────────────────────────────────────────────────────────────────────
    h2 = doc.add_heading(level=1)
    r2 = h2.add_run("2. Pressure Definition & The 3-Tier Architecture")
    r2.font.color.rgb = RGBColor(15, 23, 42)
    h2.paragraph_format.space_before = Pt(14)
    h2.paragraph_format.space_after = Pt(6)

    doc.add_paragraph(
        "What defines pressure in T20 cricket? Pressure is not a static binary label; it is a multi-dimensional state encompassing tournament stakes, "
        "match outcome incentives, scoreboard tension, and instantaneous delivery leverage. To formalize pressure without subjective heuristics, "
        "we construct a hierarchical 3-Tier Framework:"
    )

    h2_1 = doc.add_heading(level=2)
    h2_1.add_run("Tier 1: Tournament Stakes & Big-Match Multipliers")
    h2_1.paragraph_format.space_before = Pt(8)
    h2_1.paragraph_format.space_after = Pt(4)

    doc.add_paragraph(
        "Deliveries in single-elimination games carry substantially higher psychological and organizational leverage than early-season fixtures. "
        "Every delivery is mapped to competition stage metadata:"
    )
    doc.add_paragraph(
        "• Knockout / Playoff Multiplier (1.50×): Applied automatically to matches classified as Finals, Eliminators, Qualifier 1, Qualifier 2, Semi-Finals, or Super 4. Defeat in these games terminates a franchise's season.\n"
        "• Tier-1 Elite Competition Multiplier (1.25×): Applied to clashes between top-tier opponents (all 10 IPL franchises, India, Australia, England, South Africa, New Zealand, Pakistan, West Indies).\n"
        "• Associate / Minnow Discounting (0.40× Haircut): Bilateral fixtures against lower-tier associate nations (e.g., Zimbabwe, UAE, Netherlands, Oman) on sub-120 par pitches are discounted to eliminate false statistical inflation."
    )

    h2_2 = doc.add_heading(level=2)
    h2_2.add_run("Tier 2: The 'Crucible Match Win' Attribution Filter (Authentic MWPPs)")
    h2_2.paragraph_format.space_before = Pt(8)
    h2_2.paragraph_format.space_after = Pt(4)

    doc.add_paragraph(
        "To prevent empty stat-padding, our model requires an outcome mandate. A player is only credited with an Authentic Match-Winning Pressure Performance (MWPP) "
        "if four rigorous criteria are met simultaneously:"
    )
    doc.add_paragraph(
        "1. Outcome Mandate: The player's team MUST win the match (team_won == 1). Runs scored or wickets taken in lost causes or dead blowouts receive 0 match-win credit.\n"
        "2. Leverage Threshold: High-Pressure WPA $\\ge +0.50$ (or HP strike rate $\\ge 160$ with $\\ge 20$ pressure runs scored).\n"
        "3. Crisis or Finishing Mandate: The player must record either Death Chase WPA $\\ge 1.0$ or Crisis Rescue WPA $\\ge 1.5$ against elite attacks."
    )

    h2_3 = doc.add_heading(level=2)
    h2_3.add_run("Tier 3: Dynamic Ball-by-Ball Leverage Formulation")
    h2_3.paragraph_format.space_before = Pt(8)
    h2_3.paragraph_format.space_after = Pt(4)

    doc.add_paragraph(
        "At the delivery level, pressure is quantified through four mathematical gates:\n"
        "1. Instantaneous Leverage Index ($LI \\ge 1.50$): Evaluated as the derivative of Win Probability: $LI = (\\Delta WP_{wicket} - \\Delta WP_{boundary}) / \\sigma_{WP}$. Deliveries where a single boundary or wicket shifts match probability by $\\ge 1.5\\times$ standard volatility represent the top 15% game-defining moments.\n"
        "2. Scoreboard Chase Pressure ($\\text{RRR} \\ge 10.0$ RPO): Triggered in second-innings chases when the required rate escalates above 10 runs per over with $<8$ wickets in hand.\n"
        "3. Crisis Collapse Windows: Powerplay Crisis (Overs 1–6 with $\\le 2$ wickets down) and Middle Overs Collapse (Overs 7–12 with $\\ge 4$ wickets down). Distinguishes genuine innings resurrection from front-running.\n"
        "4. Death Crucible (Overs 16–20): Final four overs when the margin is under 36 runs with the result undecided."
    )

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 3: MACHINE LEARNING PAR VALUATION & ATTRIBUTION
    # ─────────────────────────────────────────────────────────────────────────
    h3 = doc.add_heading(level=1)
    r3 = h3.add_run("3. Machine Learning Expected Par Engine & Attribution")
    r3.font.color.rgb = RGBColor(15, 23, 42)
    h3.paragraph_format.space_before = Pt(14)
    h3.paragraph_format.space_after = Pt(6)

    doc.add_paragraph(
        "To establish fair player baselines, we train a gradient-boosted decision tree model (XGBoost) across 190,811 historical deliveries. "
        "The model predicts the expected run value $E[\\text{Runs}]$ of every ball given 18 contextual features: venue baseline scoring index, overs remaining, "
        "exact delivery number in the over, cumulative wickets down, required run rate, target differential, and tactical matchup archetypes (e.g., RHB vs SLA, LHB vs Off-Spin)."
    )

    doc.add_paragraph(
        "Player contribution is evaluated strictly as deviation from par:\n"
        "• Batting ML Runs Added = Runs Scored - $E[\\text{Runs}]$\n"
        "• Bowling ML Runs Saved = $E[\\text{Runs}]$ - Runs Conceded\n"
        "• High-Pressure Win Probability Added (WPA): Dynamic change in match win probability swung directly by the batter's or bowler's action on that delivery."
    )

    create_callout_box(
        doc,
        "The Principle of Non-Compensatory Flaw Penalization",
        [
            "In elite cricket, catastrophic failure in one critical dimension directly loses matches and cannot be offset by cheap accumulation elsewhere.",
            "1. Death Overs Run Leakage: Bowlers leaking runs above par in overs 16–20 trigger an explicit penalty: |Runs Leaked| * 0.80.",
            "2. Negative Crisis Rescue WPA: Batters who repeatedly fail during top-order collapses trigger an explicit penalty: |Rescue WPA| * 7.50.",
            "3. Negative Death Chase Execution: Dismissals during final overs chases trigger an explicit penalty: |Death WPA| * 3.00."
        ],
        border_color="F43F5E",
        bg_color="FFF1F2"
    )

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 4: BATTING MODEL & THE SPECIALIST STANDARD
    # ─────────────────────────────────────────────────────────────────────────
    h4 = doc.add_heading(level=1)
    r4 = h4.add_run("4. Batting Model & The Specialist Batting Standard")
    r4.font.color.rgb = RGBColor(15, 23, 42)
    h4.paragraph_format.space_before = Pt(14)
    h4.paragraph_format.space_after = Pt(6)

    doc.add_paragraph(
        "The Batting Clutch Score (0–100 scale) weights match-winning execution when the game is on the line:\n"
        "• Counter-Attack Chasing RRR $\\ge 10.0$ (24%): Win Probability Added when chasing steep targets under escalating scoreboard pressure.\n"
        "• Crisis Collapse Rescue (20%): WPA resurrecting innings after top-order collapses (Powerplay $\\le 2$ down).\n"
        "• Quality Win Impact vs Elite Attacks (20%): High-pressure WPA generated exclusively in team victories against Tier-1 bowling.\n"
        "• Authentic MWPPs (14%): Frequency of match-winning pressure performances that seal decisive wins.\n"
        "• Death Chase Finishing (12%): Execution in overs 16–20 under tight margins (<36 runs).\n"
        "• Pressure Consistency Rate (10%): Proportion of pressure appearances maintaining net-positive match contribution."
    )

    doc.add_paragraph(
        "The Specialist Batting Standard ($\\ge 750$ Career Balls):\n"
        "A critical flaw of naive rating systems is the inclusion of lower-order tailenders or brief cameo specialists whose tiny sample sizes create extreme outlier spikes. "
        "We mandate a substantive volume threshold of $\\ge 750$ career balls faced in the historical cycle. This standard correctly achieves three goals:\n"
        "1. Excludes Bowlers from Batting Ranks: Rashid Khan (506 balls faced) bats at #8; evaluating him as a batter creates volatility distortion. He is correctly ranked in his primary archetype (#7 bowler globally).\n"
        "2. Filters Low-Impact Cameos: Cameron Green managed only +11.8 Counter-Attack WPA, lacking decisive match impact despite general strike rate.\n"
        "3. Filters Brief Cameo Specialists: Dinesh Karthik (637 balls, 0.0 Death-Alive WPA) and MS Dhoni (460 balls) fail the $\\ge 750$ balls threshold, guaranteeing that Top 10 batters bear genuine full-innings responsibility."
    )

    doc.add_page_break()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 5: OFFICIAL TOP 10 RANKINGS & DETAILED EVIDENCE
    # ─────────────────────────────────────────────────────────────────────────
    h5 = doc.add_heading(level=1)
    r5 = h5.add_run("5. Official Player Rankings & Empirical Evidence")
    r5.font.color.rgb = RGBColor(15, 23, 42)
    h5.paragraph_format.space_before = Pt(12)
    h5.paragraph_format.space_after = Pt(6)

    h5_1 = doc.add_heading(level=2)
    h5_1.add_run("5.1 Official Top 10 Batters Under Pressure")
    h5_1.paragraph_format.space_before = Pt(6)
    h5_1.paragraph_format.space_after = Pt(4)

    # Batters Table
    bat_tbl = doc.add_table(rows=11, cols=10)
    bat_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    bat_tbl.autofit = False
    
    bat_col_w = [Inches(0.6), Inches(1.5), Inches(0.6), Inches(0.5), Inches(0.5), Inches(0.7), Inches(0.7), Inches(0.7), Inches(0.6), Inches(0.7)]
    for idx, w in enumerate(bat_col_w):
        bat_tbl.columns[idx].width = w

    bat_headers = ["Rank", "Player", "Balls", "MWPP", "Wins", "CA WPA", "Rescue", "Death", "Consist", "Score"]
    for idx, h in enumerate(bat_headers):
        cell = bat_tbl.cell(0, idx)
        set_cell_background(cell, "0F172A")
        set_cell_margins(cell, top=80, bottom=80, left=60, right=60)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.bold = True
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(234, 0, 138)

    bat_rows = [
        ("#1", "David Miller", "1276", "8", "15", "+42.27", "+14.28", "+17.65", "67.6%", "80.2"),
        ("#2", "Suryakumar Yadav", "2716", "8", "20", "+29.37", "+20.12", "+1.72", "70.5%", "74.0"),
        ("#3", "Namboori Tilak Varma", "2488", "7", "14", "+23.53", "+21.46", "+7.65", "57.7%", "63.7"),
        ("#4", "Heinrich Klaasen", "1410", "4", "12", "+31.61", "+24.84", "-1.02", "69.2%", "61.6"),
        ("#5", "Glenn Phillips", "1045", "4", "12", "+23.85", "+18.48", "+13.26", "69.0%", "60.6"),
        ("#6", "Shimron Hetmyer", "1240", "5", "13", "+21.95", "+16.96", "+10.20", "58.3%", "59.0"),
        ("#7", "Hardik Pandya", "1902", "3", "18", "+31.86", "+6.47", "+8.63", "67.3%", "55.7"),
        ("#8", "Virat Kohli", "2455", "6", "10", "+35.50", "+1.27", "0.00", "69.1%", "47.5"),
        ("#9", "Nicholas Pooran", "1938", "5", "11", "+25.49", "+6.29", "+1.91", "74.5%", "46.2"),
        ("#10", "Venkatesh Iyer", "942", "7", "7", "+23.56", "+3.71", "+0.48", "66.7%", "45.4")
    ]

    for row_idx, data in enumerate(bat_rows):
        bg = "FEF9C3" if row_idx == 0 else ("F8FAFC" if row_idx % 2 == 1 else "FFFFFF")
        for col_idx, val in enumerate(data):
            cell = bat_tbl.cell(row_idx + 1, col_idx)
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=60, bottom=60, left=60, right=60)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if col_idx != 1 else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(val)
            r.font.size = Pt(8.5)
            r.bold = (col_idx in [0, 1, 9] or row_idx == 0)
            if row_idx == 0 and col_idx == 9:
                r.font.color.rgb = RGBColor(180, 83, 9)

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # Detailed Batters Narrative
    doc.add_paragraph("Comprehensive Tactical Justification for Top 10 Batters:")
    bat_dossiers = [
        ("1. David Miller (80.2 pts) — The World #1 Chase Finisher", 
         "Leads world cricket in Counter-Attack WPA (+42.27) in steep chases (RRR >= 10.0) and Death WPA (+17.65). Converted 15 steep chases into victories with 8 Authentic MWPPs and zero flaw deductions. Signature match: vs CSK (IPL Qualifier: 68* off 38b, WPA +3.45) and vs India (T20I: 106* off 47b, WPA +4.10)."),
        ("2. Suryakumar Yadav (74.0 pts) — World #2 All-Phase Force", 
         "Generated the highest contextual runs above par globally (+234.4 ML Runs Added) against 98.8% elite attacks. Combines +29.37 CA WPA with +20.12 Crisis Rescue WPA, piloting 20 high-pressure team victories with 70.5% consistency. Signature match: vs RCB (83 off 35b, WPA +3.82) and vs England (117 off 55b from 31/3 collapse, WPA +4.21)."),
        ("3. Namboori Tilak Varma (63.7 pts) — Top-Order Collapse Savior", 
         "Recorded +21.46 Crisis Rescue WPA (2nd globally) and +23.53 CA WPA, repeatedly rescuing Mumbai Indians from early collapses with 7 Authentic MWPPs and 14 crucible victories. Signature match: vs CSK (51* off 43b from 33/4, WPA +2.95)."),
        ("4. Heinrich Klaasen (61.6 pts) — World #1 Crisis Rescue Crusher", 
         "World leader in Crisis Rescue WPA (+24.84) and +31.61 CA WPA. Obliterates middle-overs spin under escalating required rates across 12 crucible wins (incurs a -3.0 pt penalty for late-innings dismissals). Signature match: vs KKR (63 off 29b from 111/5, WPA +3.40)."),
        ("5. Glenn Phillips (60.6 pts) — Complete Multi-Situation Operator", 
         "One of only three batters with positive double-digit WPA across all three pressure dimensions: +18.48 Crisis Rescue, +13.26 Death Finishing, and +23.85 CA WPA with 69.0% consistency and zero deductions. Signature match: vs RR (25 off 7b sealing final over chase, WPA +3.90)."),
        ("6. Shimron Hetmyer (59.0 pts) — Rajasthan Royals Death Closer", 
         "Royals' elite pressure weapon. Accumulated +21.95 CA WPA, +16.96 Crisis Rescue WPA, and +10.20 Death WPA, sealing 13 crucible victories with 5 Authentic MWPPs. Signature match: vs GT (56* off 26b chasing 178 from 55/4, WPA +3.92)."),
        ("7. Hardik Pandya (55.7 pts) — Championship Big-Stage Champion", 
         "Elevated by a 1.50x knockout multiplier across IPL playoffs and ICC knockouts (+31.86 CA WPA, 18 high-pressure team victories). Signature match: vs RR (IPL 2022 Final: 34 off 30b & 3/17, WPA +4.20) and T20 World Cup Final 2024."),
        ("8. Virat Kohli (47.5 pts) — The Master of Chases", 
         "Highest sample volume against elite bowling (2,455 balls), generating +35.50 Counter-Attack WPA and 6 Authentic MWPPs pacing complex second-innings chases. Modest early collapse rescue (+1.27 WPA) places him at #8. Signature match: vs Pakistan (Melbourne: 82* off 53b from 31/4, WPA +5.12)."),
        ("9. Nicholas Pooran (46.2 pts) — High-Leverage Consistency King", 
         "World #1 consistency rate (74.5%), contributing positive net impact in 3 out of every 4 pressure innings with +25.49 CA WPA, 5 Authentic MWPPs, and zero flaw deductions. Signature match: vs RCB (62 off 19b chasing 213, WPA +4.30)."),
        ("10. Venkatesh Iyer (45.4 pts) — Clutch Match-Winner", 
         "Delivered 7 Authentic MWPPs in high-stakes knockout games, +23.56 Counter-Attack WPA, and a 66.7% consistency rate. Signature match: vs SRH (IPL 2024 Final: 52* off 26b, WPA +3.20).")
    ]
    for b_title, b_body in bat_dossiers:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        r1 = p.add_run(b_title + "\n")
        r1.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = RGBColor(15, 23, 42)
        r2 = p.add_run(b_body)
        r2.font.size = Pt(9.0)
        r2.font.color.rgb = RGBColor(71, 85, 105)

    doc.add_page_break()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 5.2: OFFICIAL TOP 10 BOWLERS
    # ─────────────────────────────────────────────────────────────────────────
    h5_2 = doc.add_heading(level=2)
    h5_2.add_run("5.2 Official Top 10 Bowlers Under Pressure")
    h5_2.paragraph_format.space_before = Pt(6)
    h5_2.paragraph_format.space_after = Pt(4)

    # Bowlers Table
    bowl_tbl = doc.add_table(rows=11, cols=10)
    bowl_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    bowl_tbl.autofit = False
    
    bowl_col_w = [Inches(0.6), Inches(1.5), Inches(0.6), Inches(0.5), Inches(0.7), Inches(0.7), Inches(0.7), Inches(0.6), Inches(0.6), Inches(0.7)]
    for idx, w in enumerate(bowl_col_w):
        bowl_tbl.columns[idx].width = w

    bowl_headers = ["Rank", "Bowler", "Craft", "Matches", "PP Saved", "Mid Saved", "Death Saved", "Minnow %", "Deduct", "Score"]
    for idx, h in enumerate(bowl_headers):
        cell = bowl_tbl.cell(0, idx)
        set_cell_background(cell, "0F172A")
        set_cell_margins(cell, top=80, bottom=80, left=60, right=60)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.bold = True
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(56, 189, 248) # Light Blue

    bowl_rows = [
        ("#1", "Jasprit Bumrah", "PACE", "75", "+18.0", "+74.5", "+149.8", "3.9%", "0.00", "78.5"),
        ("#2", "Sunil Narine", "SPIN", "66", "+20.2", "+80.2", "+23.6", "0.0%", "0.00", "52.4"),
        ("#3", "Josh Hazlewood", "PACE", "63", "+48.4", "-3.8", "+9.1", "0.0%", "-3.03", "52.1"),
        ("#4", "Mustafizur Rahman", "PACE", "70", "+21.9", "+18.3", "+84.8", "20.7%", "0.00", "45.3"),
        ("#5", "Nathan Ellis", "PACE", "41", "+9.4", "+32.6", "+41.5", "0.0%", "0.00", "44.0"),
        ("#6", "Bhuvneshwar Kumar", "PACE", "100", "+16.4", "-3.0", "+41.2", "2.7%", "-2.43", "43.0"),
        ("#7", "Rashid Khan", "SPIN", "122", "+20.2", "+19.5", "+10.7", "16.6%", "0.00", "39.7"),
        ("#8", "Axar Patel", "SPIN", "135", "+7.4", "-1.2", "+2.9", "3.8%", "-0.97", "38.8"),
        ("#9", "Varun Chakravarthy", "SPIN", "94", "+36.7", "+25.7", "-9.6", "0.6%", "-7.69", "38.6"),
        ("#10", "Maheesh Theekshana", "SPIN", "98", "+41.9", "+2.8", "+39.6", "8.3%", "0.00", "38.3")
    ]

    for row_idx, data in enumerate(bowl_rows):
        bg = "E0F2FE" if row_idx == 0 else ("F8FAFC" if row_idx % 2 == 1 else "FFFFFF")
        for col_idx, val in enumerate(data):
            cell = bowl_tbl.cell(row_idx + 1, col_idx)
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=60, bottom=60, left=60, right=60)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if col_idx not in [1, 2] else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(val)
            r.font.size = Pt(8.5)
            r.bold = (col_idx in [0, 1, 9] or row_idx == 0)
            if row_idx == 0 and col_idx == 9:
                r.font.color.rgb = RGBColor(2, 132, 199)

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # Detailed Bowlers Narrative
    doc.add_paragraph("Comprehensive Tactical Justification for Top 10 Bowlers:")
    bowl_dossiers = [
        ("1. Jasprit Bumrah (78.5 pts) — Undisputed King of Pace & Clutch Defense", 
         "Prevented an astronomical +149.76 runs above expected at the death (overs 16–20) alone, +74.54 middle runs, and +17.98 PP runs. Facing 100% Tier-1 elite opposition with an economy rate of 7.36 in maximum-pressure situations and zero flaw deductions. Signature match: vs SA (T20 World Cup Final 2024: 2/18, 18th over conceded 2 runs, WPA +4.50) and vs RCB (5/21, WPA +4.10)."),
        ("2. Sunil Narine (52.4 pts) — Undisputed King of Spin & All-Phase Suppression", 
         "Net-positive runs saved across all 3 phases (+20.2 PP, +80.2 Mid, +23.6 Death). Narine bowls the 18th or 19th over with ice in his veins against 100% Tier-1 opposition with 0 flaw deductions. Signature match: vs SRH (IPL 2024 Final: 1/16 in 4 overs, WPA +2.90) and vs CSK (2/15 at Chepauk)."),
        ("3. Josh Hazlewood (52.1 pts) — Powerplay Stranglehold Master", 
         "Saved a world-leading +48.43 runs in the Powerplay alone with a 65.1% consistency rate and +9.1 death runs saved against elite opposition. Signature match: vs LSG (4/25 defending 181, WPA +3.60)."),
        ("4. Mustafizur Rahman (45.3 pts) — Death Cutter Specialist (Calibrated)", 
         "Delivered +84.80 death runs saved and +21.93 in the Powerplay. Accurately discounted at 0.40x for 20.7% bilateral minnow exposure, ranking cleanly at #4. Signature match: vs RCB (4/29 in Chepauk opener, WPA +3.40)."),
        ("5. Nathan Ellis (44.0 pts) — Modern Multi-Phase T20 Specialist", 
         "Saved +41.45 death runs and +32.56 middle overs runs against 100% Tier-1 franchise opposition with 64.0% consistency and zero deductions. Signature match: vs RR (4/30 defending 197 at Barsapara, WPA +3.85)."),
        ("6. Bhuvneshwar Kumar (43.0 pts) — 100-Match Veteran Master", 
         "Demonstrated immense longevity over an immense 100-match sample size, saving +41.23 death runs and +16.45 PP runs with a 60.3% consistency rate. Signature match: vs RR (IPL 2024: 3/41 defending 2 runs off final ball, trapped Powell LBW, WPA +4.80)."),
        ("7. Rashid Khan (39.7 pts) — Middle-Overs Spin Anchor", 
         "Evaluated in his true primary archetype. Consistent run suppression across all phases (+20.2 PP, +19.5 Mid, +10.7 Death) over 122 matches. Signature match: vs AUS (T20 World Cup 2024: 1/23 historic win, WPA +3.10)."),
        ("8. Axar Patel (38.8 pts) — Tactical Pressure Economy Specialist", 
         "Maintained a world-class pressure economy rate of 8.33 RPO across 135 matches bowling difficult matchups against aggressive right-handers (+7.36 PP runs, +2.88 death runs). Signature match: vs England (T20 World Cup Semi-Final: 3/23 spin masterclass, WPA +4.20)."),
        ("9. Varun Chakravarthy (38.6 pts) — Mystery Spinner with Calibrated Death Penalty", 
         "Elite in the Powerplay (+36.66) and Middle (+25.74). However, leaked -9.61 runs above expected at the death, taking an explicit -7.69 pt non-negotiable flaw deduction, correctly situating him behind Narine. Signature match: vs SA (5/17 T20I at Gqeberha, WPA +4.10)."),
        ("10. Maheesh Theekshana (38.3 pts) — Carrom-Ball Powerplay Specialist", 
         "Saved +41.88 runs in the first six overs and +39.65 at the death over 98 matches, calibrated with associate discounting for bilateral matches. Signature match: vs RCB (3/27 in Powerplay choke, WPA +3.10).")
    ]
    for b_title, b_body in bowl_dossiers:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        r1 = p.add_run(b_title + "\n")
        r1.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = RGBColor(15, 23, 42)
        r2 = p.add_run(b_body)
        r2.font.size = Pt(9.0)
        r2.font.color.rgb = RGBColor(71, 85, 105)

    doc.add_page_break()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 6: CORE ANALYTICAL CASE STUDIES
    # ─────────────────────────────────────────────────────────────────────────
    h6 = doc.add_heading(level=1)
    r6 = h6.add_run("6. Core Analytical Case Studies & Debates")
    r6.font.color.rgb = RGBColor(15, 23, 42)
    h6.paragraph_format.space_before = Pt(12)
    h6.paragraph_format.space_after = Pt(6)

    cases = [
        ("Case 1: Sunil Narine (#2) Decisively Outperforms Varun Chakravarthy (#9)",
         "While both are world-class mystery spinners, their pressure execution diverges drastically at the death overs. Narine is net-positive across all three phases (+20.2 PP, +80.2 Mid, +23.6 Death) with a 7.88 economy and 0 flaw deductions against 100% elite competition. In contrast, Varun leaked -9.61 runs above expected at the death, incurring an explicit -7.69 pt non-compensatory deduction. Narine beats Varun decisively by 13.8 rating points."),
        ("Case 2: Schedule Strength Calibration — Mustafizur Calibrated from #2 to #4",
         "In unweighted models, Mustafizur Rahman appeared as the #2 bowler due to raw wicket tallies. However, our schedule calibration revealed that 20.7% of his delivery volume (324 balls) occurred against associate minnows in low-scoring Dhaka bilaterals. Applying a 0.40x associate haircut appropriately adjusts his numbers, preserving the integrity of the podium for Bumrah, Narine, and Hazlewood."),
        ("Case 3: Match-on-the-Line Priority — Pooran (#9) & Kohli (#8) Surpass Gill (#11)",
         "Nicholas Pooran maintains world-leading consistency (74.5%) and +25.49 Counter-Attack WPA. Virat Kohli generates +35.50 CA WPA over 2,455 balls against elite attacks. In contrast, Shubman Gill has a negative crisis rescue metric (-2.03 WPA), repeatedly falling cheaply during early collapse states. Incurring a mandatory -15.3 pt flaw penalty, Gill is demoted to #11, proving that the index values crisis stabilization over comfortable front-running."),
        ("Case 4: Specialist Batting Volume Standard (>= 750 Balls)",
         "Prevents lower-order cameo specialists (Dinesh Karthik 637 balls, 0.0 Death-Alive WPA; MS Dhoni 460 balls) and primary bowlers (Rashid Khan 506 balls) from distorting specialist batting rankings. Ensures that Top 10 batters bear genuine full-innings responsibility."),
        ("Case 5: High-Risk Death Phase Liabilities — Siraj (#19) and Bishnoi (#51) Demoted",
         "Mohammed Siraj leaked -20.99 runs above expected at the death at an 8.98 RPO (-16.8 pt deduction). Ravi Bishnoi leaked -41.78 runs at the death at 10.42 RPO (-33.4 pt deduction). Death overs defense is non-negotiable; solid middle-overs bowling cannot compensate for fatal death-phase vulnerability.")
    ]
    for c_title, c_desc in cases:
        create_callout_box(doc, c_title, [c_desc], border_color="1E40AF", bg_color="F8FAFC")

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 7: VISUAL EMPIRICAL EVIDENCE (IMAGE EMBEDDING)
    # ─────────────────────────────────────────────────────────────────────────
    h7 = doc.add_heading(level=1)
    r7 = h7.add_run("7. Visual Empirical Evidence & Dashboard Proofs")
    r7.font.color.rgb = RGBColor(15, 23, 42)
    h7.paragraph_format.space_before = Pt(12)
    h7.paragraph_format.space_after = Pt(6)

    doc.add_paragraph(
        "The findings of The Halla Bol Pressure Index are verified through empirical visualizations deployed within our production analytics studio. "
        "Below are the primary visual proofs confirming player distribution, phase defense, and schedule calibration:"
    )

    # Embed Scatter Plot if file exists
    if os.path.exists("assets/visual_proofs_scatter.png"):
        doc.add_paragraph().paragraph_format.space_after = Pt(4)
        doc.add_picture("assets/visual_proofs_scatter.png", width=Inches(6.2))
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_cap = p_cap.add_run("Figure 1: Batting Pressure Archetypes — Crisis Rescue WPA vs High-Pressure ML Runs Added (Quadrant Mapping)")
        r_cap.font.size = Pt(8.5)
        r_cap.italic = True
        r_cap.font.color.rgb = RGBColor(100, 116, 139)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # Embed Schedule & Phases if file exists
    if os.path.exists("assets/schedule_calibration.png"):
        doc.add_picture("assets/schedule_calibration.png", width=Inches(6.2))
        p_cap2 = doc.add_paragraph()
        p_cap2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_cap2 = p_cap2.add_run("Figure 2: Schedule Strength Calibration & Multi-Phase Runs Saved Matrix")
        r_cap2.font.size = Pt(8.5)
        r_cap2.italic = True
        r_cap2.font.color.rgb = RGBColor(100, 116, 139)

    doc.add_page_break()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 8: MODEL RELIABILITY & LIMITATIONS
    # ─────────────────────────────────────────────────────────────────────────
    h8 = doc.add_heading(level=1)
    r8 = h8.add_run("8. Model Reliability, Consistency & Limitations")
    r8.font.color.rgb = RGBColor(15, 23, 42)
    h8.paragraph_format.space_before = Pt(12)
    h8.paragraph_format.space_after = Pt(6)

    doc.add_paragraph(
        "8.1 Sample Size Reliability Scaling:\n"
        "To prevent single-match flukes from dominating the leaderboard, raw clutch scores are weighted by a square-root reliability curve: "
        "Reliability = min(1.0, sqrt(Matches / 45)). A player with only 10 pressure matches is discounted to 0.47x of their score, "
        "whereas veterans with >= 45 matches receive full 1.00x weight. This guarantees that Top 10 players have proven repeatable excellence over multi-season horizons."
    )

    doc.add_paragraph(
        "8.2 Pressure Consistency Metric:\n"
        "Rather than relying on volatile cumulative sums, we compute the Pressure Consistency Rate: the proportion of high-pressure match appearances where "
        "the player contributed net-positive match WPA. Batters such as Nicholas Pooran (74.5%) and Suryakumar Yadav (70.5%) demonstrate extraordinary reliability across diverse conditions."
    )

    doc.add_paragraph(
        "8.3 Known Model Boundaries & Limitations:\n"
        "1. Fielding Impact: Catches, direct-hit runouts, and boundary saves are not currently integrated into delivery-level WPA calculations.\n"
        "2. Pitch Weather Extremes: Rain-curtailed games or sudden pitch deterioration rely on venue-level ML baselines rather than ball-by-ball soil sensor telemetry.\n"
        "3. Batter Non-Striker Running: Non-striker running speed and pressure calls are currently omitted from the individual batter metric."
    )

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 9: FORMAL METHODOLOGY, PRESSURE DEFINITIONS & RANKING JUSTIFICATION
    # ─────────────────────────────────────────────────────────────────────────
    h9 = doc.add_heading(level=1)
    r9 = h9.add_run("9. Formal Methodology, Pressure Definitions & Ranking Justification")
    r9.font.color.rgb = RGBColor(15, 23, 42)
    h9.paragraph_format.space_before = Pt(12)
    h9.paragraph_format.space_after = Pt(6)

    doc.add_paragraph(
        "9.1 Operational Definitions of Match Pressure Situations:\n"
        "To satisfy the core hackathon mandate with mathematical precision, pressure is not treated as a subjective impression but as an empirical confluence of four measurable dimensions:\n"
        "• Scoreboard Chase Crucible: Triggered during second-innings run chases when the Required Run Rate (RRR) exceeds 10.0 runs per over with 7 or fewer wickets in hand. This captures high-stress target pursuit where single-ball execution directly moves win probability.\n"
        "• Early Top-Order Collapses (Crisis Windows): Operationalized as innings states where the batting team loses 2 or more wickets inside the Powerplay (Overs 1–6), or 4 or more wickets before the 12th over. Rescuing an innings from these thresholds without stalling scoring rate constitutes authentic collapse resiliency.\n"
        "• Crucible Death Overs: Overs 16–20 where the victory margin is 36 or fewer runs. In this phase, bowler runs conceded above par or batter dismissals produce maximal win-probability volatility.\n"
        "• Dynamic Leverage Index (LI >= 1.50): Calculated on every delivery from historical win probability gradients, isolating the top 15% game-volatility deliveries across all tournament fixtures."
    )

    doc.add_paragraph(
        "9.2 Mathematical Methodology & Par Valuation:\n"
        "• XGBoost Context-Aware Par Model: Trained across 190,811 deliveries using 18 context features (ground baseline par, balls remaining, wickets in hand, RRR, batter vs bowler matchups, pitch deviation). This predicts delivery-level expected runs conceded, establishing an objective benchmark.\n"
        "• Performance Above Par: Quantified as ML Runs Added (Batting) = Actual Runs - Expected Runs; ML Runs Saved (Bowling) = Expected Runs - Actual Runs Conceded.\n"
        "• Non-Compensatory Flaw Accountability: Fatal vulnerabilities in pressure situations incur mandatory deductions that cannot be offset by non-leverage accumulation. Batters failing in collapses incur a -7.5x penalty on negative rescue WPA; bowlers leaking runs above par at the death take a -0.80x penalty on runs leaked."
    )

    doc.add_paragraph(
        "9.3 Empirical Justification of Final Rankings:\n"
        "• Batting Hierarchy Justification: David Miller earns World #1 (80.2 pts) because he leads global cricket in Counter-Attack WPA (+42.27), Death WPA (+17.65), and has 8 Authentic MWPPs with zero flaw deductions. Suryakumar Yadav earns World #2 (74.0 pts) by leading the world in high-pressure team victories (20 wins) and contextual volume (+234.4 ML Runs Added). Shubman Gill (#11, 43.4 pts) is demoted out of the Top 10 due to failing in early collapses (-2.03 Crisis Rescue WPA, triggering a -15.3 pt deduction).\n"
        "• Bowling Hierarchy Justification: Jasprit Bumrah (#1, 78.5 pts) is the undisputed apex bowler, saving an unprecedented +149.8 runs above expectation at the death with an elite 7.36 pressure economy and zero deductions. Sunil Narine (#2, 52.4 pts) secures the spin crown by saving runs in all three phases (+20.2 PP, +80.2 Mid, +23.6 Death) against 100% elite competition, outranking Varun Chakravarthy (#9, 38.6 pts) who suffered a -7.69 pt penalty for death-overs leakage (-9.61 runs)."
    )

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 10: SHARE YOUR JOURNEY (OPTIONAL REQUIREMENT)
    # ─────────────────────────────────────────────────────────────────────────
    h10 = doc.add_heading(level=1)
    r10 = h10.add_run("10. The Journey Behind the Solution")
    r10.font.color.rgb = RGBColor(15, 23, 42)
    h10.paragraph_format.space_before = Pt(12)
    h10.paragraph_format.space_after = Pt(6)

    doc.add_paragraph(
        "As a data scientist passionate about cricket decision sciences, the SupeRR Selector challenge provided the ultimate playground to solve one of the sport's greatest paradoxes: "
        "why do classical statistics routinely deceive coaching staffs? When Rajasthan Royals management prepares for high-stakes IPL fixtures, conventional averages fail to answer: "
        "who will keep their composure when 48 runs are needed off 18 balls?"
    )

    doc.add_paragraph(
        "The conceptual breakthrough occurred during delivery-level analysis of the 2022–2026 dataset: seeing how raw strike rate rewards comfortable front-running. "
        "Witnessing how Shubman Gill generated high raw runs but repeatedly collapsed under early wickets (negative crisis rescue), while David Miller turned steep, impossible chases into victories, "
        "crystallized the necessity of non-compensatory flaw penalties. Engineering this system—training the XGBoost contextual model, developing the 3-Tier architecture, and deploying the interactive studio—"
        "has been an exhilarating journey. We are proud to deliver this production-ready decision intelligence framework to the Rajasthan Royals. Halla Bol!"
    )

    # Save Document
    doc_path = "d:/rr/Play_RR_Hackathon_Methodology_Report_Lohithaswin_V.docx"
    doc.save(doc_path)
    print(f"Successfully generated Word Document at: {doc_path}")

    # Convert to PDF
    pdf_path = "d:/rr/Play_RR_Hackathon_Methodology_Report_Lohithaswin_V.pdf"
    try:
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        wdoc = word.Documents.Open(os.path.abspath(doc_path))
        wdoc.SaveAs(os.path.abspath(pdf_path), FileFormat=17) # 17 = wdFormatPDF
        wdoc.Close()
        word.Quit()
        print(f"Successfully converted Word Document to PDF at: {pdf_path}")
    except Exception as e:
        print("Word PDF conversion error:", e)

if __name__ == '__main__':
    build_methodology_document()
