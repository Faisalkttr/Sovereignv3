# Sovereign Conviction Engine

A combined dashboard wiring your structural allocation grid to your three
analytical engines.

## Structure

```
Home.py                        # Combined Conviction dashboard (start here)
structural_grid.py              # Your sections/layers/tickers/target weights (from the uploaded grid image)
engines/
  expectations_engine.py        # SovereignExpectationsEngine (was app1.py) -- unchanged logic
  valuation_engine.py           # Valuation/scoring functions extracted from app3.py -- unchanged logic
  quality_engine.py             # NEW: ROIC / margins / leverage / dilution scoring
pages/
  1_Expectations_Engine.py      # Standalone single-ticker Expectations page (was streamlit_app.py)
  2_Valuation_Engine.py         # Standalone Valuation & Discipline page (was app3.py), now imports engines/valuation_engine.py
  3_Macro_Engine.py             # Macro regime page (was execution_engine.py), unchanged -- needs a FRED API key
  4_Quality_Engine.py           # NEW: standalone single-ticker Quality page
  5_Ticker_Verifier.py          # NEW: checks whether a ticker resolves in yfinance + has enough data for each engine
```

## Running it

```bash
pip install -r requirements.txt
streamlit run Home.py
```

Streamlit will automatically pick up everything in `pages/` as extra
navigation entries in the sidebar, so all four views (combined + the 3
individual engines) are reachable from one running app.

## How the pieces connect

- **structural_grid.py** is pure data: it encodes your sections (INFRA,
  ENERGY & COMMODITY, AI/SEMIS, EM, BTC, GOLD, CASH) and satellite
  holdings, each ticker's layer, and its target weight within the
  portfolio. `flatten_universe()` turns that into one row per ticker with
  an `effective_weight` (section target % x layer weight).
- **Home.py** lets you pick a subset of sections/tickers, then for each
  one runs:
  1. `valuation_engine.get_hardened_valuation_data()` + `sovereign_allocation_engine()`
     -> a 0-1.5x deployment multiplier based on how rich/cheap the ticker
     is vs. its own P/S history.
  2. `expectations_engine.SovereignExpectationsEngine` -> an Expectations
     Burden Score (0-100) measuring how much forward growth is priced in.
  3. `quality_engine.get_quality_data()` + `compute_quality_score()` -> a
     Quality Score (0-100) from ROIC, gross margin, FCF margin, net
     debt/EBITDA, and share dilution -- is this a *good business*,
     independent of price or timing?
  4. Equal-weights all three into a **Conviction Score**, and computes
     **Suggested $ Deployment** = structural weight x portfolio value x
     valuation multiplier (capped further if Expectations burden is high
     OR Quality is low) x a manual macro overlay multiplier.
- **Macro Engine (page 3)** is intentionally *not* re-implemented inside
  Home.py -- it's a portfolio-wide regime call (FRED liquidity/credit/
  dollar data), not a per-ticker one, and its ~1,400 lines of governor/
  kill-switch/positioning logic would be a second copy to maintain if
  duplicated. Run it separately, read its `governed_target` output, and
  enter that as the "Macro overlay multiplier" in Home.py's sidebar.

## Quality Engine (new)

`engines/quality_engine.py` scores five metrics against an explicit,
editable threshold table (`QUALITY_THRESHOLDS`) -- ROIC, gross margin, FCF
margin, net debt/EBITDA, and YoY share dilution -- then blends them
(re-normalized over whichever metrics were actually resolvable from the
ticker's statements) into a single Quality Score and classification.

It intentionally does **not** try to be sector-aware: royalty/streaming
names (FNV, WPM, TPL) get an explicit warning banner (`sector_caveat`)
rather than a silently misleading score, since a generic operating-company
ROIC/margin template doesn't map cleanly onto their business model. If you
add more royalty/financial/REIT-style names to the grid, add them to
`SECTOR_CAVEAT_TICKERS` too.

## Ticker Verifier (new)

`pages/5_Ticker_Verifier.py` -- run any ticker (or a whole pasted list, or
the entire structural grid at once) through the same category of data
fetches the three scoring engines depend on, and see a pass/fail verdict
*before* trusting it. This is the tool that would have caught the
ADNOC Gas/ACWA Power duplicate, `ABB` resolving to the wrong company, and
`CEO`/`CHL` being dead NYSE tickers since 2021 -- all in one batch check,
instead of one back-and-forth per bad ticker.

Use the "Verify entire grid" tab any time you edit `structural_grid.py`.

## Known gaps / things to sanity-check before trusting the output

- **Non-US ticker symbols** in `structural_grid.py` (Tokyo Electron
  `8035.T`, Lasertec `6920.T`, the GCC/EM tickers, HIJP/EIDO/CEO/1088.HK
  ETF-vs-ADR proxies) are my best-guess Yahoo Finance symbology from your
  image -- **verify each one actually resolves in yfinance** before
  relying on it; several EM/GCC names in particular may need a different
  suffix or an ADR ticker instead of the local listing.
- `CORE_ELIGIBLE_TICKERS` in `structural_grid.py` is my read of which
  tickers your notes say "can be used as core" (TPL, FNV, WPM, TSM, ASML,
  PANW, NVO, XYL, WM, RSG, CNI, CP, plus the Layer-1 hard-asset names) --
  double check this list matches your intent, since `is_core` changes
  which floor logic and caps apply in the Valuation Engine.
- Layer `effective_weight` is a **ceiling for the layer**, not an
  automatic even split across every ticker listed in it (e.g. Layer 2 of
  AI/SEMIS has 6 tickers sharing a 3% (=10%x30%) slice of the portfolio --
  the grid doesn't say how to split that further, so Home.py currently
  shows the same effective_weight for every ticker in a layer). You'll
  want to decide (manually, or by ranking) how much of a layer's ceiling
  each individual name inside it actually gets.
