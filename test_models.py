"""Simple tests - run with:  python -m pytest  (or python test_models.py)"""
import tempfile
from pathlib import Path
from models import Expense, ExpenseStore


def test_invalid_amount_rejected():
    try:
        Expense("Lunch", 0)
        assert False
    except ValueError:
        pass


def test_save_and_reload():
    p = Path(tempfile.mkdtemp()) / "e.json"
    s = ExpenseStore(p)
    s.add(Expense("Taxi", 30, "Transport"))
    s.add(Expense("Bread", 20.5, "Food"))
    assert ExpenseStore(p).total() == 50.5


if __name__ == "__main__":
    test_invalid_amount_rejected(); test_save_and_reload(); print("All tests passed")
