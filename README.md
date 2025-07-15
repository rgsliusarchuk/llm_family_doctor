# LLM-асистент сімейного лікаря  (MVP)

Single-repo for data-prep **and** Streamlit UI.

* **data-prep** → `notebooks/data_prep.ipynb` (Google Colab badge below)
* **app**      → `app.py` (run locally or on Streamlit Cloud)

[![Run data prep in Colab](https://colab.research.google.com/assets/colab-badge.svg)]
(https://colab.research.google.com/github/rsliusarchuk/llm-family-doctor/blob/main/notebooks/data_prep.ipynb) 

Ingest files:

```python scripts/ingest_protocol.py data/raw_pdfs/example.pdf```

```python scripts/ingest_protocol.py --dir data/raw_pdfs```

```python scripts/ingest_protocol.py --dir data/raw_pdfs --recursive```







