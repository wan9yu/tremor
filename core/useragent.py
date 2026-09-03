"""One User-Agent header, read by every network fetcher.

Fifteen fetcher/core modules used to each carry their own byte-identical
copy of the UA string literal (plus two ad hoc variants); a typo or a rename
in one copy had nothing to catch it drifting from the rest. HEADERS below is
the one place that string lives now — every network caller imports this
module rather than typing the literal again.

fetchers/cnh_cny.py is the one deliberate exception: it reads Yahoo
Finance's v8 chart endpoint, which is well known to reject non-browser
User-Agents (a tier-1 line's only source), so its Mozilla-shaped header is
preserved here byte-for-byte as COMPAT_HEADERS rather than folded into
HEADERS — changing it on a guess would risk silently blocking that source.
tools/reconcile_net_outages.py previously carried its own truncated variant
("tremor/1.0", missing the URL) with no such reason and now reads HEADERS
like everything else.

Stdlib only — nothing here should ever need a third-party import.
"""

HEADERS = {"User-Agent": "tremor/1.0 (+https://github.com/wan9yu/tremor)"}

# fetchers/cnh_cny.py's Yahoo Finance calls ONLY. Do not fold this into
# HEADERS above, and do not point any other caller at it — it exists solely
# because Yahoo's chart endpoint is load-bearing on a browser-shaped UA.
COMPAT_HEADERS = {"User-Agent": "Mozilla/5.0 (tremor; +https://github.com/wan9yu/tremor)"}
