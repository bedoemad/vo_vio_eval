"""Shared filtering rules for final thesis benchmark outputs.

Dummy/example adapters are useful for smoke tests, but they should not appear
in final benchmark tables, plots, or thesis results.
"""

EXCLUDED_BENCHMARK_METHODS = {
    "dummy_vo",
    "noisy_dummy_vo",
    "example_adapter",
}


def keep_real_benchmark_methods(df, method_col="method"):
    """Return a copy of df excluding smoke-test/demo methods."""
    if method_col not in df.columns:
        return df.copy()
    return df[~df[method_col].astype(str).isin(EXCLUDED_BENCHMARK_METHODS)].copy()
