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
