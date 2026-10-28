"""Pure-Python pricing and hedge analytics with explicit input validation."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import erf, exp, isfinite, log, pi, sqrt


def _finite(name: str, value: float) -> float:
    value = float(value)
    if not isfinite(value):
        raise ValueError(f"{name} must be a finite number.")
    return value


def _positive(name: str, value: float) -> float:
    value = _finite(name, value)
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero.")
    return value


def _non_negative(name: str, value: float) -> float:
    value = _finite(name, value)
    if value < 0:
        raise ValueError(f"{name} cannot be negative.")
    return value


def _year_fraction(name: str, value: float) -> float:
    value = _finite(name, value)
    if value < 0:
        raise ValueError(f"{name} cannot be negative.")
    return value


def normal_cdf(value: float) -> float:
    """Cumulative distribution function of the standard normal distribution."""
    value = _finite("value", value)
    return 0.5 * (1.0 + erf(value / sqrt(2.0)))


def normal_pdf(value: float) -> float:
    """Probability density function of the standard normal distribution."""
    value = _finite("value", value)
    return exp(-0.5 * value * value) / sqrt(2.0 * pi)


def fx_forward_rate(
    spot: float,
    domestic_rate: float,
    foreign_rate: float,
    years: float,
) -> float:
    """Covered-interest-parity forward, quoted domestic currency per foreign unit."""
    spot = _positive("spot", spot)
    domestic_rate = _finite("domestic_rate", domestic_rate)
    foreign_rate = _finite("foreign_rate", foreign_rate)
    years = _year_fraction("years", years)
    return spot * exp((domestic_rate - foreign_rate) * years)


def fx_forward_mtm(
    notional: float,
    spot: float,
    domestic_rate: float,
    foreign_rate: float,
    remaining_years: float,
    contract_rate: float,
    *,
    position: str = "long",
) -> float:
    """Present value of an FX forward from the buyer's domestic-currency view."""
    notional = _positive("notional", notional)
    contract_rate = _positive("contract_rate", contract_rate)
    if position not in {"long", "short"}:
        raise ValueError("position must be 'long' or 'short'.")
    forward = fx_forward_rate(spot, domestic_rate, foreign_rate, remaining_years)
    value = notional * exp(-domestic_rate * remaining_years) * (forward - contract_rate)
    return value if position == "long" else -value


@dataclass(frozen=True)
class FXOptionValue:
    """European FX option value and spot Greeks, per unit of foreign notional."""

    call: float
    put: float
    call_delta: float
    put_delta: float
    gamma: float
    vega: float
    d1: float | None
    d2: float | None


def garman_kohlhagen(
    spot: float,
    strike: float,
    domestic_rate: float,
    foreign_rate: float,
    volatility: float,
    years: float,
) -> FXOptionValue:
    """Price European FX call/put options and spot Greeks per foreign-currency unit."""
    spot = _positive("spot", spot)
    strike = _positive("strike", strike)
    domestic_rate = _finite("domestic_rate", domestic_rate)
    foreign_rate = _finite("foreign_rate", foreign_rate)
    volatility = _non_negative("volatility", volatility)
    years = _year_fraction("years", years)

    if years == 0:
        call_delta = 1.0 if spot > strike else 0.0 if spot < strike else 0.5
        put_delta = call_delta - 1.0
        return FXOptionValue(
            call=max(spot - strike, 0.0),
            put=max(strike - spot, 0.0),
            call_delta=call_delta,
            put_delta=put_delta,
            gamma=0.0,
            vega=0.0,
            d1=None,
            d2=None,
        )

    domestic_discount = exp(-domestic_rate * years)
    foreign_discount = exp(-foreign_rate * years)
    forward = spot * foreign_discount / domestic_discount
    discounted_forward_intrinsic = domestic_discount * (forward - strike)

    if volatility == 0:
        call_delta = (
            foreign_discount
            if forward > strike
            else 0.0
            if forward < strike
            else 0.5 * foreign_discount
        )
        put_delta = call_delta - foreign_discount
        return FXOptionValue(
            call=max(discounted_forward_intrinsic, 0.0),
            put=max(-discounted_forward_intrinsic, 0.0),
            call_delta=call_delta,
            put_delta=put_delta,
            gamma=0.0,
            vega=0.0,
            d1=None,
            d2=None,
        )

    root_time = sqrt(years)
    d1 = (log(spot / strike) + (domestic_rate - foreign_rate + 0.5 * volatility**2) * years) / (
        volatility * root_time
    )
    d2 = d1 - volatility * root_time
    call = spot * foreign_discount * normal_cdf(d1) - strike * domestic_discount * normal_cdf(d2)
    put = strike * domestic_discount * normal_cdf(-d2) - spot * foreign_discount * normal_cdf(-d1)
    density = normal_pdf(d1)
    return FXOptionValue(
        call=call,
        put=put,
        call_delta=foreign_discount * normal_cdf(d1),
        put_delta=foreign_discount * (normal_cdf(d1) - 1.0),
        gamma=foreign_discount * density / (spot * volatility * root_time),
        vega=spot * foreign_discount * density * root_time,
        d1=d1,
        d2=d2,
    )


def commodity_forward_price(
    spot: float,
    financing_rate: float,
    storage_rate: float,
    convenience_yield: float,
    years: float,
) -> float:
    """Cost-of-carry forward for a storable commodity."""
    spot = _positive("spot", spot)
    financing_rate = _finite("financing_rate", financing_rate)
    storage_rate = _finite("storage_rate", storage_rate)
    convenience_yield = _finite("convenience_yield", convenience_yield)
    years = _year_fraction("years", years)
    return spot * exp((financing_rate + storage_rate - convenience_yield) * years)


@dataclass(frozen=True)
class SwapPeriod:
    """One fixed-for-floating commodity swap payment period."""

    years: float
    quantity: float
    forward_price: float

    def __post_init__(self) -> None:
        _positive("period years", self.years)
        _positive("period quantity", self.quantity)
        _positive("period forward_price", self.forward_price)


def commodity_swap_fixed_rate(
    periods: Sequence[SwapPeriod],
    discount_rate: float,
) -> float:
    """Fair fixed rate of a commodity swap, weighted by discounted quantities."""
    if not periods:
        raise ValueError("At least one swap period is required.")
    discount_rate = _finite("discount_rate", discount_rate)
    discounted_quantity = sum(
        period.quantity * exp(-discount_rate * period.years) for period in periods
    )
    discounted_float = sum(
        period.quantity * exp(-discount_rate * period.years) * period.forward_price
        for period in periods
    )
    return discounted_float / discounted_quantity


def commodity_swap_mtm(
    periods: Sequence[SwapPeriod],
    fixed_rate: float,
    discount_rate: float,
    *,
    position: str = "pay_fixed",
) -> float:
    """Present value of a commodity swap for the fixed payer or receiver."""
    if not periods:
        raise ValueError("At least one swap period is required.")
    fixed_rate = _positive("fixed_rate", fixed_rate)
    discount_rate = _finite("discount_rate", discount_rate)
    if position not in {"pay_fixed", "receive_fixed"}:
        raise ValueError("position must be 'pay_fixed' or 'receive_fixed'.")
    value = sum(
        period.quantity * exp(-discount_rate * period.years) * (period.forward_price - fixed_rate)
        for period in periods
    )
    return value if position == "pay_fixed" else -value


def commodity_swap_payoff(
    quantity: float,
    fixed_rate: float,
    fixing: float,
    *,
    position: str = "pay_fixed",
) -> float:
    """Cash settlement for a period; positive is a receipt for the fixed payer."""
    quantity = _positive("quantity", quantity)
    fixed_rate = _positive("fixed_rate", fixed_rate)
    fixing = _positive("fixing", fixing)
    if position not in {"pay_fixed", "receive_fixed"}:
        raise ValueError("position must be 'pay_fixed' or 'receive_fixed'.")
    payoff = quantity * (fixing - fixed_rate)
    return payoff if position == "pay_fixed" else -payoff


@dataclass(frozen=True)
class HedgeMetrics:
    """OLS hedge ratio and sample-variance hedge effectiveness."""

    observations: int
    intercept: float
    hedge_ratio: float
    correlation: float
    unhedged_variance: float
    hedged_variance: float
    effectiveness: float


def hedge_metrics(
    exposure_changes: Sequence[float],
    hedge_changes: Sequence[float],
    hedge_ratio: float,
) -> HedgeMetrics:
    """Calculate minimum-variance OLS ratio and effectiveness for a fixed hedge."""
    if len(exposure_changes) != len(hedge_changes):
        raise ValueError("Exposure and hedge series must have the same length.")
    if len(exposure_changes) < 3:
        raise ValueError("At least three paired observations are required.")
    hedge_ratio = _finite("hedge_ratio", hedge_ratio)
    exposure = [_finite("exposure change", value) for value in exposure_changes]
    hedge = [_finite("hedge change", value) for value in hedge_changes]
    count = len(exposure)
    mean_exposure = sum(exposure) / count
    mean_hedge = sum(hedge) / count
    centered_exposure = [value - mean_exposure for value in exposure]
    centered_hedge = [value - mean_hedge for value in hedge]
    variance_exposure = sum(value**2 for value in centered_exposure) / (count - 1)
    variance_hedge = sum(value**2 for value in centered_hedge) / (count - 1)
    if variance_exposure <= 0 or variance_hedge <= 0:
        raise ValueError("Both series must have positive sample variance.")
    covariance = sum(
        exposure_delta * hedge_delta
        for exposure_delta, hedge_delta in zip(centered_exposure, centered_hedge, strict=True)
    ) / (count - 1)
    ratio = covariance / variance_hedge
    correlation = covariance / sqrt(variance_exposure * variance_hedge)
    residuals = [
        exposure_delta - hedge_ratio * hedge_delta
        for exposure_delta, hedge_delta in zip(exposure, hedge, strict=True)
    ]
    mean_residual = sum(residuals) / count
    hedged_variance = sum((value - mean_residual) ** 2 for value in residuals) / (count - 1)
    effectiveness = 1.0 - hedged_variance / variance_exposure
    return HedgeMetrics(
        observations=count,
        intercept=mean_exposure - ratio * mean_hedge,
        hedge_ratio=ratio,
        correlation=correlation,
        unhedged_variance=variance_exposure,
        hedged_variance=hedged_variance,
        effectiveness=effectiveness,
    )
