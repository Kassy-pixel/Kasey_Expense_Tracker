"""Data model: the Expense class (OOP unit) and JSON persistence (file handling unit)."""
import json
import logging
from dataclasses import dataclass, asdict, field
from datetime import date
from pathlib import Path
from uuid import uuid4

DATA_FILE = Path(__file__).parent / "data" / "expenses.json"
CATEGORIES = ["Food", "Transport", "Rent", "Entertainment", "Health", "Other"]
log = logging.getLogger(__name__)


@dataclass
class Expense:
    """A single expense - models a real-world entity."""
    title: str
    amount: float
    category: str = "Other"
    spent_on: str = field(default_factory=lambda: date.today().isoformat())
    id: str = field(default_factory=lambda: uuid4().hex[:8])

    def __post_init__(self):
        if not self.title.strip():
            raise ValueError("Title cannot be empty")
        if self.amount <= 0:
            raise ValueError("Amount must be greater than 0")
        if self.category not in CATEGORIES:
            self.category = "Other"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Expense":
        return cls(**d)


class ExpenseStore:
    """Loads and saves expenses to a JSON file, with error handling."""

    def __init__(self, path: Path = DATA_FILE):
        self.path = path
        self.expenses: list[Expense] = self.load()

    def load(self) -> list[Expense]:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return [Expense.from_dict(d) for d in json.load(f)]
        except FileNotFoundError:
            return []
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            log.error("Could not read %s: %s", self.path, e)
            return []

    def save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump([e.to_dict() for e in self.expenses], f, indent=2)
        except OSError as e:
            log.error("Could not save expenses: %s", e)

    def add(self, expense: Expense) -> None:
        self.expenses.append(expense)
        self.save()

    def delete(self, expense_id: str) -> None:
        self.expenses = [e for e in self.expenses if e.id != expense_id]
        self.save()

    def total(self) -> float:
        return round(sum(e.amount for e in self.expenses), 2)

    def by_category(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for e in self.expenses:
            out[e.category] = round(out.get(e.category, 0) + e.amount, 2)
        return out
