
"""Kasey Expense Tracker - Flet frontend connected to FastAPI."""

import logging
import threading
from datetime import date

import flet as ft
import requests

from client import ExpenseAPIClient
from models import CATEGORIES
from api import fetch_rates

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

ACCENT = ft.Colors.TEAL
PAD = 20


def money(value):
    return f"R {value:,.2f}"


def main(page: ft.Page):
    page.title = "Kasey Expense Tracker"
    page.theme = ft.Theme(color_scheme_seed=ACCENT)
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 420
    page.window.height = 760

    client = ExpenseAPIClient()

    def snack(message):
        page.open(ft.SnackBar(ft.Text(message)))

    def api_error(error):
        try:
            return error.response.json().get("detail", "Something went wrong.")
        except Exception:
            return "Could not connect to the server. Check that FastAPI is running."

    def heading(text):
        return ft.Text(text, size=24, weight=ft.FontWeight.BOLD)

    # ---------- Login and registration ----------

    email_f = ft.TextField(label="Email", keyboard_type=ft.KeyboardType.EMAIL)
    password_f = ft.TextField(label="Password", password=True, can_reveal_password=True)
    auth_title = ft.Text("Welcome back", size=26, weight=ft.FontWeight.BOLD)
    auth_button = ft.FilledButton("Login")
    auth_switch = ft.TextButton("Create an account")
    registering = False

    def show_auth():
        page.navigation_bar = None
        auth_title.value = "Create your account" if registering else "Welcome back"
        auth_button.text = "Register" if registering else "Login"
        auth_switch.text = "Already have an account? Login" if registering else "Create an account"

        page.controls.clear()
        page.add(
            ft.Container(
                content=ft.Column(
                    [
                        heading("Kasey Expense Tracker"),
                        auth_title,
                        email_f,
                        password_f,
                        auth_button,
                        auth_switch,
                    ],
                    spacing=18,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                ),
                padding=PAD,
                expand=True,
            )
        )
        page.update()

    def switch_auth(_):
        nonlocal registering
        registering = not registering
        show_auth()

    def authenticate(_):
        email = (email_f.value or "").strip()
        password = password_f.value or ""

        try:
            if registering:
                client.register(email, password)
                client.login(email, password)
                snack("Account created successfully!")
            else:
                client.login(email, password)

            show_app()

        except requests.RequestException as error:
            snack(api_error(error))
        except Exception as error:
            snack(str(error))

    auth_button.on_click = authenticate
    auth_switch.on_click = switch_auth

    # ---------- Main application ----------

    def show_app():
        page.controls.clear()

        def refresh_summary(total_text, breakdown):
            try:
                summary = client.get_summary()
                total_text.value = money(summary["total_spent"])
                breakdown.controls = [
                    ft.Row(
                        [ft.Text(category), ft.Text(money(amount))],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    )
                    for category, amount in summary["by_category"].items()
                ] or [ft.Text("No expenses yet. Add your first one.")]
            except requests.RequestException as error:
                snack(api_error(error))

        # Home view
        title_f = ft.TextField(label="What did you spend on?")
        amount_f = ft.TextField(
            label="Amount (R)",
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        cat_f = ft.Dropdown(
            label="Category",
            value="Food",
            options=[ft.dropdown.Option(category) for category in CATEGORIES],
        )

        total_t = ft.Text(size=32, weight=ft.FontWeight.BOLD, color=ACCENT)
        breakdown = ft.Column(spacing=6)

        def add_expense(_):
            try:
                amount = float((amount_f.value or "").replace(",", "."))
                client.add_expense(
                    title=title_f.value or "",
                    amount=amount,
                    category=cat_f.value,
                    spent_on=date.today().isoformat(),
                )
                title_f.value = ""
                amount_f.value = ""
                refresh_summary(total_t, breakdown)
                snack("Expense saved successfully!")
                page.update()

            except ValueError:
                snack("Enter a valid amount.")
            except requests.RequestException as error:
                snack(api_error(error))

        def home_view():
            refresh_summary(total_t, breakdown)
            return ft.Column(
                [
                    heading("Add expense"),
                    title_f,
                    amount_f,
                    cat_f,
                    ft.FilledButton(
                        "Save expense",
                        icon=ft.Icons.ADD,
                        on_click=add_expense,
                    ),
                    ft.Divider(),
                    ft.Text("Total spent"),
                    total_t,
                    breakdown,
                ],
                spacing=14,
                scroll=ft.ScrollMode.AUTO,
            )

        # History view
        def history_view():
            try:
                expenses = client.get_expenses()
                items = []

                for expense in expenses:
                    expense_id = expense["id"]

                    def delete_handler(eid):
                        def handler(_):
                            try:
                                client.delete_expense(eid)
                                snack("Expense deleted.")
                                show(1)
                            except requests.RequestException as error:
                                snack(api_error(error))
                        return handler

                    items.append(
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.RECEIPT_LONG, color=ACCENT),
                            title=ft.Text(expense["title"]),
                            subtitle=ft.Text(
                                f'{expense["category"]} - {expense["spent_on"]}'
                            ),
                            trailing=ft.Row(
                                [
                                    ft.Text(money(expense["amount"])),
                                    ft.IconButton(
                                        ft.Icons.DELETE_OUTLINE,
                                        tooltip="Delete",
                                        on_click=delete_handler(expense_id),
                                    ),
                                ],
                                tight=True,
                            ),
                        )
                    )

                return ft.Column(
                    [heading("History"), *(items or [ft.Text("Nothing here yet.")])],
                    spacing=8,
                    scroll=ft.ScrollMode.AUTO,
                )

            except requests.RequestException as error:
                snack(api_error(error))
                return ft.Column([heading("History"), ft.Text("Could not load expenses.")])

        # Rates view
        def rates_view():
            status = ft.Text("Loading live rates...")
            rows = ft.Column(spacing=6)
            ring = ft.ProgressRing(width=24, height=24)

            def load():
                try:
                    summary = client.get_summary()
                    rates = fetch_rates()
                    total = summary["total_spent"]

                    rows.controls = [
                        ft.Row(
                            [
                                ft.Text(currency),
                                ft.Text(f"{total * rates[currency]:,.2f} {currency}"),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        )
                        for currency in ["USD", "EUR", "GBP", "BWP", "NGN"]
                        if currency in rates
                    ]
                    status.value = f"Your total of {money(total)} in other currencies:"
                except Exception as error:
                    status.value = str(error)

                ring.visible = False
                page.update()

            threading.Thread(target=load, daemon=True).start()

            return ft.Column(
                [
                    heading("Live rates"),
                    ring,
                    status,
                    rows,
                    ft.OutlinedButton(
                        "Refresh",
                        icon=ft.Icons.REFRESH,
                        on_click=lambda _: show(2),
                    ),
                ],
                spacing=14,
            )

        # Navigation
        views = [home_view, history_view, rates_view]
        body = ft.Container(padding=PAD, expand=True)

        def logout(_):
            client.token = None
            show_auth()

        def show(index):
            nav.selected_index = index
            body.content = views[index]()
            page.update()

        nav = ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icons.HOME_OUTLINED, label="Home"
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.HISTORY, label="History"
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.CURRENCY_EXCHANGE, label="Rates"
                ),
            ],
            on_change=lambda e: show(e.control.selected_index),
        )

        page.add(
            ft.Row(
                [
                    ft.Text("Kasey Expense Tracker", weight=ft.FontWeight.BOLD),
                    ft.TextButton("Logout", on_click=logout),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            body,
        )
        page.navigation_bar = nav
        show(0)

    show_auth()


if __name__ == "__main__":
    ft.app(target=main)
