from math import exp

import pandas as pd
import streamlit as st

from hedging_system.pricing import (
    fx_forward_mtm,
    fx_forward_rate,
    garman_kohlhagen,
)

st.set_page_config(page_title="FX Pricing", page_icon="💱", layout="wide")
st.title("Wycena i hedging FX")
st.caption("Kursy i premie podawaj w jednostkach waluty krajowej za jednostkę zagraniczną.")

with st.form("fx_inputs"):
    st.subheader("Parametry rynku i ekspozycji")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        spot = st.number_input("Spot (PLN/EUR)", min_value=0.000001, value=4.30, step=0.01)
        notional = st.number_input(
            "Nominał ekspozycji (EUR)", min_value=0.01, value=1_000_000.0, step=10_000.0
        )
        years = st.number_input("Termin (lata)", min_value=0.0, value=0.5, step=0.25)
    with col2:
        domestic_rate_pct = st.number_input("Stopa PLN (% rocznie)", value=5.50, step=0.25)
        foreign_rate_pct = st.number_input("Stopa EUR (% rocznie)", value=3.00, step=0.25)
        volatility_pct = st.number_input(
            "Zmienność FX (% rocznie)", min_value=0.0, value=12.0, step=0.5
        )
    with col3:
        strike = st.number_input(
            "Strike opcji (PLN/EUR)", min_value=0.000001, value=4.35, step=0.01
        )
        forward_coverage_pct = st.number_input(
            "Pokrycie forwardem (%)", min_value=0.0, max_value=100.0, value=70.0
        )
    with col4:
        contract_rate = st.number_input(
            "Kurs istniejącego forwardu (PLN/EUR)",
            min_value=0.000001,
            value=4.25,
            step=0.01,
        )
        financing_rate_pct = st.number_input("Finansowanie premii PLN (%)", value=5.50, step=0.25)
    st.subheader("Scenariusze kursu w terminie")
    scenario_cols = st.columns(3)
    with scenario_cols[0]:
        scenario_low = st.number_input(
            "Kurs: scenariusz niski", min_value=0.000001, value=3.90, step=0.05
        )
    with scenario_cols[1]:
        scenario_base = st.number_input(
            "Kurs: scenariusz bazowy", min_value=0.000001, value=4.30, step=0.05
        )
    with scenario_cols[2]:
        scenario_high = st.number_input(
            "Kurs: scenariusz wysoki", min_value=0.000001, value=4.80, step=0.05
        )
    submitted = st.form_submit_button("Oblicz wycenę i koszty", type="primary")

if submitted:
    domestic_rate = domestic_rate_pct / 100.0
    foreign_rate = foreign_rate_pct / 100.0
    volatility = volatility_pct / 100.0
    try:
        forward = fx_forward_rate(spot, domestic_rate, foreign_rate, years)
        option = garman_kohlhagen(spot, strike, domestic_rate, foreign_rate, volatility, years)
        premium = option.call * notional
        financed_premium = premium * exp(financing_rate_pct / 100.0 * years)
        contract_mtm_value = fx_forward_mtm(
            notional, spot, domestic_rate, foreign_rate, years, contract_rate
        )
    except ValueError as error:
        st.error(f"Nieprawidłowe parametry: {error}")
    else:
        kpis = st.columns(4)
        kpis[0].metric("Kurs forward", f"{forward:,.6f} PLN/EUR")
        kpis[1].metric("Premia call", f"{premium:,.2f} PLN")
        kpis[2].metric("Delta call", f"{option.call_delta:.4f}")
        kpis[3].metric("MtM istniejącego forwardu", f"{contract_mtm_value:,.2f} PLN")

        st.subheader("Parametry opcji europejskiej")
        greeks = pd.DataFrame(
            [
                {
                    "Call / EUR (PLN)": option.call,
                    "Put / EUR (PLN)": option.put,
                    "Delta call": option.call_delta,
                    "Delta put": option.put_delta,
                    "Gamma": option.gamma,
                    "Vega / 1,00 zmienności": option.vega,
                    "d1": option.d1,
                    "d2": option.d2,
                }
            ]
        )
        st.dataframe(greeks, hide_index=True, use_container_width=True)

        coverage = forward_coverage_pct / 100.0
        scenario_rows = []
        for terminal_spot in (scenario_low, scenario_base, scenario_high):
            scenario_rows.append(
                {
                    "Kurs w terminie (PLN/EUR)": terminal_spot,
                    "Bez zabezpieczenia (PLN)": notional * terminal_spot,
                    "100% forward (PLN)": notional * forward,
                    f"Forward {forward_coverage_pct:.0f}% (PLN)": notional
                    * (coverage * forward + (1.0 - coverage) * terminal_spot),
                    "Call + finansowanie premii (PLN)": notional * min(terminal_spot, strike)
                    + financed_premium,
                }
            )
        st.subheader("Koszt zakupu w terminie")
        st.caption(
            "Porównanie nie obejmuje spreadów, prowizji, podatków ani ryzyka kontrahenta. "
            "Premia opcji jest finansowana stopą podaną w formularzu."
        )
        st.dataframe(
            pd.DataFrame(scenario_rows).style.format(
                {
                    "Kurs w terminie (PLN/EUR)": "{:.4f}",
                    "Bez zabezpieczenia (PLN)": "{:,.2f}",
                    "100% forward (PLN)": "{:,.2f}",
                    f"Forward {forward_coverage_pct:.0f}% (PLN)": "{:,.2f}",
                    "Call + finansowanie premii (PLN)": "{:,.2f}",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )
