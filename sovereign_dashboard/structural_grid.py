"""
Structural Allocation Grid
===========================
This is a straight data encoding of the portfolio grid image you uploaded
(sections -> layers -> permissible assets -> target weights -> accumulation
protocol notes). It is intentionally kept as pure data (no Streamlit, no
network calls) so any page/engine can import TICKER_INFO or SECTIONS
without side effects.

Core portfolio (sums to 100%):
  INFRA 15% + ENERGY & COMMODITY 23% + AI/SEMIS 10% + EM 7%
  + BTC 25% + GOLD 10% + CASH 10%  =  100%

"Satellite" holdings (Human Healthcare, Water & Waste Infra, Rail &
Logistics, Cyber Security, Networking, Energy, Materials, Industrials) are
kept separate since their weights don't roll into the core 100% -- they
read as an optional/diversification watchlist layered on top rather than
part of the fixed core allocation. Edit SATELLITE below if that's wrong.
"""

# ---------------------------------------------------------------------
# CORE SECTIONS (sums to 100% of the portfolio)
# ---------------------------------------------------------------------
SECTIONS = {
    "INFRA": {
        "target_pct": 0.15,
        "layers": {
            "Layer 1: Hard Assets": {
                "weight": 0.40,
                "tickers": ["TPL", "ADPORTS", "ICTEY"],
                "protocol": "Continuous monthly cash-flow deployment. Never pause.",
            },
            "Layer 2: Grid & Utilities": {
                "weight": 0.40,
                "tickers": ["LIN", "ABBN", "SU.PA", "GEV", "ETN", "NVT", "CEG", "PWR", "CWCO"],
                "protocol": "Capital deployed heavily during broad industrial pullbacks.",
            },
            "Layer 3: Tech-Adjacent": {
                "weight": 0.20,
                "tickers": ["VRT", "BE"],
                "protocol": "Accumulation strictly capped. Trim aggressively on euphoria.",
            },
        },
    },
    "ENERGY & COMMODITY": {
        "target_pct": 0.23,
        "layers": {
            "Monetary Royalties": {
                "weight": 0.40,
                "tickers": ["FNV", "WPM"],
                "protocol": "Continuous accumulation. Treat as an extension of physical gold.",
            },
            "Baseload Energy": {
                "weight": 0.40,
                "tickers": ["CCJ", "CNQ", "XOM"],
                "protocol": "Heavy accumulation during localized geopolitical/regulatory dips. "
                            "(XOM = Light weighting only.)",
                "light_only": ["XOM"],
            },
            "Industrial Materials": {
                "weight": 0.20,
                "tickers": ["FCX", "BHP", "NEM", "COP"],
                "protocol": "Strictly cyclical. Accumulate only when deep in Tier 1 pullbacks.",
            },
        },
    },
    "AI/SEMIS": {
        "target_pct": 0.10,
        "layers": {
            "Layer 1: Physical Monopolies": {
                "weight": 0.60,
                "tickers": ["TSM", "ASML", "SHECY", "6920.T"],  # 6920.T = Lasertec
                "protocol": "Core accumulation allocation. Focus heavily on ASML/TSM pullbacks. "
                            "Lasertec: accumulate on broad Japanese index liquidations.",
            },
            "Layer 2: Architecture & Robotics": {
                "weight": 0.30,
                "tickers": ["AVGO", "CDNS", "QCOM", "FANUY", "8035.T", "SNPS"],  # 8035.T = Tokyo Electron
                "protocol": "Tactical accumulation. Prioritize FANUY to diversify out of pure tech. "
                            "Tokyo Electron: trim 10% if systemic tech capex reaches parabolic euphoria "
                            "levels. SNPS: cap tightly; buy strictly on standard -20% valuation resets.",
            },
            "Layer 3: Velocity Applications": {
                "weight": 0.10,
                "tickers": ["NOW", "PANW", "STX"],
                "protocol": "PANW can be used as core. Others capped at minimal weight. "
                            "Zero tolerance for momentum chasing near highs.",
                "core_eligible": ["PANW"],
            },
        },
    },
    "EM": {
        "target_pct": 0.07,
        "layers": {
            "INDIA": {
                "weight": 0.40,
                "tickers": ["ABB.NS", "SIEMENS.NS", "POWERINDIA.NS", "CGPOWER.NS", "PIIND.NS",
                            "SUNPHARMA.NS", "HCLTECH.NS"],
                "protocol": "",
            },
            "GCC": {
                "weight": 0.40,
                "tickers": ["2222.SR", "ADNOCGAS.AB", "2082.SR", "7010.SR"],  # Aramco (Tadawul),
                                                                               # ADNOC Gas -- trades on the
                                                                               # Abu Dhabi exchange (ADX), NOT
                                                                               # Tadawul, so it is NOT a ".SR"
                                                                               # symbol. This was previously
                                                                               # a duplicate of ACWA Power's
                                                                               # 2082.SR by mistake -- that
                                                                               # was almost certainly your
                                                                               # error source. ACWA Power
                                                                               # (Tadawul), STC (Tadawul).
                "protocol": "",
            },
            "Other Jurisdiction": {
                "weight": 0.20,
                "tickers": ["HIJP.L", "TLK", "EIDO", "VALE", "0883.HK", "CSUAY", "0941.HK", "ISDE.L"],
                # HIJP.L = HSBC MSCI Japan Islamic Screened UCITS ETF -- LSE-listed, needs the ".L"
                #          suffix for Yahoo Finance/yfinance to resolve it (bare "HIJP" will not work)
                # TLK = Telkom Indonesia ADR (NYSE)
                # EIDO = iShares MSCI Indonesia ETF -- US-listed (NYSE Arca), no suffix needed
                # VALE = Vale S.A. ADR (NYSE)
                # 0883.HK = CNOOC Ltd (grid said "CEO"). CEO was CNOOC's NYSE ADR ticker, but the NYSE
                #           delisted it in March 2021 under Executive Order 13959 (barred US investment
                #           in companies with alleged Chinese military ties) -- "CEO" has not traded
                #           anywhere since and will always fail in yfinance. CNOOC's shares continue
                #           trading on the Hong Kong Stock Exchange under code 00883 (Yahoo: 0883.HK).
                # CSUAY = China Shenhua Energy ADR (OTC) -- unaffected by the 2021 delistings, still valid
                # 0941.HK = China Mobile Ltd (grid said "CHL"). Same story as CNOOC: CHL was China
                #           Mobile's NYSE ADR, delisted January 2021 under the same executive order.
                #           Trades on HKEX under code 0941 (Yahoo: 0941.HK).
                # ISDE.L = iShares MSCI EM Islamic UCITS ETF -- LSE-listed, needs the ".L" suffix.
                #          NOTE: yfinance's coverage of LSE-listed ETFs is inconsistent (pricing/history
                #          gaps are more common than for US-listed tickers) -- if this one still errors,
                #          that's a yfinance data-gap issue for this specific LSE listing, not a
                #          wrong-symbol issue.
                "protocol": "",
            },
        },
    },
    "BTC": {"target_pct": 0.25, "tickers": ["BTC"], "protocol": "Cold wallet."},
    "GOLD": {"target_pct": 0.10, "tickers": ["GOLD"], "protocol": "Physical."},
    "CASH": {"target_pct": 0.10, "tickers": ["CASH"], "protocol": "Tactical parking / dry powder."},
}

# ---------------------------------------------------------------------
# SATELLITE / WATCHLIST holdings -- weights don't roll into the 100%
# core above. Treated as an optional diversification overlay.
# ---------------------------------------------------------------------
SATELLITE = {
    "Human Healthcare": {"target_pct": 0.05, "tickers": ["NVO", "AZN", "ISRG", "TMO"],
                          "protocol": "NVO can be added in core -- 2.5%."},
    "Water & Waste Infra": {"target_pct": 0.04, "tickers": ["XYL", "ECL", "WM", "RSG"],
                             "protocol": "XYL & WM/RSG as core -- 2%."},
    "Rail & Logistics": {"target_pct": 0.03, "tickers": ["CNI", "CP", "UNP"],
                          "protocol": "CNI/CP as core -- 2%."},
    "Cyber Security": {"target_pct": 0.03, "tickers": ["FTNT", "CHKP", "CRWD", "ZS"],
                        "protocol": "PANW can be added as core in this sector."},
    "Networking": {"target_pct": 0.02, "tickers": ["ANET"], "protocol": ""},
    "Energy (satellite)": {"target_pct": None, "tickers": ["SU", "EQT", "CVX"], "protocol": ""},
    "Materials (satellite)": {"target_pct": None, "tickers": ["SCCO", "NUE"], "protocol": ""},
    "Industrials (satellite)": {"target_pct": None, "tickers": ["PH", "CAT"], "protocol": ""},
}


def flatten_universe() -> list[dict]:
    """
    Flattens the whole grid (core + satellite) into one row-per-ticker list:
    [{"ticker", "section", "layer", "layer_weight", "section_target_pct",
      "effective_weight", "protocol", "group"}]

    effective_weight = section_target_pct * layer_weight -- i.e. this
    ticker's slice of the *whole portfolio*, before you decide how many
    tickers within a layer actually get funded. Layers with N permissible
    tickers do NOT automatically split evenly across them; effective_weight
    is the layer's ceiling, not a per-ticker entitlement. Use it as an
    upper bound when ranking within a layer.
    """
    rows = []

    for section_name, section in SECTIONS.items():
        target_pct = section.get("target_pct")
        if "layers" in section:
            for layer_name, layer in section["layers"].items():
                for ticker in layer["tickers"]:
                    rows.append({
                        "ticker": ticker,
                        "section": section_name,
                        "layer": layer_name,
                        "layer_weight": layer["weight"],
                        "section_target_pct": target_pct,
                        "effective_weight": (target_pct or 0) * layer["weight"],
                        "protocol": layer.get("protocol", ""),
                        "group": "core",
                    })
        else:
            for ticker in section["tickers"]:
                rows.append({
                    "ticker": ticker,
                    "section": section_name,
                    "layer": section_name,
                    "layer_weight": 1.0,
                    "section_target_pct": target_pct,
                    "effective_weight": target_pct or 0,
                    "protocol": section.get("protocol", ""),
                    "group": "core",
                })

    for section_name, section in SATELLITE.items():
        target_pct = section.get("target_pct")
        for ticker in section["tickers"]:
            rows.append({
                "ticker": ticker,
                "section": section_name,
                "layer": section_name,
                "layer_weight": 1.0,
                "section_target_pct": target_pct,
                "effective_weight": target_pct or 0,
                "protocol": section.get("protocol", ""),
                "group": "satellite",
            })

    return rows


# Tickers that are non-equity (skip in engines that need P/S / revenue data)
NON_EQUITY_TICKERS = {"BTC", "GOLD", "CASH"}

# Tickers explicitly marked "core eligible" / floor-protected across the grid,
# used to set is_core=True automatically when running the Valuation Engine.
CORE_ELIGIBLE_TICKERS = {
    "TPL", "ADPORTS", "ICTEY", "FNV", "WPM", "TSM", "ASML", "PANW",
    "NVO", "XYL", "WM", "RSG", "CNI", "CP",
}
