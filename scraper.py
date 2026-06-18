import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import json
import os
import re

# ==================================================
# CONFIGURATION
# 

BOOKS_URL = "https://books.toscrape.com/"
BASE_CURRENCY = "GBP"

# ==================================================
# GET TARGET CURRENCY FROM USER
# ==================================================

target_currency = input(
    "Enter target currency (USD, EUR, KES, CAD, etc.): "
).upper()

# ==================================================
# GET EXCHANGE RATE
# ==================================================

def get_exchange_rate(base_currency, target_currency):
    """
    Fetch exchange rate from API
    """

    try:
        api_url = f"https://open.er-api.com/v6/latest/{base_currency}"

        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        data = response.json()

        if "rates" not in data:
            raise Exception("Exchange rates not found.")

        if target_currency not in data["rates"]:
            raise Exception(
                f"{target_currency} is not a valid currency code."
            )

        return data["rates"][target_currency]

    except requests.exceptions.RequestException as e:
        print(f"\nConnection error while fetching exchange rate:\n{e}")
        return None

    except Exception as e:
        print(f"\nCurrency conversion error:\n{e}")
        return None


# ==================================================
# SCRAPE BOOK DATA
# ==================================================

def scrape_books(number_of_books=10):
    """
    Scrape books from BooksToScrape
    """

    books = []

    try:
        response = requests.get(BOOKS_URL, timeout=10)

        response.encoding = "utf-8"

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        products = soup.select("article.product_pod")

        for product in products[:number_of_books]:

            title = product.h3.a["title"].strip()

            price_text = product.select_one(".price_color").text

            # Remove £, Â and any non-numeric characters
            clean_price = float(
                re.sub(r"[^0-9.]", "", price_text)
            )

            books.append(
                {
                    "Book Title": title,
                    "Original Price (GBP)": clean_price
                }
            )

        return books

    except requests.exceptions.RequestException as e:
        print(f"\nWebsite connection error:\n{e}")
        return []

    except Exception as e:
        print(f"\nScraping error:\n{e}")
        return []


# ==================================================
# CONVERT PRICES
# ==================================================

def convert_prices(data, exchange_rate, target_currency):
    """
    Convert prices to target currency
    """

    for item in data:

        converted_price = (
            item["Original Price (GBP)"] * exchange_rate
        )

        item[f"Converted Price ({target_currency})"] = round(
            converted_price,
            2
        )

    return data


# ==================================================
# SAVE FILES
# ==================================================

def save_files(data):
    """
    Save CSV and JSON
    """

    os.makedirs("output", exist_ok=True)

    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    csv_file = f"output/products_{timestamp}.csv"
    json_file = f"output/products_{timestamp}.json"

    df = pd.DataFrame(data)

    df.to_csv(csv_file, index=False)

    with open(json_file, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

    return csv_file, json_file, df


# ==================================================
# DISPLAY TABLE
# ==================================================

def display_table(df):

    print("\n")
    print("=" * 80)
    print("PRODUCT PRICE TABLE")
    print("=" * 80)

    print(df)

    print("=" * 80)


# ==================================================
# PLOT CHART
# ==================================================

def plot_chart(df, target_currency):

    try:

        original_column = "Original Price (GBP)"
        converted_column = (
            f"Converted Price ({target_currency})"
        )

        plt.figure(figsize=(12, 6))

        plt.bar(
            df["Book Title"],
            df[original_column],
            label="GBP"
        )

        plt.bar(
            df["Book Title"],
            df[converted_column],
            label=target_currency,
            alpha=0.7
        )

        plt.title(
            "Original vs Converted Prices"
        )

        plt.xlabel("Books")

        plt.ylabel("Price")

        plt.xticks(rotation=90)

        plt.legend()

        plt.tight_layout()

        plt.show()

    except Exception as e:
        print(f"\nChart error:\n{e}")


# ==================================================
# MAIN PROGRAM
# ==================================================

def main():

    print("\nScraping books...\n")

    books = scrape_books(10)

    if not books:
        print("No books found.")
        return

    print("Getting exchange rate...\n")

    exchange_rate = get_exchange_rate(
        BASE_CURRENCY,
        target_currency
    )

    if exchange_rate is None:
        return

    print(
        f"1 {BASE_CURRENCY} = "
        f"{exchange_rate} {target_currency}"
    )

    converted_books = convert_prices(
        books,
        exchange_rate,
        target_currency
    )

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    for item in converted_books:
        item["Conversion Timestamp"] = timestamp

    csv_file, json_file, df = save_files(
        converted_books
    )

    display_table(df)

    print("\nFiles created successfully:")
    print(csv_file)
    print(json_file)

    plot_chart(df, target_currency)


# ==================================================
# RUN APPLICATION
# ==================================================

if __name__ == "__main__":
    main()