"""US Treasury cash buffer, in days of outflows — fiscal-plumbing watchlist (tier 2).

Guarded equilibrium: the Treasury holds an operating cash balance at the Fed and
defends it deliberately, having announced a policy of keeping roughly a week of
outflows on hand. That target is not asserted here, it is VISIBLE: the median of
this line over its whole served history is 5.3 business days. The leaking hand:
when the buffer falls anyway, Treasury has lost the ability to refill it — a debt
limit binding, an auction failing, a funding market that will not take the paper.
In June 2023 this reading touched 0.21 days.

Reading: closing TGA balance divided by the trailing 20-business-day mean daily
withdrawal — how many days of its own outflows the Treasury could cover if the
money stopped coming in. A FALL is the alarming direction.

WHY A RATIO AND NOT THE BALANCE. The balance itself is unscoreable and the
radar said so before this line was built: routine single-day swings run to
$121bn, the level regime shifted by trillions across the post-2020 era, and tax
dates impose a calendar rhythm this repo has no machinery to remove. Dividing by
the burn rate normalizes all three at once — and it is not a statistical
convenience, it is the quantity the guard is actually about. A buffer is only
large or small relative to what is being spent. When outflows spike, the buffer
IS shorter, and the reading falls without the balance moving at all, which is
correct.

Source: Treasury Fiscal Data API, Daily Treasury Statement, operating cash
balance table. Keyless, business-daily, published T+1.

THE FIELD TRAP, recorded because a fetcher written from the field names alone
ships broken: in the modern schema ``close_today_bal`` is the literal STRING
"null" on every row, and the value lives in ``open_today_bal``. Verified against
live responses.
"""
import datetime
import statistics

import requests

LINE = "tga_days_cash"
LABEL = "US Treasury cash buffer (days of outflows)"
UNIT = "days"
ANOMALY_DIRECTION = "down"  # running out of days is the alarming move
TIER = 2

_URL = ("https://api.fiscaldata.treasury.gov/services/api/fiscal_service"
        "/v1/accounting/dts/operating_cash_balance")
_HEADERS = {"User-Agent": "tremor/1.0 (+https://github.com/wan9yu/tremor)"}

_CLOSING = "Treasury General Account (TGA) Closing Balance"
_WITHDRAWALS = "Total TGA Withdrawals (Table II) (-)"
_BURN_DAYS = 20     # trailing business days the burn rate is averaged over
_MIN_BURN_DAYS = 15  # ...below which the denominator is too thin to divide by
_LOOKBACK_DAYS = 60  # calendar days requested, comfortably covering _BURN_DAYS


def _value(row):
    """The row's number, from whichever field the schema is putting it in today."""
    raw = row.get("close_today_bal")
    if raw in (None, "null", "", "*"):
        raw = row.get("open_today_bal")
    if raw in (None, "null", "", "*"):
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def fetch_daily():
    since = (datetime.date.today()
             - datetime.timedelta(days=_LOOKBACK_DAYS)).isoformat()
    try:
        r = requests.get(
            _URL,
            params={"filter": f"record_date:gte:{since}",
                    "sort": "-record_date",
                    "fields": "record_date,account_type,close_today_bal,open_today_bal",
                    "page[size]": 400},
            headers=_HEADERS,
            timeout=25,
        )
    except requests.RequestException as e:
        return {"raw_value": None,
                "source_note": f"Treasury Fiscal Data request failed: {type(e).__name__}"}
    if r.status_code != 200:
        return {"raw_value": None,
                "source_note": f"Treasury Fiscal Data HTTP {r.status_code}"}
    try:
        rows = r.json().get("data") or []
    except ValueError:
        return {"raw_value": None,
                "source_note": "Treasury Fiscal Data returned a non-JSON body"}

    closing, withdrawn = {}, {}
    for row in rows:
        value = _value(row)
        if value is None:
            continue
        if row.get("account_type") == _CLOSING:
            closing[row["record_date"]] = value
        elif row.get("account_type") == _WITHDRAWALS:
            withdrawn[row["record_date"]] = value
    if not closing:
        return {"raw_value": None,
                "source_note": "Treasury Fiscal Data served no TGA closing balance"}

    obs = max(closing)
    # The burn rate is measured over the business days up to and including the
    # observation, so numerator and denominator describe the same moment — the
    # leg-alignment rule this project learned from sofr_iorb.
    days = sorted(d for d in withdrawn if d <= obs)[-_BURN_DAYS:]
    if len(days) < _MIN_BURN_DAYS:
        return {"raw_value": None,
                "source_note": (f"no reading: only {len(days)} business days of TGA "
                                f"withdrawals available to {obs}, and a burn rate "
                                f"averaged over fewer than {_MIN_BURN_DAYS} is not "
                                f"this line's denominator")}
    burn = statistics.fmean(withdrawn[d] for d in days)
    if burn <= 0:
        return {"raw_value": None,
                "source_note": (f"no reading: trailing mean TGA withdrawal to {obs} is "
                                f"{burn:.0f} $m — a buffer cannot be expressed in days "
                                f"of an outflow that is not flowing")}

    balance = closing[obs]
    return {
        "raw_value": round(balance / burn, 3),
        "source_note": (f"US Treasury cash ${balance:,.0f}m / ${burn:,.0f}m mean daily "
                        f"withdrawal over {len(days)} business days to {obs} "
                        f"= {balance / burn:.2f} days of outflows"),
        "obs_date": obs,
        # A ratio destroys its own inputs. Both are stored so a later reader can
        # ask whether the buffer fell or the spending rose — the same argument
        # that put the per-strait breakdown beside the chokepoint sum.
        "components": {"tga_balance_musd": balance, "mean_daily_withdrawal_musd": burn},
    }
