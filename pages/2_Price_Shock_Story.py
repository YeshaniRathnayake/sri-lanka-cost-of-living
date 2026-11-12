from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

st.set_page_config(page_title='The Price Shock | Story Dash', page_icon='📖', layout='wide')
DATA = Path(__file__).resolve().parents[1] / 'data'
@st.cache_data
def get_data():
    basket = pd.read_csv(DATA/'grocery_basket_monthly_2020_2026.csv', parse_dates=['month'])
    components = pd.read_csv(DATA/'grocery_basket_components_2020_2026.csv', parse_dates=['month'])
    forecast = pd.read_csv(DATA/'grocery_basket_forecast_selected_seasonal_naive.csv', parse_dates=['month'])
    macro = pd.read_csv(DATA/'macro.csv', parse_dates=['month'])
    return basket, components, forecast, macro
basket, components, forecast, macro = get_data()
basket = basket.sort_values('month')

st.title('📖 The Price Shock: Sri Lanka’s Essential Groceries')
st.caption('A data story about 2020–2026 Colombo retail prices and an experimental 2027 outlook')
st.info('This is an illustrative fixed-quantity basket of 12 groceries—not the official CCPI, a national average, or the spending of a typical family.')

first = basket.iloc[0]; last = basket.iloc[-1]
peak = basket.loc[basket.basket_cost_lkr.idxmax()]
change = (last.basket_cost_lkr / first.basket_cost_lkr - 1) * 100
k1,k2,k3,k4 = st.columns(4)
k1.metric('January 2020', f'Rs. {first.basket_cost_lkr:,.0f}')
k2.metric('October 2026', f'Rs. {last.basket_cost_lkr:,.0f}', f'+{change:.1f}% since Jan 2020')
k3.metric('Highest observed month', peak.month.strftime('%b %Y'))
k4.metric('Highest observed basket cost', f'Rs. {peak.basket_cost_lkr:,.0f}')

st.subheader('Chapter 1 · The cost of the same groceries changed dramatically')
fig=go.Figure()
fig.add_trace(go.Scatter(x=basket.month,y=basket.basket_cost_lkr,name='Observed basket cost',mode='lines',line=dict(color='#137c82',width=3),hovertemplate='%{x|%b %Y}<br>Rs. %{y:,.0f}<extra></extra>'))
fig.add_vrect(x0='2022-01-01',x1='2022-12-31',fillcolor='#e76f51',opacity=.12,line_width=0,annotation_text='2022 price shock',annotation_position='top left')
fig.update_layout(yaxis_title='LKR per fixed basket',xaxis_title='',hovermode='x unified',height=420,margin=dict(t=25,b=10))
st.plotly_chart(fig,use_container_width=True)
st.caption('The shaded 2022 period is contextual highlighting, not a statistical estimate of causation. Prices are arithmetic means of available weekly Colombo retail observations.')

st.subheader('Chapter 2 · What drove the basket’s increase?')
months=basket.month.dt.strftime('%b %Y').tolist()
left,right=st.columns(2)
with left: start_label=st.selectbox('Starting month',months,index=0)
with right: end_label=st.selectbox('Ending month',months,index=len(months)-1)
start=pd.to_datetime(start_label,format='%b %Y'); end=pd.to_datetime(end_label,format='%b %Y')
if start>=end:
    st.warning('Select an ending month after the starting month.')
else:
    a=components.loc[components.month.eq(start),['display_name','basket_component_lkr']].rename(columns={'basket_component_lkr':'start_cost'})
    b=components.loc[components.month.eq(end),['display_name','basket_component_lkr']].rename(columns={'basket_component_lkr':'end_cost'})
    delta=a.merge(b,on='display_name',validate='one_to_one')
    delta['change_lkr']=delta.end_cost-delta.start_cost
    delta=delta.sort_values('change_lkr')
    total=delta.change_lkr.sum()
    st.metric('Change in the selected basket',f'Rs. {total:+,.0f}',f'{start_label} → {end_label}')
    fig=px.bar(delta,x='change_lkr',y='display_name',orientation='h',color='change_lkr',color_continuous_scale='RdBu_r',color_continuous_midpoint=0)
    fig.update_layout(height=490,xaxis_title='Contribution to basket-cost change (LKR)',yaxis_title='',coloraxis_showscale=False,margin=dict(l=15,r=15,t=15,b=15))
    st.plotly_chart(fig,use_container_width=True)
    st.caption('Contributions are differences in each item’s fixed-quantity cost, so they sum to the overall basket-cost change. Negative bars represent offsets.')
    with st.expander('See the contribution calculations'):
        st.dataframe(delta.sort_values('change_lkr',ascending=False),hide_index=True,use_container_width=True)

st.subheader('Chapter 3 · The 2022 food inflation surge in context')
food_inf=macro[['month','food_yoy_pct_derived','headline_yoy_pct_derived']].dropna(how='all',subset=['food_yoy_pct_derived','headline_yoy_pct_derived'])
fig=px.line(food_inf,x='month',y=['food_yoy_pct_derived','headline_yoy_pct_derived'],labels={'value':'Year-on-year inflation (%)','variable':'Indicator','month':''})
fig.update_layout(height=370,hovermode='x unified',legend_title_text='',margin=dict(t=15,b=15))
st.plotly_chart(fig,use_container_width=True)
st.caption('DCS CCPI-derived year-on-year rates from the supplied macro dataset; these are not basket-price growth rates. CPI index base changes mean raw index levels must not be spliced across the rebasing boundary.')

st.subheader('Chapter 4 · A cautious view toward 2027')
forecast=forecast.sort_values('month')
last_forecast=forecast.iloc[-1]
st.metric('December 2027 benchmark projection',f'Rs. {last_forecast.forecast_basket_cost_lkr:,.0f}',help='Seasonal-naïve projection, not a confidence-bound prediction.')
fig=go.Figure()
fig.add_trace(go.Scatter(x=basket.month,y=basket.basket_cost_lkr,name='Observed 2020–Oct 2026',mode='lines',line=dict(color='#137c82',width=3)))
fig.add_trace(go.Scatter(x=forecast.month,y=forecast.forecast_basket_cost_lkr,name='Seasonal-naïve projection',mode='lines+markers',line=dict(color='#d97706',width=3,dash='dash')))
fig.add_vline(x=basket.month.max().timestamp()*1000,line_dash='dot',line_color='gray')
fig.update_layout(height=420,xaxis_title='',yaxis_title='Basket cost (LKR)',hovermode='x unified',margin=dict(t=15,b=15))
st.plotly_chart(fig,use_container_width=True)
st.warning('The 2027 projection is experimental. Four overlapping 14-month historical backtests favored seasonal naïve among the tested models, but this does not establish future accuracy. No calibrated prediction intervals are available.')
st.caption('Seasonal naïve repeats the value from 12 months earlier. November–December 2027 therefore inherit projected November–December 2026 values, because observed 2026 data ends in October.')

with st.expander('Methods, scope and reproducibility'):
    st.markdown('''**Geography:** Colombo retail prices, not all Sri Lanka.  
**Observed period:** January 2020–October 2026; November 2026 onward is forecast.  
**Basket:** 12 groceries with fixed, illustrative purchase quantities; it is not expenditure-weighted.  
**Monthly prices:** arithmetic means of the available DCS weekly Colombo retail-price observations.  
**Contribution chart:** quantity × monthly unit price, differenced between selected months.  
**Forecast model:** seasonal naïve, selected as the lowest-RMSE candidate in the available four-origin 14-month backtest; model rankings may change with additional origins.  
**Interpretation:** co-occurring economic changes are not proof of a causal relationship.''')
    st.download_button('Download monthly basket series',basket.to_csv(index=False),file_name='storydash_basket_monthly.csv',mime='text/csv')
    st.download_button('Download forecast series',forecast.to_csv(index=False),file_name='storydash_forecast.csv',mime='text/csv')

st.caption('Sources: DCS Colombo weekly retail prices via Macro Lab; DCS CCPI data; forecast and validation files supplied with this Story Dash project.')
