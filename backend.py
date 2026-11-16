import sqlite3

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import FastAPI


from pydantic import BaseModel, Field, field_validator

from database import create_tables, get_connection
from security import hash_password, verify_password
from auth import create_access_token, verify_access_token

# Create our FastAPI application
app = FastAPI(
    title="Kasey Expense Tracker API",
    description="Backend API for managing personal expenses",
    version="1.0.0"
)

# Authentication scheme for protected endpoints
bearer_scheme = HTTPBearer(auto_error=False)

class UserRegister(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class ExpenseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    amount: float = Field(gt=0)
    category: str = "Other"
    spent_on: str

class ExpenseUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    amount: float = Field(gt=0)
    category: str
    spent_on: str

    @field_validator("category")
    @classmethod
    def validate_category(cls, value):
        allowed_categories = [
            "Food",
            "Transport",
            "Rent",
            "Entertainment",
            "Health",
            "Other"
        ]

        if value not in allowed_categories:
            raise ValueError("Invalid expense category.")

        return value

    @field_validator("category")
    @classmethod
    def validate_category(cls, value):
        allowed_categories = [
            "Food",
            "Transport",
            "Rent",
            "Entertainment",
            "Health",
            "Other"
        ]

        if value not in allowed_categories:
            raise ValueError("Invalid expense category.")

        return value

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)
):
    # Check whether the user supplied an authentication token
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication token is required.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = credentials.credentials

    # Verify the token and retrieve the user ID
    try:
        user_id = verify_access_token(token)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Find the user in our database
    connection = get_connection()

    try:
        user = connection.execute(
            "SELECT id, email FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

        if user is None:
            raise HTTPException(
                status_code=401,
                detail="User account not found."
            )

        return {
            "id": user["id"],
            "email": user["email"]
        }

    finally:
        connection.close()


@app.get("/")
def home():
    return {
        "message": "Welcome to Kasey Expense Tracker API!",
        "status": "Backend is running successfully"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.post("/register")
def register_user(user: UserRegister):

    # Clean up the email address
    email = user.email.strip().lower()

    # Check that the email looks valid
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(
            status_code=400,
            detail="Please enter a valid email address."
        )

    # Check password length
    if len(user.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 8 characters."
        )

    # Securely hash the password
    password_hash = hash_password(user.password)

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO users (email, password_hash)
            VALUES (?, ?)
            """,
            (email, password_hash)
        )

        connection.commit()

        return {
            "message": "User registered successfully!",
            "email": email
        }

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="This email address is already registered."
        )

    finally:
        connection.close()


@app.post("/login")
def login_user(user: UserLogin):

    # Clean up the email address
    email = user.email.strip().lower()

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Find the registered user
        cursor.execute(
            "SELECT id, email, password_hash FROM users WHERE email = ?",
            (email,)
        )

        existing_user = cursor.fetchone()

        # Check whether the user exists
        if existing_user is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password."
            )

        # Verify the submitted password
        if not verify_password(
            user.password,
            existing_user["password_hash"]
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password."
            )

        # Login successful - generate an access token
        access_token = create_access_token(existing_user["id"])

        return {
            "message": "Login successful!",
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": existing_user["id"],
            "email": existing_user["email"]
        }

    finally:
        connection.close()

@app.get("/me")
def read_current_user(
    current_user: dict = Depends(get_current_user)
):
    return {
        "message": "You are authenticated!",
        "user_id": current_user["id"],
        "email": current_user["email"]
    }

@app.post("/expenses")
def add_expense(
    expense: ExpenseCreate,
    current_user: dict = Depends(get_current_user)
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO expenses (
                user_id, title, amount, category, spent_on
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                current_user["id"],
                expense.title,
                expense.amount,
                expense.category,
                expense.spent_on
            )
        )

        connection.commit()

        return {
            "message": "Expense added successfully!",
            "expense_id": cursor.lastrowid,
            "title": expense.title,
            "amount": expense.amount,
            "category": expense.category,
            "spent_on": expense.spent_on
        }

    finally:
        connection.close()


@app.get("/expenses")
def get_expenses(
    current_user: dict = Depends(get_current_user)
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, title, amount, category, spent_on
            FROM expenses
            WHERE user_id = ?
            ORDER BY spent_on DESC
            """,
            (current_user["id"],)
        )

        expenses = cursor.fetchall()

        return {
            "expenses": [dict(expense) for expense in expenses]
        }

    finally:
        connection.close()

@app.delete("/expenses/{expense_id}")
def delete_expense(
    expense_id: int,
    current_user: dict = Depends(get_current_user)
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM expenses
            WHERE id = ? AND user_id = ?
            """,
            (expense_id, current_user["id"])
        )

        connection.commit()

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Expense not found."
            )

        return {
            "message": "Expense deleted successfully!"
        }

    finally:
        connection.close()


@app.put("/expenses/{expense_id}")
def update_expense(
    expense_id: int,
    expense: ExpenseUpdate,
    current_user: dict = Depends(get_current_user)
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE expenses
            SET title = ?, amount = ?, category = ?, spent_on = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                expense.title,
                expense.amount,
                expense.category,
                expense.spent_on,
                expense_id,
                current_user["id"]
            )
        )

        connection.commit()

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Expense not found."
            )

        return {
            "message": "Expense updated successfully!",
            "expense_id": expense_id
        }

    finally:
        connection.close()


@app.get("/expenses/summary")
def expense_summary(
    current_user: dict = Depends(get_current_user)
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_expenses,
                COALESCE(SUM(amount), 0) AS total_spent
            FROM expenses
            WHERE user_id = ?
            """,
            (current_user["id"],)
        )

        totals = cursor.fetchone()

        cursor.execute(
            """
            SELECT category, SUM(amount) AS total
            FROM expenses
            WHERE user_id = ?
            GROUP BY category
            """,
            (current_user["id"],)
        )

        categories = cursor.fetchall()

        return {
            "total_expenses": totals["total_expenses"],
            "total_spent": round(totals["total_spent"], 2),
            "by_category": {
                row["category"]: round(row["total"], 2)
                for row in categories
            }
        }

    finally:
        connection.close()
