# PLAY RR HACKATHON — SEASON 2
## OFFICIAL PRESENTATION SLIDE DECK & EXECUTIVE WALKTHROUGH

**Project Title:** SupeRR Selector: The Halla Bol Pressure Index  
**Subtitle:** Context-Aware Multi-Phase Leverage & Win Probability Engine | IPL & T20I (2022–2026)  
**Lead Researcher & Submitter:** **LOHITHASWIN V**  
**Target Organization:** Rajasthan Royals (RR) Analytics & High-Performance Decision Sciences  
**PowerPoint File:** [Play_RR_Hackathon_Lohithaswin_V.pptx](file:///d:/rr/Play_RR_Hackathon_Lohithaswin_V.pptx)  
**Live Published Web Dashboard:** [https://lohithaswin.github.io/play-rr-hackathon-2026/](https://lohithaswin.github.io/play-rr-hackathon-2026/)  
**GitHub Repository:** [https://github.com/Lohithaswin/play-rr-hackathon-2026](https://github.com/Lohithaswin/play-rr-hackathon-2026)  
**Local Interactive Dashboard:** [http://127.0.0.1:8050](http://127.0.0.1:8050)  
**Comprehensive Research Whitepaper:** [PLAY_RR_HACKATHON_SUBMISSION.md](file:///d:/rr/PLAY_RR_HACKATHON_SUBMISSION.md)  
**Scope:** 883 Matches • 190,811 Deliveries  

---

## SLIDE 1: TITLE SLIDE (Brand & Submitter Identification)

### Slide Layout & Visual Elements
- **Header Badge:** RAJASTHAN ROYALS HIGH-PERFORMANCE CRICKET ANALYTICS STUDIO
- **Primary Title:** SupeRR Selector: The Halla Bol Pressure Index
- **Secondary Subtitle:** Context-Aware Multi-Phase Leverage & Win Probability Engine | IPL & T20I (2022–2026)
- **Author Callout:** **Lead Submitter: LOHITHASWIN V**
- **Competition Metadata:** Play RR Hackathon Season 2 (2026) | 883 Matches | 190,811 Deliveries

### Speaker Notes & Presentation Script
> *"Good morning, esteemed members of the Rajasthan Royals analytics and decision sciences group. My name is **Lohithaswin V**, and today I am presenting **The Halla Bol Pressure Index** — an institutional machine learning and leverage evaluation engine engineered specifically for Rajasthan Royals squad management, auction strategy, and in-game tactical deployment. Built on an exhaustive dataset of 883 matches and over 190,000 deliveries across the 2022–2026 cycle, our system eliminates context-blind statistical noise to identify who actually wins cricket matches when the game is on the line."*

---

## SLIDE 2: THE CONTEXT BLINDNESS OF TRADITIONAL CRICKET METRICS

### Slide Layout & 3-Column Card Architecture
1. **Card 1 (Flat State Assumption):** Conventional batting averages and strike rates assume all runs are created equal. A boundary scored in the 3rd over of a bilateral dead-rubber carries identical weight to a boundary scored needing 14 runs off the final over of an IPL Eliminator.
2. **Card 2 (Empty Run Accumulation):** Uncalibrated counting statistics reward front-runners who pad volume on flat pitches or when matches are already decided, while penalizing middle-order anchors who enter under top-order collapses.
3. **Card 3 (The Strategic Mandate):** A franchise cannot construct a championship roster on context-blind data. We need an objective system that evaluates execution under dynamic leverage, scoreboard pressure, and tournament stakes.

### Key Data Callouts
- **Traditional Batting Average Flaw:** Does not account for required run rate, wickets lost, or phase of the match.
- **Traditional Economy Rate Flaw:** Leaking 35 runs in the Powerplay is bad, but leaking 25 runs in the 20th over loses the match directly.

---

## SLIDE 3: THE 3-TIER IDENTIFICATION ARCHITECTURE

### Slide Layout & Structure
A structured flowchart detailing the three analytical tiers used to tag and isolate pressure:

```
TIER 1: TOURNAMENT STAKES (Big Matches)
├── Knockout Multiplier (1.50x): Finals, Eliminators, Qualifiers, Super 4
└── Schedule Strength: 1.25x Elite (IPL & Top 7 ICC) vs 0.40x Associate Haircut

TIER 2: MATCH-WINNING ATTRIBUTION (Must-Wins)
├── Outcome Constraint: Team MUST Win (team_won == 1)
├── Leverage Standard: High-Pressure WPA ≥ +0.50
└── Finishing / Crisis Mandate: Death WPA ≥ 1.0 OR Rescue WPA ≥ 1.5

TIER 3: DYNAMIC BALL-BY-BALL LEVERAGE (Pressure Crucible)
├── Leverage Index (LI ≥ 1.50): Top 15% Game-Defining Deliveries
├── Scoreboard Chase Pressure: 2nd Innings RRR ≥ 10.0 RPO (<8 wickets in hand)
├── Crisis Collapse Windows: PP (Overs 1-6 with ≥2 down) | Mid (Overs 7-12 with ≥4 down)
└── Death Crucible: Overs 16-20 with Match Margin < 36 Runs
```

---

## SLIDE 4: THE MACHINE LEARNING PAR VALUATION ENGINE

### Slide Layout & Analytical Features
- **Left Panel:** The XGBoost Context-Aware Par Model
  - Trained across 190,811 deliveries using 18 predictive context features: ground par baseline, overs remaining, wickets in hand, current run rate, required run rate, batter archetype vs bowler hand/type, and pitch deviation index.
  - Predicts the exact par run value of every single delivery.
- **Right Panel:** Attribution & Strict Flaw Penalties
  - $\text{ML Runs Added (Batting)} = \text{Runs Scored} - \text{Expected Runs}$
  - $\text{ML Runs Saved (Bowling)} = \text{Expected Runs} - \text{Runs Conceded}$
  - **Non-Compensatory Flaw Accountability:** Fatal liabilities in critical phases trigger direct score deductions that cannot be redeemed by front-running volume.

---

## SLIDE 5: BATTING MODEL: MATCH-ON-THE-LINE ENGINE & ELIGIBILITY

### Mathematical Formulation
$$\text{Batting Clutch Score} = \left( \sum W_i \cdot S_i \right) \cdot \text{Reliability} - \text{Flaw Penalties}$$

### The 6 Core Mathematical Weights
1. **Counter-Attack Chasing ($RRR \ge 10.0$ RPO): 24%** — Ice-cold boundary hitting under escalating chase pressure.
2. **Crisis Collapse Rescue: 20%** — Elevating the team after early top-order collapse ($\le 2$ wkts down in Powerplay).
3. **Quality Win Impact vs Elite Attacks: 20%** — WPA generated strictly in team victories against Tier-1 opposition.
4. **Authentic MWPP Frequency: 14%** — Match-Winning Pressure Performances delivering decisive outcomes.
5. **Death Chase Finishing (Overs 16–20): 12%** — Finishing execution with match margins under 36 runs.
6. **High-Leverage Consistency Rate: 10%** — Proportion of crucible appearances producing positive net WPA.

### The Specialist Batting Standard ($\ge 750$ Career Balls)
- **Eliminating Bowlers from Batting:** Rashid Khan faced only 506 balls. In batting at #8, a 15-ball cameo creates high statistical variance; he is properly assigned to the **Bowling Top 10 (#7 globally)**.
- **Filtering Low-Impact Players:** Cameron Green (1,068 balls) managed only +11.8 Counter-Attack WPA, falling well short of match-winning impact despite general strike rate.
- **Filtering Cameos:** Dinesh Karthik (637 balls, 0.0 Death-Alive WPA) and MS Dhoni (460 balls) fail the $\ge 750$ balls standard.

---

## SLIDE 6: OFFICIAL FINAL TOP 10 BATTERS (MATCH ON THE LINE)

| Rank | Batter | Career Balls | MWPPs | Crucible Wins | Counter-Attack WPA | Crisis Rescue WPA | Death Chase WPA | Consistency Rate | Halla Bol Clutch Score |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **#1** | **David Miller** | 1276 | **8** | 15 | **+42.27 (World #1)** | +14.28 | **+17.65 (World #1)** | 67.6% | **80.2** |
| **#2** | **Suryakumar Yadav** | 2716 | **8** | **20 (World #1)** | +29.37 | +20.12 | +1.72 | 70.5% | **74.0** |
| **#3** | **Namboori Tilak Varma** | 2488 | 7 | 14 | +23.53 | +21.46 | +7.65 | 57.7% | **63.7** |
| **#4** | **Heinrich Klaasen** | 1410 | 4 | 12 | +31.61 | **+24.84 (World #1)** | -1.02 | 69.2% | **61.6** |
| **#5** | **Glenn Phillips** | 1045 | 4 | 12 | +23.85 | +18.48 | +13.26 | 69.0% | **60.6** |
| **#6** | **Shimron Hetmyer** | 1240 | 5 | 13 | +21.95 | +16.96 | +10.20 | 58.3% | **59.0** |
| **#7** | **Hardik Pandya** | 1902 | 3 | 18 | +31.86 | +6.47 | +8.63 | 67.3% | **55.7** |
| **#8** | **Virat Kohli** | 2455 | 6 | 10 | +35.50 | +1.27 | 0.00 | 69.1% | **47.5** |
| **#9** | **Nicholas Pooran** | 1938 | 5 | 11 | +25.49 | +6.29 | +1.91 | **74.5% (World #1)** | **46.2** |
| **#10** | **Venkatesh Iyer** | 942 | 7 | 7 | +23.56 | +3.71 | +0.48 | 66.7% | **45.4** |

---

## SLIDE 7: BATTING FORENSIC DEEP DIVES & MATCH PROOFS

### 1. David Miller (#1 — 80.2 pts): The Chase Finisher
- **Key Evidence:** World #1 in Counter-Attack WPA (+42.27) and Death Chase WPA (+17.65) with 8 MWPPs, 15 crucible wins, and 0.0 deductions.
- **Match Proof:** `[2022-04-17] vs CSK (IPL 2022)`: GT was 16/3 and 87/5 chasing 170. Miller smashed 94* off 51b (HP SR: 200.0) with +10.99 CA WPA and +10.53 Rescue WPA to win on the penultimate delivery.

### 2. Suryakumar Yadav (#2 — 74.0 pts): The All-Phase Force
- **Key Evidence:** World leader in High-Pressure Team Wins (20 Wins) and Contextual Runs Added (+234.4 ML Runs). Faced 2,424 balls against Tier-1 elite bowling (98.75% elite schedule).
- **Match Proof:** `[2023-05-24] vs LSG (IPL Eliminator)`: High-stakes knockout pressure; 33 off 20b (+11.44 CA WPA, +5.23 Match WPA) to win.

### 3. Shubman Gill Demotion (#11 — 43.4 pts)
- **Forensic Failure:** Possesses strong counter-attack volume (+31.4 WPA), but suffers from a negative crisis rescue metric (**$-2.03$ WPA**). When early wickets fall, Gill fails to stabilize the innings.
- **Penalty Applied:** Incurs an explicit **$-15.3$ pt flaw penalty** ($7.5\times$ multiplier), demoting him outside the Top 10.

---

## SLIDE 8: BOWLING MODEL: MULTI-PHASE DEFENSE ALLOCATION

### Metric Architecture & Accountability
1. **Quality Runs Saved Across 3 Phases (30%):** Evaluated against context par across Powerplay (1–6), Middle (7–15), and Death (16–20).
2. **Momentum-Breaking Dots (20%):** Dot balls delivered in high-pressure defensive overs stopping scoring momentum.
3. **Clutch Breakthrough Wickets (18%):** Wickets dismissing set batters during escalating target states.
4. **Pressure Economy vs Par (12%):** Maintaining sub-par economy under extreme chase pressure.
5. **High-Pressure WPA (10%) & Consistency (10%):** Win probability added and match consistency across appearances.

### Fatal Death Run Leakage Penalties
- Leaking runs above expectation in overs 16–20 directly loses T20 matches.
- $\text{Penalty}_{\text{death}} = |\text{Death Runs Leaked Above Par}| \times 0.80$.

---

## SLIDE 9: OFFICIAL FINAL TOP 10 BOWLERS (MULTI-PHASE DEFENSE)

| Rank | Bowler | Craft | Matches | PP Saved | Mid Saved | Death Saved | Minnow % | Deductions | Halla Bol Clutch Score |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **#1** | **Jasprit Bumrah** | PACE | 75 | +18.0 | **+74.5** | **+149.8 (World #1)** | 3.9% | **0.00** | **78.5** |
| **#2** | **Sunil Narine** | SPIN | 66 | +20.2 | **+80.2** | +23.6 | **0.0%** | **0.00** | **52.4** |
| **#3** | **Josh Hazlewood** | PACE | 63 | **+48.4 (World #1)** | -3.8 | +9.1 | **0.0%** | **-3.03** | **52.1** |
| **#4** | **Mustafizur Rahman** | PACE | 70 | +21.9 | +18.3 | **+84.8** | 20.7% | **0.00** | **45.3** |
| **#5** | **Nathan Ellis** | PACE | 41 | +9.4 | +32.6 | +41.5 | **0.0%** | **0.00** | **44.0** |
| **#6** | **Bhuvneshwar Kumar** | PACE | 100 | +16.4 | -3.0 | +41.2 | 2.7% | **-2.43** | **43.0** |
| **#7** | **Rashid Khan** | SPIN | 122 | +20.2 | +19.5 | +10.7 | 16.6% | **0.00** | **39.7** |
| **#8** | **Axar Patel** | SPIN | 135 | +7.4 | -1.2 | +2.9 | 3.8% | **-0.97** | **38.8** |
| **#9** | **Varun Chakravarthy** | SPIN | 94 | +36.7 | +25.7 | **-9.6** | 0.6% | **-7.69** | **38.6** |
| **#10** | **Maheesh Theekshana** | SPIN | 98 | +41.9 | +2.8 | +39.6 | 8.3% | **0.00** | **38.3** |

---

## SLIDE 10: BOWLING FORENSIC DEEP DIVES & PHASE RISK

### 1. Jasprit Bumrah (#1 — 78.5 pts): Undisputed King of Pace
- Saved **+149.8 runs above par at the death** (more than double all competitors).
- Conceded an unbelievable 7.36 pressure economy with 64.4% consistency and zero deductions.
- Match Proof: `[2024-04-11] vs RCB`: 4.0–0–22–5 (24b, Eco: 4.20) with +3.91 Match WPA on a 395-run pitch.

### 2. Sunil Narine (#2 — 52.4 pts): Undisputed King of Spin
- Positive runs saved across all 3 phases (+20.2 PP, +80.2 Mid, +23.6 Death) against 100% elite competition (0.0% minnows).
- **Decisive Contrast vs Varun Chakravarthy (#9):** Varun is elite in PP (+36.7) and Mid (+25.7), but leaked **$-9.61$ runs at the death**, taking an explicit **$-7.69$ pt penalty**. Narine beats Varun decisively by 13.8 pts.

### 3. Schedule Strength Calibration: Mustafizur Rahman (#4)
- 20.7% of Mustafizur's deliveries (324 balls) came against associate minnows in Dhaka on 120-run par pitches.
- Applying a $0.40\times$ associate discount accurately calibrated him from #2 to #4, correctly placing him behind Bumrah, Narine, and Hazlewood.

### 4. Phase Risk Demotions: Mohammed Siraj & Ravi Bishnoi
- **Mohammed Siraj (#19, 30.2 pts):** Conceded **$-20.99$ runs above par at the death** at an 8.98 RPO ($-16.8$ pt deduction).
- **Ravi Bishnoi (#51, 15.4 pts):** Leaked **$-41.78$ runs at the death** with a 10.42 death economy ($-33.4$ pt deduction).

---

## SLIDE 11: STRATEGIC INSIGHTS & AUCTION BLUEPRINT FOR RAJASTHAN ROYALS

### 1. Core Retention Validation
- **Shimron Hetmyer (#6 Batter, 59.0 pts):** Confirmed as an elite clutch closer (+21.95 CA WPA, +16.96 Rescue WPA, +10.20 Death WPA). Retaining Hetmyer guarantees proven execution when $RRR \ge 12.0$.
- **Sandeep Sharma (#12 Bowler, 35.5 pts):** 70.0% pressure consistency rate with 0.0 deductions over 43 matches. Validated as an elite domestic death-overs stabilizer.

### 2. High-Value Auction Targets
- **Nathan Ellis (#5 Bowler, 44.0 pts):** Exceptional multi-phase fast bowler (+41.5 death, +32.6 mid) with 0.0 deductions against 100% elite competition.
- **Heinrich Klaasen (#4 Batter, 61.6 pts):** World #1 in Crisis Rescue (+24.84 WPA); completely neutralizes middle-overs spin.
- **Tilak Varma (#3 Batter, 63.7 pts):** Elite young anchor with +21.46 Rescue WPA and 7 Authentic MWPPs.

### 3. Tactical Deployment Rules
- **Death Phase Risk Mandate:** Never entrust the 18th–20th overs to bowlers with negative death par metrics (e.g. Siraj, Bishnoi, Varun).
- **Chase Composition Rule:** Pair explosive finishers (Miller, Hetmyer) with high-consistency anchors (Pooran 74.5%, Kohli 69.1%) to maximize target conversion.

---

## SLIDE 12: PRODUCTION STUDIO & REPOSITORY DELIVERABLES

### Live Interactive Analytics Studio
- **Platform:** Python Dash + Plotly Web App Architecture
- **Online Access:** [https://lohithaswin.github.io/play-rr-hackathon-2026/](https://lohithaswin.github.io/play-rr-hackathon-2026/)
- **GitHub Repository:** [https://github.com/Lohithaswin/play-rr-hackathon-2026](https://github.com/Lohithaswin/play-rr-hackathon-2026)
- **Local Access:** Running locally on port 8050 (`http://127.0.0.1:8050`) or offline via `index.html`
- **Tabs:**
  - Tab 1: Leaderboards & Multi-Phase Audit
  - Tab 2: Visual Proofs & Forensic Player Evidence Dossiers
  - Tab 3: Analytical Case Studies (The 5 Core Debates)
  - Tab 4: Mathematical Architecture & Pressure Methodology
- **Sanitized UI:** Professional typography, official Rajasthan Royals color scheme, and zero extraneous emojis.

### Verified Files on Disk (`d:\rr\`)
- Presentation Slide Deck: [Play_RR_Hackathon_Lohithaswin_V.pptx](file:///d:/rr/Play_RR_Hackathon_Lohithaswin_V.pptx)
- Official Submission Whitepaper: [PLAY_RR_HACKATHON_SUBMISSION.md](file:///d:/rr/PLAY_RR_HACKATHON_SUBMISSION.md)
- Repository README: [README.md](file:///d:/rr/README.md)
- Inning-by-Inning Match Audit Log: [player_hp_summary.txt](file:///d:/rr/player_hp_summary.txt)
- Transparent Datasets: [bat_final_transparent.csv](file:///d:/rr/bat_final_transparent.csv) and [bowl_final_transparent.csv](file:///d:/rr/bowl_final_transparent.csv)
- Master Parquet Tables: `bat_rankings_final.parquet`, `bowl_rankings_final.parquet`, `bat_hp_match_logs.parquet`, `bowl_hp_match_logs.parquet`

---
*Official Rajasthan Royals Hackathon Submission | Lead Submitter: Lohithaswin V | Halla Bol!*
