from tools import calculate_cagr

result = calculate_cagr.invoke({
    "initial_value": 100000,
    "final_value": 350000,
    "years": 7
})

print(result)