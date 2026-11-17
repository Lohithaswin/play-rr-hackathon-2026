"""
SupeRR Selector Season 2 — Advanced WPA Dashboard v2
=====================================================
Run: python dashboard_v2.py  →  http://127.0.0.1:8050
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
df       = pd.read_parquet('bbb_v2_wpa.parquet')
valid    = pd.read_parquet('valid_v2.parquet')
bat_rank = pd.read_parquet('bat_rankings_v2.parquet')
bowl_rank= pd.read_parquet('bowl_rankings_v2.parquet')

bat_top10  = bat_rank.sort_values('batting_clutch_score', ascending=False).head(10).reset_index(drop=True)
bowl_top10 = bowl_rank.sort_values('bowling_clutch_score', ascending=False).head(10).reset_index(drop=True)

# ─────────────────────────────────────────────
# COLOUR PALETTE
# ─────────────────────────────────────────────
BG      = '#0a0d1a'
CARD    = '#141828'
CARD2   = '#1c2135'
BORDER  = '#252d4a'
ACCENT  = '#00c8ff'
GOLD    = '#f5c518'
RED     = '#ff4b6e'
GREEN   = '#00e5a0'
PURPLE  = '#9b8ef5'
ORANGE  = '#ff9f43'
TEXT    = '#e8ecf8'
SUBTEXT = '#6b7db3'

def stat_card(label, value, sub='', color=ACCENT):
    return html.Div([
        html.P(label, style={'margin':'0','fontSize':'10px','color':SUBTEXT,
                             'letterSpacing':'1.5px','textTransform':'uppercase','fontWeight':'600'}),
        html.H3(value, style={'margin':'6px 0 2px','fontSize':'26px','color':color,'fontWeight':'800'}),
        html.P(sub, style={'margin':'0','fontSize':'11px','color':SUBTEXT}),
    ], style={
        'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'14px',
        'padding':'16px 20px','textAlign':'center','flex':'1','minWidth':'130px',
        'borderTop':f'3px solid {color}'
    })

# ─────────────────────────────────────────────
# CHART HELPERS
# ─────────────────────────────────────────────

def ranking_bar(top10_df, name_col, score_col, color, title, label_cols=None):
    df_p = top10_df.head(10).copy().reset_index(drop=True)
    medals = ['🥇','🥈','🥉'] + [f'#{i+1}' for i in range(3,10)]

    # Build hover text
    if label_cols:
        hover = ['<br>'.join([f"<b>{row[name_col]}</b>"] +
                 [f"{k}: {row[k]:.2f}" if isinstance(row[k], float) else f"{k}: {row[k]}"
                  for k,v in label_cols.items()])
                 for _, row in df_p.iterrows()]
    else:
        hover = df_p[name_col].tolist()

    colors_bar = [GOLD if i==0 else '#c0c0c0' if i==1 else '#cd7f32' if i==2
                  else color for i in range(len(df_p))]

    fig = go.Figure(go.Bar(
        x=df_p[score_col],
        y=[f"{medals[i]}  {df_p.iloc[i][name_col]}" for i in range(len(df_p))],
        orientation='h',
        marker=dict(color=colors_bar, line=dict(color='rgba(0,0,0,0)')),
        text=[f"  {v:.1f}" for v in df_p[score_col]],
        textposition='outside',
        textfont=dict(color=TEXT, size=11),
        hovertemplate='%{y}<br>Score: %{x:.2f}<extra></extra>',
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(color=TEXT, size=15)),
        paper_bgcolor=BG, plot_bgcolor=CARD,
        font=dict(color=TEXT, family='Inter, sans-serif'),
        margin=dict(l=20, r=70, t=50, b=20),
        xaxis=dict(gridcolor=BORDER, range=[0, df_p[score_col].max()*1.18], zeroline=False),
        yaxis=dict(gridcolor='rgba(0,0,0,0)', autorange='reversed'),
        height=420
    )
    return fig


def radar_chart(player_name, is_batter=True):
    if is_batter:
        row_df = bat_rank[bat_rank['striker_name'] == player_name]
        if row_df.empty: return go.Figure()
        r = row_df.iloc[0]
        categories = ['Strike Rate', 'Average', 'WPA Score', 'Boundary %', 'Pressure Release']
        pressure_vals = [
            min(r['sr'] / 200 * 100, 100),
            min(r.get('avg', 0) / 60 * 100, 100) if pd.notna(r.get('avg')) else 0,
            min(max(r.get('wpa_score', 0), 0), 100),
            min(r.get('bdry_pct', 0) / 35 * 100, 100),
            min(r.get('release_per_50', 0) / 5 * 100, 100),
        ]
        baseline_vals = [
            min(r.get('sr_base', 130) / 200 * 100, 100),
            min(r.get('avg_base', 25) / 60 * 100, 100) if pd.notna(r.get('avg_base')) else 0,
            50, 50, 50,
        ]
        fill_p, fill_b = f'rgba(0,200,255,0.25)', 'rgba(155,142,245,0.1)'
        line_p = dict(color=ACCENT, width=2.5)
    else:
        row_df = bowl_rank[bowl_rank['bowler_name'] == player_name]
        if row_df.empty: return go.Figure()
        r = row_df.iloc[0]
        categories = ['Economy\nControl', 'Wicket Rate', 'WPA Score', 'Dot Ball %', 'Shutdown Overs']
        pressure_vals = [
            max(0, (1 - r['economy'] / 15) * 100),
            min(r.get('wkt_pct', 0) * 15, 100),
            min(max(r.get('wpa_score', 0), 0), 100),
            min(r.get('dot_pct', 0), 100),
            min(r.get('shutdown_per_10', 0) / 3 * 100, 100),
        ]
        baseline_vals = [
            max(0, (1 - r.get('eco_base', 8) / 15) * 100),
            50, 50,
            min(r.get('dot_pct_base', 35), 100),
            50,
        ]
        fill_p, fill_b = 'rgba(255,75,110,0.25)', 'rgba(155,142,245,0.1)'
        line_p = dict(color=RED, width=2.5)

    cats_closed = categories + [categories[0]]
    pv_closed   = pressure_vals + [pressure_vals[0]]
    bv_closed   = baseline_vals + [baseline_vals[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=pv_closed, theta=cats_closed, fill='toself',
        name='Under Pressure', line=line_p, fillcolor=fill_p))
    fig.add_trace(go.Scatterpolar(r=bv_closed, theta=cats_closed, fill='toself',
        name='Baseline', line=dict(color=PURPLE, width=1.5, dash='dot'),
        fillcolor=fill_b))
    fig.update_layout(
        polar=dict(bgcolor=CARD2,
            radialaxis=dict(visible=True, range=[0,100], gridcolor=BORDER, tickfont=dict(color=SUBTEXT, size=9)),
            angularaxis=dict(gridcolor=BORDER, tickfont=dict(color=TEXT, size=10))),
        showlegend=True,
        legend=dict(font=dict(color=TEXT, size=10), bgcolor='rgba(0,0,0,0)'),
        paper_bgcolor=BG, font=dict(color=TEXT),
        title=dict(text=f'<b>{player_name}</b><br><sup>Pressure vs Baseline</sup>',
                   font=dict(color=TEXT, size=13)),
        margin=dict(l=50, r=50, t=70, b=50), height=380
    )
    return fig


def wpa_distribution_chart(is_batter=True):
    if is_batter:
        data = valid[valid['is_high_pressure']].groupby('striker_name')['wpa_batting'].sum()
        label = 'Total WPA Added (Batting) in Pressure Situations'
        color = ACCENT
    else:
        data = valid[valid['is_high_pressure']].groupby('bowler_name')['wpa_bowling'].sum()
        label = 'Total WPA Added (Bowling) in Pressure Situations'
        color = RED

    top = data.nlargest(15)
    fig = go.Figure(go.Bar(
        x=top.values, y=top.index, orientation='h',
        marker=dict(color=top.values, colorscale=[[0,BORDER],[0.5,color],[1,GOLD]]),
        hovertemplate='<b>%{y}</b><br>WPA: %{x:.3f}<extra></extra>'
    ))
    fig.update_layout(
        title=label, paper_bgcolor=BG, plot_bgcolor=CARD,
        font=dict(color=TEXT), margin=dict(l=20,r=20,t=50,b=20),
        xaxis=dict(gridcolor=BORDER, title='Win Probability Added'),
        yaxis=dict(gridcolor='rgba(0,0,0,0)', autorange='reversed'),
        height=380
    )
    return fig


def leverage_vs_wpa_scatter(is_batter=True):
    press = valid[valid['is_high_pressure']].copy()
    if is_batter:
        g = press.groupby(['striker_id','striker_name']).agg(
            avg_li=('leverage_index_norm','mean'),
            total_wpa=('wpa_batting','sum'),
            balls=('runs','count'),
        ).reset_index().rename(columns={'striker_name':'name'})
        color, hover_name = ACCENT, 'Batter'
    else:
        g = press.groupby(['bowler_id','bowler_name']).agg(
            avg_li=('leverage_index_norm','mean'),
            total_wpa=('wpa_bowling','sum'),
            balls=('runs','count'),
        ).reset_index().rename(columns={'bowler_name':'name'})
        color, hover_name = RED, 'Bowler'

    g = g[g['balls'] >= 50]

    fig = go.Figure(go.Scatter(
        x=g['avg_li'], y=g['total_wpa'],
        mode='markers+text',
        marker=dict(size=g['balls']/10, color=g['total_wpa'],
                    colorscale=[[0,BORDER],[0.5,color],[1,GOLD]],
                    sizemin=5, opacity=0.8,
                    line=dict(color=BORDER, width=0.5)),
        text=g['name'], textposition='top center',
        textfont=dict(size=8, color=TEXT),
        hovertemplate=f'<b>%{{text}}</b><br>Avg LI: %{{x:.3f}}<br>Total WPA: %{{y:.3f}}<br>Balls: %{{marker.size:.0f}}<extra></extra>'
    ))
    fig.add_hline(y=0, line_dash='dash', line_color=SUBTEXT)
    fig.update_layout(
        title=f'Leverage Index vs Win Probability Added — {hover_name}s',
        paper_bgcolor=BG, plot_bgcolor=CARD,
        font=dict(color=TEXT), margin=dict(l=20,r=20,t=50,b=20),
        xaxis=dict(title='Avg Leverage Index (High = more critical balls faced)',
                   gridcolor=BORDER),
        yaxis=dict(title='Total WPA in Pressure Situations', gridcolor=BORDER),
        height=400
    )
    return fig


def pressure_over_heatmap():
    over_li = valid.groupby(['innings','overid'])['leverage_index_norm'].mean().reset_index()
    over_li['innings_label'] = over_li['innings'].map(
        {1:'Innings 1 (Batting First)', 2:'Innings 2 (Chasing)'})
    pivot = over_li.pivot(index='innings_label', columns='overid', values='leverage_index_norm')
    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns.astype(str), y=pivot.index,
        colorscale=[[0,CARD],[0.4,ACCENT],[0.75,GOLD],[1.0,RED]],
        hovertemplate='Innings: %{y}<br>Over: %{x}<br>Avg LI: %{z:.3f}<extra></extra>',
        colorbar=dict(title='Avg LI', tickfont=dict(color=TEXT), titlefont=dict(color=TEXT))
    ))
    fig.update_layout(
        title='Average Leverage Index by Over — Where are the Most Critical Moments?',
        paper_bgcolor=BG, plot_bgcolor=CARD,
        font=dict(color=TEXT), margin=dict(l=20,r=20,t=50,b=20),
        xaxis=dict(title='Over Number', tickmode='linear'),
        yaxis=dict(title=''),
        height=240
    )
    return fig


def shutdown_chart():
    shutdown = valid[valid.get('is_high_pressure', False) if 'is_high_pressure' in valid.columns else valid['leverage_index_norm'] > 0.4].copy()
    if 'shutdown_overs' not in bowl_rank.columns:
        return go.Figure()
    top_sd = bowl_rank.nlargest(15,'shutdown_overs')[['bowler_name','shutdown_overs','bowling_clutch_score']]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=top_sd['bowler_name'], y=top_sd['shutdown_overs'],
        name='Shutdown Overs',
        marker_color=GREEN,
        hovertemplate='<b>%{x}</b><br>Shutdown Overs: %{y}<extra></extra>'
    ))
    fig.update_layout(
        title='Shutdown Overs — Bowlers Who Killed High-Scoring Momentum',
        paper_bgcolor=BG, plot_bgcolor=CARD,
        font=dict(color=TEXT), margin=dict(l=20,r=20,t=50,b=20),
        xaxis=dict(tickangle=-30, gridcolor='rgba(0,0,0,0)'),
        yaxis=dict(title='Number of Shutdown Overs', gridcolor=BORDER),
        height=330
    )
    return fig


def pressure_release_chart():
    top_rel = bat_rank.nlargest(15,'release_moments')[['striker_name','release_moments','batting_clutch_score']]
    fig = go.Figure(go.Bar(
        x=top_rel['striker_name'], y=top_rel['release_moments'],
        marker_color=ORANGE,
        hovertemplate='<b>%{x}</b><br>Pressure Release Moments: %{y}<extra></extra>'
    ))
    fig.update_layout(
        title='Pressure Release Moments — Batters Who Broke the Pressure',
        paper_bgcolor=BG, plot_bgcolor=CARD,
        font=dict(color=TEXT), margin=dict(l=20,r=20,t=50,b=20),
        xaxis=dict(tickangle=-30, gridcolor='rgba(0,0,0,0)'),
        yaxis=dict(title='Pressure Release Moments', gridcolor=BORDER),
        height=330
    )
    return fig


# ─────────────────────────────────────────────
# BUILD APP
# ─────────────────────────────────────────────
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "SupeRR Selector v2 — WPA Pressure Dashboard"

STATS = {
    'matches': df['match_id'].nunique(),
    'valid': len(valid),
    'pressure': int(valid['is_high_pressure'].sum()),
    'pct': valid['is_high_pressure'].mean()*100,
    'batters': len(bat_rank),
    'bowlers': len(bowl_rank),
}

bat_opts  = [{'label':n,'value':n} for n in bat_rank.sort_values('batting_clutch_score',ascending=False)['striker_name']]
bowl_opts = [{'label':n,'value':n} for n in bowl_rank.sort_values('bowling_clutch_score',ascending=False)['bowler_name']]

TAB_STYLE = {'color':SUBTEXT,'background':CARD,'border':f'1px solid {BORDER}','borderBottom':'none','padding':'10px 18px','fontSize':'13px','fontWeight':'600'}
TAB_SEL   = {'color':ACCENT, 'background':BG,'borderTop':f'2px solid {ACCENT}','border':f'1px solid {BORDER}','borderBottom':'none','padding':'10px 18px','fontSize':'13px','fontWeight':'700'}

app.layout = html.Div([
    # HEADER
    html.Div([
        html.Div([
            html.H1("SupeRR Selector Season 2", style={'margin':'0','fontSize':'28px','color':GOLD,'fontWeight':'900','letterSpacing':'1px'}),
            html.P("Win Probability Added · Clutch Performance · Pressure Intelligence  |  IPL & T20I 2022–2026",
                   style={'margin':'5px 0 0','color':SUBTEXT,'fontSize':'12px'}),
        ]),
        html.Div([
            html.Span("WP MODEL", style={'background':GREEN,'color':'#000','fontSize':'9px','fontWeight':'800','padding':'3px 8px','borderRadius':'4px','marginRight':'8px'}),
            html.Span("Inn1 AUC 0.72", style={'color':SUBTEXT,'fontSize':'11px','marginRight':'12px'}),
            html.Span("Inn2 AUC 0.978", style={'color':GREEN,'fontSize':'11px','fontWeight':'700'}),
        ], style={'textAlign':'right'}),
    ], style={'background':CARD,'borderBottom':f'2px solid {BORDER}',
              'padding':'20px 32px','display':'flex','justifyContent':'space-between','alignItems':'center'}),

    dcc.Tabs(id='tabs', value='overview', style={'background':CARD},
             children=[
        dcc.Tab(label='Overview',         value='overview',   style=TAB_STYLE, selected_style=TAB_SEL),
        dcc.Tab(label='WPA Analysis',     value='wpa',        style=TAB_STYLE, selected_style=TAB_SEL),
        dcc.Tab(label='Top 10 Batters',   value='batters',    style=TAB_STYLE, selected_style=TAB_SEL),
        dcc.Tab(label='Top 10 Bowlers',   value='bowlers',    style=TAB_STYLE, selected_style=TAB_SEL),
        dcc.Tab(label='Clutch Moments',   value='clutch',     style=TAB_STYLE, selected_style=TAB_SEL),
        dcc.Tab(label='Player Drill-Down',value='drilldown',  style=TAB_STYLE, selected_style=TAB_SEL),
    ]),

    html.Div(id='tab-content',
             style={'padding':'24px 28px','background':BG,'minHeight':'80vh'}),

], style={'background':BG,'fontFamily':'"Inter","Segoe UI",sans-serif','color':TEXT,'minHeight':'100vh'})


@app.callback(Output('tab-content','children'), Input('tabs','value'))
def render_tab(tab):

    # ── OVERVIEW
    if tab == 'overview':
        return html.Div([
            html.Div([
                stat_card("Matches", f"{STATS['matches']:,}", "IPL + T20I 2022–2026", GOLD),
                stat_card("Valid Balls", f"{STATS['valid']:,}", "total deliveries", ACCENT),
                stat_card("Pressure Balls", f"{STATS['pressure']:,}", f"{STATS['pct']:.1f}% · LI-based + context", RED),
                stat_card("Eligible Batters", str(STATS['batters']), "≥100 pressure balls", GREEN),
                stat_card("Eligible Bowlers", str(STATS['bowlers']), "≥80 pressure balls", PURPLE),
            ], style={'display':'flex','gap':'12px','flexWrap':'wrap','marginBottom':'24px'}),

            html.Div([
                html.Div([dcc.Graph(figure=ranking_bar(bat_top10,'striker_name','batting_clutch_score',
                    ACCENT,'Top 10 Batters Under Pressure (WPA-based)'))],
                    style={'flex':'1','minWidth':'420px'}),
                html.Div([dcc.Graph(figure=ranking_bar(bowl_top10,'bowler_name','bowling_clutch_score',
                    RED,'Top 10 Bowlers Under Pressure (WPA-based)'))],
                    style={'flex':'1','minWidth':'420px'}),
            ], style={'display':'flex','gap':'16px','marginBottom':'20px'}),

            dcc.Graph(figure=pressure_over_heatmap()),
        ])

    # ── WPA ANALYSIS
    elif tab == 'wpa':
        return html.Div([
            html.H2("Win Probability Added Analysis", style={'color':ACCENT,'marginBottom':'6px'}),
            html.P([
                "Each delivery's WPA = WP(after ball) − WP(before ball). ",
                "Computed using a LightGBM model trained on 200k+ deliveries. ",
                html.Strong("High Pressure = Top 30% Leverage Index + at least 1 context flag.")
            ], style={'color':SUBTEXT,'lineHeight':'1.7','marginBottom':'20px'}),

            html.Div([
                html.Div([
                    html.H4("How Leverage Index Varies", style={'color':GOLD,'margin':'0 0 8px'}),
                    html.P("Leverage Index (LI) = |WP if boundary − WP if wicket|. "
                           "High LI means the outcome of THIS ball could massively swing the result.",
                           style={'color':SUBTEXT,'fontSize':'12px'}),
                ], style={'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px',
                          'padding':'16px','marginBottom':'20px'}),
            ]),

            dcc.Graph(figure=pressure_over_heatmap()),

            html.Div([
                html.Div([dcc.Graph(figure=wpa_distribution_chart(True))],  style={'flex':'1','minWidth':'400px'}),
                html.Div([dcc.Graph(figure=wpa_distribution_chart(False))], style={'flex':'1','minWidth':'400px'}),
            ], style={'display':'flex','gap':'16px','marginTop':'20px'}),

            html.Div([
                html.Div([dcc.Graph(figure=leverage_vs_wpa_scatter(True))],  style={'flex':'1','minWidth':'400px'}),
                html.Div([dcc.Graph(figure=leverage_vs_wpa_scatter(False))], style={'flex':'1','minWidth':'400px'}),
            ], style={'display':'flex','gap':'16px','marginTop':'16px'}),
        ])

    # ── BATTERS
    elif tab == 'batters':
        cols = [
            {'name':'Rank','id':'rank'},
            {'name':'Player','id':'striker_name'},
            {'name':'Balls (P)','id':'balls'},
            {'name':'Runs (P)','id':'runs'},
            {'name':'SR (P)','id':'sr'},
            {'name':'Avg (P)','id':'avg'},
            {'name':'SR Baseline','id':'sr_base'},
            {'name':'Clutch WPA','id':'clutch_wpa'},
            {'name':'WPA/Ball','id':'clutch_wpa_mean'},
            {'name':'Releases','id':'release_moments'},
            {'name':'Score','id':'batting_clutch_score'},
        ]
        td = bat_top10.copy()
        td['rank'] = [f"#{i+1}" for i in range(len(td))]
        for c in ['sr','avg','sr_base','clutch_wpa','clutch_wpa_mean','batting_clutch_score']:
            td[c] = td[c].round(3)
        td['release_moments'] = td['release_moments'].astype(int)
        td['runs'] = td['runs'].astype(int)
        td['balls'] = td['balls'].astype(int)

        return html.Div([
            html.H2("Top 10 Batters Under Pressure", style={'color':ACCENT}),
            html.P("Primary metric: Win Probability Added (WPA) in high-leverage pressure situations. "
                   "Augmented by Strike Rate, clutch ratio vs baseline, pressure release moments, and outcome weighting.",
                   style={'color':SUBTEXT,'marginBottom':'20px'}),
            dcc.Graph(figure=ranking_bar(bat_top10,'striker_name','batting_clutch_score',ACCENT,
                                         'Batting Clutch Score — WPA × Leverage × Context')),
            html.Div([
                dash_table.DataTable(
                    data=td[[c['id'] for c in cols]].to_dict('records'), columns=cols,
                    sort_action='native',
                    style_table={'overflowX':'auto'},
                    style_cell={'background':CARD,'color':TEXT,'border':f'1px solid {BORDER}',
                                'padding':'11px 14px','fontSize':'12px','textAlign':'center'},
                    style_header={'background':BORDER,'color':GOLD,'fontWeight':'700','fontSize':'12px'},
                    style_data_conditional=[
                        {'if':{'filter_query':'{rank} = "#1"'},'background':'rgba(245,197,24,0.12)','color':GOLD,'fontWeight':'800'},
                        {'if':{'filter_query':'{rank} = "#2"'},'background':'rgba(192,192,192,0.08)'},
                        {'if':{'filter_query':'{rank} = "#3"'},'background':'rgba(205,127,50,0.08)'},
                    ]
                )
            ], style={'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px',
                      'padding':'16px','marginTop':'20px','marginBottom':'28px'}),

            html.H3("Top 3 — Pressure vs Baseline Radar", style={'color':GOLD}),
            html.Div([
                html.Div([dcc.Graph(figure=radar_chart(bat_top10.iloc[i]['striker_name'], True))],
                          style={'flex':'1','minWidth':'300px'})
                for i in range(min(3, len(bat_top10)))
            ], style={'display':'flex','gap':'16px'}),

            html.H3("Pressure Release Champions", style={'color':ORANGE,'marginTop':'28px'}),
            dcc.Graph(figure=pressure_release_chart()),
        ])

    # ── BOWLERS
    elif tab == 'bowlers':
        cols = [
            {'name':'Rank','id':'rank'},
            {'name':'Player','id':'bowler_name'},
            {'name':'Balls (P)','id':'balls'},
            {'name':'Wickets (P)','id':'wkts'},
            {'name':'Eco (P)','id':'economy'},
            {'name':'Dot % (P)','id':'dot_pct'},
            {'name':'Eco Baseline','id':'eco_base'},
            {'name':'Clutch WPA','id':'clutch_wpa'},
            {'name':'WPA/Ball','id':'clutch_wpa_mean'},
            {'name':'Shutdowns','id':'shutdown_overs'},
            {'name':'Score','id':'bowling_clutch_score'},
        ]
        td = bowl_top10.copy()
        td['rank'] = [f"#{i+1}" for i in range(len(td))]
        for c in ['economy','dot_pct','eco_base','clutch_wpa','clutch_wpa_mean','bowling_clutch_score']:
            td[c] = td[c].round(3)
        td['shutdown_overs'] = td['shutdown_overs'].astype(int)
        td['wkts'] = td['wkts'].astype(int)
        td['balls'] = td['balls'].astype(int)

        return html.Div([
            html.H2("Top 10 Bowlers Under Pressure", style={'color':RED}),
            html.P("Primary metric: Win Probability Added (WPA) in high-leverage pressure situations. "
                   "Augmented by Economy, Wicket rate, Dot%, Shutdown overs, and outcome weighting.",
                   style={'color':SUBTEXT,'marginBottom':'20px'}),
            dcc.Graph(figure=ranking_bar(bowl_top10,'bowler_name','bowling_clutch_score',RED,
                                         'Bowling Clutch Score — WPA × Leverage × Context')),
            html.Div([
                dash_table.DataTable(
                    data=td[[c['id'] for c in cols]].to_dict('records'), columns=cols,
                    sort_action='native',
                    style_table={'overflowX':'auto'},
                    style_cell={'background':CARD,'color':TEXT,'border':f'1px solid {BORDER}',
                                'padding':'11px 14px','fontSize':'12px','textAlign':'center'},
                    style_header={'background':BORDER,'color':GOLD,'fontWeight':'700','fontSize':'12px'},
                    style_data_conditional=[
                        {'if':{'filter_query':'{rank} = "#1"'},'background':'rgba(245,197,24,0.12)','color':GOLD,'fontWeight':'800'},
                        {'if':{'filter_query':'{rank} = "#2"'},'background':'rgba(192,192,192,0.08)'},
                        {'if':{'filter_query':'{rank} = "#3"'},'background':'rgba(205,127,50,0.08)'},
                    ]
                )
            ], style={'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px',
                      'padding':'16px','marginTop':'20px','marginBottom':'28px'}),

            html.H3("Top 3 — Pressure vs Baseline Radar", style={'color':GOLD}),
            html.Div([
                html.Div([dcc.Graph(figure=radar_chart(bowl_top10.iloc[i]['bowler_name'], False))],
                          style={'flex':'1','minWidth':'300px'})
                for i in range(min(3, len(bowl_top10)))
            ], style={'display':'flex','gap':'16px'}),

            html.H3("Shutdown Over Leaders", style={'color':GREEN,'marginTop':'28px'}),
            dcc.Graph(figure=shutdown_chart()),
        ])

    # ── CLUTCH MOMENTS
    elif tab == 'clutch':
        return html.Div([
            html.H2("Clutch Moment Analysis", style={'color':PURPLE}),
            html.Div([
                html.Div([
                    html.H4("Pressure Release Moments", style={'color':ORANGE,'margin':'0 0 6px'}),
                    html.P("Batter hits 4+ runs when facing 3+ dots or after a wicket fell, "
                           "in a high-leverage situation.", style={'color':SUBTEXT,'fontSize':'12px'}),
                ], style={'flex':'1','background':CARD,'border':f'1px solid {BORDER}',
                          'borderRadius':'12px','padding':'16px'}),
                html.Div([
                    html.H4("Shutdown Overs", style={'color':GREEN,'margin':'0 0 6px'}),
                    html.P("Bowler concedes ≤6 runs in an over where the previous 2-over RR was ≥9 "
                           "(killing momentum).", style={'color':SUBTEXT,'fontSize':'12px'}),
                ], style={'flex':'1','background':CARD,'border':f'1px solid {BORDER}',
                          'borderRadius':'12px','padding':'16px'}),
            ], style={'display':'flex','gap':'16px','marginBottom':'20px'}),

            html.Div([
                html.Div([dcc.Graph(figure=pressure_release_chart())], style={'flex':'1','minWidth':'400px'}),
                html.Div([dcc.Graph(figure=shutdown_chart())],          style={'flex':'1','minWidth':'400px'}),
            ], style={'display':'flex','gap':'16px'}),

            html.Div([
                html.Div([dcc.Graph(figure=leverage_vs_wpa_scatter(True))],  style={'flex':'1','minWidth':'400px'}),
                html.Div([dcc.Graph(figure=leverage_vs_wpa_scatter(False))], style={'flex':'1','minWidth':'400px'}),
            ], style={'display':'flex','gap':'16px','marginTop':'16px'}),
        ])

    # ── DRILL-DOWN
    elif tab == 'drilldown':
        return html.Div([
            html.H2("Player Drill-Down", style={'color':PURPLE}),
            html.Div([
                html.Div([
                    html.Label("Select Batter", style={'color':SUBTEXT,'fontSize':'12px','marginBottom':'6px','display':'block','fontWeight':'600'}),
                    dcc.Dropdown(id='bat-sel', options=bat_opts,
                                 value=bat_top10.iloc[0]['striker_name'],
                                 style={'background':CARD2,'color':'#111','borderColor':BORDER}),
                    dcc.Graph(id='bat-radar'),
                    html.Div(id='bat-cards'),
                ], style={'flex':'1','minWidth':'380px'}),

                html.Div([
                    html.Label("Select Bowler", style={'color':SUBTEXT,'fontSize':'12px','marginBottom':'6px','display':'block','fontWeight':'600'}),
                    dcc.Dropdown(id='bowl-sel', options=bowl_opts,
                                 value=bowl_top10.iloc[0]['bowler_name'],
                                 style={'background':CARD2,'color':'#111','borderColor':BORDER}),
                    dcc.Graph(id='bowl-radar'),
                    html.Div(id='bowl-cards'),
                ], style={'flex':'1','minWidth':'380px'}),
            ], style={'display':'flex','gap':'24px','flexWrap':'wrap'}),
        ])

    return html.Div("Tab not found")


@app.callback(Output('bat-radar','figure'), Input('bat-sel','value'))
def upd_bat_radar(n): return radar_chart(n, True) if n else go.Figure()

@app.callback(Output('bowl-radar','figure'), Input('bowl-sel','value'))
def upd_bowl_radar(n): return radar_chart(n, False) if n else go.Figure()

@app.callback(Output('bat-cards','children'), Input('bat-sel','value'))
def upd_bat_cards(name):
    if not name: return []
    r = bat_rank[bat_rank['striker_name']==name].iloc[0]
    return html.Div([
        html.Div([
            stat_card("SR (Pressure)",   f"{r['sr']:.1f}",          "strike rate",    ACCENT),
            stat_card("Avg (Pressure)",  f"{r['avg']:.1f}" if pd.notna(r.get('avg')) else "N/A", "batting avg", GREEN),
            stat_card("Clutch WPA",      f"{r['clutch_wpa']:.3f}",  "total WPA",      GOLD),
            stat_card("WPA/Ball",        f"{r['clutch_wpa_mean']:.4f}", "per delivery", ORANGE),
            stat_card("Releases",        f"{int(r['release_moments'])}", "pressure release moments", RED),
        ], style={'display':'flex','gap':'8px','flexWrap':'wrap'})
    ], style={'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px','padding':'14px','marginTop':'10px'})

@app.callback(Output('bowl-cards','children'), Input('bowl-sel','value'))
def upd_bowl_cards(name):
    if not name: return []
    r = bowl_rank[bowl_rank['bowler_name']==name].iloc[0]
    return html.Div([
        html.Div([
            stat_card("Economy (P)",    f"{r['economy']:.2f}",         "runs per over",  RED),
            stat_card("Wickets (P)",    f"{int(r['wkts'])}",           "under pressure", GREEN),
            stat_card("Clutch WPA",     f"{r['clutch_wpa']:.3f}",      "total WPA",      GOLD),
            stat_card("WPA/Ball",       f"{r['clutch_wpa_mean']:.4f}", "per delivery",   ORANGE),
            stat_card("Shutdowns",      f"{int(r['shutdown_overs'])}", "shutdown overs", ACCENT),
        ], style={'display':'flex','gap':'8px','flexWrap':'wrap'})
    ], style={'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px','padding':'14px','marginTop':'10px'})


if __name__ == '__main__':
    print("\n" + "="*55)
    print("  SupeRR Selector WPA Dashboard v2")
    print("  Open: http://127.0.0.1:8050")
    print("="*55 + "\n")
    app.run(debug=False, port=8050)
