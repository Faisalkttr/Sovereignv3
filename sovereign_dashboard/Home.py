"""
Sovereign Conviction Engine -- combined dashboard.

This is the real version of the "paste a CSV, get a ranked Top 10" idea --
wired to your actual Expectations Engine and Valuation Engine (not fake
manual 0-100 inputs), and scoped to the tickers in your structural
allocation grid (structural_grid.py) rather than a blank text box.

WHAT IT DOES
  For each selected ticker:
    1. Runs the Valuation Engine  -> richness vs. own history (z-score,
       percentile, MAD) -> a 0-1.5x deployment multiplier.
    2. Runs the Expectations Engine -> how much forward growth is priced
       in vs. required -> an Expectations Burden Score (0-100, higher =
       more priced-for-perfection risk).
    3. Blends both into a single Conviction Score, and combines the
       Valuation multiplier with your structural target weight (from the
       grid) to size a suggested $ deployment.

WHAT IT DOESN'T DO
  It does NOT re-implement the Macro Engine's FRED pipeline here (that's
  a portfolio-wide regime call, not a per-ticker one, and duplicating a
  1,400-line pipeline into this page would be its own maintenance burden).
  Instead, run the Macro Engine page separately and enter its output
  as the "Macro overlay multiplier" in the sidebar -- same manual-input
  philosophy the Macro Engine itself already uses for your allocation %
  and positioning inputs.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent))
from engines.expectations_engine import SovereignExpectationsEngine
from engines import valuation_engine
from engines import quality_engine
from structural_grid import (
    CORE_ELIGIBLE_TICKERS,
    NON_EQUITY_TICKERS,
    flatten_universe,
)

st.set_page_config(page_title="Sovereign Conviction Engine", page_icon="🏆", layout="wide")

st.title("🏆 Sovereign Conviction Engine")
st.caption(
    "Structural Grid + Valuation Engine + Expectations Engine -> ranked deployment table. "
    "Macro regime is a manual overlay -- run the Macro Engine page and enter its reading below."
)

UNIVERSE = flatten_universe()
UNIVERSE_DF = pd.DataFrame(UNIVERSE)

# ----------------------------------------------------------------------
# Sidebar controls
# ----------------------------------------------------------------------

st.sidebar.header("💵 Portfolio Sizing")
total_portfolio_value = st.sidebar.number_input(
    "Total portfolio value", min_value=0.0, value=100000.0, step=1000.0,
    help="Used with each ticker's structural target weight to size suggested $ deployment.",
)

st.sidebar.header("🌐 Macro Overlay (manual)")
macro_multiplier = st.sidebar.slider(
    "Macro regime multiplier", min_value=0.0, max_value=2.0, value=1.0, step=0.05,
    help="Read this off the Macro Engine page (governed_target / your normal target, roughly) "
         "and enter it here. 1.0 = neutral / no macro adjustment. This scales every risk-asset "
         "suggested deployment below; it is NOT re-derived from FRED inside this page.",
)
macro_mode_for_valuation = st.sidebar.selectbox(
    "Macro liquidity regime (feeds the Valuation Engine's own floor logic)",
    options=[
        "🟢 Expansion Mode (Unrestricted System Liquidity)",
        "🟡 Transition / K-Polarization (Contracting Liquidity)",
        "🔴 Forced System Crunch / Active Asset Stripping",
    ],
    index=1,
)

st.sidebar.header("📊 Valuation Engine Parameters")
lookback_years = st.sidebar.slider("Historical Lookback (Years)", 3, 10, 5)
z_threshold = st.sidebar.number_input("Z-Score Pressure Threshold (σ)", value=2.0, step=0.1)

st.sidebar.header("👑 Core Floor Settings")
core_crunch_floor = st.sidebar.number_input("Core Crunch Floor", value=0.10, min_value=0.0, max_value=1.0, step=0.05)
core_transition_floor = st.sidebar.number_input("Core Transition Floor", value=0.25, min_value=0.0, max_value=1.0, step=0.05)
core_expansion_floor = st.sidebar.number_input("Core Expansion Floor", value=0.35, min_value=0.0, max_value=1.0, step=0.05)
floors_cfg = {"crunch": core_crunch_floor, "transition": core_transition_floor, "expansion": core_expansion_floor}

# ----------------------------------------------------------------------
# Ticker selection
# ----------------------------------------------------------------------

st.subheader("📋 Select tickers to scan")

sections_available = sorted(UNIVERSE_DF["section"].unique())
picked_sections = st.multiselect(
    "Sections", options=sections_available, default=["INFRA", "ENERGY & COMMODITY", "AI/SEMIS"],
    help="Each ticker triggers 2 data-fetch pipelines (Valuation + Expectations). Keep the list "
         "short while testing -- yfinance calls are the slow part.",
)

candidate_df = UNIVERSE_DF[UNIVERSE_DF["section"].isin(picked_sections)]
candidate_tickers = sorted(t for t in candidate_df["ticker"].unique() if t not in NON_EQUITY_TICKERS)

picked_tickers = st.multiselect(
    "Tickers (equity only -- BTC/GOLD/CASH are shown separately below as fixed sleeves)",
    options=candidate_tickers, default=candidate_tickers,
)

run_clicked = st.button("🚀 Run Conviction Scan", type="primary")

# ----------------------------------------------------------------------
# Fixed non-equity sleeves (BTC / GOLD / CASH) -- always shown, no engine calls
# ----------------------------------------------------------------------

st.subheader("🪙 Fixed Sleeves (not scored -- structural allocation only)")
fixed_rows = UNIVERSE_DF[UNIVERSE_DF["ticker"].isin(NON_EQUITY_TICKERS)]
fixed_display = fixed_rows[["ticker", "effective_weight"]].copy()
fixed_display["Suggested $"] = fixed_display["effective_weight"] * total_portfolio_value
fixed_display.columns = ["Sleeve", "Target Weight", "Suggested $"]
fixed_display["Target Weight"] = fixed_display["Target Weight"].map(lambda x: f"{x:.1%}")
fixed_display["Suggested $"] = fixed_display["Suggested $"].map(lambda x: f"{x:,.0f}")
st.dataframe(fixed_display, use_container_width=True, hide_index=True)

st.divider()

# ----------------------------------------------------------------------
# Scan
# ----------------------------------------------------------------------

if not run_clicked:
    st.info("Pick your sections/tickers above and click **Run Conviction Scan**.")
    st.stop()

if not picked_tickers:
    st.warning("No tickers selected.")
    st.stop()

results = []
progress = st.progress(0.0, text="Starting scan...")

for i, ticker in enumerate(picked_tickers):
    progress.progress((i) / len(picked_tickers), text=f"Scanning {ticker}...")

    grid_row = candidate_df[candidate_df["ticker"] == ticker].iloc[0]
    is_core = ticker in CORE_ELIGIBLE_TICKERS

    row = {
        "Ticker": ticker,
        "Section": grid_row["section"],
        "Layer": grid_row["layer"],
        "Structural Weight": grid_row["effective_weight"],
        "Core": "Yes" if is_core else "No",
        "Valuation Status": "N/A",
        "Expectations Status": "N/A",
        "Quality Status": "N/A",
        "Valuation Multiplier": np.nan,
        "Expectations Burden": np.nan,
        "Quality Score": np.nan,
        "Conviction Score": np.nan,
        "Suggested $ Deployment": np.nan,
        "Notes": "",
    }

    # --- Valuation Engine ---
    try:
        df_data, error, report_freq, fx_note = valuation_engine.get_hardened_valuation_data(ticker, lookback_years)
        if error or df_data is None or df_data.empty:
            row["Notes"] = f"Valuation Engine: {error or 'no data'}"
        else:
            current_ps = df_data["PS_Ratio"].iloc[-1]
            mean_ps = df_data["PS_Ratio"].mean()
            std_ps = df_data["PS_Ratio"].std()
            z_score = (current_ps - mean_ps) / std_ps if std_ps and not np.isnan(std_ps) and std_ps != 0 else 0.0
            robust_z, _, _ = valuation_engine.calculate_robust_z_score(df_data["PS_Ratio"], current_ps)
            diags = valuation_engine.calculate_distribution_diagnostics(df_data["PS_Ratio"], current_ps)

            status_stance, val_mult, explanation, _ = valuation_engine.sovereign_allocation_engine(
                ticker=ticker, is_core=is_core, z_score=z_score, robust_z_score=robust_z,
                z_threshold=z_threshold, percentile=diags["percentile"], skewness=diags["skewness"],
                macro_mode=macro_mode_for_valuation, floors=floors_cfg,
            )
            row["Valuation Status"] = status_stance
            row["Valuation Multiplier"] = val_mult
    except Exception as e:
        row["Notes"] = f"Valuation Engine exception: {e}"

    # --- Expectations Engine ---
    try:
        engine = SovereignExpectationsEngine(ticker, is_core=is_core)
        exp_df = engine.hydrate_standalone_data()
        metrics = engine.execute(exp_df)
        row["Expectations Status"] = metrics["Expectations Classification"]
        row["Expectations Burden"] = metrics["Expectations Burden Score"]
    except Exception as e:
        row["Notes"] = (row["Notes"] + " | " if row["Notes"] else "") + f"Expectations Engine exception: {e}"

    # --- Quality Engine ---
    try:
        q_metrics, q_error = quality_engine.get_quality_data(ticker)
        if q_error or q_metrics is None:
            row["Notes"] = (row["Notes"] + " | " if row["Notes"] else "") + f"Quality Engine: {q_error or 'no data'}"
        else:
            q_result = quality_engine.compute_quality_score(ticker, q_metrics)
            row["Quality Status"] = q_result["classification"]
            row["Quality Score"] = q_result["quality_score"]
    except Exception as e:
        row["Notes"] = (row["Notes"] + " | " if row["Notes"] else "") + f"Quality Engine exception: {e}"

    # --- Blend into Conviction Score + suggested deployment ---
    val_mult = row["Valuation Multiplier"]
    burden = row["Expectations Burden"]
    quality_score = row["Quality Score"]

    have_any = not np.isnan(val_mult) or not np.isnan(burden) or not np.isnan(quality_score)
    if have_any:
        val_component = min(max(val_mult, 0), 1.5) / 1.5 * 100 if not np.isnan(val_mult) else 50.0
        exp_component = 100 - burden if not np.isnan(burden) else 50.0
        qual_component = quality_score if not np.isnan(quality_score) else 50.0

        # Equal-weighted three-way blend. Valuation and Expectations answer
        # "is now a good time / price," Quality answers "is this a good
        # business at all" -- independent axes, so no single engine should
        # be able to carry a bad business to a high Conviction Score just
        # because it looks statistically cheap or unpriced-for-perfection.
        row["Conviction Score"] = (val_component + exp_component + qual_component) / 3

        # Expectations and Quality both act as hard caps on deployment
        # intensity, not just score inputs -- a cheap-looking multiple on a
        # fragile business, or one still pricing in aggressive growth,
        # shouldn't get full-size deployment just because the Valuation
        # Engine alone says "Value Zone".
        effective_mult = val_mult if not np.isnan(val_mult) else 0.0
        if not np.isnan(burden):
            if burden >= 75:
                effective_mult = min(effective_mult, 0.50)
            elif burden >= 55:
                effective_mult = min(effective_mult, 0.75)
        if not np.isnan(quality_score):
            if quality_score < 35:
                effective_mult = min(effective_mult, 0.50)
            elif quality_score < 50:
                effective_mult = min(effective_mult, 0.75)

        deployment_mult = effective_mult * (macro_multiplier if not is_core else max(macro_multiplier, 0.5))
        row["Suggested $ Deployment"] = grid_row["effective_weight"] * total_portfolio_value * deployment_mult

    results.append(row)

progress.progress(1.0, text="Scan complete.")
progress.empty()

results_df = pd.DataFrame(results).sort_values("Conviction Score", ascending=False, na_position="last")

st.subheader("🏆 Ranked Conviction Output")

display_df = results_df.copy()
display_df["Structural Weight"] = display_df["Structural Weight"].map(lambda x: f"{x:.1%}")
display_df["Valuation Multiplier"] = display_df["Valuation Multiplier"].map(
    lambda x: f"{x:.2f}x" if pd.notna(x) else "-")
display_df["Expectations Burden"] = display_df["Expectations Burden"].map(
    lambda x: f"{x:.1f}" if pd.notna(x) else "-")
display_df["Quality Score"] = display_df["Quality Score"].map(
    lambda x: f"{x:.1f}" if pd.notna(x) else "-")
display_df["Conviction Score"] = display_df["Conviction Score"].map(
    lambda x: f"{x:.1f}" if pd.notna(x) else "-")
display_df["Suggested $ Deployment"] = display_df["Suggested $ Deployment"].map(
    lambda x: f"{x:,.0f}" if pd.notna(x) else "-")

st.dataframe(display_df, use_container_width=True, hide_index=True)

failed = results_df[results_df["Notes"] != ""]
if not failed.empty:
    with st.expander(f"⚠️ {len(failed)} ticker(s) had data issues"):
        st.dataframe(failed[["Ticker", "Notes"]], use_container_width=True, hide_index=True)

st.caption(
    "Conviction Score equal-weights three independent axes: Valuation richness (is now a good price, "
    "vs. this ticker's own trading history), Expectations burden (how much growth is already priced "
    "in), and Quality (is this a good business at all -- ROIC, margins, leverage, dilution). "
    "Suggested $ Deployment = structural target weight x portfolio value x valuation multiplier "
    "(capped further by high Expectations burden or low Quality) x macro overlay. Data sourced from "
    "Yahoo Finance via yfinance; informational only, not investment advice."
)
