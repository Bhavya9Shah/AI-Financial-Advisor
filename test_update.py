from tools import update_user_profile

result = update_user_profile.invoke({
    "field": "age",
    "value": 27
})

print(result)