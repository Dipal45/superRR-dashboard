import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title='SupeRR Selector', page_icon='🏏', layout='wide')

PURPLE='#3B1765'; PINK='#E8287D'; LAV='#F1E7FA'; GOLD='#F5B841'; DARK='#241233'

st.markdown(f'''<style>
.stApp {{ background: linear-gradient(135deg, #fff8fc 0%, #f4ecfb 100%); }}
h1,h2,h3 {{ color:{PURPLE}; }}
[data-testid="stMetricValue"] {{ color:{PINK}; }}
.block-container {{ padding-top: 1.2rem; }}
</style>''', unsafe_allow_html=True)

@st.cache_data
def load_data():
    base=Path(__file__).parent
    bat=pd.read_csv(base/'refined_batter_rankings.csv')
    bowl=pd.read_csv(base/'refined_bowler_rankings.csv')
    return bat,bowl

bat,bowl=load_data()

st.sidebar.markdown('## 🏏 SupeRR Selector')
page=st.sidebar.radio('Navigate', ['Overview','Batters','Bowlers','Player Comparison','Methodology'])


def fmt(x, d=2):
    return '—' if pd.isna(x) else f'{x:.{d}f}'

def rank_table(df, role):
    cols=['rank','player','final_score','raw_score','reliability','hp_balls','hp_matches','seasons']
    out=df[cols].copy().sort_values('rank')
    out.columns=['Rank','Player','Final Score','Raw Score','Reliability','Pressure Balls','Pressure Matches','Seasons']
    return out

def radar(df, player, role):
    row=df.loc[df.player==player].iloc[0]
    if role=='Batter':
        keys=['pressure_perf_z','impact_z','risk_z','baseline_z','consistency_z']
        labels=['Pressure','Impact','Risk Mgmt','Baseline','Consistency']
    else:
        keys=['pressure_perf_z','threat_z','control_z','baseline_z','consistency_z']
        labels=['Pressure','Threat','Control','Baseline','Consistency']
    vals=pd.to_numeric(row[keys],errors='coerce').fillna(0).values.astype(float)
    # min-max within the selected role for a readable player-profile chart
    norm=[]
    for k,v in zip(keys,vals):
        s=pd.to_numeric(df[k],errors='coerce').replace([np.inf,-np.inf],np.nan)
        lo,hi=s.min(),s.max()
        norm.append(50 if pd.isna(lo) or hi==lo else 100*(v-lo)/(hi-lo))
    fig=go.Figure(go.Scatterpolar(r=norm+[norm[0]],theta=labels+[labels[0]],fill='toself',name=player,line_color=PINK))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True,range=[0,100])),showlegend=False,height=420,margin=dict(l=30,r=30,t=30,b=30))
    return fig

if page=='Overview':
    st.title('🏏 SupeRR Selector — Pressure Performance Dashboard')
    st.caption('Season 2 • 2022 onwards • Rankings calculated from the provided analysis outputs')
    c1,c2,c3,c4=st.columns(4)
    c1.metric('Eligible Batters',len(bat)); c2.metric('Eligible Bowlers',len(bowl))
    c3.metric('Top Batter',bat.sort_values('rank').iloc[0].player)
    c4.metric('Top Bowler',bowl.sort_values('rank').iloc[0].player)
    st.markdown('### What does “pressure” mean?')
    st.info('Pressure is the difficulty and urgency of the match situation before a delivery. The model uses contextual signals such as scoring urgency, runs and balls remaining, wickets/resources, innings phase and match closeness.')
    st.markdown('### Top-ranked players')
    a,b=st.columns(2)
    with a: st.subheader('Batters'); st.dataframe(rank_table(bat,'Batter').head(10),use_container_width=True,hide_index=True)
    with b: st.subheader('Bowlers'); st.dataframe(rank_table(bowl,'Bowler').head(10),use_container_width=True,hide_index=True)

elif page in ['Batters','Bowlers']:
    role='Batter' if page=='Batters' else 'Bowler'; df=bat if role=='Batter' else bowl
    st.title(f'🏏 {page} Rankings')
    top_n=st.slider('Show top N players',5,min(25,len(df)),10)
    min_balls=st.slider('Minimum pressure balls',0,int(df.hp_balls.max()),0)
    view=df[df.hp_balls>=min_balls].sort_values('rank').copy()
    st.dataframe(rank_table(view,role).head(top_n),use_container_width=True,hide_index=True)
    if len(view):
        fig=px.bar(view.head(top_n).sort_values('final_score'),x='final_score',y='player',orientation='h',text='rank',color='reliability',color_continuous_scale='RdPu',labels={'final_score':'Final Score','player':'Player','reliability':'Reliability'})
        fig.update_layout(height=max(400,35*top_n),coloraxis_colorbar_title='Reliability')
        st.plotly_chart(fig,use_container_width=True)
    st.markdown('### Player profile')
    player=st.selectbox('Select a player',view.sort_values('rank').player.tolist())
    row=view[view.player==player].iloc[0]
    m1,m2,m3,m4=st.columns(4)
    m1.metric('Rank',int(row['rank'])); m2.metric('Final Score',fmt(row['final_score'],3)); m3.metric('Reliability',fmt(row['reliability'],3)); m4.metric('Pressure Balls',int(row['hp_balls']))
    l,r=st.columns([1,1])
    with l: st.plotly_chart(radar(df,player,role),use_container_width=True)
    with r:
        st.markdown('#### Supporting metrics')
        metrics=['hp_matches','seasons','hp_rpb','base_rpb','uplift_rel','extreme_balls','consistency_pos']
        available=[x for x in metrics if x in row.index]
        st.dataframe(pd.DataFrame({'Metric':available,'Value':[row[x] for x in available]}),use_container_width=True,hide_index=True)

elif page=='Player Comparison':
    st.title('⚔️ Player Comparison')
    role=st.radio('Role',['Batter','Bowler'],horizontal=True)
    df=bat if role=='Batter' else bowl
    options=df.sort_values('rank').player.tolist()
    c1,c2=st.columns(2)
    with c1: p1=st.selectbox('Player 1',options,index=0)
    with c2: p2=st.selectbox('Player 2',options,index=min(1,len(options)-1))
    if p1==p2: st.warning('Choose two different players.')
    else:
        rows=df.set_index('player').loc[[p1,p2]]
        st.dataframe(rows[['rank','final_score','raw_score','reliability','hp_balls','hp_matches','seasons','uplift_rel','consistency_pos']].reset_index(),use_container_width=True,hide_index=True)
        if role=='Batter': keys=['pressure_perf_z','impact_z','risk_z','baseline_z','consistency_z']
        else: keys=['pressure_perf_z','threat_z','control_z','baseline_z','consistency_z']
        comp=rows[keys].T.reset_index().melt(id_vars='index',var_name='Player',value_name='Score')
        fig=px.bar(comp,x='index',y='Score',color='Player',barmode='group',labels={'index':'Dimension'})
        st.plotly_chart(fig,use_container_width=True)

else:
    st.title('🧠 Methodology')
    st.markdown('''### 1. Scope
Only the eligible player universe used in the supplied ranking outputs is shown, with analysis from 2022 onwards.

### 2. Pressure definition
Pressure is estimated from the pre-delivery match situation. The outcome of the delivery is not used to define its prior pressure level.

### 3. Dynamic Pressure Index
**PIₜ = 100 × Σ(wᵢ × Cᵢ,ₜ)**

### 4. Batter score
**B_raw = 0.25P + 0.15I + 0.15R + 0.20U + 0.15C + 0.10X**

### 5. Bowler score
**O_raw = 0.25P + 0.15W + 0.15D + 0.20U + 0.15C + 0.10X**

### 6. Baseline comparison
Batters: **Uᵦ = (SR_pressure / SR_baseline) − 1**

Bowlers: **Uₒ = (Econ_baseline / Econ_pressure) − 1**

### 7. Reliability adjustment
**Final = Rel × Raw Score + (1 − Rel) × Benchmark**

Reliability is treated as a confidence adjustment based on the available pressure evidence, rather than a reward for simply playing more matches.
''')
    st.caption('The dashboard displays and explores the ranking outputs already produced by the methodology.')
