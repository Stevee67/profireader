from .blueprints import front_bp
from flask import render_template, request, url_for, redirect, g, current_app
from ..models.articles import Article, ArticlePortal
from ..models.portal import CompanyPortal, PortalDivision, Portal
from config import Config
# from profapp import
from .pagination import pagination

@front_bp.route('/', methods=['GET'])
def index():

    page = 1
    search_text = '%'
    app = current_app._get_current_object()
    portal = g.db().query(Portal).filter_by(host=app.config['SERVER_NAME']).one()
    division = g.db().query(PortalDivision).filter_by(portal_id=portal.id).first()
    sub_query = Article.subquery_articles_at_portal(search_text=search_text)
    articles, pages, page = pagination(query=sub_query, page_size=Config.ITEMS_PER_PAGE,
                                       page=page)

    return render_template('front/bird/index.html',
                           articles={a.id: a.get_client_side_dict() for
                                     a in articles},
                           division=division.get_client_side_dict(),
                           portal=portal,
                           pages=pages,
                           current_page=page,
                           page_buttons=Config.PAGINATION_BUTTONS,
                           search_text=search_text)

@front_bp.route('<string:division_name>/<int:page>/'
                '<string:search_text>', methods=['GET'])
def division(division_name, page, search_text):

    app = current_app._get_current_object()
    portal = g.db().query(Portal).filter_by(host=app.config['SERVER_NAME']).one()
    search_text = search_text if not request.args.get(
        'search_text') else request.args.get('search_text')
    division = g.db().query(PortalDivision).filter_by(portal_id=portal.id, name=division_name).one()

    sub_query = Article.subquery_articles_at_portal(search_text=search_text,
                                                    portal_division_id=division.id)
    articles, pages, page = pagination(query=sub_query, page_size=Config.ITEMS_PER_PAGE, page=page)
    return render_template('front/bird/division.html',
                           articles={a.id: a.get_client_side_dict() for
                                     a in articles},
                           division=division.get_client_side_dict(),
                           portal=portal,
                           pages=pages,
                           current_page=page,
                           page_buttons=Config.PAGINATION_BUTTONS,
                           search_text=search_text)

# TODO OZ by OZ: portal filter, move portal filtering to decorator

@front_bp.route('details/<string:article_portal_id>')
def details(article_portal_id):
    article = ArticlePortal.get(article_portal_id).\
        to_dict('id, title,short, cr_tm, md_tm, '
                'publishing_tm, status, long, image_file_id,'
                'division.name, division.portal.id,'
                'company.name')
    return render_template('front/bird/article_details.html',
                           article=article,
                           portal=article['division']['portal']
                           )
