import pandas as pd
import streamlit as st

from hedging_system.pricing import (
    SwapPeriod,
    commodity_forward_price,
    commodity_swap_fixed_rate,
    commodity_swap_mtm,
    commodity_swap_payoff,
)

st.set_page_config(page_title="Commodity Pricing", page_icon="🛢️", layout="wide")
st.title("Wycena instrumentów towarowych")
st.caption("Dane demonstracyjne; cena zakupu fizycznego może różnić się od benchmarku.")

forward_tab, swap_tab = st.tabs(["Forward: koszt przenoszenia", "Swap: fixed-for-floating"])

with forward_tab:
    with st.form("commodity_forward_inputs"):
        columns = st.columns(3)
        with columns[0]:
            spot = st.number_input("Cena spot (USD/bbl)", min_value=0.000001, value=80.0, step=1.0)
            quantity = st.number_input("Ilość (bbl)", min_value=0.01, value=10_000.0, step=1_000.0)
        with columns[1]:
            financing_pct = st.number_input("Stopa finansowania (%)", value=4.0, step=0.25)
            storage_pct = st.number_input("Koszt składowania (%)", value=2.5, step=0.25)
        with columns[2]:
            convenience_yield_pct = st.number_input("Convenience yield (%)", value=1.5, step=0.25)
            maturity = st.number_input("Termin (lata)", min_value=0.0, value=0.5, step=0.25)
        forward_submitted = st.form_submit_button("Oblicz forward", type="primary")

    if forward_submitted:
        try:
            forward = commodity_forward_price(
                spot,
                financing_pct / 100.0,
                storage_pct / 100.0,
                convenience_yield_pct / 100.0,
                maturity,
            )
        except ValueError as error:
            st.error(f"Nieprawidłowe parametry: {error}")
        else:
            result_columns = st.columns(2)
            result_columns[0].metric("Cena forward", f"{forward:,.4f} USD/bbl")
            result_columns[1].metric("Koszt dla podanej ilości", f"{forward * quantity:,.2f} USD")
            st.caption(
                "Model kosztu przenoszenia jest ilustracyjny. Dla wyceny transakcyjnej "
                "preferuj obserwowaną krzywą właściwego benchmarku."
            )

with swap_tab:
    st.markdown(
        "Kontrakt demonstracyjny ma cztery kwartalne okresy; ilość i fixing są "
        "wprowadzane osobno dla każdego okresu."
    )
    with st.form("commodity_swap_inputs"):
        discount_rate_pct = st.number_input(
            "Stopa dyskontowa USD (% rocznie)", value=4.0, step=0.25
        )
        period_columns = st.columns(4)
        forwards = []
        quantities = []
        fixings = []
        for index, period_column in enumerate(period_columns, start=1):
            with period_column:
                st.markdown(f"**Kwartał {index}**")
                forward_price = st.number_input(
                    f"Forward Q{index} (USD/bbl)",
                    min_value=0.000001,
                    value=79.0 + index,
                    step=1.0,
                    key=f"swap_forward_{index}",
                )
                period_quantity = st.number_input(
                    f"Ilość Q{index} (bbl)",
                    min_value=0.01,
                    value=10_000.0,
                    step=1_000.0,
                    key=f"swap_quantity_{index}",
                )
                fixing = st.number_input(
                    f"Fixing Q{index} (USD/bbl)",
                    min_value=0.000001,
                    value=80.0 + index,
                    step=1.0,
                    key=f"swap_fixing_{index}",
                )
                forwards.append(forward_price)
                quantities.append(period_quantity)
                fixings.append(fixing)
        swap_submitted = st.form_submit_button("Wyceń swap i rozliczenia", type="primary")

    if swap_submitted:
        periods = [
            SwapPeriod(
                years=index * 0.25,
                quantity=quantities[index - 1],
                forward_price=forwards[index - 1],
            )
            for index in range(1, 5)
        ]
        try:
            discount_rate = discount_rate_pct / 100.0
            fixed_rate = commodity_swap_fixed_rate(periods, discount_rate)
            initial_mtm = commodity_swap_mtm(periods, fixed_rate, discount_rate)
        except ValueError as error:
            st.error(f"Nieprawidłowe parametry: {error}")
        else:
            kpis = st.columns(2)
            kpis[0].metric("Fair fixed rate", f"{fixed_rate:,.6f} USD/bbl")
            kpis[1].metric("MtM przy zawarciu", f"{initial_mtm:,.6f} USD")
            rows = []
            for index, period in enumerate(periods):
                payoff = commodity_swap_payoff(period.quantity, fixed_rate, fixings[index])
                purchase_cost = period.quantity * fixings[index]
                rows.append(
                    {
                        "Okres": index + 1,
                        "Forward (USD/bbl)": period.forward_price,
                        "Fixing (USD/bbl)": fixings[index],
                        "Ilość (bbl)": period.quantity,
                        "Payoff swapu (USD)": payoff,
                        "Zakup fizyczny (USD)": purchase_cost,
                        "Koszt netto (USD)": purchase_cost - payoff,
                    }
                )
            st.dataframe(
                pd.DataFrame(rows).style.format(
                    {
                        "Forward (USD/bbl)": "{:,.4f}",
                        "Fixing (USD/bbl)": "{:,.4f}",
                        "Ilość (bbl)": "{:,.0f}",
                        "Payoff swapu (USD)": "{:,.2f}",
                        "Zakup fizyczny (USD)": "{:,.2f}",
                        "Koszt netto (USD)": "{:,.2f}",
                    }
                ),
                hide_index=True,
                use_container_width=True,
            )
            st.caption(
                "Dodatni payoff jest wpływem dla płatnika ceny stałej. Pominięto basis, "
                "spready, collateral i opóźnienie między fixingiem a płatnością."
            )
