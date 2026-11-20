"""API client for communicating with the Expense Tracker backend."""

import os
import requests

# On Render, use the port assigned to this service. Locally, default to 8000.
BASE_URL = (
    os.getenv("API_BASE_URL")
    or f"http://127.0.0.1:{os.getenv('PORT', '8000')}"
).rstrip("/")


class ExpenseAPIClient:

    def __init__(self):
        self.token = None

    def get_headers(self):
        """Return authentication headers when logged in."""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def register(self, email, password):
        """Register a new user."""
        response = requests.post(
            f"{BASE_URL}/register",
            json={"email": email, "password": password},
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    def login(self, email, password):
        """Log in and save the access token."""
        response = requests.post(
            f"{BASE_URL}/login",
            json={"email": email, "password": password},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        self.token = data["access_token"]
        return data

    def add_expense(self, title, amount, category, spent_on):
        """Add an expense to the logged-in user's account."""
        response = requests.post(
            f"{BASE_URL}/expenses",
            json={
                "title": title,
                "amount": amount,
                "category": category,
                "spent_on": spent_on
            },
            headers=self.get_headers(),
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    def get_expenses(self):
        """Retrieve expenses belonging to the logged-in user."""
        response = requests.get(
            f"{BASE_URL}/expenses",
            headers=self.get_headers(),
            timeout=10
        )
        response.raise_for_status()
        return response.json()["expenses"]

    def delete_expense(self, expense_id):
        """Delete an expense."""
        response = requests.delete(
            f"{BASE_URL}/expenses/{expense_id}",
            headers=self.get_headers(),
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    def update_expense(self, expense_id, title, amount, category, spent_on):
        """Update an existing expense."""
        response = requests.put(
            f"{BASE_URL}/expenses/{expense_id}",
            json={
                "title": title,
                "amount": amount,
                "category": category,
                "spent_on": spent_on
            },
            headers=self.get_headers(),
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    def get_summary(self):
        """Retrieve the spending summary."""
        response = requests.get(
            f"{BASE_URL}/expenses/summary",
            headers=self.get_headers(),
            timeout=10
        )
        response.raise_for_status()
        return response.json()
