"""
SupeRR Selector v3 — Enhanced Dashboard
========================================
Run: python dashboard_v3.py → http://127.0.0.1:8050
"""
import pandas as pd, numpy as np, plotly.graph_objects as go, plotly.express as px
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, dash_table
import warnings; warnings.filterwarnings('ignore')

print("Loading v3 data...")
valid     = pd.read_parquet('valid_v3.parquet')
bat_rank  = pd.read_parquet('bat_rankings_v3.parquet')
bowl_rank = pd.read_parquet('bowl_rankings_v3.parquet')
bat_top10  = bat_rank.sort_values('batting_clutch_score', ascending=False).head(10).reset_index(drop=True)
bowl_top10 = bowl_rank.sort_values('bowling_clutch_score', ascending=False).head(10).reset_index(drop=True)

BG='#0a0d1a'; CARD='#141828'; CARD2='#1c2135'; BORDER='#252d4a'
ACCENT='#00c8ff'; GOLD='#f5c518'; RED='#ff4b6e'; GREEN='#00e5a0'
PURPLE='#9b8ef5'; ORANGE='#ff9f43'; TEXT='#e8ecf8'; SUBTEXT='#6b7db3'

def stat_card(label,value,sub='',color=ACCENT):
    return html.Div([
        html.P(label,style={'margin':'0','fontSize':'10px','color':SUBTEXT,'letterSpacing':'1.5px','textTransform':'uppercase','fontWeight':'600'}),
        html.H3(value,style={'margin':'6px 0 2px','fontSize':'24px','color':color,'fontWeight':'800'}),
        html.P(sub,style={'margin':'0','fontSize':'11px','color':SUBTEXT}),
    ],style={'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'14px','padding':'14px 18px','textAlign':'center','flex':'1','minWidth':'120px','borderTop':f'3px solid {color}'})

def ranking_bar(t10,ncol,scol,color,title):
    d=t10.head(10).reset_index(drop=True)
    medals=['1st','2nd','3rd']+[f'#{i+1}' for i in range(3,10)]
    colors_bar=[GOLD if i==0 else '#c0c0c0' if i==1 else '#cd7f32' if i==2 else color for i in range(len(d))]
    fig=go.Figure(go.Bar(x=d[scol],y=[f"{medals[i]}  {d.iloc[i][ncol]}" for i in range(len(d))],
        orientation='h',marker=dict(color=colors_bar),text=[f"  {v:.1f}" for v in d[scol]],
        textposition='outside',textfont=dict(color=TEXT,size=11)))
    fig.update_layout(title=dict(text=title,font=dict(color=TEXT,size=14)),
        paper_bgcolor=BG,plot_bgcolor=CARD,font=dict(color=TEXT),
        margin=dict(l=20,r=70,t=50,b=20),xaxis=dict(gridcolor=BORDER,range=[0,d[scol].max()*1.18],zeroline=False),
        yaxis=dict(gridcolor='rgba(0,0,0,0)',autorange='reversed'),height=420)
    return fig

def radar_chart(name,is_batter=True):
    if is_batter:
        rd=bat_rank[bat_rank['striker_name']==name]
        if rd.empty: return go.Figure()
        r=rd.iloc[0]
        cats=['Strike Rate','Average','WPA Score','Comebacks','Pressure\nRelease','Match\nImportance']
        pv=[min(r['sr']/200*100,100),min(r.get('avg',0)/60*100,100) if pd.notna(r.get('avg')) else 0,
            min(max(r.get('wpa_score',0),0),100),min(r.get('comeback_score',0)/25*100,100),
            min(r.get('release_score',0)/30*100,100),min(r.get('importance_score',0)/20*100,100)]
        bv=[min(r.get('sr_base',130)/200*100,100),min(r.get('avg_base',25)/60*100,100) if pd.notna(r.get('avg_base')) else 0,50,50,50,50]
        fill_p,lp=f'rgba(0,200,255,0.25)',dict(color=ACCENT,width=2.5)
    else:
        rd=bowl_rank[bowl_rank['bowler_name']==name]
        if rd.empty: return go.Figure()
        r=rd.iloc[0]
        cats=['Economy\nControl','Wicket Rate','WPA Score','Shutdowns','Comeback\nSpells','Match\nImportance']
        pv=[max(0,(1-r['economy']/15)*100),min(r.get('wkt_pct',0)*15,100),
            min(max(r.get('wpa_score',0),0),100),min(r.get('shutdown_score',0)/30*100,100),
            min(r.get('comeback_score',0)/25*100,100),min(r.get('importance_score',0)/20*100,100)]
        bv=[max(0,(1-r.get('eco_base',8)/15)*100),50,50,50,50,50]
        fill_p,lp='rgba(255,75,110,0.25)',dict(color=RED,width=2.5)
    cc=cats+[cats[0]];pvc=pv+[pv[0]];bvc=bv+[bv[0]]
    fig=go.Figure()
    fig.add_trace(go.Scatterpolar(r=pvc,theta=cc,fill='toself',name='Under Pressure',line=lp,fillcolor=fill_p))
    fig.add_trace(go.Scatterpolar(r=bvc,theta=cc,fill='toself',name='Baseline',line=dict(color=PURPLE,width=1.5,dash='dot'),fillcolor='rgba(155,142,245,0.1)'))
    fig.update_layout(polar=dict(bgcolor=CARD2,radialaxis=dict(visible=True,range=[0,100],gridcolor=BORDER),
        angularaxis=dict(gridcolor=BORDER,tickfont=dict(color=TEXT,size=10))),
        showlegend=True,legend=dict(font=dict(color=TEXT,size=10)),paper_bgcolor=BG,font=dict(color=TEXT),
        title=dict(text=f'<b>{name}</b>',font=dict(color=TEXT,size=13)),
        margin=dict(l=50,r=50,t=60,b=50),height=380)
    return fig

def wpa_chart(is_batter=True):
    hi=valid[valid['is_high_pressure']]
    if is_batter:
        data=hi.groupby('striker_name')['wpa_bat_final'].sum().nlargest(15)
        title='Total Enhanced WPA (Batting) - Top 15'; c=ACCENT
    else:
        data=hi.groupby('bowler_name')['wpa_bowl_final'].sum().nlargest(15)
        title='Total Enhanced WPA (Bowling) - Top 15'; c=RED
    fig=go.Figure(go.Bar(x=data.values,y=data.index,orientation='h',
        marker=dict(color=data.values,colorscale=[[0,BORDER],[0.5,c],[1,GOLD]])))
    fig.update_layout(title=title,paper_bgcolor=BG,plot_bgcolor=CARD,font=dict(color=TEXT),
        margin=dict(l=20,r=20,t=50,b=20),xaxis=dict(gridcolor=BORDER,title='Enhanced WPA'),
        yaxis=dict(gridcolor='rgba(0,0,0,0)',autorange='reversed'),height=380)
    return fig

def comeback_chart():
    top=bat_rank.nlargest(15,'comeback_innings')[['striker_name','comeback_innings','rescue_innings','batting_clutch_score']]
    fig=go.Figure()
    fig.add_trace(go.Bar(x=top['striker_name'],y=top['comeback_innings'],name='Comeback Innings',marker_color=ORANGE))
    fig.add_trace(go.Bar(x=top['striker_name'],y=top['rescue_innings'],name='Rescue Innings (WP<20%)',marker_color=RED))
    fig.update_layout(barmode='stack',title='Comeback Champions - Pulling Team Back from Behind',
        paper_bgcolor=BG,plot_bgcolor=CARD,font=dict(color=TEXT),margin=dict(l=20,r=20,t=50,b=20),
        xaxis=dict(tickangle=-30),yaxis=dict(title='Innings Count',gridcolor=BORDER),
        legend=dict(font=dict(color=TEXT)),height=350)
    return fig

def shutdown_chart():
    top=bowl_rank.nlargest(15,'shutdown_overs')[['bowler_name','shutdown_overs','bowling_clutch_score']]
    fig=go.Figure(go.Bar(x=top['bowler_name'],y=top['shutdown_overs'],marker_color=GREEN))
    fig.update_layout(title='Shutdown Over Leaders - Killed High-Scoring Momentum',
        paper_bgcolor=BG,plot_bgcolor=CARD,font=dict(color=TEXT),margin=dict(l=20,r=20,t=50,b=20),
        xaxis=dict(tickangle=-30),yaxis=dict(title='Shutdown Overs',gridcolor=BORDER),height=350)
    return fig

def dependency_chart():
    top_dep=bat_rank.nlargest(15,'avg_dependency')[['striker_name','avg_dependency','batting_clutch_score']]
    fig=go.Figure(go.Bar(x=top_dep['striker_name'],y=top_dep['avg_dependency'],
        marker=dict(color=top_dep['avg_dependency'],colorscale=[[0,BORDER],[0.5,PURPLE],[1,GOLD]])))
    fig.update_layout(title='Team Dependency Index - Players Who Carried Their Teams',
        paper_bgcolor=BG,plot_bgcolor=CARD,font=dict(color=TEXT),margin=dict(l=20,r=20,t=50,b=20),
        xaxis=dict(tickangle=-30),yaxis=dict(title='Avg Dependency Index',gridcolor=BORDER),height=350)
    return fig

def importance_heatmap():
    ov=valid.groupby(['innings','overid'])['leverage_index_norm'].mean().reset_index()
    ov['inn_label']=ov['innings'].map({1:'Innings 1 (Batting First)',2:'Innings 2 (Chasing)'})
    piv=ov.pivot(index='inn_label',columns='overid',values='leverage_index_norm')
    fig=go.Figure(go.Heatmap(z=piv.values,x=piv.columns.astype(str),y=piv.index,
        colorscale=[[0,CARD],[0.4,ACCENT],[0.75,GOLD],[1.0,RED]],
        colorbar=dict(title='Avg LI',tickfont=dict(color=TEXT))))
    fig.update_layout(title='Leverage Index Heatmap by Over',paper_bgcolor=BG,plot_bgcolor=CARD,
        font=dict(color=TEXT),margin=dict(l=20,r=20,t=50,b=20),xaxis=dict(title='Over',tickmode='linear'),height=240)
    return fig

def score_breakdown_chart(top10,ncol,components,title,color):
    fig=go.Figure()
    for comp_name,comp_col,c in components:
        fig.add_trace(go.Bar(name=comp_name,x=top10[ncol],y=top10[comp_col].fillna(0),marker_color=c))
    fig.update_layout(barmode='stack',title=title,paper_bgcolor=BG,plot_bgcolor=CARD,font=dict(color=TEXT),
        margin=dict(l=20,r=20,t=50,b=20),xaxis=dict(tickangle=-30),
        yaxis=dict(title='Score Contribution',gridcolor=BORDER),legend=dict(font=dict(color=TEXT)),height=380)
    return fig

# ─────────────────────────────────────────────
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "SupeRR Selector v3 - Advanced Pressure Intelligence"

STATS={
    'matches':valid['match_id'].nunique(),'valid':len(valid),
    'pressure':int(valid['is_high_pressure'].sum()),'pct':valid['is_high_pressure'].mean()*100,
    'batters':len(bat_rank),'bowlers':len(bowl_rank),
    'comebacks':int(bat_rank['comeback_innings'].sum()),'shutdowns':int(bowl_rank['shutdown_overs'].sum()),
}

bat_opts=[{'label':n,'value':n} for n in bat_rank.sort_values('batting_clutch_score',ascending=False)['striker_name']]
bowl_opts=[{'label':n,'value':n} for n in bowl_rank.sort_values('bowling_clutch_score',ascending=False)['bowler_name']]

TS={'color':SUBTEXT,'background':CARD,'border':f'1px solid {BORDER}','borderBottom':'none','padding':'10px 16px','fontSize':'12px','fontWeight':'600'}
TSS={'color':ACCENT,'background':BG,'borderTop':f'2px solid {ACCENT}','border':f'1px solid {BORDER}','borderBottom':'none','padding':'10px 16px','fontSize':'12px','fontWeight':'700'}

app.layout = html.Div([
    html.Div([
        html.Div([html.H1("SupeRR Selector Season 2",style={'margin':'0','fontSize':'26px','color':GOLD,'fontWeight':'900'}),
            html.P("WPA + Match Importance + Team Dependency + Comeback Factor + Shutdown Analysis | v3",
                style={'margin':'4px 0 0','color':SUBTEXT,'fontSize':'11px'})]),
        html.Div([
            html.Span("WP MODEL",style={'background':GREEN,'color':'#000','fontSize':'9px','fontWeight':'800','padding':'3px 8px','borderRadius':'4px','marginRight':'8px'}),
            html.Span("Inn2 AUC 0.978",style={'color':GREEN,'fontSize':'11px','fontWeight':'700'}),
        ],style={'textAlign':'right'}),
    ],style={'background':CARD,'borderBottom':f'2px solid {BORDER}','padding':'18px 28px','display':'flex','justifyContent':'space-between','alignItems':'center'}),
    dcc.Tabs(id='tabs',value='overview',style={'background':CARD},children=[
        dcc.Tab(label='Overview',value='overview',style=TS,selected_style=TSS),
        dcc.Tab(label='Top 10 Batters',value='batters',style=TS,selected_style=TSS),
        dcc.Tab(label='Top 10 Bowlers',value='bowlers',style=TS,selected_style=TSS),
        dcc.Tab(label='Clutch Moments',value='clutch',style=TS,selected_style=TSS),
        dcc.Tab(label='Player Drill-Down',value='drilldown',style=TS,selected_style=TSS),
    ]),
    html.Div(id='tab-content',style={'padding':'22px 26px','background':BG,'minHeight':'80vh'}),
],style={'background':BG,'fontFamily':'"Inter","Segoe UI",sans-serif','color':TEXT,'minHeight':'100vh'})

@app.callback(Output('tab-content','children'),Input('tabs','value'))
def render_tab(tab):
    if tab=='overview':
        return html.Div([
            html.Div([stat_card("Matches",f"{STATS['matches']:,}","IPL + T20I",GOLD),
                stat_card("Pressure Balls",f"{STATS['pressure']:,}",f"{STATS['pct']:.1f}%",RED),
                stat_card("Batters",str(STATS['batters']),"eligible",GREEN),
                stat_card("Bowlers",str(STATS['bowlers']),"eligible",PURPLE),
                stat_card("Comebacks",str(STATS['comebacks']),"innings detected",ORANGE),
                stat_card("Shutdowns",str(STATS['shutdowns']),"overs detected",ACCENT),
            ],style={'display':'flex','gap':'10px','flexWrap':'wrap','marginBottom':'22px'}),
            html.Div([
                html.Div([dcc.Graph(figure=ranking_bar(bat_top10,'striker_name','batting_clutch_score',ACCENT,'Top 10 Batters Under Pressure'))],style={'flex':'1','minWidth':'400px'}),
                html.Div([dcc.Graph(figure=ranking_bar(bowl_top10,'bowler_name','bowling_clutch_score',RED,'Top 10 Bowlers Under Pressure'))],style={'flex':'1','minWidth':'400px'}),
            ],style={'display':'flex','gap':'14px','marginBottom':'18px'}),
            dcc.Graph(figure=importance_heatmap()),
        ])

    elif tab=='batters':
        cols=[{'name':'#','id':'rank'},{'name':'Player','id':'striker_name'},
            {'name':'Balls','id':'balls'},{'name':'Runs','id':'runs'},
            {'name':'SR(P)','id':'sr'},{'name':'Avg(P)','id':'avg'},
            {'name':'WPA','id':'clutch_wpa'},{'name':'WPA/Ball','id':'clutch_wpa_mean'},
            {'name':'Releases','id':'release_moments'},{'name':'Comebacks','id':'comeback_innings'},
            {'name':'MatchImp','id':'avg_importance'},{'name':'Score','id':'batting_clutch_score'}]
        td=bat_top10.copy(); td['rank']=[f"#{i+1}" for i in range(len(td))]
        for c in ['sr','avg','clutch_wpa','clutch_wpa_mean','avg_importance','batting_clutch_score']: td[c]=td[c].round(2)
        for c in ['balls','runs','release_moments','comeback_innings']: td[c]=td[c].astype(int)

        bat_comps=[('WPA Score','wpa_score',ACCENT),('SR Score','sr_score',GREEN),
            ('Clutch Ratio','ratio_score',PURPLE),('Release','release_score',ORANGE),
            ('Comeback','comeback_score',RED),('Importance','importance_score',GOLD)]
        n_bat_top = bat_top10.copy()
        for _,cc,_ in bat_comps:
            scale = {'wpa_score':0.30,'sr_score':0.15,'ratio_score':0.12,'release_score':0.12,'comeback_score':0.10,'importance_score':0.08}
            n_bat_top[cc] = n_bat_top[cc].fillna(0) * scale.get(cc,0.05)

        return html.Div([
            html.H2("Top 10 Batters Under Pressure",style={'color':ACCENT}),
            html.P("WPA-weighted, importance-adjusted, with comeback and pressure-release bonuses.",style={'color':SUBTEXT,'marginBottom':'18px'}),
            dcc.Graph(figure=ranking_bar(bat_top10,'striker_name','batting_clutch_score',ACCENT,'Batting Clutch Score')),
            html.Div([dash_table.DataTable(data=td[[c['id'] for c in cols]].to_dict('records'),columns=cols,sort_action='native',
                style_table={'overflowX':'auto'},style_cell={'background':CARD,'color':TEXT,'border':f'1px solid {BORDER}','padding':'10px 12px','fontSize':'12px','textAlign':'center'},
                style_header={'background':BORDER,'color':GOLD,'fontWeight':'700'},
                style_data_conditional=[{'if':{'filter_query':'{rank} = "#1"'},'background':'rgba(245,197,24,0.12)','color':GOLD,'fontWeight':'800'}])
            ],style={'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px','padding':'14px','marginTop':'18px','marginBottom':'24px'}),
            html.H3("Top 3 Radar",style={'color':GOLD}),
            html.Div([html.Div([dcc.Graph(figure=radar_chart(bat_top10.iloc[i]['striker_name'],True))],style={'flex':'1','minWidth':'300px'}) for i in range(min(3,len(bat_top10)))],style={'display':'flex','gap':'14px'}),
            html.Div([html.Div([dcc.Graph(figure=comeback_chart())],style={'flex':'1'}),
                html.Div([dcc.Graph(figure=dependency_chart())],style={'flex':'1'})],style={'display':'flex','gap':'14px','marginTop':'20px'}),
        ])

    elif tab=='bowlers':
        cols=[{'name':'#','id':'rank'},{'name':'Player','id':'bowler_name'},
            {'name':'Balls','id':'balls'},{'name':'Wkts','id':'wkts'},
            {'name':'Eco(P)','id':'economy'},{'name':'Dot%','id':'dot_pct'},
            {'name':'WPA','id':'clutch_wpa'},{'name':'WPA/Ball','id':'clutch_wpa_mean'},
            {'name':'Shutdowns','id':'shutdown_overs'},{'name':'Comebacks','id':'comeback_spells'},
            {'name':'MatchImp','id':'avg_importance'},{'name':'Score','id':'bowling_clutch_score'}]
        td=bowl_top10.copy(); td['rank']=[f"#{i+1}" for i in range(len(td))]
        for c in ['economy','dot_pct','clutch_wpa','clutch_wpa_mean','avg_importance','bowling_clutch_score']: td[c]=td[c].round(2)
        for c in ['balls','wkts','shutdown_overs','comeback_spells']: td[c]=td[c].astype(int)

        return html.Div([
            html.H2("Top 10 Bowlers Under Pressure",style={'color':RED}),
            html.P("WPA-weighted, importance-adjusted, with shutdown over and comeback spell bonuses.",style={'color':SUBTEXT,'marginBottom':'18px'}),
            dcc.Graph(figure=ranking_bar(bowl_top10,'bowler_name','bowling_clutch_score',RED,'Bowling Clutch Score')),
            html.Div([dash_table.DataTable(data=td[[c['id'] for c in cols]].to_dict('records'),columns=cols,sort_action='native',
                style_table={'overflowX':'auto'},style_cell={'background':CARD,'color':TEXT,'border':f'1px solid {BORDER}','padding':'10px 12px','fontSize':'12px','textAlign':'center'},
                style_header={'background':BORDER,'color':GOLD,'fontWeight':'700'},
                style_data_conditional=[{'if':{'filter_query':'{rank} = "#1"'},'background':'rgba(245,197,24,0.12)','color':GOLD,'fontWeight':'800'}])
            ],style={'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px','padding':'14px','marginTop':'18px','marginBottom':'24px'}),
            html.H3("Top 3 Radar",style={'color':GOLD}),
            html.Div([html.Div([dcc.Graph(figure=radar_chart(bowl_top10.iloc[i]['bowler_name'],False))],style={'flex':'1','minWidth':'300px'}) for i in range(min(3,len(bowl_top10)))],style={'display':'flex','gap':'14px'}),
            dcc.Graph(figure=shutdown_chart(),style={'marginTop':'20px'}),
        ])

    elif tab=='clutch':
        return html.Div([
            html.H2("Clutch Moment Analysis",style={'color':PURPLE}),
            html.Div([
                html.Div([html.H4("Comebacks",style={'color':ORANGE,'margin':'0 0 4px'}),
                    html.P("Entered when WP < 35% and improved it by 10%+",style={'color':SUBTEXT,'fontSize':'12px'})],
                    style={'flex':'1','background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px','padding':'14px'}),
                html.Div([html.H4("Rescues",style={'color':RED,'margin':'0 0 4px'}),
                    html.P("Entered when WP < 20% and swung it by 15%+",style={'color':SUBTEXT,'fontSize':'12px'})],
                    style={'flex':'1','background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px','padding':'14px'}),
                html.Div([html.H4("Shutdowns",style={'color':GREEN,'margin':'0 0 4px'}),
                    html.P("Conceded <=6 runs when opposition was scoring at 9+ RPO",style={'color':SUBTEXT,'fontSize':'12px'})],
                    style={'flex':'1','background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px','padding':'14px'}),
                html.Div([html.H4("Team Carry",style={'color':PURPLE,'margin':'0 0 4px'}),
                    html.P("Scored 30-40%+ of team runs in a match innings",style={'color':SUBTEXT,'fontSize':'12px'})],
                    style={'flex':'1','background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px','padding':'14px'}),
            ],style={'display':'flex','gap':'12px','flexWrap':'wrap','marginBottom':'20px'}),
            html.Div([html.Div([dcc.Graph(figure=comeback_chart())],style={'flex':'1'}),
                html.Div([dcc.Graph(figure=shutdown_chart())],style={'flex':'1'})],style={'display':'flex','gap':'14px'}),
            html.Div([html.Div([dcc.Graph(figure=dependency_chart())],style={'flex':'1'}),
                html.Div([dcc.Graph(figure=wpa_chart(True))],style={'flex':'1'})],style={'display':'flex','gap':'14px','marginTop':'16px'}),
        ])

    elif tab=='drilldown':
        return html.Div([
            html.H2("Player Drill-Down",style={'color':PURPLE}),
            html.Div([
                html.Div([html.Label("Select Batter",style={'color':SUBTEXT,'fontSize':'12px','fontWeight':'600'}),
                    dcc.Dropdown(id='bat-sel',options=bat_opts,value=bat_top10.iloc[0]['striker_name'],style={'background':CARD2,'color':'#111'}),
                    dcc.Graph(id='bat-radar'),html.Div(id='bat-cards')],style={'flex':'1','minWidth':'380px'}),
                html.Div([html.Label("Select Bowler",style={'color':SUBTEXT,'fontSize':'12px','fontWeight':'600'}),
                    dcc.Dropdown(id='bowl-sel',options=bowl_opts,value=bowl_top10.iloc[0]['bowler_name'],style={'background':CARD2,'color':'#111'}),
                    dcc.Graph(id='bowl-radar'),html.Div(id='bowl-cards')],style={'flex':'1','minWidth':'380px'}),
            ],style={'display':'flex','gap':'24px','flexWrap':'wrap'}),
        ])
    return html.Div("Not found")

@app.callback(Output('bat-radar','figure'),Input('bat-sel','value'))
def u1(n): return radar_chart(n,True) if n else go.Figure()
@app.callback(Output('bowl-radar','figure'),Input('bowl-sel','value'))
def u2(n): return radar_chart(n,False) if n else go.Figure()

@app.callback(Output('bat-cards','children'),Input('bat-sel','value'))
def u3(name):
    if not name: return []
    r=bat_rank[bat_rank['striker_name']==name].iloc[0]
    return html.Div([html.Div([
        stat_card("SR(P)",f"{r['sr']:.1f}","",ACCENT),
        stat_card("Avg(P)",f"{r['avg']:.1f}" if pd.notna(r.get('avg')) else "N/A","",GREEN),
        stat_card("WPA",f"{r['clutch_wpa']:.3f}","enhanced",GOLD),
        stat_card("Comebacks",f"{int(r['comeback_innings'])}","innings",ORANGE),
        stat_card("Releases",f"{int(r['release_moments'])}","moments",RED),
        stat_card("Dep. Index",f"{r['avg_dependency']:.2f}","team carry",PURPLE),
    ],style={'display':'flex','gap':'8px','flexWrap':'wrap'})],
    style={'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px','padding':'12px','marginTop':'10px'})

@app.callback(Output('bowl-cards','children'),Input('bowl-sel','value'))
def u4(name):
    if not name: return []
    r=bowl_rank[bowl_rank['bowler_name']==name].iloc[0]
    return html.Div([html.Div([
        stat_card("Eco(P)",f"{r['economy']:.2f}","",RED),
        stat_card("Wkts(P)",f"{int(r['wkts'])}","",GREEN),
        stat_card("WPA",f"{r['clutch_wpa']:.3f}","enhanced",GOLD),
        stat_card("Shutdowns",f"{int(r['shutdown_overs'])}","overs",ACCENT),
        stat_card("Comebacks",f"{int(r['comeback_spells'])}","spells",ORANGE),
        stat_card("Dep. Index",f"{r['avg_dependency']:.2f}","team carry",PURPLE),
    ],style={'display':'flex','gap':'8px','flexWrap':'wrap'})],
    style={'background':CARD,'border':f'1px solid {BORDER}','borderRadius':'12px','padding':'12px','marginTop':'10px'})

if __name__=='__main__':
    print("\n" + "="*55)
    print("  SupeRR Selector v3 Dashboard")
    print("  Open: http://127.0.0.1:8050")
    print("="*55 + "\n")
    app.run(debug=False,port=8050)
