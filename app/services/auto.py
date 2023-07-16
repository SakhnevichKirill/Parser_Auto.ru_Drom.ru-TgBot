from typing import Optional, SupportsIndex
from selenium.webdriver.common.by import By
from selenium.webdriver.remote import webelement
from selenium.webdriver.remote.webdriver import WebDriver
from parser import Parser
import time
import os, sys
import pandas as pd

sys.path.insert(1, os.path.join(sys.path[0], "../"))
from models import Advertisement
from database import app, conn
from bot import send_ad, escape_reserved

# from bot import send_ad


class AutoParser(Parser):
    def __init__(self, price: int, debug: Optional[bool] = False):
        Parser.__init__(self, service="auto", debug=debug)
        self.price = price
        self.driver: WebDriver
        self.advertisement = dict()
        self.url = f"https://auto.ru/moskva/cars/all/?top_days=2&price_to={self.price}&with_discount=false&sort=cr_date-desc&damage_group=ANY&page="

    def parse_specs(self, text: str) -> dict:
        spec_str_list = text.rsplit("\n")
        spec_dict = {}
        for i in range(0, len(spec_str_list), 2):
            spec_dict[spec_str_list[i]] = spec_str_list[i + 1]
        return spec_dict

    def parse_page(
        self, csv_folder_path="./data_results", save_to_csv=False, save_to_db=False
    ) -> int:
        try:
            page: int = 0
            while True:
                page += 1
                if page == 1:
                    time.sleep(1)
                    self.load_cookie(url=self.url + str(page))
                    time.sleep(2)
                else:
                    self.driver.get(url=self.url + str(page))

                # Wait for captcha solution from user
                # time.sleep(3)

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

                    # print("names count: ", len(ad_name))
                    # print("price count: ", len(ad_price))
                    # print("details count: ", len(ad_details))
                    # print("milage count: ", len(ad_milage))
                    # print("year count: ", len(ad_year))

                    assert not any(
                        len(x) != len(ad_href)
                        for x in [ad_name, ad_price, ad_details, ad_milage, ad_year]
                    ), "Error: parsing attributes len mismatch"

                    for i in range(len(ad_href)):
                        self.advertisement[ad_href[i]] = {
                            "href": ad_href[i],
                            "name": escape_reserved(ad_name[i]),
                            "price": escape_reserved(ad_price[i]),
                            "details": escape_reserved(ad_details[i]),
                            "milage": escape_reserved(ad_milage[i]),
                            "year": escape_reserved(ad_year[i]),
                        }
                        self.driver.get(url=ad_href[i])
                        specifications_url = self.driver.find_element(
                            by=By.XPATH,
                            value='//a[contains(text(),"Характеристики модели в каталоге")]',
                        )
                        specifications_url = specifications_url.get_attribute("href")
                        if specifications_url:
                            # print(specifications_url)

                            self.driver.get(url=specifications_url)
                            specification = self.driver.find_element(
                                by=By.XPATH,
                                value='//div[contains(@class,"ModificationInfo-GiDD1")]',
                            )
                            titles = self.driver.find_elements(
                                by=By.XPATH,
                                value='//h3[contains(@class,"ModificationInfo__groupName")]',
                            )
                            ad_titles = list(map(lambda x: x.text, titles))
                            text_res = specification.text
                            # text_res = text_res.replace("\n", " \n " )
                            # print(text_res)
                            # time.sleep(2)

                            text_res = escape_reserved(text_res)
                            split_text = []
                            start_index = 0
                            end_index = -1
                            for title in reversed(ad_titles):
                                start_index = text_res.find(title, 0, end_index)
                                split_text.append(text_res[start_index:end_index])
                                end_index = start_index
                            # print(len(split_text))
                            msg = ""
                            import re

                            for text in split_text:
                                text = re.sub(
                                    pattern="\n", repl="* \n", string=text, count=1
                                )
                                text_arr = text.splitlines()
                                msg += "    \n\n *" + text_arr[0] + "||"
                                for text_index in range(1, len(text_arr)):
                                    if text_index % 2 == 1:
                                        msg += "\n" + text_arr[text_index][:-1]
                                    else:
                                        msg += ": " + text_arr[text_index]
                                msg += "||"
                            self.advertisement[ad_href[i]]["modification_info"] = msg
                    if save_to_csv:
                        df = pd.DataFrame.from_dict(self.advertisement, orient="index")
                        if not os.path.exists(csv_folder_path):
                            os.makedirs(csv_folder_path)
                        df.to_csv(f"{csv_folder_path}/auto{page}.csv", index=False)

                    if save_to_db:
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
                                    modification_info=self.advertisement[key][
                                        "modification_info"
                                    ],
                                    is_send=False,
                                    service=self.service,
                                )
                                print(output)

                                ad = Advertisement.query.filter_by(href=key).first()

                                if ad.is_send is False:
                                    send_ad(
                                        href=self.advertisement[key]["href"],
                                        name=self.advertisement[key]["name"],
                                        price=self.advertisement[key]["price"],
                                        details=self.advertisement[key]["details"],
                                        service=self.service,
                                        milage=self.advertisement[key]["milage"],
                                        year=self.advertisement[key]["year"],
                                        modification_info=self.advertisement[key][
                                            "modification_info"
                                        ],
                                    )

                                    ad.is_send = True
                                    conn.session.commit()

                                else:
                                    pass

                            if output["status"] is False:
                                self.break_status = True

                if self.break_status:
                    self.break_status = False
                    break
                self.advertisement = dict()
            return page

        except Exception as e:
            print(e)
            # return e
            return page

        finally:
            self.close_parser()
            return page


if __name__ == "__main__":
    ap = AutoParser(price=8000000, debug=True)
    csv_folder_path = "./data_results"
    num_page = ap.parse_page(csv_folder_path=csv_folder_path, save_to_csv=True)
    print(num_page)
    if num_page > 0:
        for i in range(1, num_page):
            if i == 1:
                df = pd.read_csv(f"{csv_folder_path}/auto{i}.csv")
            else:
                df_next = pd.read_csv(f"{csv_folder_path}/auto{i}.csv")
                df = pd.concat([df, df_next])
        df.to_csv("auto.csv", index=False)
    print(ap.advertisement)

# if __name__ == "__main__":
#     ap = AutoParser(price=8000000, debug=True)
#     ap.parse_page(save_to_db=True)
#     print(ap.advertisement)
