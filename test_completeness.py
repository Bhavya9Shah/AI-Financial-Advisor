from tools import _check_profile_completeness

profile = {
    "age": "27",
    "monthly_income": "90000",
    "risk_tolerance": None,
    "investment_horizon_years": None,
    "monthly_expenses": None,
    "financial_goals": []
}

result = _check_profile_completeness(profile)

print(result)