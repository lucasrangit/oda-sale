# from https://www.pythonmorsels.com/p/2v4yk/
import requests
import pyperclip

cookies = {
    'sessionid': 'yhkn5fnrbib9a6b2o4v4al47hj6lxlq9',
}

all_products = []
halfprice_products = []
counter = 0
more = True

# Get all products
while more and counter < 49:
    counter += 1
    print(f"\rRufe Seite {counter} ab...", end="")
    url = f"https://oda.com/tienda-web-api/v1/search/mixed/?q=angebot&size=99&page={counter}&type=product"
    response = requests.get(url, cookies=cookies)
    data = response.json()
    more = data["attributes"]["has_more_items"]
    for item in data["items"]:
        all_products.append(item)

# Filter out those with 50% off and availability
for product in all_products:
    discount = product["attributes"]["discount"]["description_short"]
    is_available = product["attributes"]["availability"]["is_available"]
    if discount == "-50%" and is_available:
        halfprice_products.append(product)

sorted_list = sorted(halfprice_products, key=lambda d: d['attributes']['gross_price'])

html = '<html lang="de"><head><meta charset="utf-8"><title>50% Rabatt</title></head><body><ul>'
for product in sorted_list:
    name = product["attributes"]["name"]
    price = product["attributes"]["gross_price"]
    url = product["attributes"]["front_url"]
    html_element = f'<li><a href="{url}">{name}</a> für {price}€</li>'
    html += html_element
html += "</body></ul>"

pyperclip.copy(html)
print("\nHTML in Zwischenablage kopiert.")