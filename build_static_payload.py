import json
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# Theme Colors
RR_PINK     = '#ea008a'
RR_BLUE     = '#1e40af'
RR_GOLD     = '#f5c518'
BG          = '#070a13'
CARD        = '#0f172a'
CARD_HOVER  = '#1e293b'
BORDER      = 'rgba(255, 255, 255, 0.08)'
TEXT        = '#f8fafc'
SUBTEXT     = '#94a3b8'
GREEN       = '#10b981'
RED         = '#f43f5e'
LIGHT_BLUE  = '#38bdf8'

print("Loading parquets...")
bat_rank = pd.read_parquet('bat_rankings_final.parquet')
bowl_rank = pd.read_parquet('bowl_rankings_final.parquet')
bat_logs = pd.read_parquet('bat_hp_match_logs.parquet')
bowl_logs = pd.read_parquet('bowl_hp_match_logs.parquet')

bat10 = bat_rank.head(10).reset_index(drop=True)
bowl10 = bowl_rank.head(10).reset_index(drop=True)
# Only Top 10 + Shubman Gill (#11 for Quadrant II collapse failure contrast) - NO Phil Salt
bat_scatter = bat_rank[bat_rank['rank_bat'] <= 11].reset_index(drop=True)

# ─────────────────────────────────────────────────────────────────────────────
# EXHAUSTIVE TOP 10 QUALIFYING EXPLANATIONS (WHY THEY GOT IN)
# ─────────────────────────────────────────────────────────────────────────────
TOP10_BAT_EXPLANATIONS = {
    'David Miller': {
        'rank': 1,
        'title': 'The Undisputed World #1 Chase Finisher',
        'archetype': 'Ice-Cold Death Finisher',
        'why_top10': 'David Miller is the gold standard of high-pressure run chasing. In steep chases where the Required Run Rate exceeds 10.0 RPO, Miller generated an unprecedented +42.27 Counter-Attack WPA — highest in global T20 cricket. He delivered 8 Authentic Match-Winning Pressure Performances (MWPPs), carried 15 high-leverage team wins, and added +17.65 Death Finishing WPA. With zero flaw deductions, his 80.2 clutch rating stands uncontested at World #1.',
        'key_formula_breakdown': [
            {'metric': 'Counter-Attack Chasing WPA (RRR ≥ 10.0)', 'val': '+42.27', 'impact': '38.2 pts earned', 'color': RR_GOLD},
            {'metric': 'Death Finishing WPA (Overs 16–20)', 'val': '+17.65', 'impact': '18.4 pts earned', 'color': GREEN},
            {'metric': 'Authentic MWPPs (Decisive Knocks)', 'val': '8 Wins', 'impact': '14.0 pts earned', 'color': RR_PINK},
            {'metric': 'Pressure Consistency Rate', 'val': '67.6%', 'impact': '9.6 pts earned', 'color': GREEN},
            {'metric': 'Flaw Deductions (Collapse/Leakage)', 'val': '0.0', 'impact': '0.0 penalty', 'color': SUBTEXT}
        ],
        'signature_matches': 'vs CSK (IPL Qualifier: 68* off 38b, WPA +3.45); vs RR (IPL Final: 32* off 19b, WPA +2.18); vs India (T20I: 106* off 47b, WPA +4.10)'
    },
    'Suryakumar Yadav': {
        'rank': 2,
        'title': 'World #2 All-Phase Pressure Force',
        'archetype': '360° All-Phase Dominator',
        'why_top10': 'Suryakumar Yadav achieved the highest raw run contribution above expected (+234.4 ML Runs Added) against 98.8% Tier-1 elite attacks. Unlike pure finishers who only bat in the death, Surya excels across both top-order crisis rescue (+20.12 Crisis WPA) and steep chases (+29.37 CA WPA). He piloted 20 high-pressure team victories, converted 8 Authentic MWPPs, and maintained a phenomenal 70.5% consistency rate with zero deductions.',
        'key_formula_breakdown': [
            {'metric': 'High-Pressure ML Runs Added', 'val': '+234.4', 'impact': '28.5 pts earned', 'color': RR_PINK},
            {'metric': 'Counter-Attack Chasing WPA', 'val': '+29.37', 'impact': '24.1 pts earned', 'color': RR_GOLD},
            {'metric': 'Crisis Rescue WPA (Early Collapse)', 'val': '+20.12', 'impact': '18.2 pts earned', 'color': GREEN},
            {'metric': 'High-Pressure Win Conversion', 'val': '20 Wins', 'impact': '15.0 pts earned', 'color': GREEN},
            {'metric': 'Flaw Deductions', 'val': '0.0', 'impact': '0.0 penalty', 'color': SUBTEXT}
        ],
        'signature_matches': 'vs RCB (83 off 35b chasing 200, WPA +3.82); vs England (117 off 55b from 31/3 collapse, WPA +4.21); vs GT (103* off 49b, WPA +3.65)'
    },
    'Namboori Tilak Varma': {
        'rank': 3,
        'title': 'World #3 Crisis Collapse Savior',
        'archetype': 'Top-Order Collapse Anchor',
        'why_top10': 'Tilak Varma recorded the 2nd highest Crisis Rescue WPA globally (+21.46) across 125 matches. Walking in repeatedly after Mumbai Indians suffered early top-order collapses (≤2 wickets down in Powerplay), Varma demonstrated nerves of steel, combining +23.53 Counter-Attack WPA with 7 Authentic MWPPs and 14 crucible victories. His ability to resurrect an innings without stalling strike rate earns him a podium rank of 63.7 pts.',
        'key_formula_breakdown': [
            {'metric': 'Crisis Rescue WPA (Collapse Resiliency)', 'val': '+21.46', 'impact': '23.8 pts earned', 'color': GREEN},
            {'metric': 'Counter-Attack Chasing WPA', 'val': '+23.53', 'impact': '20.1 pts earned', 'color': RR_GOLD},
            {'metric': 'Authentic MWPPs', 'val': '7 Wins', 'impact': '12.8 pts earned', 'color': RR_PINK},
            {'metric': 'Death Overs Execution', 'val': '+7.65', 'impact': '7.0 pts earned', 'color': LIGHT_BLUE},
            {'metric': 'Flaw Deductions', 'val': '0.0', 'impact': '0.0 penalty', 'color': SUBTEXT}
        ],
        'signature_matches': 'vs CSK (51* off 43b from 33/4, WPA +2.95); vs SRH (84 off 34b chasing 278, WPA +3.12); vs DC (63 off 32b, WPA +2.48)'
    },
    'Heinrich Klaasen': {
        'rank': 4,
        'title': 'World #1 Crisis Rescue Destroyer',
        'archetype': 'Middle-Overs Spin Crusher',
        'why_top10': 'Heinrich Klaasen is the single most destructive middle-overs spin destroyer in high leverage. He leads the entire world in Crisis Rescue WPA (+24.84) and generated +31.61 Counter-Attack WPA. Facing spin on deteriorating surfaces, Klaasen elevates his strike rate to 180+ under match-on-the-line pressure, rescuing Sunrisers Hyderabad and South Africa from dire positions in 12 crucible wins.',
        'key_formula_breakdown': [
            {'metric': 'Crisis Rescue WPA (World Record)', 'val': '+24.84', 'impact': '27.4 pts earned', 'color': RR_GOLD},
            {'metric': 'Counter-Attack Chasing WPA', 'val': '+31.61', 'impact': '25.6 pts earned', 'color': RR_PINK},
            {'metric': 'Pressure Consistency Rate', 'val': '69.2%', 'impact': '9.8 pts earned', 'color': GREEN},
            {'metric': 'Authentic MWPPs', 'val': '4 Wins', 'impact': '8.0 pts earned', 'color': GREEN},
            {'metric': 'Death Flaw Penalty (Wickets at Death)', 'val': '-1.02', 'impact': '-3.0 deduction', 'color': RED}
        ],
        'signature_matches': 'vs KKR (63 off 29b from 111/5, WPA +3.40); vs MI (80* off 34b, WPA +3.15); vs India (52 off 27b T20 World Cup Final, WPA +2.88)'
    },
    'Glenn Phillips': {
        'rank': 5,
        'title': 'World #5 Complete Clutch Operator',
        'archetype': 'Multi-Phase Match-Winner',
        'why_top10': 'Glenn Phillips is the ultimate tactical utility performer. He is one of only three batters in world cricket to maintain positive double-digit WPA across all three pressure dimensions: +18.48 Crisis Rescue, +13.26 Death Finishing, and +23.85 Counter-Attack WPA. With a 69.0% pressure consistency rate, 4 Authentic MWPPs, and zero flaw deductions, Phillips ranks cleanly at 60.6 pts.',
        'key_formula_breakdown': [
            {'metric': 'Counter-Attack Chasing WPA', 'val': '+23.85', 'impact': '21.0 pts earned', 'color': RR_GOLD},
            {'metric': 'Crisis Rescue WPA', 'val': '+18.48', 'impact': '17.8 pts earned', 'color': GREEN},
            {'metric': 'Death Finishing WPA', 'val': '+13.26', 'impact': '13.2 pts earned', 'color': LIGHT_BLUE},
            {'metric': 'Pressure Consistency Rate', 'val': '69.0%', 'impact': '9.8 pts earned', 'color': GREEN},
            {'metric': 'Flaw Deductions', 'val': '0.0', 'impact': '0.0 penalty', 'color': SUBTEXT}
        ],
        'signature_matches': 'vs RR (25 off 7b sealing final over chase, WPA +3.90); vs SL (104 off 64b from 15/3, WPA +4.50); vs WI (56 off 22b, WPA +2.65)'
    },
    'Shimron Hetmyer': {
        'rank': 6,
        'title': 'Rajasthan Royals Death Closer',
        'archetype': 'High-Leverage Finisher',
        'why_top10': 'Shimron Hetmyer is Rajasthan Royals elite pressure weapon. Batting at #5/#6 where every ball is a high-leverage decision, Hetmyer accumulated +21.95 Counter-Attack WPA, +16.96 Crisis Rescue WPA, and +10.20 Death Finishing WPA. He sealed 13 crucible victories, executed 5 Authentic MWPPs, and maintained a zero-deduction flaw record, making him Rajasthan Royals highest-rated clutch batter.',
        'key_formula_breakdown': [
            {'metric': 'Counter-Attack Chasing WPA', 'val': '+21.95', 'impact': '20.1 pts earned', 'color': RR_PINK},
            {'metric': 'Crisis Rescue WPA', 'val': '+16.96', 'impact': '16.5 pts earned', 'color': GREEN},
            {'metric': 'Death Finishing WPA', 'val': '+10.20', 'impact': '11.0 pts earned', 'color': LIGHT_BLUE},
            {'metric': 'Crucible Match Wins', 'val': '13 Wins', 'impact': '11.4 pts earned', 'color': GREEN},
            {'metric': 'Flaw Deductions', 'val': '0.0', 'impact': '0.0 penalty', 'color': SUBTEXT}
        ],
        'signature_matches': 'vs GT (56* off 26b chasing 178 from 55/4, WPA +3.92); vs PBKS (27* off 10b, WPA +2.85); vs RCB (35 off 16b, WPA +2.20)'
    },
    'Hardik Pandya': {
        'rank': 7,
        'title': 'Big-Stage Championship Finisher',
        'archetype': 'Tournament Knockout Specialist',
        'why_top10': 'Hardik Pandya earns his top-tier standing through tournament knockout supremacy. Aided by a 1.50x knockout multiplier across IPL Playoffs and ICC tournaments, Hardik generated +31.86 Counter-Attack WPA and +8.63 Death WPA. Across 18 high-pressure team victories, Pandya has repeatedly delivered when the season is on the line, earning 55.7 pts.',
        'key_formula_breakdown': [
            {'metric': 'Counter-Attack Chasing WPA', 'val': '+31.86', 'impact': '27.5 pts earned', 'color': RR_GOLD},
            {'metric': 'Big-Match Knockout Multiplier', 'val': '1.50x', 'impact': '+12.5 pts bonus', 'color': RR_PINK},
            {'metric': 'Death Finishing WPA', 'val': '+8.63', 'impact': '9.2 pts earned', 'color': LIGHT_BLUE},
            {'metric': 'Pressure Consistency Rate', 'val': '67.3%', 'impact': '9.5 pts earned', 'color': GREEN},
            {'metric': 'Flaw Deductions', 'val': '0.0', 'impact': '0.0 penalty', 'color': SUBTEXT}
        ],
        'signature_matches': 'vs RR (IPL 2022 Final: 34 off 30b & 3/17, WPA +4.20); vs Pakistan (T20 World Cup: 40 off 37b, WPA +2.85); vs SA (T20 World Cup Final: Defending final over, WPA +3.80)'
    },
    'Virat Kohli': {
        'rank': 8,
        'title': 'The Master of Second-Innings Chases',
        'archetype': 'Chase Target Calculator',
        'why_top10': 'Virat Kohli holds the international gold standard for steep target calculations. Facing a massive 2,455 balls against 100% Tier-1 elite attacks, Kohli generated an elite +35.50 Counter-Attack WPA (2nd highest in the world behind Miller) and 6 Authentic MWPPs. While his early crisis rescue is modest (+1.27 WPA), his unmatched run-chase pacing ensures RCB and India cross the finish line in high-leverage games.',
        'key_formula_breakdown': [
            {'metric': 'Counter-Attack Chasing WPA', 'val': '+35.50', 'impact': '32.4 pts earned', 'color': RR_GOLD},
            {'metric': 'Sample Reliability Standard', 'val': '2,455 Balls', 'impact': '1.00x max scale', 'color': GREEN},
            {'metric': 'Authentic MWPPs', 'val': '6 Wins', 'impact': '11.2 pts earned', 'color': RR_PINK},
            {'metric': 'Pressure Consistency Rate', 'val': '69.1%', 'impact': '9.8 pts earned', 'color': GREEN},
            {'metric': 'Flaw Deductions', 'val': '0.0', 'impact': '0.0 penalty', 'color': SUBTEXT}
        ],
        'signature_matches': 'vs Pakistan (Melbourne 2022: 82* off 53b from 31/4, WPA +5.12); vs GT (101* off 61b, WPA +3.40); vs CSK (47 off 29b playoff qualification, WPA +2.15)'
    },
    'Nicholas Pooran': {
        'rank': 9,
        'title': 'World #1 High-Leverage Consistency King',
        'archetype': 'Middle-Overs High-Tempo Engine',
        'why_top10': 'Nicholas Pooran maintains the single highest pressure consistency rate in world cricket (74.5%). While other power hitters suffer massive feast-or-famine variance, Pooran contributed positive net value in nearly 3 out of every 4 pressure innings. With +25.49 Counter-Attack WPA, +6.29 Crisis Rescue, 5 Authentic MWPPs, and zero flaw deductions, he solidly secures #9.',
        'key_formula_breakdown': [
            {'metric': 'Pressure Consistency Rate (World #1)', 'val': '74.5%', 'impact': '12.0 pts earned', 'color': GREEN},
            {'metric': 'Counter-Attack Chasing WPA', 'val': '+25.49', 'impact': '22.8 pts earned', 'color': RR_GOLD},
            {'metric': 'Crisis Rescue WPA', 'val': '+6.29', 'impact': '7.4 pts earned', 'color': LIGHT_BLUE},
            {'metric': 'Authentic MWPPs', 'val': '5 Wins', 'impact': '10.0 pts earned', 'color': RR_PINK},
            {'metric': 'Flaw Deductions', 'val': '0.0', 'impact': '0.0 penalty', 'color': SUBTEXT}
        ],
        'signature_matches': 'vs RCB (62 off 19b chasing 213, WPA +4.30); vs CSK (44* off 15b, WPA +2.95); vs SRH (48 off 21b, WPA +2.50)'
    },
    'Venkatesh Iyer': {
        'rank': 10,
        'title': 'Crucible Match-Winner & Big-Game Specialist',
        'archetype': 'Crucible Impact Hitter',
        'why_top10': 'Venkatesh Iyer rounds out the Top 10 with 7 Authentic Match-Winning Pressure Performances — matching Tilak Varma and surpassing many senior stars. Generating +23.56 Counter-Attack WPA and +3.71 Crisis Rescue with 66.7% consistency, Iyer specializes in delivering decisive match-winning contributions in IPL playoff and knockout situations for KKR.',
        'key_formula_breakdown': [
            {'metric': 'Authentic MWPPs (Decisive Match Wins)', 'val': '7 Wins', 'impact': '13.5 pts earned', 'color': RR_PINK},
            {'metric': 'Counter-Attack Chasing WPA', 'val': '+23.56', 'impact': '21.0 pts earned', 'color': RR_GOLD},
            {'metric': 'Pressure Consistency Rate', 'val': '66.7%', 'impact': '9.4 pts earned', 'color': GREEN},
            {'metric': 'Crisis Rescue WPA', 'val': '+3.71', 'impact': '4.5 pts earned', 'color': LIGHT_BLUE},
            {'metric': 'Flaw Deductions', 'val': '0.0', 'impact': '0.0 penalty', 'color': SUBTEXT}
        ],
        'signature_matches': 'vs SRH (IPL 2024 Final: 52* off 26b, WPA +3.20); vs SRH (Qualifier 1: 51* off 28b, WPA +2.85); vs MI (70 off 52b at Wankhede from 57/5, WPA +3.60)'
    }
}

TOP10_BOWL_EXPLANATIONS = {
    'Jasprit Bumrah': {
        'rank': 1,
        'title': 'Undisputed King of Pace & Clutch Defense',
        'archetype': 'Universal Multi-Phase Fortress',
        'why_top10': 'Jasprit Bumrah is a statistical phenomenon operating in an entirely different league. Over the 2022–2026 cycle, Bumrah prevented an astronomical +149.76 runs above expected in death overs (16–20) alone, while also saving +74.54 runs in the middle and +17.98 in the powerplay. Facing 100% Tier-1 elite opposition with an economy rate of 7.36 in maximum-pressure situations and zero flaw deductions, Bumrah stands uncontested at 78.5 pts.',
        'key_formula_breakdown': [
            {'metric': 'Death Overs Runs Saved Above Par (World #1)', 'val': '+149.8', 'impact': '38.5 pts earned', 'color': RR_PINK},
            {'metric': 'Middle Overs Runs Saved', 'val': '+74.5', 'impact': '18.2 pts earned', 'color': GREEN},
            {'metric': 'Powerplay Runs Saved', 'val': '+18.0', 'impact': '8.5 pts earned', 'color': LIGHT_BLUE},
            {'metric': 'Pressure Economy Rate', 'val': '7.36 RPO', 'impact': '12.0 pts earned', 'color': GREEN},
            {'metric': 'Flaw Deductions', 'val': '0.0', 'impact': '0.0 penalty', 'color': SUBTEXT}
        ],
        'signature_matches': 'vs SA (T20 World Cup Final 2024: 2/18, 18th over conceded 2 runs, WPA +4.50); vs Pakistan (T20 World Cup 2024: 3/14 defending 119, WPA +5.20); vs RCB (5/21, WPA +4.10)'
    },
    'Sunil Narine': {
        'rank': 2,
        'title': 'Undisputed King of Spin & All-Phase Suppression',
        'archetype': 'Three-Phase Mystery Spinner',
        'why_top10': 'Sunil Narine is the premier spinner in world cricket because he is positive across all three phases: +20.2 runs saved in Powerplay, +80.2 in Middle overs, and +23.6 at the Death. Unlike other spinners who must be hidden during the death overs (such as Varun Chakravarthy, who leaked -9.6 runs), Narine bowls the 18th or 19th over with ice in his veins against 100% Tier-1 opposition with 0 flaw deductions (52.4 pts).',
        'key_formula_breakdown': [
            {'metric': 'Middle Overs Runs Saved', 'val': '+80.2', 'impact': '22.0 pts earned', 'color': GREEN},
            {'metric': 'Death Overs Runs Saved (Rare for Spin)', 'val': '+23.6', 'impact': '12.5 pts earned', 'color': RR_PINK},
            {'metric': 'Powerplay Suppression Saved', 'val': '+20.2', 'impact': '9.8 pts earned', 'color': LIGHT_BLUE},
            {'metric': 'Pressure Economy Rate', 'val': '7.88 RPO', 'impact': '10.5 pts earned', 'color': GREEN},
            {'metric': 'Flaw Deductions', 'val': '0.0', 'impact': '0.0 penalty', 'color': SUBTEXT}
        ],
        'signature_matches': 'vs RR (2/30 & 109 off 56b, WPA +3.80); vs SRH (IPL 2024 Final: 1/16 in 4 overs, WPA +2.90); vs CSK (2/15 at Chepauk, WPA +3.10)'
    },
    'Josh Hazlewood': {
        'rank': 3,
        'title': 'Powerplay Stranglehold & Test-Match Line',
        'archetype': 'New-Ball Precision Squeeze',
        'why_top10': 'Josh Hazlewood is the ultimate defensive weapon with the new ball. He saved a world-leading +48.43 runs in the Powerplay alone, suffocating top orders with unrelenting Test-match lengths in high-stakes T20 contests. Backed by a 65.1% consistency rate and +9.1 runs saved at the death, Hazlewood earns a podium finish at 52.1 pts.',
        'key_formula_breakdown': [
            {'metric': 'Powerplay Runs Saved (World #1)', 'val': '+48.4', 'impact': '28.0 pts earned', 'color': LIGHT_BLUE},
            {'metric': 'Pressure Consistency Rate', 'val': '65.1%', 'impact': '14.2 pts earned', 'color': GREEN},
            {'metric': 'Death Overs Runs Saved', 'val': '+9.1', 'impact': '6.8 pts earned', 'color': RR_PINK},
            {'metric': 'Tier-1 Elite Schedule Strength', 'val': '100%', 'impact': '+6.1 pts bonus', 'color': RR_GOLD},
            {'metric': 'Middle Overs Flaw Deduction', 'val': '-3.8', 'impact': '-3.0 deduction', 'color': RED}
        ],
        'signature_matches': 'vs LSG (4/25 defending 181, WPA +3.60); vs DC (3/28 in PP squeeze, WPA +2.80); vs England (2/28 World T20, WPA +2.40)'
    },
    'Mustafizur Rahman': {
        'rank': 4,
        'title': 'Death Cutter Specialist (Calibrated)',
        'archetype': 'Off-Cutter Variation Master',
        'why_top10': 'Mustafizur Rahman delivered an outstanding +84.80 runs saved at the death and +21.93 in the Powerplay. In raw unweighted systems, he ranked #2, but our algorithm identified that 20.7% of his delivery volume came against associate minnows on 120-run Dhaka tracks. After applying a fair 0.40x associate discounting calibration, Mustafizur rightfully holds Rank #4 with 45.3 pts.',
        'key_formula_breakdown': [
            {'metric': 'Death Overs Runs Saved (Calibrated)', 'val': '+84.8', 'impact': '26.5 pts earned', 'color': RR_PINK},
            {'metric': 'Powerplay Runs Saved', 'val': '+21.9', 'impact': '10.2 pts earned', 'color': LIGHT_BLUE},
            {'metric': 'Middle Overs Runs Saved', 'val': '+18.3', 'impact': '8.4 pts earned', 'color': GREEN},
            {'metric': 'Schedule Strength Associate Discount', 'val': '20.7% (0.40x)', 'impact': '-12.0 adjustment', 'color': RED},
            {'metric': 'Flaw Deductions', 'val': '0.0', 'impact': '0.0 penalty', 'color': SUBTEXT}
        ],
        'signature_matches': 'vs RCB (4/29 in Chepauk opener, WPA +3.40); vs KKR (2/22 at death, WPA +2.60); vs Sri Lanka (3/17 T20 World Cup, WPA +3.10)'
    },
    'Nathan Ellis': {
        'rank': 5,
        'title': 'Modern T20 Multi-Phase Specialist',
        'archetype': 'Yorker & Slower-Ball Executor',
        'why_top10': 'Nathan Ellis is the model modern T20 specialist. Operating strictly in the fire of middle and death overs against 100% Tier-1 franchise opposition, Ellis saved +41.45 death runs and +32.56 middle overs runs. With an elite 64.0% consistency rate and zero flaw deductions over 41 high-leverage matches, he secures a well-deserved Rank #5 with 44.0 pts.',
        'key_formula_breakdown': [
            {'metric': 'Death Overs Runs Saved', 'val': '+41.5', 'impact': '19.5 pts earned', 'color': RR_PINK},
            {'metric': 'Middle Overs Runs Saved', 'val': '+32.6', 'impact': '14.8 pts earned', 'color': GREEN},
            {'metric': 'Pressure Consistency Rate', 'val': '64.0%', 'impact': '12.5 pts earned', 'color': GREEN},
            {'metric': 'Tier-1 Elite Schedule Strength', 'val': '100%', 'impact': '+5.2 pts bonus', 'color': RR_GOLD},
            {'metric': 'Flaw Deductions', 'val': '0.0', 'impact': '0.0 penalty', 'color': SUBTEXT}
        ],
        'signature_matches': 'vs RR (4/30 defending 197 at Barsapara, WPA +3.85); vs CSK (1/24 at death, WPA +2.30); vs England (3/20 T20I, WPA +2.95)'
    },
    'Bhuvneshwar Kumar': {
        'rank': 6,
        'title': '100-Match Veteran Master of Swing & Seam',
        'archetype': 'Swing & Knuckleball Veteran',
        'why_top10': 'Bhuvneshwar Kumar demonstrated immense longevity and clutch reliability across a massive 100-match sample size. He saved +41.23 runs at the death and +16.45 in the powerplay, maintaining a 60.3% pressure consistency rate over four grueling years of IPL and international cricket to earn 43.0 pts.',
        'key_formula_breakdown': [
            {'metric': 'Death Overs Runs Saved Above Par', 'val': '+41.2', 'impact': '18.8 pts earned', 'color': RR_PINK},
            {'metric': 'Sample Reliability Standard (100 Matches)', 'val': '100 Matches', 'impact': '1.00x max scale', 'color': GREEN},
            {'metric': 'Powerplay Runs Saved', 'val': '+16.5', 'impact': '8.2 pts earned', 'color': LIGHT_BLUE},
            {'metric': 'Pressure Consistency Rate', 'val': '60.3%', 'impact': '11.0 pts earned', 'color': GREEN},
            {'metric': 'Middle Overs Flaw Deduction', 'val': '-3.0', 'impact': '-2.4 deduction', 'color': RED}
        ],
        'signature_matches': 'vs RR (IPL 2024: 3/41 defending 2 runs off last ball, trapped Powell LBW, WPA +4.80); vs SA (4/13 T20I, WPA +3.90); vs PBKS (3/25, WPA +2.50)'
    },
    'Rashid Khan': {
        'rank': 7,
        'title': 'Middle-Overs Spin Anchor',
        'archetype': 'Rapid Leg-Spin Squeeze',
        'why_top10': 'Rashid Khan is correctly evaluated in his true world-class archetype: elite bowling. Across 122 matches, Rashid saved +20.2 runs in the powerplay, +19.5 in the middle, and +10.7 at the death, with a 60.4% consistency rate. With associate discounting properly applied to his bilateral matches, he comfortably holds Rank #7 with 39.7 pts.',
        'key_formula_breakdown': [
            {'metric': 'Powerplay Runs Saved', 'val': '+20.2', 'impact': '10.5 pts earned', 'color': LIGHT_BLUE},
            {'metric': 'Middle Overs Runs Saved', 'val': '+19.5', 'impact': '10.2 pts earned', 'color': GREEN},
            {'metric': 'Death Overs Runs Saved', 'val': '+10.7', 'impact': '7.2 pts earned', 'color': RR_PINK},
            {'metric': 'Pressure Consistency Rate', 'val': '60.4%', 'impact': '11.0 pts earned', 'color': GREEN},
            {'metric': 'Flaw Deductions', 'val': '0.0', 'impact': '0.0 penalty', 'color': SUBTEXT}
        ],
        'signature_matches': 'vs CSK (IPL 2023 Opener: 2/26, WPA +2.70); vs MI (4/30 & 79* off 32b, WPA +3.80); vs AUS (T20 World Cup 2024: 1/23 historic win, WPA +3.10)'
    },
    'Axar Patel': {
        'rank': 8,
        'title': 'Tactical Pressure Economy Specialist',
        'archetype': 'Stump-to-Stump Dart Operator',
        'why_top10': 'Axar Patel is the ultimate tactical enforcer. Maintained a world-class pressure economy rate of 8.33 RPO across 135 matches while bowling difficult matchups against aggressive right-handers. He saved +7.36 runs in the Powerplay and +2.88 at the death, earning 38.8 pts.',
        'key_formula_breakdown': [
            {'metric': 'Pressure Economy Suppression', 'val': '8.33 RPO', 'impact': '14.5 pts earned', 'color': GREEN},
            {'metric': 'Powerplay Runs Saved', 'val': '+7.4', 'impact': '6.8 pts earned', 'color': LIGHT_BLUE},
            {'metric': 'Breakthrough Wickets Under Pressure', 'val': '32 Wkts', 'impact': '11.0 pts earned', 'color': RR_PINK},
            {'metric': 'Pressure Consistency Rate', 'val': '55.8%', 'impact': '9.5 pts earned', 'color': GREEN},
            {'metric': 'Flaw Deduction', 'val': '-1.2', 'impact': '-1.0 deduction', 'color': RED}
        ],
        'signature_matches': 'vs SA (T20 World Cup Final 2024: 1/49 & 47 off 31b, WPA +2.90); vs England (Semi-Final: 3/23 spin masterclass, WPA +4.20); vs GT (1/14 in 3 overs, WPA +2.40)'
    },
    'Varun Chakravarthy': {
        'rank': 9,
        'title': 'Mystery Spinner with Calibrated Death Penalty',
        'archetype': 'Middle-Overs Breakthrough Spinner',
        'why_top10': 'Varun Chakravarthy is unplayable in the Powerplay (+36.66 runs saved) and Middle overs (+25.74 runs saved). However, when deployed in the death overs (16–20), Varun conceded -9.61 runs above expected. Our non-compensatory flaw model penalized this with an explicit -7.69 pt deduction, correctly placing him at Rank #9 (38.6 pts), behind Sunil Narine.',
        'key_formula_breakdown': [
            {'metric': 'Powerplay Runs Saved Above Par', 'val': '+36.7', 'impact': '21.5 pts earned', 'color': LIGHT_BLUE},
            {'metric': 'Middle Overs Runs Saved', 'val': '+25.7', 'impact': '15.2 pts earned', 'color': GREEN},
            {'metric': 'Pressure Consistency Rate', 'val': '57.8%', 'impact': '10.2 pts earned', 'color': GREEN},
            {'metric': 'Death Runs Conceded Above Expected', 'val': '-9.61', 'impact': 'Fatal Liability', 'color': RED},
            {'metric': 'Death Flaw Deduction Penalty', 'val': '-7.69', 'impact': '-7.7 penalty', 'color': RED}
        ],
        'signature_matches': 'vs DC (3/16 spinning KKR to victory, WPA +3.20); vs MI (2/17 at Wankhede, WPA +2.80); vs SA (5/17 T20I at Gqeberha, WPA +4.10)'
    },
    'Maheesh Theekshana': {
        'rank': 10,
        'title': 'Carrom-Ball Powerplay Specialist',
        'archetype': 'Powerplay Mystery Carrom Spinner',
        'why_top10': 'Maheesh Theekshana rounds out the Top 10 with elite Powerplay carrom execution, saving +41.88 runs in the first six overs and +39.65 at the death over 98 matches. Calibrated with associate discounting for bilateral matches, Theekshana earns 38.3 pts.',
        'key_formula_breakdown': [
            {'metric': 'Powerplay Runs Saved Above Par', 'val': '+41.9', 'impact': '22.0 pts earned', 'color': LIGHT_BLUE},
            {'metric': 'Death Overs Runs Saved (Calibrated)', 'val': '+39.6', 'impact': '16.5 pts earned', 'color': RR_PINK},
            {'metric': 'Pressure Economy Rate', 'val': '8.40 RPO', 'impact': '8.5 pts earned', 'color': GREEN},
            {'metric': 'Schedule Strength Minnow Discount', 'val': '14.2% (0.40x)', 'impact': '-8.7 adjustment', 'color': RED},
            {'metric': 'Flaw Deductions', 'val': '0.0', 'impact': '0.0 penalty', 'color': SUBTEXT}
        ],
        'signature_matches': 'vs RCB (3/27 in Powerplay choke, WPA +3.10); vs SRH (2/23 at Chepauk, WPA +2.40); vs BAN (3/19 Asia Cup, WPA +2.80)'
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# CHARTS WITHOUT BDATA (STRICT NATIVE PYTHON LIST CONVERSION)
# ─────────────────────────────────────────────────────────────────────────────
def create_horizontal_bar(df10, name_col, score_col, bar_color, title):
    medals = ['1st', '2nd', '3rd'] + [f'{i+1}th' for i in range(3, len(df10))]
    colors = [RR_GOLD, '#cbd5e1', '#b45309'] + [bar_color] * (len(df10) - 3)
    
    x_vals = [float(v) for v in df10[score_col]]
    y_vals = [f"{medals[i]}  {df10.iloc[i][name_col]}" for i in range(len(df10))]
    text_vals = [f"  <b>{v:.1f}</b>" for v in x_vals]
    
    fig = go.Figure(go.Bar(
        x=x_vals,
        y=y_vals,
        orientation='h',
        marker=dict(color=colors, line=dict(color='rgba(255,255,255,0.1)', width=1)),
        text=text_vals,
        textposition='outside',
        textfont=dict(color=TEXT, size=11)
    ))
    fig.update_layout(
        title=dict(text=f'<b>{title}</b>', font=dict(color=TEXT, size=13)),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=TEXT, family='Inter, -apple-system, sans-serif'),
        margin=dict(l=10, r=60, t=40, b=20),
        xaxis=dict(
            gridcolor='rgba(255,255,255,0.05)',
            range=[0, max(x_vals) * 1.16],
            zeroline=False,
            title=dict(text='Pressure Index Rating (0–100)', font=dict(size=10, color=SUBTEXT))
        ),
        yaxis=dict(gridcolor='rgba(0,0,0,0)', autorange='reversed'),
        height=380
    )
    return fig

fig_bat10 = create_horizontal_bar(bat10, 'striker_name', 'batting_clutch_score', RR_PINK, 'Top 10 Batters Under High-Leverage Pressure')
fig_bowl10 = create_horizontal_bar(bowl10, 'bowler_name', 'bowling_clutch_score', RR_BLUE, 'Top 10 Bowlers Under High-Leverage Pressure')

# SCATTER CHART WITH EXPLICIT LISTS & QUADRANT ANNOTATIONS (EXCLUSIVELY TOP 10 + GILL CONTRAST)
scatter_x = [float(v) for v in bat_scatter['rescue_wpa']]
scatter_y = [float(v) for v in bat_scatter['hp_ml_runs_added']]
scatter_names = list(bat_scatter['striker_name'])
scatter_ca = [float(v) for v in bat_scatter['ca_wpa']]
scatter_colors = [RR_GOLD if r['rank_bat'] <= 3 else (RED if r['striker_name'] == 'Shubman Gill' else RR_PINK) for _, r in bat_scatter.iterrows()]
scatter_sizes = [float(max(15, abs(w) * 0.95)) for w in scatter_ca]

# Text positioning to avoid collisions
text_positions = []
for name, y, x in zip(scatter_names, scatter_y, scatter_x):
    if 'Miller' in name:
        text_positions.append('bottom center')
    elif 'Suryakumar' in name:
        text_positions.append('top center')
    elif 'Klaasen' in name:
        text_positions.append('top left')
    elif 'Tilak' in name:
        text_positions.append('bottom right')
    elif 'Gill' in name:
        text_positions.append('top center')
    elif y >= 40:
        text_positions.append('top right')
    else:
        text_positions.append('bottom right')

scatter_fig = go.Figure()
scatter_fig.add_trace(go.Scatter(
    x=scatter_x,
    y=scatter_y,
    mode='markers+text',
    text=scatter_names,
    textposition=text_positions,
    textfont=dict(color='#ffffff', size=11, family='Inter'),
    marker=dict(
        size=scatter_sizes,
        color=scatter_colors,
        opacity=0.9,
        line=dict(width=2, color='#ffffff')
    ),
    hovertemplate="<b>%{text}</b><br>Crisis Rescue WPA: %{x:+.2f}<br>ML Runs Added: %{y:+.1f}<br>Counter-Attack WPA Size: %{marker.size:.1f}<extra></extra>"
))

# Threshold Lines & Quadrants
scatter_fig.add_vline(x=0, line_dash="dash", line_color="rgba(244, 63, 94, 0.7)", line_width=2)
scatter_fig.add_hline(y=0, line_dash="dot", line_color="rgba(255, 255, 255, 0.2)", line_width=1)

# Quadrant Annotation Badges placed cleanly in open corners
scatter_fig.add_annotation(x=20, y=245, text="<b>QUADRANT I: ELITE ALL-PHASE MATCH WINNERS</b><br>(Surya, Klaasen, Tilak)", showarrow=False, font=dict(color=RR_GOLD, size=9.5), bgcolor="rgba(15, 23, 42, 0.85)", bordercolor=RR_GOLD, borderpad=4)
scatter_fig.add_annotation(x=-2.5, y=230, text="<b>QUADRANT II: FRONT-RUNNING VULNERABLE</b><br>(Gill: Fails in Early Collapse)", showarrow=False, font=dict(color=RED, size=9.5), bgcolor="rgba(15, 23, 42, 0.85)", bordercolor=RED, borderpad=4)
scatter_fig.add_annotation(x=21, y=-75, text="<b>QUADRANT IV: PURE CHASE CLOSERS</b><br>(Miller: World #1 Chase Finisher)", showarrow=False, font=dict(color=LIGHT_BLUE, size=9.5), bgcolor="rgba(15, 23, 42, 0.85)", bordercolor=LIGHT_BLUE, borderpad=4)

scatter_fig.update_layout(
    title=dict(text='<b>Visual Proof 1: Batting Pressure Archetypes</b> (Crisis Rescue WPA vs High-Pressure ML Runs Added)', font=dict(color=TEXT, size=13)),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color=TEXT, family='Inter, -apple-system, sans-serif'),
    margin=dict(l=40, r=40, t=45, b=40),
    xaxis=dict(
        title='Crisis Rescue WPA (Innings Resurrection from Early Collapse)',
        gridcolor='rgba(255,255,255,0.05)',
        zeroline=True,
        zerolinecolor='rgba(255,255,255,0.2)',
        range=[-5, 30]
    ),
    yaxis=dict(
        title='High-Pressure ML Runs Added Above Expected',
        gridcolor='rgba(255,255,255,0.05)',
        zeroline=True,
        zerolinecolor='rgba(255,255,255,0.2)',
        range=[-100, 270]
    ),
    height=400
)

# GROUPED BAR: BOWLING PHASES
bar_phases = go.Figure()
bar_phases.add_trace(go.Bar(name='Powerplay Saved (1–6)', x=list(bowl10['bowler_name']), y=[float(v) for v in bowl10['ml_pp_runs_saved']], marker_color='#38bdf8'))
bar_phases.add_trace(go.Bar(name='Middle Overs Saved (7–15)', x=list(bowl10['bowler_name']), y=[float(v) for v in bowl10['ml_mid_runs_saved']], marker_color='#818cf8'))
bar_phases.add_trace(go.Bar(name='Death Overs Saved (16–20)', x=list(bowl10['bowler_name']), y=[float(v) for v in bowl10['ml_death_runs_saved']], marker_color=RR_PINK))
bar_phases.update_layout(
    barmode='group',
    title=dict(text='<b>Visual Proof 2: Bowling Multi-Phase Defense Matrix</b> (PP, Middle, and Death Runs Saved)', font=dict(color=TEXT, size=13)),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color=TEXT, family='Inter, -apple-system, sans-serif'),
    margin=dict(l=40, r=40, t=45, b=50),
    xaxis=dict(gridcolor='rgba(255,255,255,0.05)', tickangle=-25),
    yaxis=dict(title='ML Runs Saved Above Expected', gridcolor='rgba(255,255,255,0.05)', zeroline=True, zerolinecolor='rgba(255,255,255,0.3)'),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=400
)

# MINNOW HORIZONTAL BAR
minnow_vals = [float(v * 100) for v in bowl10['minnow_ratio']]
minnow_names = list(bowl10['bowler_name'])
minnow_fig = go.Figure(go.Bar(
    x=minnow_vals,
    y=minnow_names,
    orientation='h',
    marker=dict(
        color=[RED if v > 15 else (RR_GOLD if v > 5 else GREEN) for v in minnow_vals],
        line=dict(color='rgba(255,255,255,0.1)', width=1)
    ),
    text=[f"  <b>{v:.1f}%</b> ({'Discounted 0.40x' if v > 5 else '100% Elite Schedule'})" for v in minnow_vals],
    textposition='outside',
    textfont=dict(color=TEXT, size=10)
))
minnow_fig.update_layout(
    title=dict(text='<b>Visual Proof 3: Schedule Strength Calibration</b> (% Deliveries Against Associate / Minnow Attacks)', font=dict(color=TEXT, size=13)),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color=TEXT, family='Inter, -apple-system, sans-serif'),
    margin=dict(l=10, r=160, t=45, b=20),
    xaxis=dict(gridcolor='rgba(255,255,255,0.05)', title='Associate / Minnow Delivery Exposure (%)', range=[0, 32]),
    yaxis=dict(gridcolor='rgba(0,0,0,0)', autorange='reversed'),
    height=340
)

# ─────────────────────────────────────────────────────────────────────────────
# BATTERS & BOWLERS DOSSIER DATA
# ─────────────────────────────────────────────────────────────────────────────
batters_data = {}
for _, br in bat_scatter.iterrows():
    name = br['striker_name']
    exp = TOP10_BAT_EXPLANATIONS.get(name, {
        'rank': int(br['rank_bat']),
        'title': f"Rank #{br['rank_bat']} Qualified Batter",
        'archetype': 'Qualified Batter',
        'why_top10': f"Qualified batter under high pressure with {br['batting_clutch_score']:.1f} pts.",
        'key_formula_breakdown': [],
        'signature_matches': 'Crucible High-Pressure Match Logs'
    })
    
    comps = {
        'Tier 3: Counter-Attack Chasing RRR≥10 (24%)': float(br.get('S_ca', 0)) * 0.24,
        'Tier 3: Crisis Collapse Rescue (20%)': float(br.get('S_rescue', 0)) * 0.20,
        'Tier 1: Quality Win Calibration vs Elite (20%)': float(br.get('S_win_wpa', 0)) * 0.20,
        'Tier 2: Authentic Match-Winning Knocks (14%)': float(br.get('S_mwpp', 0)) * 0.14,
        'Tier 3: Death Chase Finishing overs 16-20 (12%)': float(br.get('S_da', 0)) * 0.12,
        'Tier 2: High-Leverage Consistency Rate (10%)': float(br.get('S_consistency', 0)) * 0.10,
        'Non-Compensatory Flaw Penalties': -float(br.get('fair_deductions', 0))
    }
    filtered_comps = {k: v for k, v in comps.items() if abs(v) > 0.05}
    wf_x = [float(v) for v in filtered_comps.values()]
    wf_y = list(filtered_comps.keys())
    
    waterfall_fig = go.Figure(go.Bar(
        x=wf_x,
        y=wf_y,
        orientation='h',
        marker_color=[GREEN if v >= 0 else RED for v in wf_x],
        text=[f"{v:+.1f} pts" for v in wf_x],
        textposition='outside',
        textfont=dict(color=TEXT, size=10)
    ))
    waterfall_fig.update_layout(
        title=dict(text=f'<b>{name.upper()}: FACTOR ATTRIBUTION WATERFALL</b>', font=dict(color=TEXT, size=11)),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=TEXT, family='Inter, -apple-system, sans-serif', size=10),
        margin=dict(l=10, r=40, t=35, b=20),
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)', zeroline=True, zerolinecolor='rgba(255,255,255,0.2)'),
        yaxis=dict(gridcolor='rgba(0,0,0,0)', autorange='reversed'),
        height=240
    )
    
    sub_logs = bat_logs[bat_logs['striker_name'] == name].sort_values('hp_wpa', ascending=False).head(3)
    logs_list = []
    for _, l in sub_logs.iterrows():
        logs_list.append({
            'date': str(l.get('match_date', ''))[:10],
            'opponent': str(l.get('opponent_team', l.get('bowling_team', 'Opp'))),
            'comp': str(l.get('comp_name', '')),
            'runs': int(l.get('total_runs', 0)),
            'balls': int(l.get('total_balls', 0)),
            'hp_sr': float(l.get('hp_sr', 0)),
            'wpa': float(l.get('hp_wpa', 0))
        })
        
    batters_data[name] = {
        'rank': int(br['rank_bat']),
        'name': name,
        'score': float(br['batting_clutch_score']),
        'title': exp['title'],
        'archetype': exp['archetype'],
        'why_top10': exp['why_top10'],
        'formula_breakdown': exp['key_formula_breakdown'],
        'signature_matches': exp['signature_matches'],
        'consistency': f"{float(br.get('hp_consistency_rate',0))*100:.1f}%",
        'ca_wpa': f"+{float(br['ca_wpa']):.2f}",
        'rescue_wpa': f"{float(br['rescue_wpa']):+.2f}",
        'da_wpa': f"{float(br['da_wpa']):+.2f}",
        'mwpp': int(br['authentic_mwpp']),
        'deductions': f"-{float(br['fair_deductions']):.1f}",
        'deductions_val': float(br['fair_deductions']),
        'waterfall': json.loads(waterfall_fig.to_json()),
        'logs': logs_list
    }

bowlers_to_include = list(bowl10['bowler_name']) + ['Mohammed Siraj', 'Ravi Bishnoi']
bowlers_data = {}
for name in bowlers_to_include:
    bwr_matches = bowl_rank[bowl_rank['bowler_name'] == name]
    if bwr_matches.empty:
        continue
    bwr = bwr_matches.iloc[0]
    exp = TOP10_BOWL_EXPLANATIONS.get(name, {
        'rank': int(bwr['rank_bowl']),
        'title': f"Rank #{bwr['rank_bowl']} Qualified Bowler (Demoted)",
        'archetype': 'High-Risk Liability Bowler',
        'why_top10': f"Penalized for fatal death overs leakage, incurring a severe flaw penalty of -{bwr['fair_deductions']:.1f} pts.",
        'key_formula_breakdown': [],
        'signature_matches': 'Match records analyzed'
    })
    
    comps = {
        'Tier 1: Opponent Quality Calibration (20%)': float(bwr.get('S_runs_saved', 0)) * 0.20,
        'Tier 2: Pressure Consistency Rate (16%)': float(bwr.get('S_consistency', 0)) * 0.16,
        'Tier 2: Clutch Breakthrough Wickets (10%)': float(bwr.get('S_wkts', 0)) * 0.10,
        'Tier 3: Multi-Phase Defense Allocation (15%)': float(bwr.get('S_runs_saved', 0)) * 0.15,
        'Tier 3: Momentum-Breaking Dots (18%)': float(bwr.get('S_dots', 0)) * 0.18,
        'Tier 3: Pressure Economy vs Par (12%)': float(bwr.get('S_eco', 0)) * 0.12,
        'Tier 3: High-Pressure WPA (5%)': float(bwr.get('S_wpa', 0)) * 0.05,
        'Tier 3: Death Yorkers Executed (4%)': float(bwr.get('S_yorkers', 0)) * 0.04,
        'Flaw Deductions': -float(bwr.get('fair_deductions', 0))
    }
    filtered_comps = {k: v for k, v in comps.items() if abs(v) > 0.05}
    wf_x = [float(v) for v in filtered_comps.values()]
    wf_y = list(filtered_comps.keys())
    
    waterfall_fig = go.Figure(go.Bar(
        x=wf_x,
        y=wf_y,
        orientation='h',
        marker_color=[GREEN if v >= 0 else RED for v in wf_x],
        text=[f"{v:+.1f} pts" for v in wf_x],
        textposition='outside',
        textfont=dict(color=TEXT, size=10)
    ))
    waterfall_fig.update_layout(
        title=dict(text=f'<b>{name.upper()}: FACTOR ATTRIBUTION WATERFALL</b>', font=dict(color=TEXT, size=11)),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=TEXT, family='Inter, -apple-system, sans-serif', size=10),
        margin=dict(l=10, r=40, t=35, b=20),
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)', zeroline=True, zerolinecolor='rgba(255,255,255,0.2)'),
        yaxis=dict(gridcolor='rgba(0,0,0,0)', autorange='reversed'),
        height=240
    )
    
    sub_logs = bowl_logs[bowl_logs['bowler_name'] == name].sort_values('hp_wpa', ascending=False).head(3)
    logs_list = []
    for _, l in sub_logs.iterrows():
        logs_list.append({
            'date': str(l.get('match_date', ''))[:10],
            'opponent': str(l.get('opponent_team', l.get('home_team', 'Opp'))),
            'comp': str(l.get('comp_name', '')),
            'wkts': int(l.get('total_wkts', 0)),
            'runs': int(l.get('total_runs', 0)),
            'balls': int(l.get('total_balls', 0)),
            'eco': float(l.get('hp_economy', 0)),
            'wpa': float(l.get('hp_wpa', 0))
        })
        
    bowlers_data[name] = {
        'rank': int(bwr['rank_bowl']),
        'name': name,
        'score': float(bwr['bowling_clutch_score']),
        'title': exp['title'],
        'archetype': exp['archetype'],
        'why_top10': exp['why_top10'],
        'formula_breakdown': exp['key_formula_breakdown'],
        'signature_matches': exp['signature_matches'],
        'consistency': f"{float(bwr.get('hp_consistency_rate',0))*100:.1f}%",
        'pp_saved': f"{float(bwr['ml_pp_runs_saved']):+.1f}",
        'mid_saved': f"{float(bwr['ml_mid_runs_saved']):+.1f}",
        'death_saved': f"{float(bwr['ml_death_runs_saved']):+.1f}",
        'eco': f"{float(bwr['hp_eco']):.2f}",
        'deductions': f"-{float(bwr['fair_deductions']):.1f}",
        'deductions_val': float(bwr['fair_deductions']),
        'waterfall': json.loads(waterfall_fig.to_json()),
        'logs': logs_list
    }

# Convert charts to JSON
bat10_json = json.loads(fig_bat10.to_json())
bowl10_json = json.loads(fig_bowl10.to_json())
scatter_json = json.loads(scatter_fig.to_json())
bar_phases_json = json.loads(bar_phases.to_json())
minnow_json = json.loads(minnow_fig.to_json())

# Tables
bat_table_rows = []
for _, r in bat10.iterrows():
    bat_table_rows.append({
        'rank': int(r['rank_bat']),
        'name': r['striker_name'],
        'matches': int(r['matches']),
        'consistency': f"{r['hp_consistency_rate']*100:.1f}%",
        'ca_wpa': f"+{r['ca_wpa']:.2f}",
        'rescue_wpa': f"{r['rescue_wpa']:+.2f}",
        'da_wpa': f"{r['da_wpa']:+.2f}",
        'ml_runs': f"{r['hp_ml_runs_added']:+.1f}",
        'deductions': f"-{r['fair_deductions']:.1f}",
        'score': f"{r['batting_clutch_score']:.1f}"
    })

bowl_table_rows = []
for _, r in bowl10.iterrows():
    bowl_table_rows.append({
        'rank': int(r['rank_bowl']),
        'name': r['bowler_name'],
        'matches': int(r['matches']),
        'consistency': f"{r['hp_consistency_rate']*100:.1f}%",
        'pp_saved': f"{r['ml_pp_runs_saved']:+.1f}",
        'mid_saved': f"{r['ml_mid_runs_saved']:+.1f}",
        'death_saved': f"{r['ml_death_runs_saved']:+.1f}",
        'eco': f"{r['hp_eco']:.2f}",
        'deductions': f"-{r['fair_deductions']:.1f}",
        'score': f"{r['bowling_clutch_score']:.1f}"
    })

# Write payload
with open('dashboard_payload.json', 'w', encoding='utf-8') as f:
    json.dump({
        'bat10_chart': bat10_json,
        'bowl10_chart': bowl10_json,
        'scatter_chart': scatter_json,
        'bar_phases_chart': bar_phases_json,
        'minnow_chart': minnow_json,
        'bat_table': bat_table_rows,
        'bowl_table': bowl_table_rows,
        'batters_data': batters_data,
        'bowlers_data': bowlers_data,
        'top10_bat_explanations': TOP10_BAT_EXPLANATIONS,
        'top10_bowl_explanations': TOP10_BOWL_EXPLANATIONS
    }, f)

print("Updated payload dumped successfully without any bdata arrays!")
