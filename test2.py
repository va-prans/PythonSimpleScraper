import time
from selenium import webdriver
from bs4 import BeautifulSoup as bs
from textblob import TextBlob
import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, Date, DECIMAL, exists, DateTime, Boolean, extract
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy import Sequence
from sqlalchemy.orm import sessionmaker
import decimal

engine = create_engine('mysql+mysqldb://root:@127.0.0.1:3306/redditscrape?charset=utf8', pool_recycle=3600,
                       encoding='utf-8')
Base = declarative_base()


class Post(Base):
    __tablename__ = 'posts'
    url = Column(String(200), primary_key=True)
    date = Column(DateTime, index=True)
    user = Column(String(200))
    title = Column(String(500))
    polarity = Column(DECIMAL(4, 2))
    subjectivity = Column(DECIMAL(4, 2))
    comment_count = Column(Integer)
    isParsed = Column(Boolean, index=True)


class DailyStats(Base):
    __tablename__ = 'daily_stats'
    date = Column(DateTime, primary_key=True)
    posts = Column(Integer)
    comments = Column(Integer)
    comments_per_post = Column(DECIMAL(4, 2))
    positive_polarity = Column(DECIMAL(4, 2))
    negative_polarity = Column(DECIMAL(4, 2))
    net_polarity = Column(DECIMAL(4, 2))
    subjectivity = Column(DECIMAL(4, 2))


Column(Integer, Sequence('user_id_seq'), primary_key=True)


class WordCount(Base):
    __tablename__ = 'word_counts'
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    date = Column(DateTime, index=True)
    word = Column(String(30), index=True)
    count = Column(Integer)

    def __init__(self, date, word, count):
        self.date = date
        self.word = word
        self.count = count


Post.__table__
DailyStats.__table__
WordCount.__table__

Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)
session = DBSession()

browser = webdriver.Chrome("C:\\Users\master\Desktop\pythonstuff\chromedriver.exe")
browser.get("https://new.reddit.com/r/Bitcoin/new/")
while True:
    time.sleep(5)
    browser.refresh()
    time.sleep(5)

    for i in range(0, 20):
        time.sleep(5)
        browser.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
    # Now that the page is fully scrolled, grab the source code.
    time.sleep(10)
    source_data = browser.page_source

    # Throw your source into BeautifulSoup and start parsing!
    soup = bs(source_data, "html5lib")
    threads = soup.find_all('div', class_="scrollerItem")
    now = datetime.datetime.now()

    for div in threads:
        print("----------------------")
        div_descendants = div.descendants
        post = Post()
        for descElement in div_descendants:
            if descElement.name == 'h2':
                print(descElement.text)
                print(TextBlob(descElement.text).sentiment)
                post.title = descElement.text
                post.polarity = round(TextBlob(descElement.text).sentiment.polarity, 2)
                post.subjectivity = round(TextBlob(descElement.text).sentiment.subjectivity, 2)

            if descElement.name == 'a' and descElement.get('data-click-id') == 'body':
                print(descElement.get("href"))
                post.url = descElement.get("href")

            if descElement.name == 'a' and descElement.get('data-click-id') == 'timestamp':

                wordList = descElement.text.split(" ")

                postDate = now
                if wordList[1] == "minutes" or wordList[1] == "minute":
                    timeSincePost = int(wordList[0])
                    postDate = now - datetime.timedelta(minutes=int(wordList[0]))

                elif wordList[1] == "hours" or wordList[1] == "hour":
                    timeSincePost = int(wordList[0])
                    postDate = now - datetime.timedelta(hours=int(wordList[0]))

                elif wordList[1] == "days" or wordList[1] == "day":
                    timeSincePost = int(wordList[0])
                    postDate = now - datetime.timedelta(days=int(wordList[0]))

                print(descElement.text)
                print(postDate)
                postDate = postDate.replace(microsecond=0)
                post.date = datetime.datetime(postDate.year, postDate.month, postDate.day, postDate.hour,
                                              postDate.minute)

            if descElement.name == 'a' and descElement.get('data-click-id') == 'comments':
                print(descElement.text)
                commentCount = 0
                if descElement.text[0] != "c":
                    commentCount = int(descElement.text[0])
                post.comment_count = commentCount

            if descElement.name == 'a' and descElement.get('data-click-id') != 'body' and descElement.get(
                    'data-click-id') != 'timestamp' and descElement.get('data-click-id') != 'comments':
                if len(descElement.text) > 0 and descElement.text[0] == 'u':
                    print(descElement.text)
                    post.user = descElement.text

        if session.query(Post.url).filter_by(url=post.url).scalar() is None:
            print("New post! Adding to Database!")
            post.isParsed = False
            session.add(post)
        else:
            session.query(Post).filter(Post.url == post.url). \
                update({Post.comment_count: post.comment_count})

    session.commit()

    unParsedPosts = session.query(Post).filter(Post.isParsed == False)
    unParsedPosts.all()
    nowTime = datetime.datetime.now()
    for unparsedPost in unParsedPosts:
        print(unparsedPost.url)
        postWords = unparsedPost.title.split(" ")
        for word in postWords:
            dailyWord = session.query(WordCount).filter(
                WordCount.date == datetime.datetime(unparsedPost.date.year, unparsedPost.date.month,
                                                    unparsedPost.date.day)). \
                filter(WordCount.word == word)
            if dailyWord.scalar() is None:
                print("Word: " + word + " found for day: " + unparsedPost.date.strftime('%d/%m/%Y'))
                date = datetime.datetime(unparsedPost.date.year, unparsedPost.date.month,
                                         unparsedPost.date.day)
                session.add(WordCount(date,
                                      word,
                                      1))
            else:
                print("Word: " + word + " exists for day: " + unparsedPost.date.strftime('%d/%m/%Y'))
                dailyWord.update({WordCount.count: WordCount.count + 1})

            session.commit()
        # update post age detector
        if unparsedPost.date <= nowTime - datetime.timedelta(hours=24):
            print("Post age is larger than 24 hours.")
            session.query(Post).filter(Post.url == unparsedPost.url). \
                update({Post.isParsed: True})
            dailyStat = session.query(DailyStats).filter(
                DailyStats.date == datetime.datetime(unparsedPost.date.year, unparsedPost.date.month,
                                                     unparsedPost.date.day))
            if dailyStat.scalar() is None:
                print("No daily stat found for day: " + unparsedPost.date.strftime('%d/%m/%Y'))
                newDailyStat = DailyStats()
                newDailyStat.date = datetime.datetime(unparsedPost.date.year, unparsedPost.date.month,
                                                      unparsedPost.date.day)
                newDailyStat.posts = 1
                newDailyStat.comments = unparsedPost.comment_count
                newDailyStat.comments_per_post = newDailyStat.comments / newDailyStat.posts
                newDailyStat.subjectivity = unparsedPost.subjectivity
                if unparsedPost.polarity < 0:
                    newDailyStat.negative_polarity = unparsedPost.polarity
                    newDailyStat.net_polarity = unparsedPost.polarity
                    newDailyStat.positive_polarity = 0

                else:
                    newDailyStat.positive_polarity = unparsedPost.polarity
                    newDailyStat.net_polarity = unparsedPost.polarity
                    newDailyStat.negative_polarity = 0

                session.add(newDailyStat)
                session.commit()

            else:
                if unparsedPost.polarity < 0:
                    dailyStat. \
                        update({DailyStats.posts: DailyStats.posts + 1,
                                DailyStats.comments: DailyStats.comments + unparsedPost.comment_count,
                                DailyStats.comments_per_post: DailyStats.comments / DailyStats.posts,
                                DailyStats.negative_polarity: DailyStats.negative_polarity - unparsedPost.polarity,
                                DailyStats.net_polarity: DailyStats.net_polarity - unparsedPost.polarity,
                                DailyStats.subjectivity: DailyStats.subjectivity + unparsedPost.subjectivity})
                else:
                    dailyStat. \
                        update({DailyStats.posts: DailyStats.posts + 1,
                                DailyStats.comments: DailyStats.comments + unparsedPost.comment_count,
                                DailyStats.comments_per_post: DailyStats.comments / DailyStats.posts,
                                DailyStats.positive_polarity: DailyStats.positive_polarity + unparsedPost.polarity,
                                DailyStats.net_polarity: DailyStats.net_polarity + unparsedPost.polarity,
                                DailyStats.subjectivity: DailyStats.subjectivity + unparsedPost.subjectivity})
            session.commit()

    session.commit()
    print("Waiting an hour before reading posts again..")
    time.sleep(60 * 60)
