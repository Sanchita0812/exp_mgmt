import requests

def convert_currency(amount, currency):

    if currency == 'INR':
        return amount

    url = f"https://api.exchangerate-api.com/v4/latest/{currency}"

    response = requests.get(url)

    data = response.json()

    rate = data['rates']['INR']

    converted_amount = amount * rate

    return round(converted_amount, 2)