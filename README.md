# Parser Auto.ru, Drom.ru, Telegram Bot

---

#### Auto.ru:

1. Необходимо сохранение cookie в сессию для обхода re-captcha
2. Все параметры поиска конфигурируются в url кроме радиуса поиска (радиус конфигурируется в cookie)
3. На последней странице поиска убирает все объявления с бесконечным поиском не попадающими под поисковый запрос

```.js
const remove = (sel) => document.querySelectorAll(sel).forEach(el => el.remove()); remove(".ListingInfiniteDesktop__snippet");
```

4. При отсутсвии элементов на странице заканчивает парсинг и заносит результат в бд (добавляет новые посты)

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

#### Get started

```.sh
python app/services/auto.py
```

##### For arch linux

```.sh
yay xvfb
yay Xephyr
```
