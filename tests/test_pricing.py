from math import exp, isclose

import pytest

from hedging_system.pricing import (
    SwapPeriod,
    commodity_forward_price,
    commodity_swap_fixed_rate,
    commodity_swap_mtm,
    commodity_swap_payoff,
    fx_forward_mtm,
    fx_forward_rate,
    garman_kohlhagen,
    hedge_metrics,
)


def test_fx_forward_rate_and_inception_mtm() -> None:
    forward = fx_forward_rate(4.30, 0.055, 0.03, 0.5)
    assert isclose(forward, 4.3540873416247275, rel_tol=1e-12)
    assert abs(fx_forward_mtm(1_000_000, 4.30, 0.055, 0.03, 0.5, forward)) < 1e-8


def test_fx_forward_mtm_changes_sign_for_short_position() -> None:
    long_value = fx_forward_mtm(1_000_000, 4.50, 0.055, 0.03, 0.25, 4.3540873416)
    short_value = fx_forward_mtm(
        1_000_000,
        4.50,
        0.055,
        0.03,
        0.25,
        4.3540873416,
        position="short",
    )
    assert long_value > 0
    assert isclose(long_value, -short_value, rel_tol=1e-12)


def test_garman_kohlhagen_values_and_put_call_parity() -> None:
    option = garman_kohlhagen(4.30, 4.35, 0.055, 0.03, 0.12, 0.5)
    assert isclose(option.call, 0.14528050894468825, rel_tol=1e-11)
    assert isclose(option.put, 0.14130403775904332, rel_tol=1e-11)
    parity = 4.30 * exp(-0.03 * 0.5) - 4.35 * exp(-0.055 * 0.5)
    assert isclose(option.call - option.put, parity, abs_tol=1e-12)


def test_garman_kohlhagen_expiry_and_zero_volatility_boundaries() -> None:
    expired = garman_kohlhagen(4.50, 4.35, 0.055, 0.03, 0.12, 0.0)
    assert expired.call == pytest.approx(0.15)
    assert expired.put == 0
    assert expired.d1 is None

    deterministic = garman_kohlhagen(4.30, 4.00, 0.055, 0.03, 0.0, 0.5)
    forward = fx_forward_rate(4.30, 0.055, 0.03, 0.5)
    expected_call = exp(-0.055 * 0.5) * (forward - 4.00)
    assert deterministic.call == pytest.approx(expected_call)
    assert deterministic.put == 0


def test_garman_kohlhagen_rejects_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="spot"):
        garman_kohlhagen(0, 4.35, 0.055, 0.03, 0.12, 0.5)
    with pytest.raises(ValueError, match="volatility"):
        garman_kohlhagen(4.30, 4.35, 0.055, 0.03, -0.12, 0.5)


def test_commodity_forward_example() -> None:
    price = commodity_forward_price(80, 0.04, 0.025, 0.015, 0.5)
    assert isclose(price, 82.02520964195386, rel_tol=1e-12)


def test_commodity_swap_fair_rate_and_payoff() -> None:
    periods = [
        SwapPeriod(years=index * 0.25, quantity=10_000, forward_price=80 + index)
        for index in range(1, 5)
    ]
    fixed_rate = commodity_swap_fixed_rate(periods, 0.04)
    assert isclose(fixed_rate, 82.48750035415313, rel_tol=1e-12)
    assert abs(commodity_swap_mtm(periods, fixed_rate, 0.04)) < 1e-7
    assert commodity_swap_payoff(10_000, fixed_rate, 95) > 0
    assert commodity_swap_payoff(10_000, fixed_rate, 95, position="receive_fixed") < 0


def test_commodity_swap_mtm_changes_sign_for_fixed_receiver() -> None:
    periods = [SwapPeriod(years=0.5, quantity=100, forward_price=90)]
    payer_value = commodity_swap_mtm(periods, 80, 0.04)
    receiver_value = commodity_swap_mtm(periods, 80, 0.04, position="receive_fixed")
    assert payer_value > 0
    assert receiver_value == pytest.approx(-payer_value)


def test_cross_hedge_ratio_and_out_of_sample_effectiveness() -> None:
    train_x = [-4, -3, -2, -1, 1, 2, 3, 4]
    train_y = [-2.8, -2.8, -2.0, -0.4, 1.2, 1.2, 2.0, 3.6]
    training = hedge_metrics(train_y, train_x, 0.0)
    assert training.hedge_ratio == pytest.approx(0.8)
    training_evaluation = hedge_metrics(train_y, train_x, training.hedge_ratio)
    assert training_evaluation.effectiveness == pytest.approx(0.967741935483871)

    test_x = [-6, -3, -1, 2, 4, -2, 1, 5]
    test_y = [-3.0, -2.7, -0.1, 0.2, 3.4, -2.0, 1.9, 2.3]
    testing = hedge_metrics(test_y, test_x, training.hedge_ratio)
    assert testing.effectiveness == pytest.approx(0.752941176470588)


def test_hedge_metrics_rejects_invalid_series() -> None:
    with pytest.raises(ValueError, match="same length"):
        hedge_metrics([1, 2, 3], [1, 2], 1.0)
    with pytest.raises(ValueError, match="positive sample variance"):
        hedge_metrics([1, 2, 3], [4, 4, 4], 1.0)
