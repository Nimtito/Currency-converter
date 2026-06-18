import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import json
import os

URL = "https://books.toscrape.com/catalogue/page-1.html"
API = "https://open.er-api.com/v6/latest/GBP"
TARGET = "USD"


def get_rate():
    try:
        r = requests.get(API, timeout=10)
        r.raise_for_status()
        return r.json()["rates"][TARGET]
    except:
        print("Error fetching rate")
        return None


def scrape():
    try:
        r = requests.get(URL, timeout=10)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        books = soup.select("article.product_pod")

        data = []

        for b in books[:10]:
            title = b.h3.a["title"]
            price = float(b.select_one(".price_color").text.replace("£", ""))

            data.append({
                "name": title,
                "price_gbp": price
            })

        return data

    except Exception as e:
        print("Scraping error:", e)
        return []


def convert(data, rate):
    for i in data:
        i["price_usd"] = round(i["price_gbp"] * rate, 2)
    return data


def save(data):
    os.makedirs("output", exist_ok=True)

    time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    df = pd.DataFrame(data)

    csv_path = f"output/products_{time}.csv"
    json_path = f"output/products_{time}.json"

    df.to_csv(csv_path, index=False)

    with open(json_path, "w") as f:
        json.dump(data, f, indent=4)

    return df, csv_path, json_path


def main():
    print("Scraping...")

    data = scrape()
    if not data:
        return

    rate = get_rate()
    if not rate:
        return

    data = convert(data, rate)

    df, csv_file, json_file = save(data)

    print("\nDONE")
    print(df)
    print(csv_file)
    print(json_file)


main()