TEST_CASES = [

    {
        "name": "Profile Retrieval",
        "query": "What do you know about me?",
        "expected_tools": ["get_user_profile"],
        "response_should_contain": [
            "profile"
        ]
    },

    {
        "name": "Stock Lookup",
        "query": "What is the current price of INFY.NS?",
        "expected_tools": ["get_stock_info"],
        "expected_args": {
            "ticker": "INFY.NS"
        },
        "response_should_contain": [
            "INFY",
            "price",
            "stock"
        ]
    },

    {
        "name": "SIP Calculator",
        "query": "If I invest ₹5000/month for 20 years at 12%, how much will I get?",
        "expected_tools": ["calculate_sip_returns"],
        "expected_args": {
            "monthly_amount": 5000,
            "annual_rate": 12,
            "years": 20
        },
        "response_should_contain": [
            "future",
            "value",
            "investment",
            "₹"
        ]
    },

    {
        "name": "CAGR Calculator",
        "query": "My investment grew from ₹50,000 to ₹2,00,000 in 10 years. What's the CAGR?",
        "expected_tools": ["calculate_cagr"],
        "expected_args": {
            "initial_value": 50000,
            "final_value": 200000,
            "years": 10
        },
        "response_should_contain": [
            "CAGR",
            "%",
            "annual",
            "growth"
        ]
    },

    {
        "name": "Financial News",
        "query": "What is the latest news about TCS?",
        "expected_tools": ["get_financial_news"],
        "expected_args": {
            "ticker": "TCS.NS"
        },
        "response_should_contain": [
            "TCS",
            "news",
            "sentiment",
            "headline"
        ]
    }

]