"""
Sri Lanka | Cost of Living Dashboard
Midnight Navy & Teal · Tabbed story version
"""

from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from dashboard_theme import apply_theme, TEAL, MINT, NAVY, AMBER, PALETTE

# ----------------------------------------------------------
# PAGE CONFIG + THEME
# ----------------------------------------------------------
st.set_page_config(
    page_title="Sri Lanka | Cost of Living",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

DATA = Path(__file__).parent / "data"

# ----------------------------------------------------------
# DATA LOADING
# ----------------------------------------------------------
@st.cache_data
def load_all():
    macro = pd.read_csv(DATA / "macro.csv", parse_dates=["month"])
    food = pd.read_csv(DATA / "food.csv", parse_dates=["month"])
    basket = pd.read_csv(DATA / "grocery_basket_monthly_2020_2026.csv", parse_dates=["month"])
    components = pd.read_csv(DATA / "grocery_basket_components_2020_2026.csv", parse_dates=["month"])
    cfg = pd.read_csv(DATA / "grocery_basket_configuration.csv")

    # Optional forecast files (graceful if missing)
    fc_path = DATA / "grocery_basket_forecast_selected_seasonal_naive.csv"
    models_path = DATA / "grocery_14month_model_comparison.csv"
    fc = pd.read_csv(fc_path, parse_dates=["month"]) if fc_path.exists() else None
    models = pd.read_csv(models_path) if models_path.exists() else None

    return macro, food, basket, components, cfg, fc, models


macro, food, basket, components, cfg, fc, models = load_all()

# ----------------------------------------------------------
# SIDEBAR – GLOBAL FILTERS
# ----------------------------------------------------------
with st.sidebar:
    st.header("Filters")
    st.caption("Applies to Overview and Food Prices tabs")

    dr = st.date_input(
        "Date range",
        value=(macro["month"].min().date(), macro["month"].max().date()),
        min_value=macro["month"].min().date(),
        max_value=macro["month"].max().date(),
    )
    if not isinstance(dr, (tuple, list)) or len(dr) != 2:
        st.stop()
    start, end = map(pd.Timestamp, dr)
    if start > end:
        st.warning("End date must be after start date.")
        st.stop()

    show_crisis = st.toggle("Highlight 2022 crisis", value=True)

    st.markdown("---")
    st.caption("Sources: DCS · CBSL · Macro Lab (Colombo weekly retail)")

# Filtered macro
m = macro[macro["month"].between(start, end)]
if m.empty:
    st.warning("No macro data in the selected range.")
    st.stop()

# ----------------------------------------------------------
# HEADER
# ----------------------------------------------------------
st.title("Sri Lanka | Cost of Living")
st.caption(
    "How have prices changed since 2019? Explore inflation, essential groceries, "
    "the 2022 price shock, and an experimental 2027 outlook."
)
st.info(
    "The grocery basket is an **illustrative fixed set of 12 items** priced in Colombo — "
    "not an official national cost-of-living measure."
)

# ----------------------------------------------------------
# TABS
# ----------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📉 Overview",
    "📖 Price Shock",
    "🛒 Food Prices",
    "🧮 My Basket",
    "🔮 2027 Outlook",
])

# ==========================================================
# TAB 1 – OVERVIEW
# ==========================================================
with tab1:
    st.subheader("Key indicators")

    def latest(col, fmt):
        x = m[col].dropna()
        return fmt.format(x.iloc[-1]) if not x.empty else "—"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Headline inflation", latest("headline_yoy_pct_derived", "{:.1f}%"))
    c2.metric("Petrol 92", latest("petrol92_monthly_mean_lkr_per_litre", "Rs. {:,.0f}/L"))
    c3.metric("Diesel", latest("auto_diesel_monthly_mean_lkr_per_litre", "Rs. {:,.0f}/L"))
    c4.metric("USD / LKR", latest("usd_lkr_monthly_average", "Rs. {:.1f}"))

    st.caption("Latest values inside the selected date range.")

    # Inflation series selector
    series_map = {
        "Headline": "headline_yoy_pct_derived",
        "Food": "food_yoy_pct_derived",
        "Non-food": "nonfood_yoy_pct_derived",
    }
    chosen = st.multiselect(
        "Inflation series",
        options=list(series_map.keys()),
        default=["Headline", "Food"],
    )

    if chosen:
        fig = go.Figure()
        colors = [NAVY, TEAL, MINT]
        for i, name in enumerate(chosen):
            col = series_map[name]
            fig.add_trace(
                go.Scatter(
                    x=m["month"], y=m[col],
                    name=name, line=dict(color=colors[i % 3], width=2.5),
                )
            )
        if show_crisis:
            fig.add_vrect(
                x0="2022-01-01", x1="2022-12-31",
                fillcolor=AMBER, opacity=0.12, line_width=0,
                annotation_text="2022",
            )
        fig.update_layout(
            height=400, yaxis_title="YoY %",
            legend=dict(orientation="h", y=1.08),
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)

    # Basket cost overview
    st.subheader("Illustrative grocery basket cost")
    first, last = basket.iloc[0], basket.iloc[-1]
    a, b, c = st.columns(3)
    a.metric("Jan 2020", f"Rs. {first.basket_cost_lkr:,.0f}")
    b.metric("Latest", f"Rs. {last.basket_cost_lkr:,.0f}")
    c.metric("Change", f"{(last.basket_cost_lkr / first.basket_cost_lkr - 1) * 100:+.1f}%")

    fig_b = px.line(
        basket, x="month", y="basket_cost_lkr",
        labels={"month": "", "basket_cost_lkr": "Rs. per basket"},
    )
    fig_b.update_traces(line=dict(color=TEAL, width=3))
    if show_crisis:
        fig_b.add_vrect(
            x0="2022-01-01", x1="2022-12-31",
            fillcolor=AMBER, opacity=0.12, line_width=0,
            annotation_text="2022 price shock",
        )
    fig_b.update_layout(height=380)
    st.plotly_chart(fig_b, use_container_width=True)

# ==========================================================
# TAB 2 – PRICE SHOCK STORY
# ==========================================================
with tab2:
    st.subheader("The 2022 price shock")
    st.caption("How the same fixed basket of groceries changed in cost.")

    # Metrics
    first, last = basket.iloc[0], basket.iloc[-1]
    a, b, c = st.columns(3)
    a.metric("Jan 2020", f"Rs. {first.basket_cost_lkr:,.0f}")
    b.metric("Latest (Oct 2026)", f"Rs. {last.basket_cost_lkr:,.0f}")
    c.metric("Overall change", f"{(last.basket_cost_lkr / first.basket_cost_lkr - 1) * 100:+.1f}%")

    # Main basket line
    fig = px.line(
        basket, x="month", y="basket_cost_lkr",
        labels={"month": "", "basket_cost_lkr": "Rs. per basket"},
    )
    fig.update_traces(line=dict(color=TEAL, width=3))
    fig.add_vrect(
        x0="2022-01-01", x1="2022-12-31",
        fillcolor=AMBER, opacity=0.14, line_width=0,
        annotation_text="2022 crisis",
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Period comparison
    st.subheader("Which items drove the change?")
    months = basket["month"].tolist()
    col_a, col_b = st.columns(2)
    with col_a:
        begin = st.selectbox(
            "From", months, index=0,
            format_func=lambda x: x.strftime("%b %Y"), key="shock_from",
        )
    with col_b:
        finish = st.selectbox(
            "To", months, index=len(months) - 1,
            format_func=lambda x: x.strftime("%b %Y"), key="shock_to",
        )

    if begin >= finish:
        st.warning("Choose a later ending month.")
    else:
        x = components.loc[
            components["month"].eq(begin), ["display_name", "basket_component_lkr"]
        ].rename(columns={"basket_component_lkr": "before"})
        y = components.loc[
            components["month"].eq(finish), ["display_name", "basket_component_lkr"]
        ].rename(columns={"basket_component_lkr": "after"})
        ch = x.merge(y, on="display_name")
        ch["change"] = ch["after"] - ch["before"]
        ch = ch.sort_values("change")

        st.metric("Net change in basket", f"Rs. {ch['change'].sum():+,.0f}")

        # Horizontal contribution bar
        fig_bar = px.bar(
            ch, x="change", y="display_name", orientation="h",
            color_discrete_sequence=[TEAL],
            labels={"change": "Contribution (Rs.)", "display_name": ""},
        )
        fig_bar.update_layout(height=480)
        st.plotly_chart(fig_bar, use_container_width=True)

        # Side-by-side donuts – composition then vs now
        st.subheader("Basket composition (share of cost)")
        d1, d2 = st.columns(2)

        def make_donut(df_month, title):
            fig = px.pie(
                df_month, names="display_name", values="basket_component_lkr",
                hole=0.45, color_discrete_sequence=PALETTE,
            )
            fig.update_layout(title=title, height=360, showlegend=True,
                              legend=dict(orientation="h", y=-0.15))
            fig.update_traces(textposition="inside", textinfo="percent")
            return fig

        with d1:
            before_df = components[components["month"] == begin]
            st.plotly_chart(make_donut(before_df, begin.strftime("%b %Y")), use_container_width=True)
        with d2:
            after_df = components[components["month"] == finish]
            st.plotly_chart(make_donut(after_df, finish.strftime("%b %Y")), use_container_width=True)

# ==========================================================
# TAB 3 – FOOD PRICES
# ==========================================================
with tab3:
    st.subheader("Explore individual food prices")
    st.caption("Colombo retail averages. Compare trends, not absolute levels across different units.")

    choices = sorted(food["commodity_unit"].dropna().unique())
    # Sensible defaults
    defaults = [c for c in choices if any(k in c for k in ["Samba", "Nadu", "Egg", "Chicken", "Coconut - average"])][:3]

    selected = st.multiselect(
        "Select commodities (max 5)",
        choices,
        default=defaults,
        max_selections=5,
    )

    if selected:
        f = food[
            food["commodity_unit"].isin(selected)
            & (food["weeks_observed"] >= 3)
            & food["month"].between(start, end)
        ]
        if f.empty:
            st.info("No sufficiently observed prices for these dates.")
        else:
            fig = px.line(
                f, x="month", y="mean_price_lkr", color="commodity_unit",
                color_discrete_sequence=PALETTE,
                labels={"month": "", "mean_price_lkr": "Rs.", "commodity_unit": ""},
            )
            if show_crisis:
                fig.add_vrect(
                    x0="2022-01-01", x1="2022-12-31",
                    fillcolor=AMBER, opacity=0.10, line_width=0,
                )
            fig.update_layout(height=420, legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig, use_container_width=True)

    # Biggest risers (optional insight)
    st.subheader("Largest price increases (selected window)")
    if selected and not f.empty:
        # % change from first to last observation in range
        summary = []
        for item in selected:
            sub = f[f["commodity_unit"] == item].sort_values("month")
            if len(sub) < 2:
                continue
            p0, p1 = sub["mean_price_lkr"].iloc[0], sub["mean_price_lkr"].iloc[-1]
            summary.append({
                "Item": item,
                "Start": p0,
                "End": p1,
                "Change %": (p1 / p0 - 1) * 100 if p0 else None,
            })
        if summary:
            sdf = pd.DataFrame(summary).dropna().sort_values("Change %", ascending=True)
            fig_r = px.bar(
                sdf, x="Change %", y="Item", orientation="h",
                color_discrete_sequence=[TEAL],
                labels={"Change %": "% change in window", "Item": ""},
            )
            fig_r.update_layout(height=max(280, 40 * len(sdf)))
            st.plotly_chart(fig_r, use_container_width=True)

# ==========================================================
# TAB 4 – MY BASKET (IMPROVED)
# ==========================================================
with tab4:
    st.subheader("Build your own basket")
    st.caption(
        "Adjust quantities below. Costs use Colombo monthly averages from the component series."
    )

    # Quantity inputs
    st.markdown("##### Monthly quantities")
    qty = {}
    cols = st.columns(3)
    for i, row in cfg.iterrows():
        with cols[i % 3]:
            qty[row["display_name"]] = st.number_input(
                f"{row['display_name']} ({row['purchase_unit']})",
                min_value=0.0,
                value=float(row["basket_quantity"]),
                step=0.5,
                key=f"qty_{row['display_name']}",
            )

    # Map display_name → component costs over time
    # We scale the original component cost by (user_qty / original_qty)
    orig_qty = dict(zip(cfg["display_name"], cfg["basket_quantity"]))

    # Use latest and a base month
    base_month = pd.Timestamp("2020-01-01")
    latest_month = components["month"].max()

    def scaled_cost(month, display_name, user_q):
        row = components[
            (components["month"] == month) & (components["display_name"] == display_name)
        ]
        if row.empty or orig_qty.get(display_name, 0) == 0:
            return None
        unit_cost = row["basket_component_lkr"].iloc[0] / orig_qty[display_name]
        return unit_cost * user_q

    rows = []
    total_base = 0.0
    total_now = 0.0

    for name, user_q in qty.items():
        if user_q <= 0:
            continue
        c_base = scaled_cost(base_month, name, user_q)
        c_now = scaled_cost(latest_month, name, user_q)
        if c_base is None or c_now is None:
            continue
        total_base += c_base
        total_now += c_now
        rows.append({
            "Item": name,
            "Qty": user_q,
            "Cost 2020": round(c_base),
            "Cost now": round(c_now),
            "Change %": round((c_now / c_base - 1) * 100, 1) if c_base else None,
        })

    st.markdown("---")

    if rows:
        change = (total_now / total_base - 1) * 100 if total_base else 0

        m1, m2, m3 = st.columns(3)
        m1.metric("Basket · Jan 2020", f"Rs. {total_base:,.0f}")
        m2.metric("Basket · now", f"Rs. {total_now:,.0f}")
        m3.metric("Change", f"{change:+.1f}%")

        # Then vs Now bar
        fig_cmp = go.Figure()
        fig_cmp.add_trace(go.Bar(name="Jan 2020", x=["Your basket"], y=[total_base], marker_color=NAVY))
        fig_cmp.add_trace(go.Bar(name="Now", x=["Your basket"], y=[total_now], marker_color=TEAL))
        fig_cmp.update_layout(barmode="group", height=280, yaxis_title="LKR", margin=dict(t=20))
        st.plotly_chart(fig_cmp, use_container_width=True)

        # Detail table
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # Optional: user basket composition pie (latest)
        pie_df = pd.DataFrame(rows)
        if not pie_df.empty:
            fig_pie = px.pie(
                pie_df, names="Item", values="Cost now",
                hole=0.45, color_discrete_sequence=PALETTE,
                title="Your basket · current cost share",
            )
            fig_pie.update_layout(height=360, legend=dict(orientation="h", y=-0.15))
            st.plotly_chart(fig_pie, use_container_width=True)

        if change > 0:
            st.warning(f"Your basket costs **{change:.0f}% more** than in January 2020.")
        else:
            st.success(f"Your basket costs **{abs(change):.0f}% less** than in January 2020.")
    else:
        st.info("Set some quantities above zero to calculate the basket.")

# ==========================================================
# TAB 5 – 2027 OUTLOOK
# ==========================================================
with tab5:
    st.subheader("Experimental outlook to 2027")
    st.info(
        "Illustrative projections only — not official inflation forecasts. "
        "Uncertainty bands are not shown because reliable interval coverage has not been established."
    )

    if fc is not None and not fc.empty:
        last = basket.iloc[-1]
        end = fc.iloc[-1]

        a, b, c = st.columns(3)
        a.metric("Last observed", f"Rs. {last.basket_cost_lkr:,.0f}")
        b.metric("Projected · Dec 2027", f"Rs. {end.forecast_basket_cost_lkr:,.0f}")
        c.metric("Model", "Seasonal naïve")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=basket["month"], y=basket["basket_cost_lkr"],
            name="Observed", line=dict(color=TEAL, width=3),
        ))
        # Connect last observed to forecast
        fig.add_trace(go.Scatter(
            x=pd.concat([pd.Series([last["month"]]), fc["month"]]),
            y=[last["basket_cost_lkr"]] + fc["forecast_basket_cost_lkr"].tolist(),
            name="Projected", line=dict(color=AMBER, dash="dash", width=3),
        ))
        fig.update_layout(
            height=450, yaxis_title="Rs. per fixed basket",
            legend=dict(orientation="h", y=-0.15), hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Seasonal-naïve method repeats the corresponding month of the previous year. "
            "Forecasts beyond the first year use earlier projected values."
        )
    else:
        st.warning("Forecast file not found in the data folder.")

    # Model comparison if available
    if models is not None and not models.empty:
        st.subheader("Model comparison (backtest)")
        # Flexible: show whatever numeric columns exist
        st.dataframe(models, use_container_width=True, hide_index=True)

with st.expander("Sources and methodology"):
    st.markdown(
        """
**Sources:** Department of Census and Statistics (DCS), Central Bank of Sri Lanka (CBSL),  
and DCS weekly Colombo retail prices (via Macro Lab).

**Methods:** Monthly aggregation, descriptive comparisons, a fixed-quantity illustrative basket,  
and rolling-origin forecast evaluation. The 2027 projection uses a seasonal-naïve benchmark.

**Limits:** Colombo food prices are not national averages; the basket is not expenditure-weighted;  
forecasts are experimental.
"""
    )