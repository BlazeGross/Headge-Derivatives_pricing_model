import pandas as pd
import streamlit as st

from hedging_system.demo_data import load_cross_hedge_data
from hedging_system.pricing import hedge_metrics

st.set_page_config(page_title="Cross Hedge", page_icon="📉", layout="wide")
st.title("Dobór hedge ratio i skuteczność cross-hedge")
st.caption(
    "Zbiór demonstracyjny jest syntetyczny. Parametr estymujemy wyłącznie na "
    "próbie train, a następnie zamrażamy przy ocenie test."
)

try:
    observations = load_cross_hedge_data()
except (FileNotFoundError, ValueError) as error:
    st.error(f"Nie można wczytać zbioru demonstracyjnego: {error}")
else:
    training_rows = [row for row in observations if row["sample"] == "train"]
    test_rows = [row for row in observations if row["sample"] == "test"]
    train_exposure = [float(row["physical_change_usd_per_bbl"]) for row in training_rows]
    train_hedge = [float(row["benchmark_change_usd_per_bbl"]) for row in training_rows]
    test_exposure = [float(row["physical_change_usd_per_bbl"]) for row in test_rows]
    test_hedge = [float(row["benchmark_change_usd_per_bbl"]) for row in test_rows]
    try:
        training_metrics = hedge_metrics(train_exposure, train_hedge, 0.0)
        test_metrics = hedge_metrics(test_exposure, test_hedge, training_metrics.hedge_ratio)
        training_metrics = hedge_metrics(train_exposure, train_hedge, training_metrics.hedge_ratio)
    except ValueError as error:
        st.error(f"Nie można oszacować hedge ratio: {error}")
    else:
        metrics_columns = st.columns(4)
        metrics_columns[0].metric("Hedge ratio OLS (train)", f"{training_metrics.hedge_ratio:.4f}")
        metrics_columns[1].metric("Korelacja (train)", f"{training_metrics.correlation:.4f}")
        metrics_columns[2].metric("HE in-sample", f"{training_metrics.effectiveness:.2%}")
        metrics_columns[3].metric("HE out-of-sample", f"{test_metrics.effectiveness:.2%}")

        st.subheader("Wariancja zmian kosztu")
        variance_table = pd.DataFrame(
            [
                {
                    "Próba": "Train",
                    "Obserwacje": training_metrics.observations,
                    "Wariancja bez hedge": training_metrics.unhedged_variance,
                    "Wariancja po hedge": training_metrics.hedged_variance,
                    "Redukcja wariancji": training_metrics.effectiveness,
                },
                {
                    "Próba": "Test",
                    "Obserwacje": test_metrics.observations,
                    "Wariancja bez hedge": test_metrics.unhedged_variance,
                    "Wariancja po hedge": test_metrics.hedged_variance,
                    "Redukcja wariancji": test_metrics.effectiveness,
                },
            ]
        )
        st.dataframe(
            variance_table.style.format(
                {
                    "Wariancja bez hedge": "{:.6f}",
                    "Wariancja po hedge": "{:.6f}",
                    "Redukcja wariancji": "{:.2%}",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )

        st.subheader("Obserwacje i zmiany kosztu rezydualnego")
        display_rows = []
        for row in observations:
            residual = float(row["physical_change_usd_per_bbl"]) - (
                training_metrics.hedge_ratio * float(row["benchmark_change_usd_per_bbl"])
            )
            display_rows.append(
                {
                    "Próba": row["sample"],
                    "Obserwacja": row["observation_id"],
                    "Benchmark (USD/bbl)": row["benchmark_change_usd_per_bbl"],
                    "Cena fizyczna (USD/bbl)": row["physical_change_usd_per_bbl"],
                    "Zmiana kosztu po hedge (USD/bbl)": residual,
                }
            )
        display_data = pd.DataFrame(display_rows)
        st.line_chart(
            display_data.pivot(
                index="Obserwacja",
                columns="Próba",
                values="Zmiana kosztu po hedge (USD/bbl)",
            )
        )
        st.dataframe(display_data, hide_index=True, use_container_width=True)
        st.warning(
            "Próba jest mała i syntetyczna. Wynik nie jest backtestem rynkowym, "
            "prognozą ani dowodem skuteczności przyszłego zabezpieczenia."
        )
