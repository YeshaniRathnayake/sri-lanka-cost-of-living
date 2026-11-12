from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title='Sri Lanka | Cost of Living', page_icon='📊', layout='wide')
BASE = Path(__file__).parent / 'data'
@st.cache_data
def load():
    macro = pd.read_csv(BASE/'macro.csv', parse_dates=['month'])
    food = pd.read_csv(BASE/'food.csv', parse_dates=['month'])
    return macro, food
macro, food = load()

st.title('Sri Lanka | Cost of Living')
st.caption('2019–2025 · Monthly economic trends and Colombo retail food prices · Prototype based on reconciled historical datasets')
min_date, max_date = macro.month.min().date(), macro.month.max().date()
with st.sidebar:
    st.header('Explore the data')
    period = st.date_input('Common date range', (min_date, max_date), min_value=min_date, max_value=max_date)
    if not isinstance(period, (list,tuple)) or len(period) != 2:
        st.info('Choose a start and end date.')
        st.stop()
    start, end = pd.Timestamp(period[0]), pd.Timestamp(period[1])
    if start > end: st.warning('Start must be before end.'); st.stop()
    st.caption('The same date range applies to all charts. Missing observations are not filled.')

m = macro.loc[macro.month.between(start,end)].copy()
f = food.loc[food.month.between(start,end)].copy()
if m.empty: st.warning('No observations in the selected period.'); st.stop()

page = st.tabs(['Overview','Food prices','Fuel & exchange rates','Relationships','Data quality'])
def line(df, y, title, ylabel, color=None):
    if df.empty: st.info('No observations available in this period.'); return
    fig = px.line(df, x='month', y=y, color=color, title=title, markers=False)
    fig.update_layout(yaxis_title=ylabel, xaxis_title='', legend_title_text='', hovermode='x unified', margin=dict(t=55,b=20))
    fig.update_xaxes(range=[start,end + pd.offsets.MonthEnd(0)])
    st.plotly_chart(fig, use_container_width=True)
def last_value(s,fmt):
    v=s.dropna()
    return fmt.format(v.iloc[-1]) if len(v) else 'N/A'

with page[0]:
    a,b,c,d=st.columns(4)
    a.metric('Latest headline inflation*',last_value(m.headline_yoy_pct_derived,'{:.1f}%'))
    b.metric('Petrol 92 (LKR/L)',last_value(m.petrol92_monthly_mean_lkr_per_litre,'{:.0f}'))
    c.metric('Diesel (LKR/L)',last_value(m.auto_diesel_monthly_mean_lkr_per_litre,'{:.0f}'))
    d.metric('USD/LKR monthly avg.',last_value(m.usd_lkr_monthly_average,'{:.2f}'))
    st.caption('*Derived year-on-year inflation from rounded CCPI indices; not independently verified against official published rates. Metrics show the latest available observation in the selected range, which may differ by indicator.')
    line(m,['headline_yoy_pct_derived','food_yoy_pct_derived'],'Headline vs food inflation','Year-on-year change (%)')
    st.info('Food retail-price coverage begins in December 2019 (one week only). Reliable monthly commodity comparisons generally begin January 2020. The exchange-rate series ends in August 2025.')

with page[1]:
    st.subheader('Colombo retail food prices')
    choices=sorted(f.commodity_unit.unique())
    preferred=[v for v in choices if any(k in v.lower() for k in ['samba - average','mysore dhall - average','bread (450'])]
    chosen=st.multiselect('Choose commodities (compare price levels only when units match)',choices,default=preferred[:3] or choices[:3])
    foodview=f[f.commodity_unit.isin(chosen)].copy()
    min_weeks=st.slider('Minimum weekly observations per month',1,5,3)
    foodview=foodview[foodview.weeks_observed>=min_weeks]
    line(foodview,'mean_price_lkr','Monthly mean retail prices','LKR per labelled unit','commodity_unit')
    st.caption('Each monthly value is the arithmetic mean of available weekly DCS Colombo prices. The threshold excludes sparse months; no interpolation is applied. Do not interpret Colombo market prices as national averages.')
    if chosen:
        count=f[f.commodity_unit.isin(chosen)].groupby('commodity_unit').agg(months=('month','nunique'),months_3plus=('weeks_observed',lambda x:(x>=3).sum())).reset_index()
        st.dataframe(count,use_container_width=True,hide_index=True)

with page[2]:
    st.subheader('Fuel and exchange rates')
    line(m,['petrol92_monthly_mean_lkr_per_litre','auto_diesel_monthly_mean_lkr_per_litre'],'Monthly fuel prices (day-weighted)','LKR per litre')
    line(m,'usd_lkr_monthly_average','USD/LKR monthly average','LKR per USD')
    st.caption('Fuel prices come from a third-party revision compilation and require official CPC spot checks. USD/LKR is unavailable September–December 2025; the line stops at the last observation.')

with page[3]:
    st.subheader('Explore associations — not causation')
    options={'Headline inflation (%)':'headline_yoy_pct_derived','Food inflation (%)':'food_yoy_pct_derived','Petrol 92 (LKR/L)':'petrol92_monthly_mean_lkr_per_litre','Diesel (LKR/L)':'auto_diesel_monthly_mean_lkr_per_litre','USD/LKR':'usd_lkr_monthly_average'}
    col1,col2=st.columns(2)
    with col1: xname=st.selectbox('X variable',list(options),index=4)
    with col2: yname=st.selectbox('Y variable',list(options),index=0)
    x,y=options[xname],options[yname]
    valid=m[['month',x,y]].dropna() if x!=y else m[['month',x]].dropna()
    if x==y: st.info('Select two different indicators.')
    elif len(valid)<3: st.info('Not enough overlapping observations.')
    else:
        fig=px.scatter(valid,x=x,y=y,hover_data=['month'],title=f'{xname} vs {yname}')
        fig.update_layout(xaxis_title=xname,yaxis_title=yname)
        st.plotly_chart(fig,use_container_width=True)
        st.caption(f'{len(valid)} overlapping months. Pearson correlation: {valid[x].corr(valid[y]):.2f}. Shared trends and serial dependence can create misleading correlations; no causal inference.')

with page[4]:
    st.subheader('Coverage and methodology')
    st.write('All panels use the selected global time range, but coverage is not equal across indicators.')
    coverage=pd.DataFrame([
        {'Indicator':'Headline CCPI index','Available months':int(m.headline_index.notna().sum()),'Caution':'Two base years; never splice index levels directly'},
        {'Indicator':'Derived headline YoY inflation','Available months':int(m.headline_yoy_pct_derived.notna().sum()),'Caution':'Derived from rounded index values; validate official rates'},
        {'Indicator':'Petrol 92','Available months':int(m.petrol92_monthly_mean_lkr_per_litre.notna().sum()),'Caution':'Third-party history; CPC validation pending'},
        {'Indicator':'USD/LKR','Available months':int(m.usd_lkr_monthly_average.notna().sum()),'Caution':'Missing Sep–Dec 2025'},
        {'Indicator':'Any Colombo food series','Available months':int(f.month.nunique()),'Caution':'2019 only December; individual commodity gaps vary'},
    ])
    st.dataframe(coverage,use_container_width=True,hide_index=True)
    st.write('**CCPI base-year boundaries**')
    st.dataframe(m.groupby('ccpi_base_year',dropna=False).agg(first_month=('month','min'),last_month=('month','max'),months=('month','size')).reset_index(),use_container_width=True,hide_index=True)
    st.warning('This prototype is for exploration, not a finalized official statistical release. Reconcile published CCPI inflation, verify CPC fuel revisions and complete FX months before presenting definitive conclusions.')
    st.download_button('Download selected monthly macro data',m.to_csv(index=False).encode(),file_name='selected_macro.csv',mime='text/csv')
    st.download_button('Download selected food observations',f.to_csv(index=False).encode(),file_name='selected_food.csv',mime='text/csv')

st.divider()
st.caption('Sources: DCS Colombo weekly retail prices via Macro Lab; DCS CCPI publications; CBSL monthly USD/LKR; historical fuel revisions compiled by Dulaj Mendis. See README for limitations.')
