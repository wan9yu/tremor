"""Shared test helpers."""
import contextlib
import re
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


@contextlib.contextmanager
def stub_attr(obj, name, value):
    """Swap ``obj.name`` for ``value`` for the block, then always restore it.

    One stubbing style for the whole suite: a swap that is not restored leaks
    into whatever test runs next, and the failure surfaces far from its cause.
    """
    real = getattr(obj, name)
    setattr(obj, name, value)
    try:
        yield
    finally:
        setattr(obj, name, real)


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def cron_hours(path):
    """Every ``cron:`` hour declared in a workflow file, in order.

    Deliberately a regex and not a YAML parse: this helper is imported by the
    pre-collect gate, which may only use the stdlib, and a dependency here
    would fail the daily run before a single row is written.

    Captures only the FIRST hour field of each ``cron:`` line — a multi-hour
    field such as ``"0 2,8,14,20 * * *"`` (intraday.yml) yields just its first
    hour, not the full list. That is enough for the single-hour daily cron
    this helper exists to bind; it does not parse comma-separated hour lists.
    """
    return [int(m) for m in re.findall(r'cron:\s*["\']?\s*\d+\s+(\d+)', _read(path))]


def workflow_run_steps(path):
    """The text of every ``run:`` block in a workflow file."""
    text = _read(path)
    steps, buf, indent = [], None, 0
    for line in text.splitlines():
        stripped = line.strip()
        if buf is not None:
            if stripped and (len(line) - len(line.lstrip())) <= indent:
                steps.append("\n".join(buf))
                buf = None
            else:
                buf.append(line)
                continue
        if stripped.startswith("- run:") or stripped.startswith("run:"):
            indent = len(line) - len(line.lstrip())
            buf = [line.split("run:", 1)[1]]
    if buf is not None:
        steps.append("\n".join(buf))
    return steps
