#!/usr/bin/env python3

import feedparser

# Модули для работы с датой и временем
from datetime import datetime
import time


from contextlib import contextmanager
import signal
from db import DB

db = DB()

sleep_time = 60*60 # время повторного опроса RSS в секундах
net_timeout = 10  # время ожидания ответа к url в секундах

class TimeoutException(Exception): pass


# Список новостных лент
# tass - http://tass.ru/rss/v2.xml - ok - 6
# rg - https://rg.ru/xml/index.xml - 5
# kommersant - https://www.kommersant.ru/RSS/news.xml - 9 
# rdc - http://static.feed.rbc.ru/rbc/logical/footer/news.rss - 2
# известия - https://iz.ru/xml/rss/all.xml - 4
# vedomosti - https://www.vedomosti.ru/rss/news - 1
# novayagazeta - https://content.novayagazeta.ru/rss/all.xml  - 7
# https://www.gazeta.ru/export/rss/lastnews.xml - 3
# feed = feedparser.parse("https://www.kommersant.ru/RSS/news.xml")


@contextmanager
def timeout_sec(seconds):
  def signal_handler(signum, frame):
    raise TimeoutException(Exception("Время вышло!"))
  signal.signal(signal.SIGALRM, signal_handler)
  signal.alarm(seconds)
  try:
    yield
  finally:
    signal.alarm(0)

def run_parse_feed():
    while True:
        feed_list = db.get_feeds();
        print("Идет обработка {} новостных лент...".format(len(feed_list)))

        for feed in feed_list:
            print(feed)
            f = None
            try:
                with timeout_sec(net_timeout):
                    f = feedparser.parse(feed[1])
            except TimeoutException:
                print("Ошибка: Время вышло!")
                continue

            feed_title = f['feed'].get('title', '(NO TITLE)')
            feed_link = f['feed'].get('link', '(NO LINK)')

            print(feed_title)
            print(feed_link)
            last_public_date = db.last_news_date(feed[0])
            for entry in f['entries']:
                article_title = entry.title
                article_link = entry.link
                article_published_at = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                try:
                    article_description = entry.summary
                except:
                    article_description = ''

                if last_public_date is None:
                    db.add_news(
                        feed_id=feed[0],
                        title=article_title,
                        public_date=article_published_at,
                        description = article_description,
                        link=article_link
                    )
                else:
                    if last_public_date < article_published_at:
                        db.add_news(
                            feed_id=feed[0],
                            title=article_title,
                            public_date=article_published_at,
                            description = article_description,
                            link=article_link
                        )


        print("Ожидание {} секунд...".format(sleep_time))
        time.sleep(sleep_time)

if __name__ == "__main__":
    run_parse_feed();