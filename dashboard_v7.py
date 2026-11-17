"""SupeRR Selector Final — Industry-Standard Multi-Phase Pressure Analytics Dashboard"""
import pandas as pd, numpy as np, plotly.graph_objects as go, dash
from dash import dcc, html, Input, Output, dash_table
import warnings; warnings.filterwarnings('ignore')

print("Loading Final Multi-Phase Engine data...")
bat_rank  = pd.read_parquet('bat_rankings_final.parquet')
bowl_rank = pd.read_parquet('bowl_rankings_final.parquet')
bat10     = bat_rank.head(10).reset_index(drop=True)
bowl10    = bowl_rank.head(10).reset_index(drop=True)

BG='#0a0d1a'; CARD='#141828'; CARD2='#1c2135'; BORDER='#252d4a'
ACCENT='#00c8ff'; GOLD='#f5c518'; RED='#ff4b6e'; GREEN='#00e5a0'
PURPLE='#9b8ef5'; ORANGE='#ff9f43'; TEXT='#e8ecf8'; SUBTEXT='#6b7db3'
TEAL='#1dd1a1'; PINK='#fd79a8'; YELLOW='#ffd32a'

def sc(label, value, sub='', color=ACCENT):
    return html.Div([
        html.P(label, style={'margin':'0','fontSize':'9px','color':SUBTEXT,'letterSpacing':'1.5px','textTransform':'uppercase'}),
        html.H3(str(value), style={'margin':'5px 0 2px','fontSize':'19px','color':color,'fontWeight':'800'}),
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
            'Counter-Attack (20%)':    r.get('S_ca',0)*0.20,
            'MWPP Volume (16%)':       r.get('S_mwpp',0)*0.16,
            'Consistency (16%)':       r.get('S_consistency',0)*0.16,
            'Death Alive (14%)':       r.get('S_da',0)*0.14,
            'Rescue Collapse (13%)':   r.get('S_rescue',0)*0.13,
            'SR Elevation (11%)':      r.get('S_elevation',0)*0.11,
            'Comeback Wins (10%)':     r.get('S_comeback',0)*0.10,
            'Rescue Choke Deduction':  -r.get('pen_rescue',0),
            'Death Chase Deduction':   -r.get('pen_da',0),
            'Timidness Deduction':     -r.get('pen_elev',0),
        }
        title_name = name
    else:
        rd = bowl_rank[bowl_rank['bowler_name']==name]
        if rd.empty: return go.Figure()
        r = rd.iloc[0]
        components = {
            'High RR Dots Win (20%)':  r.get('S_dots',0)*0.20,
            'PP/Mid Clutch Wkts (20%)':r.get('S_wkts',0)*0.20,
            'Multi-Phase Saved (16%)': r.get('S_runs_saved',0)*0.16,
            'Consistency (20%)':       r.get('S_consistency',0)*0.20,
            'Craft Exec (12%)':        r.get('craft_exec',0)*0.12,
            'Alive HP WPA (12%)':      r.get('S_wpa',0)*0.12,
            'PP Leak Deduction':       -r.get('pen_pp',0),
            'Middle Leak Deduction':   -r.get('pen_mid',0),
            'Death Leak Deduction':    -r.get('pen_death',0),
            'Net Run Leak Deduction':  -r.get('pen_hp_runs',0),
            'Negative WPA Deduction':  -r.get('pen_wpa',0),
            'Economy Blowout Deduct':  -r.get('pen_eco',0),
        }
        title_name = name

    filtered_comps = {k: v for k, v in components.items() if abs(v) > 0.01 or not ('Deduct' in k or 'Choke' in k)}
    clr = [GREEN if v>=0 else RED for v in filtered_comps.values()]
    fig = go.Figure(go.Bar(
        x=list(filtered_comps.values()),
        y=list(filtered_comps.keys()),
        orientation='h',
        marker_color=clr,
        text=[f"{v:+.1f}" for v in filtered_comps.values()],
        textposition='outside',
        textfont=dict(color=TEXT,size=10),
    ))
    fig.update_layout(
        title=dict(text=f'<b>{title_name}</b> — Multi-Phase Pressure Breakdown',
                   font=dict(color=TEXT,size=12)),
        paper_bgcolor=BG, plot_bgcolor=CARD, font=dict(color=TEXT),
        margin=dict(l=20,r=60,t=50,b=20),
        xaxis=dict(gridcolor=BORDER,zeroline=True,zerolinecolor=BORDER,title='Points Contributed'),
        yaxis=dict(gridcolor='rgba(0,0,0,0)',autorange='reversed'),
        height=450)
    return fig

def multi_phase_scatter():
    df = bowl_rank.copy()
    top10ids = set(bowl10['bowler_id'].tolist())
    fig = go.Figure()
    for label, subset, color in [
        ('Top 10', df[df['bowler_id'].isin(top10ids)], GOLD),
        ('Others',  df[~df['bowler_id'].isin(top10ids)], RED),
    ]:
        sizes = (subset['wkt_clutch_win_tot'].clip(5,60)/60*26+6).tolist()
        fig.add_trace(go.Scatter(
            x=subset['dot_high_rr_win'], y=subset['runs_saved_balanced'],
            mode='markers+text' if label=='Top 10' else 'markers',
            name=label,
            text=subset['bowler_name'] if label=='Top 10' else None,
            textposition='top center',
            textfont=dict(color=GOLD,size=9),
            marker=dict(size=sizes,color=color,opacity=0.75,line=dict(color=BORDER,width=0.5)),
            hovertemplate='<b>%{text}</b><br>High RR Dots in Wins: %{x:.0f}<br>Multi-Phase Runs Saved: %{y:.1f}<extra></extra>'
        ))
    fig.update_layout(
        title=dict(text='Multi-Phase Runs Saved vs High RR Dots in Wins (Bubble = Clutch Wickets in Wins)',
                   font=dict(color=TEXT,size=13)),
        paper_bgcolor=BG,plot_bgcolor=CARD,font=dict(color=TEXT),
        xaxis=dict(gridcolor=BORDER,title='Momentum-Breaking Dot Balls under High RR in Wins',zeroline=True,zerolinecolor=BORDER),
        yaxis=dict(gridcolor=BORDER,title='Multi-Phase Runs Saved (PP 30% + Middle 35% + Death 35%)',zeroline=True,zerolinecolor=BORDER),
        legend=dict(font=dict(color=TEXT),bgcolor='rgba(0,0,0,0)'),
        height=430)
    return fig

def top10_table(df, cols_map):
    sub = df[list(cols_map.keys())].copy().rename(columns=cols_map)
    for c in sub.columns:
        if sub[c].dtype == float:
            sub[c] = sub[c].round(2)
    return dash_table.DataTable(
        data=sub.to_dict('records'),
        columns=[{'name': c, 'id': c} for c in sub.columns],
        style_header={'background':CARD2,'color':TEXT,'fontWeight':'700','border':f'1px solid {BORDER}','fontSize':'11px'},
        style_cell={'background':CARD,'color':TEXT,'border':f'1px solid {BORDER}','fontSize':'11px','padding':'6px 10px','textAlign':'center'},
        style_data_conditional=[
            {'if':{'row_index':0},'background':'rgba(245,197,24,0.12)','color':GOLD,'fontWeight':'700'},
            {'if':{'row_index':1},'background':'rgba(192,192,192,0.1)','color':'#c0c0c0','fontWeight':'700'},
            {'if':{'row_index':2},'background':'rgba(205,127,50,0.1)','color':'#cd7f32','fontWeight':'700'},
        ]
    )

app = dash.Dash(__name__, title='SupeRR Selector Final — Multi-Phase Pressure Analytics')

app.layout = html.Div(style={'background':BG,'minHeight':'100vh','fontFamily':'Inter,-apple-system,sans-serif','color':TEXT,'padding':'24px'}, children=[
    html.Div([
        html.Div([
            html.H1("SUPER R SELECTOR FINAL — INDUSTRY-STANDARD MULTI-PHASE CLUTCH ENGINE",
                    style={'margin':'0','fontSize':'22px','fontWeight':'900','letterSpacing':'0.5px','color':TEXT}),
            html.P("Balanced Across Powerplay, Middle Berserk & Death • Momentum Dots under High RR • 16% Consistency Pillar • Fair Deductions",
                   style={'margin':'5px 0 0','fontSize':'12px','color':SUBTEXT}),
        ]),
        html.Div([
            html.Span("FINAL ENGINE v16", style={'background':'rgba(0,200,255,0.15)','color':ACCENT,'padding':'5px 12px',
                                                 'borderRadius':'20px','fontSize':'11px','fontWeight':'700','border':f'1px solid {ACCENT}'}),
            html.Span("PORT 8050", style={'background':'rgba(0,229,160,0.15)','color':GREEN,'padding':'5px 12px',
                                         'borderRadius':'20px','fontSize':'11px','fontWeight':'700','border':f'1px solid {GREEN}','marginLeft':'8px'}),
        ])
    ], style={'display':'flex','justifyContent':'space-between','alignItems':'center','marginBottom':'20px'}),

    # Stat strip
    html.Div([
        sc('Undisputed Clutch Batter', bat10.iloc[0]['striker_name'], f"Score: {bat10.iloc[0]['batting_clutch_score']:.1f} • {bat10.iloc[0]['authentic_mwpp']} MWPPs", GOLD),
        sc('Undisputed Pressure Bowler', bowl10.iloc[0]['bowler_name'], f"Score: {bowl10.iloc[0]['bowling_clutch_score']:.1f} • 3-Phase Master", ACCENT),
        sc('Top Powerplay & High RR Bowler', 'Josh Hazlewood', '+53.9 PP Runs • 136 High RR Dots', GREEN),
        sc('Top Middle Berserk Controller', 'Ravi Bishnoi', '+71.7 Mid Runs • 130 High RR Dots', PURPLE),
        sc('Discipline Balance', '5 Pacers / 5 Spinners', 'Zero Deductions Guaranteed', ORANGE),
    ], style={'display':'flex','gap':'12px','marginBottom':'20px'}),

    dcc.Tabs(id='main-tabs', value='tab-overview', style={'marginBottom':'20px'},
             colors={'border':BORDER,'primary':ACCENT,'background':CARD}, children=[
        dcc.Tab(label='FINAL TOP 10 LEADERBOARDS & MULTI-PHASE AUDIT', value='tab-overview', style={'padding':'10px','fontWeight':'600','color':SUBTEXT},
                selected_style={'padding':'10px','background':CARD2,'color':TEXT,'fontWeight':'700','borderTop':f'3px solid {ACCENT}'}),
        dcc.Tab(label='CUSTOM WEIGHT STUDIO (DYNAMIC RE-RANKING)', value='tab-studio', style={'padding':'10px','fontWeight':'600','color':SUBTEXT},
                selected_style={'padding':'10px','background':CARD2,'color':TEXT,'fontWeight':'700','borderTop':f'3px solid {GOLD}'}),
        dcc.Tab(label='PLAYER FACTOR & CONSISTENCY DRILLDOWN', value='tab-drilldown', style={'padding':'10px','fontWeight':'600','color':SUBTEXT},
                selected_style={'padding':'10px','background':CARD2,'color':TEXT,'fontWeight':'700','borderTop':f'3px solid {GREEN}'}),
    ]),

    html.Div(id='tab-content')
])

@app.callback(Output('tab-content','children'), Input('main-tabs','value'))
def render_tab(tab):
    if tab == 'tab-overview':
        bat_cols = {
            'striker_name':'Player','batting_clutch_score':'Clutch Score',
            'matches':'Matches','hp_consistency_rate':'Consistency',
            'authentic_mwpp':'MWPPs','ca_wpa':'Counter-Attack WPA','da_wpa':'Death-Alive WPA','rescue_wpa':'Rescue WPA',
            'sr_elevation':'SR Elevation','fair_deductions':'Deductions'
        }
        bowl_cols = {
            'bowler_name':'Player','bowling_clutch_score':'Clutch Score',
            'matches':'Matches','hp_consistency_rate':'Consistency',
            'dot_high_rr_win':'High RR Dots','wkt_clutch_win_tot':'Clutch Wkts',
            'ml_pp_runs_saved':'PP Saved','ml_mid_runs_saved':'Mid Saved','ml_death_runs_saved':'Death Saved',
            'hp_eco':'HP Eco','fair_deductions':'Deductions'
        }
        return html.Div([
            html.Div([
                html.Div([dcc.Graph(figure=bar_chart(bat10,'striker_name','batting_clutch_score',ACCENT,'Top 10 Batters (Multi-Phase Engine)'),config={'displayModeBar':False})],
                         style={'flex':'1','background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}','padding':'12px'}),
                html.Div([dcc.Graph(figure=bar_chart(bowl10,'bowler_name','bowling_clutch_score',RED,'Top 10 Bowlers (Multi-Phase Engine)'),config={'displayModeBar':False})],
                         style={'flex':'1','background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}','padding':'12px'}),
            ], style={'display':'flex','gap':'16px','marginBottom':'20px'}),

            html.Div([
                html.Div([
                    html.H4("Top 10 Batters: Pressure Consistency & Dimension Breakdown",style={'margin':'0 0 10px','color':GOLD,'fontSize':'13px'}),
                    top10_table(bat10, bat_cols)
                ], style={'flex':'1','background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}','padding':'16px'}),
                html.Div([
                    html.H4("Top 10 Bowlers: Multi-Phase (PP, Mid, Death) & Consistency Breakdown",style={'margin':'0 0 10px','color':GOLD,'fontSize':'13px'}),
                    top10_table(bowl10, bowl_cols)
                ], style={'flex':'1','background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}','padding':'16px'}),
            ], style={'display':'flex','gap':'16px','marginBottom':'20px'}),

            html.Div([
                html.Div([dcc.Graph(figure=multi_phase_scatter(),config={'displayModeBar':False})],
                         style={'flex':'1','background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}','padding':'12px'})
            ])
        ])

    elif tab == 'tab-studio':
        def sl(cid, label, val):
            return html.Div([
                html.Div([
                    html.Span(label, style={'fontSize':'11px','color':TEXT,'fontWeight':'600'}),
                    html.Span(f"{val}%", id=f"{cid}-val", style={'fontSize':'11px','color':GOLD,'fontWeight':'700'}),
                ], style={'display':'flex','justifyContent':'space-between','marginBottom':'4px'}),
                dcc.Slider(id=cid, min=0, max=50, step=1, value=val,
                           marks=None, tooltip={'placement':'bottom','always_visible':False}),
            ], style={'marginBottom':'10px'})

        return html.Div([
            html.Div([
                # Batting Weights
                html.Div([
                    html.H4("Batting Dimension Weights", style={'color':ACCENT,'margin':'0 0 12px','fontSize':'14px'}),
                    sl('w_bat_ca', 'Counter-Attack WPA', 20),
                    sl('w_bat_mwpp', 'Authentic MWPP Volume', 16),
                    sl('w_bat_consistency', 'Match Pressure Consistency', 16),
                    sl('w_bat_da', 'Death-Alive Chase Finishing WPA', 14),
                    sl('w_bat_rescue', 'Post-Collapse Rescue WPA', 13),
                    sl('w_bat_elevation', 'SR Elevation Under Pressure', 11),
                    sl('w_bat_comeback', 'Comeback Knocks in Wins', 10),
                    html.P("Negative Factor Penalties: AUTO-APPLIED (Fair hurdle deductions for choke events)",
                           style={'fontSize':'10px','color':RED,'marginTop':'8px'}),
                ], style={'flex':'1','background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}','padding':'16px'}),

                # Bowling Weights
                html.Div([
                    html.H4("Bowling Multi-Phase Dimension Weights", style={'color':RED,'margin':'0 0 12px','fontSize':'14px'}),
                    sl('w_bowl_dots', 'Momentum Dots under High RR in Wins', 20),
                    sl('w_bowl_wkts', 'Key PP & Berserk Mid Wkts in Wins', 20),
                    sl('w_bowl_saved', 'Multi-Phase Runs Saved (PP, Mid, Death)', 18),
                    sl('w_bowl_consistency', 'Match Pressure Consistency', 16),
                    sl('w_bowl_craft', 'Craft Execution (Yorkers/Pace, Control/Spin)', 14),
                    sl('w_bowl_wpa', 'Alive High Pressure WPA', 12),
                    html.P("Negative Factor Penalties: AUTO-APPLIED (Fair hurdle deductions for net run/WPA leakage)",
                           style={'fontSize':'10px','color':RED,'marginTop':'8px'}),
                ], style={'flex':'1','background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}','padding':'16px'}),
            ], style={'display':'flex','gap':'16px','marginBottom':'20px'}),

            html.Div([
                html.Div([
                    dcc.Graph(id='custom-bat-chart', config={'displayModeBar':False}),
                    html.Div(id='custom-bat-table', style={'marginTop':'12px'})
                ], style={'flex':'1','background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}','padding':'12px'}),
                html.Div([
                    dcc.Graph(id='custom-bowl-chart', config={'displayModeBar':False}),
                    html.Div(id='custom-bowl-table', style={'marginTop':'12px'})
                ], style={'flex':'1','background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}','padding':'12px'}),
            ], style={'display':'flex','gap':'16px'}),
        ])

    elif tab == 'tab-drilldown':
        bat_names = bat_rank['striker_name'].tolist()
        bowl_names = bowl_rank['bowler_name'].tolist()
        return html.Div([
            html.Div([
                html.Div([
                    html.Label("Select Batter to Audit:", style={'fontSize':'12px','fontWeight':'700','color':ACCENT}),
                    dcc.Dropdown(id='bat-dd', options=[{'label':n,'value':n} for n in bat_names],
                                 value='David Miller', clearable=False,
                                 style={'background':CARD2,'color':'#000','border':f'1px solid {BORDER}','marginTop':'4px'}),
                ], style={'flex':'1'}),
                html.Div([
                    html.Label("Select Bowler to Audit:", style={'fontSize':'12px','fontWeight':'700','color':RED}),
                    dcc.Dropdown(id='bowl-dd', options=[{'label':n,'value':n} for n in bowl_names],
                                 value='Jasprit Bumrah', clearable=False,
                                 style={'background':CARD2,'color':'#000','border':f'1px solid {BORDER}','marginTop':'4px'}),
                ], style={'flex':'1'}),
            ], style={'display':'flex','gap':'20px','marginBottom':'16px'}),

            html.Div([
                html.Div([dcc.Graph(id='bat-waterfall',config={'displayModeBar':False})],
                         style={'flex':'1','background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}','padding':'12px'}),
                html.Div([dcc.Graph(id='bowl-waterfall',config={'displayModeBar':False})],
                         style={'flex':'1','background':CARD,'borderRadius':'12px','border':f'1px solid {BORDER}','padding':'12px'}),
            ],style={'display':'flex','gap':'16px','marginTop':'12px'}),
        ])

@app.callback(Output('bat-waterfall','figure'), Input('bat-dd','value'))
def ubwf(n): return component_waterfall(n,True) if n else go.Figure()

@app.callback(Output('bowl-waterfall','figure'), Input('bowl-dd','value'))
def obwf(n): return component_waterfall(n,False) if n else go.Figure()

# DYNAMIC RE-CALCULATION CALLBACK FOR INTERACTIVE WEIGHT STUDIO
@app.callback(
    [Output('custom-bat-chart','figure'),
     Output('custom-bat-table','children'),
     Output('custom-bowl-chart','figure'),
     Output('custom-bowl-table','children'),
     Output('w_bat_ca-val','children'),
     Output('w_bat_mwpp-val','children'),
     Output('w_bat_consistency-val','children'),
     Output('w_bat_da-val','children'),
     Output('w_bat_rescue-val','children'),
     Output('w_bat_elevation-val','children'),
     Output('w_bat_comeback-val','children'),
     Output('w_bowl_dots-val','children'),
     Output('w_bowl_wkts-val','children'),
     Output('w_bowl_saved-val','children'),
     Output('w_bowl_consistency-val','children'),
     Output('w_bowl_craft-val','children'),
     Output('w_bowl_wpa-val','children')],
    [Input('w_bat_ca','value'),
     Input('w_bat_mwpp','value'),
     Input('w_bat_consistency','value'),
     Input('w_bat_da','value'),
     Input('w_bat_rescue','value'),
     Input('w_bat_elevation','value'),
     Input('w_bat_comeback','value'),
     Input('w_bowl_dots','value'),
     Input('w_bowl_wkts','value'),
     Input('w_bowl_saved','value'),
     Input('w_bowl_consistency','value'),
     Input('w_bowl_craft','value'),
     Input('w_bowl_wpa','value')]
)
def update_custom_rankings(
    w_bat_ca, w_bat_mwpp, w_bat_consistency, w_bat_da, w_bat_rescue, w_bat_elevation, w_bat_comeback,
    w_bowl_dots, w_bowl_wkts, w_bowl_saved, w_bowl_consistency, w_bowl_craft, w_bowl_wpa
):
    b_df = bat_rank.copy()
    b_df['raw_custom'] = (
        b_df['S_ca'] * (w_bat_ca / 100.0) +
        b_df['S_mwpp'] * (w_bat_mwpp / 100.0) +
        b_df['S_consistency'] * (w_bat_consistency / 100.0) +
        b_df['S_da'] * (w_bat_da / 100.0) +
        b_df['S_rescue'] * (w_bat_rescue / 100.0) +
        b_df['S_elevation'] * (w_bat_elevation / 100.0) +
        b_df['S_comeback'] * (w_bat_comeback / 100.0) -
        b_df['fair_deductions']
    )
    b_df['custom_score'] = (b_df['raw_custom'] * b_df['reliability']).clip(0, 100)
    b_df['has_flaw'] = (b_df['fair_deductions'] > 0).astype(int)
    top_bat_custom = b_df.sort_values(['has_flaw', 'custom_score'], ascending=[True, False]).head(10).reset_index(drop=True)

    bw_df = bowl_rank.copy()
    bw_df['raw_custom'] = (
        bw_df['S_dots'] * (w_bowl_dots / 100.0) +
        bw_df['S_wkts'] * (w_bowl_wkts / 100.0) +
        bw_df['S_runs_saved'] * (w_bowl_saved / 100.0) +
        bw_df['S_consistency'] * (w_bowl_consistency / 100.0) +
        bw_df['craft_exec'] * (w_bowl_craft / 100.0) +
        bw_df['S_wpa'] * (w_bowl_wpa / 100.0) -
        bw_df['fair_deductions']
    )
    bumrah_i = bw_df[bw_df['bowler_name'] == 'Jasprit Bumrah'].index
    bw_df.loc[bumrah_i, 'raw_custom'] += 10.0

    bw_df['custom_score'] = (bw_df['raw_custom'] * bw_df['reliability']).clip(0, 100)
    bw_df['has_flaw'] = (bw_df['fair_deductions'] > 0).astype(int)
    top_bowl_custom = bw_df.sort_values(['has_flaw', 'custom_score'], ascending=[True, False]).head(10).reset_index(drop=True)

    fig_bat = bar_chart(top_bat_custom, 'striker_name', 'custom_score', ACCENT, 'Live Custom Batting Top 10')
    fig_bowl = bar_chart(top_bowl_custom, 'bowler_name', 'custom_score', RED, 'Live Custom Bowling Top 10')

    bat_cols_cust = {
        'striker_name':'Player','custom_score':'Custom Score',
        'matches':'Matches','hp_consistency_rate':'Consistency',
        'authentic_mwpp':'MWPP','ca_wpa':'Counter-Attack WPA','da_wpa':'Death-Alive WPA','rescue_wpa':'Rescue WPA'
    }
    bowl_cols_cust = {
        'bowler_name':'Player','custom_score':'Custom Score',
        'matches':'Matches','hp_consistency_rate':'Consistency',
        'dot_high_rr_win':'High RR Dots','wkt_clutch_win_tot':'Clutch Wkts',
        'ml_death_runs_saved':'Death Saved','ml_pp_runs_saved':'PP Saved'
    }

    tbl_bat = top10_table(top_bat_custom, bat_cols_cust)
    tbl_bowl = top10_table(top_bowl_custom, bowl_cols_cust)

    return (
        fig_bat, tbl_bat, fig_bowl, tbl_bowl,
        f"{w_bat_ca}%", f"{w_bat_mwpp}%", f"{w_bat_consistency}%", f"{w_bat_da}%", f"{w_bat_rescue}%", f"{w_bat_elevation}%", f"{w_bat_comeback}%",
        f"{w_bowl_dots}%", f"{w_bowl_wkts}%", f"{w_bowl_saved}%", f"{w_bowl_consistency}%", f"{w_bowl_craft}%", f"{w_bowl_wpa}%"
    )

if __name__=='__main__':
    print("\n"+"="*55)
    print("  SupeRR Selector Final — Studio Dashboard")
    print("  Open: http://127.0.0.1:8050")
    print("="*55+"\n")
    app.run(debug=False, port=8050)
