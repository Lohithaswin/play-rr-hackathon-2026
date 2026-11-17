"""SupeRR Selector v4 Dashboard — Phase-Aware + Choke Penalty"""
import pandas as pd, numpy as np, plotly.graph_objects as go, dash
from dash import dcc, html, Input, Output, dash_table
import warnings; warnings.filterwarnings('ignore')

print("Loading v4 data...")
valid     = pd.read_parquet('valid_v4.parquet')
bat_rank  = pd.read_parquet('bat_rankings_v4.parquet')
bowl_rank = pd.read_parquet('bowl_rankings_v4.parquet')
bat10  = bat_rank.sort_values('batting_clutch_score',  ascending=False).head(10).reset_index(drop=True)
bowl10 = bowl_rank.sort_values('bowling_clutch_score', ascending=False).head(10).reset_index(drop=True)

BG='#0a0d1a'; CARD='#141828'; CARD2='#1c2135'; BORDER='#252d4a'
ACCENT='#00c8ff'; GOLD='#f5c518'; RED='#ff4b6e'; GREEN='#00e5a0'
PURPLE='#9b8ef5'; ORANGE='#ff9f43'; TEXT='#e8ecf8'; SUBTEXT='#6b7db3'
TEAL='#1dd1a1'; PINK='#fd79a8'

def sc(label,value,sub='',color=ACCENT):
    return html.Div([
        html.P(label,style={'margin':'0','fontSize':'9px','color':SUBTEXT,'letterSpacing':'1.5px','textTransform':'uppercase'}),
        html.H3(value,style={'margin':'5px 0 2px','fontSize':'22px','color':color,'fontWeight':'800'}),
        html.P(sub,style={'margin':'0','fontSize':'10px','color':SUBTEXT}),
    ],style={'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px','padding':'12px 16px',
             'textAlign':'center','flex':'1','minWidth':'110px','borderTop':f'3px solid {color}'})

def bar_chart(t10, ncol, scol, color, title):
    d = t10.reset_index(drop=True)
    medals = ['1st','2nd','3rd'] + [f'#{i+1}' for i in range(3,10)]
    colors = [GOLD,  '#c0c0c0', '#cd7f32'] + [color]*(len(d)-3)
    fig = go.Figure(go.Bar(
        x=d[scol], y=[f"{medals[i]}  {d.iloc[i][ncol]}" for i in range(len(d))],
        orientation='h', marker=dict(color=colors),
        text=[f"  {v:.1f}" for v in d[scol]],
        textposition='outside', textfont=dict(color=TEXT, size=11)))
    fig.update_layout(title=dict(text=title,font=dict(color=TEXT,size=14)),
        paper_bgcolor=BG, plot_bgcolor=CARD, font=dict(color=TEXT),
        margin=dict(l=20,r=70,t=50,b=20),
        xaxis=dict(gridcolor=BORDER,range=[0,d[scol].max()*1.18],zeroline=False),
        yaxis=dict(gridcolor='rgba(0,0,0,0)',autorange='reversed'), height=430)
    return fig

def radar(name, is_bat):
    if is_bat:
        rd = bat_rank[bat_rank['striker_name']==name]
        if rd.empty: return go.Figure()
        r = rd.iloc[0]
        cats = ['WPA Score','Strike Rate','Clutch Ratio','Pressure\nRelease','Death Alive\nWPA','Comeback']
        pv = [min(max(r.get('wpa_score',0),0),100), min(r['sr']/200*100,100),
              min(r.get('ratio_score',50),100), min(r.get('release_score',0)/30*100,100),
              min(r.get('da_score',0)/25*100,100), min(r.get('comeback_score',0)/30*100,100)]
        bv = [50, min(r.get('sr_base',130)/200*100,100), 50, 50, 50, 50]
        fill_p, lp = 'rgba(0,200,255,0.25)', dict(color=ACCENT,width=2.5)
    else:
        rd = bowl_rank[bowl_rank['bowler_name']==name]
        if rd.empty: return go.Figure()
        r = rd.iloc[0]
        cats = ['WPA Score','Economy\nControl','Wicket Rate','Shutdown\nOvers','Death Alive\nWPA','Comeback']
        pv = [min(max(r.get('wpa_score',0),0),100), min(max(0,(1-r['economy']/15)*100),100),
              min(r.get('wkt_score',0),100), min(r.get('shutdown_score',0)/30*100,100),
              min(r.get('da_score',0)/25*100,100), min(r.get('comeback_score',0)/25*100,100)]
        bv = [50, min(max(0,(1-r.get('eco_base',8)/15)*100),100), 50, 50, 50, 50]
        fill_p, lp = 'rgba(255,75,110,0.25)', dict(color=RED,width=2.5)
    cc = cats+[cats[0]]; pvc = pv+[pv[0]]; bvc = bv+[bv[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=pvc,theta=cc,fill='toself',name='Under Pressure',line=lp,fillcolor=fill_p))
    fig.add_trace(go.Scatterpolar(r=bvc,theta=cc,fill='toself',name='Baseline',line=dict(color=PURPLE,width=1.5,dash='dot'),fillcolor='rgba(155,142,245,0.1)'))
    fig.update_layout(polar=dict(bgcolor=CARD2,
        radialaxis=dict(visible=True,range=[0,100],gridcolor=BORDER,tickfont=dict(color=SUBTEXT,size=8)),
        angularaxis=dict(gridcolor=BORDER,tickfont=dict(color=TEXT,size=10))),
        showlegend=True,legend=dict(font=dict(color=TEXT,size=10),bgcolor='rgba(0,0,0,0)'),
        paper_bgcolor=BG,font=dict(color=TEXT),
        title=dict(text=f'<b>{name}</b>',font=dict(color=TEXT,size=12)),
        margin=dict(l=50,r=50,t=60,b=50),height=380)
    return fig

def phase_pressure_chart():
    buckets = {
        'Chase Death\n(Alive, Ov16-20)': 'bucket_chase_death_alive',
        'Chase Late\n(Alive, Ov11-15)':  'bucket_chase_late_alive',
        'Bat-first Death\n(Ov16-20)':    'bucket_bat_death',
        'Chase PP\n(Alive, Ov1-6)':      'bucket_chase_pp',
        'Bat PP End\n(Ov5-6)':           'bucket_bat_pp_end',
    }
    counts = {k: int(valid[v].sum()) for k,v in buckets.items()}
    weights = {'Chase Death\n(Alive, Ov16-20)':3.0,'Chase Late\n(Alive, Ov11-15)':2.2,
               'Bat-first Death\n(Ov16-20)':2.0,'Chase PP\n(Alive, Ov1-6)':1.5,'Bat PP End\n(Ov5-6)':1.3}
    colors_p = [RED, ORANGE, GOLD, ACCENT, PURPLE]
    fig = go.Figure()
    for i,(k,cnt) in enumerate(counts.items()):
        fig.add_trace(go.Bar(name=k.replace('\n',' '),x=[k.replace('\n',' ')],y=[cnt],
            marker_color=colors_p[i],
            text=[f"Ball×{weights[k]}"],textposition='outside',textfont=dict(color=TEXT,size=10)))
    fig.update_layout(title='Pressure Buckets — Phase-Aware Classification',showlegend=False,
        paper_bgcolor=BG,plot_bgcolor=CARD,font=dict(color=TEXT),
        margin=dict(l=20,r=20,t=50,b=80),
        xaxis=dict(tickangle=-15,gridcolor='rgba(0,0,0,0)'),
        yaxis=dict(title='Number of Balls',gridcolor=BORDER),height=330)
    return fig

def choke_chart():
    top_bat = bat_rank.nlargest(15,'choke_dismissals')[['striker_name','choke_dismissals','choke_innings','batting_clutch_score']]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=top_bat['striker_name'],y=top_bat['choke_dismissals'],name='Choke Dismissals',marker_color=RED))
    fig.add_trace(go.Bar(x=top_bat['striker_name'],y=top_bat['choke_innings'],name='Choke Innings',marker_color=PINK))
    fig.update_layout(barmode='group',title='Choke Events — Batters Who Fell Under Pressure',
        paper_bgcolor=BG,plot_bgcolor=CARD,font=dict(color=TEXT),
        margin=dict(l=20,r=20,t=50,b=80),xaxis=dict(tickangle=-30),
        yaxis=dict(title='Count',gridcolor=BORDER),legend=dict(font=dict(color=TEXT)),height=350)
    return fig

def da_wpa_bat_chart():
    top = bat_rank.nlargest(15,'da_wpa')[['striker_name','da_wpa','da_sr','da_balls']]
    top = top[top['da_balls'] >= 5]
    fig = go.Figure(go.Bar(x=top['striker_name'],y=top['da_wpa'],
        marker=dict(color=top['da_wpa'],colorscale=[[0,BORDER],[0.5,TEAL],[1,GOLD]]),
        text=[f"SR:{sr:.0f}" for sr in top['da_sr']],textposition='outside',textfont=dict(color=TEXT,size=10)))
    fig.update_layout(title='Death Alive Chase WPA — Best Batters in THE Most Critical Phase',
        paper_bgcolor=BG,plot_bgcolor=CARD,font=dict(color=TEXT),
        margin=dict(l=20,r=20,t=50,b=80),xaxis=dict(tickangle=-30),
        yaxis=dict(title='Enhanced WPA in Chase Death (alive)',gridcolor=BORDER),height=350)
    return fig

def da_wpa_bowl_chart():
    top = bowl_rank.nlargest(15,'da_wpa')[['bowler_name','da_wpa','da_wkts','da_balls']]
    top = top[top['da_balls'] >= 5]
    colors_b = [GREEN if v>0 else RED for v in top['da_wpa']]
    fig = go.Figure(go.Bar(x=top['bowler_name'],y=top['da_wpa'],marker_color=colors_b,
        text=[f"Wkts:{int(w)}" for w in top['da_wkts']],textposition='outside',textfont=dict(color=TEXT,size=10)))
    fig.update_layout(title='Death Alive Chase WPA — Best Bowlers When Defending in Death',
        paper_bgcolor=BG,plot_bgcolor=CARD,font=dict(color=TEXT),
        margin=dict(l=20,r=20,t=50,b=80),xaxis=dict(tickangle=-30),
        yaxis=dict(title='Enhanced WPA in Chase Death (alive)',gridcolor=BORDER),height=350)
    return fig

def li_heatmap():
    valid['phase_label'] = valid['phase'].astype(str)
    grp = valid[valid['match_alive']].groupby(['innings','phase_label'])['li_norm'].mean().reset_index()
    grp['innings'] = grp['innings'].map({1:'Inn1 (Bat First)',2:'Inn2 (Chase)'})
    piv = grp.pivot(index='innings',columns='phase_label',values='li_norm')
    fig = go.Figure(go.Heatmap(z=piv.values,x=['PP','Middle','Late','Death'],y=piv.index,
        colorscale=[[0,CARD],[0.4,ACCENT],[0.75,GOLD],[1.0,RED]],
        colorbar=dict(title='Avg LI',tickfont=dict(color=TEXT))))
    fig.update_layout(title='Leverage Index in ALIVE Matches by Phase (the real pressure zones)',
        paper_bgcolor=BG,plot_bgcolor=CARD,font=dict(color=TEXT),
        margin=dict(l=20,r=20,t=50,b=20),height=250)
    return fig

# ── APP
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "SupeRR Selector v4 — Choke-Penalised Clutch Rankings"

TS  = {'color':SUBTEXT,'background':CARD,'border':f'1px solid {BORDER}','borderBottom':'none','padding':'10px 16px','fontSize':'12px','fontWeight':'600'}
TSS = {'color':ACCENT,'background':BG,'borderTop':f'2px solid {ACCENT}','border':f'1px solid {BORDER}','borderBottom':'none','padding':'10px 16px','fontSize':'12px','fontWeight':'700'}

n_hi = int(valid['is_high_pressure'].sum())
n_el = int(valid['is_elite_pressure'].sum())

bat_opts  = [{'label':n,'value':n} for n in bat_rank.sort_values('batting_clutch_score',ascending=False)['striker_name']]
bowl_opts = [{'label':n,'value':n} for n in bowl_rank.sort_values('bowling_clutch_score',ascending=False)['bowler_name']]

app.layout = html.Div([
    html.Div([
        html.Div([
            html.H1("SupeRR Selector Season 2  |  v4",style={'margin':'0','fontSize':'24px','color':GOLD,'fontWeight':'900'}),
            html.P("Aliveness-Conditioned LI · Phase Buckets · Choke Penalty · Death Overs Focus",style={'margin':'4px 0 0','color':SUBTEXT,'fontSize':'11px'}),
        ]),
        html.Div([
            html.Span("INN1 AUC 0.775",style={'color':ACCENT,'fontSize':'11px','marginRight':'14px','fontWeight':'700'}),
            html.Span("INN2 AUC 0.996",style={'color':GREEN,'fontSize':'11px','fontWeight':'700'}),
        ]),
    ],style={'background':CARD,'borderBottom':f'2px solid {BORDER}','padding':'16px 28px','display':'flex','justifyContent':'space-between','alignItems':'center'}),
    dcc.Tabs(id='tabs',value='overview',style={'background':CARD},children=[
        dcc.Tab(label='Overview',value='overview',style=TS,selected_style=TSS),
        dcc.Tab(label='Top 10 Batters',value='batters',style=TS,selected_style=TSS),
        dcc.Tab(label='Top 10 Bowlers',value='bowlers',style=TS,selected_style=TSS),
        dcc.Tab(label='Phase Analysis',value='phase',style=TS,selected_style=TSS),
        dcc.Tab(label='Choke & Clutch',value='choke',style=TS,selected_style=TSS),
        dcc.Tab(label='Player Drill-Down',value='drill',style=TS,selected_style=TSS),
    ]),
    html.Div(id='tab-content',style={'padding':'20px 24px','background':BG,'minHeight':'80vh'}),
],style={'background':BG,'fontFamily':'"Inter","Segoe UI",sans-serif','color':TEXT,'minHeight':'100vh'})

@app.callback(Output('tab-content','children'),Input('tabs','value'))
def render(tab):
    if tab == 'overview':
        return html.Div([
            html.Div([
                sc("Matches",f"{valid['match_id'].nunique():,}","IPL + T20I",GOLD),
                sc("High-Pressure Balls",f"{n_hi:,}",f"{n_hi/len(valid)*100:.1f}%",RED),
                sc("Elite Pressure",f"{n_el:,}",f"{n_el/len(valid)*100:.1f}%",ORANGE),
                sc("Chase Death Alive",f"{int(valid['bucket_chase_death_alive'].sum()):,}","3x weight",TEAL),
                sc("Choke Dismissals",f"{int(bat_rank['choke_dismissals'].sum()):,}","penalised",PINK),
                sc("Shutdown Overs",f"{int(bowl_rank['shutdown_overs'].sum()):,}","detected",GREEN),
            ],style={'display':'flex','gap':'10px','flexWrap':'wrap','marginBottom':'20px'}),
            html.Div([
                html.Div([dcc.Graph(figure=bar_chart(bat10,'striker_name','batting_clutch_score',ACCENT,'Top 10 Batters Under Pressure — v4'))],style={'flex':'1','minWidth':'400px'}),
                html.Div([dcc.Graph(figure=bar_chart(bowl10,'bowler_name','bowling_clutch_score',RED,'Top 10 Bowlers Under Pressure — v4'))],style={'flex':'1','minWidth':'400px'}),
            ],style={'display':'flex','gap':'14px','marginBottom':'18px'}),
            dcc.Graph(figure=li_heatmap()),
        ])

    elif tab == 'batters':
        cols=[{'name':'#','id':'rank'},{'name':'Player','id':'striker_name'},
              {'name':'Balls','id':'balls'},{'name':'SR','id':'sr'},{'name':'Avg','id':'avg'},
              {'name':'WPA','id':'wpa'},{'name':'DA-WPA','id':'da_wpa'},
              {'name':'Releases','id':'release_moments'},{'name':'Comebacks','id':'comeback_inn'},
              {'name':'ChokeDis','id':'choke_dismissals'},{'name':'Score','id':'batting_clutch_score'}]
        td = bat10.copy(); td['rank']=[f"#{i+1}" for i in range(len(td))]
        for c in ['sr','avg','wpa','da_wpa','batting_clutch_score']: td[c]=td[c].round(2)
        for c in ['balls','release_moments','comeback_inn','choke_dismissals']: td[c]=td[c].astype(int)
        return html.Div([
            html.H2("Top 10 Batters Under Pressure",style={'color':ACCENT}),
            html.P("WPA × Phase Weight × Aliveness × Match Importance — penalised for choke dismissals in alive matches",style={'color':SUBTEXT}),
            dcc.Graph(figure=bar_chart(bat10,'striker_name','batting_clutch_score',ACCENT,'Batting Clutch Score v4')),
            html.Div([dash_table.DataTable(data=td[[c['id'] for c in cols]].to_dict('records'),columns=cols,sort_action='native',
                style_table={'overflowX':'auto'},style_cell={'background':CARD,'color':TEXT,'border':f'1px solid {BORDER}','padding':'9px 12px','fontSize':'12px','textAlign':'center'},
                style_header={'background':BORDER,'color':GOLD,'fontWeight':'700'},
                style_data_conditional=[{'if':{'filter_query':'{rank} = "#1"'},'background':'rgba(245,197,24,0.12)','color':GOLD,'fontWeight':'800'}])],
                style={'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px','padding':'14px','marginTop':'18px','marginBottom':'24px'}),
            html.H3("Top 3 Radar",style={'color':GOLD}),
            html.Div([html.Div([dcc.Graph(figure=radar(bat10.iloc[i]['striker_name'],True))],style={'flex':'1','minWidth':'300px'}) for i in range(min(3,len(bat10)))],style={'display':'flex','gap':'14px'}),
            dcc.Graph(figure=da_wpa_bat_chart(),style={'marginTop':'20px'}),
        ])

    elif tab == 'bowlers':
        cols=[{'name':'#','id':'rank'},{'name':'Player','id':'bowler_name'},
              {'name':'Balls','id':'balls'},{'name':'Eco','id':'economy'},{'name':'Wkts','id':'wkts'},
              {'name':'WPA','id':'wpa'},{'name':'DA-WPA','id':'da_wpa'},
              {'name':'Shutdowns','id':'shutdown_overs'},{'name':'Comebacks','id':'comeback_spells'},
              {'name':'ChokeBdry','id':'choke_boundaries'},{'name':'Score','id':'bowling_clutch_score'}]
        td = bowl10.copy(); td['rank']=[f"#{i+1}" for i in range(len(td))]
        for c in ['economy','wpa','da_wpa','bowling_clutch_score']: td[c]=td[c].round(2)
        for c in ['balls','wkts','shutdown_overs','comeback_spells','choke_boundaries']: td[c]=td[c].astype(int)
        return html.Div([
            html.H2("Top 10 Bowlers Under Pressure",style={'color':RED}),
            html.P("WPA × Phase Weight × Aliveness × Match Importance — penalised for boundaries conceded in alive high-leverage moments",style={'color':SUBTEXT}),
            dcc.Graph(figure=bar_chart(bowl10,'bowler_name','bowling_clutch_score',RED,'Bowling Clutch Score v4')),
            html.Div([dash_table.DataTable(data=td[[c['id'] for c in cols]].to_dict('records'),columns=cols,sort_action='native',
                style_table={'overflowX':'auto'},style_cell={'background':CARD,'color':TEXT,'border':f'1px solid {BORDER}','padding':'9px 12px','fontSize':'12px','textAlign':'center'},
                style_header={'background':BORDER,'color':GOLD,'fontWeight':'700'},
                style_data_conditional=[{'if':{'filter_query':'{rank} = "#1"'},'background':'rgba(245,197,24,0.12)','color':GOLD,'fontWeight':'800'}])],
                style={'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px','padding':'14px','marginTop':'18px','marginBottom':'24px'}),
            html.H3("Top 3 Radar",style={'color':GOLD}),
            html.Div([html.Div([dcc.Graph(figure=radar(bowl10.iloc[i]['bowler_name'],False))],style={'flex':'1','minWidth':'300px'}) for i in range(min(3,len(bowl10)))],style={'display':'flex','gap':'14px'}),
            dcc.Graph(figure=da_wpa_bowl_chart(),style={'marginTop':'20px'}),
        ])

    elif tab == 'phase':
        return html.Div([
            html.H2("Phase-Aware Pressure Architecture",style={'color':PURPLE}),
            html.Div([
                html.Div([html.H4("Chase Death Alive",style={'color':RED,'margin':'0 0 4px'}),html.P("Overs 16-20, Innings 2, WP 20-80%",style={'color':SUBTEXT,'fontSize':'12px'}),html.P("Weight: 3.0x",style={'color':RED,'fontWeight':'700','fontSize':'14px'})],style={'flex':'1','background':CARD,'border':f'2px solid {RED}','borderRadius':'12px','padding':'14px'}),
                html.Div([html.H4("Chase Late Alive",style={'color':ORANGE,'margin':'0 0 4px'}),html.P("Overs 11-15, Innings 2, WP 20-80%",style={'color':SUBTEXT,'fontSize':'12px'}),html.P("Weight: 2.2x",style={'color':ORANGE,'fontWeight':'700','fontSize':'14px'})],style={'flex':'1','background':CARD,'border':f'2px solid {ORANGE}','borderRadius':'12px','padding':'14px'}),
                html.Div([html.H4("Bat-first Death",style={'color':GOLD,'margin':'0 0 4px'}),html.P("Overs 16-20, Innings 1 (all)",style={'color':SUBTEXT,'fontSize':'12px'}),html.P("Weight: 2.0x",style={'color':GOLD,'fontWeight':'700','fontSize':'14px'})],style={'flex':'1','background':CARD,'border':f'2px solid {GOLD}','borderRadius':'12px','padding':'14px'}),
                html.Div([html.H4("Chase PP Alive",style={'color':ACCENT,'margin':'0 0 4px'}),html.P("Overs 1-6, Innings 2, WP 20-80%",style={'color':SUBTEXT,'fontSize':'12px'}),html.P("Weight: 1.5x",style={'color':ACCENT,'fontWeight':'700','fontSize':'14px'})],style={'flex':'1','background':CARD,'border':f'2px solid {ACCENT}','borderRadius':'12px','padding':'14px'}),
                html.Div([html.H4("Bat PP End",style={'color':PURPLE,'margin':'0 0 4px'}),html.P("Overs 5-6, Innings 1",style={'color':SUBTEXT,'fontSize':'12px'}),html.P("Weight: 1.3x",style={'color':PURPLE,'fontWeight':'700','fontSize':'14px'})],style={'flex':'1','background':CARD,'border':f'2px solid {PURPLE}','borderRadius':'12px','padding':'14px'}),
            ],style={'display':'flex','gap':'12px','flexWrap':'wrap','marginBottom':'20px'}),
            dcc.Graph(figure=phase_pressure_chart()),
            dcc.Graph(figure=li_heatmap()),
        ])

    elif tab == 'choke':
        return html.Div([
            html.H2("Choke & Clutch Analysis",style={'color':PINK}),
            html.Div([
                html.Div([html.H4("Choke Events (Bat)",style={'color':PINK,'margin':'0 0 4px'}),
                    html.P("Dismissed in high-pressure alive match → −1.5x WPA penalty",style={'color':SUBTEXT,'fontSize':'12px'})],
                    style={'flex':'1','background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px','padding':'14px'}),
                html.Div([html.H4("Choke Spells (Bowl)",style={'color':RED,'margin':'0 0 4px'}),
                    html.P("Concedes 4+ in high-pressure alive ball → −1.5x WPA penalty",style={'color':SUBTEXT,'fontSize':'12px'})],
                    style={'flex':'1','background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px','padding':'14px'}),
                html.Div([html.H4("Clutch Hits (Bat)",style={'color':TEAL,'margin':'0 0 4px'}),
                    html.P("Scores 4+ in high-pressure alive ball → extra WPA credit",style={'color':SUBTEXT,'fontSize':'12px'})],
                    style={'flex':'1','background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px','padding':'14px'}),
            ],style={'display':'flex','gap':'12px','flexWrap':'wrap','marginBottom':'20px'}),
            html.Div([
                html.Div([dcc.Graph(figure=choke_chart())],style={'flex':'1'}),
                html.Div([dcc.Graph(figure=da_wpa_bat_chart())],style={'flex':'1'}),
            ],style={'display':'flex','gap':'14px'}),
            html.Div([dcc.Graph(figure=da_wpa_bowl_chart())]),
        ])

    elif tab == 'drill':
        return html.Div([
            html.H2("Player Drill-Down",style={'color':PURPLE}),
            html.Div([
                html.Div([
                    html.Label("Batter",style={'color':SUBTEXT,'fontSize':'12px','fontWeight':'600'}),
                    dcc.Dropdown(id='bs',options=bat_opts,value=bat10.iloc[0]['striker_name'],style={'background':CARD2,'color':'#111'}),
                    dcc.Graph(id='br'),html.Div(id='bc'),
                ],style={'flex':'1','minWidth':'380px'}),
                html.Div([
                    html.Label("Bowler",style={'color':SUBTEXT,'fontSize':'12px','fontWeight':'600'}),
                    dcc.Dropdown(id='bws',options=bowl_opts,value=bowl10.iloc[0]['bowler_name'],style={'background':CARD2,'color':'#111'}),
                    dcc.Graph(id='bwr'),html.Div(id='bwc'),
                ],style={'flex':'1','minWidth':'380px'}),
            ],style={'display':'flex','gap':'24px','flexWrap':'wrap'}),
        ])
    return html.Div("Tab not found")

@app.callback(Output('br','figure'),Input('bs','value'))
def u1(n): return radar(n,True) if n else go.Figure()
@app.callback(Output('bwr','figure'),Input('bws','value'))
def u2(n): return radar(n,False) if n else go.Figure()

@app.callback(Output('bc','children'),Input('bs','value'))
def u3(name):
    if not name: return []
    r = bat_rank[bat_rank['striker_name']==name].iloc[0]
    return html.Div([html.Div([
        sc("SR(P)",f"{r['sr']:.1f}","",ACCENT), sc("Avg(P)",f"{r['avg']:.1f}" if pd.notna(r.get('avg')) else "N/A","",GREEN),
        sc("WPA",f"{r['wpa']:.2f}","enhanced",GOLD), sc("DA-WPA",f"{r['da_wpa']:.2f}","death alive",RED),
        sc("Releases",f"{int(r['release_moments'])}","clutch hits",ORANGE),
        sc("Choke Dis",f"{int(r['choke_dismissals'])}","penalised",PINK),
    ],style={'display':'flex','gap':'8px','flexWrap':'wrap'})],
    style={'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px','padding':'12px','marginTop':'10px'})

@app.callback(Output('bwc','children'),Input('bws','value'))
def u4(name):
    if not name: return []
    r = bowl_rank[bowl_rank['bowler_name']==name].iloc[0]
    return html.Div([html.Div([
        sc("Eco(P)",f"{r['economy']:.2f}","",RED), sc("Wkts(P)",f"{int(r['wkts'])}","",GREEN),
        sc("WPA",f"{r['wpa']:.2f}","enhanced",GOLD), sc("DA-WPA",f"{r['da_wpa']:.2f}","death alive",TEAL),
        sc("Shutdowns",f"{int(r['shutdown_overs'])}","overs",ACCENT),
        sc("Choke Bdry",f"{int(r['choke_boundaries'])}","penalised",PINK),
    ],style={'display':'flex','gap':'8px','flexWrap':'wrap'})],
    style={'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px','padding':'12px','marginTop':'10px'})

if __name__=='__main__':
    print("\n" + "="*55)
    print("  SupeRR Selector v4 Dashboard")
    print("  Open: http://127.0.0.1:8050")
    print("="*55 + "\n")
    app.run(debug=False, port=8050)
