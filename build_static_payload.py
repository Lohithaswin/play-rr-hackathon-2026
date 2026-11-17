import json
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio

# Colors
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

print("Loading parquets...")
bat_rank = pd.read_parquet('bat_rankings_final.parquet')
bowl_rank = pd.read_parquet('bowl_rankings_final.parquet')
bat_logs = pd.read_parquet('bat_hp_match_logs.parquet')
bowl_logs = pd.read_parquet('bowl_hp_match_logs.parquet')

bat10 = bat_rank.head(10).reset_index(drop=True)
bowl10 = bowl_rank.head(10).reset_index(drop=True)
bat12 = bat_rank.head(12).reset_index(drop=True)

# Dossier Analytical Justifications
BAT_PROOFS = {
    'David Miller': {
        'badge': 'World #1 Match-Winning Chase Finisher',
        'desc': 'World #1 Match-on-the-Line Clutch Performer (80.2 pts). Generates an unprecedented +42.27 Counter-Attack WPA in steep chases (RRR >= 10.0) and +17.65 Death WPA, with 8 Authentic MWPPs, 15 win matches, and zero flaw deductions.',
        'highlight_stat': '80.2 pts',
        'highlight_lbl': 'World #1 Clutch Score'
    },
    'Suryakumar Yadav': {
        'badge': 'World #2 All-Phase Pressure Force',
        'desc': 'World #2 Clutch Performer (74.0 pts). Elite dual-threat profile combining +29.37 Counter-Attack WPA, +20.12 Crisis Rescue WPA from early collapses, 8 Authentic MWPPs, 20 high-leverage team wins, and 70.5% consistency with zero deductions.',
        'highlight_stat': '74.0 pts',
        'highlight_lbl': 'World #2 Clutch Score'
    },
    'Namboori Tilak Varma': {
        'badge': 'World #3 Crisis Anchor & Finisher',
        'desc': 'Recorded +21.46 Crisis Rescue WPA, +23.53 Counter-Attack WPA, 7 Authentic MWPPs, and 14 crucible team wins. Exceptional under top-order collapse conditions across 125 matches.',
        'highlight_stat': '63.7 pts',
        'highlight_lbl': 'World #3 Clutch Score'
    },
    'Heinrich Klaasen': {
        'badge': 'World #4 Crisis Rescue Crusher',
        'desc': 'World leader in Crisis Rescue WPA (+24.84) and +31.61 Counter-Attack WPA. Unstoppable middle-overs spin destroyer with 4 Authentic MWPPs and 12 crucible wins.',
        'highlight_stat': '61.6 pts',
        'highlight_lbl': 'World #4 Clutch Score'
    },
    'Glenn Phillips': {
        'badge': 'World #5 Complete Clutch Operator',
        'desc': 'Complete multi-situation operator: +18.48 Crisis Rescue WPA, +13.26 Death Finishing WPA, +23.85 Counter-Attack WPA, 4 Authentic MWPPs, and 12 crucible wins with zero deductions.',
        'highlight_stat': '60.6 pts',
        'highlight_lbl': 'World #5 Clutch Score'
    },
    'Shimron Hetmyer': {
        'badge': 'World #6 Rajasthan Royals Closer',
        'desc': 'Royals match-closer with +21.95 Counter-Attack WPA, +16.96 Crisis Rescue WPA, +10.20 Death WPA, 5 Authentic MWPPs, and 13 crucible wins.',
        'highlight_stat': '59.0 pts',
        'highlight_lbl': 'World #6 Clutch Score'
    },
    'Hardik Pandya': {
        'badge': 'World #7 Big-Stage Champion',
        'desc': 'Championship pedigree: +31.86 Counter-Attack WPA, +8.63 Death WPA, 18 crucible team wins, reinforced by a 1.50x knockout multiplier across IPL playoffs and ICC knockouts.',
        'highlight_stat': '55.7 pts',
        'highlight_lbl': 'World #7 Clutch Score'
    },
    'Virat Kohli': {
        'badge': 'World #8 The Master of Chases',
        'desc': 'The international benchmark for steep chase execution, generating +35.50 Counter-Attack WPA, 6 Authentic Match-Winning Pressure Performances (MWPPs), 10 crucible wins, and facing 2,455 balls against elite bowling.',
        'highlight_stat': '47.5 pts',
        'highlight_lbl': 'World #8 Clutch Score'
    },
    'Nicholas Pooran': {
        'badge': 'World #9 High-Leverage Consistency King',
        'desc': 'World #1 consistency rate (74.5%), +25.49 Counter-Attack WPA, +6.29 Crisis Rescue WPA, 5 Authentic MWPPs, and 11 crucible wins with zero flaw deductions.',
        'highlight_stat': '46.2 pts',
        'highlight_lbl': 'World #9 Clutch Score'
    },
    'Venkatesh Iyer': {
        'badge': 'World #10 Clutch Match-Winner',
        'desc': 'Delivered 7 Authentic Match-Winning Pressure Performances (MWPPs), +23.56 Counter-Attack WPA, +3.71 Crisis Rescue WPA, and a 66.7% consistency rate in high-pressure matches.',
        'highlight_stat': '45.4 pts',
        'highlight_lbl': 'World #10 Clutch Score'
    },
    'Shubman Gill': {
        'badge': 'Demoted Outside Top 10 (#11)',
        'desc': 'Possesses strong counter-attack volume (+31.4 WPA), but suffers from a negative crisis rescue metric (-2.03 WPA), failing to stabilize top-order collapses. Incurs a mandatory -15.3 pt flaw penalty.',
        'highlight_stat': '-15.3 pts',
        'highlight_lbl': 'Crisis Flaw Deduction'
    },
    'Phil Salt': {
        'badge': 'Top 12 Aggressive Opener',
        'desc': 'Aggressive Powerplay intent (+18.4 WPA), but carries higher variance across steep chases compared to the top 10 finishers.',
        'highlight_stat': '42.1 pts',
        'highlight_lbl': 'Clutch Rating'
    },
    'Dinesh Karthik': {
        'badge': 'Filtered: Sub-Threshold Specialist',
        'desc': 'While effective in brief death cameos (637 career balls), Karthik fails the substantive specialist batting threshold (>= 750 balls) and contributed 0.0 Death-Alive WPA, placing him outside the institutional Top 10.',
        'highlight_stat': '637 Balls',
        'highlight_lbl': 'Fails >= 750 Balls Threshold'
    },
    'Rashid Khan': {
        'badge': 'Filtered: Specialist Bowler Archetype',
        'desc': 'With only 506 balls faced, Rashid is categorized in his primary elite bowling archetype (#7 bowler globally) and correctly filtered out from the specialist batting rankings.',
        'highlight_stat': '506 Balls',
        'highlight_lbl': 'Filtered Bowler Archetype'
    },
    'Cameron Green': {
        'badge': 'Filtered: Sub-Threshold Match Impact',
        'desc': 'Despite strong career strike rate, Green managed only +11.8 Counter-Attack WPA and lower high-pressure win conversion, placing him well outside the Top 10 match-winning echelon.',
        'highlight_stat': '+11.8 WPA',
        'highlight_lbl': 'Low Match-on-the-Line WPA'
    }
}

BOWL_PROOFS = {
    'Jasprit Bumrah': {
        'badge': 'Undisputed King of Pace',
        'desc': 'Saves an astounding +149.76 runs above expected at the death, +74.54 runs in middle overs, and +17.98 in the powerplay. Maintained a 7.36 pressure economy with 64.4% consistency and zero deductions.',
        'highlight_stat': '+149.8 Runs',
        'highlight_lbl': 'Death Runs Saved Above Par'
    },
    'Sunil Narine': {
        'badge': 'Undisputed King of Spin',
        'desc': 'Positive runs saved across all 3 phases (+20.2 PP, +80.2 Mid, +23.6 Death). 100% elite franchise schedule (0.0% minnows), an elite 7.88 pressure economy, and zero flaw deductions.',
        'highlight_stat': '+124.0 Runs',
        'highlight_lbl': 'Total Runs Saved Across 3 Phases'
    },
    'Josh Hazlewood': {
        'badge': 'Powerplay Suppression Master',
        'desc': 'Saved a world-leading +48.43 runs in the Powerplay alone, backed by a 65.1% pressure consistency rate and +59.3 HP WPA against 100% elite international/IPL opposition.',
        'highlight_stat': '+48.4 Runs',
        'highlight_lbl': 'Powerplay Runs Saved Above Par'
    },
    'Mustafizur Rahman': {
        'badge': 'Death Cutter Specialist (Calibrated)',
        'desc': 'Saved +84.80 runs at the death and +21.93 in the powerplay. Calibrated accurately via 0.40x discounting for his 20.7% delivery volume in bilateral associate games, ranking cleanly at #4.',
        'highlight_stat': '+84.8 Runs',
        'highlight_lbl': 'Death Runs Saved (Calibrated)'
    },
    'Nathan Ellis': {
        'badge': 'Multi-Phase T20 Specialist',
        'desc': 'Saved +41.45 death runs and +32.56 middle overs runs against 100% elite competition with 64.0% consistency and zero flaw deductions across 41 high-leverage matches.',
        'highlight_stat': '+74.0 Runs',
        'highlight_lbl': 'Mid + Death Runs Saved'
    },
    'Bhuvneshwar Kumar': {
        'badge': '100-Match Veteran Master',
        'desc': 'Saved +41.23 runs at the death and +16.45 in the powerplay across 100 matches analyzed, maintaining a 60.3% pressure consistency rate over a massive historical sample.',
        'highlight_stat': '100 Matches',
        'highlight_lbl': 'Elite Sample Volume'
    },
    'Rashid Khan': {
        'badge': 'Middle-Overs Spin Controller',
        'desc': 'Saved +20.21 PP runs, +19.45 middle runs, and +10.73 death runs with a 60.4% consistency rate across 122 matches, calibrated with minnow discounting.',
        'highlight_stat': '+50.4 Runs',
        'highlight_lbl': 'Total Runs Saved'
    },
    'Axar Patel': {
        'badge': 'High-Leverage Economy Squeeze',
        'desc': 'Maintained an elite pressure economy of 8.33 RPO, saving +7.36 runs in the powerplay and +2.88 at the death across 135 matches with high tactical versatility.',
        'highlight_stat': '8.33 RPO',
        'highlight_lbl': 'Pressure Economy Rate'
    },
    'Varun Chakravarthy': {
        'badge': 'Mystery Spinner with Death Liability (#9)',
        'desc': 'Exceptional in the powerplay (+36.66 runs) and middle overs (+25.74 runs), but incurs an explicit -7.69 pt deduction for leaking -9.61 runs above expected at the death, ranking below Narine.',
        'highlight_stat': '-7.69 pts',
        'highlight_lbl': 'Death Run Leakage Penalty'
    },
    'Maheesh Theekshana': {
        'badge': 'Powerplay Carrom Specialist',
        'desc': 'Saved +41.88 runs in the powerplay and +39.65 at the death across 98 matches, calibrated with 0.40x discounting for associate fixtures.',
        'highlight_stat': '+41.9 Runs',
        'highlight_lbl': 'Powerplay Runs Saved'
    },
    'Mohammed Siraj': {
        'badge': 'High-Risk Death Phase Demotion (#19)',
        'desc': 'Solid in early overs (+24.5 PP runs saved), but severely vulnerable at the death, conceding -20.99 runs above expected at 8.98 RPO, resulting in a -16.8 pt deduction.',
        'highlight_stat': '-16.8 pts',
        'highlight_lbl': 'Death Overs Penalty'
    },
    'Ravi Bishnoi': {
        'badge': 'Severe Death Overs Liability (#51)',
        'desc': 'Elite in middle overs (+64.7 runs saved), but suffered catastrophic death-overs leakage of -41.78 runs above par, taking a severe -33.4 pt deduction.',
        'highlight_stat': '-33.4 pts',
        'highlight_lbl': 'Death Overs Penalty'
    }
}

# --- CHARTS ---
def create_horizontal_bar(df10, name_col, score_col, bar_color, title):
    medals = ['1st', '2nd', '3rd'] + [f'{i+1}th' for i in range(3, len(df10))]
    colors = [RR_GOLD, '#cbd5e1', '#b45309'] + [bar_color] * (len(df10) - 3)
    fig = go.Figure(go.Bar(
        x=df10[score_col],
        y=[f"{medals[i]}  {df10.iloc[i][name_col]}" for i in range(len(df10))],
        orientation='h',
        marker=dict(color=colors, line=dict(color='rgba(255,255,255,0.1)', width=1)),
        text=[f"  <b>{v:.1f}</b>" for v in df10[score_col]],
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
            range=[0, df10[score_col].max() * 1.16],
            zeroline=False,
            title=dict(text='Pressure Index Rating (0–100)', font=dict(size=10, color=SUBTEXT))
        ),
        yaxis=dict(gridcolor='rgba(0,0,0,0)', autorange='reversed'),
        height=380
    )
    return fig

fig_bat10 = create_horizontal_bar(bat10, 'striker_name', 'batting_clutch_score', RR_PINK, 'Top 10 Batters Under High-Leverage Pressure')
fig_bowl10 = create_horizontal_bar(bowl10, 'bowler_name', 'bowling_clutch_score', RR_BLUE, 'Top 10 Bowlers Under High-Leverage Pressure')

# Scatter
scatter_fig = go.Figure()
colors = [RR_GOLD if r['rank_bat'] <= 3 else (RED if r['striker_name'] == 'Shubman Gill' else RR_PINK) for _, r in bat12.iterrows()]
scatter_fig.add_trace(go.Scatter(
    x=bat12['rescue_wpa'],
    y=bat12['hp_ml_runs_added'],
    mode='markers+text',
    text=bat12['striker_name'],
    textposition='top center',
    marker=dict(
        size=[max(14, abs(w) * 0.9) for w in bat12['ca_wpa']],
        color=colors,
        opacity=0.88,
        line=dict(width=1.5, color='#ffffff')
    ),
    hovertemplate="<b>%{text}</b><br>Crisis Rescue WPA: %{x:+.2f}<br>ML Runs Added: %{y:+.1f}<br>Counter-Attack WPA Size: %{marker.size}<extra></extra>"
))
scatter_fig.add_vline(x=0, line_dash="dash", line_color="rgba(244, 63, 94, 0.5)", annotation_text="Collapse Failure Threshold", annotation_position="bottom right", annotation_font_color=RED)
scatter_fig.update_layout(
    title=dict(text='<b>Visual Proof 1: Batting Pressure Archetypes</b> (Crisis Rescue WPA vs High-Pressure ML Runs Added)', font=dict(color=TEXT, size=13)),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color=TEXT, family='Inter, -apple-system, sans-serif'),
    margin=dict(l=40, r=40, t=45, b=40),
    xaxis=dict(title='Crisis Rescue WPA (Collapse Resiliency)', gridcolor='rgba(255,255,255,0.05)', zeroline=True, zerolinecolor='rgba(255,255,255,0.2)'),
    yaxis=dict(title='High-Pressure ML Runs Added Above Expected', gridcolor='rgba(255,255,255,0.05)', zeroline=True, zerolinecolor='rgba(255,255,255,0.2)'),
    height=370
)

# Phase defense
bar_phases = go.Figure()
bar_phases.add_trace(go.Bar(name='Powerplay Saved', x=bowl10['bowler_name'], y=bowl10['ml_pp_runs_saved'], marker_color='#38bdf8'))
bar_phases.add_trace(go.Bar(name='Middle Overs Saved', x=bowl10['bowler_name'], y=bowl10['ml_mid_runs_saved'], marker_color='#818cf8'))
bar_phases.add_trace(go.Bar(name='Death Overs Saved', x=bowl10['bowler_name'], y=bowl10['ml_death_runs_saved'], marker_color=RR_PINK))
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
    height=370
)

# Minnow exposure
minnow_fig = go.Figure(go.Bar(
    x=bowl10['minnow_ratio'] * 100,
    y=bowl10['bowler_name'],
    orientation='h',
    marker=dict(
        color=[RED if v > 15 else (RR_GOLD if v > 5 else GREEN) for v in (bowl10['minnow_ratio'] * 100)],
        line=dict(color='rgba(255,255,255,0.1)', width=1)
    ),
    text=[f"  <b>{v*100:.1f}%</b> ({'Discounted 0.40x' if v > 0.05 else '100% Elite'})" for v in bowl10['minnow_ratio']],
    textposition='outside',
    textfont=dict(color=TEXT, size=10)
))
minnow_fig.update_layout(
    title=dict(text='<b>Visual Proof 3: Schedule Strength Calibration</b> (% Deliveries Against Associate / Minnow Attacks)', font=dict(color=TEXT, size=13)),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color=TEXT, family='Inter, -apple-system, sans-serif'),
    margin=dict(l=10, r=160, t=45, b=20),
    xaxis=dict(gridcolor='rgba(255,255,255,0.05)', title='Minnow Delivery Exposure (%)', range=[0, 32]),
    yaxis=dict(gridcolor='rgba(0,0,0,0)', autorange='reversed'),
    height=320
)

# Prepare Batters Data for Dossier
batters_data = {}
for _, br in bat12.iterrows():
    name = br['striker_name']
    b_proof = BAT_PROOFS.get(name, {
        'badge': 'Qualified Batter',
        'desc': f"Rank #{br['rank_bat']} qualified batter under high pressure.",
        'highlight_stat': f"{br['batting_clutch_score']:.1f} pts",
        'highlight_lbl': 'Clutch Rating'
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
    
    # Filter non-zero
    filtered_comps = {k: v for k, v in comps.items() if abs(v) > 0.05}
    waterfall_fig = go.Figure(go.Bar(
        x=list(filtered_comps.values()),
        y=list(filtered_comps.keys()),
        orientation='h',
        marker_color=[GREEN if v >= 0 else RED for v in filtered_comps.values()],
        text=[f"{v:+.1f} pts" for v in filtered_comps.values()],
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
    
    # Match logs
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
        'badge': b_proof['badge'],
        'desc': b_proof['desc'],
        'consistency': f"{float(br.get('hp_consistency_rate',0))*100:.1f}%",
        'hl_stat': b_proof['highlight_stat'],
        'hl_lbl': b_proof['highlight_lbl'],
        'deductions': f"-{float(br['fair_deductions']):.1f}",
        'deductions_val': float(br['fair_deductions']),
        'waterfall': json.loads(waterfall_fig.to_json()),
        'logs': logs_list
    }

# Prepare Bowlers Data for Dossier
bowlers_to_include = list(bowl10['bowler_name']) + ['Mohammed Siraj', 'Ravi Bishnoi']
bowlers_data = {}
for name in bowlers_to_include:
    bwr_matches = bowl_rank[bowl_rank['bowler_name'] == name]
    if bwr_matches.empty:
        continue
    bwr = bwr_matches.iloc[0]
    bw_proof = BOWL_PROOFS.get(name, {
        'badge': 'Qualified Bowler',
        'desc': f"Rank #{bwr['rank_bowl']} qualified bowler under high pressure.",
        'highlight_stat': f"{bwr['bowling_clutch_score']:.1f} pts",
        'highlight_lbl': 'Clutch Rating'
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
    waterfall_fig = go.Figure(go.Bar(
        x=list(filtered_comps.values()),
        y=list(filtered_comps.keys()),
        orientation='h',
        marker_color=[GREEN if v >= 0 else RED for v in filtered_comps.values()],
        text=[f"{v:+.1f} pts" for v in filtered_comps.values()],
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
        'badge': bw_proof['badge'],
        'desc': bw_proof['desc'],
        'consistency': f"{float(bwr.get('hp_consistency_rate',0))*100:.1f}%",
        'hl_stat': bw_proof['highlight_stat'],
        'hl_lbl': bw_proof['highlight_lbl'],
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

# Write payload to a json helper or generate HTML directly
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
        'bowlers_data': bowlers_data
    }, f)

print("Payload dumped successfully!")
