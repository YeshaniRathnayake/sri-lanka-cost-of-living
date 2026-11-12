# Sri Lanka Cost of Living Dashboard — Prototype

## Start
1. Unzip this folder.
2. Open Command Prompt inside the extracted `sri_lanka_cost_of_living_streamlit` folder.
3. Run `py -m pip install -r requirements.txt`.
4. Run `py -m streamlit run app.py`.
5. Streamlit should open in your browser. If not, open the localhost URL printed in the terminal.

## Data
- `data/macro.csv`: 84 monthly rows, 2019–2025. CCPI, derived inflation, fuel, exchange rate.
- `data/food.csv`: Colombo retail commodity-month prices, 2019–2025 (2019 has December only).

## Statistical cautions
- Monthly food prices are arithmetic averages of available DCS weekly Colombo prices, not national prices.
- Default 3-week threshold prevents very sparse food-price months from being plotted.
- 2019 has only one December weekly food observation. No values were invented for January–November.
- Inflation rates are derived from published rounded CCPI indices and require verification against published inflation series; raw index levels from different base years must not be spliced.
- Fuel revision history is third-party compiled and needs spot verification against CPC official revisions.
- Exchange rate months September–December 2025 are missing. Latest-available metrics may have different effective dates.
- Correlations are descriptive and do not establish causation.

## Future improvements
- Verify 2019 prices, official CCPI rates, CPC revisions, and late-2025 exchange rates.
- Consider adding an official 2019 CBSL price snapshot as a separate historical-context panel, not a continuation of DCS prices.
- Create consistent-market comparison panels if using WFP market-level data.


## New: 2027 Forecast Explorer

Run `streamlit run app.py`, then choose **2027 Forecast Explorer** from the Streamlit page navigation.

The new page contains historical fixed-basket and adjustable-basket costs, commodity contributions, a precomputed ETS forecast through December 2027, illustrative uncertainty ranges, backtesting metrics, and CSV downloads. It uses the existing 2019–2025 dashboard unchanged; the new page reads additional data files in `data/`.

**Important:** Adjusting quantities changes historical comparisons only. The forecast always applies to the original fixed basket; the uncertainty ranges are illustrative and are not formally calibrated prediction intervals. The source data represent Colombo, not all Sri Lanka.


## Forecast diagnostics update
Added fitted ETS residual diagnostics (Ljung–Box, Jarque–Bera), 3-month pooled backtest horizon-error audit, and experimental error envelopes. Existing point forecasts remain unchanged. The envelopes are **not calibrated prediction intervals**; horizons 13–14 extrapolate beyond available backtests. The fitted diagnostic ETS specification may not exactly match the original forecast fit. Additional longer-horizon rolling-origin validation and formal interval calibration remain necessary.


## 14-month validation
Four rolling origins (2023-10, 2024-04, 2024-10, 2025-08), each with a 14-month forecast. ETS uses additive seasonal damped trend; SARIMA uses (1,1,1)(0,1,1,12); seasonal naive repeats last 12 months. Data: `data/grocery_14month_*`. Interval coverage is exploratory and not calibrated. Previous point forecasts are not changed.


## Forecast selection update (November 2026)
The 2027 explorer now displays seasonal-naive (12-month lag) forecasts, matching the 14-month rolling-origin RMSE winner. No prediction intervals are claimed. Prior ETS forecasts and diagnostic datasets remain for comparison. The interactive basket quantity controls only recalculate historical values.
