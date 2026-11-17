"""SupeRR Selector v6 Dashboard — Full Transparent Metrics"""
import pandas as pd, numpy as np, plotly.graph_objects as go, dash
from dash import dcc, html, Input, Output, dash_table
import warnings; warnings.filterwarnings('ignore')

print("Loading v6 data...")
bat_rank  = pd.read_parquet('bat_rankings_v6.parquet')
bowl_rank = pd.read_parquet('bowl_rankings_v6.parquet')
bat10     = bat_rank.sort_values('batting_clutch_score', ascending=False).head(10).reset_index(drop=True)
bowl10    = bowl_rank.sort_values('bowling_clutch_score', ascending=False).head(10).reset_index(drop=True)

BG='#0a0d1a'; CARD='#141828'; CARD2='#1c2135'; BORDER='#252d4a'
ACCENT='#00c8ff'; GOLD='#f5c518'; RED='#ff4b6e'; GREEN='#00e5a0'
PURPLE='#9b8ef5'; ORANGE='#ff9f43'; TEXT='#e8ecf8'; SUBTEXT='#6b7db3'
TEAL='#1dd1a1'; PINK='#fd79a8'; YELLOW='#ffd32a'

def sc(label, value, sub='', color=ACCENT):
    return html.Div([
        html.P(label, style={'margin':'0','fontSize':'9px','color':SUBTEXT,'letterSpacing':'1.5px','textTransform':'uppercase'}),
        html.H3(str(value), style={'margin':'5px 0 2px','fontSize':'20px','color':color,'fontWeight':'800'}),
        html.P(sub, style={'margin':'0','fontSize':'10px','color':SUBTEXT}),
    ], style={'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px',
              'padding':'12px 16px','textAlign':'center','flex':'1','minWidth':'100px',
              'borderTop':f'3px solid {color}'})

def bar_chart(df10, name_col, score_col, color, title):
    medals = ['1st','2nd','3rd'] + [f'#{i+1}' for i in range(3,10)]
    colors = [GOLD,'#c0c0c0','#cd7f32'] + [color]*(len(df10)-3)
    fig = go.Figure(go.Bar(
        x=df10[score_col],
        y=[f"{medals[i]}  {df10.iloc[i][name_col]}" for i in range(len(df10))],
        orientation='h', marker=dict(color=colors),
        text=[f"  {v:.1f}" for v in df10[score_col]],
        textposition='outside', textfont=dict(color=TEXT,size=11)))
    fig.update_layout(
        title=dict(text=title,font=dict(color=TEXT,size=14)),
        paper_bgcolor=BG, plot_bgcolor=CARD, font=dict(color=TEXT),
        margin=dict(l=20,r=70,t=50,b=20),
        xaxis=dict(gridcolor=BORDER,range=[0,df10[score_col].max()*1.18],zeroline=False),
        yaxis=dict(gridcolor='rgba(0,0,0,0)',autorange='reversed'),height=430)
    return fig

def component_waterfall(name, is_bat):
    if is_bat:
        rd = bat_rank[bat_rank['striker_name']==name]
        if rd.empty: return go.Figure()
        r = rd.iloc[0]
        components = {
            'HP WPA (30%)':      r.get('S_wpa',0)*0.30,
            'Death Alive (15%)': r.get('S_da',0)*0.15,
            'Counter-Attack (12%)': r.get('S_ca',0)*0.12,
            'Rescue (10%)':      r.get('S_rescue',0)*0.10,
            'Close Death (8%)':  r.get('S_cd',0)*0.08,
            'Knockout (8%)':     r.get('S_ko',0)*0.08,
            'MWPP (7%)':         r.get('S_mwpp',0)*0.07,
            'Man of Match (5%)': r.get('S_mom',0)*0.05,
            'HP Strike Rate (3%)':r.get('S_hpsr',0)*0.03,
            'Consistency (2%)':  r.get('S_consist',0)*0.02,
            'Season Bonus':      r.get('S_season',0),
            'Choke Penalty':     -r.get('S_choke',0)*0.08,
        }
        clr = [GREEN if v>=0 else RED for v in components.values()]
        title_name = name
        bar_color = ACCENT
    else:
        rd = bowl_rank[bowl_rank['bowler_name']==name]
        if rd.empty: return go.Figure()
        r = rd.iloc[0]
        components = {
            'HP WPA (30%)':      r.get('S_wpa',0)*0.30,
            'Death Alive (15%)': r.get('S_da',0)*0.15,
            'Shutdown (12%)':    r.get('S_shutdown',0)*0.12,
            'Close Death (8%)':  r.get('S_cd',0)*0.08,
            'Knockout (7%)':     r.get('S_ko',0)*0.07,
            'Wkt Rate (7%)':     r.get('S_wkt',0)*0.07,
            'Death Yorker (6%)': r.get('S_dy',0)*0.06,
            'Economy (5%)':      r.get('S_eco',0)*0.05,
            'MWPP (4%)':         r.get('S_mwpp',0)*0.04,
            'Man of Match (3%)': r.get('S_mom',0)*0.03,
            'Wkt Variety (2%)':  r.get('S_variety',0)*0.02,
            'Season Bonus':      r.get('S_season',0),
            'Choke Penalty':     -r.get('S_choke',0)*0.08,
        }
        clr = [GREEN if v>=0 else RED for v in components.values()]
        title_name = name
        bar_color = RED

    fig = go.Figure(go.Bar(
        x=list(components.values()),
        y=list(components.keys()),
        orientation='h',
        marker_color=clr,
        text=[f"{v:+.1f}" for v in components.values()],
        textposition='outside',
        textfont=dict(color=TEXT,size=10),
    ))
    fig.update_layout(
        title=dict(text=f'<b>{title_name}</b> — Score Breakdown (how each component contributes)',
                   font=dict(color=TEXT,size=12)),
        paper_bgcolor=BG, plot_bgcolor=CARD, font=dict(color=TEXT),
        margin=dict(l=20,r=60,t=50,b=20),
        xaxis=dict(gridcolor=BORDER,zeroline=True,zerolinecolor=BORDER,title='Points Contributed'),
        yaxis=dict(gridcolor='rgba(0,0,0,0)',autorange='reversed'),
        height=450)
    return fig

def radar_bat(name):
    rd = bat_rank[bat_rank['striker_name']==name]
    if rd.empty: return go.Figure()
    r = rd.iloc[0]
    cats = ['HP WPA','Death Alive','Counter-Attack','Rescue','Close-Death','Knockout','MWPP','MoM']
    pv   = [r.get(f'S_{k}',0) for k in ['wpa','da','ca','rescue','cd','ko','mwpp','mom']]
    baseline = [50]*len(cats)
    cc = cats+[cats[0]]; pvc = pv+[pv[0]]; bvc = baseline+[baseline[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=pvc,theta=cc,fill='toself',name='Player',
        line=dict(color=ACCENT,width=2.5),fillcolor='rgba(0,200,255,0.2)'))
    fig.add_trace(go.Scatterpolar(r=bvc,theta=cc,fill='toself',name='Avg (50)',
        line=dict(color=PURPLE,width=1.5,dash='dot'),fillcolor='rgba(155,142,245,0.1)'))
    fig.update_layout(
        polar=dict(bgcolor=CARD2,
            radialaxis=dict(visible=True,range=[0,100],gridcolor=BORDER,tickfont=dict(color=SUBTEXT,size=8)),
            angularaxis=dict(gridcolor=BORDER,tickfont=dict(color=TEXT,size=10))),
        showlegend=True,legend=dict(font=dict(color=TEXT,size=10),bgcolor='rgba(0,0,0,0)'),
        paper_bgcolor=BG,font=dict(color=TEXT),
        title=dict(text=f'<b>{name}</b>',font=dict(color=TEXT,size=12)),
        margin=dict(l=50,r=50,t=60,b=50),height=400)
    return fig

def radar_bowl(name):
    rd = bowl_rank[bowl_rank['bowler_name']==name]
    if rd.empty: return go.Figure()
    r = rd.iloc[0]
    cats = ['HP WPA','Death Alive','Shutdown','Close-Death','Knockout','Wkt Rate','Yorker','MWPP','MoM']
    pv   = [r.get(f'S_{k}',0) for k in ['wpa','da','shutdown','cd','ko','wkt','dy','mwpp','mom']]
    baseline = [50]*len(cats)
    cc = cats+[cats[0]]; pvc = pv+[pv[0]]; bvc = baseline+[baseline[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=pvc,theta=cc,fill='toself',name='Player',
        line=dict(color=RED,width=2.5),fillcolor='rgba(255,75,110,0.2)'))
    fig.add_trace(go.Scatterpolar(r=bvc,theta=cc,fill='toself',name='Avg (50)',
        line=dict(color=PURPLE,width=1.5,dash='dot'),fillcolor='rgba(155,142,245,0.1)'))
    fig.update_layout(
        polar=dict(bgcolor=CARD2,
            radialaxis=dict(visible=True,range=[0,100],gridcolor=BORDER,tickfont=dict(color=SUBTEXT,size=8)),
            angularaxis=dict(gridcolor=BORDER,tickfont=dict(color=TEXT,size=10))),
        showlegend=True,legend=dict(font=dict(color=TEXT,size=10),bgcolor='rgba(0,0,0,0)'),
        paper_bgcolor=BG,font=dict(color=TEXT),
        title=dict(text=f'<b>{name}</b>',font=dict(color=TEXT,size=12)),
        margin=dict(l=50,r=50,t=60,b=50),height=400)
    return fig

def scatter_bat():
    df = bat_rank.copy()
    top10ids = set(bat10['striker_id'].tolist())
    fig = go.Figure()
    for label, subset, color, size_col in [
        ('Top 10', df[df['striker_id'].isin(top10ids)], GOLD, 'mwpp_v6'),
        ('Others',  df[~df['striker_id'].isin(top10ids)], ACCENT, 'mwpp_v6'),
    ]:
        sizes = (subset[size_col].clip(1,25)/25*25+6).tolist()
        fig.add_trace(go.Scatter(
            x=subset['ca_wpa'], y=subset['da_wpa'],
            mode='markers+text' if label=='Top 10' else 'markers',
            name=label,
            text=subset['striker_name'] if label=='Top 10' else None,
            textposition='top center',
            textfont=dict(color=GOLD,size=9),
            marker=dict(size=sizes,color=color,opacity=0.75,line=dict(color=BORDER,width=0.5)),
            hovertemplate='<b>%{text}</b><br>CA-WPA: %{x:.2f}<br>DA-WPA: %{y:.2f}<extra></extra>',
        ))
    fig.update_layout(
        title=dict(text='Batting: Counter-Attack WPA vs Death-Alive WPA (bubble = MWPP count)',
                   font=dict(color=TEXT,size=13)),
        paper_bgcolor=BG,plot_bgcolor=CARD,font=dict(color=TEXT),
        xaxis=dict(gridcolor=BORDER,title='Counter-Attack WPA',zeroline=False),
        yaxis=dict(gridcolor=BORDER,title='Death-Alive WPA',zeroline=False),
        legend=dict(font=dict(color=TEXT),bgcolor='rgba(0,0,0,0)'),
        margin=dict(l=20,r=20,t=50,b=20),height=420)
    return fig

def scatter_bowl():
    df = bowl_rank.copy()
    top10ids = set(bowl10['bowler_id'].tolist())
    fig = go.Figure()
    for label, subset, color in [
        ('Top 10', df[df['bowler_id'].isin(top10ids)], GOLD),
        ('Others',  df[~df['bowler_id'].isin(top10ids)], RED),
    ]:
        sizes = (subset['mwpp_v6'].clip(1,33)/33*25+6).tolist()
        fig.add_trace(go.Scatter(
            x=subset['shutdown_wpa'], y=subset['da_wpa'],
            mode='markers+text' if label=='Top 10' else 'markers',
            name=label,
            text=subset['bowler_name'] if label=='Top 10' else None,
            textposition='top center',
            textfont=dict(color=GOLD,size=9),
            marker=dict(size=sizes,color=color,opacity=0.75,line=dict(color=BORDER,width=0.5)),
            hovertemplate='<b>%{text}</b><br>SD-WPA: %{x:.2f}<br>DA-WPA: %{y:.2f}<extra></extra>',
        ))
    fig.update_layout(
        title=dict(text='Bowling: Shutdown WPA vs Death-Alive WPA (bubble = MWPP count)',
                   font=dict(color=TEXT,size=13)),
        paper_bgcolor=BG,plot_bgcolor=CARD,font=dict(color=TEXT),
        xaxis=dict(gridcolor=BORDER,title='Shutdown WPA',zeroline=False),
        yaxis=dict(gridcolor=BORDER,title='Death-Alive WPA',zeroline=False),
        legend=dict(font=dict(color=TEXT),bgcolor='rgba(0,0,0,0)'),
        margin=dict(l=20,r=20,t=50,b=20),height=420)
    return fig

# ── TABLE BUILDERS ──
def top10_table(df10, cols_map):
    medals = ['🥇','🥈','🥉']+[f'#{i+1}' for i in range(3,10)]
    rows=[]
    for i,r in df10.iterrows():
        row={'#':medals[i]}
        for src,dst in cols_map.items():
            v = r.get(src,'')
            if isinstance(v,float): v=f"{v:.1f}"
            elif isinstance(v,(int,np.integer)): v=str(int(v))
            row[dst]=v
        rows.append(row)
    return dash_table.DataTable(
        data=rows,columns=[{'name':c,'id':c} for c in ['#']+list(cols_map.values())],
        style_table={'overflowX':'auto'},
        style_header={'backgroundColor':CARD2,'color':ACCENT,'fontWeight':'700',
                      'border':f'1px solid {BORDER}','textAlign':'center'},
        style_cell={'backgroundColor':CARD,'color':TEXT,'border':f'1px solid {BORDER}',
                    'padding':'8px 12px','textAlign':'center','fontSize':'11px'},
        style_data_conditional=[
            {'if':{'row_index':0},'color':GOLD,'fontWeight':'800'},
            {'if':{'row_index':1},'color':'#c0c0c0','fontWeight':'700'},
            {'if':{'row_index':2},'color':'#cd7f32','fontWeight':'700'},
        ])

def component_table(df10, name_col, score_cols):
    """Full transparent component scores table"""
    medals = ['🥇','🥈','🥉']+[f'#{i+1}' for i in range(3,10)]
    rows=[]
    for i,r in df10.iterrows():
        row={'#':medals[i],'Player':r[name_col],'TOTAL':f"{r[score_cols[0]]:.1f}"}
        for col,lbl in score_cols[1:]:
            v = r.get(col,0)
            row[lbl] = f"{v:.1f}" if isinstance(v,float) else str(v)
        rows.append(row)
    all_cols = ['#','Player','TOTAL'] + [lbl for _,lbl in score_cols[1:]]
    return dash_table.DataTable(
        data=rows, columns=[{'name':c,'id':c} for c in all_cols],
        style_table={'overflowX':'auto'},
        style_header={'backgroundColor':CARD2,'color':YELLOW,'fontWeight':'700',
                      'border':f'1px solid {BORDER}','textAlign':'center','fontSize':'11px'},
        style_cell={'backgroundColor':CARD,'color':TEXT,'border':f'1px solid {BORDER}',
                    'padding':'6px 10px','textAlign':'center','fontSize':'10px'},
        style_data_conditional=[
            {'if':{'row_index':0},'color':GOLD,'fontWeight':'800'},
        ])

bat_cols_main = {
    'striker_name':'Player','batting_clutch_score':'Score',
    'wpa_v5':'WPA','da_wpa':'DA-WPA','ca_wpa':'CA-WPA',
    'rescue_wpa':'Rescue','cd_wpa_agg':'CD-WPA','ko_wpa':'KO-WPA',
    'mwpp_v6':'MWPP','mom_bat':'MoM','sr':'SR','hp_sr':'HP-SR','seasons':'Seas',
}
bowl_cols_main = {
    'bowler_name':'Player','bowling_clutch_score':'Score',
    'wpa_v5':'WPA','da_wpa':'DA-WPA','shutdown_wpa':'SD-WPA',
    'cd_wpa':'CD-WPA','ko_wpa_bowl':'KO-WPA','dy_wpa':'Yorker-WPA',
    'mwpp_v6':'MWPP','mom_bowl':'MoM','economy':'Eco','hp_economy':'HP-Eco','seasons':'Seas',
}

bat_names  = sorted(bat_rank['striker_name'].unique())
bowl_names = sorted(bowl_rank['bowler_name'].unique())

# ─────────── LAYOUT ───────────────────────────────────────────────
TAB_STYLE={'color':SUBTEXT,'background':CARD,'border':'none',
           'padding':'10px 20px','fontSize':'13px','fontWeight':'600'}
TAB_SEL={**TAB_STYLE,'color':ACCENT,'borderBottom':f'2px solid {ACCENT}','background':CARD2}

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "SupeRR Selector v6"

app.layout = html.Div(style={'backgroundColor':BG,'minHeight':'100vh',
    'fontFamily':"'Inter','Segoe UI',sans-serif",'color':TEXT}, children=[

    html.Div([
        html.H1("SupeRR Selector v6",style={'margin':'0','fontSize':'26px',
            'background':f'linear-gradient(90deg,{ACCENT},{GOLD})','WebkitBackgroundClip':'text',
            'WebkitTextFillColor':'transparent','fontWeight':'900'}),
        html.P("Pressure Intelligence — Transparent Full Metrics | WPA + Rescue + Close-Death + Yorker + MoM + MWPP",
               style={'margin':'4px 0 0','color':SUBTEXT,'fontSize':'12px'}),
    ],style={'background':f'linear-gradient(135deg,{CARD},{CARD2})','padding':'18px 28px',
             'borderBottom':f'1px solid {BORDER}'}),

    dcc.Tabs(id='tabs',value='overview',children=[
        dcc.Tab(label='Overview',         value='overview',  style=TAB_STYLE,selected_style=TAB_SEL),
        dcc.Tab(label='Top 10 Batters',   value='batters',   style=TAB_STYLE,selected_style=TAB_SEL),
        dcc.Tab(label='Top 10 Bowlers',   value='bowlers',   style=TAB_STYLE,selected_style=TAB_SEL),
        dcc.Tab(label='Methodology',      value='method',    style=TAB_STYLE,selected_style=TAB_SEL),
        dcc.Tab(label='Player Drill-Down',value='drilldown', style=TAB_STYLE,selected_style=TAB_SEL),
    ],style={'background':CARD,'borderBottom':f'1px solid {BORDER}'}),

    html.Div(id='tab-content',style={'padding':'20px 24px'}),
])

@app.callback(Output('tab-content','children'), Input('tabs','value'))
def render(tab):
    if tab=='overview':
        return html.Div([
            # Summary cards
            html.Div([
                sc("Matches", f"{bat_rank['matches'].max():.0f}", "max per player", ACCENT),
                sc("Eligible Batters", str(len(bat_rank)), "5+ MWPP filter", PURPLE),
                sc("Eligible Bowlers", str(len(bowl_rank)), "4+ MWPP filter", RED),
                sc("Rescue Innings", "124", "4+ rescue balls", GREEN),
                sc("Close-Death Balls", "4,449", "WP35-65%, ov18+", GOLD),
                sc("Death Yorker Balls", "3,026", "ov16+", TEAL),
            ],style={'display':'flex','gap':'10px','flexWrap':'wrap','marginBottom':'16px'}),
            html.Div([
                html.Div([
                    html.H3("Top 10 Batters Under Pressure — v6",style={'color':ACCENT,'marginBottom':'12px','fontSize':'14px'}),
                    top10_table(bat10, bat_cols_main),
                ],style={'flex':'1','background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}','padding':'16px'}),
                html.Div([
                    html.H3("Top 10 Bowlers Under Pressure — v6",style={'color':RED,'marginBottom':'12px','fontSize':'14px'}),
                    top10_table(bowl10, bowl_cols_main),
                ],style={'flex':'1','background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}','padding':'16px'}),
            ],style={'display':'flex','gap':'16px'}),
            html.Div([
                html.Div([dcc.Graph(figure=scatter_bat(),config={'displayModeBar':False})],
                         style={'flex':'1','background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}','padding':'12px'}),
                html.Div([dcc.Graph(figure=scatter_bowl(),config={'displayModeBar':False})],
                         style={'flex':'1','background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}','padding':'12px'}),
            ],style={'display':'flex','gap':'16px','marginTop':'16px'}),
        ])

    elif tab=='batters':
        return html.Div([
            html.Div([dcc.Graph(figure=bar_chart(bat10,'striker_name','batting_clutch_score',
                ACCENT,'Batting Clutch Score v6'),config={'displayModeBar':False})],
                style={'background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}','padding':'12px','marginBottom':'16px'}),
            html.Div([
                html.H3("Full Metric Breakdown — All 10 Components Visible",
                        style={'color':YELLOW,'marginBottom':'12px','fontSize':'14px'}),
                top10_table(bat10, bat_cols_main),
                html.Hr(style={'borderColor':BORDER,'margin':'12px 0'}),
                html.P("SCORE = 30%×WPA + 15%×DA + 12%×CA + 10%×Rescue + 8%×CD + 8%×KO + 7%×MWPP + 5%×MoM + 3%×HP-SR + 2%×Consistency + Season Bonus − 8%×Choke",
                       style={'color':SUBTEXT,'fontSize':'11px','fontFamily':'monospace'}),
                html.Hr(style={'borderColor':BORDER,'margin':'12px 0'}),
                # Component score table
                html.H4("Raw Component Scores (0-100 each)",style={'color':ACCENT,'fontSize':'13px','marginBottom':'8px'}),
                dash_table.DataTable(
                    data=[{
                        'Player': r['striker_name'],
                        'S_WPA': f"{r.get('S_wpa',0):.0f}",
                        'S_DA':  f"{r.get('S_da',0):.0f}",
                        'S_CA':  f"{r.get('S_ca',0):.0f}",
                        'S_Rescue':f"{r.get('S_rescue',0):.0f}",
                        'S_CD':  f"{r.get('S_cd',0):.0f}",
                        'S_KO':  f"{r.get('S_ko',0):.0f}",
                        'S_MWPP':f"{r.get('S_mwpp',0):.0f}",
                        'S_MoM': f"{r.get('S_mom',0):.0f}",
                        'S_Choke':f"{r.get('S_choke',0):.0f}",
                        'S_Season':f"{r.get('S_season',0):.1f}",
                        'TOTAL': f"{r['batting_clutch_score']:.1f}",
                    } for _,r in bat10.iterrows()],
                    columns=[{'name':c,'id':c} for c in [
                        'Player','S_WPA','S_DA','S_CA','S_Rescue','S_CD',
                        'S_KO','S_MWPP','S_MoM','S_Choke','S_Season','TOTAL']],
                    style_table={'overflowX':'auto'},
                    style_header={'backgroundColor':CARD2,'color':YELLOW,'fontWeight':'700',
                        'border':f'1px solid {BORDER}','textAlign':'center','fontSize':'11px'},
                    style_cell={'backgroundColor':CARD,'color':TEXT,'border':f'1px solid {BORDER}',
                        'padding':'6px 10px','textAlign':'center','fontSize':'11px'},
                    style_data_conditional=[
                        {'if':{'column_id':'TOTAL'},'color':GOLD,'fontWeight':'800'},
                    ]),
            ],style={'background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}','padding':'16px'}),
        ])

    elif tab=='bowlers':
        return html.Div([
            html.Div([dcc.Graph(figure=bar_chart(bowl10,'bowler_name','bowling_clutch_score',
                RED,'Bowling Clutch Score v6'),config={'displayModeBar':False})],
                style={'background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}','padding':'12px','marginBottom':'16px'}),
            html.Div([
                html.H3("Full Metric Breakdown — All 12 Components Visible",
                        style={'color':YELLOW,'marginBottom':'12px','fontSize':'14px'}),
                top10_table(bowl10, bowl_cols_main),
                html.Hr(style={'borderColor':BORDER,'margin':'12px 0'}),
                html.P("SCORE = 30%×WPA + 15%×DA + 12%×Shutdown + 8%×CD + 7%×KO + 7%×WktRate + 6%×Yorker + 5%×Eco + 4%×MWPP + 3%×MoM + 2%×Variety + 1%×Consist + Season − 8%×Choke",
                       style={'color':SUBTEXT,'fontSize':'11px','fontFamily':'monospace'}),
                html.Hr(style={'borderColor':BORDER,'margin':'12px 0'}),
                html.H4("Raw Component Scores (0-100 each)",style={'color':RED,'fontSize':'13px','marginBottom':'8px'}),
                dash_table.DataTable(
                    data=[{
                        'Player': r['bowler_name'],
                        'S_WPA':  f"{r.get('S_wpa',0):.0f}",
                        'S_DA':   f"{r.get('S_da',0):.0f}",
                        'S_Shutdown':f"{r.get('S_shutdown',0):.0f}",
                        'S_CD':   f"{r.get('S_cd',0):.0f}",
                        'S_KO':   f"{r.get('S_ko',0):.0f}",
                        'S_Wkt':  f"{r.get('S_wkt',0):.0f}",
                        'S_Yorker':f"{r.get('S_dy',0):.0f}",
                        'S_Eco':  f"{r.get('S_eco',0):.0f}",
                        'S_MWPP': f"{r.get('S_mwpp',0):.0f}",
                        'S_MoM':  f"{r.get('S_mom',0):.0f}",
                        'S_Choke':f"{r.get('S_choke',0):.0f}",
                        'S_Season':f"{r.get('S_season',0):.1f}",
                        'TOTAL':  f"{r['bowling_clutch_score']:.1f}",
                    } for _,r in bowl10.iterrows()],
                    columns=[{'name':c,'id':c} for c in [
                        'Player','S_WPA','S_DA','S_Shutdown','S_CD','S_KO',
                        'S_Wkt','S_Yorker','S_Eco','S_MWPP','S_MoM','S_Choke','S_Season','TOTAL']],
                    style_table={'overflowX':'auto'},
                    style_header={'backgroundColor':CARD2,'color':YELLOW,'fontWeight':'700',
                        'border':f'1px solid {BORDER}','textAlign':'center','fontSize':'11px'},
                    style_cell={'backgroundColor':CARD,'color':TEXT,'border':f'1px solid {BORDER}',
                        'padding':'6px 10px','textAlign':'center','fontSize':'11px'},
                    style_data_conditional=[
                        {'if':{'column_id':'TOTAL'},'color':GOLD,'fontWeight':'800'},
                    ]),
            ],style={'background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}','padding':'16px'}),
        ])

    elif tab=='method':
        def method_card(title, color, items):
            return html.Div([
                html.H4(title,style={'color':color,'margin':'0 0 8px','fontSize':'13px'}),
                html.Ul([html.Li(i,style={'color':TEXT,'fontSize':'12px','marginBottom':'4px'}) for i in items]),
            ],style={'background':CARD2,'borderRadius':'8px','padding':'12px','flex':'1'})

        return html.Div([
            html.Div([
                html.H3("How v6 Identifies Pressure & Scores Players",
                        style={'color':YELLOW,'marginBottom':'16px','fontSize':'15px'}),
                html.Div([
                    method_card("Phase Pressure Buckets",[ACCENT],[
                        "Chase Death Alive (Ov16-20, WP 20-80%) → 3.0x weight — HIGHEST pressure",
                        "Chase Late Alive (Ov11-15, WP 20-80%) → 2.2x weight",
                        "Bat-first Death (Ov16-20) → 2.0x weight",
                        "Chase PP Alive (Ov1-6, WP 20-80%) → 1.5x weight",
                        "Bat PP End (Ov5-6) → 1.3x weight",
                        "Win Probability model (LightGBM) trained on 190k+ deliveries",
                    ]),
                    method_card("New v6 Pressure Signals",[GREEN],[
                        "Post-Collapse Rescue: 2+ wickets in last 12 balls → batter scores 2+ or boundary",
                        "Close-Death Clutch: WP 35-65%, over 18+ — absolute last-ball pressure",
                        "Death Yorker Execution: Yorker/Wide Yorker in overs 16-20, economy & wickets",
                        "Knockout Match Premium: Final, SF, Qualifier, Eliminator = higher weight",
                        "Man of Match Frequency: independent match-impact validator (292 players tracked)",
                        "Shutdown Spells: prev 2-over RR ≥10 → bowler concedes ≤7 this over",
                    ]),
                ],style={'display':'flex','gap':'12px','marginBottom':'12px'}),
                html.Div([
                    method_card("Anti-One-Wonder Filter (MWPP)",[GOLD],[
                        "MWPP = Match-Winning Pressure Performance",
                        "Bat: team won + HP WPA > 0 + 3+ HP balls in that match",
                        "Bowl: team won + HP WPA > 0 + 3+ HP balls bowled in that match",
                        "Min threshold: Batters 5+ MWPPs, Bowlers 4+ MWPPs",
                        "Also requires: 2+ seasons active OR 20+ matches (bat) / 15+ matches (bowl)",
                        "Eliminates one-season wonders and low-sample flukes",
                    ]),
                    method_card("Choke Penalty (Negative Points)",[RED],[
                        "Choke event: gave up large WPA in a high-pressure alive situation",
                        "Batting choke: got out at critical moment (WP swing > threshold)",
                        "Bowling choke: conceded boundary / got hit in death alive over",
                        "Penalty applied as negative component: −8% × Choke Score",
                        "Prevents chokers from masking bad moments with one good game",
                    ]),
                ],style={'display':'flex','gap':'12px'}),
            ],style={'background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}','padding':'16px','marginBottom':'16px'}),
            # Weight tables
            html.Div([
                html.Div([
                    html.H4("Batting Formula Weights",style={'color':ACCENT,'marginBottom':'8px','fontSize':'13px'}),
                    dash_table.DataTable(
                        data=[
                            {'Component':'HP WPA','Weight':'30%','What it measures':'Win Probability Added in all HP balls'},
                            {'Component':'Death Alive WPA','Weight':'15%','What it measures':'WPA when chase is alive in death overs (highest pressure)'},
                            {'Component':'Counter-Attack WPA','Weight':'12%','What it measures':'WPA when dots/wickets piled up → batter attacked'},
                            {'Component':'Post-Collapse Rescue','Weight':'10%','What it measures':'WPA after 2+ wickets fell in 12 balls'},
                            {'Component':'Close-Death WPA','Weight':'8%','What it measures':'WPA in ov18+, WP 35-65% (most critical)'},
                            {'Component':'Knockout WPA','Weight':'8%','What it measures':'WPA in Finals/SF/Qualifiers/Eliminators'},
                            {'Component':'MWPP Count','Weight':'7%','What it measures':'Number of match-winning pressure performances'},
                            {'Component':'Man of Match','Weight':'5%','What it measures':'Independent match-impact validator'},
                            {'Component':'HP Strike Rate','Weight':'3%','What it measures':'Scoring rate specifically in HP balls'},
                            {'Component':'Consistency','Weight':'2%','What it measures':'Average WPA per match (sustained impact)'},
                            {'Component':'Season Bonus','Weight':'+15 pts','What it measures':'Reward for sustained performance across seasons'},
                            {'Component':'Choke Penalty','Weight':'−8%','What it measures':'Penalty for losing game in pressure situations'},
                        ],
                        columns=[{'name':c,'id':c} for c in ['Component','Weight','What it measures']],
                        style_table={'overflowX':'auto'},
                        style_header={'backgroundColor':CARD2,'color':ACCENT,'fontWeight':'700','border':f'1px solid {BORDER}'},
                        style_cell={'backgroundColor':CARD,'color':TEXT,'border':f'1px solid {BORDER}','padding':'7px 10px','fontSize':'11px','textAlign':'left'},
                        style_data_conditional=[{'if':{'column_id':'Weight'},'color':GOLD,'fontWeight':'700','textAlign':'center'}]),
                ],style={'flex':'1','background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}','padding':'14px'}),
                html.Div([
                    html.H4("Bowling Formula Weights",style={'color':RED,'marginBottom':'8px','fontSize':'13px'}),
                    dash_table.DataTable(
                        data=[
                            {'Component':'HP WPA','Weight':'30%','What it measures':'Win Probability Added in all HP balls'},
                            {'Component':'Death Alive WPA','Weight':'15%','What it measures':'WPA when chase is alive in death overs'},
                            {'Component':'Shutdown WPA','Weight':'12%','What it measures':'WPA when previous RR ≥10 → bowler clamps ≤7'},
                            {'Component':'Close-Death WPA','Weight':'8%','What it measures':'WPA in ov18+, WP 35-65%'},
                            {'Component':'Knockout WPA','Weight':'7%','What it measures':'WPA in Finals/SF/Qualifiers/Eliminators'},
                            {'Component':'HP Wicket Rate','Weight':'7%','What it measures':'Wickets per 6 balls in HP situations'},
                            {'Component':'Death Yorker WPA','Weight':'6%','What it measures':'WPA from Yorkers/Wide Yorkers in ov16-20'},
                            {'Component':'HP Economy','Weight':'5%','What it measures':'Runs conceded per over in HP balls'},
                            {'Component':'MWPP Count','Weight':'4%','What it measures':'Match-winning pressure performances count'},
                            {'Component':'Man of Match','Weight':'3%','What it measures':'Independent match-impact validator'},
                            {'Component':'Wkt Variety','Weight':'2%','What it measures':'No. of different delivery styles that took wickets'},
                            {'Component':'Consistency','Weight':'1%','What it measures':'Average WPA per match'},
                            {'Component':'Season Bonus','Weight':'+15 pts','What it measures':'Reward for sustained cross-season performance'},
                            {'Component':'Choke Penalty','Weight':'−8%','What it measures':'Penalty for going for runs at critical moments'},
                        ],
                        columns=[{'name':c,'id':c} for c in ['Component','Weight','What it measures']],
                        style_table={'overflowX':'auto'},
                        style_header={'backgroundColor':CARD2,'color':RED,'fontWeight':'700','border':f'1px solid {BORDER}'},
                        style_cell={'backgroundColor':CARD,'color':TEXT,'border':f'1px solid {BORDER}','padding':'7px 10px','fontSize':'11px','textAlign':'left'},
                        style_data_conditional=[{'if':{'column_id':'Weight'},'color':GOLD,'fontWeight':'700','textAlign':'center'}]),
                ],style={'flex':'1','background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}','padding':'14px'}),
            ],style={'display':'flex','gap':'16px'}),
        ])

    elif tab=='drilldown':
        return html.Div([
            html.Div([
                html.Div([
                    html.Label("Select Batter:",style={'color':SUBTEXT,'fontSize':'12px','marginBottom':'4px'}),
                    dcc.Dropdown(id='bat-dd',
                        options=[{'label':n,'value':n} for n in bat_names],
                        value=bat10.iloc[0]['striker_name'],
                        style={'background':CARD,'color':BG,'border':f'1px solid {BORDER}'}),
                ],style={'flex':'1'}),
                html.Div([
                    html.Label("Select Bowler:",style={'color':SUBTEXT,'fontSize':'12px','marginBottom':'4px'}),
                    dcc.Dropdown(id='bowl-dd',
                        options=[{'label':n,'value':n} for n in bowl_names],
                        value=bowl10.iloc[0]['bowler_name'],
                        style={'background':CARD,'color':BG,'border':f'1px solid {BORDER}'}),
                ],style={'flex':'1'}),
            ],style={'display':'flex','gap':'24px','marginBottom':'16px'}),
            html.Div([
                html.Div([dcc.Graph(id='bat-radar',config={'displayModeBar':False})],
                         style={'flex':'1','background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}','padding':'12px'}),
                html.Div([dcc.Graph(id='bowl-radar',config={'displayModeBar':False})],
                         style={'flex':'1','background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}','padding':'12px'}),
            ],style={'display':'flex','gap':'16px'}),
            html.Div([
                html.Div([dcc.Graph(id='bat-waterfall',config={'displayModeBar':False})],
                         style={'flex':'1','background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}','padding':'12px'}),
                html.Div([dcc.Graph(id='bowl-waterfall',config={'displayModeBar':False})],
                         style={'flex':'1','background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}','padding':'12px'}),
            ],style={'display':'flex','gap':'16px','marginTop':'12px'}),
            html.Div(id='bat-stats',style={'marginTop':'12px'}),
            html.Div(id='bowl-stats',style={'marginTop':'12px'}),
        ])

@app.callback(Output('bat-radar','figure'), Input('bat-dd','value'))
def ubr(n): return radar_bat(n) if n else go.Figure()
@app.callback(Output('bowl-radar','figure'), Input('bowl-dd','value'))
def ubwr(n): return radar_bowl(n) if n else go.Figure()
@app.callback(Output('bat-waterfall','figure'), Input('bat-dd','value'))
def ubwf(n): return component_waterfall(n,True) if n else go.Figure()
@app.callback(Output('bowl-waterfall','figure'), Input('bowl-dd','value'))
def obwf(n): return component_waterfall(n,False) if n else go.Figure()

@app.callback(Output('bat-stats','children'), Input('bat-dd','value'))
def ubs(name):
    if not name: return []
    r = bat_rank[bat_rank['striker_name']==name]
    if r.empty: return []
    r = r.iloc[0]
    return html.Div([html.Div([
        sc("Score",    f"{r['batting_clutch_score']:.1f}","v6 total",          GOLD),
        sc("WPA",      f"{r['wpa_v5']:.2f}","HP enhanced",                     ACCENT),
        sc("DA-WPA",   f"{r['da_wpa']:.2f}","death alive",                     TEAL),
        sc("CA-WPA",   f"{r['ca_wpa']:.2f}","counter-attack",                  GREEN),
        sc("Rescue",   f"{r['rescue_wpa']:.2f}","post-collapse",               ORANGE),
        sc("CD-WPA",   f"{r['cd_wpa_agg']:.2f}","ov18+,WP35-65%",             PURPLE),
        sc("KO-WPA",   f"{r['ko_wpa']:.2f}","finals+playoffs",                 PINK),
        sc("MWPP",     f"{int(r['mwpp_v6'])}","win perfs",                     YELLOW),
        sc("MoM",      f"{int(r['mom_bat'])}","times awarded",                 SUBTEXT),
        sc("SR",       f"{r['sr']:.1f}","overall",                             TEXT),
        sc("HP-SR",    f"{r['hp_sr']:.1f}","pressure only",                    ACCENT),
        sc("Seasons",  f"{int(r['seasons'])}","active",                        SUBTEXT),
    ],style={'display':'flex','gap':'6px','flexWrap':'wrap'})],
    style={'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px','padding':'12px'})

@app.callback(Output('bowl-stats','children'), Input('bowl-dd','value'))
def obs(name):
    if not name: return []
    r = bowl_rank[bowl_rank['bowler_name']==name]
    if r.empty: return []
    r = r.iloc[0]
    return html.Div([html.Div([
        sc("Score",       f"{r['bowling_clutch_score']:.1f}","v6 total",       GOLD),
        sc("WPA",         f"{r['wpa_v5']:.2f}","HP enhanced",                  RED),
        sc("DA-WPA",      f"{r['da_wpa']:.2f}","death alive",                  TEAL),
        sc("SD-WPA",      f"{r['shutdown_wpa']:.2f}","shutdown spells",        GREEN),
        sc("CD-WPA",      f"{r['cd_wpa']:.2f}","ov18+,WP35-65%",              PURPLE),
        sc("KO-WPA",      f"{r['ko_wpa_bowl']:.2f}","finals+playoffs",         PINK),
        sc("Yorker-WPA",  f"{r['dy_wpa']:.2f}","death yorkers",               ORANGE),
        sc("EliteSD",     f"{int(r['elite_shutdowns'])}","wkt in shutdown",    ACCENT),
        sc("Wkt Variety", f"{int(r['wkt_delivery_variety'])}","delivery types",YELLOW),
        sc("MWPP",        f"{int(r['mwpp_v6'])}","win perfs",                  SUBTEXT),
        sc("MoM",         f"{int(r['mom_bowl'])}","times awarded",             SUBTEXT),
        sc("HP-Eco",      f"{r['hp_economy']:.2f}","pressure economy",         TEXT),
    ],style={'display':'flex','gap':'6px','flexWrap':'wrap'})],
    style={'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px','padding':'12px'})

if __name__=='__main__':
    print("\n"+"="*55)
    print("  SupeRR Selector v6 — Full Transparent Dashboard")
    print("  Open: http://127.0.0.1:8050")
    print("="*55+"\n")
    app.run(debug=False, port=8050)
