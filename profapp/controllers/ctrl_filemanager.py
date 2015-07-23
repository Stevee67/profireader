import os
from time import gmtime, strftime
from stat import ST_MTIME, ST_SIZE
from flask import jsonify, request, Blueprint, send_file
import shutil
static_bp = Blueprint('static', __name__, static_url_path='', static_folder='/static/filemanager/files')
root = os.getcwd()+'/profapp/static/filemanager/files'
json_result = {"result": {"success": True, "error": None}}

@static_bp.route('/filemanager/bridges/python/ctrl_filemanager.py', methods=['GET', 'POST'])
def ctrl_filemanager():

    if request.method != 'GET':
        try:
            for params in request.json.values():
                if params['mode'] == 'list':
                    return jsonify(listing(params['path']))
                elif params['mode'] == 'rename':
                    return jsonify(rename(params['path'], params['newPath'], json_result))
                elif params['mode'] == 'delete':
                    return jsonify(remove(params['path'], json_result))
                elif params['mode'] == 'editfile':
                     return jsonify(get_content(params['path']))
                elif params['mode'] == 'savefile':
                    return jsonify(edit_file(params['path'], params['content'], json_result))
                elif params['mode'] == 'addfolder':
                    return jsonify(create_folder(params['name'], params['path'], json_result))
                elif params['mode'] == 'copy':
                    return jsonify(copy_paste(params['path'], params['newPath'], json_result))
        except AttributeError:
            print(request.files)

            return jsonify(upload(json_result))
    get_mode = request.args.get('mode')
    get_path = request.args.get('path')
    if get_mode == 'download':
        return send_file(root+get_path)
    return json_result


def listing(folder_path):

    info = []
    files = os.listdir(root+folder_path)
    for file in files:
        st = os.stat(root+folder_path+'/'+file)
        params = dict()
        params['size'] = st[ST_SIZE]
        params['date'] = strftime("%Y-%d-%m %X", gmtime(st[ST_MTIME]))
        params['name'] = os.path.basename(file)
        params['rights'] = 'drwxr-xr-x'
        if os.path.isfile(root+folder_path+'/'+file):
            params['type'] = 'file'
        else:
            params['type'] = 'dir'
        info.append(params)
    result = {"result": info}
    return result

def rename(path, new_path, result):

    try:
        os.renames(root+path, root+new_path)
    except PermissionError:
        result = {"result": {
                "success": False,
                "error": "Access denied to rename file"}
            }
    return result

def remove(file, result):

    try:
        if os.path.isfile(root+file):
            os.remove(root+file)
        else:
            os.removedirs(root+file)
    except PermissionError:
        result = {"result": {
                "success": False,
                "error": "Access denied to remove file"}
            }
    return result

def get_content(file):

    opener = open(root+file)
    reader = opener.read()
    result = {"result": reader}
    opener.close()
    return result

def edit_file(file, content, result):

    try:
        opener = open(root+file, mode='w')
        opener.write(content)
        opener.close()
    except PermissionError:
        result = {"result": {
                "success": False,
                "error": "Access denied to edit file"}
            }
    return result

def create_folder(name, folder_path, result):

    os.makedirs(root+'/'+folder_path+'/'+name)
    return result

def copy_paste(file_path, new_file_path, result):
    try:
        shutil.copy2(root+file_path, root+new_file_path)
    except shutil.SameFileError:
        result = {"result": {
                "success": False,
                "error": "This name already exist"}
            }
    return result

def upload(result):

    file = request.files['file-1']
    filename = file.filename
    file.save(root+filename)
    return result