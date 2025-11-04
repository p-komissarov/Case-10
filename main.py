# Case №10 by Greshnova S., Loseva E., Shevchenko A., Komissarov P.

from datetime import datetime
import csv
import json
import os
from collections import defaultdict
import ru_local as ru


def _parse_date(date_str: str) -> str | None:

    """
    Utility function to parse date from string to datetime object.

    Args:
        date_str (str): Date string in various formats.
    Returns:
        datetime | None: Parsed datetime object or None if parsing fails.
    """

    if not date_str:
        return None
    formats = ("%Y-%m-%d", "%d.%m.%Y", "%Y/%m/%d", "%d/%m/%Y")
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    return None


def _format_rub(amount: float) -> str:

    """
    Utility function to format amount as Russian ruble currency string.

    Args:
        amount (float): Amount in rubles.
    Returns:
        str: Formatted amount string.
    """

    rub = f"{amount:,.2f} {ru.RUBLES}".replace(",", " ")
    return rub


def read_csv_file(filename: str) -> list:

    """
     Read a CSV file and return its contents as a list of dictionaries.

        Args:
            filename (str): Path to the CSV file.
        Returns:
            list: List of rows as dictionaries.
    """

    if not os.path.exists(filename):
        raise FileNotFoundError(f"{ru.FILE_NOT_FOUND} {filename}")
    rows = []
    with open(filename, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({(k if k is not None else ""): v for k, v in r.items()})
    return rows


def read_json_file(filename: str) -> list:

    """
    Read a JSON file and return its contents as a list of dictionaries.

    Args:
        filename (str): Path to the JSON file.
    Returns:
        list: List of rows as dictionaries.
    """

    if not os.path.exists(filename):
        raise FileNotFoundError(f"{ru.FILE_NOT_FOUND} {filename}")
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def import_financial_data(filename: str) -> list:

    """
    Import financial data from a CSV or JSON file and return it as a list of dictionaries.

    Args:
        filename (str): Path to the input file (CSV or JSON).
    Returns:
        list: List of financial data rows as dictionaries.
    """

    if not os.path.exists(filename):
        raise FileNotFoundError(filename)
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".csv":
        raw = read_csv_file(filename)
    elif ext == ".json":
        raw = read_json_file(filename)
    else:
        raise ValueError(ru.SUPPORTED_FILES)

    rows = []
    for r in raw:
        date = r["date"]
        amount = float(r["amount"])
        desc = r.get("description", "") or ""
        rows.append({"date": date, "amount": amount, "description": desc})
    return rows


def create_categories() -> dict:
    
    """
    Creates and returns a dictionary of transaction categories with their associated keywords.

    The dictionary maps category names to lists of keywords that are used to identify
    transactions belonging to that category through text matching in transaction descriptions.

    Returns:
        dict: A dictionary where keys are category names (str) and values are lists
              of keywords (str) for that category.
    """

    categories = {
        ru.FOOD: ru.FOOD_CATEGORIES,
        ru.TRANSPORT: ru.TRANSPORT_CATEGORIES,
        ru.ENTERTAINMENT: ru.ENTERTAINMENT_CATEGORIES,
        ru.HEALTH: ru.HEALTH_CATEGORIES,
        ru.UTILITIES: ru.UTILITIES_CATEGORIES,
        ru.CLOTHING: ru.CLOTHING_CATEGORIES
    }
    return categories


def categorize_transaction(description: str, categories: dict) -> str:

    """ 
    Categorizes a single transaction based on its description text.

    Args:
        description (str): The transaction description text to analyze
        categories (dict): Dictionary of categories and their keywords from create_categories()

    Returns:
        str: The name of the matched category, or "other" if no match found
    """

    description_lower = description.lower()

    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in description_lower:
                return category
    return ru.OTHER


def categorize_all_transactions(transactions: list) -> list:

    """ 
    Adds category field to all transactions using keyword matching.

    Args:
        transactions: List of transaction dictionaries

    Returns:
        New list with categorized transactions (originals preserved).
    """

    categories = create_categories()
    categorized_transactions = []
    
    for transaction in transactions:
        transaction_copy = transaction.copy()
        description = transaction.get("description", "")
        category = categorize_transaction(description, categories)
        transaction_copy["category"] = category
        categorized_transactions.append(transaction_copy)
    return categorized_transactions


def calculate_basic_stats(transactions: dict) -> dict:

    """
    Function to calculate basic statistics from transactions.

    Args:
        transactions (dict): List of transaction dictionaries.
    Returns:
        dict: Dictionary containing total income, total expense, balance,
              number of transactions, income count, and expense count.
    """

    total_income = 0
    total_expense = 0
    income_count = 0
    expense_count = 0

    for tx in transactions:
        amount = tx.get("amount", 0)
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            continue

        if amount >= 0:
            total_income += amount
            income_count += 1
        else:
            total_expense += abs(amount)
            expense_count += 1

    balance = total_income - total_expense
    return {
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "balance": round(balance, 2),
        "transactions_count": len(transactions),
        "income_count": income_count,
        "expense_count": expense_count
    }


def calculate_by_category(transactions: dict) -> dict:

    """
    Function to calculate statistics by category from transactions.

    Args:
        transactions (dict): List of transaction dictionaries.
    Returns:
        dict: Dictionary containing statistics per category including total amount,
              total expenses, count of transactions, and percentage of total expenses.
    """
   
    category_totals = defaultdict(float)
    category_expense_totals = defaultdict(float)
    category_counts = defaultdict(int)
    total_expenses = 0

    for tx in transactions:
        amount = tx.get("amount", 0)
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            continue

        category = tx.get("category") or ru.OTHER
        category = category if isinstance(category, str) else ru.OTHER

        if amount < 0:
            expense = abs(amount)
            category_expense_totals[category] += expense
            total_expenses += expense

        category_totals[category] += amount
        category_counts[category] += 1

    result = {}
    for cat in category_counts:
        expense_total = category_expense_totals.get(cat, 0)
        percent = (
            (expense_total / total_expenses * 100) if total_expenses > 0 else 0
        )
        result[cat] = {
            "total": round(category_totals.get(cat, 0), 2),
            "expense_total": round(expense_total, 2),
            "count": category_counts[cat],
            "percent_of_expenses": round(percent, 2)
        }

    return result


def analyze_by_time(transactions: list) -> dict:

    """
    Function to analyze transactions by time (monthly).

    Args:
        transactions (list): List of transaction dictionaries.
    Returns:
        dict: Dictionary containing monthly income, expense, and top categories.
    """

    months_income = defaultdict(float)
    months_expense = defaultdict(float)
    months_category_expense = defaultdict(lambda: defaultdict(float))

    for tx in transactions:
        date_str = tx.get("date")
        date = _parse_date(date_str)
        if date is None:
            continue
        month_key = date.strftime("%Y-%m")
        try:
            amount = float(tx.get("amount", 0))
        except (ValueError, TypeError):
            continue

        category = tx.get("category") or ru.OTHER
        category = category if isinstance(category, str) else ru.OTHER

        if amount >= 0:
            months_income[month_key] += amount
        else:
            exp = abs(amount)
            months_expense[month_key] += exp
            months_category_expense[month_key][category] += exp

    result = {}
    months = sorted(set(months_income) | set(months_expense))
    for month in months:
        cat_exp = months_category_expense.get(month, {})
        top = sorted(cat_exp.items(), key=lambda i: i[1], reverse=True)[:3]
        top = [(cat, round(exp, 2)) for cat, exp in top]
        result[month] = {
            "income": round(months_income.get(month, 0), 2),
            "expense": round(months_expense.get(month, 0), 2),
            "top_categories": top
        }

    return result


def analyze_historical_spending(months_analysis: dict) -> dict:

    """
    Analyzes historical spending data to compute average monthly spending and income.

    Args:
        months_analysis (dict): Monthly analysis data from analyze_by_time
    Returns:
        dict: Analysis results including average monthly spending, income, and top categories.
    """

    total_spending = 0
    total_income = 0
    month_count = len(months_analysis)
    category_totals = defaultdict(float)

    for month_data in months_analysis.values():
        total_spending += month_data.get("expense", 0)
        total_income += month_data.get("income", 0)
        for category, amount in month_data.get("top_categories", []):
            category_totals[category] += amount

    average_monthly_spending = round(total_spending / month_count, 2) if month_count > 0 else 0
    average_monthly_income = round(total_income / month_count, 2) if month_count > 0 else 0

    top_categories = dict(sorted(category_totals.items(), key=lambda i: i[1], reverse=True)[:3])

    return {
        "average_monthly_spending": average_monthly_spending,
        "average_monthly_income": average_monthly_income,
        "total_avg_spending": round(total_spending / month_count, 2) if month_count > 0 else 0,
        "top_categories": top_categories
    }


def create_budget_template(analysis: dict, current_stats: dict) -> dict:

    """
    Creates budget recommendations based on historical financial analysis and current statistics.

    Args:
        analysis (dict): Historical spending analysis from analyze_historical_spending()
        current_stats (dict): Current financial statistics from calculate_basic_stats()

    Returns:
        dict: Budget recommendations including verdict, advice, goal, and budget limits per category.
    """

    avg_spending_by_category = analysis["top_categories"]
    total_avg_spending = analysis["total_avg_spending"]
    avg_income = analysis["average_monthly_income"]

    current_income = current_stats["total_income"]
    current_spending = current_stats["total_expense"]

    budget_limits = {
        category: round(avg_amount * 0.9, 2)
        for category, avg_amount in avg_spending_by_category.items()
    }

    if current_income >= avg_income and current_spending <= total_avg_spending:
        verdict = ru.VERDICT_1

        if analysis["top_categories"]:
            top_category = list(analysis["top_categories"].keys())[0]
            top_amount = analysis["top_categories"][top_category]
            percent_of_total = (top_amount / total_avg_spending * 100) if total_avg_spending > 0 else 0
            suggested_reduction = 10
            advice = f"{ru.ADVICE_1}{top_category}{ru.ADVICE_2}{suggested_reduction}%\n{ru.ADVICE_3}{percent_of_total:.1f}%{ru.ADVICE_4}"
        else:
            advice = ru.ADVICE_5
    else:
        if current_income < avg_income:
            income_diff_percent = ((avg_income - current_income) / avg_income * 100) if avg_income > 0 else 0
            verdict = ru.VERDICt_2
            advice = f"{ru.ADVICE_6}{income_diff_percent:.1f}%."
        else:
            spending_diff_percent = ((current_spending - total_avg_spending) / total_avg_spending * 100) if total_avg_spending > 0 else 0
            verdict = ru.VERDICT_3
            advice = f"{ru.ADVICE_7}{spending_diff_percent:.1f}%."

    raw_target = current_income * 0.2
    savings_target = int(round(raw_target / 5000) * 5000)
    goal = f"{ru.GOAL_1}{savings_target:,}{ru.GOAL_2}".replace(",", " ")

    return {
        "verdict": verdict,
        "advice": advice,
        "goal": goal,
        "budget_limits": budget_limits,
        "savings_target": savings_target
    }


def compare_budget_vs_actual(budget: dict, category_stats: dict) -> dict:

    """
    Compares planned budget with actual spending and provides category-specific analysis.

    Args:
        budget (dict): Budget recommendations from create_budget_template
        category_stats (dict): Category statistics from calculate_by_category
    Returns:
        dict: Comparison results with detailed analysis
    """

    actual_spending = {}
    for category, data in category_stats.items():
        actual_spending[category] = data["expense_total"]
    
    comparison = {}
    within_budget = []
    exceeded_budget = []
    
    for category, budget_limit in budget["budget_limits"].items():
        actual = actual_spending.get(category, 0)
        difference = budget_limit - actual
        status = True if difference >= 0 else False
        
        comparison[category] = {
            "budget": budget_limit,
            "actual": actual,
            "difference": abs(difference),
            "status": status
        }
        
        if status:
            within_budget.append(category)
        else:
            exceeded_budget.append(category)
    
    total_budget = sum(budget["budget_limits"].values())
    total_actual = sum(actual_spending.values())
    overall_status = True if total_actual <= total_budget else False
    
    return {
        "comparison": comparison,
        "within_budget": within_budget,
        "exceeded_budget": exceeded_budget,
        "total_budget": total_budget,
        "total_actual": total_actual,
        "overall_status": overall_status
    }


def print_report(stats: dict, category_stats: dict, budget: dict, budget_comparison: dict) -> None:

    """
    Function to print a summary report of financial statistics.

    Args:
        stats (dict): Basic statistics dictionary from calculate_basic_stats().
        category_stats (dict): Category statistics dictionary from calculate_by_category().
        budget (dict): Budget template dictionary from create_budget_template().
    """

    print(ru.FINANCIAL_REPORT)
    print(ru.MAIN_STATISTICS)
    print(f"{ru.INCOME}{_format_rub(stats.get("total_income"))}")
    print(f"{ru.EXPENSE}{_format_rub(stats.get("total_expense"))}")
    print(f"{ru.BALANCE}{_format_rub(stats.get("balance"))}")
    print(ru.CATEGORY_EXPENSES)
    for category, data in category_stats.items():
        print(f"  {category}: {_format_rub(data.get("expense_total"))} ({data.get("percent_of_expenses")}%)")
    print(ru.BUDGET_REPORT)
    print(budget["verdict"])
    print(budget["advice"])
    print(budget["goal"])
    if budget_comparison["overall_status"]:
        print(ru.BUDGET_REPORT_1)
    else:
        overspend = budget_comparison["total_actual"] - budget_comparison["total_budget"]
        print(f"{ru.BUDGET_REPORT_2}{_format_rub(overspend)}")


def main():

    """ 
    Main function to run the financial analysis and reporting. 
    """

    transactions = import_financial_data(r"money.csv")

    categorized_transactions = categorize_all_transactions(transactions)
    
    stats = calculate_basic_stats(categorized_transactions)
    months_analysis = analyze_by_time(categorized_transactions)
    category_stats = calculate_by_category(categorized_transactions)
    
    analysis = analyze_historical_spending(months_analysis)
    budget = create_budget_template(analysis, stats)
    budget_comparison = compare_budget_vs_actual(budget, category_stats)
    
    print_report(stats, category_stats, budget, budget_comparison)


if __name__ == "__main__":   
    main()
