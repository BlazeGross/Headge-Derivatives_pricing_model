import streamlit as st

st.set_page_config(
    page_title="Hedging & Derivatives Pricing",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Hedging & Derivatives Pricing")
st.caption("Analityczny prototyp wyceny instrumentów FX i towarowych")

st.info(
    "Wyniki korzystają z parametrów wprowadzonych przez użytkownika lub z jawnych "
    "danych syntetycznych. Aplikacja nie pobiera notowań rynkowych i nie generuje "
    "rekomendacji transakcyjnych."
)

st.subheader("Zakres analityczny")
left, right = st.columns(2)
with left:
    st.markdown(
        """
        **FX**
        - Forward i jego wartość rynkowa (MtM)
        - Europejskie opcje call/put: Garman–Kohlhagen
        - Scenariusze kosztu importera z finansowaniem premii
        """
    )
with right:
    st.markdown(
        """
        **Towary i ryzyko**
        - Forward metodą kosztu przenoszenia
        - Fixed-for-floating swap: fair rate, MtM i rozliczenia
        - Minimalnowariancyjne hedge ratio i skuteczność poza próbą
        """
    )

st.subheader("Szybki start")
st.markdown(
    """
    1. Otwórz **FX Pricing**, aby wycenić forward i opcję.
    2. Otwórz **Commodity Pricing**, aby przeanalizować forward i swap.
    3. Otwórz **Cross Hedge**, aby oszacować hedge ratio na zbiorze demonstracyjnym.
    """
)

with st.expander("Założenia i ograniczenia"):
    st.markdown(
        """
        Modele są ilustracyjne: zakładają stałe stopy, zgodne jednostki, idealne
        dopasowanie instrumentu i brak spreadów, opłat, collateral oraz ryzyka
        kontrahenta. Model Garmana–Kohlhagena dotyczy opcji europejskiej. Wartości
        nie są ofertą rynkową ani wyceną księgową. Przed użyciem decyzyjnym wymagane
        są walidowane dane rynkowe, konwencje kontraktowe i niezależny przegląd modelu.
        """
    )
