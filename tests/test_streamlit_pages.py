from pathlib import Path

from streamlit.testing.v1 import AppTest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_home_page_runs_without_streamlit_exceptions() -> None:
    app = AppTest.from_file(str(PROJECT_ROOT / "app.py")).run(timeout=30)
    assert not app.exception


def test_analytics_pages_run_without_streamlit_exceptions() -> None:
    page_paths = sorted((PROJECT_ROOT / "pages").glob("*.py"))
    assert len(page_paths) == 3
    for page_path in page_paths:
        app = AppTest.from_file(str(page_path)).run(timeout=30)
        assert not app.exception, page_path.name


def test_fx_form_calculates_values_without_streamlit_exceptions() -> None:
    page_path = PROJECT_ROOT / "pages" / "1_FX_Pricing.py"
    app = AppTest.from_file(str(page_path)).run(timeout=30)
    app.button[0].click().run(timeout=30)
    assert not app.exception
    assert any("MtM istniejącego forwardu" in metric.label for metric in app.metric)


def test_commodity_forms_calculate_without_streamlit_exceptions() -> None:
    page_path = PROJECT_ROOT / "pages" / "2_Commodity_Pricing.py"
    app = AppTest.from_file(str(page_path)).run(timeout=30)
    app.button[0].click().run(timeout=30)
    assert not app.exception

    app = AppTest.from_file(str(page_path)).run(timeout=30)
    app.button[1].click().run(timeout=30)
    assert not app.exception
    assert any("Fair fixed rate" in metric.label for metric in app.metric)
