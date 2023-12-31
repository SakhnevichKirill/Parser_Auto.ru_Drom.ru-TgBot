# Parser Auto.ru, Drom.ru, Telegram Bot

---

#### Auto.ru:

1. Необходимо сохранение cookie в сессию для обхода re-captcha
2. Все параметры поиска конфигурируются в url кроме радиуса поиска (радиус конфигурируется в cookie)
3. На последней странице поиска убирает все объявления с бесконечным поиском не попадающими под поисковый запрос

```.js
const remove = (sel) => document.querySelectorAll(sel).forEach(el => el.remove()); remove(".ListingInfiniteDesktop__snippet");
```

4. Скрол страниц идет до первого совпадения объявления с бд. При отсутсвии элементов на странице заканчивает парсинг и заносит результат в бд (добавляет новые посты)

---

#### Drom.ru:

1. Все параметры поиска конфигурируются в url
2. Скрол страниц идет до первого совпадения объявления с бд

---

#### Install deps

1. Make venv

```.sh
python -m venv venv
```

2. Activate venv

```.sh
source venv/bin/activate
```

3. Install deps

```.sh
pip install -r requirements.txt
```

---

#### Конфигурация бд

1. Очистите занятые докер контейнеры через docker-station или мануально

```.sh
sudo docker stop $(sudo docker ps -a -q)
sudo docker rm $(sudo docker ps -a -q)
```

2. Билд и поднятие докера с postgresql и pgAdmin4

```.sh
 docker compose -f docker-compose.yml build
 docker compose -f docker-compose.yml up -d
```

3. Чекните IP - адресс поднятого докера для соединения с бд

```.sh
 docker inspect pgdb | grep IPAddress
 ------------Output-----------------
"SecondaryIPAddresses": null,
"IPAddress": "",
        "IPAddress": "172.29.0.2",
```

4. Измените ip_address подключения к бд в app.database.config

```.py
ip_address = 172.29.0.2
```

##### root:root - user/pass | database_name - должны быть аналогичны в docker-compose.yml

5. Создайте таблицы в бд

```.sh
cd app/database
python -m flask commands create_db
```
6. Подколючиться и просмотреть содержимое
```CMD
psql postgresql://root:root@172.29.0.2:5432/autoparser
\c autoparser
\dt
```

```SQL
SELECT * FROM advertisement;
```

7. PgAdmin: `http://localhost:5050`

---


#### Get started

Parsing Auto.ru to csv
```.sh
python app/services/auto.py
```
---

Подготовьте токен бота
```.sh
echo "telegram_bot_token=<bot_token>" > /.env
```

Подключитесь к боту
```.sh
python app/services/bot.py
```

Старт парсинга из Drom.ru и Auto.ru в бд
```.sh
python app/services/sheduler.py
```
---



#### Создание сессии с cookie для Auto.ru

##### app.services.parser

```.py
p = Parser()
p.create_session(url = <auto.ru search configured url>)
```

##### Pass Re-Captcha and configure search radius; Session will be saved in app.sessions.auto

---

#### Edit Selenium webdriver source for moving geckodriver.log in logs folder (by defualt cant change log dir)

```.txt
Edit in webdriver.py (from webdriver.Firefox) DEFAULT_SERVICE_LOG_PATH to = "logs/geckodriver.log"
```

#### Install deps on your system for virtual display (requires by cli server)

##### For arch linux

```.sh
yay xvfb
yay Xephyr
```
