from math import isclose

from hedging_system.demo_data import load_cross_hedge_data


def test_bundled_demo_dataset_has_train_and_test_samples() -> None:
    rows = load_cross_hedge_data()
    assert len(rows) == 16
    assert sum(row["sample"] == "train" for row in rows) == 8
    assert sum(row["sample"] == "test" for row in rows) == 8
    assert all(
        set(row)
        == {
            "observation_id",
            "sample",
            "benchmark_change_usd_per_bbl",
            "physical_change_usd_per_bbl",
        }
        for row in rows
    )


def test_bundled_dataset_produces_expected_hedge_ratio() -> None:
    rows = load_cross_hedge_data()
    train = [row for row in rows if row["sample"] == "train"]
    exposure = [float(row["physical_change_usd_per_bbl"]) for row in train]
    benchmark = [float(row["benchmark_change_usd_per_bbl"]) for row in train]
    count = len(train)
    mean_exposure = sum(exposure) / count
    mean_benchmark = sum(benchmark) / count
    covariance = sum(
        (physical - mean_exposure) * (hedge - mean_benchmark)
        for physical, hedge in zip(exposure, benchmark, strict=True)
    )
    variance = sum((hedge - mean_benchmark) ** 2 for hedge in benchmark)
    assert isclose(covariance / variance, 0.8, rel_tol=1e-12)
