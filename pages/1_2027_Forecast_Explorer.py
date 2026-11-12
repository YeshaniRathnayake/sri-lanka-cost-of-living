from pathlib import Path
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="2027 Grocery Forecast Explorer", page_icon="🛒", layout="wide")
DATA=Path(__file__).resolve().parent.parent / "data"
@st.cache_data
def load():
    cfg=pd.read_csv(DATA/'grocery_basket_configuration.csv')
    comp=pd.read_csv(DATA/'grocery_basket_components_2020_2026.csv')
    comp['month']=pd.to_datetime(comp['month'])
    monthly=pd.read_csv(DATA/'grocery_basket_monthly_2020_2026.csv',parse_dates=['month'])
    fc=pd.read_csv(DATA/'grocery_basket_forecast_selected_seasonal_naive.csv',parse_dates=['month'])
    metrics=pd.read_csv(DATA/'grocery_14month_model_comparison.csv')
    bt=pd.read_csv(DATA/'grocery_14month_rolling_backtest.csv')
    return cfg,comp,monthly,fc,metrics,bt
cfg,comp,monthly,fc,metrics,bt=load()
st.title('🛒 2027 Cost of Living Forecast Explorer')
st.caption('Colombo retail food prices · Historical January 2020–October 2026 · Forecast November 2026–December 2027')
st.info('This is an illustrative **12-commodity grocery basket**, not an official national cost-of-living forecast. The seasonal-naïve projection is for the **original fixed-quantity basket** only. It repeats the same calendar month cost from the previous year; forecasts beyond October 2027 recursively use earlier predictions.')

with st.sidebar:
    st.header('Build your basket')
    st.caption('Quantities are per month. These are illustrative choices, not official household consumption weights.')
    if st.button('Reset quantities to original basket'):
        for _,r in cfg.iterrows():
            st.session_state[f"qty_{r['commodity_unit']}"]=float(r['basket_quantity'])
        st.rerun()
    qty={}
    for _,r in cfg.iterrows():
        key=f"qty_{r['commodity_unit']}"
        if key not in st.session_state: st.session_state[key]=float(r['basket_quantity'])
        qty[r['commodity_unit']]=st.number_input(f"{r['display_name']} ({r['purchase_unit']})",min_value=0.0,max_value=100.0,step=1.0,key=key)
    st.divider()
    start=st.selectbox('Historical chart starts',monthly.month.dt.strftime('%b %Y').tolist(),index=0)
    st.caption('No prediction bands are shown: the prior experimental intervals have not demonstrated reliable coverage.')

pivot=comp.pivot_table(index='month',columns='commodity_unit',values='mean_price_lkr',aggfunc='first').sort_index()
cols=cfg.commodity_unit.tolist()
missing=[c for c in cols if c not in pivot.columns]
if missing:
    st.error('Missing price series: '+', '.join(missing)); st.stop()
custom=pivot[cols].mul(pd.Series(qty),axis=1).sum(axis=1,min_count=len(cols))
original=pivot[cols].mul(cfg.set_index('commodity_unit').loc[cols,'basket_quantity'],axis=1).sum(axis=1,min_count=len(cols))
if not np.allclose(original.to_numpy(),monthly.set_index('month').loc[original.index,'basket_cost_lkr'].to_numpy(),atol=0.03):
    st.error('Basket reconstruction differs from stored monthly totals. Check inputs.'); st.stop()
last=custom.iloc[-1]; first=custom.iloc[0]; last_original=original.iloc[-1]
last_fc=fc.iloc[-1]['forecast_basket_cost_lkr']
base_fc=fc.loc[fc.month.dt.year.eq(2027),'forecast_basket_cost_lkr']

c1,c2,c3,c4=st.columns(4)
c1.metric('Your basket · Oct 2026',f'Rs. {last:,.0f}')
c2.metric('Your basket · Jan 2020',f'Rs. {first:,.0f}')
c3.metric('Historical change',f'{(last/first-1)*100:+.1f}%' if first>0 else 'N/A')
c4.metric('Original basket · Dec 2027 forecast',f'Rs. {last_fc:,.0f}')

st.subheader('Historical prices and original-basket forecast')
plot_start=pd.to_datetime(start)
fig=go.Figure()
orig=original.loc[original.index>=plot_start]
custom_show=custom.loc[custom.index>=plot_start]
fig.add_trace(go.Scatter(x=orig.index,y=orig.values,mode='lines',name='Original basket · actual',line=dict(color='#2563eb',width=2)))
fig.add_trace(go.Scatter(x=custom_show.index,y=custom_show.values,mode='lines',name='Your basket · actual',line=dict(color='#059669',width=2)))
fig.add_trace(go.Scatter(x=pd.concat([pd.Series([original.index[-1]]),fc.month]),y=[original.iloc[-1]]+fc.forecast_basket_cost_lkr.tolist(),mode='lines+markers',name='Original basket · seasonal naïve forecast',line=dict(color='#d97706',dash='dash',width=3),marker=dict(size=4)))
fig.add_vline(x=fc.month.iloc[0].timestamp()*1000,line_dash='dot',line_color='gray')
fig.update_layout(hovermode='x unified',xaxis_title='',yaxis_title='LKR per basket',legend=dict(orientation='h',y=-0.25),height=480,margin=dict(t=25,b=30))
st.plotly_chart(fig,use_container_width=True)
st.caption('Forecast is for the original fixed basket only. Adjusting quantities does not refit it. Uncertainty bands are intentionally withheld because empirical coverage was not reliably calibrated.')

st.subheader('Compare two historical months')
months=custom.index
left,right=st.columns(2)
with left: a=st.selectbox('From month',months,format_func=lambda x:x.strftime('%b %Y'),index=0)
with right: b=st.selectbox('To month',months,format_func=lambda x:x.strftime('%b %Y'),index=len(months)-1)
if a>b:
    st.warning('Choose a later end month.')
else:
    before=(pivot.loc[a,cols]*pd.Series(qty)).rename('Before (LKR)')
    after=(pivot.loc[b,cols]*pd.Series(qty)).rename('After (LKR)')
    breakdown=pd.concat([before,after],axis=1)
    breakdown['Change (LKR)']=breakdown['After (LKR)']-breakdown['Before (LKR)']
    breakdown['Commodity']=cfg.set_index('commodity_unit').loc[breakdown.index,'display_name']
    breakdown=breakdown.reset_index(drop=True).sort_values('Change (LKR)',ascending=False)
    total_change=breakdown['Change (LKR)'].sum()
    st.metric('Change in your monthly basket',f'Rs. {total_change:+,.0f}',f'{total_change/before.sum()*100:+.1f}%' if before.sum()>0 else None)
    st.plotly_chart(px.bar(breakdown,x='Change (LKR)',y='Commodity',orientation='h',title='Which commodities contributed to the change?',color='Change (LKR)',color_continuous_scale='RdBu_r').update_layout(yaxis=dict(autorange='reversed'),height=460),use_container_width=True)
    st.dataframe(breakdown[['Commodity','Before (LKR)','After (LKR)','Change (LKR)']].round(2),hide_index=True,use_container_width=True)
    st.download_button('Download your basket history',custom.rename('custom_basket_cost_lkr').rename_axis('month').reset_index().to_csv(index=False).encode(),file_name='custom_basket_history.csv',mime='text/csv')

st.subheader('2027 monthly forecast — original basket')
fc27=fc.loc[fc.month.dt.year==2027].copy()
fc27['month']=fc27.month.dt.strftime('%b %Y')
st.dataframe(fc27[['month','forecast_basket_cost_lkr','forecast_source_month']].rename(columns={'month':'Month','forecast_basket_cost_lkr':'Seasonal naïve forecast (LKR)','forecast_source_month':'Same month previous year'}).round(2),hide_index=True,use_container_width=True)
st.download_button('Download original-basket forecast CSV',fc.to_csv(index=False).encode(),file_name='forecast_nov2026_dec2027.csv',mime='text/csv')

st.subheader('Model validation')
metric_view=metrics.copy().sort_values('rmse_lkr')
st.dataframe(metric_view.rename(columns={'model':'Model','backtest_predictions':'Backtest predictions','mae_lkr':'MAE (LKR)','rmse_lkr':'RMSE (LKR)','bias_lkr':'Bias (LKR)'}).round(2),hide_index=True,use_container_width=True)
st.plotly_chart(px.bar(metric_view,x='model',y='rmse_lkr',title='Backtest RMSE · lower is better',labels={'model':'Model','rmse_lkr':'RMSE (LKR)'}),use_container_width=True)
h=st.slider('Inspect forecast horizon (months ahead)',1,14,14)
err=bt.loc[bt.horizon_month==h].copy()
if len(err):
    st.plotly_chart(px.bar(err,x='origin',y='absolute_error_lkr',color='model',barmode='group',title=f'Absolute error at {h}-month horizon',labels={'absolute_error_lkr':'Absolute error (LKR)','origin':'Forecast origin'}),use_container_width=True)
st.caption('Primary model selection uses four historical origins, each with a 14-month forecast window (56 predictions per model). The windows overlap. Seasonal naïve has the lowest RMSE among the tested specifications; this does not guarantee future accuracy.')

with st.expander('Methodology, sources and important limitations',expanded=False):
    st.markdown("""- **Data:** DCS weekly Colombo retail prices via Macro Lab, averaged into months; 12 selected commodities; January 2020–October 2026. The 2026 selected weekly values were checked against DCS PDFs in the project audit.
- **Original basket:** fixed, illustrative monthly quantities; not official consumption weights or a representative household budget. Price changes cannot be interpreted as the official CPI.
- **Forecast:** precomputed seasonal-naïve model predictions for November 2026–December 2027. No live model fitting occurs in this page.
- **Adjustable basket:** changing quantities recomputes *historical* costs and contributions only. It does not change the seasonal-naïve forecast.
- **Uncertainty:** no forecast intervals are displayed because historical interval coverage was insufficiently calibrated.
- **Geography:** Colombo retail market observations, not a Sri Lanka-wide average.
- **Interpretation:** scenarios and forecasts are conditional projections, not guarantees. Policy changes, supply disruptions and exchange rates can change outcomes.""")
    st.download_button('Download original basket configuration',cfg.to_csv(index=False).encode(),file_name='grocery_basket_configuration.csv',mime='text/csv')


st.subheader('Additional diagnostic checks (experimental)')
st.caption('Historical ETS residual diagnostics retained for comparison only. They do NOT describe the selected seasonal-naïve forecast.')
diag=pd.read_csv(DATA/'grocery_ets_residual_diagnostics.csv')
st.dataframe(diag.round(4),hide_index=True,use_container_width=True)
st.caption('Ljung–Box p < 0.05 suggests remaining residual autocorrelation; Jarque–Bera p < 0.05 suggests departures from normality. Model selection should prioritize rolling-origin errors.')
st.subheader('Forecast-horizon error audit')
st.dataframe(pd.read_csv(DATA/'grocery_forecast_horizon_error_audit.csv').round(2),hide_index=True,use_container_width=True)
st.warning('Only four rolling origins and 12-month maximum validation horizon. Quantiles use 12 pooled errors per horizon group and are NOT statistically calibrated 80% or 95% prediction intervals. November–December 2027 envelopes extrapolate beyond the tested horizon. Do not use as a guaranteed price range.')


st.divider()
st.subheader("14-month rolling-origin validation (experimental)")
st.caption("Four historical training cutoffs (see the backtest CSV for exact dates). Each forecasts the next 14 months. Models are refitted at each cutoff; results are out-of-sample. These results use a fixed SARIMA(1,1,1)(0,1,1,12) specification and an additive damped-trend seasonal ETS, which may differ from earlier saved forecast specifications.")
comp14 = pd.read_csv(DATA / "grocery_14month_model_comparison.csv")
st.dataframe(comp14, use_container_width=True, hide_index=True)
st.subheader("Errors by forecast horizon")
horizon14 = pd.read_csv(DATA / "grocery_14month_horizon_errors.csv")
st.dataframe(horizon14, use_container_width=True, hide_index=True)
st.subheader("Exploratory empirical interval coverage")
coverage14 = pd.read_csv(DATA / "grocery_14month_interval_coverage.csv")
st.dataframe(coverage14, use_container_width=True, hide_index=True)
st.warning("Coverage uses only four overlapping forecast origins. These are diagnostic checks, NOT validated 80%/95% prediction intervals. Forecast months 13–14 have particularly little independent evidence. The point forecast shown above now uses the 14-month benchmark winner: seasonal naïve.")
