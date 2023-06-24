import aiohttp
import asyncio
import backoff
from bs4 import BeautifulSoup
import json
import sys

def parse_html_from_file(filename):
    with open(filename, 'r') as f:
        html = f.read()
        soup = BeautifulSoup(html, 'html.parser')
        return soup
    return None

def parse_products_from_file(filename):
    products = []
    with open(filename, 'r') as f:
        html = f.read()
        soup = BeautifulSoup(html, 'html.parser')
        for li in soup.find_all('li'):
            product = {}
            a = li.find('a')
            link = a['href']
            if link not in products:
                products.append(link)
    return products

def check_product_exists(products, product_link):
    for product in products:
        if product['link'] == product_link:
            return True
    return False

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

def generate_html_table(products, available=True):
    sorted_products = sorted(products, key=lambda p: (p['discount'], -float(p['price'])))

    table_html = '<table>\n'
    table_html += '<tr><th>Name</th><th>Link</th><th>Price</th><th>Discount</th><th>Image</th></tr>\n'

    for product in sorted_products:
        if available or product['available']:
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

product_list = []

@backoff.on_exception(backoff.expo, aiohttp.ClientError, max_time=600)
async def parse_html_from_url(url):
    async with aiohttp.ClientSession(raise_for_status=True) as session:
        async with session.get(url) as response:
            html_content = await response.text()
            return html_content

async def parse_product_table(url):
    try:
        html_content = await parse_html_from_url(url)
        soup = BeautifulSoup(html_content, 'html.parser')
        if soup:
            product = {}
            data = parse_product_data(soup)
            product['name'] = data['name']
            product['link'] = data['offers']['url']
            product['price'] = data['offers']['price'].replace('€','')
            try:
                product['discount'] = data['discount']
            except:
                percentage_text = find_percentage_text(soup)
                if percentage_text:
                    product['discount'] = percentage_text
            if len(data['image']) > 0:
                product['image'] = data['image'][0]
            try:
                product['available'] = "InStock" in data['offers']['availability']
            except:
                product['available'] = False # "SoldOut"

            print(product)

        product_list.append(product)
    except aiohttp.ClientResponseError as e:
        print(url, file=sys.stderr)
        print(e)

async def parse_product_tables_parallel(urls):
    tasks = []
    for url in urls:
        tasks.append(asyncio.create_task(parse_product_table(url)))
    await asyncio.gather(*tasks)

def main():
    # get product urls
    # TODO from url https://schneinet.de/50off.html
    product_urls = parse_products_from_file('50off.html')
    print(f"Found {len(product_urls)} product URLs")

    # fetch product pages and build product list
    asyncio.run(parse_product_tables_parallel(product_urls))
    print(f"Found {len(product_list)} product details")

    # output results
    html_table = generate_html_table(product_list)
    filename = 'products.html'
    with open(filename, 'w') as file:
        file.write(html_table)
        print(f"Product table written to {filename}")

if __name__ == '__main__':
    main()