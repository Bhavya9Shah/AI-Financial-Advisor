TEST_CASES = [

    {
        "name": "Profile Retrieval",
        "query": "What do you know about me?",
        "expected_tools": ["get_user_profile"]
    },

    {
        "name": "Stock Lookup",
        "query": "What is the current price of INFY.NS?",
        "expected_tools": ["get_stock_info"]
    },

    {
        "name": "SIP Calculator",
        "query": "If I invest ₹5000/month for 20 years at 12%, how much will I get?",
        "expected_tools": ["calculate_sip_returns"]
    },

    {
        "name": "CAGR Calculator",
        "query": "My investment grew from ₹50,000 to ₹2,00,000 in 10 years. What's the CAGR?",
        "expected_tools": ["calculate_cagr"]
    },
    
    {
    "name": "Financial News",
    "query": "What is the latest news about TCS?"
    }
]