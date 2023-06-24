from bs4 import BeautifulSoup
import json
import requests

def parse_html_from_url(url):
    response = requests.get(url)
    if response.status_code == 200:
        html = response.content
        soup = BeautifulSoup(html, 'html.parser')
        return soup
    return None

def parse_html_from_file(filename):
    with open(filename, 'r') as f:
        html = f.read()
        soup = BeautifulSoup(html, 'html.parser')
        return soup
    return None

def check_product_exists(products, product_link):
    for product in products:
        if product['link'] == product_link:
            return True
    return False

def parse_product_table(soup):
    product_list = []

    for li in soup.find_all('li'):
        product = {}
        a = li.find('a')
        product['name'] = a.text.replace('\n', ' ').replace('  ',' ')
        product['link'] = a['href']
        product['price'] = li.contents[-1].replace('für ', '').replace('für','').replace('\n', ' ').replace('€','').strip()

        if check_product_exists(product_list, product['link']):
            continue

        product_soup = parse_html_from_url(product['link'])
        if product_soup:
            # discount
            percentage_text = find_percentage_text(product_soup)
            if percentage_text:
                product['discount'] = percentage_text

            # image
            image_url = find_image_url(product_soup)
            if image_url:
                product['image'] = image_url

            data = parse_product_data(product_soup)

            # more accurate image
            if len(data['image']) > 0:
                product['image'] = data['image'][0]

            # availability
            try:
                product['available'] = "InStock" in data['offers']['availability']
            except:
                product['available'] = False # "SoldOut"

        print(product)

        product_list.append(product)

        # if len(product_list) > 5:
        #     break

    return product_list

def find_image_url(soup):
    image_element = soup.find('img', class_='k-image k-image--contain')
    if image_element:
        image_url = image_element['src']
        return image_url
    return None

def find_percentage_text(soup):
    element = soup.find('div', class_='styles_discountBubble__Y0zBY')
    if element:
        percentage_text = element.text.strip()
        return percentage_text
    return None

def generate_html_table(products):
    sorted_products = sorted(products, key=lambda p: (p['discount'], -float(p['price'])))

    table_html = '<table>\n'
    table_html += '<tr><th>Name</th><th>Link</th><th>Price</th><th>Discount</th><th>Image</th></tr>\n'

    for product in sorted_products:
        available = product['available']
        if available:
            name = product['name']
            link = product['link']
            price = product['price']
            discount = product['discount']
            image = product['image']
            image_width = 400
            table_html += f'<tr><td>{name}</td><td><a href="{link}">{link}</a></td><td>{price}</td><td>{discount}</td><td><img src="{image}" width="{image_width}"></td></tr>\n'

    table_html += '</table>'

    return table_html

def parse_product_data(soup):
    script_tag = soup.find('script', {'type': 'application/ld+json'})
    if script_tag:
        json_str = script_tag.string.strip()
        data = json.loads(json_str)
        if data.get('@type') == 'Product':
            return data
    return None

def main():
    # from file
    soup = parse_html_from_file('50off.html')

    # from url
    # soup = parse_html_from_url('https://schneinet.de/50off.html')

    if soup:
        products = parse_product_table(soup)

        html_table = generate_html_table(products)
        filename = 'products.html'
        with open(filename, 'w') as file:
            file.write(html_table)

            print(f"Product table written to {filename}")

if __name__ == '__main__':
    main()