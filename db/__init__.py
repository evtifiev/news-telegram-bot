import sqlite3
from datetime import datetime, timedelta
import time

class DB:
    def __init__(self, dbname="newsbot.db"):
        self.dbname = dbname
        self.connect = sqlite3.connect(dbname, check_same_thread=False)
        self.cursor = self.connect.cursor()
    # Инициализация и создание таблицы в БД
    def setup(self):
        """Создаем таблицы subscribers(подписчики), feeds(новостные ленты) и news(новости)"""
        """
        Создадим таблицу подписчиками subscribers
        subscriber_id - уникальный идентификатор
        user_id - уникальный идентификатор пользователя в Telegram
        is_admin - статус администратора
        """
        subscriber_table = '''
            CREATE TABLE IF NOT EXISTS subscribers (
                subscriber_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                is_admin INTEGER DEFAULT 0 NOT NULL,
                is_search INTEGER DEFAULT 0 NOT NULL
                )
        '''

        """
        Создадим таблицу с новостными лентами feeds
        feed_id - уникальный идентификатор
        title - название издания
        url - адрес издания
        rating - рейтинг
        """

        feed_table = '''
            CREATE TABLE IF NOT EXISTS feeds (
                feed_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE,
                url TEXT NOT NULL UNIQUE,
                rating INTEGER NOT NULL
                )
            '''
        
        """ 
        Создадим таблицу с новостями news
        news_id - идентификатор
        public_date - дата публикации
        title - заголовок новости
        description - краткое описание новости
        link - ссылка на полную новость
        """
        news_table = '''
            CREATE TABLE IF NOT EXISTS news(
                news_id INTEGER PRIMARY KEY AUTOINCREMENT,
                feed_id INTEGER NOT NULL,
                public_date TEXT NOT NULL,
                title TEXT NOT NULL COLLATE NOCASE,
                description TEXT NOT NULL COLLATE NOCASE,
                link TEXT NOT NULL,
                CONSTRAINT fk_feeds
                    FOREIGN KEY (feed_id)
                    REFERENCES feeds(feed_id)
                    ON DELETE CASCADE
            )
        '''
        self.cursor.execute(subscriber_table)
        self.cursor.execute(feed_table)
        self.cursor.execute(news_table)
        self.connect.commit()

    # ---------- Работа с таблицей Подписчики ---
    def add_subscriber(self, user_id):
        """ Добавление нового подписчика в таблицу subscribers  БД"""

        # Если подписчик администратор, тогда проверяем его идентификатор
        # и добавляем в БД как администратора бота
        admin_lst = [1381101,]  # Задаем идентификаторы администраторов
        if user_id in admin_lst:
            query = "INSERT INTO subscribers (user_id, is_admin) VALUES (?, 1)"
        else: 
            query = "INSERT INTO subscribers (user_id) VALUES (?)"
        args = (user_id, )
        try:
            self.cursor.execute(query, args)
            self.connect.commit()
        except:
            return None

    def is_admin(self, user_id):
        """Проверим статус подписчика"""
        query = "SELECT is_admin FROM subscribers WHERE user_id = (?)"
        args = (user_id, )
        try:
            return bool(self.cursor.execute(query, args))
        except:
            return False
    
    def is_search(self, user_id):
        """Проверим выставлен ли режим поиска у пользователя"""
        query = "SELECT is_admin FROM subscribers WHERE user_id = (?)"
        args = (user_id, )
        try:
            return bool(self.cursor.execute(query, args))
        except:
            return False

    def update_search_status_subscriber(self, user_id, status):
        """Меняем статус пользователю, если он выбрал поиск"""
        query = "UPDATE subscribers SET is_search = ? WHERE user_id = ?"
        args = (status, user_id)
        self.cursor.execute(query, args)
        self.connect.commit()

    # ---------- Работа с таблицей Новостные ленты ---
    def add_feed(self, title, url, rating):
        """ Добавление нового  новостного feed в БД"""
        query = "INSERT INTO feeds (title, url, rating) VALUES (?, ?, ?)"
        args = (title, url, rating)
        self.cursor.execute(query, args)
        self.connect.commit()
    
    def delete_feed(self, title):
        """ Удаление новостного feed из БД"""
        query = "DELETE FROM feeds WHERE title = (?)"
        args = (title, )
        self.cursor.execute(query, args)
        self.cursor.commit()

    def get_feeds(self):
        """ Получить все новостные ленты """
        query = "SELECT feed_id, url FROM feeds"
        self.cursor.execute(query)
        feeds = self.cursor.fetchall()
        return feeds

    
    # ---------- Работа с таблицей новости ---
    def last_news_date(self, feed_id):
        """Получить дату последней новости для определенного новостного канала"""
        query = "SELECT MAX(public_date) FROM news WHERE feed_id = (?)"
        args = (feed_id, )
        try:
            date = [x[0] for x in self.cursor.execute(query, args)]
            return datetime.strptime(date[0],  "%Y-%m-%d %H:%M:%S")
        except:
            return None

    def add_news(self, feed_id, title, public_date, description, link):
        """Добавить новость в БД"""
        query = "INSERT INTO news (feed_id, title, public_date, description, link) VALUES (?, ?, ?, ?, ?)"
        args = (feed_id, title, public_date, description, link)
        self.cursor.execute(query, args)
        self.connect.commit()

    def search_news(self, text):
        """Поиск по новостям(находим все новости и устанавливаем лимит в 3)"""
        clock_in_half_hour = datetime.today()  # Выбираем новости за сутки от текущего времени
        query = "SELECT title, description, link FROM news WHERE public_date > ? and (title like ? or description like ?)"
        args = (clock_in_half_hour.strftime("%Y-%m-%d 00:00:00"),'%{}%'.format(text), '%{}%'.format(text))
        self.cursor.execute(query, args)
        news = self.cursor.fetchall()
        if len(news) > 0:
            return news
        else:
            args = (clock_in_half_hour.strftime("%Y-%m-%d 00:00:00"),'%{}%'.format(text.title()), '%{}%'.format(text.title()))
            self.cursor.execute(query, args)
            news = self.cursor.fetchall()
            return news
        


    # Добавление новой записи в БД
    def add_item(self, item_text, owner):
        query = "INSERT INTO items (description, owner) VALUES (?, ?)"
        args = (item_text, owner)
        self.cursor.execute(query, args)
        self.connect.commit()

    # Удаление записи из базы данных
    def delete_item(self, item_text, owner):
        query = "DELETE FROM items WHERE description = (?) AND owner = (?)"
        args = (item_text, owner)
        self.cursor.execute(query, args)
        self.cursor.commit()

    # Запрос на получение всех записей из таблицы базы данных
    def get_items(self, owner):
        query = "SELECT description FROM items WHERE owner = (?)"
        args = (owner, )
        return [x[0] for x in self.cursor.execute(query, args)]

    def close(self):
        """Закрываем соединение с БД"""
        self.cursor.close()


