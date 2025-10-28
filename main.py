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


def read_csv_file(filename: str) -> list:

    """
     Read a CSV file and return its contents as a list of dictionaries.

        Args:
            filename (str): Path to the CSV file.
        Returns:
            list: List of rows as dictionaries.
    """

    if not os.path.exists(filename):
        raise FileNotFoundError(f"Файл не найден: {filename}")
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
        raise FileNotFoundError(f"Файл не найден: {filename}")
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
        raise ValueError("Поддерживаются только .csv и .json")

    rows = []
    for r in raw:
        date = r["date"]
        amount = float(r["amount"])
        desc = r.get("description", "") or ""
        typ = r.get("type", "") or ("расход" if amount < 0 else "доход")
        rows.append({"date": date, "amount": amount, "description": desc, "type": typ})
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
        "expense_count": expense_count,
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

        category_totals[category] += amount
        category_counts[category] += 1

        if amount < 0:
            expense = abs(amount)
            category_expense_totals[category] += expense
            total_expenses += expense

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
            "percent_of_expenses": round(percent, 2),
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
            "top_categories": top,
        }

    return result


def analyze_historical_spending(transactions: list) -> dict:

    """
    Analyzes the user's transaction history:
    # 1. Calculates average monthly spending by category
    # 2. Identifies seasonal patterns
    # 3. Determines which categories have the highest spending
    # 4. Returns planning recommendations
    Args:
        transactions (list): list with numerical values ​​of transactions
    Returns:
        analysis (dict): A dictionary containing average costs, seasonal patterns,the
        user's most expensive categories, and budget planning recommendations.
    """

    monthly_stats = {}
    for transaction in transactions:
        date = transaction["date"]
        month = date[:7]
        category = transaction["category"]
        amount = abs(transaction["amount"])
        
        if month not in monthly_stats:
            monthly_stats[month] = {}
        if category not in monthly_stats[month]:
            monthly_stats[month][category] = 0
        monthly_stats[month][category] += amount
    

    category_totals = {}
    category_counts = {}
    for month, categories in monthly_stats.items():
        for category, amount in categories.items():
            if category not in category_totals:
                category_totals[category] = 0
                category_counts[category] = 0
            category_totals[category] += amount
            category_counts[category] += 1
    
    average_monthly = {}
    for category in category_totals:
        average_monthly[category] = category_totals[category] / category_counts[category]
    
    seasonal_patterns = {}
    for month in monthly_stats:
        seasonal_patterns[month] = sum(monthly_stats[month].values())
    
    sorted_categories = sorted(average_monthly.items(), key=lambda i: i[1], reverse=True)
    top_categories = {}
    for i in range(min(3, len(sorted_categories))):
        category, amount = sorted_categories[i]
        top_categories[category] = amount
    
    recommendations = []
    if top_categories:
        first_category = list(top_categories.items())[0]
        recommendations.append(f"Самые крупные траты: {first_category[0]} ({first_category[1]:.0f} руб/мес)")

    analysis = {
        "average_monthly_spending": average_monthly,
        "seasonal_patterns": seasonal_patterns,
        "top_categories": top_categories,
        "recommendations": recommendations
    }
    return analysis


def create_budget_template(analysis: dict) -> dict:

    """
    Offers limits by category (10% less than average), takes into account the user's 
    income (we assume a fixed income), and adds a "savings" category (20% of income).

    Args:
        analysis (dict): A dictionary containing average costs, seasonal patterns,the
        user's most expensive categories, and budget planning recommendations.
    Returns:
        dict: A dictionary containing the user's income, budget limits by category, and the user's savings amount.
    """

    avg_spending = analysis["average_monthly_spending"]
    budget_limits = {}
    for category, avg_amount in avg_spending.items():
        budget_limits[category] = round(avg_amount * 0.9)
    
    monthly_income = 50000 #здесь доход пользователя надо
    
    savings_target = monthly_income * 0.2
    budget_limits["накопления"] = savings_target
    
    return {
        "monthly_income": monthly_income,
        "budget_limits": budget_limits,
        "savings_target": savings_target
    }


def compare_budget_vs_actual(budget: dict, actual_transactions: list) -> dict:

    """
    Compares planned budget with actual spending, calculates expenses by category, 
    determines where the user stayed within budget and where they exceeded it.
    
    Args:
        budget (dict): A dictionary containing the user's income, budget limits by category, 
                      and savings target
        actual_transactions (list): A list of transactions with categories and amounts 
                                   for the period being analyzed
                                   
    Returns:
        dict: A dictionary containing detailed comparison by category, lists of categories 
              within and exceeded budget, and total amounts
    """

    actual_spending = {}
    for transaction in actual_transactions:
        category = transaction["category"]
        amount = abs(transaction["amount"])
        if category not in actual_spending:
            actual_spending[category] = 0
        actual_spending[category] += amount
    
    comparison = {}
    for category, budget_limit in budget["budget_limits"].items():
        actual = actual_spending.get(category, 0)
        difference = budget_limit - actual
        status = "в рамках бюджета" if difference >= 0 else "превышение"
        
        comparison[category] = {
            "budget": budget_limit,
            "actual": actual,
            "difference": difference,
            "status": status
        }
    
    within_budget = []
    exceeded_budget = []
    
    for category, data in comparison.items():
        if data["status"] == "в рамках бюджета":
            within_budget.append(category)
        else:
            exceeded_budget.append(category)
    

    return {
        "comparison": comparison,
        "within_budget": within_budget,
        "exceeded_budget": exceeded_budget,
        "total_budget": sum(budget["budget_limits"].values()),
        "total_actual": sum(actual_spending.values())
    }


def print_report(stats: dict, category_stats: dict, budget: dict) -> None:

    """
    Function to print a summary report of financial statistics.

    Args:
        stats (dict): Basic statistics dictionary from calculate_basic_stats().
        category_stats (dict): Category statistics dictionary from calculate_by_category().
        budget (dict): Budget template dictionary from create_budget_template().
    """

    print("=== ФИНАНСОВЫЙ ОТЧЕТ ===\n")
    print("ОСНОВНЫЕ ПОКАЗАТЕЛИ:")
    for key, value in stats.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    print("\nРАСХОДЫ ПО КАТЕГОРИЯМ:")
    for category, data in category_stats.items():
        print(f"  Category: {category}")
        for key, value in data.items():
            print(f"    {key.replace('_', ' ').title()}: {value}")
    print("\nРЕКОМЕНДАЦИИ ПО БЮДЖЕТУ:")
    for category, amount in budget.items():
        print(f"  {category}: {amount}")


def main():
    transactions = import_financial_data("my_money.csv")

    categorized_transactions = categorize_all_transactions(transactions)
    
    stats = calculate_basic_stats(categorized_transactions)
    category_stats = calculate_by_category(categorized_transactions)
    
    analysis = analyze_historical_spending(categorized_transactions)
    budget = create_budget_template(analysis)
    
    print_report(stats, category_stats, budget)


if __name__ == "__main__":   
    main()
