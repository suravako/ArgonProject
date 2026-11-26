# Messy documents → decisions (Gemini 4 Argon)

An agent that reads vendor contracts and invoices, extracts structured data, flags risks
(auto-renewal deadlines, overbilling, high exit penalties), and writes a one-page weekly brief.

**Design principle:** the model reads and writes; plain Python makes the risk calls. Every extraction
carries a confidence score and an evidence quote, and low-confidence items are routed to a human.

## Run it
```bash
pip install google-genai pydantic streamlit
export GEMINI_API_KEY=your_key
python make_samples.py      # synthetic data + answer key
python eval.py              # field-level accuracy
streamlit run app.py
```

## Using this in your business
1. **Audit:** pick one document type that causes pain (contracts, invoices, POs).
2. **Pilot:** run 20-50 of your documents, review the flags, and measure accuracy.
3. **Roll out:** add PDF/OCR intake, connect email or Drive, and send the weekly brief automatically.

Synthetic data only. Swap the rules in `find_flags` for your own business logic.
