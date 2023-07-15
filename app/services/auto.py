from typing import Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.remote import webelement
from parser_1 import Parser
import time
import os, sys
import pandas as pd

sys.path.insert(1, os.path.join(sys.path[0], "../"))
from models import Advertisement
from database import app, conn

# from bot import send_ad


class AutoParser(Parser):
    def __init__(self, price: int, debug: Optional[bool] = False):
        Parser.__init__(self, service="auto", debug=debug)
        self.price = price
        self.advertisement = dict()
        self.url = f"https://auto.ru/moskva/cars/all/?top_days=2&price_to={self.price}&with_discount=false&sort=cr_date-desc&damage_group=ANY&page="

    def parse_specs(self, text: str) -> dict:
        spec_str_list = text.rsplit("\n")
        spec_dict = {}
        for i in range(0, len(spec_str_list), 2):
            spec_dict[spec_str_list[i]] = spec_str_list[i + 1]
        return spec_dict

    def parse_page(self) -> int:
        try:
            page: int = 0
            while True:
                page += 1
                if page == 1:
                    self.load_cookie(url=self.url + str(page))
                else:
                    self.driver.get(url=self.url + str(page))
                time.sleep(5)
                # delete infinity advertisement scrolling
                self.driver.execute_script(
                    'const remove = (sel) => document.querySelectorAll(sel).forEach(el => el.remove()); remove(".ListingInfiniteDesktop__snippet");'
                )
                # self.driver.get_log('browser')
                href = self.driver.find_elements(
                    by=By.XPATH, value='//a[@class="Link ListingItemTitle__link"]'
                )
                if len(href) != 0:
                    price = self.driver.find_elements(
                        by=By.XPATH,
                        value='//div[contains(@class, "ListingItem__priceBlock")]',
                    )
                    tech_details = self.driver.find_elements(
                        by=By.XPATH,
                        value='//div[@class="ListingItemTechSummaryDesktop ListingItem__techSummary"]',
                    )
                    mileage = self.driver.find_elements(
                        by=By.XPATH, value='//div[@class="ListingItem__kmAge"]'
                    )
                    year = self.driver.find_elements(
                        by=By.XPATH, value='//div[@class="ListingItem__yearBlock"]'
                    )

                    ad_href = list(map(lambda x: x.get_attribute("href"), href))
                    ad_name = list(map(lambda x: x.text, href))
                    ad_price = list(map(lambda x: x.text, price))
                    ad_details = list(map(lambda x: x.text, tech_details))
                    ad_milage = list(map(lambda x: x.text, mileage))
                    ad_year = list(map(lambda x: x.text, year))

                    print("names count: ", len(ad_name))
                    print("price count: ", len(ad_price))
                    print("details count: ", len(ad_details))
                    print("milage count: ", len(ad_milage))
                    print("year count: ", len(ad_year))

                    assert not any(
                        len(x) != len(ad_href)
                        for x in [ad_name, ad_price, ad_details, ad_milage, ad_year]
                    ), "Error: parsing attributes len mismatch"

                    for i in range(2):
                        self.advertisement[ad_href[i]] = {
                            "href": ad_href[i],
                            "name": ad_name[i],
                            "price": ad_price[i],
                            "details": ad_details[i],
                            "milage": ad_milage[i],
                            "year": ad_year[i],
                        }
                        self.driver.get(url=ad_href[i])
                        specifications_urls = self.driver.find_elements(
                            by=By.XPATH,
                            value='//a[contains(text(),"Характеристики модели в каталоге")]',
                        )
                        specifications_urls = list(
                            map(lambda x: x.get_attribute("href"), specifications_urls)
                        )
                        if len(specifications_urls) != 0:
                            print(len(specifications_urls))
                            self.driver.get(url=specifications_urls[0])

                            specifications = self.driver.find_elements(
                                by=By.XPATH,
                                value='//dl[contains(@class,"list-values clearfix")]',
                            )
                            specifications_dict_list = list(
                                map(lambda x: self.parse_specs(x.text), specifications)
                            )
                            for specifications_dict in specifications_dict_list:
                                self.advertisement[ad_href[i]] = (
                                    self.advertisement[ad_href[i]] | specifications_dict
                                )

                        print(self.advertisement[ad_href[i]])
                        time.sleep(3)

                    print(0)

                    df = pd.DataFrame.from_dict(self.advertisement, orient="index")
                    df.to_csv(f"./data_results/auto{page}.csv", index=False)

                    with app.app_context():
                        app.config.from_pyfile("config.py")
                        conn.init_app(app)

                        for key, value in self.advertisement.items():
                            output = Advertisement().create(
                                href=self.advertisement[key]["href"],
                                title=self.advertisement[key]["name"],
                                price=self.advertisement[key]["price"],
                                details=self.advertisement[key]["details"],
                                milage=self.advertisement[key]["milage"],
                                year=self.advertisement[key]["year"],
                                is_send=False,
                                service=self.service,
                            )
                            print(output)

                            ad = Advertisement.query.filter_by(href=key).first()

                            if ad.is_send is False:
                                print(
                                    href=self.advertisement[key]["href"],
                                    name=self.advertisement[key]["name"],
                                    price=self.advertisement[key]["price"],
                                    details=self.advertisement[key]["details"],
                                    service=self.service,
                                    milage=self.advertisement[key]["milage"],
                                    year=self.advertisement[key]["year"],
                                )

                                ad.is_send = True
                                conn.session.commit()

                            else:
                                pass
                else:
                    break
            return page

        except Exception as e:
            print(e)
            # return e
            return page

        finally:
            self.close_parser()
            return page


ap = AutoParser(price=8000000, debug=True)
num_page = ap.parse_page()
print(num_page)
if num_page > 0:
    for i in range(1, num_page):
        if i == 1:
            df = pd.read_csv(f"auto{i}.csv")
        else:
            df_next = pd.read_csv(f"auto{i}.csv")
            df = pd.concat([df, df_next])
    df.to_csv("auto.csv", index=False)
# print(ap.advertisement)
