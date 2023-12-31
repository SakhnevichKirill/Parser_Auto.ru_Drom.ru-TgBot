from typing import Optional
from selenium.webdriver.common.by import By
from parser import Parser
import time

import os, sys

sys.path.insert(1, os.path.join(sys.path[0], "../"))
from models import Advertisement
from database import app, conn
from bot import send_ad, escape_reserved


class DromParser(Parser):
    def __init__(self, price: int, debug: Optional[bool] = False):
        Parser.__init__(self, service="drom", debug=debug)
        self.price = price
        self.advertisement = dict()
        self.break_status = False

    def parse_page(self):
        try:
            page = 0
            while True:
                page += 1
                url = f"https://moscow.drom.ru/auto/all/page{page}/?maxprice={self.price}&ph=1&unsold=1&distance=100"
                self.driver.get(url=url)

                href = self.driver.find_elements(
                    by=By.XPATH, value='//a[@data-ftid="bulls-list_bull"]'
                )
                price = self.driver.find_elements(
                    by=By.XPATH, value='//span[@data-ftid="bull_price"]'
                )
                title = self.driver.find_elements(
                    by=By.XPATH, value='//span[@data-ftid="bull_title"]'
                )
                details = self.driver.find_elements(
                    by=By.XPATH, value='//div[@class="css-1fe6w6s e162wx9x0"]'
                )

                ad_href = list(map(lambda x: x.get_attribute("href"), href))
                ad_price = list(map(lambda x: x.text, price))
                ad_details = list(map(lambda x: x.text, details))
                ad_title = list(map(lambda x: x.text, title))

                print("href count: ", len(ad_href))
                print("price count: ", len(ad_price))
                print("details count: ", len(ad_details))
                print("names count: ", len(ad_title))
                # print("milage count: ", len(ad_milage))
                # print("year count: ", len(ad_year))

                for i in range(len(ad_href)):
                    self.advertisement[ad_href[i]] = {
                        "href": ad_href[i],
                        "name": escape_reserved(ad_title[i]),
                        "price": escape_reserved(ad_price[i]),
                        "details": escape_reserved(ad_details[i]),
                    }

                with app.app_context():
                    app.config.from_pyfile("config.py")
                    conn.init_app(app)

                    for key, value in self.advertisement.items():
                        output = Advertisement().create(
                            href=self.advertisement[key]["href"],
                            title=self.advertisement[key]["name"],
                            price=self.advertisement[key]["price"],
                            details=self.advertisement[key]["details"],
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

        except Exception as e:
            print(e)
            return e

        finally:
            self.close_parser()


if __name__ == "__main__":
    dp = DromParser(price=8000000, debug=True)
    dp.parse_page()
    print(dp.advertisement)
