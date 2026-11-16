# Expense Tracker (Flet capstone)

Track daily spending, see totals per category, and convert your total into other currencies using live exchange rates.

## Features (mapped to the course units)
- **Class modelling a real entity** - `Expense` in `models.py`, with validation
- **Persistence** - expenses saved to `data/expenses.json`
- **Live API** - exchange rates from open.er-api.com (`api.py`), loaded in the background
- **Multi-view Flet UI** - Home, History and Rates via a navigation bar, one teal theme via `page.theme`
- **Error handling & logging** - try/except around file and network access, errors written to `app.log`
- **Form validation** - empty titles and non-numeric/zero amounts are rejected with clear messages

## How to run
```
python -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt   # tested with Flet 0.27
flet run main.py               # or: python main.py
```
Run tests: `python test_models.py`

## Folder structure
```
main.py          UI and navigation
models.py        Expense class + JSON store
api.py           live exchange-rate API
test_models.py   tests
data/            saved expenses
assets/          images/icons
```
