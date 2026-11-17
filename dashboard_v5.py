"""SupeRR Selector v5 Dashboard — Counter-attack + Shutdown + Min-Perf Filter"""
import pandas as pd, numpy as np, plotly.graph_objects as go, dash
from dash import dcc, html, Input, Output, dash_table
import warnings; warnings.filterwarnings('ignore')

print("Loading v5 data...")
valid    = pd.read_parquet('valid_v5.parquet')
bat_rank = pd.read_parquet('bat_rankings_v5.parquet')
bowl_rank= pd.read_parquet('bowl_rankings_v5.parquet')
bat10    = bat_rank.sort_values('batting_clutch_score',  ascending=False).head(10).reset_index(drop=True)
bowl10   = bowl_rank.sort_values('bowling_clutch_score', ascending=False).head(10).reset_index(drop=True)

BG='#0a0d1a'; CARD='#141828'; CARD2='#1c2135'; BORDER='#252d4a'
ACCENT='#00c8ff'; GOLD='#f5c518'; RED='#ff4b6e'; GREEN='#00e5a0'
PURPLE='#9b8ef5'; ORANGE='#ff9f43'; TEXT='#e8ecf8'; SUBTEXT='#6b7db3'
TEAL='#1dd1a1'; PINK='#fd79a8'; YELLOW='#ffd32a'

def sc(label, value, sub='', color=ACCENT):
    return html.Div([
        html.P(label, style={'margin':'0','fontSize':'9px','color':SUBTEXT,'letterSpacing':'1.5px','textTransform':'uppercase'}),
        html.H3(value, style={'margin':'5px 0 2px','fontSize':'22px','color':color,'fontWeight':'800'}),
        html.P(sub,   style={'margin':'0','fontSize':'10px','color':SUBTEXT}),
    ], style={'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px',
              'padding':'12px 16px','textAlign':'center','flex':'1','minWidth':'110px',
              'borderTop':f'3px solid {color}'})

def bar_chart(df10, name_col, score_col, color, title):
    medals = ['1st','2nd','3rd'] + [f'#{i+1}' for i in range(3,10)]
    colors = [GOLD,'#c0c0c0','#cd7f32'] + [color]*(len(df10)-3)
    fig = go.Figure(go.Bar(
        x=df10[score_col],
        y=[f"{medals[i]}  {df10.iloc[i][name_col]}" for i in range(len(df10))],
        orientation='h', marker=dict(color=colors),
        text=[f"  {v:.1f}" for v in df10[score_col]],
        textposition='outside', textfont=dict(color=TEXT, size=11)))
    fig.update_layout(
        title=dict(text=title, font=dict(color=TEXT, size=14)),
        paper_bgcolor=BG, plot_bgcolor=CARD, font=dict(color=TEXT),
        margin=dict(l=20,r=70,t=50,b=20),
        xaxis=dict(gridcolor=BORDER, range=[0, df10[score_col].max()*1.18], zeroline=False),
        yaxis=dict(gridcolor='rgba(0,0,0,0)', autorange='reversed'), height=430)
    return fig

def radar_bat(name):
    rd = bat_rank[bat_rank['striker_name']==name]
    if rd.empty: return go.Figure()
    r = rd.iloc[0]
    cats = ['WPA Score','HP Strike Rate','Death Alive','Counter-Attack','MWPP','Consistency']
    pv = [
        float(r.get('wpa_score', 0)),
        float(r.get('sr_score', 0)),
        float(r.get('da_score', 0)),
        float(r.get('ca_score', 0)),
        float(r.get('mwpp_score', 0)),
        float(r.get('consistency_score', 0)),
    ]
    baseline = [50]*6
    cc = cats + [cats[0]]; pvc = pv + [pv[0]]; bvc = baseline + [baseline[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=pvc, theta=cc, fill='toself',
        name='Under Pressure', line=dict(color=ACCENT, width=2.5),
        fillcolor='rgba(0,200,255,0.2)'))
    fig.add_trace(go.Scatterpolar(r=bvc, theta=cc, fill='toself',
        name='League Average', line=dict(color=PURPLE, width=1.5, dash='dot'),
        fillcolor='rgba(155,142,245,0.1)'))
    fig.update_layout(
        polar=dict(bgcolor=CARD2,
            radialaxis=dict(visible=True, range=[0,100], gridcolor=BORDER, tickfont=dict(color=SUBTEXT,size=8)),
            angularaxis=dict(gridcolor=BORDER, tickfont=dict(color=TEXT,size=10))),
        showlegend=True, legend=dict(font=dict(color=TEXT,size=10), bgcolor='rgba(0,0,0,0)'),
        paper_bgcolor=BG, font=dict(color=TEXT),
        title=dict(text=f'<b>{name}</b> — Pressure Profile', font=dict(color=TEXT,size=12)),
        margin=dict(l=50,r=50,t=60,b=50), height=400)
    return fig

def radar_bowl(name):
    rd = bowl_rank[bowl_rank['bowler_name']==name]
    if rd.empty: return go.Figure()
    r = rd.iloc[0]
    cats = ['WPA Score','Economy Control','Wicket Rate','Death Alive','Shutdown Spells','MWPP']
    pv = [
        float(r.get('wpa_score', 0)),
        float(r.get('eco_score', 0)),
        float(r.get('wkt_score', 0)),
        float(r.get('da_score', 0)),
        float(r.get('shutdown_score', 0)),
        float(r.get('mwpp_score', 0)),
    ]
    baseline = [50]*6
    cc = cats + [cats[0]]; pvc = pv + [pv[0]]; bvc = baseline + [baseline[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=pvc, theta=cc, fill='toself',
        name='Under Pressure', line=dict(color=RED, width=2.5),
        fillcolor='rgba(255,75,110,0.2)'))
    fig.add_trace(go.Scatterpolar(r=bvc, theta=cc, fill='toself',
        name='League Average', line=dict(color=PURPLE, width=1.5, dash='dot'),
        fillcolor='rgba(155,142,245,0.1)'))
    fig.update_layout(
        polar=dict(bgcolor=CARD2,
            radialaxis=dict(visible=True, range=[0,100], gridcolor=BORDER, tickfont=dict(color=SUBTEXT,size=8)),
            angularaxis=dict(gridcolor=BORDER, tickfont=dict(color=TEXT,size=10))),
        showlegend=True, legend=dict(font=dict(color=TEXT,size=10), bgcolor='rgba(0,0,0,0)'),
        paper_bgcolor=BG, font=dict(color=TEXT),
        title=dict(text=f'<b>{name}</b> — Pressure Profile', font=dict(color=TEXT,size=12)),
        margin=dict(l=50,r=50,t=60,b=50), height=400)
    return fig

def phase_pressure_chart():
    buckets = {
        'Chase Death Alive\n(Ov16-20, WP 20-80%)': 'bucket_chase_death_alive',
        'Chase Late Alive\n(Ov11-15, WP 20-80%)':  'bucket_chase_late_alive',
        'Bat-first Death\n(Ov16-20)':              'bucket_bat_death',
        'Chase PP Alive\n(Ov1-6, WP 20-80%)':     'bucket_chase_pp',
        'Bat PP End\n(Ov5-6)':                     'bucket_bat_pp_end',
    }
    rows = []
    for label, col in buckets.items():
        sub = valid[valid[col]==1]
        rows.append({
            'bucket': label.replace('\n', ' '),
            'balls': len(sub),
            'avg_wpa_bat': sub['wpa_bat_v4'].mean() * 100,
            'ca_balls': sub['is_counter_attack_ball'].sum() if 'is_counter_attack_ball' in sub.columns else 0,
            'shutdown_overs': sub['is_shutdown_over'].sum() if 'is_shutdown_over' in sub.columns else 0,
        })
    dfp = pd.DataFrame(rows)
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Deliveries', x=dfp['bucket'], y=dfp['balls'],
        marker_color=ACCENT, opacity=0.8))
    fig.add_trace(go.Bar(name='Counter-attack Balls', x=dfp['bucket'], y=dfp['ca_balls'],
        marker_color=GOLD, opacity=0.9))
    fig.add_trace(go.Bar(name='Shutdown Over Balls', x=dfp['bucket'], y=dfp['shutdown_overs']*6,
        marker_color=GREEN, opacity=0.9))
    fig.update_layout(barmode='group',
        title=dict(text='Pressure Phase Breakdown — Deliveries + Counter-attacks + Shutdowns',
                   font=dict(color=TEXT,size=13)),
        paper_bgcolor=BG, plot_bgcolor=CARD, font=dict(color=TEXT),
        legend=dict(font=dict(color=TEXT), bgcolor='rgba(0,0,0,0)'),
        xaxis=dict(gridcolor=BORDER, tickfont=dict(color=TEXT,size=10)),
        yaxis=dict(gridcolor=BORDER, title='Count'),
        margin=dict(l=20,r=20,t=50,b=20), height=380)
    return fig

def mwpp_chart():
    """Match-winning pressure performances distribution"""
    top_bat  = bat_rank.nlargest(20, 'mwpp')[['striker_name','mwpp','batting_clutch_score']].copy()
    top_bowl = bowl_rank.nlargest(20, 'mwpp')[['bowler_name','mwpp','bowling_clutch_score']].copy()
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Batters - MWPP',
        x=top_bat['striker_name'], y=top_bat['mwpp'],
        marker_color=ACCENT, opacity=0.85))
    fig.add_trace(go.Bar(name='Bowlers - MWPP',
        x=top_bowl['bowler_name'], y=top_bowl['mwpp'],
        marker_color=RED, opacity=0.85))
    fig.add_hline(y=5, line_dash='dot', line_color=GOLD, annotation_text='Min. bat (5)',
                  annotation_font_color=GOLD)
    fig.add_hline(y=4, line_dash='dot', line_color=GREEN, annotation_text='Min. bowl (4)',
                  annotation_font_color=GREEN)
    fig.update_layout(barmode='overlay',
        title=dict(text='Match-Winning Pressure Performances (MWPP) — Eligibility Filter',
                   font=dict(color=TEXT,size=13)),
        paper_bgcolor=BG, plot_bgcolor=CARD, font=dict(color=TEXT),
        legend=dict(font=dict(color=TEXT),bgcolor='rgba(0,0,0,0)'),
        xaxis=dict(gridcolor=BORDER,tickangle=45,tickfont=dict(color=TEXT,size=9)),
        yaxis=dict(gridcolor=BORDER,title='MWPP Count'),
        margin=dict(l=20,r=20,t=50,b=100), height=400)
    return fig

def ca_shutdown_scatter():
    """Counter-attack WPA vs Death-alive WPA for batters"""
    df_plot = bat_rank[bat_rank['hp_balls']>=50].copy()
    sizes = (df_plot['mwpp'].clip(1,25) / 25 * 30 + 6).tolist()
    top10ids = set(bat10['striker_id'].tolist())
    colors = [GOLD if sid in top10ids else ACCENT for sid in df_plot['striker_id']]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_plot['ca_wpa'], y=df_plot['da_wpa'],
        mode='markers+text',
        text=[n if sid in top10ids else '' for n,sid in zip(df_plot['striker_name'],df_plot['striker_id'])],
        textposition='top center', textfont=dict(color=GOLD, size=9),
        marker=dict(size=sizes, color=colors, opacity=0.75,
                    line=dict(color=BORDER, width=0.5)),
        hovertemplate='<b>%{text}</b><br>CA-WPA: %{x:.2f}<br>DA-WPA: %{y:.2f}<extra></extra>',
    ))
    fig.update_layout(
        title=dict(text='Batting: Counter-Attack WPA vs Death-Alive WPA (size = MWPP count)',
                   font=dict(color=TEXT,size=13)),
        paper_bgcolor=BG, plot_bgcolor=CARD, font=dict(color=TEXT),
        xaxis=dict(gridcolor=BORDER, title='Counter-Attack WPA', zeroline=False),
        yaxis=dict(gridcolor=BORDER, title='Death-Alive WPA', zeroline=False),
        margin=dict(l=20,r=20,t=50,b=20), height=420)
    return fig

def bowl_shutdown_scatter():
    df_plot = bowl_rank[bowl_rank['hp_balls']>=50].copy()
    sizes = (df_plot['mwpp'].clip(1,33) / 33 * 30 + 6).tolist()
    top10ids = set(bowl10['bowler_id'].tolist())
    colors = [GOLD if bid in top10ids else RED for bid in df_plot['bowler_id']]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_plot['shutdown_wpa'], y=df_plot['da_wpa'],
        mode='markers+text',
        text=[n if bid in top10ids else '' for n,bid in zip(df_plot['bowler_name'],df_plot['bowler_id'])],
        textposition='top center', textfont=dict(color=GOLD, size=9),
        marker=dict(size=sizes, color=colors, opacity=0.75,
                    line=dict(color=BORDER, width=0.5)),
        hovertemplate='<b>%{text}</b><br>Shutdown WPA: %{x:.2f}<br>DA-WPA: %{y:.2f}<extra></extra>',
    ))
    fig.update_layout(
        title=dict(text='Bowling: Shutdown WPA vs Death-Alive WPA (size = MWPP count)',
                   font=dict(color=TEXT,size=13)),
        paper_bgcolor=BG, plot_bgcolor=CARD, font=dict(color=TEXT),
        xaxis=dict(gridcolor=BORDER, title='Shutdown Spell WPA', zeroline=False),
        yaxis=dict(gridcolor=BORDER, title='Death-Alive WPA', zeroline=False),
        margin=dict(l=20,r=20,t=50,b=20), height=420)
    return fig

# ─────────────────────── LAYOUT ───────────────────────────────────
TAB_STYLE = {'color': SUBTEXT, 'background': CARD, 'border': 'none',
             'padding': '10px 20px', 'fontSize': '13px', 'fontWeight': '600'}
TAB_SEL   = {**TAB_STYLE, 'color': ACCENT, 'borderBottom': f'2px solid {ACCENT}',
             'background': CARD2}

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "SupeRR Selector v5"

# ── OVERVIEW STAT CARDS ──
n_hp    = valid['is_high_pressure'].sum()
n_elite = valid['is_elite_pressure'].sum()
n_ca    = valid['is_counter_attack_ball'].sum()
n_sd    = valid['is_shutdown_over'].sum()
n_match = valid['match_id'].nunique()

overview_cards = html.Div([
    sc("Matches Analysed",    f"{n_match:,}",             "IPL + T20I 2022–26", ACCENT),
    sc("HP Deliveries",       f"{n_hp:,}",                "High-pressure balls", PURPLE),
    sc("Elite Pressure",      f"{n_elite:,}",             "Top-tier moments", GOLD),
    sc("Counter-Attack Balls",f"{n_ca:,}",                "Dots/wkt → attack", GREEN),
    sc("Shutdown Overs",      f"{n_sd:,}",                "High-RR → clamp", TEAL),
    sc("Eligible Batters",    f"{len(bat_rank)}",         "5+ MWPP filter", ORANGE),
    sc("Eligible Bowlers",    f"{len(bowl_rank)}",        "4+ MWPP filter", RED),
], style={'display':'flex','gap':'10px','flexWrap':'wrap','marginBottom':'16px'})

# ── TOP-10 TABLE helper ──
def top10_table(df10, cols_map, style_col=None):
    rows = []
    medals = ['🥇','🥈','🥉'] + [f'#{i+1}' for i in range(3,10)]
    for i, r in df10.iterrows():
        row = {'#': medals[i]}
        for src, dst in cols_map.items():
            v = r.get(src, '')
            if isinstance(v, float): v = f"{v:.1f}"
            elif isinstance(v, (int, np.integer)): v = str(v)
            row[dst] = v
        rows.append(row)
    all_cols = ['#'] + list(cols_map.values())
    return dash_table.DataTable(
        data=rows, columns=[{'name': c, 'id': c} for c in all_cols],
        style_table={'overflowX':'auto'},
        style_header={'backgroundColor':CARD2,'color':ACCENT,'fontWeight':'700',
                      'border':f'1px solid {BORDER}','textAlign':'center'},
        style_cell={'backgroundColor':CARD,'color':TEXT,'border':f'1px solid {BORDER}',
                    'padding':'8px 12px','textAlign':'center','fontSize':'12px'},
        style_data_conditional=[
            {'if':{'row_index':0},'color':GOLD,'fontWeight':'800'},
            {'if':{'row_index':1},'color':'#c0c0c0','fontWeight':'700'},
            {'if':{'row_index':2},'color':'#cd7f32','fontWeight':'700'},
        ]
    )

bat_cols = {
    'striker_name':'Player','batting_clutch_score':'Score',
    'wpa_v5':'WPA','da_wpa':'DA-WPA','ca_wpa':'CA-WPA',
    'mwpp':'MWPP','sr':'SR','seasons':'Seas',
}
bowl_cols = {
    'bowler_name':'Player','bowling_clutch_score':'Score',
    'wpa_v5':'WPA','da_wpa':'DA-WPA','shutdown_wpa':'SD-WPA',
    'mwpp':'MWPP','economy':'Eco','seasons':'Seas',
}

bat_names  = sorted(bat_rank['striker_name'].unique())
bowl_names = sorted(bowl_rank['bowler_name'].unique())

app.layout = html.Div(style={'backgroundColor':BG,'minHeight':'100vh',
    'fontFamily':"'Inter','Segoe UI',sans-serif",'color':TEXT}, children=[

    # HEADER
    html.Div([
        html.H1("SupeRR Selector v5", style={'margin':'0','fontSize':'26px',
            'background':f'linear-gradient(90deg,{ACCENT},{PURPLE})','WebkitBackgroundClip':'text',
            'WebkitTextFillColor':'transparent','fontWeight':'900'}),
        html.P("Pressure Intelligence Dashboard — Counter-Attack + Shutdown Spells + MWPP Filter",
               style={'margin':'4px 0 0','color':SUBTEXT,'fontSize':'13px'}),
    ], style={'background':f'linear-gradient(135deg,{CARD},{CARD2})','padding':'18px 28px',
              'borderBottom':f'1px solid {BORDER}','marginBottom':'0'}),

    # TABS
    dcc.Tabs(id='tabs', value='overview', children=[
        dcc.Tab(label='Overview',         value='overview',  style=TAB_STYLE, selected_style=TAB_SEL),
        dcc.Tab(label='Top 10 Batters',   value='batters',   style=TAB_STYLE, selected_style=TAB_SEL),
        dcc.Tab(label='Top 10 Bowlers',   value='bowlers',   style=TAB_STYLE, selected_style=TAB_SEL),
        dcc.Tab(label='Phase Analysis',   value='phase',     style=TAB_STYLE, selected_style=TAB_SEL),
        dcc.Tab(label='Counter-Attack & Shutdown', value='ca_sd', style=TAB_STYLE, selected_style=TAB_SEL),
        dcc.Tab(label='MWPP Filter',      value='mwpp',      style=TAB_STYLE, selected_style=TAB_SEL),
        dcc.Tab(label='Player Drill-Down',value='drilldown', style=TAB_STYLE, selected_style=TAB_SEL),
    ], style={'background':CARD,'borderBottom':f'1px solid {BORDER}'}),

    html.Div(id='tab-content', style={'padding':'20px 24px'}),
])

@app.callback(Output('tab-content','children'), Input('tabs','value'))
def render_tab(tab):
    if tab == 'overview':
        return html.Div([
            overview_cards,
            html.Div([
                html.Div([dcc.Graph(figure=phase_pressure_chart(), config={'displayModeBar':False})],
                         style={'flex':'1','background':CARD,'borderRadius':'12px',
                                'border':f'1px solid {BORDER}','padding':'12px'}),
            ], style={'display':'flex','gap':'16px'}),
            html.Div([
                html.Div([
                    html.H3("Top 10 Batters Under Pressure", style={'color':ACCENT,'marginBottom':'12px','fontSize':'14px'}),
                    top10_table(bat10, bat_cols),
                ], style={'flex':'1','background':CARD,'borderRadius':'12px',
                          'border':f'1px solid {BORDER}','padding':'16px'}),
                html.Div([
                    html.H3("Top 10 Bowlers Under Pressure", style={'color':RED,'marginBottom':'12px','fontSize':'14px'}),
                    top10_table(bowl10, bowl_cols),
                ], style={'flex':'1','background':CARD,'borderRadius':'12px',
                          'border':f'1px solid {BORDER}','padding':'16px'}),
            ], style={'display':'flex','gap':'16px','marginTop':'16px'}),
        ])

    elif tab == 'batters':
        return html.Div([
            html.Div([
                html.Div([dcc.Graph(figure=bar_chart(bat10,'striker_name','batting_clutch_score',
                    ACCENT,'Batting Clutch Score v5 — WPA + Counter-Attack + MWPP Filter'),
                    config={'displayModeBar':False})],
                    style={'flex':'1','background':CARD,'borderRadius':'12px',
                           'border':f'1px solid {BORDER}','padding':'12px'}),
            ], style={'display':'flex','gap':'16px'}),
            html.Div([
                html.H3("Full Top 10 — Batting Under Pressure",
                        style={'color':ACCENT,'marginBottom':'12px','fontSize':'14px'}),
                top10_table(bat10, bat_cols),
                html.P("Score = 40% WPA + 18% Death-Alive WPA + 15% Counter-Attack WPA + 12% MWPP + 8% HP-SR + 7% Consistency — Choke Penalty + Season Bonus",
                       style={'color':SUBTEXT,'fontSize':'11px','marginTop':'10px'}),
            ], style={'background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}',
                      'padding':'16px','marginTop':'16px'}),
        ])

    elif tab == 'bowlers':
        return html.Div([
            html.Div([
                html.Div([dcc.Graph(figure=bar_chart(bowl10,'bowler_name','bowling_clutch_score',
                    RED,'Bowling Clutch Score v5 — WPA + Shutdown Spells + MWPP Filter'),
                    config={'displayModeBar':False})],
                    style={'flex':'1','background':CARD,'borderRadius':'12px',
                           'border':f'1px solid {BORDER}','padding':'12px'}),
            ], style={'display':'flex','gap':'16px'}),
            html.Div([
                html.H3("Full Top 10 — Bowling Under Pressure",
                        style={'color':RED,'marginBottom':'12px','fontSize':'14px'}),
                top10_table(bowl10, bowl_cols),
                html.P("Score = 35% WPA + 18% Death-Alive WPA + 15% Shutdown WPA + 12% Wkt Rate + 8% Economy + 7% MWPP + 5% Consistency — Choke Penalty + Season Bonus",
                       style={'color':SUBTEXT,'fontSize':'11px','marginTop':'10px'}),
            ], style={'background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}',
                      'padding':'16px','marginTop':'16px'}),
        ])

    elif tab == 'phase':
        return html.Div([
            html.Div([
                html.Div([dcc.Graph(figure=phase_pressure_chart(), config={'displayModeBar':False})],
                         style={'flex':'2','background':CARD,'borderRadius':'12px',
                                'border':f'1px solid {BORDER}','padding':'12px'}),
            ], style={'display':'flex','gap':'16px'}),
            # Phase weight table
            html.Div([
                html.H3("Phase Pressure Bucket Weights", style={'color':GOLD,'marginBottom':'12px','fontSize':'14px'}),
                dash_table.DataTable(
                    data=[
                        {'Phase':'Chase Death Alive (Ov16-20, WP 20-80%)','Weight':'3.0x','Rationale':'Highest pressure — match on the line in final overs'},
                        {'Phase':'Chase Late Alive (Ov11-15, WP 20-80%)',  'Weight':'2.2x','Rationale':'Mid-death, match alive'},
                        {'Phase':'Bat-first Death (Ov16-20)',              'Weight':'2.0x','Rationale':'Setting big totals under pressure'},
                        {'Phase':'Chase PP Alive (Ov1-6, WP 20-80%)',     'Weight':'1.5x','Rationale':'Early pressure sets tone'},
                        {'Phase':'Bat PP End (Ov5-6)',                     'Weight':'1.3x','Rationale':'End of batting PP, momentum shift'},
                        {'Phase':'Counter-Attack Balls (dots/wkt → runs)',  'Weight':'1.8-2.2x','Rationale':'NEW v5: responding under duress'},
                        {'Phase':'Shutdown Overs (high RR → clamp)',       'Weight':'1.6-2.4x','Rationale':'NEW v5: bowling team back into game'},
                    ],
                    columns=[{'name':c,'id':c} for c in ['Phase','Weight','Rationale']],
                    style_table={'overflowX':'auto'},
                    style_header={'backgroundColor':CARD2,'color':ACCENT,'fontWeight':'700',
                        'border':f'1px solid {BORDER}'},
                    style_cell={'backgroundColor':CARD,'color':TEXT,'border':f'1px solid {BORDER}',
                        'padding':'8px 12px','textAlign':'left','fontSize':'12px'},
                    style_data_conditional=[
                        {'if':{'row_index':5},'color':GREEN},
                        {'if':{'row_index':6},'color':TEAL},
                    ]
                ),
            ], style={'background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}',
                      'padding':'16px','marginTop':'16px'}),
        ])

    elif tab == 'ca_sd':
        return html.Div([
            html.Div([
                html.Div([dcc.Graph(figure=ca_shutdown_scatter(), config={'displayModeBar':False})],
                         style={'flex':'1','background':CARD,'borderRadius':'12px',
                                'border':f'1px solid {BORDER}','padding':'12px'}),
                html.Div([dcc.Graph(figure=bowl_shutdown_scatter(), config={'displayModeBar':False})],
                         style={'flex':'1','background':CARD,'borderRadius':'12px',
                                'border':f'1px solid {BORDER}','padding':'12px'}),
            ], style={'display':'flex','gap':'16px'}),
            # Explain CA + shutdown
            html.Div([
                html.H3("How Counter-Attack & Shutdown Detection Works",
                        style={'color':YELLOW,'marginBottom':'12px','fontSize':'14px'}),
                html.Div([
                    html.Div([
                        html.H4("Counter-Attack Trigger (Bat)", style={'color':GREEN,'margin':'0 0 8px'}),
                        html.P("Triggered when: 3+ dot balls in last 5 deliveries OR a wicket fell in last 5 balls with 2+ dots",
                               style={'color':TEXT,'fontSize':'12px','margin':'0 0 6px'}),
                        html.P("Counter-attack ball: trigger is active AND batter scores 2+ runs or hits a boundary",
                               style={'color':TEXT,'fontSize':'12px','margin':'0 0 6px'}),
                        html.P("Bonus: 1.8x WPA multiplier (2.2x for sixes)", style={'color':GOLD,'fontSize':'12px'}),
                        html.P("Sustained CA Innings: 3+ counter-attack balls in one innings", style={'color':SUBTEXT,'fontSize':'11px'}),
                    ], style={'flex':'1','background':CARD2,'borderRadius':'8px','padding':'12px'}),
                    html.Div([
                        html.H4("Shutdown Spell Trigger (Bowl)", style={'color':TEAL,'margin':'0 0 8px'}),
                        html.P("Triggered when: previous 2 overs avg RR >= 10 AND this bowler concedes <= 7 runs (or >= 9 RR and <= 6 runs)",
                               style={'color':TEXT,'fontSize':'12px','margin':'0 0 6px'}),
                        html.P("Elite shutdown: shutdown over + takes a wicket",
                               style={'color':TEXT,'fontSize':'12px','margin':'0 0 6px'}),
                        html.P("Bonus: 1.6x (normal), 2.0x (elite), 2.4x (elite + match alive)",
                               style={'color':GOLD,'fontSize':'12px'}),
                        html.P("Captures: bowling the team back after a batting onslaught", style={'color':SUBTEXT,'fontSize':'11px'}),
                    ], style={'flex':'1','background':CARD2,'borderRadius':'8px','padding':'12px'}),
                ], style={'display':'flex','gap':'12px'}),
            ], style={'background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}',
                      'padding':'16px','marginTop':'16px'}),
        ])

    elif tab == 'mwpp':
        return html.Div([
            html.Div([
                html.Div([dcc.Graph(figure=mwpp_chart(), config={'displayModeBar':False})],
                         style={'flex':'2','background':CARD,'borderRadius':'12px',
                                'border':f'1px solid {BORDER}','padding':'12px'}),
            ], style={'display':'flex','gap':'16px'}),
            html.Div([
                html.H3("MWPP Eligibility Filter — No One-Match Wonders",
                        style={'color':GOLD,'marginBottom':'12px','fontSize':'14px'}),
                html.P("A Match-Winning Pressure Performance (MWPP) is counted when:", style={'color':TEXT,'fontSize':'12px'}),
                html.Ul([
                    html.Li("Player appeared in 3+ High-Pressure balls in the match", style={'color':TEXT,'fontSize':'12px'}),
                    html.Li("Their net WPA in HP balls was positive (they helped, not hurt)", style={'color':TEXT,'fontSize':'12px'}),
                    html.Li("Their team won the match", style={'color':TEXT,'fontSize':'12px'}),
                ]),
                html.P("Minimum thresholds to qualify for Top 10:", style={'color':TEXT,'fontSize':'12px','marginTop':'8px'}),
                html.Ul([
                    html.Li(f"Batters: 5+ MWPPs  |  100+ HP balls  |  2+ seasons or 20+ matches", style={'color':GOLD,'fontSize':'12px','fontWeight':'700'}),
                    html.Li(f"Bowlers: 4+ MWPPs  |  150+ HP balls  |  2+ seasons or 15+ matches", style={'color':TEAL,'fontSize':'12px','fontWeight':'700'}),
                ]),
                html.P(f"Eligible batters after filter: {len(bat_rank)} / 756   |   Eligible bowlers: {len(bowl_rank)} / 537",
                       style={'color':SUBTEXT,'fontSize':'11px','marginTop':'8px'}),
            ], style={'background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}',
                      'padding':'16px','marginTop':'16px'}),
        ])

    elif tab == 'drilldown':
        return html.Div([
            html.Div([
                html.Div([
                    html.Label("Select Batter:", style={'color':SUBTEXT,'fontSize':'12px','marginBottom':'4px'}),
                    dcc.Dropdown(id='bat-dd',
                        options=[{'label':n,'value':n} for n in bat_names],
                        value=bat10.iloc[0]['striker_name'],
                        style={'background':CARD,'color':BG,'border':f'1px solid {BORDER}'},
                        className='dd'),
                ], style={'flex':'1'}),
                html.Div([
                    html.Label("Select Bowler:", style={'color':SUBTEXT,'fontSize':'12px','marginBottom':'4px'}),
                    dcc.Dropdown(id='bowl-dd',
                        options=[{'label':n,'value':n} for n in bowl_names],
                        value=bowl10.iloc[0]['bowler_name'],
                        style={'background':CARD,'color':BG,'border':f'1px solid {BORDER}'},
                        className='dd'),
                ], style={'flex':'1'}),
            ], style={'display':'flex','gap':'24px','marginBottom':'16px'}),
            html.Div([
                html.Div([dcc.Graph(id='bat-radar', config={'displayModeBar':False})],
                         style={'flex':'1','background':CARD,'borderRadius':'12px',
                                'border':f'1px solid {BORDER}','padding':'12px'}),
                html.Div([dcc.Graph(id='bowl-radar', config={'displayModeBar':False})],
                         style={'flex':'1','background':CARD,'borderRadius':'12px',
                                'border':f'1px solid {BORDER}','padding':'12px'}),
            ], style={'display':'flex','gap':'16px'}),
            html.Div(id='bat-stats',  style={'marginTop':'12px'}),
            html.Div(id='bowl-stats', style={'marginTop':'12px'}),
        ])

@app.callback(Output('bat-radar','figure'),  Input('bat-dd','value'))
def update_bat_radar(name): return radar_bat(name) if name else go.Figure()

@app.callback(Output('bowl-radar','figure'), Input('bowl-dd','value'))
def update_bowl_radar(name): return radar_bowl(name) if name else go.Figure()

@app.callback(Output('bat-stats','children'), Input('bat-dd','value'))
def update_bat_stats(name):
    if not name: return []
    r = bat_rank[bat_rank['striker_name']==name]
    if r.empty: return []
    r = r.iloc[0]
    return html.Div([html.Div([
        sc("Clutch Score",  f"{r['batting_clutch_score']:.1f}", "v5",         GOLD),
        sc("WPA (HP)",      f"{r['wpa_v5']:.2f}",   "enhanced",               ACCENT),
        sc("DA-WPA",        f"{r['da_wpa']:.2f}",   "death alive",            TEAL),
        sc("CA-WPA",        f"{r['ca_wpa']:.2f}",   "counter-attack",         GREEN),
        sc("MWPP",          f"{int(r['mwpp'])}",    "win perfs",              PURPLE),
        sc("SR",            f"{r['sr']:.1f}",       "overall",                ORANGE),
        sc("HP SR",         f"{r['hp_sr']:.1f}",    "HP only",                PINK),
        sc("Seasons",       f"{int(r['seasons'])}",  "active",                SUBTEXT),
    ], style={'display':'flex','gap':'8px','flexWrap':'wrap'})],
    style={'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px',
           'padding':'12px'})

@app.callback(Output('bowl-stats','children'), Input('bowl-dd','value'))
def update_bowl_stats(name):
    if not name: return []
    r = bowl_rank[bowl_rank['bowler_name']==name]
    if r.empty: return []
    r = r.iloc[0]
    return html.Div([html.Div([
        sc("Clutch Score",    f"{r['bowling_clutch_score']:.1f}", "v5",        GOLD),
        sc("WPA (HP)",        f"{r['wpa_v5']:.2f}",  "enhanced",              RED),
        sc("DA-WPA",          f"{r['da_wpa']:.2f}",  "death alive",           TEAL),
        sc("Shutdown WPA",    f"{r['shutdown_wpa']:.2f}", "spell WPA",         GREEN),
        sc("Elite Shutdowns", f"{int(r['elite_shutdown_overs'])}", "wkt+shutdown", ACCENT),
        sc("MWPP",            f"{int(r['mwpp'])}",   "win perfs",             PURPLE),
        sc("Economy",         f"{r['economy']:.2f}", "overall",               ORANGE),
        sc("Seasons",         f"{int(r['seasons'])}","active",                SUBTEXT),
    ], style={'display':'flex','gap':'8px','flexWrap':'wrap'})],
    style={'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px',
           'padding':'12px'})

if __name__ == '__main__':
    print("\n" + "="*55)
    print("  SupeRR Selector v5 Dashboard")
    print("  Open: http://127.0.0.1:8050")
    print("="*55 + "\n")
    app.run(debug=False, port=8050)
