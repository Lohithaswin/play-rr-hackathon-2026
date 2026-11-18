import sys
import os
import pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
import win32com.client

def build_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Theme Colors
    BG_DARK   = RGBColor(7, 10, 19)       # #070a13
    CARD_BG   = RGBColor(15, 23, 42)      # #0f172a
    CARD_BORDER = RGBColor(30, 41, 59)    # #1e293b
    RR_PINK   = RGBColor(234, 0, 138)     # #ea008a
    RR_BLUE   = RGBColor(30, 64, 175)     # #1e40af
    RR_GOLD   = RGBColor(245, 197, 24)    # #f5c518
    WHITE     = RGBColor(255, 255, 255)
    SUBTEXT   = RGBColor(148, 163, 184)   # #94a3b8
    GREEN     = RGBColor(16, 185, 129)    # #10b981
    RED       = RGBColor(244, 63, 94)     # #f43f5e
    LIGHT_BLUE= RGBColor(96, 165, 250)    # #60a5fa

    def add_blank_slide():
        slide = prs.slides.add_slide(blank_layout)
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_DARK
        bg.line.fill.background()
        return slide

    def add_header(slide, tag, title, subtitle):
        header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.733), Inches(1.1))
        tf = header_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p_tag = tf.paragraphs[0]
        p_tag.text = tag.upper()
        p_tag.font.size = Pt(10)
        p_tag.font.bold = True
        p_tag.font.color.rgb = RR_PINK

        p_title = tf.add_paragraph()
        p_title.text = title
        p_title.font.size = Pt(21)
        p_title.font.bold = True
        p_title.font.color.rgb = WHITE
        p_title.space_after = Pt(2)

        p_sub = tf.add_paragraph()
        p_sub.text = subtitle
        p_sub.font.size = Pt(10.5)
        p_sub.font.color.rgb = SUBTEXT

    def add_card(slide, left, top, width, height, title, body_lines, accent=RR_PINK):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        shape.fill.solid()
        shape.fill.fore_color.rgb = CARD_BG
        shape.line.color.rgb = CARD_BORDER
        shape.line.width = Pt(1)

        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(0.06))
        line.fill.solid()
        line.fill.fore_color.rgb = accent
        line.line.fill.background()

        tb = slide.shapes.add_textbox(Inches(left + 0.25), Inches(top + 0.15), Inches(width - 0.5), Inches(height - 0.3))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p_t = tf.paragraphs[0]
        p_t.text = title.upper()
        p_t.font.size = Pt(10.5)
        p_t.font.bold = True
        p_t.font.color.rgb = accent
        p_t.space_after = Pt(5)

        for line_item in body_lines:
            p = tf.add_paragraph()
            p.text = line_item
            p.font.size = Pt(9.5)
            p.font.color.rgb = SUBTEXT
            p.space_after = Pt(3.5)

    # ─────────────────────────────────────────────────────────────────────────
    # SLIDE 1: TITLE SLIDE
    # ─────────────────────────────────────────────────────────────────────────
    s1 = add_blank_slide()
    pill = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.1), Inches(3.4), Inches(0.35))
    pill.fill.solid()
    pill.fill.fore_color.rgb = RR_PINK
    pill.line.fill.background()
    p = pill.text_frame.paragraphs[0]
    p.text = "RAJASTHAN ROYALS ANALYTICS"
    p.alignment = PP_ALIGN.CENTER
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = WHITE

    tb_title = s1.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(11.733), Inches(2.2))
    tf1 = tb_title.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    p1.text = "SupeRR Selector: The Halla Bol Pressure Index"
    p1.font.size = Pt(36)
    p1.font.bold = True
    p1.font.color.rgb = WHITE
    p1.space_after = Pt(8)

    p2 = tf1.add_paragraph()
    p2.text = "Context-Aware Multi-Phase Leverage & Win Probability Engine | IPL & T20I (2022–2026)"
    p2.font.size = Pt(16)
    p2.font.color.rgb = RR_GOLD

    auth_card = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(4.3), Inches(11.733), Inches(2.3))
    auth_card.fill.solid()
    auth_card.fill.fore_color.rgb = CARD_BG
    auth_card.line.color.rgb = CARD_BORDER
    auth_card.line.width = Pt(1)

    top_line = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(4.3), Inches(11.733), Inches(0.08))
    top_line.fill.solid()
    top_line.fill.fore_color.rgb = RR_PINK
    top_line.line.fill.background()

    tb_auth = s1.shapes.add_textbox(Inches(1.2), Inches(4.55), Inches(11.0), Inches(1.8))
    tf_auth = tb_auth.text_frame
    tf_auth.word_wrap = True

    pa1 = tf_auth.paragraphs[0]
    pa1.text = "OFFICIAL HACKATHON SUBMISSION  •  PLAY RR SEASON 2 (2026)"
    pa1.font.size = Pt(10.5)
    pa1.font.bold = True
    pa1.font.color.rgb = RR_PINK
    pa1.space_after = Pt(4)

    pa2 = tf_auth.add_paragraph()
    pa2.text = "SUBMITTED BY:  LOHITHASWIN V"
    pa2.font.size = Pt(18)
    pa2.font.bold = True
    pa2.font.color.rgb = WHITE
    pa2.space_after = Pt(4)

    pa3 = tf_auth.add_paragraph()
    pa3.text = "TARGET: Rajasthan Royals Decision Sciences Group  •  SCOPE: 883 Matches | 190,811 Deliveries"
    pa3.font.size = Pt(11)
    pa3.font.color.rgb = SUBTEXT
    pa3.space_after = Pt(4)

    pa4 = tf_auth.add_paragraph()
    pa4.text = "LIVE WEB APP: https://lohithaswin.github.io/play-rr-hackathon-2026/  •  GITHUB: Lohithaswin/play-rr-hackathon-2026"
    pa4.font.size = Pt(10.5)
    pa4.font.bold = True
    pa4.font.color.rgb = RR_GOLD

    # ─────────────────────────────────────────────────────────────────────────
    # SLIDE 2: THE CONTEXT BLINDNESS OF TRADITIONAL METRICS
    # ─────────────────────────────────────────────────────────────────────────
    s2 = add_blank_slide()
    add_header(s2, "Problem Statement & Strategic Imperative", "The Context Blindness of Traditional Cricket Metrics", "Why conventional batting averages, strike rates, and economy rates fail modern IPL franchise decision-making.")

    add_card(s2, 0.8, 1.8, 3.6, 5.0, "1. Flat State Assumption", [
        "Traditional metrics assign identical value to every ball regardless of game state.",
        "A boundary scored in Over 3 of a dead-rubber against a minnow nation is treated the same as 14 runs needed off the final over of an IPL Eliminator.",
        "Front-running batters inflate raw volume against weak bowling in non-decisive situations, masking true pressure fragility."
    ], RR_PINK)

    add_card(s2, 4.86, 1.8, 3.6, 5.0, "2. Empty Run Accumulation", [
        "Uncalibrated strike rates reward cameos accumulated when the match outcome is already decided.",
        "Batters who score 40 runs at 160 SR in lost causes or runaway blowouts receive unearned statistical credit.",
        "Top-order anchors who fail to stabilize the team during early top-order collapses cannot be redeemed by comfortable front-running runs."
    ], RR_GOLD)

    add_card(s2, 8.93, 1.8, 3.6, 5.0, "3. The Halla Bol Solution", [
        "3-Tier Identification Architecture isolating Big Matches, Must-Wins, and Dynamic Leverage.",
        "XGBoost Expected Par Valuation trained on 190,811 deliveries predicting context-specific expected runs.",
        "Non-Compensatory Flaw Penalization: Fatal liabilities (death runs leaked, negative collapse rescue) trigger severe deductions."
    ], GREEN)

    # ─────────────────────────────────────────────────────────────────────────
    # SLIDE 3: THE 3-TIER IDENTIFICATION ARCHITECTURE
    # ─────────────────────────────────────────────────────────────────────────
    s3 = add_blank_slide()
    add_header(s3, "Methodology & Structural Design", "The 3-Tier Identification Architecture", "Eliminating subjective debate through a rigorous multi-level framework defining Big Matches, Must-Wins, and Pressure.")

    add_card(s3, 0.8, 1.8, 3.6, 5.0, "Tier 1: Big Matches & Stakes", [
        "Knockout Stage Stakes (1.50x Multiplier): Programmatically applied to IPL Finals, Eliminators, Qualifiers, and ICC tournament knockouts.",
        "Schedule Strength Tiering: 1.25x Multiplier for Tier-1 Elite opposition (all IPL franchises + Top 7 ICC nations).",
        "Associate / Minnow Haircut (0.40x Discount): Bilateral games against lower-tier associates on low-par wickets are strictly discounted."
    ], RR_BLUE)

    add_card(s3, 4.86, 1.8, 3.6, 5.0, "Tier 2: Must-Win Attribution", [
        "Outcome Mandate: The player's team MUST win the match (team_won == 1). Runs or wickets in defeats receive 0 match-win credit.",
        "Minimum Leverage Standard: High-Pressure WPA >= +0.50 (or HP strike rate >= 160 with >= 20 runs under pressure).",
        "Crisis or Finishing Mandate: Player must record either Death Chase WPA >= 1.0 or Crisis Rescue WPA >= 1.5 against elite opposition."
    ], RR_PINK)

    add_card(s3, 8.93, 1.8, 3.6, 5.0, "Tier 3: Dynamic Ball Leverage", [
        "Leverage Index (LI >= 1.50): Derivative of win probability isolating the top 15% high-volatility deliveries in cricket.",
        "Scoreboard Chase Pressure: Triggered in 2nd innings chases when RRR >= 10.0 RPO with fewer than 8 wickets in hand.",
        "Crisis Collapse Windows: Powerplay Crisis (Overs 1-6 with <= 2 wickets down) and Middle Overs Collapse (Overs 7-12 with >= 4 down)."
    ], RR_GOLD)

    # ─────────────────────────────────────────────────────────────────────────
    # SLIDE 4: THE MACHINE LEARNING ENGINE
    # ─────────────────────────────────────────────────────────────────────────
    s4 = add_blank_slide()
    add_header(s4, "Predictive Modeling & Par Calculation", "The Machine Learning Par Valuation Engine", "Contextual expected runs model establishing objective benchmark par scores across every phase.")

    add_card(s4, 0.8, 1.8, 5.7, 5.0, "XGBoost Context-Aware Par Model", [
        "Trained across 190,811 historical deliveries using 18 predictive context features.",
        "Context Signals Evaluated on Every Delivery:",
        "  • Ground baseline par score & venue scoring index",
        "  • Overs remaining & balls bowled in current over",
        "  • Cumulative wickets lost & current run rate",
        "  • Required run rate & target differential (in second innings chases)",
        "  • Batter career archetype against specific bowler hand/type",
        "  • Pitch speed, boundary dimensions, and phase deviation index",
        "Calculates exact expected runs conceded per ball to quantify true run value."
    ], RR_PINK)

    add_card(s4, 6.8, 1.8, 5.7, 5.0, "Value Attribution & Flaw Penalties", [
        "Performance Above Expectation:",
        "  • ML Runs Added (Batting) = Runs Scored - Expected Runs",
        "  • ML Runs Saved (Bowling) = Expected Runs - Bowler Runs Conceded",
        "Non-Compensatory Flaw Penalization:",
        "  • A player cannot compensate for catastrophic phase failures with cheap volume elsewhere.",
        "  • Bowlers leaking runs above expected at the death trigger an explicit penalty: |Runs Leaked| * 0.80.",
        "  • Batters with negative crisis rescue WPA trigger an explicit penalty: |Rescue WPA| * 7.50.",
        "  • Negative death execution in chases triggers an explicit penalty: |Death WPA| * 3.00."
    ], GREEN)

    # ─────────────────────────────────────────────────────────────────────────
    # SLIDE 5: BATTING MODEL & ALLOCATION
    # ─────────────────────────────────────────────────────────────────────────
    s5 = add_blank_slide()
    add_header(s5, "Batting Formula & Allocation", "Batting Model: Match-on-the-Line Weighting Engine", "Prioritizing winning execution when the game is on the line, supported by a substantive specialist threshold.")

    add_card(s5, 0.8, 1.8, 5.7, 5.0, "The 6 Core Weightages", [
        "1. Counter-Attack Chasing (24%): WPA when chasing steep targets (RRR >= 10.0 RPO) with match on the line.",
        "2. Crisis Collapse Rescue (20%): WPA resurrecting innings after top-order collapses (<= 2 wkts in Powerplay).",
        "3. Quality Win Impact (20%): High-pressure WPA generated strictly in team victories against Tier-1 elite attacks.",
        "4. Authentic MWPP Frequency (14%): Match-Winning Pressure Performances delivering decisive outcomes.",
        "5. Death Chase Finishing (12%): Ice-cold finishing execution in overs 16-20 under tight margins (<36 runs).",
        "6. High-Leverage Consistency Rate (10%): Proportion of crucible pressure appearances generating net-positive WPA."
    ], RR_GOLD)

    add_card(s5, 6.8, 1.8, 5.7, 5.0, "Specialist Batting Standard (>= 750 Balls)", [
        "Excluding Bowlers from Batting Ranks:",
        "  • Rashid Khan faced only 506 balls. Batting at #8 creates high-variance outlier spikes.",
        "  • Rashid is properly categorized in the Bowling Top 10 (#7 globally).",
        "Filtering Low-Impact Players:",
        "  • Cameron Green managed only +11.8 Counter-Attack WPA, lacking clutch match-winning impact despite general strike rate.",
        "Filtering Cameo Finishers:",
        "  • Dinesh Karthik (637 balls, 0.0 Death-Alive WPA) and MS Dhoni (460 balls) fail the >= 750 balls standard.",
        "  • Guarantees that Top 10 batters bear full-innings responsibility."
    ], RR_BLUE)

    # ─────────────────────────────────────────────────────────────────────────
    # SLIDE 6: OFFICIAL TOP 10 BATTERS TABLE
    # ─────────────────────────────────────────────────────────────────────────
    s6 = add_blank_slide()
    add_header(s6, "Official Hackathon Results", "Official Final Top 10 Batters (Match on the Line)", "Ranked strictly by the Halla Bol Pressure Index (0-100 scale) with full factor transparency.")

    table_shape = s6.shapes.add_table(11, 10, Inches(0.8), Inches(1.8), Inches(11.733), Inches(5.0))
    table = table_shape.table

    col_widths = [Inches(0.8), Inches(2.2), Inches(0.9), Inches(1.1), Inches(1.1), Inches(1.2), Inches(1.2), Inches(1.1), Inches(1.0), Inches(1.133)]
    for idx, width in enumerate(col_widths):
        table.columns[idx].width = width

    headers = ["Rank", "Batter", "Balls", "MWPPs", "Wins", "CA WPA", "Rescue WPA", "Death WPA", "Consist.", "Clutch Score"]
    for idx, header in enumerate(headers):
        cell = table.cell(0, idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(30, 41, 59)
        p = cell.text_frame.paragraphs[0]
        p.text = header
        p.alignment = PP_ALIGN.CENTER
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = RR_PINK

    bat_data = [
        ["#1", "David Miller", "1276", "8", "15", "+42.27", "+14.28", "+17.65", "67.6%", "80.2"],
        ["#2", "Suryakumar Yadav", "2716", "8", "20", "+29.37", "+20.12", "+1.72", "70.5%", "74.0"],
        ["#3", "Namboori Tilak Varma", "2488", "7", "14", "+23.53", "+21.46", "+7.65", "57.7%", "63.7"],
        ["#4", "Heinrich Klaasen", "1410", "4", "12", "+31.61", "+24.84", "-1.02", "69.2%", "61.6"],
        ["#5", "Glenn Phillips", "1045", "4", "12", "+23.85", "+18.48", "+13.26", "69.0%", "60.6"],
        ["#6", "Shimron Hetmyer", "1240", "5", "13", "+21.95", "+16.96", "+10.20", "58.3%", "59.0"],
        ["#7", "Hardik Pandya", "1902", "3", "18", "+31.86", "+6.47", "+8.63", "67.3%", "55.7"],
        ["#8", "Virat Kohli", "2455", "6", "10", "+35.50", "+1.27", "0.00", "69.1%", "47.5"],
        ["#9", "Nicholas Pooran", "1938", "5", "11", "+25.49", "+6.29", "+1.91", "74.5%", "46.2"],
        ["#10", "Venkatesh Iyer", "942", "7", "7", "+23.56", "+3.71", "+0.48", "66.7%", "45.4"]
    ]

    for row_idx, row in enumerate(bat_data):
        for col_idx, val in enumerate(row):
            cell = table.cell(row_idx + 1, col_idx)
            cell.fill.solid()
            if row_idx == 0:
                cell.fill.fore_color.rgb = RGBColor(245, 197, 24)
            elif row_idx % 2 == 1:
                cell.fill.fore_color.rgb = RGBColor(15, 23, 42)
            else:
                cell.fill.fore_color.rgb = RGBColor(20, 30, 50)

            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.alignment = PP_ALIGN.CENTER if col_idx != 1 else PP_ALIGN.LEFT
            p.font.size = Pt(9.5)
            p.font.bold = (col_idx in [0, 1, 9] or row_idx == 0)
            p.font.color.rgb = RGBColor(7, 10, 19) if row_idx == 0 else WHITE

    # ─────────────────────────────────────────────────────────────────────────
    # SLIDE 7: BATTING FORENSIC DEEP DIVES
    # ─────────────────────────────────────────────────────────────────────────
    s7 = add_blank_slide()
    add_header(s7, "Forensic Case Studies", "Batting Deep Dives: Match Proofs & Demotions", "Concrete match logs proving why David Miller is #1, SKY is #2, and Shubman Gill was demoted.")

    add_card(s7, 0.8, 1.8, 3.6, 5.0, "David Miller (#1 — 80.2 pts)", [
        "World #1 Clutch Chase Finisher",
        "• Leads world in Counter-Attack WPA (+42.27) and Death Chase WPA (+17.65) with 8 MWPPs and 0 deductions.",
        "Defining Match Proof:",
        "  [2022-04-17] vs CSK (IPL 2022): GT was reeling at 16/3 and 87/5 chasing 170. Miller scored 94* off 51b (HP SR: 200.0) with +10.99 CA WPA and +10.53 Rescue WPA to win on the penultimate ball.",
        "  [2026-05-11] vs PBKS: 51* off 28b (+15.54 CA WPA, +12.78 Match WPA)."
    ], RR_GOLD)

    add_card(s7, 4.86, 1.8, 3.6, 5.0, "Suryakumar Yadav (#2 — 74.0 pts)", [
        "World #2 All-Phase Pressure Force",
        "• World #1 in High-Pressure Team Wins (20 Wins) and Contextual Runs Added (+234.4 ML Runs).",
        "• Faced 98.75% elite opposition schedule (2,424 balls vs Tier-1 bowling).",
        "Defining Match Proof:",
        "  [2023-05-24] vs LSG (IPL Eliminator): High-stakes knockout pressure; 33 off 20b (+11.44 CA WPA, +5.23 Match WPA) to win.",
        "  [2023-05-12] vs GT: 103* off 49b (HP SR: 257.9) with +3.89 Match WPA."
    ], RR_PINK)

    add_card(s7, 8.93, 1.8, 3.6, 5.0, "Shubman Gill Demotion (#11)", [
        "Non-Compensatory Flaw Penalty",
        "• While possessing high counter-attack volume (+31.4 WPA), Gill suffers from a negative crisis rescue score (-2.03 WPA).",
        "• When top order collapses, Gill fails to stabilize innings, repeatedly getting dismissed cheaply.",
        "• Triggers a mandatory -15.3 pt flaw penalty (7.5x crisis collapse multiplier), demoting him from Top 10 to #11 (43.4 pts).",
        "• Proves system rewards crisis anchors over front-runners."
    ], RED)

    # ─────────────────────────────────────────────────────────────────────────
    # SLIDE 8: VISUAL PROOF 1: BATTING PRESSURE QUADRANTS
    # ─────────────────────────────────────────────────────────────────────────
    s8 = add_blank_slide()
    add_header(s8, "Visual Empirical Evidence", "Visual Proof 1: Batting Pressure Archetypes & Quadrant Analysis", "Empirical scatter distribution of Crisis Rescue WPA vs High-Pressure ML Runs Added.")

    if os.path.exists("assets/visual_proofs_scatter.png"):
        s8.shapes.add_picture("assets/visual_proofs_scatter.png", Inches(0.8), Inches(1.8), width=Inches(6.8))

    add_card(s8, 7.8, 1.8, 4.733, 5.0, "Quadrant Analytical Insights", [
        "Quadrant I: Elite All-Phase Match Winners",
        "  • High ML Runs Added & High Collapse Resiliency.",
        "  • Suryakumar Yadav (+234.4 ML Runs, +20.12 Rescue WPA), Heinrich Klaasen (+24.84 Rescue), and Tilak Varma (+21.46 Rescue) occupy this apex echelon.",
        "Quadrant II: Front-Running Vulnerable",
        "  • High raw runs but negative crisis collapse score.",
        "  • Shubman Gill (-2.03 Rescue WPA) in red: fails to resurrect innings when wickets fall early, incurring a -15.3 pt deduction.",
        "Quadrant IV: Pure Chase Closers",
        "  • Specialized finishers taking over late chases.",
        "  • David Miller (#1): Unrivaled +42.27 Counter-Attack WPA converting steep chases (RRR >= 10.0)."
    ], RR_GOLD)

    # ─────────────────────────────────────────────────────────────────────────
    # SLIDE 9: BOWLING MODEL & PHASE ALLOCATION
    # ─────────────────────────────────────────────────────────────────────────
    s9 = add_blank_slide()
    add_header(s9, "Bowling Architecture & Attribution", "Bowling Model: Multi-Phase Defensive Allocation", "Evaluating bowling craft across Powerplay, Middle Overs, and Death with strict run leakage penalties.")

    add_card(s9, 0.8, 1.8, 5.7, 5.0, "Multi-Phase Runs Saved & Metrics", [
        "1. ML Runs Saved Across 3 Phases (30%):",
        "   Evaluated independently across Powerplay (1-6), Middle (7-15), and Death (16-20) against context par.",
        "2. Momentum-Breaking Dots (20%):",
        "   Dot balls delivered in high-pressure defensive overs stopping scoring momentum.",
        "3. Clutch Breakthrough Wickets (18%):",
        "   Wickets dismissing set batters during escalating target states.",
        "4. Pressure Economy vs Par (12%):",
        "   Maintaining sub-par economy under extreme chase pressure.",
        "5. High-Pressure WPA (10%) & Consistency (10%):",
        "   Win probability added and match consistency across appearances."
    ], RR_BLUE)

    add_card(s9, 6.8, 1.8, 5.7, 5.0, "Phase Risk Penalties & Schedule Scaling", [
        "Non-Negotiable Death Overs Accountability:",
        "  • Death bowling is non-negotiable in T20 cricket. Conceding runs above expectation in overs 16-20 directly loses games.",
        "  • Death Run Leakage Penalty = |Death Runs Conceded Above Par| * 0.80.",
        "Schedule Strength Minnow Calibration:",
        "  • Bowlers with heavy volume against associate nations are discounted at 0.40x.",
        "  • Mustafizur Rahman bowled 20.7% of balls (324 balls) against associate minnows in Dhaka on 120-run par pitches.",
        "  • Calibrated accurately, placing him at #4 behind Bumrah, Narine, and Hazlewood."
    ], GREEN)

    # ─────────────────────────────────────────────────────────────────────────
    # SLIDE 10: OFFICIAL TOP 10 BOWLERS TABLE
    # ─────────────────────────────────────────────────────────────────────────
    s10 = add_blank_slide()
    add_header(s10, "Official Hackathon Results", "Official Final Top 10 Bowlers (Multi-Phase Defense)", "Ranked strictly by the Halla Bol Pressure Index (0-100 scale) with complete phase accountability.")

    table_shape2 = s10.shapes.add_table(11, 10, Inches(0.8), Inches(1.8), Inches(11.733), Inches(5.0))
    table2 = table_shape2.table

    col_widths2 = [Inches(0.8), Inches(2.2), Inches(0.9), Inches(1.0), Inches(1.1), Inches(1.1), Inches(1.2), Inches(1.1), Inches(1.1), Inches(1.233)]
    for idx, width in enumerate(col_widths2):
        table2.columns[idx].width = width

    headers2 = ["Rank", "Bowler", "Craft", "Matches", "PP Saved", "Mid Saved", "Death Saved", "Minnow %", "Deductions", "Clutch Score"]
    for idx, header in enumerate(headers2):
        cell = table2.cell(0, idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(30, 41, 59)
        p = cell.text_frame.paragraphs[0]
        p.text = header
        p.alignment = PP_ALIGN.CENTER
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = RR_PINK

    bowl_data = [
        ["#1", "Jasprit Bumrah", "PACE", "75", "+18.0", "+74.5", "+149.8", "3.9%", "0.00", "78.5"],
        ["#2", "Sunil Narine", "SPIN", "66", "+20.2", "+80.2", "+23.6", "0.0%", "0.00", "52.4"],
        ["#3", "Josh Hazlewood", "PACE", "63", "+48.4", "-3.8", "+9.1", "0.0%", "-3.03", "52.1"],
        ["#4", "Mustafizur Rahman", "PACE", "70", "+21.9", "+18.3", "+84.8", "20.7%", "0.00", "45.3"],
        ["#5", "Nathan Ellis", "PACE", "41", "+9.4", "+32.6", "+41.5", "0.0%", "0.00", "44.0"],
        ["#6", "Bhuvneshwar Kumar", "PACE", "100", "+16.4", "-3.0", "+41.2", "2.7%", "-2.43", "43.0"],
        ["#7", "Rashid Khan", "SPIN", "122", "+20.2", "+19.5", "+10.7", "16.6%", "0.00", "39.7"],
        ["#8", "Axar Patel", "SPIN", "135", "+7.4", "-1.2", "+2.9", "3.8%", "-0.97", "38.8"],
        ["#9", "Varun Chakravarthy", "SPIN", "94", "+36.7", "+25.7", "-9.6", "0.6%", "-7.69", "38.6"],
        ["#10", "Maheesh Theekshana", "SPIN", "98", "+41.9", "+2.8", "+39.6", "8.3%", "0.00", "38.3"]
    ]

    for row_idx, row in enumerate(bowl_data):
        for col_idx, val in enumerate(row):
            cell = table2.cell(row_idx + 1, col_idx)
            cell.fill.solid()
            if row_idx == 0:
                cell.fill.fore_color.rgb = RGBColor(245, 197, 24)
            elif row_idx % 2 == 1:
                cell.fill.fore_color.rgb = RGBColor(15, 23, 42)
            else:
                cell.fill.fore_color.rgb = RGBColor(20, 30, 50)

            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.alignment = PP_ALIGN.CENTER if col_idx not in [1, 2] else PP_ALIGN.LEFT
            p.font.size = Pt(9.5)
            p.font.bold = (col_idx in [0, 1, 9] or row_idx == 0)
            p.font.color.rgb = RGBColor(7, 10, 19) if row_idx == 0 else WHITE

    # ─────────────────────────────────────────────────────────────────────────
    # SLIDE 11: BOWLING FORENSIC DEEP DIVES
    # ─────────────────────────────────────────────────────────────────────────
    s11 = add_blank_slide()
    add_header(s11, "Forensic Case Studies", "Bowling Deep Dives: King of Pace & King of Spin", "Concrete match proofs showing Bumrah's dominance, Narine vs Varun, and death overs risk.")

    add_card(s11, 0.8, 1.8, 3.6, 5.0, "Jasprit Bumrah (#1 — 78.5 pts)", [
        "Undisputed King of Pace",
        "• +149.8 runs saved above par at the death (more than double all competitors).",
        "• 7.36 pressure economy rate with 64.4% consistency and zero deductions.",
        "Defining Match Proof:",
        "  [2024-04-11] vs RCB (IPL 2024): On a high-scoring Wankhede pitch, dismantled RCB with 5/22 (24b, Eco: 4.20) and +3.91 Match WPA.",
        "  [2024-03-24] vs GT: 3/15 (24b, Eco: 4.36, +3.13 WPA)."
    ], RR_GOLD)

    add_card(s11, 4.86, 1.8, 3.6, 5.0, "Sunil Narine (#2 — 52.4 pts)", [
        "Undisputed King of Spin",
        "• Flawless across all 3 phases: +20.2 PP, +80.2 Mid, and +23.6 Death runs saved.",
        "• Faced 100% Tier-1 elite opposition (0.0% minnows) with 0.00 deductions.",
        "Contrast vs Varun Chakravarthy (#9):",
        "  • Varun is elite in PP (+36.7) and Mid (+25.7) but leaked -9.61 runs at the death, taking an explicit -7.69 pt penalty.",
        "  • Narine beats Varun decisively by 13.8 pts."
    ], RR_PINK)

    add_card(s11, 8.93, 1.8, 3.6, 5.0, "Phase Risk Penalties (Siraj & Bishnoi)", [
        "Fatal Death Leakage Demotions",
        "• Mohammed Siraj (#19, 30.2 pts): Leaked -20.99 runs above expected at the death at an 8.98 RPO, taking a -16.8 pt deduction.",
        "• Ravi Bishnoi (#51, 15.4 pts): Elite in middle overs (+64.7) but leaked -41.78 runs at the death (10.42 RPO), taking a -33.4 pt deduction.",
        "• Proves high powerplay bowling cannot compensate for fatal death leakage."
    ], RED)

    # ─────────────────────────────────────────────────────────────────────────
    # SLIDE 12: VISUAL PROOF 2 & 3: MULTI-PHASE MATRIX & SCHEDULE CALIBRATION
    # ─────────────────────────────────────────────────────────────────────────
    s12 = add_blank_slide()
    add_header(s12, "Visual Empirical Evidence", "Visual Proof 2 & 3: Multi-Phase Matrix & Schedule Calibration", "Empirical validation of Bowling Runs Saved by phase and Associate Minnow Exposure.")

    if os.path.exists("assets/schedule_calibration.png"):
        s12.shapes.add_picture("assets/schedule_calibration.png", Inches(0.8), Inches(1.8), width=Inches(6.8))

    add_card(s12, 7.8, 1.8, 4.733, 5.0, "Key Empirical Discoveries", [
        "Multi-Phase Defensive Allocation",
        "  • Jasprit Bumrah's death-phase bar is completely unmatched (+149.8 runs saved), dwarfing the rest of the cohort.",
        "  • Varun Chakravarthy's death bar extends into negative red (-9.61), confirming his tactical death-phase vulnerability.",
        "Schedule Strength Calibration",
        "  • Mustafizur Rahman's 20.7% associate minnow delivery volume is discounted by 0.40x, adjusting his rank from #2 to #4.",
        "  • Sunil Narine and Josh Hazlewood faced 0.0% minnows, guaranteeing their top podium standing."
    ], RR_BLUE)

    # ─────────────────────────────────────────────────────────────────────────
    # SLIDE 13: STRATEGIC INSIGHTS & AUCTION BLUEPRINT FOR RR
    # ─────────────────────────────────────────────────────────────────────────
    s13 = add_blank_slide()
    add_header(s13, "Franchise Decision Sciences", "Strategic Insights & Auction Blueprint for Rajasthan Royals", "Actionable recommendations for squad building, auction targets, and role deployment.")

    add_card(s13, 0.8, 1.8, 3.6, 5.0, "1. Core Retention Validation", [
        "Shimron Hetmyer (#6 Batter, 59.0 pts):",
        "  • Confirmed as an elite clutch closer (+21.95 CA WPA, +16.96 Rescue WPA, +10.20 Death WPA).",
        "  • Retaining Hetmyer guarantees proven execution when RRR >= 12.0.",
        "Sandeep Sharma (#12 Bowler, 35.5 pts):",
        "  • 70.0% pressure consistency rate with 0.0 deductions over 43 matches.",
        "  • Validated as an elite domestic death-overs stabilizer."
    ], RR_PINK)

    add_card(s13, 4.86, 1.8, 3.6, 5.0, "2. High-Value Auction Targets", [
        "Nathan Ellis (#5 Bowler, 44.0 pts):",
        "  • Saves +41.5 death runs and +32.6 middle runs against 100% elite competition with zero deductions.",
        "Heinrich Klaasen (#4 Batter, 61.6 pts):",
        "  • World #1 in Crisis Rescue (+24.84 WPA); dismantles middle-overs spin.",
        "Tilak Varma (#3 Batter, 63.7 pts):",
        "  • Elite crisis anchor with +21.46 Rescue WPA and 7 Authentic MWPPs."
    ], RR_GOLD)

    add_card(s13, 8.93, 1.8, 3.6, 5.0, "3. Tactical Deployment Rules", [
        "Death Phase Risk Mandate:",
        "  • Never entrust the 18th-20th overs to bowlers with negative death par metrics (e.g. Siraj, Bishnoi, Varun).",
        "Anchoring Balance in Chases:",
        "  • Pair explosive finishers (Miller, Hetmyer) with high-consistency anchors (Pooran 74.5%, Kohli 69.1%) to maximize win conversion."
    ], GREEN)

    # ─────────────────────────────────────────────────────────────────────────
    # SLIDE 14: PRODUCTION STUDIO & REPOSITORY ARCHITECTURE
    # ─────────────────────────────────────────────────────────────────────────
    s14 = add_blank_slide()
    add_header(s14, "Software Deliverables & Verification", "Production Studio & Repository Architecture", "Enterprise-grade Dash dashboard and reproducible datasets delivered for the Rajasthan Royals.")

    add_card(s14, 0.8, 1.8, 5.7, 5.0, "Live Interactive Analytics Studio", [
        "Dashboard Architecture (Python Dash + Plotly Web App):",
        "  • Live Online Dashboard: https://lohithaswin.github.io/play-rr-hackathon-2026/",
        "  • GitHub Repository: https://github.com/Lohithaswin/play-rr-hackathon-2026",
        "  • Local Dash Studio: http://127.0.0.1:8050",
        "  • Tab 1: Leaderboards & Multi-Phase Audit",
        "  • Tab 2: Visual Proofs & Forensic Player Evidence Dossiers",
        "  • Tab 3: How Each Player Reached Top 10 (Deep Dives)",
        "  • Tab 4: Analytical Case Studies (5 Core Franchise Debates)",
        "  • Tab 5: Mathematical Architecture & Pressure Methodology",
        "Completely sanitized UI with clean typography, institutional Rajasthan Royals branding, and zero extraneous emojis."
    ], RR_PINK)

    add_card(s14, 6.8, 1.8, 5.7, 5.0, "Reproducible Data Deliverables", [
        "Transparent Files on Disk (d:\\rr):",
        "  • bat_rankings_final.parquet & bat_final_transparent.csv",
        "  • bowl_rankings_final.parquet & bowl_final_transparent.csv",
        "  • bat_hp_match_logs.parquet & bowl_hp_match_logs.parquet",
        "  • player_hp_summary.txt (Full inning-by-inning audit log)",
        "  • Play_RR_Hackathon_Methodology_Report_Lohithaswin_V.docx",
        "  • Play_RR_Hackathon_Methodology_Report_Lohithaswin_V.pdf",
        "  • Play_RR_Hackathon_Lohithaswin_V.pptx & .pdf",
        "Submitted by: LOHITHASWIN V"
    ], RR_BLUE)

    # Save presentation
    output_path = 'd:/rr/Play_RR_Hackathon_Lohithaswin_V.pptx'
    prs.save(output_path)
    print(f"Successfully generated PowerPoint presentation at: {output_path}")

    # Export to PDF via PowerPoint COM
    pdf_output = 'd:/rr/Play_RR_Hackathon_Lohithaswin_V.pdf'
    try:
        powerpoint = win32com.client.Dispatch("PowerPoint.Application")
        ppt = powerpoint.Presentations.Open(os.path.abspath(output_path), WithWindow=False)
        ppt.SaveAs(os.path.abspath(pdf_output), 32) # 32 = ppSaveAsPDF
        ppt.Close()
        powerpoint.Quit()
        print(f"Successfully converted PowerPoint presentation to PDF at: {pdf_output}")
    except Exception as e:
        print("PowerPoint PDF conversion error:", e)

if __name__ == '__main__':
    build_presentation()
