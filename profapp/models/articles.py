from db_connect import sql_session, metadata
from sqlalchemy import Table, Column, Integer, Text, ForeignKey
from sqlalchemy.orm import mapper

article_history_table=Table('article_history',metadata,
                            Column('id',Integer,primary_key=True),
                            Column('article_text',Text),
                            Column('status',Integer),
                            Column('contributor_user_id',Integer,ForeignKey('user.id'))
                            )
class ArticleHistory(object):
    query=sql_session.query_property()
    def __init__(self,article_text,status,contributor_user_id):
        self.article_text=article_text
        self.status=status
        self.contributor_user_id=contributor_user_id
mapper(ArticleHistory,article_history_table)


article_table=Table('article',metadata,
                    Column('id',Integer,primary_key=True),
                    Column('author_user_id',Integer,ForeignKey('user.id')),
                    Column('company_id',Integer,ForeignKey('company.id'))
                    )
class Article(object):
    query=sql_session.query_property()
    def __init__(self, author_user_id, company_id):
        self.author_user_id=author_user_id
        self.company_id=company_id
mapper(Article,article_table)
