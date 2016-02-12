from .blueprints_declaration import company_bp

from flask.ext.login import login_required, current_user
from flask import render_template, request, url_for, g, redirect
from ..models.company import Company, UserCompany
from ..models.users import User
from ..models.translate import TranslateTemplate
from .request_wrapers import ok, check_rights, tos_required
from ..constants.STATUS import STATUS
from flask.ext.login import login_required
from ..models.articles import Article
from ..models.portal import PortalDivision

from ..models.articles import ArticleCompany, ArticlePortalDivision
from utils.db_utils import db
from ..constants.FILES_FOLDERS import FOLDER_AND_FILE
from collections import OrderedDict
from ..models.tag import TagPortalDivisionArticle
# from ..models.rights import list_of_RightAtomic_attributes
from profapp.models.rights import RIGHTS
from ..models.files import File, ImageCroped
from flask import session
from .pagination import pagination
from .views_file import crop_image
from config import Config
from ..models.pr_base import Search, PRBase, Grid
import base64
from PIL import Image
from io import BytesIO
import re


@company_bp.route('/search_to_submit_article/', methods=['POST'])
@login_required
# @check_rights(simple_permissions(Right[RIGHTS.SUBMIT_PUBLICATIONS()]))
def search_to_submit_article(json):
    companies = Company().search_for_company(g.user_dict['id'], json['search'])
    return companies


@company_bp.route('/', methods=['GET'])
@tos_required
@login_required
# @check_rights(simple_permissions([]))
def show():
    return render_template('company/companies.html')


@company_bp.route('/', methods=['POST'])
@login_required
# @check_rights(simple_permissions([]))
@ok
def load_companies(json):
    user_companies = [user_comp for user_comp in current_user.employer_assoc]
    return {'companies': [usr_cmp.employer.get_client_side_dict() for usr_cmp in user_companies
                          ],

            'user_id': g.user_dict['id']}


@company_bp.route('/<string:company_id>/materials/', methods=['GET'])
@tos_required
@login_required
# @check_rights(simple_permissions([]))
def materials(company_id):
    return render_template('company/materials.html', company=db(Company, id=company_id).one())


@company_bp.route('/<string:company_id>/materials/', methods=['POST'])
@ok
def materials_load(json, company_id):
    subquery = ArticleCompany.subquery_company_materials(company_id, json.get('filter'), json.get('sort'))
    materials, pages, current_page, count = pagination(subquery, **Grid.page_options(json.get('paginationOptions')))

    grid_filters = {
        'portal.name': [{'value': portal, 'label': portal} for portal_id, portal in
                    ArticlePortalDivision.get_portals_where_company_send_article(company_id).items()],
        'material_status': Grid.filter_for_status(ArticleCompany.STATUSES),
        'status': Grid.filter_for_status(ArticlePortalDivision.STATUSES),
        'publication_visibility': Grid.filter_for_status(ArticlePortalDivision.VISIBILITIES)
    }
    return {'grid_data': Grid.grid_tuple_to_dict([Article.get_material_grid_data(material) for material in materials]),
            'grid_filters': {k: [{'value': None, 'label': TranslateTemplate.getTranslate('', '__-- all --')}] + v for
                             (k, v) in grid_filters.items()},
            'total': count
            }


@company_bp.route('/<string:article_portal_division_id>/', methods=['POST'])
@login_required
@ok
# @check_rights(simple_permissions([]))
def delete_atricle_from_portal(json, article_portal_division_id):
    g.sql_connection.execute("DELETE FROM article_portal_division WHERE id='%s';"
                             % article_portal_division_id)
    new_json = json.copy()
    for article in json:
        if json[article]['id'] == article_portal_division_id:
            del new_json[article]
    return new_json


# file_author_user_id_fkey	FOREIGN KEY (author_user_id) REFERENCES "user"(id)

@company_bp.route('/get_tags/<string:portal_division_id>', methods=['POST'])
@login_required
# @check_rights(simple_permissions([]))
@ok
def get_tags(json, portal_division_id):
    available_tags = g.db.query(PortalDivision).get(portal_division_id).portal_division_tags
    available_tag_names = list(map(lambda x: getattr(x, 'name'), available_tags))
    return {'availableTags': available_tag_names}


@company_bp.route('/update_material_status/<string:company_id>/<string:article_id>',
                  methods=['POST'])
# @login_required
# @check_rights(simple_permissions([]))
@ok
def update_material_status(json, company_id, article_id):
    allowed_statuses = ArticleCompany.STATUSES.keys()
    # ARTICLE_STATUS_IN_COMPANY.can_user_change_status_to(json['new_status'])

    ArticleCompany.update_article(
            company_id=company_id,
            article_id=article_id,
            **{'status': json['new_status']})

    return {'article_new_status': json['new_status'],
            'allowed_statuses': allowed_statuses,
            'status': 'ok'}


# @company_bp.route('/profile/<string:company_id>/')
# @tos_required
# @login_required
# # @check_rights(simple_permissions(['manage_rights_company']))
# def profile(company_id):
#     user_companies = [user_comp for user_comp in current_user.employer_assoc]
#     user_have_comp = True if len(user_companies) > 0 else False
#     return render_template('company/company_profile.html',
#                            company=db(Company, id=company_id).one(),
#                            rights_user_in_company=UserCompany.get(company_id=company_id).get_rights(),
#                            user_company = user_have_comp
#                            )


@company_bp.route('/<string:company_id>/employees/', methods=['GET'])
@tos_required
@login_required
# @check_rights(simple_permissions([]))
def employees(company_id):
    return render_template('company/company_employees.html', company=Company.get(company_id))


@company_bp.route('/<string:company_id>/employees/', methods=['POST'])
@ok
def employees_load(json, company_id):
    company = Company.get(company_id)
    employees_list = [
        PRBase.merge_dicts(employment.employee.get_client_side_dict(), employment.get_client_side_dict())
        for employment in company.employee_assoc]
    print(employees_list)

    return {
        'company': company.get_client_side_dict(fields='id,name'),
        'grid_data': employees_list
    }
    # company_user_rights = UserCompany.show_rights(company_id)
    # ordered_rights = sorted(Right.keys(), key=lambda t: Right.RIGHT_POSITION()[t.lower()])
    # ordered_rights = list(map((lambda x: getattr(x, 'lower')()), ordered_rights))

    # for user_id in company_user_rights.keys():
    #     rights = company_user_rights[user_id]['rights']
    #     rez = OrderedDict()
    #     for elem in ordered_rights:
    #         rez[elem] = True if elem in rights else False
    #     company_user_rights[user_id]['rights'] = rez

    # user_id = current_user.get_id()
    # curr_user = {user_id: company_user_rights[user_id]}
    # curr_user = {user_id: []}

    # return render_template('company/company_employees.html',
    #                        company=db(Company, id=company_id).one(),
    #                        company_user_rights=[],
    #                        curr_user=curr_user,
    #                        rights={})


@company_bp.route('/<string:company_id>/employee_details/<string:user_id>/', methods=['GET'])
@tos_required
@login_required
# @check_rights(simple_permissions([]))
def employee_details(company_id, user_id):
    employment = UserCompany.get(user_id=user_id, company_id=company_id)
    return render_template('company/company_employee_details.html',
                           employer=employment.employer.get_client_side_dict(),
                           employee=employment.employee.get_client_side_dict(),
                           employment=employment.get_client_side_dict())


@company_bp.route('/<string:company_id>/employee_update/<string:user_id>/', methods=['GET'])
@tos_required
@login_required
# @check_rights(simple_permissions([]))
def employee_update(company_id, user_id):
    return render_template('company/company_employee_update.html',
                           employment=UserCompany.get(user_id=user_id, company_id=company_id))
    # employer=employment.employer.get_client_side_dict(),
    # employee=employment.employee.get_client_side_dict())


@company_bp.route('/<string:company_id>/employee_update/<string:user_id>/', methods=['POST'])
@tos_required
@login_required
@ok
# @check_rights(simple_permissions([]))
def employee_update_load(json, company_id, user_id):
    action = g.req('action', allowed=['load', 'validate', 'save'])
    employment = UserCompany.get(user_id=user_id, company_id=company_id)
    if action == 'load':
        return  {'employment': employment.get_client_side_dict(),
                'employee': employment.employee.get_client_side_dict(),
                'employer': employment.employer.get_client_side_dict(fields='id|logo_file_id|name'),
                'statuses_available': employment.get_statuses_avaible(),
                'rights_available': employment.get_rights_avaible()}
    else:
        employment.set_client_side_dict(json['employment'])
        if action == 'validate':
            employment.detach()
            return employment.validate(False)
        else:
            employment.save()
    return employment.get_client_side_dict()


@company_bp.route('/update_rights', methods=['POST'])
@login_required
# @check_rights(simple_permissions([RIGHTS.MANAGE_RIGHTS_COMPANY()]))
def update_rights():
    data = request.form
    company_id, user_id, position = (data.get('company_id'), data.get('user_id'), data['position'])
    if not db(Company, id=company_id, author_user_id=user_id).count():
        UserCompany.update_rights(user_id=data['user_id'],
                                  company_id=data['company_id'],
                                  new_rights=data.getlist('right'),
                                  position=data['position'])
    else:
        db(UserCompany, company_id=company_id, user_id=user_id).update(dict(position=position))
    return redirect(url_for('company.employees',
                            company_id=data['company_id']))


@company_bp.route('/create/', methods=['GET'])
@tos_required
@login_required
# @check_rights(simple_permissions([]))
def update(company_id=None):
    user_companies = [user_comp for user_comp in current_user.employer_assoc]
    user_have_comp = True if len(user_companies) > 0 else False
    company = db(Company, id=company_id).first()
    return render_template('company/company_edit.html', company_id=company_id, user_comp=user_have_comp,
                           company_name=company.name if company else '',
                           company=company if company else {})

@company_bp.route('/profile/<string:company_id>/', methods=['GET'])
@tos_required
@login_required
# @check_rights(simple_permissions([]))
def profile(company_id=None):
    user_companies = [user_comp for user_comp in current_user.employer_assoc]
    user_have_comp = True if len(user_companies) > 0 else False
    company = db(Company, id=company_id).first()
    return render_template('company/company_profile.html', company_id=company_id, user_comp=user_have_comp,
                           company_name=company.name if company else '',
                           rights_user_in_company=UserCompany.get(company_id=company_id).get_rights(),
                           company=company)



@company_bp.route('/create/', methods=['POST'])
@company_bp.route('/profile/<string:company_id>/', methods=['POST'])
@login_required
@ok
def load(json, company_id=None):
    action = g.req('action', allowed=['load', 'validate', 'save'])
    company = Company() if company_id is None else Company.get(company_id)
    if action == 'load':
        company_dict = company.get_client_side_dict()
        image_dict = {'ratio': Config.IMAGE_EDITOR_RATIO, 'coordinates': None,
                      'image_file_id': company_dict.get('logo_file_id'),
                      'no_image_url': g.fileUrl(FOLDER_AND_FILE.no_logo())
                      }
        try:
            if company_dict.get('logo_file_id'):
                image_dict['image_file_id'], image_dict['coordinates'] = ImageCroped. \
                    get_coordinates_and_original_img(company_dict.get('logo_file_id'))
            else:
                image_dict['image_file_id'] = None
        except Exception as e:
            pass
        image = {'image': image_dict}
        company_dict.update(image)
        return company_dict
    else:
        company.attr(g.filter_json(json, 'about', 'address', 'country', 'email', 'name', 'phone',
                                   'phone2', 'region', 'short_description', 'lon', 'lat'))
        if action == 'validate':
            if company_id is not None:
                company.detach()
            return company.validate(company_id is None)
        else:
            if json['image'].get('uploaded'):
                if company_id is None:
                    company.setup_new_company()
                company.save().get_client_side_dict()
                imgdataContent = json['image']['dataContent']
                image_data = re.sub('^data:image/.+;base64,', '', imgdataContent)
                bb = base64.b64decode(image_data)
                new_comp = db(Company, id=company.id).first()
                file_id = File.uploadForCompany(bb, json['image']['name'], json['image']['type'], new_comp)
                logo_id = crop_image(file_id, json['image']['coordinates'])
                new_comp.updates({'logo_file_id': logo_id})
            else:
                img = json['image']
                img_id = img.get('image_file_id')
                if img_id:
                    company.logo_file_id = crop_image(img_id, img['coordinates'])
                elif not img_id:
                    company.logo_file_id = None
                if company_id is None:
                    company.setup_new_company()
                return company.save().get_client_side_dict()


# @company_bp.route('/confirm_create/', methods=['POST'])
# @login_required
# # @check_rights(simple_permissions([]))
# @ok
# def confirm_create(json):


# @company_bp.route('/edit/<string:company_id>/', methods=['POST'])
# @login_required
# @ok
# # @check_rights(simple_permissions([RIGHTS.MANAGE_RIGHTS_COMPANY()]))
# def edit_load(json, company_id):
#     company = db(Company, id=company_id).one()
#     return company.get_client_side_dict()


# @company_bp.route('/confirm_edit/<string:company_id>', methods=['POST'])
# @login_required
# @ok
# # @check_rights(simple_permissions([RIGHTS.MANAGE_RIGHTS_COMPANY()]))
# def confirm_edit(json, company_id):
#
#     return {}



@company_bp.route('/search_for_company_to_join/', methods=['POST'])
@login_required
@ok
# @check_rights(simple_permissions([]))
def search_for_company_to_join(json):
    companies = Company().search_for_company_to_join(g.user_dict['id'], json['search'])
    return companies


@company_bp.route('/search_for_user/<string:company_id>', methods=['POST'])
@login_required
@ok
# @check_rights(simple_permissions([]))
def search_for_user(json, company_id):
    users = UserCompany().search_for_user_to_join(company_id, json['search'])
    return users


@company_bp.route('/send_article_to_user/', methods=['POST'])
@login_required
@ok
# @check_rights(simple_permissions([]))
def send_article_to_user(json):
    return {'user': json['send_to_user']}


@company_bp.route('/join_to_company/<string:company_id>/', methods=['POST'])
@login_required
@ok
# @check_rights(simple_permissions([]))
def join_to_company(json, company_id):
    company_role = UserCompany(user_id=g.user_dict['id'],
                               company_id=json.get('company_id'),
                               status=UserCompany.STATUSES['APPLICANT'])
    company_role.subscribe_to_company().save()
    return {'companies': [employer.get_client_side_dict() for employer in current_user.employers]}


@company_bp.route('/subscribe/<string:company_id>/')
@tos_required
@login_required
# @check_rights(simple_permissions([]))
def subscribe(company_id):
    company_role = UserCompany(user_id=g.user_dict['id'],
                               company_id=company_id,
                               status=UserCompany.STATUSES['APPLICANT'])
    company_role.subscribe_to_company().save()

    return redirect(url_for('company.profile', company_id=company_id))


@company_bp.route('/add_subscriber/', methods=['POST'])
@login_required
# @check_rights(simple_permissions([RIGHTS.ADD_EMPLOYEE()]))
def confirm_subscriber():
    company_role = UserCompany()
    data = request.form
    company_role.apply_request(company_id=data['company_id'],
                               user_id=data['user_id'],
                               bool=data['req'])
    return redirect(url_for('company.profile', company_id=data['company_id']))


@company_bp.route('/suspend_employee/', methods=['POST'])
@login_required
# @check_rights(simple_permissions([RIGHTS.SUSPEND_EMPLOYEE()]))
def suspend_employee():
    data = request.form
    UserCompany.change_status_employee(user_id=data['user_id'],
                                       company_id=data['company_id'])
    return redirect(url_for('company.employees',
                            company_id=data['company_id']))


@company_bp.route('/fire_employee/', methods=['POST'])
@login_required
def fire_employee():
    data = request.form
    UserCompany.change_status_employee(company_id=data.get('company_id'),
                                       user_id=data.get('user_id'),
                                       status=UserCompany.STATUSES['FIRED'])
    return redirect(url_for('company.employees', company_id=data.get('company_id')))


@company_bp.route('/unsuspend/<string:user_id>,<string:company_id>')
@login_required
def unsuspend(user_id, company_id):
    UserCompany.change_status_employee(user_id=user_id,
                                       company_id=company_id,
                                       status=UserCompany.STATUSES['ACTIVE'])
    return redirect(url_for('company.employees', company_id=company_id))


@company_bp.route('/suspended_employees/<string:company_id>',
                  methods=['GET'])
@tos_required
@login_required
# @check_rights(simple_permissions([]))
def suspended_employees(company_id):
    company = db(Company, id=company_id).one()
    return render_template('company/company_fired.html', company_id=company_id, company=company)


@company_bp.route('/suspended_employees/<string:company_id>', methods=['POST'])
@login_required
# @check_rights(simple_permissions([]))
@ok
def load_suspended_employees(json, company_id):
    suspend_employees = Company.query_company(company_id)
    suspend_employees = suspend_employees.suspended_employees()
    return suspend_employees


@company_bp.route('/readers/<string:company_id>/', methods=['GET'])
@company_bp.route('/readers/<string:company_id>/<int:page>/', methods=['GET'])
@tos_required
@login_required
# @check_rights(simple_permissions([]))
def readers(company_id, page=1):
    company = Company.get(company_id)
    company_readers, pages, page, count = pagination(query=company.readers_query, page=page)

    reader_fields = ('id', 'email', 'nickname', 'first_name', 'last_name')
    company_readers_list_dict = list(map(lambda x: dict(zip(reader_fields, x)), company_readers))

    return render_template('company/company_readers.html',
                           company=company,
                           companyReaders=company_readers_list_dict,
                           pages=pages,
                           current_page=page,
                           page_buttons=Config.PAGINATION_BUTTONS,
                           search_text=None,
                           )


@company_bp.route('/readers/<string:company_id>/', methods=['POST'])
@ok
def readers_load(json, company_id):
    company = Company.get(company_id)
    company_readers, pages, page, count = pagination(query=company.get_readers_for_portal(json.get('filter')),
                                                     **Grid.page_options(json.get('paginationOptions')))

    return {'grid_data': [reader.get_client_side_dict(
            'id,profireader_email,profireader_name,profireader_first_name,profireader_last_name') for reader in
                          company_readers],
            'total': count
            }
