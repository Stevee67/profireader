import sys
sys.path.append('../../profireader')
from profapp.models.articles import Article, ArticleCompany, ArticleCompanyHistory, \
    ArticlePortalDivision
from profapp.models.company import Company, UserCompany
from profapp.models.files import File, FileContent
from profapp.models.users import User
from profapp.models.pr_base import MLStripper
from sqlalchemy import create_engine, event
from profapp.models.pr_base import Search
from profapp.constants.SEARCH import RELEVANCE
import re
from sqlalchemy.orm import scoped_session, sessionmaker
from config import ProductionDevelopmentConfig
classes = [ArticlePortalDivision, Article, ArticleCompany, ArticleCompanyHistory,
           Company, UserCompany, FileContent, File, User]
engine = create_engine(ProductionDevelopmentConfig.SQLALCHEMY_DATABASE_URI)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

def add_to_search(target=None):
    if hasattr(target, 'search_fields'):
        target_fields = ','.join(target.search_fields.keys())
        target_dict = target.get_client_side_dict(fields=target_fields + ',id')
        options = {'relevance': lambda field_name: getattr(RELEVANCE, field_name),
                   'processing': lambda text: MLStripper().strip_tags(text),
                   'index': lambda target_id: target_id}
        for field in target_fields.split(','):
            field_options = target.search_fields[field]
            field_options.update({key: options[key] for key in options
                                 if key not in field_options.keys()})
            pos = getattr(target, 'position', 0)
            position = pos if pos else 0
            db_session.add(Search(index=field_options['index'](target_dict['id']),
                                  table_name=target.__tablename__,
                                  relevance=field_options['relevance'](field), kind=field,
                                  text=field_options['processing'](str(target_dict[field])),
                                  position=position))

def update_search_table(target=None):

    if hasattr(target, 'search_fields'):
        if delete_from_search(target):
            add_to_search(target)
        else:
            add_to_search(target)


def delete_from_search(target):
    if hasattr(target, 'search_fields') and \
            db_session.query(Search).filter_by(index=target.id).count():
        db_session.query(Search).filter_by(index=target.id).delete()
        return True
    return False


if __name__ == '__main__':
    for cls in classes:
        variables = vars(cls).copy()
        variables = variables.keys()

        for key in variables:
            if type(key) is not bool:
                keys = getattr(cls, str(key), None)
                try:
                    stripped_key = str(keys).split('.')[1]
                    type_of_field = str(cls.__table__.c[stripped_key].type)
                    chars_int = int(re.findall(r'\b\d+\b', type_of_field)[0])
                    if chars_int > 36:
                        for c in db_session.query(cls).all():
                            original_field = getattr(c, stripped_key)
                            modify_field = original_field + ' '
                            update_search_table(target=c)
                        break
                except Exception as e:
                    print(e.__repr__())
    db_session.commit()
