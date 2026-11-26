"""Field-level accuracy against the synthetic answer key. This is your LinkedIn number."""
import json, pathlib
from collections import defaultdict
from pipeline import load_and_extract

key = {k["contract_id"]: k for k in json.loads(pathlib.Path("data/answer_key.json").read_text())}
records = load_and_extract("data")
hits, total = defaultdict(int), defaultdict(int)

for r in records:
    truth = key[r["contract_id"]]
    # contracts are scored on contract fields, invoices on the amount
    fields = (["vendor", "monthly_fee", "end_date", "auto_renew", "notice_days", "termination_penalty_pct"]
              if r["doc_type"] == "contract" else ["invoice_amount"])
    for f in fields:
        total[f] += 1
        got, want = r[f], truth[f]
        ok = (abs(got - want) < 0.01) if isinstance(want, (int, float)) and not isinstance(want, bool) and got is not None else got == want
        hits[f] += ok
        if not ok:
            print(f"MISS {r['file']}: {f} got={got!r} want={want!r}")

print()
for f in total:
    print(f"{f:28s} {hits[f]}/{total[f]}  ({100 * hits[f] / total[f]:.0f}%)")
print(f"{'OVERALL':28s} {sum(hits.values())}/{sum(total.values())}  "
      f"({100 * sum(hits.values()) / sum(total.values()):.0f}%)")
