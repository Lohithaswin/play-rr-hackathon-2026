"""
SupeRR Selector Season 2 — Interactive Pressure Performance Dashboard
======================================================================
Run: python dashboard.py
Then open: http://127.0.0.1:8050
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, dash_table
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
print("Loading data...")
df       = pd.read_parquet('bbb_enriched.parquet')
bat_rank = pd.read_parquet('bat_rankings.parquet')
bowl_rank= pd.read_parquet('bowl_rankings.parquet')

valid    = df[df['is_valid_ball']].copy()
pressure = valid[valid['pressure_index'] >= 25].copy()
normal   = valid[valid['pressure_index'] < 10].copy()

# Top 10 lists
bat_top10  = bat_rank.sort_values('batting_pressure_score_adj', ascending=False).head(10).reset_index(drop=True)
bowl_top10 = bowl_rank.sort_values('bowling_pressure_score_adj', ascending=False).head(10).reset_index(drop=True)

# ─────────────────────────────────────────────
# COLOUR PALETTE
# ─────────────────────────────────────────────
BG       = '#0f1117'
CARD     = '#1a1d2e'
BORDER   = '#2d3561'
ACCENT   = '#00d4ff'
GOLD     = '#ffd700'
RED      = '#ff4757'
GREEN    = '#2ed573'
PURPLE   = '#a29bfe'
TEXT     = '#e8eaf6'
SUBTEXT  = '#8892b0'

# ─────────────────────────────────────────────
# HELPER: PRESSURE INDEX BREAKDOWN CHART
# ─────────────────────────────────────────────
def pressure_breakdown_chart():
    components = {
        'Powerplay End\n(Over 5-6, Innings 1)': 'pp_end_pressure',
        'Quick Wickets\n(3+ in 30 balls)':      'quick_wicket_pressure',
        'Dot Ball Pile-up\n(4+ in 5 balls)':    'dot_pressure',
        'Death Overs\n(17-20)':                  'death_pressure',
        'Chase RRR\n(>8 req. run rate)':         'chase_rrr_pressure',
        'Big Total Chase\n(Target ≥185)':        'big_chase_pressure',
        'Knockout / Finals':                      'knockout_pressure',
        'Late Collapse\n(≤3 wkts in death)':     'collapse_pressure',
    }
    pct = []
    for label, col in components.items():
        if col in pressure.columns:
            pct.append({'Component': label.replace('\n', ' '),
                        'Avg Contribution': round(pressure[col].mean(), 2),
                        'Balls Triggered': int((pressure[col] > 0).sum())})

    comp_df = pd.DataFrame(pct).sort_values('Avg Contribution', ascending=True)
    fig = go.Figure(go.Bar(
        x=comp_df['Avg Contribution'],
        y=comp_df['Component'],
        orientation='h',
        marker=dict(
            color=comp_df['Avg Contribution'],
            colorscale=[[0,'#2d3561'],[0.5,ACCENT],[1.0,RED]],
            showscale=False
        ),
        text=[f"{v:.1f}" for v in comp_df['Avg Contribution']],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Avg Contribution: %{x:.2f}<extra></extra>'
    ))
    fig.update_layout(
        title='Pressure Index Component Breakdown<br><sup>Average contribution per pressure ball</sup>',
        paper_bgcolor=BG, plot_bgcolor=CARD,
        font=dict(color=TEXT, size=11),
        margin=dict(l=20, r=60, t=60, b=20),
        xaxis=dict(gridcolor=BORDER, title='Avg Score Added'),
        yaxis=dict(gridcolor='rgba(0,0,0,0)'),
        height=360
    )
    return fig

# ─────────────────────────────────────────────
# HELPER: PRESSURE DISTRIBUTION CHART
# ─────────────────────────────────────────────
def pressure_dist_chart():
    bins = [0,10,20,30,40,50,60,70,80,90,100]
    labels = ['0-10','10-20','20-30','30-40','40-50','50-60','60-70','70-80','80-90','90-100']
    valid2 = valid.copy()
    valid2['pi_bin'] = pd.cut(valid2['pressure_index'], bins=bins, labels=labels, right=False)
    dist = valid2['pi_bin'].value_counts().sort_index()
    colors = [GREEN if i < 2 else ACCENT if i < 4 else GOLD if i < 7 else RED
              for i in range(len(dist))]
    fig = go.Figure(go.Bar(
        x=dist.index.astype(str),
        y=dist.values,
        marker_color=colors,
        hovertemplate='PI Range: %{x}<br>Balls: %{y:,}<extra></extra>'
    ))
    fig.update_layout(
        title='Distribution of Pressure Index Across All Deliveries',
        paper_bgcolor=BG, plot_bgcolor=CARD,
        font=dict(color=TEXT),
        margin=dict(l=20, r=20, t=60, b=20),
        xaxis=dict(title='Pressure Index Range', gridcolor=BORDER),
        yaxis=dict(title='Number of Balls', gridcolor=BORDER),
        height=320
    )
    return fig

# ─────────────────────────────────────────────
# HELPER: BATTER RADAR CHART
# ─────────────────────────────────────────────
def batter_radar(player_name):
    row = bat_rank[bat_rank['striker_name'] == player_name]
    if row.empty:
        return go.Figure()
    r = row.iloc[0]

    categories = ['Strike Rate', 'Average', 'Boundary %', 'Consistency', 'Clutch Ratio']
    pressure_vals = [
        min(r['strike_rate_p'] / 180 * 100, 100),
        min(r['average_p'] / 50 * 100, 100),
        min(r['boundary_rate_p'] / 30 * 100, 100),
        max(0, 100 - r['dot_rate_p']),
        min(r['bat_cpr'] / 2 * 100, 100),
    ]
    baseline_vals = [
        min(r['strike_rate_b'] / 180 * 100, 100) if pd.notna(r.get('strike_rate_b')) else 50,
        min(r['average_b'] / 50 * 100, 100) if pd.notna(r.get('average_b')) else 50,
        min(r['boundary_rate_b'] / 30 * 100, 100) if pd.notna(r.get('boundary_rate_b')) else 50,
        max(0, 100 - r.get('dot_rate_b', 50)),
        50,
    ]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=pressure_vals + [pressure_vals[0]],
        theta=categories + [categories[0]],
        fill='toself',
        name='Under Pressure',
        line=dict(color=ACCENT, width=2),
        fillcolor=f'rgba(0, 212, 255, 0.2)'
    ))
    fig.add_trace(go.Scatterpolar(
        r=baseline_vals + [baseline_vals[0]],
        theta=categories + [categories[0]],
        fill='toself',
        name='Baseline',
        line=dict(color=PURPLE, width=2, dash='dash'),
        fillcolor=f'rgba(162, 155, 254, 0.1)'
    ))
    fig.update_layout(
        polar=dict(
            bgcolor=CARD,
            radialaxis=dict(visible=True, range=[0, 100], gridcolor=BORDER, tickcolor=TEXT),
            angularaxis=dict(gridcolor=BORDER, tickcolor=TEXT)
        ),
        showlegend=True,
        legend=dict(font=dict(color=TEXT)),
        paper_bgcolor=BG,
        font=dict(color=TEXT),
        title=f'{player_name}<br><sup>Pressure vs Baseline</sup>',
        margin=dict(l=40, r=40, t=70, b=40),
        height=380
    )
    return fig

# ─────────────────────────────────────────────
# HELPER: BOWLER RADAR CHART
# ─────────────────────────────────────────────
def bowler_radar(player_name):
    row = bowl_rank[bowl_rank['bowler_name'] == player_name]
    if row.empty:
        return go.Figure()
    r = row.iloc[0]

    categories = ['Economy\nControl', 'Wicket\nRate', 'Dot Ball\n%', 'Boundary\nSuppression', 'Clutch Ratio']
    max_eco = 15
    pressure_vals = [
        max(0, (1 - r['economy_p'] / max_eco) * 100),
        min(r['wickets_p'] / r['balls_bowled_p'] * 600, 100),
        min(r['dot_rate_p'], 100),
        max(0, 100 - r['boundary_rate_p'] * 3),
        min(r['bowl_cpr'] / 2 * 100, 100),
    ]
    baseline_vals = [
        max(0, (1 - r.get('economy_b', 8) / max_eco) * 100),
        min(r.get('wickets_b', 0) / max(r.get('balls_bowled_b', 1), 1) * 600, 100),
        min(r.get('dot_rate_b', 40), 100),
        max(0, 100 - r.get('boundary_rate_b', 10) * 3),
        50,
    ]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=pressure_vals + [pressure_vals[0]],
        theta=categories + [categories[0]],
        fill='toself',
        name='Under Pressure',
        line=dict(color=RED, width=2),
        fillcolor='rgba(255, 71, 87, 0.2)'
    ))
    fig.add_trace(go.Scatterpolar(
        r=baseline_vals + [baseline_vals[0]],
        theta=categories + [categories[0]],
        fill='toself',
        name='Baseline',
        line=dict(color=PURPLE, width=2, dash='dash'),
        fillcolor='rgba(162, 155, 254, 0.1)'
    ))
    fig.update_layout(
        polar=dict(
            bgcolor=CARD,
            radialaxis=dict(visible=True, range=[0, 100], gridcolor=BORDER, tickcolor=TEXT),
            angularaxis=dict(gridcolor=BORDER, tickcolor=TEXT)
        ),
        showlegend=True,
        legend=dict(font=dict(color=TEXT)),
        paper_bgcolor=BG,
        font=dict(color=TEXT),
        title=f'{player_name}<br><sup>Pressure vs Baseline</sup>',
        margin=dict(l=40, r=40, t=70, b=40),
        height=380
    )
    return fig

# ─────────────────────────────────────────────
# HELPER: TOP 10 RANKING BAR CHART
# ─────────────────────────────────────────────
def ranking_bar(top10_df, name_col, score_col, color, title):
    df_plot = top10_df.head(10).copy()
    df_plot['Rank'] = [f"#{i+1}" for i in range(len(df_plot))]
    fig = go.Figure(go.Bar(
        x=df_plot[score_col],
        y=df_plot[name_col] + '  ',
        orientation='h',
        marker=dict(
            color=df_plot[score_col],
            colorscale=[[0, BORDER], [0.5, color], [1.0, GOLD]],
            showscale=False,
            line=dict(color=BORDER, width=0.5)
        ),
        text=[f"  #{i+1}  {s:.1f}" for i, s in enumerate(df_plot[score_col])],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Score: %{x:.2f}<extra></extra>'
    ))
    fig.update_layout(
        title=title,
        paper_bgcolor=BG, plot_bgcolor=CARD,
        font=dict(color=TEXT),
        margin=dict(l=20, r=80, t=60, b=20),
        xaxis=dict(gridcolor=BORDER, range=[0, df_plot[score_col].max() * 1.15]),
        yaxis=dict(gridcolor='rgba(0,0,0,0)', autorange='reversed'),
        height=400
    )
    return fig

# ─────────────────────────────────────────────
# HELPER: PRESSURE BY OVER HEATMAP
# ─────────────────────────────────────────────
def pressure_over_heatmap():
    over_pi = valid.groupby(['innings', 'overid'])['pressure_index'].mean().reset_index()
    over_pi['innings_label'] = over_pi['innings'].map({1: 'Innings 1 (Batting First)', 2: 'Innings 2 (Chasing)'})
    fig = px.density_heatmap(
        over_pi, x='overid', y='innings_label', z='pressure_index',
        color_continuous_scale=[[0,'#1a1d2e'],[0.3,ACCENT],[0.7,GOLD],[1.0,RED]],
        nbinsx=20
    )
    fig.update_layout(
        title='Average Pressure Index by Over and Innings',
        paper_bgcolor=BG, plot_bgcolor=CARD,
        font=dict(color=TEXT),
        margin=dict(l=20, r=20, t=60, b=20),
        coloraxis_colorbar=dict(title='Avg PI', tickcolor=TEXT, titlefont=dict(color=TEXT)),
        xaxis=dict(title='Over', gridcolor=BORDER, dtick=1),
        yaxis=dict(title='', gridcolor='rgba(0,0,0,0)'),
        height=250
    )
    return fig

# ─────────────────────────────────────────────
# HELPER: PRESSURE SITUATION TIMELINE
# ─────────────────────────────────────────────
def pressure_situation_summary():
    cats = {
        'Death Overs (17-20)':          (valid['overid'] >= 17).sum(),
        'High Chase RRR (>9)':          (valid['required_rr'] > 9).sum(),
        'Quick Wickets (3+ in 30)':     (valid['recent_wickets'] >= 3).sum(),
        'Powerplay End (Ov 5-6, Inn1)': ((valid['overid'].isin([5,6])) & (valid['innings']==1)).sum(),
        'Dot Ball Pile-up (4+ in 5)':   (valid['recent_dots'] >= 4).sum(),
        'Big Total Chase (Tgt≥185)':    ((valid['innings']==2) & (valid['target']>=185)).sum(),
        'Knockout / Finals':            ((valid['knock_out']==1) | (valid['stage'].isin(['Final','Semi Final']))).sum(),
        'Late Collapse (≤3 wkts)':      ((valid['overid']>=15) & (valid['wickets_remaining']<=3)).sum(),
    }
    df_cat = pd.DataFrame({'Situation': list(cats.keys()), 'Balls': list(cats.values())})
    df_cat = df_cat.sort_values('Balls', ascending=True)
    fig = go.Figure(go.Bar(
        x=df_cat['Balls'],
        y=df_cat['Situation'],
        orientation='h',
        marker=dict(color=df_cat['Balls'], colorscale=[[0,BORDER],[0.5,PURPLE],[1.0,ACCENT]]),
        hovertemplate='<b>%{y}</b><br>Balls: %{x:,}<extra></extra>'
    ))
    fig.update_layout(
        title='Pressure Situation Frequency Across Dataset',
        paper_bgcolor=BG, plot_bgcolor=CARD,
        font=dict(color=TEXT),
        margin=dict(l=20, r=20, t=60, b=20),
        xaxis=dict(title='Number of Balls', gridcolor=BORDER),
        yaxis=dict(gridcolor='rgba(0,0,0,0)'),
        height=330
    )
    return fig

# ─────────────────────────────────────────────
# STAT CARD HELPER
# ─────────────────────────────────────────────
def stat_card(label, value, sub='', color=ACCENT):
    return html.Div([
        html.P(label, style={'margin':'0','fontSize':'11px','color':SUBTEXT,'letterSpacing':'1px','textTransform':'uppercase'}),
        html.H3(value, style={'margin':'4px 0','fontSize':'28px','color':color,'fontWeight':'800'}),
        html.P(sub, style={'margin':'0','fontSize':'11px','color':SUBTEXT}),
    ], style={
        'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px',
        'padding':'18px 20px','textAlign':'center','flex':'1','minWidth':'140px'
    })

# ─────────────────────────────────────────────
# BUILD DASH APP
# ─────────────────────────────────────────────
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "SupeRR Selector — Pressure Performance Dashboard"

GLOBAL_STATS = {
    'total_matches': df['match_id'].nunique(),
    'total_balls':   len(valid),
    'pressure_balls': len(pressure),
    'pressure_pct': len(pressure)/len(valid)*100,
    'eligible_batters': len(bat_rank),
    'eligible_bowlers': len(bowl_rank),
}

bat_dropdown_options  = [{'label': n, 'value': n} for n in bat_rank.sort_values('batting_pressure_score_adj', ascending=False)['striker_name']]
bowl_dropdown_options = [{'label': n, 'value': n} for n in bowl_rank.sort_values('bowling_pressure_score_adj', ascending=False)['bowler_name']]

app.layout = html.Div([
    # ── HEADER
    html.Div([
        html.H1("🏏 SupeRR Selector Season 2", style={'margin':'0','fontSize':'32px','color':GOLD,'fontWeight':'900'}),
        html.P("Pressure Performance Dashboard · IPL & T20I 2022–2026",
               style={'margin':'6px 0 0','color':SUBTEXT,'fontSize':'14px'}),
    ], style={'background':CARD,'borderBottom':f'2px solid {BORDER}',
              'padding':'24px 32px','textAlign':'center'}),

    # ── TABS
    dcc.Tabs(id='tabs', value='overview', children=[
        dcc.Tab(label='📊 Overview',       value='overview'),
        dcc.Tab(label='🔥 Pressure Model', value='pressure'),
        dcc.Tab(label='🏏 Top 10 Batters', value='batters'),
        dcc.Tab(label='🎳 Top 10 Bowlers', value='bowlers'),
        dcc.Tab(label='🔍 Player Drill-Down', value='drilldown'),
    ], style={'fontFamily':'sans-serif'},
       colors={'border':BORDER,'primary':ACCENT,'background':CARD}),

    html.Div(id='tab-content', style={'padding':'24px 28px','background':BG,'minHeight':'80vh'}),

], style={'background':BG,'fontFamily':'"Inter", sans-serif','color':TEXT,'minHeight':'100vh'})


# ─────────────────────────────────────────────
# CALLBACKS
# ─────────────────────────────────────────────
@app.callback(Output('tab-content','children'), Input('tabs','value'))
def render_tab(tab):

    # ── OVERVIEW TAB
    if tab == 'overview':
        return html.Div([
            # Stat Cards Row
            html.Div([
                stat_card("Matches Analysed",  f"{GLOBAL_STATS['total_matches']:,}", "IPL + T20I 2022–2026", GOLD),
                stat_card("Total Deliveries",  f"{GLOBAL_STATS['total_balls']:,}", "Valid balls", ACCENT),
                stat_card("Pressure Balls",    f"{GLOBAL_STATS['pressure_balls']:,}", f"{GLOBAL_STATS['pressure_pct']:.1f}% of all balls", RED),
                stat_card("Eligible Batters",  f"{GLOBAL_STATS['eligible_batters']}", "≥50 pressure balls faced", GREEN),
                stat_card("Eligible Bowlers",  f"{GLOBAL_STATS['eligible_bowlers']}", "≥50 pressure balls bowled", PURPLE),
            ], style={'display':'flex','gap':'12px','flexWrap':'wrap','marginBottom':'24px'}),

            # Row: Batting & Bowling Top 10 bar charts
            html.Div([
                html.Div([dcc.Graph(figure=ranking_bar(bat_top10,'striker_name','batting_pressure_score_adj',
                                                        ACCENT,'🏏 Top 10 Batters Under Pressure'))],
                          style={'flex':'1','minWidth':'400px'}),
                html.Div([dcc.Graph(figure=ranking_bar(bowl_top10,'bowler_name','bowling_pressure_score_adj',
                                                        RED,'🎳 Top 10 Bowlers Under Pressure'))],
                          style={'flex':'1','minWidth':'400px'}),
            ], style={'display':'flex','gap':'16px','marginBottom':'24px'}),

            # Pressure over heatmap
            dcc.Graph(figure=pressure_over_heatmap()),
        ])

    # ── PRESSURE MODEL TAB
    elif tab == 'pressure':
        return html.Div([
            html.H2("🔥 How We Define Pressure", style={'color':ACCENT,'marginBottom':'8px'}),
            html.P([
                "Each delivery receives a ", html.Strong("Pressure Index (0–100)"),
                " composed of 8 independent signals. A ball is classified as a ",
                html.Strong("Pressure Situation"), " when PI ≥ 25.",
            ], style={'color':SUBTEXT,'marginBottom':'20px','lineHeight':'1.7'}),

            html.Div([
                html.Div([dcc.Graph(figure=pressure_breakdown_chart())],
                          style={'flex':'1','minWidth':'400px'}),
                html.Div([dcc.Graph(figure=pressure_situation_summary())],
                          style={'flex':'1','minWidth':'400px'}),
            ], style={'display':'flex','gap':'16px','marginBottom':'24px'}),

            dcc.Graph(figure=pressure_dist_chart()),

            # Pressure components table
            html.Div([
                html.H3("Pressure Component Definitions", style={'color':GOLD,'marginBottom':'12px'}),
                dash_table.DataTable(
                    data=[
                        {'Component':'Powerplay End (Ov 5-6, Inn1)','Weight':'15','Trigger':'Over 5 or 6 in Innings 1','Rationale':'Last powerplay overs are pivotal for setting/scoring a launch pad'},
                        {'Component':'Quick Wickets','Weight':'25','Trigger':'3+ wickets in last 30 valid balls','Rationale':'Rapid collapse creates batting/bowling pressure'},
                        {'Component':'Dot Ball Pile-up','Weight':'15','Trigger':'4+ dots in last 5 balls','Rationale':'Scoreboard pressure builds, batter must take risks'},
                        {'Component':'Death Overs (17-20)','Weight':'20','Trigger':'Over ≥ 17','Rationale':'Highest-stakes overs — maximise runs / take wickets'},
                        {'Component':'Chase RRR > 8','Weight':'20','Trigger':'Required Run Rate > 8 (Innings 2)','Rationale':'High RRR = do-or-die batting & must-defend bowling'},
                        {'Component':'Big Total Chase (Tgt≥185)','Weight':'10','Trigger':'Innings 2, target ≥ 185','Rationale':'Chasing a huge score demands aggression from ball 1'},
                        {'Component':'Knockout / Finals','Weight':'10','Trigger':'knock_out=1 or stage=Final/SF/QF/EL','Rationale':'Elimination pressure amplifies every delivery'},
                        {'Component':'Late Collapse (≤3 wkts)','Weight':'15','Trigger':'Over ≥ 15 and wickets_remaining ≤ 3','Rationale':'Tail-end batting/bowling is inherently high stakes'},
                    ],
                    columns=[{'name':c,'id':c} for c in ['Component','Weight','Trigger','Rationale']],
                    style_table={'overflowX':'auto'},
                    style_cell={'background':CARD,'color':TEXT,'border':f'1px solid {BORDER}','padding':'10px 14px','fontSize':'12px'},
                    style_header={'background':BORDER,'color':GOLD,'fontWeight':'700'},
                )
            ], style={'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px','padding':'20px','marginTop':'20px'}),
        ])

    # ── BATTERS TAB
    elif tab == 'batters':
        cols_display = [
            {'name':'#','id':'rank'},
            {'name':'Player','id':'striker_name'},
            {'name':'Balls (P)','id':'balls_faced_p'},
            {'name':'Runs (P)','id':'runs_scored_p'},
            {'name':'SR (P)','id':'strike_rate_p'},
            {'name':'Avg (P)','id':'average_p'},
            {'name':'Boundary % (P)','id':'boundary_rate_p'},
            {'name':'SR (Baseline)','id':'strike_rate_b'},
            {'name':'Avg (Baseline)','id':'average_b'},
            {'name':'Clutch Ratio','id':'bat_cpr'},
            {'name':'Pressure Score','id':'batting_pressure_score_adj'},
        ]
        table_data = bat_top10.copy()
        table_data['rank'] = [f"#{i+1}" for i in range(len(table_data))]
        for col in ['strike_rate_p','average_p','boundary_rate_p','strike_rate_b','average_b','bat_cpr','batting_pressure_score_adj']:
            table_data[col] = table_data[col].round(2)
        for col in ['balls_faced_p','runs_scored_p']:
            table_data[col] = table_data[col].astype(int)

        fig_bars = ranking_bar(bat_top10,'striker_name','batting_pressure_score_adj',ACCENT,'🏏 Top 10 Batters Under Pressure — Composite Score')

        return html.Div([
            html.H2("🏏 Top 10 Batters Under Pressure", style={'color':ACCENT}),
            html.P("Ranked by composite Pressure Score = 65% absolute performance (SR, Avg, Boundary%) + 35% Clutch Performance Ratio vs baseline.",
                   style={'color':SUBTEXT,'marginBottom':'20px'}),
            dcc.Graph(figure=fig_bars),
            html.Div([
                dash_table.DataTable(
                    id='bat-table',
                    data=table_data[[c['id'] for c in cols_display]].to_dict('records'),
                    columns=cols_display,
                    sort_action='native',
                    style_table={'overflowX':'auto'},
                    style_cell={'background':CARD,'color':TEXT,'border':f'1px solid {BORDER}','padding':'12px 14px','fontSize':'13px'},
                    style_header={'background':BORDER,'color':GOLD,'fontWeight':'700','fontSize':'13px'},
                    style_data_conditional=[
                        {'if':{'filter_query':'{rank} = "#1"'},'background':'rgba(255,215,0,0.1)','color':GOLD,'fontWeight':'700'},
                        {'if':{'filter_query':'{rank} = "#2"'},'background':'rgba(192,192,192,0.08)'},
                        {'if':{'filter_query':'{rank} = "#3"'},'background':'rgba(205,127,50,0.08)'},
                    ]
                )
            ], style={'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px','padding':'16px','marginTop':'20px'}),

            # Quick radars for top 3
            html.H3("Top 3 — Pressure vs Baseline Radar", style={'color':GOLD,'marginTop':'28px'}),
            html.Div([
                html.Div([dcc.Graph(figure=batter_radar(bat_top10.iloc[i]['striker_name']))],
                          style={'flex':'1','minWidth':'300px'})
                for i in range(3)
            ], style={'display':'flex','gap':'16px'}),
        ])

    # ── BOWLERS TAB
    elif tab == 'bowlers':
        cols_display = [
            {'name':'#','id':'rank'},
            {'name':'Player','id':'bowler_name'},
            {'name':'Balls (P)','id':'balls_bowled_p'},
            {'name':'Wickets (P)','id':'wickets_p'},
            {'name':'Economy (P)','id':'economy_p'},
            {'name':'Dot % (P)','id':'dot_rate_p'},
            {'name':'Bdry % (P)','id':'boundary_rate_p'},
            {'name':'Economy (Base)','id':'economy_b'},
            {'name':'Clutch Ratio','id':'bowl_cpr'},
            {'name':'Pressure Score','id':'bowling_pressure_score_adj'},
        ]
        table_data = bowl_top10.copy()
        table_data['rank'] = [f"#{i+1}" for i in range(len(table_data))]
        for col in ['economy_p','dot_rate_p','boundary_rate_p','economy_b','bowl_cpr','bowling_pressure_score_adj']:
            table_data[col] = table_data[col].round(2)
        for col in ['balls_bowled_p','wickets_p']:
            table_data[col] = table_data[col].astype(int)

        fig_bars = ranking_bar(bowl_top10,'bowler_name','bowling_pressure_score_adj',RED,'🎳 Top 10 Bowlers Under Pressure — Composite Score')

        return html.Div([
            html.H2("🎳 Top 10 Bowlers Under Pressure", style={'color':RED}),
            html.P("Ranked by composite Pressure Score = 65% absolute performance (Economy, Wickets, Dots, Boundaries-suppressed) + 35% Clutch Ratio vs baseline.",
                   style={'color':SUBTEXT,'marginBottom':'20px'}),
            dcc.Graph(figure=fig_bars),
            html.Div([
                dash_table.DataTable(
                    id='bowl-table',
                    data=table_data[[c['id'] for c in cols_display]].to_dict('records'),
                    columns=cols_display,
                    sort_action='native',
                    style_table={'overflowX':'auto'},
                    style_cell={'background':CARD,'color':TEXT,'border':f'1px solid {BORDER}','padding':'12px 14px','fontSize':'13px'},
                    style_header={'background':BORDER,'color':GOLD,'fontWeight':'700','fontSize':'13px'},
                    style_data_conditional=[
                        {'if':{'filter_query':'{rank} = "#1"'},'background':'rgba(255,215,0,0.1)','color':GOLD,'fontWeight':'700'},
                        {'if':{'filter_query':'{rank} = "#2"'},'background':'rgba(192,192,192,0.08)'},
                        {'if':{'filter_query':'{rank} = "#3"'},'background':'rgba(205,127,50,0.08)'},
                    ]
                )
            ], style={'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px','padding':'16px','marginTop':'20px'}),

            # Quick radars for top 3
            html.H3("Top 3 — Pressure vs Baseline Radar", style={'color':GOLD,'marginTop':'28px'}),
            html.Div([
                html.Div([dcc.Graph(figure=bowler_radar(bowl_top10.iloc[i]['bowler_name']))],
                          style={'flex':'1','minWidth':'300px'})
                for i in range(3)
            ], style={'display':'flex','gap':'16px'}),
        ])

    # ── DRILL-DOWN TAB
    elif tab == 'drilldown':
        return html.Div([
            html.H2("🔍 Player Drill-Down", style={'color':PURPLE}),
            html.Div([
                # Batter selector
                html.Div([
                    html.Label("Select Batter", style={'color':SUBTEXT,'marginBottom':'6px','display':'block'}),
                    dcc.Dropdown(
                        id='bat-selector', options=bat_dropdown_options,
                        value=bat_top10.iloc[0]['striker_name'],
                        style={'background':CARD,'color':'#000'}
                    ),
                    dcc.Graph(id='bat-radar')
                ], style={'flex':'1','minWidth':'380px'}),

                # Bowler selector
                html.Div([
                    html.Label("Select Bowler", style={'color':SUBTEXT,'marginBottom':'6px','display':'block'}),
                    dcc.Dropdown(
                        id='bowl-selector', options=bowl_dropdown_options,
                        value=bowl_top10.iloc[0]['bowler_name'],
                        style={'background':CARD,'color':'#000'}
                    ),
                    dcc.Graph(id='bowl-radar')
                ], style={'flex':'1','minWidth':'380px'}),
            ], style={'display':'flex','gap':'24px','flexWrap':'wrap'}),

            # Stats comparison cards
            html.Div(id='player-stats-cards', style={'marginTop':'20px'}),
        ])

    return html.Div("Tab not found", style={'color':RED})


# Drill-down callbacks
@app.callback(Output('bat-radar','figure'), Input('bat-selector','value'))
def update_bat_radar(name):
    return batter_radar(name) if name else go.Figure()

@app.callback(Output('bowl-radar','figure'), Input('bowl-selector','value'))
def update_bowl_radar(name):
    return bowler_radar(name) if name else go.Figure()

@app.callback(Output('player-stats-cards','children'),
              [Input('bat-selector','value'), Input('bowl-selector','value')])
def update_stats_cards(bat_name, bowl_name):
    cards = []
    if bat_name:
        r = bat_rank[bat_rank['striker_name']==bat_name].iloc[0]
        cards.append(html.Div([
            html.H4(f"🏏 {bat_name}", style={'color':ACCENT,'margin':'0 0 12px'}),
            html.Div([
                stat_card("SR (Pressure)", f"{r['strike_rate_p']:.1f}", "balls faced", ACCENT),
                stat_card("Average (P)", f"{r['average_p']:.1f}", "per dismissal", GREEN),
                stat_card("SR (Baseline)", f"{r['strike_rate_b']:.1f}" if pd.notna(r.get('strike_rate_b')) else "N/A", "normal play", PURPLE),
                stat_card("Clutch Ratio", f"{r['bat_cpr']:.2f}", ">1 = better under P", GOLD),
                stat_card("Pressure Score", f"{r['batting_pressure_score_adj']:.1f}", "/100", RED),
            ], style={'display':'flex','gap':'10px','flexWrap':'wrap'}),
        ], style={'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px','padding':'18px','marginBottom':'14px'}))

    if bowl_name:
        r = bowl_rank[bowl_rank['bowler_name']==bowl_name].iloc[0]
        cards.append(html.Div([
            html.H4(f"🎳 {bowl_name}", style={'color':RED,'margin':'0 0 12px'}),
            html.Div([
                stat_card("Economy (P)", f"{r['economy_p']:.2f}", "runs per over", RED),
                stat_card("Wickets (P)", f"{int(r['wickets_p'])}", "under pressure", GREEN),
                stat_card("Dot % (P)", f"{r['dot_rate_p']:.1f}%", "dot balls", ACCENT),
                stat_card("Clutch Ratio", f"{r['bowl_cpr']:.2f}", ">1 = better under P", GOLD),
                stat_card("Pressure Score", f"{r['bowling_pressure_score_adj']:.1f}", "/100", PURPLE),
            ], style={'display':'flex','gap':'10px','flexWrap':'wrap'}),
        ], style={'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px','padding':'18px'}))

    return cards


# ─────────────────────────────────────────────
# LAUNCH
# ─────────────────────────────────────────────
if __name__ == '__main__':
    print("\n" + "="*55)
    print("  SupeRR Selector Pressure Dashboard")
    print("  Open: http://127.0.0.1:8050")
    print("="*55 + "\n")
    app.run(debug=False, port=8050)
