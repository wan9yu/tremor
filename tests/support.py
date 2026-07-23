"""Shared test helpers."""
import contextlib
import types


@contextlib.contextmanager
def stub_requests(module, get):
    """Swap ``module.requests`` for a stub whose ``get`` is ``get`` for the block.

    Fetchers call ``requests.get`` directly; this replaces it with a callable
    returning a fake response and always restores the real module, so a stub can
    never leak into a later test.
    """
    real = module.requests
    module.requests = types.SimpleNamespace(get=get, RequestException=Exception)
    try:
        yield
    finally:
        module.requests = real
