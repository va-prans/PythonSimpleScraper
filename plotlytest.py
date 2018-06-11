from sqlalchemy import Column, ForeignKey, Integer, String, Date, DECIMAL, exists, DateTime, Boolean, extract
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy import Sequence
from sqlalchemy.orm import sessionmaker
import decimal
import plotly as py
import plotly.graph_objs as go
from plotly import tools

engine = create_engine('mysql+mysqldb://root:@127.0.0.1:3306/redditscrape?charset=utf8', pool_recycle=3600,
                       encoding='utf-8')
Base = declarative_base()


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


DailyStats.__table__
WordCount.__table__

Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)
session = DBSession()

dailyStats = session.query(DailyStats).order_by(DailyStats.date).all()
xVal = []
yValPosts = []
yValComments = []
yValCommentsPerPost = []
yValNetPol = []
yValPosPol = []
yValNegPol = []

for day in dailyStats:
    xVal.append(day.date)
    yValPosts.append(day.posts)
    yValComments.append(day.comments)
    yValCommentsPerPost.append(day.comments_per_post)
    yValNetPol.append(day.net_polarity)
    yValPosPol.append(day.positive_polarity)
    yValNegPol.append(day.negative_polarity)

barPosts = go.Bar(x=xVal, y=yValPosts, name='Posts')
barComments = go.Bar(x=xVal, y=yValComments, name='Comments')
barCommentsPerPost = go.Bar(x=xVal, y=yValCommentsPerPost, name='CommentsPerPost')
barNetPol = go.Bar(x=xVal, y=yValNetPol, name='NetPolarity')
barPosPol = go.Bar(x=xVal, y=yValPosPol, name='PosPolarity')
barNegPol = go.Bar(x=xVal, y=yValNegPol, name='NegPolarity')

fig = tools.make_subplots(rows=2, cols=3, subplot_titles=('Posts', 'Comments', 'PlusPolarity',
                                                          'CommentsPerPost', 'NetPolarity', 'NegativePolarity'))
fig.append_trace(barPosts, 1, 1)
fig.append_trace(barComments, 1, 2)
fig.append_trace(barPosPol, 1, 3)
fig.append_trace(barCommentsPerPost, 2, 1)
fig.append_trace(barNetPol, 2, 2)
fig.append_trace(barNegPol, 2, 3)

fig['layout'].update(height=800, width=1200, title='Reddit Scraper')

py.offline.plot(fig, filename='redditStats.html')
