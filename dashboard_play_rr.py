"""
================================================================================
  RAJASTHAN ROYALS HIGH-PERFORMANCE CRICKET ANALYTICS STUDIO
  PROJECT: SupeRR Selector — The Halla Bol Pressure Index
  VERSION: Production Release 3.0 (Official Play RR Hackathon Submission)
================================================================================
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import dash
from dash import dcc, html, Input, Output, dash_table
import warnings
warnings.filterwarnings('ignore')

print("Loading Production Datasets for RR Analytics Studio...")
bat_rank = pd.read_parquet('bat_rankings_final.parquet')
bowl_rank = pd.read_parquet('bowl_rankings_final.parquet')
bat_logs = pd.read_parquet('bat_hp_match_logs.parquet')
bowl_logs = pd.read_parquet('bowl_hp_match_logs.parquet')

bat10 = bat_rank.head(10).reset_index(drop=True)
bowl10 = bowl_rank.head(10).reset_index(drop=True)
bat12 = bat_rank.head(12).reset_index(drop=True)

# ─────────────────────────────────────────────────────────────────────────────
# INSTITUTIONAL RAJASTHAN ROYALS DESIGN SYSTEM
# ─────────────────────────────────────────────────────────────────────────────
RR_PINK     = '#ea008a'              # Official Halla Bol Pink
RR_BLUE     = '#1e40af'              # Royal Blue
RR_GOLD     = '#f5c518'              # Royal Gold
BG          = '#070a13'              # Deep Stadium Night
CARD        = '#0f172a'              # Slate Navy Surface
CARD_HOVER  = '#1e293b'              # Elevated Surface
BORDER      = 'rgba(255, 255, 255, 0.08)'  # Subtle Clean Border
TEXT        = '#f8fafc'              # Pure White
SUBTEXT     = '#94a3b8'              # Technical Slate
GREEN       = '#10b981'              # Precision Green
RED         = '#f43f5e'              # Variance Red

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

# ─────────────────────────────────────────────────────────────────────────────
# UI COMPONENTS
# ─────────────────────────────────────────────────────────────────────────────
def kpi_card(title, value, subtitle, accent_color=RR_PINK, category='METRIC'):
    return html.Div([
        html.Div([
            html.Span(category, style={
                'fontSize': '9px', 'color': accent_color, 'letterSpacing': '1px',
                'textTransform': 'uppercase', 'fontWeight': '800', 'background': 'rgba(255,255,255,0.04)',
                'padding': '2px 6px', 'borderRadius': '4px', 'marginRight': '8px'
            }),
            html.Span(title, style={
                'fontSize': '10px', 'color': SUBTEXT, 'letterSpacing': '1.2px',
                'textTransform': 'uppercase', 'fontWeight': '700'
            }),
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '4px'}),
        html.H3(str(value), style={
            'margin': '2px 0', 'fontSize': '21px', 'color': '#ffffff', 'fontWeight': '900',
            'letterSpacing': '-0.5px'
        }),
        html.P(subtitle, style={'margin': '0', 'fontSize': '11px', 'color': SUBTEXT, 'fontWeight': '500'}),
    ], style={
        'background': CARD, 'border': f'1px solid {BORDER}', 'borderRadius': '14px',
        'padding': '14px 18px', 'flex': '1', 'minWidth': '180px',
        'borderTop': f'3px solid {accent_color}', 'boxShadow': '0 4px 20px rgba(0,0,0,0.3)'
    })

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

def create_table(df, cols_map):
    sub = df[list(cols_map.keys())].copy()
    sub.columns = list(cols_map.values())
    
    for c in sub.columns:
        if sub[c].dtype == float:
            sub[c] = sub[c].map(lambda x: f"{x:.2f}" if abs(x) < 10 else f"{x:.1f}")
            
    return dash_table.DataTable(
        data=sub.to_dict('records'),
        columns=[{'name': i, 'id': i} for i in sub.columns],
        style_as_list_view=True,
        style_header={
            'backgroundColor': 'rgba(15, 23, 42, 0.95)',
            'color': RR_PINK,
            'fontWeight': '800',
            'fontSize': '11px',
            'borderBottom': f'2px solid {RR_PINK}',
            'textTransform': 'uppercase',
            'letterSpacing': '0.5px',
            'padding': '10px'
        },
        style_cell={
            'backgroundColor': CARD,
            'color': TEXT,
            'fontSize': '11px',
            'borderBottom': f'1px solid {BORDER}',
            'padding': '9px 12px',
            'textAlign': 'center',
            'fontFamily': 'Inter, -apple-system, sans-serif'
        },
        style_cell_conditional=[
            {'if': {'column_id': 'Player'}, 'textAlign': 'left', 'fontWeight': '700', 'color': '#ffffff'}
        ],
        style_data_conditional=[
            {
                'if': {'row_index': 0},
                'backgroundColor': 'rgba(245, 197, 24, 0.06)',
                'fontWeight': 'bold'
            }
        ]
    )

# ─────────────────────────────────────────────────────────────────────────────
# APP INITIALIZATION
# ─────────────────────────────────────────────────────────────────────────────
app = dash.Dash(__name__, title="Rajasthan Royals — SupeRR Selector Studio")
server = app.server

app.layout = html.Div(style={
    'background': BG,
    'minHeight': '100vh',
    'fontFamily': 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    'color': TEXT,
    'padding': '24px 36px'
}, children=[

    # ─────────────────────────────────────────────────────────────────────────
    # HEADER
    # ─────────────────────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.Div([
                html.Span("RAJASTHAN ROYALS", style={
                    'background': RR_PINK, 'color': '#ffffff', 'padding': '3px 8px',
                    'borderRadius': '4px', 'fontSize': '10px', 'fontWeight': '900', 'letterSpacing': '1.5px'
                }),
                html.Span("HIGH-PERFORMANCE CRICKET ANALYTICS STUDIO", style={
                    'color': RR_GOLD, 'fontSize': '11px', 'fontWeight': '700', 'marginLeft': '10px', 'letterSpacing': '1px'
                }),
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '6px'}),
            html.H1("SupeRR Selector: The Halla Bol Pressure Index", style={
                'margin': '0', 'fontSize': '26px', 'fontWeight': '900', 'letterSpacing': '-0.5px',
                'color': '#ffffff'
            }),
            html.P("Context-Aware Multi-Phase Leverage & Win Probability Engine | IPL & T20I (2022–2026)", style={
                'margin': '4px 0 0', 'fontSize': '13px', 'color': SUBTEXT
            }),
        ]),
        html.Div([
            html.Div([
                html.Span("SUBMISSION BY: LOHITHASWIN V", style={
                    'background': 'rgba(234, 0, 138, 0.15)', 'color': RR_PINK, 'padding': '5px 12px',
                    'borderRadius': '6px', 'fontSize': '11px', 'fontWeight': '800', 'border': f'1px solid rgba(234, 0, 138, 0.3)'
                }),
                html.Span("PLAY RR HACKATHON 2026", style={
                    'background': 'rgba(245, 197, 24, 0.12)', 'color': RR_GOLD, 'padding': '5px 12px',
                    'borderRadius': '6px', 'fontSize': '11px', 'fontWeight': '800', 'border': f'1px solid rgba(245, 197, 24, 0.3)', 'marginLeft': '8px'
                }),
                html.Span("883 MATCHES • 190,811 DELIVERIES", style={
                    'background': 'rgba(30, 64, 175, 0.2)', 'color': '#60a5fa', 'padding': '5px 12px',
                    'borderRadius': '6px', 'fontSize': '11px', 'fontWeight': '800', 'border': f'1px solid rgba(96, 165, 250, 0.3)', 'marginLeft': '8px'
                }),
            ], style={'display': 'flex', 'alignItems': 'center'}),
        ])
    ], style={
        'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center',
        'paddingBottom': '20px', 'borderBottom': f'1px solid {BORDER}', 'marginBottom': '22px'
    }),

    # ─────────────────────────────────────────────────────────────────────────
    # STAT KPI STRIP
    # ─────────────────────────────────────────────────────────────────────────
    html.Div([
        kpi_card('Peak Fast Bowling Execution', 'Jasprit Bumrah', '78.5 Index Rating • +149.8 Death Saved • 0.0 Deductions', RR_GOLD, 'PACE ELITE'),
        kpi_card('Peak Spin Bowling Execution', 'Sunil Narine', '52.4 Index Rating • +124.0 Runs Saved across 3 Phases', RR_PINK, 'SPIN ELITE'),
        kpi_card('Match-on-the-Line Finisher', 'David Miller', '80.2 Index Rating • #1 Counter-Attack (+42.3 WPA) • 8 MWPPs', RR_GOLD, 'BAT CLUTCH #1'),
        kpi_card('All-Phase Pressure Batting', 'Suryakumar Yadav', '74.0 Index Rating • 20 Crucible Wins • 70.5% Consistency', RR_PINK, 'BAT CLUTCH #2'),
        kpi_card('Specialist Eligibility Filter', '≥ 750 Career Balls', 'Bowler Cameos Filtered • 100% Specialist Integrity', GREEN, 'STANDARD'),
    ], style={'display': 'flex', 'gap': '14px', 'marginBottom': '24px', 'flexWrap': 'wrap'}),

    # ─────────────────────────────────────────────────────────────────────────
    # NAVIGATION TABS
    # ─────────────────────────────────────────────────────────────────────────
    dcc.Tabs(id='rr-tabs', value='tab-rankings', style={'marginBottom': '20px'},
             colors={'border': BORDER, 'primary': RR_PINK, 'background': CARD}, children=[
        dcc.Tab(label='INDEX LEADERBOARDS & MULTI-PHASE AUDIT', value='tab-rankings',
                style={'padding': '11px', 'fontWeight': '700', 'color': SUBTEXT, 'background': CARD},
                selected_style={'padding': '11px', 'background': CARD_HOVER, 'color': '#ffffff', 'fontWeight': '900', 'borderTop': f'3px solid {RR_PINK}'}),
        dcc.Tab(label='TOP 10 VISUAL PROOFS & EVIDENCE DOSSIERS', value='tab-proofs',
                style={'padding': '11px', 'fontWeight': '700', 'color': SUBTEXT, 'background': CARD},
                selected_style={'padding': '11px', 'background': CARD_HOVER, 'color': '#ffffff', 'fontWeight': '900', 'borderTop': f'3px solid {RR_GOLD}'}),
        dcc.Tab(label='ANALYTICAL CASE STUDIES (THE 5 CORE DEBATES)', value='tab-audits',
                style={'padding': '11px', 'fontWeight': '700', 'color': SUBTEXT, 'background': CARD},
                selected_style={'padding': '11px', 'background': CARD_HOVER, 'color': '#ffffff', 'fontWeight': '900', 'borderTop': f'3px solid {RR_BLUE}'}),
        dcc.Tab(label='MATHEMATICAL ARCHITECTURE & PRESSURE METHODOLOGY', value='tab-methodology',
                style={'padding': '11px', 'fontWeight': '700', 'color': SUBTEXT, 'background': CARD},
                selected_style={'padding': '11px', 'background': CARD_HOVER, 'color': '#ffffff', 'fontWeight': '900', 'borderTop': f'3px solid {GREEN}'}),
    ]),

    html.Div(id='rr-tab-content')
])

# ─────────────────────────────────────────────────────────────────────────────
# ROUTING CALLBACK
# ─────────────────────────────────────────────────────────────────────────────
@app.callback(Output('rr-tab-content', 'children'), Input('rr-tabs', 'value'))
def render_content(tab):
    if tab == 'tab-rankings':
        bat_cols = {
            'rank_bat': 'Rank', 'striker_name': 'Player', 'matches': 'Matches',
            'hp_consistency_rate': 'Consistency', 'ca_wpa': 'Counter-Attack', 'rescue_wpa': 'Crisis Rescue',
            'da_wpa': 'Death Finishing', 'hp_ml_runs_added': 'ML Runs Added', 'fair_deductions': 'Deductions', 'batting_clutch_score': 'Index Rating'
        }
        bowl_cols = {
            'rank_bowl': 'Rank', 'bowler_name': 'Player', 'matches': 'Matches',
            'hp_consistency_rate': 'Consistency', 'ml_pp_runs_saved': 'PP Saved', 'ml_mid_runs_saved': 'Mid Saved',
            'ml_death_runs_saved': 'Death Saved', 'hp_eco': 'Pressure Eco', 'fair_deductions': 'Deductions', 'bowling_clutch_score': 'Index Rating'
        }
        return html.Div([
            html.Div([
                html.Div([
                    dcc.Graph(figure=create_horizontal_bar(bat10, 'striker_name', 'batting_clutch_score', RR_PINK, 'Top 10 Batters Under High-Leverage Pressure'), config={'displayModeBar': False})
                ], style={'flex': '1', 'background': CARD, 'borderRadius': '14px', 'border': f'1px solid {BORDER}', 'padding': '16px'}),
                html.Div([
                    dcc.Graph(figure=create_horizontal_bar(bowl10, 'bowler_name', 'bowling_clutch_score', RR_BLUE, 'Top 10 Bowlers Under High-Leverage Pressure'), config={'displayModeBar': False})
                ], style={'flex': '1', 'background': CARD, 'borderRadius': '14px', 'border': f'1px solid {BORDER}', 'padding': '16px'}),
            ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '20px'}),

            html.Div([
                html.Div([
                    html.Div([
                        html.Span("QUALIFIED BATTERS (≥500 BALLS)", style={'fontSize': '12px', 'fontWeight': '900', 'color': RR_PINK, 'letterSpacing': '0.5px'}),
                        html.Span("Contextual Win Probability, Crisis Anchoring & ML Attribution", style={'fontSize': '11px', 'color': SUBTEXT, 'marginLeft': '10px'})
                    ], style={'marginBottom': '10px'}),
                    create_table(bat10, bat_cols)
                ], style={'flex': '1', 'background': CARD, 'borderRadius': '14px', 'border': f'1px solid {BORDER}', 'padding': '16px'}),

                html.Div([
                    html.Div([
                        html.Span("QUALIFIED BOWLERS (MULTI-PHASE AUDIT)", style={'fontSize': '12px', 'fontWeight': '900', 'color': RR_BLUE, 'letterSpacing': '0.5px'}),
                        html.Span("Phase-by-Phase Runs Saved, Dots & Flaw Deductions", style={'fontSize': '11px', 'color': SUBTEXT, 'marginLeft': '10px'})
                    ], style={'marginBottom': '10px'}),
                    create_table(bowl10, bowl_cols)
                ], style={'flex': '1', 'background': CARD, 'borderRadius': '14px', 'border': f'1px solid {BORDER}', 'padding': '16px'}),
            ], style={'display': 'flex', 'gap': '16px'})
        ])

    elif tab == 'tab-proofs':
        # 1. BATTING SCATTER PROOF
        scatter_fig = go.Figure()
        
        # Color mapping: Top 3 Gold, #4-#10 Pink, Gill Red
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

        # 2. BOWLING PHASE DEFENSE GROUPED BAR PROOF
        bar_phases = go.Figure()
        bar_phases.add_trace(go.Bar(
            name='Powerplay Saved',
            x=bowl10['bowler_name'],
            y=bowl10['ml_pp_runs_saved'],
            marker_color='#38bdf8'
        ))
        bar_phases.add_trace(go.Bar(
            name='Middle Overs Saved',
            x=bowl10['bowler_name'],
            y=bowl10['ml_mid_runs_saved'],
            marker_color='#818cf8'
        ))
        bar_phases.add_trace(go.Bar(
            name='Death Overs Saved',
            x=bowl10['bowler_name'],
            y=bowl10['ml_death_runs_saved'],
            marker_color=RR_PINK
        ))
        
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

        # 3. SCHEDULE STRENGTH MINNOW EXPOSURE HORIZONTAL BAR
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

        return html.Div([
            html.Div([
                html.Div([dcc.Graph(figure=scatter_fig, config={'displayModeBar': False})], style={'flex': '1', 'background': CARD, 'borderRadius': '14px', 'border': f'1px solid {BORDER}', 'padding': '16px'}),
                html.Div([dcc.Graph(figure=bar_phases, config={'displayModeBar': False})], style={'flex': '1', 'background': CARD, 'borderRadius': '14px', 'border': f'1px solid {BORDER}', 'padding': '16px'}),
            ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '20px'}),

            html.Div([
                html.Div([dcc.Graph(figure=minnow_fig, config={'displayModeBar': False})], style={'flex': '1', 'background': CARD, 'borderRadius': '14px', 'border': f'1px solid {BORDER}', 'padding': '16px'}),
                html.Div([
                    html.H4("CRITICAL TAKEAWAYS FROM VISUAL PROOFS", style={'margin': '0 0 10px', 'fontSize': '12px', 'fontWeight': '900', 'color': RR_GOLD, 'letterSpacing': '1px'}),
                    html.Ul([
                        html.Li([html.B("David Miller (+42.27 Counter-Attack WPA): ", style={'color': RR_GOLD}), "World #1 Match-on-the-Line chase finisher. Unmatched in converting high RRR (≥10.0) run chases into victories with +17.65 Death WPA and 8 Authentic MWPPs."], style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '8px'}),
                        html.Li([html.B("Suryakumar Yadav (+234.4 ML Runs): ", style={'color': RR_PINK}), "World #2 all-phase pressure force. Generates extraordinary runs above par against 98.75% elite bowling, converting 20 crucible matches into team victories."], style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '8px'}),
                        html.Li([html.B("Heinrich Klaasen (+24.84 Rescue WPA): ", style={'color': RR_GOLD}), "World #1 in resurrecting batting teams from top-order collapse, obliterating spin across the middle overs."], style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '8px'}),
                        html.Li([html.B("Jasprit Bumrah (+149.8 Death Saved): ", style={'color': RR_PINK}), "Completely off the charts. Concedes 7.36 RPO in pressure and prevents +149.8 runs above expected at the death."], style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '8px'}),
                        html.Li([html.B("Sunil Narine vs Varun Chakravarthy: ", style={'color': RR_GOLD}), "Narine is positive across all 3 phases (+20.2, +80.2, +23.6); Varun drops into negative red (-9.61) at the death."], style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '8px'}),
                        html.Li([html.B("Mustafizur Rahman Calibration: ", style={'color': GREEN}), "20.7% associate minnow deliveries discounted at 0.40x, correctly situating him at #4 behind Bumrah, Narine, and Hazlewood."], style={'fontSize': '11px', 'color': SUBTEXT})
                    ], style={'paddingLeft': '16px', 'margin': '0'})
                ], style={'flex': '1', 'background': CARD, 'borderRadius': '14px', 'border': f'1px solid {BORDER}', 'padding': '18px'})
            ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '20px'}),

            # INTERACTIVE DOSSIER SELECTOR
            html.Div([
                html.Div([
                    html.H3("FORENSIC PLAYER EVIDENCE DOSSIER", style={'margin': '0', 'fontSize': '14px', 'fontWeight': '900', 'color': '#ffffff', 'letterSpacing': '1px'}),
                    html.P("Select any qualified batter or bowler to inspect full factor attribution, proof metrics, and high-leverage match logs.", style={'margin': '2px 0 0', 'fontSize': '11px', 'color': SUBTEXT})
                ], style={'marginBottom': '14px'}),

                html.Div([
                    html.Div([
                        html.Label("SELECT BATTER:", style={'fontSize': '10px', 'fontWeight': '800', 'color': RR_PINK, 'letterSpacing': '1px', 'marginBottom': '4px', 'display': 'block'}),
                        dcc.Dropdown(
                            id='sel-bat',
                            options=[{'label': f"#{r['rank_bat']} {r['striker_name']} ({r['batting_clutch_score']:.1f} pts)", 'value': r['striker_name']} for _, r in bat12.iterrows()],
                            value='David Miller',
                            clearable=False,
                            style={'color': '#000000', 'fontSize': '12px', 'fontWeight': '700'}
                        )
                    ], style={'flex': '1'}),
                    html.Div([
                        html.Label("SELECT BOWLER:", style={'fontSize': '10px', 'fontWeight': '800', 'color': RR_BLUE, 'letterSpacing': '1px', 'marginBottom': '4px', 'display': 'block'}),
                        dcc.Dropdown(
                            id='sel-bowl',
                            options=[
                                {'label': f"#{r['rank_bowl']} {r['bowler_name']} ({r['bowling_clutch_score']:.1f} pts)", 'value': r['bowler_name']} for _, r in bowl10.iterrows()
                            ] + [
                                {'label': '#19 Mohammed Siraj (31.0 pts - Flaw Demotion)', 'value': 'Mohammed Siraj'},
                                {'label': '#51 Ravi Bishnoi (15.1 pts - Flaw Demotion)', 'value': 'Ravi Bishnoi'}
                            ],
                            value='Jasprit Bumrah',
                            clearable=False,
                            style={'color': '#000000', 'fontSize': '12px', 'fontWeight': '700'}
                        )
                    ], style={'flex': '1'}),
                ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '16px'}),

                html.Div(id='player-audit-display')
            ], style={'background': CARD, 'borderRadius': '14px', 'border': f'1px solid {BORDER}', 'padding': '20px'})
        ])

    elif tab == 'tab-audits':
        return html.Div([
            html.Div([
                # Case 1: Narine vs Varun
                html.Div([
                    html.Div([
                        html.Span("CASE STUDY 01", style={'fontSize': '10px', 'fontWeight': '900', 'color': RR_GOLD, 'letterSpacing': '1px'}),
                        html.H4("Sunil Narine (#2) Decisively Outperforms Varun Chakravarthy (#9)", style={'color': '#ffffff', 'margin': '4px 0 8px', 'fontSize': '15px'}),
                    ]),
                    html.P("Both are world-class mystery spinners, but their pressure execution diverges drastically at the death overs.", style={'fontSize': '12px', 'color': SUBTEXT, 'lineHeight': '1.5'}),
                    html.Div([
                        html.Div([
                            html.H5("Sunil Narine (#2 — 52.4 pts)", style={'color': RR_PINK, 'margin': '0 0 4px', 'fontSize': '12px'}),
                            html.Ul([
                                html.Li("Positive runs saved in ALL 3 phases (+20.2 PP, +80.2 Mid, +23.6 Death)", style={'fontSize': '11px', 'color': SUBTEXT}),
                                html.Li("Faced 100% Tier-1 elite opposition (0.0% minnows)", style={'fontSize': '11px', 'color': SUBTEXT}),
                                html.Li("Economy rate in pressure: 7.88 RPO | 0.0 Deductions", style={'fontSize': '11px', 'color': SUBTEXT}),
                            ], style={'paddingLeft': '14px', 'margin': '0'})
                        ], style={'flex': '1', 'background': 'rgba(234, 0, 138, 0.05)', 'padding': '12px', 'borderRadius': '8px', 'border': '1px solid rgba(234, 0, 138, 0.2)'}),
                        html.Div([
                            html.H5("Varun Chakravarthy (#9 — 38.6 pts)", style={'color': RR_BLUE, 'margin': '0 0 4px', 'fontSize': '12px'}),
                            html.Ul([
                                html.Li("Exceptional in PP (+36.7) and Mid (+25.7)", style={'fontSize': '11px', 'color': SUBTEXT}),
                                html.Li("Conceded -9.61 runs above expected at the Death", style={'fontSize': '11px', 'color': RED}),
                                html.Li("Takes an explicit -7.69 pt Non-Negotiable Flaw Penalty", style={'fontSize': '11px', 'color': RED}),
                            ], style={'paddingLeft': '14px', 'margin': '0'})
                        ], style={'flex': '1', 'background': 'rgba(30, 64, 175, 0.05)', 'padding': '12px', 'borderRadius': '8px', 'border': '1px solid rgba(30, 64, 175, 0.2)'})
                    ], style={'display': 'flex', 'gap': '12px', 'marginTop': '10px'})
                ], style={'flex': '1', 'background': CARD, 'borderRadius': '14px', 'border': f'1px solid {BORDER}', 'padding': '18px'}),

                # Case 2: Mustafizur
                html.Div([
                    html.Div([
                        html.Span("CASE STUDY 02", style={'fontSize': '10px', 'fontWeight': '900', 'color': RR_GOLD, 'letterSpacing': '1px'}),
                        html.H4("Schedule Strength: Mustafizur Calibrated from #2 to #4", style={'color': '#ffffff', 'margin': '4px 0 8px', 'fontSize': '15px'}),
                    ]),
                    html.P("In unweighted systems, Mustafizur inflated raw numbers in low-scoring Dhaka bilaterals. Context weighting reveals the true hierarchy.", style={'fontSize': '12px', 'color': SUBTEXT, 'lineHeight': '1.5'}),
                    html.Div([
                        html.Ul([
                            html.Li("20.7% of Mustafizur's deliveries (324 balls) came against minnows (Zimbabwe, UAE, Netherlands, Oman) on 120-run par pitches.", style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '6px'}),
                            html.Li("With 0.40x associate discounting, his inflated numbers adjust to true elite par.", style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '6px'}),
                            html.Li("Result: Jasprit Bumrah (#1), Sunil Narine (#2), and Josh Hazlewood (#3) rightfully hold the podium.", style={'fontSize': '11px', 'color': GREEN}),
                        ], style={'paddingLeft': '14px', 'margin': '0'})
                    ], style={'background': 'rgba(255, 255, 255, 0.02)', 'padding': '12px', 'borderRadius': '8px', 'border': f'1px solid {BORDER}', 'marginTop': '10px'})
                ], style={'flex': '1', 'background': CARD, 'borderRadius': '14px', 'border': f'1px solid {BORDER}', 'padding': '18px'}),
            ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '16px'}),

            html.Div([
                # Case 3: Pooran & Kohli vs Gill
                html.Div([
                    html.Div([
                        html.Span("CASE STUDY 03", style={'fontSize': '10px', 'fontWeight': '900', 'color': RR_GOLD, 'letterSpacing': '1px'}),
                        html.H4("Match-on-the-Line Priority: Pooran (#9) & Kohli (#8) Surpass Gill (#11)", style={'color': '#ffffff', 'margin': '4px 0 8px', 'fontSize': '15px'}),
                    ]),
                    html.P("Top-order batters who fail to stabilize the team during collapses cannot be compensated by comfortable front-running runs.", style={'fontSize': '12px', 'color': SUBTEXT, 'lineHeight': '1.5'}),
                    html.Ul([
                        html.Li("Nicholas Pooran (#9 — 46.2 pts) maintains a world-leading 74.5% pressure consistency, +25.49 Counter-Attack WPA, and 5 Authentic MWPPs with 0.0 deductions.", style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '4px'}),
                        html.Li("Virat Kohli (#8 — 47.5 pts) delivers unmatched chase pacing with +35.50 Counter-Attack WPA and 6 Authentic MWPPs against 100% elite bowling.", style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '4px'}),
                        html.Li("Shubman Gill has a negative crisis rescue score (-2.03 WPA), repeatedly falling cheaply during early collapse states.", style={'fontSize': '11px', 'color': RED, 'marginBottom': '4px'}),
                        html.Li("Gill incurs a mandatory -15.3 pt non-compensatory flaw penalty (7.5x crisis collapse multiplier), demoting him to #11.", style={'fontSize': '11px', 'color': RED})
                    ], style={'paddingLeft': '14px', 'margin': '0'})
                ], style={'flex': '1', 'background': CARD, 'borderRadius': '14px', 'border': f'1px solid {BORDER}', 'padding': '18px'}),

                # Case 4: Specialist Batting Standard (Filtering Non-Specialists)
                html.Div([
                    html.Div([
                        html.Span("CASE STUDY 04", style={'fontSize': '10px', 'fontWeight': '900', 'color': RR_GOLD, 'letterSpacing': '1px'}),
                        html.H4("Specialist Standard (≥750 Balls): Filtering Bowlers (Rashid Khan), Low-Impact Players (Green), & Cameos (DK, Dhoni)", style={'color': '#ffffff', 'margin': '4px 0 8px', 'fontSize': '15px'}),
                    ]),
                    html.P("A true clutch batting index must evaluate proven top/middle-order specialists who bear match responsibility, not brief cameos or lower-order tailenders.", style={'fontSize': '12px', 'color': SUBTEXT, 'lineHeight': '1.5'}),
                    html.Ul([
                        html.Li("Rashid Khan (506 balls) is an elite bowler (#7 globally), but batting down at #8 with 506 balls creates massive volatility distortion; he belongs strictly in the bowling ranks.", style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '4px'}),
                        html.Li("Cameron Green manages only +11.8 Counter-Attack WPA and fails high-pressure match-on-the-line impact despite high raw strike rate.", style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '4px'}),
                        html.Li("Dinesh Karthik (637 balls, 0.0 Death-Alive WPA) and MS Dhoni (460 balls) fail the substantive ≥750 balls standard, preventing sample distortion.", style={'fontSize': '11px', 'color': GREEN})
                    ], style={'paddingLeft': '14px', 'margin': '0'})
                ], style={'flex': '1', 'background': CARD, 'borderRadius': '14px', 'border': f'1px solid {BORDER}', 'padding': '18px'}),

                # Case 5: Siraj & Bishnoi
                html.Div([
                    html.Div([
                        html.Span("CASE STUDY 05", style={'fontSize': '10px', 'fontWeight': '900', 'color': RR_GOLD, 'letterSpacing': '1px'}),
                        html.H4("Phase Risk Audit: Siraj (#19) and Bishnoi (#51) Demoted", style={'color': '#ffffff', 'margin': '4px 0 8px', 'fontSize': '15px'}),
                    ]),
                    html.P("Death overs defense is non-negotiable. Fatal leakage cannot be masked by good powerplay or middle overs bowling.", style={'fontSize': '12px', 'color': SUBTEXT, 'lineHeight': '1.5'}),
                    html.Ul([
                        html.Li("Mohammed Siraj leaked -20.99 runs above expected at the death at 8.98 RPO (-16.8 pt penalty).", style={'fontSize': '11px', 'color': RED, 'marginBottom': '4px'}),
                        html.Li("Ravi Bishnoi leaked -41.78 runs above expected at the death at 10.42 RPO (-33.4 pt penalty).", style={'fontSize': '11px', 'color': RED, 'marginBottom': '4px'}),
                        html.Li("Both bowlers demonstrate extreme tactical liability in death-pressure situations.", style={'fontSize': '11px', 'color': SUBTEXT})
                    ], style={'paddingLeft': '14px', 'margin': '0'})
                ], style={'flex': '1', 'background': CARD, 'borderRadius': '14px', 'border': f'1px solid {BORDER}', 'padding': '18px'})
            ], style={'display': 'flex', 'gap': '16px'})
        ])

    elif tab == 'tab-methodology':
        return html.Div([
            # ROW 1: HOW BIG MATCHES, MUST-WINS & PRESSURE ARE IDENTIFIED
            html.Div([
                # Left Column: Big Matches & Must-Wins
                html.Div([
                    html.Div([
                        html.Span("IDENTIFICATION ENGINE", style={'fontSize': '10px', 'fontWeight': '900', 'color': RR_GOLD, 'letterSpacing': '1px'}),
                        html.H3("HOW BIG MATCHES & MUST-WINS ARE IDENTIFIED", style={'color': '#ffffff', 'fontSize': '15px', 'fontWeight': '900', 'margin': '4px 0 12px'}),
                    ]),
                    
                    html.Div([
                        html.H4("1. Tournament Knockouts & Elimination Stakes (1.50x Multiplier)", style={'color': RR_PINK, 'fontSize': '12px', 'margin': '0 0 4px'}),
                        html.P("Every delivery is tagged by match stage metadata. Matches qualify for the 1.50x Big-Match Knockout Multiplier if knock_out == 1 OR stage is classified as Final, Eliminator, Qualifier 1, Qualifier 2, Semi Final, or Super 4. These are single-elimination games where defeat ends the tournament campaign.", style={'fontSize': '11px', 'color': SUBTEXT, 'margin': '0 0 10px', 'lineHeight': '1.5'})
                    ], style={'background': 'rgba(255,255,255,0.02)', 'padding': '12px', 'borderRadius': '8px', 'border': f'1px solid {BORDER}', 'marginBottom': '10px'}),

                    html.Div([
                        html.H4("2. The 'Crucible Match Win' Attribution Filter (Authentic MWPPs)", style={'color': RR_PINK, 'fontSize': '12px', 'margin': '0 0 4px'}),
                        html.P("To eliminate empty stat-padding, a player is only credited with a Crucible Match Win if four strict criteria are satisfied simultaneously:", style={'fontSize': '11px', 'color': SUBTEXT, 'margin': '0 0 6px'}),
                        html.Ul([
                            html.Li([html.B("Outcome Mandate: "), "The player's team MUST have won the match (team_won == 1). Runs or wickets in lost causes receive zero match-win credit."], style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '4px'}),
                            html.Li([html.B("Minimum Leverage Threshold: "), "High-Pressure WPA >= +0.50 (or HP strike rate >= 160 with >= 20 runs scored under pressure)."], style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '4px'}),
                            html.Li([html.B("Crisis / Finishing Requirement: "), "Either Death Chase WPA >= 1.0 or Crisis Rescue WPA >= 1.5."], style={'fontSize': '11px', 'color': SUBTEXT})
                        ], style={'paddingLeft': '14px', 'margin': '0 0 10px'})
                    ], style={'background': 'rgba(255,255,255,0.02)', 'padding': '12px', 'borderRadius': '8px', 'border': f'1px solid {BORDER}', 'marginBottom': '10px'}),

                    html.Div([
                        html.H4("3. Schedule Strength & Opposition Tiering", style={'color': RR_PINK, 'fontSize': '12px', 'margin': '0 0 4px'}),
                        html.P("Performance against elite attacks is amplified; stats against weak bowling are penalized:", style={'fontSize': '11px', 'color': SUBTEXT, 'margin': '0 0 4px'}),
                        html.Ul([
                            html.Li([html.B("Tier 1 Elite (1.25x Boost): "), "All IPL franchise clashes, India, Australia, England, South Africa, New Zealand, Pakistan, West Indies."], style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '2px'}),
                            html.Li([html.B("Associate / Minnow (0.40x Discount): "), "Bilateral series against lower-tier associates (e.g. Zimbabwe, UAE, Netherlands, Oman) on low-par pitches."], style={'fontSize': '11px', 'color': SUBTEXT})
                        ], style={'paddingLeft': '14px', 'margin': '0'})
                    ], style={'background': 'rgba(255,255,255,0.02)', 'padding': '12px', 'borderRadius': '8px', 'border': f'1px solid {BORDER}'})
                ], style={'flex': '1', 'background': CARD, 'borderRadius': '14px', 'padding': '20px', 'border': f'1px solid {BORDER}'}),

                # Right Column: Dynamic Ball-by-Ball Pressure Formulation
                html.Div([
                    html.Div([
                        html.Span("DYNAMIC PRESSURE ENGINE", style={'fontSize': '10px', 'fontWeight': '900', 'color': RR_GOLD, 'letterSpacing': '1px'}),
                        html.H3("DYNAMIC BALL-BY-BALL PRESSURE DETECTION", style={'color': '#ffffff', 'fontSize': '15px', 'fontWeight': '900', 'margin': '4px 0 12px'}),
                    ]),

                    html.Div([
                        html.H4("1. Instantaneous Leverage Index (LI ≥ 1.50)", style={'color': '#38bdf8', 'fontSize': '12px', 'margin': '0 0 4px'}),
                        html.P("Evaluated on every delivery as the derivative of Win Probability: LI = (ΔWP_wicket - ΔWP_boundary) / σ_WP. Isolates deliveries where a single boundary or wicket swings match probability by at least 1.5x the historical volatility (top 15% game-defining deliveries).", style={'fontSize': '11px', 'color': SUBTEXT, 'margin': '0 0 10px', 'lineHeight': '1.5'})
                    ], style={'background': 'rgba(255,255,255,0.02)', 'padding': '12px', 'borderRadius': '8px', 'border': f'1px solid {BORDER}', 'marginBottom': '10px'}),

                    html.Div([
                        html.H4("2. Scoreboard Chase Pressure (RRR ≥ 10.0 RPO)", style={'color': '#38bdf8', 'fontSize': '12px', 'margin': '0 0 4px'}),
                        html.P("Triggered in second innings run chases where the required run rate reaches or exceeds 10.0 runs per over with fewer than 8 wickets in hand. Evaluates ice-cold boundary hitting under escalating scoreboard pressure.", style={'fontSize': '11px', 'color': SUBTEXT, 'margin': '0 0 10px', 'lineHeight': '1.5'})
                    ], style={'background': 'rgba(255,255,255,0.02)', 'padding': '12px', 'borderRadius': '8px', 'border': f'1px solid {BORDER}', 'marginBottom': '10px'}),

                    html.Div([
                        html.H4("3. Crisis Collapse Windows (Early & Middle Overs)", style={'color': '#38bdf8', 'fontSize': '12px', 'margin': '0 0 4px'}),
                        html.P("Identifies deliveries where the batting team is reeling in a top-order collapse: Powerplay Crisis (Overs 1–6 with >= 2 wickets lost) or Middle Overs Collapse (Overs 7–12 with >= 4 wickets lost). Distinguishes authentic innings resurrection from front-running.", style={'fontSize': '11px', 'color': SUBTEXT, 'margin': '0 0 10px', 'lineHeight': '1.5'})
                    ], style={'background': 'rgba(255,255,255,0.02)', 'padding': '12px', 'borderRadius': '8px', 'border': f'1px solid {BORDER}', 'marginBottom': '10px'}),

                    html.Div([
                        html.H4("4. Death Crucible (Overs 16–20)", style={'color': '#38bdf8', 'fontSize': '12px', 'margin': '0 0 4px'}),
                        html.P("Deliveries in the final four overs when the match margin is under 36 runs with the result still undecided. Death yorkers and boundary balls in this window carry maximal leverage multipliers.", style={'fontSize': '11px', 'color': SUBTEXT, 'margin': '0', 'lineHeight': '1.5'})
                    ], style={'background': 'rgba(255,255,255,0.02)', 'padding': '12px', 'borderRadius': '8px', 'border': f'1px solid {BORDER}'})
                ], style={'flex': '1', 'background': CARD, 'borderRadius': '14px', 'padding': '20px', 'border': f'1px solid {BORDER}'})
            ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '20px'}),

            # ROW 2: WEIGHTAGE MATRIX & XGBOOST ENGINE
            html.Div([
                # Left Column: Mathematical Weightage Matrix
                html.Div([
                    html.H3("EXACT MATHEMATICAL WEIGHTAGE MATRIX", style={'color': RR_GOLD, 'fontSize': '14px', 'fontWeight': '900', 'margin': '0 0 14px', 'letterSpacing': '1px'}),

                    html.H5("BATTING CLUTCH SCORE (0–100 SCALE):", style={'color': RR_PINK, 'fontSize': '11px', 'fontWeight': '800', 'margin': '0 0 6px', 'letterSpacing': '0.5px'}),
                    html.Ul([
                        html.Li([html.B("Counter-Attack Chasing RRR≥10.0 (24%): "), "WPA when chasing steep targets under escalating scoreboard pressure."], style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '4px'}),
                        html.Li([html.B("Crisis Collapse Rescue (20%): "), "WPA resurrecting innings after top-order collapses (≤2 wickets down in Powerplay)."], style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '4px'}),
                        html.Li([html.B("Quality Win Impact (20%): "), "High-pressure WPA generated exclusively in team victories against Tier-1 elite attacks."], style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '4px'}),
                        html.Li([html.B("Authentic MWPPs (14%): "), "Frequency of Authentic Match-Winning Pressure Performances delivering decisive results."], style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '4px'}),
                        html.Li([html.B("Death Chase Finishing (12%): "), "Finishing execution in overs 16–20 under tight margins (<36 runs)."], style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '4px'}),
                        html.Li([html.B("Pressure Consistency Rate (10%): "), "Proportion of high-leverage matches maintaining net-positive match contribution."], style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '4px'}),
                        html.Li([html.B("Specialist Standard Filter: "), "Mandatory threshold of ≥ 750 career balls faced to filter cameos and tailenders."], style={'fontSize': '11px', 'color': RR_GOLD, 'marginBottom': '4px'}),
                        html.Li([html.B("Non-Compensatory Flaw Penalties: "), "Negative Crisis Rescue WPA penalized at 7.5x; negative death execution at 3.0x."], style={'fontSize': '11px', 'color': RED})
                    ], style={'paddingLeft': '14px', 'margin': '0 0 14px'}),

                    html.Hr(style={'borderColor': BORDER, 'margin': '10px 0'}),

                    html.H5("BOWLING CLUTCH SCORE (0–100 SCALE):", style={'color': RR_BLUE, 'fontSize': '11px', 'fontWeight': '800', 'margin': '0 0 6px', 'letterSpacing': '0.5px'}),
                    html.Ul([
                        html.Li([html.B("Quality Runs Saved (30%): "), "ML runs saved across PP (1–6), Middle (7–15), and Death (16–20)."], style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '4px'}),
                        html.Li([html.B("Momentum-Breaking Dots (20%): "), "Dot balls delivered in high-pressure defensive overs."], style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '4px'}),
                        html.Li([html.B("Clutch Wickets (18%): "), "Breakthrough wickets removing set batters under pressure."], style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '4px'}),
                        html.Li([html.B("Pressure Consistency (16%): "), "Proportion of matches with positive pressure contributions."], style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '4px'}),
                        html.Li([html.B("Pressure Economy vs Par (10%): "), "Suppression of run flow below venue par rate."], style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '4px'}),
                        html.Li([html.B("High-Pressure WPA (6%): "), "Net win probability swung towards bowling side."], style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '4px'}),
                        html.Li([html.B("Non-Compensatory Flaw Penalty: "), "Death overs runs leaked above par penalized at 0.80x."], style={'fontSize': '11px', 'color': RED})
                    ], style={'paddingLeft': '14px', 'margin': '0'})
                ], style={'flex': '1', 'background': CARD, 'borderRadius': '14px', 'padding': '20px', 'border': f'1px solid {BORDER}'}),

                # Right Column: Machine Learning Par Engine
                html.Div([
                    html.H3("THE XGBOOST ML CONTEXT ENGINE", style={'color': GREEN, 'fontSize': '14px', 'fontWeight': '900', 'margin': '0 0 14px', 'letterSpacing': '1px'}),
                    html.P("Rather than using crude batting averages or economy rates, our model evaluates performance against ball-by-ball expected runs E[Runs] trained on 190,811 deliveries using 18 predictive contextual features:", style={'fontSize': '11px', 'color': SUBTEXT, 'lineHeight': '1.5', 'margin': '0 0 10px'}),
                    html.Ul([
                        html.Li([html.B("Ground & Venue Par: "), "Historical ground scoring index and pitch pacing rate."], style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '4px'}),
                        html.Li([html.B("Innings Phase: "), "Overs remaining and exact ball number in the current over."], style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '4px'}),
                        html.Li([html.B("Wickets & Pressure: "), "Cumulative wickets lost and current match run rate."], style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '4px'}),
                        html.Li([html.B("Target Dynamics: "), "Required run rate and target differential in second-innings chases."], style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '4px'}),
                        html.Li([html.B("Tactical Matchups: "), "Batter career archetype vs bowler arm and skill (RHB vs SLA, LHB vs Off-Spin)."], style={'fontSize': '11px', 'color': SUBTEXT, 'marginBottom': '4px'}),
                    ], style={'paddingLeft': '14px', 'margin': '0 0 12px'}),
                    html.Hr(style={'borderColor': BORDER, 'margin': '10px 0'}),
                    html.H5("SAMPLE RELIABILITY FILTER:", style={'color': RR_GOLD, 'fontSize': '11px', 'fontWeight': '800', 'margin': '0 0 4px', 'letterSpacing': '0.5px'}),
                    html.P("To prevent single-match flukes, scores are scaled by a square-root reliability curve: Reliability = sqrt(Matches / 45) capped at 1.0. Batters must also satisfy the Substantive Volume Standard (>= 500 balls faced) to eliminate cameo specialists.", style={'fontSize': '11px', 'color': SUBTEXT, 'lineHeight': '1.5', 'margin': '0'})
                ], style={'flex': '1', 'background': CARD, 'borderRadius': '14px', 'padding': '20px', 'border': f'1px solid {BORDER}'})
            ], style={'display': 'flex', 'gap': '16px'})
        ])

# ─────────────────────────────────────────────────────────────────────────────
# ATTRIBUTION CALLBACK
# ─────────────────────────────────────────────────────────────────────────────
@app.callback(Output('player-audit-display', 'children'), [Input('sel-bat', 'value'), Input('sel-bowl', 'value')])
def update_attribution(bat_name, bowl_name):
    b_row = bat_rank[bat_rank['striker_name'] == bat_name]
    bw_row = bowl_rank[bowl_rank['bowler_name'] == bowl_name]

    if b_row.empty or bw_row.empty:
        return html.Div("Player record not found.")

    br = b_row.iloc[0]
    bwr = bw_row.iloc[0]

    b_proof = BAT_PROOFS.get(bat_name, {'badge': 'Qualified Batter', 'desc': '', 'highlight_stat': 'N/A', 'highlight_lbl': 'N/A'})
    bw_proof = BOWL_PROOFS.get(bowl_name, {'badge': 'Qualified Bowler', 'desc': '', 'highlight_stat': 'N/A', 'highlight_lbl': 'N/A'})

    bat_comps = {
        'Tier 3: Counter-Attack Chasing RRR≥10 (24%)': br.get('S_ca', 0) * 0.24,
        'Tier 3: Crisis Collapse Rescue (20%)': br.get('S_rescue', 0) * 0.20,
        'Tier 1: Quality Win Calibration vs Elite (20%)': br.get('S_win_wpa', 0) * 0.20,
        'Tier 2: Authentic Match-Winning Knocks (14%)': br.get('S_mwpp', 0) * 0.14,
        'Tier 3: Death Chase Finishing overs 16-20 (12%)': br.get('S_da', 0) * 0.12,
        'Tier 2: High-Leverage Consistency Rate (10%)': br.get('S_consistency', 0) * 0.10,
        'Non-Compensatory Flaw Penalties': -br.get('fair_deductions', 0)
    }

    bowl_comps = {
        'Tier 1: Opponent Quality Calibration (20%)': bwr.get('S_runs_saved', 0) * 0.20,
        'Tier 2: Pressure Consistency Rate (16%)': bwr.get('S_consistency', 0) * 0.16,
        'Tier 2: Clutch Breakthrough Wickets (10%)': bwr.get('S_wkts', 0) * 0.10,
        'Tier 3: Multi-Phase Defense Allocation (15%)': bwr.get('S_runs_saved', 0) * 0.15,
        'Tier 3: Momentum-Breaking Dots (18%)': bwr.get('S_dots', 0) * 0.18,
        'Tier 3: Pressure Economy vs Par (12%)': bwr.get('S_eco', 0) * 0.12,
        'Tier 3: High-Pressure WPA (5%)': bwr.get('S_wpa', 0) * 0.05,
        'Tier 3: Death Yorkers Executed (4%)': bwr.get('S_yorkers', 0) * 0.04,
        'Flaw Deductions': -bwr.get('fair_deductions', 0)
    }

    def build_waterfall(comps, title):
        filtered = {k: v for k, v in comps.items() if abs(v) > 0.05}
        colors = [GREEN if v >= 0 else RED for v in filtered.values()]
        fig = go.Figure(go.Bar(
            x=list(filtered.values()),
            y=list(filtered.keys()),
            orientation='h',
            marker_color=colors,
            text=[f"{v:+.1f} pts" for v in filtered.values()],
            textposition='outside',
            textfont=dict(color=TEXT, size=10)
        ))
        fig.update_layout(
            title=dict(text=f'<b>{title}</b> — Factor Points Contribution', font=dict(color=TEXT, size=12)),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=TEXT, family='Inter, -apple-system, sans-serif'),
            margin=dict(l=10, r=60, t=35, b=20),
            xaxis=dict(gridcolor='rgba(255,255,255,0.05)', zeroline=True, zerolinecolor=BORDER),
            yaxis=dict(gridcolor='rgba(0,0,0,0)', autorange='reversed'),
            height=320
        )
        return fig

    sub_bat_logs = bat_logs[bat_logs['striker_name'] == bat_name].head(4)
    sub_bowl_logs = bowl_logs[bowl_logs['bowler_name'] == bowl_name].head(4)

    return html.Div([
        html.Div([
            # Batter Panel
            html.Div([
                html.Div([
                    html.Div([
                        html.Span(f"RANK #{br['rank_bat']}", style={'background': RR_PINK, 'color': '#ffffff', 'padding': '2px 8px', 'borderRadius': '4px', 'fontSize': '10px', 'fontWeight': '900'}),
                        html.H4(bat_name.upper(), style={'margin': '4px 0 0', 'color': '#ffffff', 'fontSize': '19px', 'fontWeight': '900'}),
                        html.Span(b_proof['badge'], style={'fontSize': '11px', 'fontWeight': '700', 'color': RR_GOLD}),
                    ]),
                    html.Div([
                        html.Span("INDEX RATING", style={'fontSize': '9px', 'color': SUBTEXT, 'fontWeight': '700', 'letterSpacing': '1px'}),
                        html.H3(f"{br['batting_clutch_score']:.1f}", style={'margin': '0', 'fontSize': '28px', 'color': RR_PINK, 'fontWeight': '900'})
                    ], style={'textAlign': 'right'})
                ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'flex-start', 'marginBottom': '12px'}),

                html.P(b_proof['desc'], style={'fontSize': '11px', 'color': '#cbd5e1', 'lineHeight': '1.5', 'margin': '0 0 12px', 'background': 'rgba(255,255,255,0.02)', 'padding': '10px', 'borderRadius': '8px', 'border': f'1px solid {BORDER}'}),

                html.Div([
                    kpi_card('Consistency', f"{br.get('hp_consistency_rate',0)*100:.1f}%", 'High-Leverage WPA > 0', GREEN),
                    kpi_card('Key Proof Metric', b_proof['highlight_stat'], b_proof['highlight_lbl'], RR_GOLD),
                    kpi_card('Flaw Penalty', f"-{br['fair_deductions']:.1f}", 'Non-Negotiable Flaw', RED if br['fair_deductions'] > 0 else SUBTEXT),
                ], style={'display': 'flex', 'gap': '10px', 'marginBottom': '12px'}),

                dcc.Graph(figure=build_waterfall(bat_comps, bat_name), config={'displayModeBar': False}),
                
                html.Hr(style={'borderColor': BORDER, 'margin': '12px 0'}),
                html.H5("CRUCIBLE MATCH PROOFS (HIGH-LEVERAGE RECORD LOG):", style={'margin': '0 0 8px', 'fontSize': '11px', 'color': RR_PINK, 'textTransform': 'uppercase', 'letterSpacing': '0.5px'}),
                html.Div([
                    html.Div([
                        html.Span(f"[{str(l.get('match_date',''))[:10]}]", style={'color': RR_GOLD, 'fontSize': '10px', 'fontWeight': '700', 'marginRight': '6px'}),
                        html.Span(f"vs {l.get('opponent_team', l.get('away_team','Opp'))} ({l.get('comp_name','')})", style={'color': '#ffffff', 'fontSize': '11px', 'fontWeight': '700'}),
                        html.Span(f" — {l.get('total_runs',0)} runs off {l.get('total_balls',0)}b (HP SR: {l.get('hp_sr',0):.1f})", style={'color': SUBTEXT, 'fontSize': '11px'}),
                        html.Span(f" [WPA: +{l.get('hp_wpa',0):.2f}]", style={'color': GREEN, 'fontSize': '11px', 'fontWeight': '700', 'marginLeft': '6px'}),
                    ], style={'marginBottom': '6px', 'paddingBottom': '4px', 'borderBottom': '1px dashed rgba(255,255,255,0.05)'})
                    for _, l in sub_bat_logs.iterrows()
                ])
            ], style={'flex': '1', 'background': CARD, 'borderRadius': '14px', 'border': f'1px solid {BORDER}', 'padding': '18px'}),

            # Bowler Panel
            html.Div([
                html.Div([
                    html.Div([
                        html.Span(f"RANK #{bwr['rank_bowl']}", style={'background': RR_BLUE, 'color': '#ffffff', 'padding': '2px 8px', 'borderRadius': '4px', 'fontSize': '10px', 'fontWeight': '900'}),
                        html.H4(bowl_name.upper(), style={'margin': '4px 0 0', 'color': '#ffffff', 'fontSize': '19px', 'fontWeight': '900'}),
                        html.Span(bw_proof['badge'], style={'fontSize': '11px', 'fontWeight': '700', 'color': RR_GOLD}),
                    ]),
                    html.Div([
                        html.Span("INDEX RATING", style={'fontSize': '9px', 'color': SUBTEXT, 'fontWeight': '700', 'letterSpacing': '1px'}),
                        html.H3(f"{bwr['bowling_clutch_score']:.1f}", style={'margin': '0', 'fontSize': '28px', 'color': RR_BLUE, 'fontWeight': '900'})
                    ], style={'textAlign': 'right'})
                ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'flex-start', 'marginBottom': '12px'}),

                html.P(bw_proof['desc'], style={'fontSize': '11px', 'color': '#cbd5e1', 'lineHeight': '1.5', 'margin': '0 0 12px', 'background': 'rgba(255,255,255,0.02)', 'padding': '10px', 'borderRadius': '8px', 'border': f'1px solid {BORDER}'}),

                html.Div([
                    kpi_card('Consistency', f"{bwr.get('hp_consistency_rate',0)*100:.1f}%", 'Pressure Economy & Wkts', GREEN),
                    kpi_card('Key Proof Metric', bw_proof['highlight_stat'], bw_proof['highlight_lbl'], RR_GOLD),
                    kpi_card('Flaw Penalty', f"-{bwr['fair_deductions']:.1f}", 'Death Run Leakage Penalty', RED if bwr['fair_deductions'] > 0 else SUBTEXT),
                ], style={'display': 'flex', 'gap': '10px', 'marginBottom': '12px'}),

                dcc.Graph(figure=build_waterfall(bowl_comps, bowl_name), config={'displayModeBar': False}),

                html.Hr(style={'borderColor': BORDER, 'margin': '12px 0'}),
                html.H5("CRUCIBLE MATCH PROOFS (HIGH-LEVERAGE RECORD LOG):", style={'margin': '0 0 8px', 'fontSize': '11px', 'color': RR_BLUE, 'textTransform': 'uppercase', 'letterSpacing': '0.5px'}),
                html.Div([
                    html.Div([
                        html.Span(f"[{str(l.get('match_date',''))[:10]}]", style={'color': RR_GOLD, 'fontSize': '10px', 'fontWeight': '700', 'marginRight': '6px'}),
                        html.Span(f"vs {l.get('opponent_team', l.get('home_team','Opp'))} ({l.get('comp_name','')})", style={'color': '#ffffff', 'fontSize': '11px', 'fontWeight': '700'}),
                        html.Span(f" — {l.get('total_wkts',0)}/{l.get('total_runs',0)} ({l.get('total_balls',0)}b, Eco: {l.get('hp_economy',0):.2f})", style={'color': SUBTEXT, 'fontSize': '11px'}),
                        html.Span(f" [WPA: +{l.get('hp_wpa',0):.2f}]", style={'color': GREEN, 'fontSize': '11px', 'fontWeight': '700', 'marginLeft': '6px'}),
                    ], style={'marginBottom': '6px', 'paddingBottom': '4px', 'borderBottom': '1px dashed rgba(255,255,255,0.05)'})
                    for _, l in sub_bowl_logs.iterrows()
                ])
            ], style={'flex': '1', 'background': CARD, 'borderRadius': '14px', 'border': f'1px solid {BORDER}', 'padding': '18px'}),
        ], style={'display': 'flex', 'gap': '16px'})
    ])

if __name__ == '__main__':
    print("Serving Rajasthan Royals Analytics Studio v3.0 on Port 8050...")
    app.run(debug=False, port=8050, host='127.0.0.1')
