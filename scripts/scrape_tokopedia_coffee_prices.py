"""
Scrapes Arabica/Robusta coffee product listings from Tokopedia to build the
West Java coffee price dataset (Harga_Kopi_Jabar.csv) used by the Tableau
dashboard's treemap visualization.

Usage:
    python scrape_tokopedia_coffee_prices.py
"""
import os
import time

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class Scraper:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.driver = webdriver.Chrome(options=options)

    def get_data(self, search_query, pages):
        data = []
        for page_num in range(1, pages + 1):
            url = f"https://www.tokopedia.com/search?q={search_query}&page={page_num}"
            self.driver.get(url)
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#zeus-root"))
            )

            # Scroll to trigger lazy-loaded product cards
            scroll_steps = 12 if page_num == pages else 15
            for _ in range(scroll_steps):
                self.driver.execute_script("window.scrollBy(0,500)")
                time.sleep(1)

            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            for item in soup.find_all("div", class_="css-qa82pd"):
                product_name = item.find(
                    "div", class_="prd_link-product-name css-3um8ox"
                ).text.strip()
                price = item.find(
                    "div", class_="prd_link-product-price css-h66vau"
                ).text.strip()

                rate_tag = item.find("span", class_="prd_rating-average-text css-t70v7i")
                rate = rate_tag.text.strip() if rate_tag else ""

                sold_tag = item.find("span", class_="prd_label-integrity css-1sgek4h")
                sold = sold_tag.text.strip() if sold_tag else 0

                link_tag = item.find("a", class_="pcv3__info-content")
                product_link = link_tag["href"] if link_tag else ""

                image_tag = item.find("img", class_="css-1q90pod")
                image_url = image_tag["src"] if image_tag else ""

                location_tag = item.find(
                    "span", class_="prd_link-shop-loc css-1kdc32b flip"
                )
                location = location_tag.text.strip() if location_tag else ""

                seller_tag = item.find(
                    "span", class_="prd_link-shop-name css-1kdc32b flip"
                )
                seller = seller_tag.text.strip() if seller_tag else ""

                data.append(
                    {
                        "Penjual": seller,
                        "Lokasi": location,
                        "Produk": product_name,
                        "Harga": price,
                        "Rate": rate,
                        "Terjual": sold,
                        "Link": product_link,
                        "Image_URL": image_url,
                    }
                )
            time.sleep(1)

        self.driver.close()
        return data


if __name__ == "__main__":
    search_query = "Kopi+Arabika+1kg"
    pages = 1

    scraper = Scraper()
    data = scraper.get_data(search_query, pages)
    df = pd.DataFrame(data)

    # Output saved relative to this script, inside ../data/
    output_dir = os.path.join(os.path.dirname(__file__), "..", "data", "scraped")
    os.makedirs(output_dir, exist_ok=True)

    csv_filename = f"Produk {search_query.replace('+', ' ').title()} Tokopedia.csv"
    csv_path = os.path.join(output_dir, csv_filename)

    df.to_csv(csv_path, index=False)
    print(f"Data exported to {csv_path}")
