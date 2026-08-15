import numpy as np

from app.services.usage_forecaster import TransformerLiteForecaster


def test_forecaster_requires_sufficient_history():
    model = TransformerLiteForecaster(window_size=12, horizon_steps=6)
    short_series = np.zeros(10)
    try:
        model.fit(short_series)
        assert False, "expected ValueError for too-short series"
    except ValueError:
        pass


def test_forecaster_output_shape_and_range():
    rng = np.random.default_rng(0)
    series = np.clip(0.5 + 0.3 * np.sin(np.arange(100) / 5) + rng.normal(0, 0.05, 100), 0, 1)

    model = TransformerLiteForecaster(window_size=12, horizon_steps=6).fit(series[:80])
    forecast = model.predict(series[68:80])

    assert forecast.shape == (6,)
    assert np.all(forecast >= 0) and np.all(forecast <= 1)


def test_attention_weights_sum_to_one():
    rng = np.random.default_rng(1)
    series = rng.uniform(0, 1, 60)
    model = TransformerLiteForecaster(window_size=10, horizon_steps=4).fit(series)
    weights = model.attention_weights(series[-10:])
    assert abs(weights.sum() - 1.0) < 1e-6
