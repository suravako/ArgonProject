"""LLM extracts -> plain Python validates -> LLM writes the brief.
Design rule: the model reads and writes; deterministic code makes the risk calls."""
import json, pathlib
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from typing import Literal, Optional

from google import genai
from google.genai import types
from pydantic import BaseModel

MODEL = "gemini-3.5-flash"
client = genai.Client()  # reads GEMINI_API_KEY from the environment
MIN_GAP = 1

class Doc(BaseModel):
    doc_type: Literal["contract","invoice"]  # "contract" or "invoice"
    contract_id: str
    vendor: str
    monthly_fee: Optional[float] = None
    end_date: Optional[str] = None       # YYYY-MM-DD
    auto_renew: Optional[bool] = None
    notice_days: Optional[int] = None
    termination_penalty_pct: Optional[float] = None
    invoice_amount: Optional[float] = None
    confidence: float                    # 0-1, model's own certainty
    evidence: str                        # short quote supporting the key fields


SYSTEM = ("Extract fields from the document. Use null for anything not stated; never guess. "
          "Dates must be YYYY-MM-DD. Lower the confidence if wording is ambiguous.")


def extract(text: str) -> dict:
    r = client.models.generate_content(
        model=MODEL, contents=text,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM,
            response_mime_type="application/json",
            response_schema=Doc))
    return Doc.model_validate_json(r.text).model_dump()


def load_and_extract(folder: str) -> list[dict]:
    files = sorted(p for p in pathlib.Path(folder).glob("*.txt"))
    with ThreadPoolExecutor(max_workers=4) as pool:
        return list(pool.map(lambda p: {**extract(p.read_text()), "file": p.name}, files))


def find_flags(records: list[dict], today: date) -> list[dict]:
    contracts = {r["contract_id"]: r for r in records if r["doc_type"] == "contract"}
    flags = []

    def add(r, severity, issue, action):
        flags.append(dict(contract_id=r["contract_id"], vendor=r["vendor"],
                          severity=severity, issue=issue, action=action))

    for r in records:
        if r["confidence"] < 0.8:
            add(r, "review", f"Low extraction confidence ({r['file']})", "Human check before acting")
        if r["doc_type"] == "contract":
            if r["auto_renew"] and r["end_date"] and r["notice_days"]:
                try:
                    deadline = date.fromisoformat(r["end_date"]) - timedelta(days=r["notice_days"])
                except ValueError:
                    add(r, "review", "Unreadable end date", "Human check")
                    continue
                left = (deadline - today).days
                if left <= 90:
                    add(r, "high" if left <= 30 else "medium",
                        f"Auto-renews; cancellation notice due {deadline} ({left} days)",
                        "Decide renew or cancel before the deadline")
            if (r["termination_penalty_pct"] or 0) >= 25:
                add(r, "low", f"High exit penalty ({r['termination_penalty_pct']}%)",
                    "Factor into renewal negotiation")
        else:
            c = contracts.get(r["contract_id"])
            if c and c["monthly_fee"] and r["invoice_amount"] and r["invoice_amount"] > c["monthly_fee"] * 1.02:
                add(r, "high", f"Invoice ${r['invoice_amount']:.0f} exceeds contracted ${c['monthly_fee']:.0f}",
                    "Dispute with vendor")
    order = {"high": 0, "medium": 1, "review": 2, "low": 3}
    return sorted(flags, key=lambda f: order[f["severity"]])


def write_brief(flags: list[dict]) -> str:
    prompt = ("Write a one-page weekly brief for a busy business owner from these flags. "
              "Lead with the 3 most urgent actions, then a short list of the rest. "
              "Use ONLY facts in the data; do not invent numbers or dates.\n\n" + json.dumps(flags))
    return client.models.generate_content(model=MODEL, contents=prompt).text


def run(folder: str, today: Optional[date] = None) -> dict:
    today = today or date.today()
    records = load_and_extract(folder)
    flags = find_flags(records, today)
    return {"records": records, "flags": flags, "brief": write_brief(flags)}


def ask(question: str, records: list[dict]) -> str:
    prompt = ("Answer using only this extracted data. If it isn't there, say so. "
              "Cite contract IDs.\n\nDATA:\n" + json.dumps(records) + "\n\nQUESTION: " + question)
    return client.models.generate_content(model=MODEL, contents=prompt).text
