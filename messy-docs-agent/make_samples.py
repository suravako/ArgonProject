"""Generate synthetic contracts + invoices and an answer key for evaluation.
No real client data is ever used."""
import json, pathlib, random
from datetime import date, timedelta

random.seed(7)
out = pathlib.Path("data"); out.mkdir(exist_ok=True)
today = date.today()
vendors = ["Acme Freight", "BlueLeaf Cleaning", "Cortex IT Support", "Delta Packaging",
           "Evergreen Security", "Falcon Fuel Cards", "Granite Insurance", "Helix Software"]
key = []

for i, v in enumerate(vendors, 1):
    cid = f"C-{i:03d}"
    monthly = random.choice([1200, 2500, 4000, 6500, 9000])
    end = today + timedelta(days=random.randint(20, 300))   # renewals land in the near future
    start = end.replace(year=end.year - 1)
    auto = random.random() < 0.6
    notice = random.choice([30, 60, 90])
    penalty = random.choice([0, 10, 25])
    renewal = (f"This agreement renews automatically for 12 months unless Client gives written "
               f"notice at least {notice} days before the end date."
               if auto else "This agreement expires at term end unless both parties sign a renewal.")
    (out / f"contract_{cid}.txt").write_text(
        f"SERVICE AGREEMENT {cid}\n"
        f'Between Northwind Traders Pvt Ltd ("Client") and {v} ("Vendor").\n'
        f"Term: begins {start.isoformat()} and ends {end.isoformat()}.\n"
        f"Fees: Client pays ${monthly} per month.\n"
        f"Renewal: {renewal}\n"
        f"Early termination: Client pays {penalty}% of remaining fees.\n")
    billed = round(monthly * 1.15) if i % 3 == 0 else monthly   # every 3rd vendor overbills
    (out / f"invoice_{cid}.txt").write_text(
        f"INVOICE for agreement {cid}\nVendor: {v}\nMonth: last month\nAmount due: ${billed}\n")
    key.append(dict(contract_id=cid, vendor=v, monthly_fee=monthly, end_date=end.isoformat(),
                    auto_renew=auto, notice_days=notice if auto else None,
                    termination_penalty_pct=penalty, invoice_amount=billed))

(out / "answer_key.json").write_text(json.dumps(key, indent=2))
print(f"Wrote {len(vendors) * 2} documents + answer_key.json to {out}/")
