import os

from werkzeug.utils import secure_filename

from flask import (
    Blueprint, request, abort, current_app, jsonify, send_from_directory, request, redirect, url_for, Flask, flash, render_template
)


bp = Blueprint('files', __name__, url_prefix='/files')



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@bp.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            return redirect("/")
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''


@bp.route('/uploads')
def list_files():
    files = os.listdir(current_app.config["UPLOAD_FOLDER"])
    files.sort()
    return render_template("list_files.jinja2", files=files, path=current_app.config["UPLOAD_FOLDER"])


@bp.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], name)

@bp.route('/results/<name>')
def download_results(name):
    print(name)
    return send_from_directory(current_app.config["RESULTS_FOLDER"], name)

@bp.route('/results')
def list_results():
    files = os.listdir(current_app.config["RESULTS_FOLDER"])
    files.sort()
    return render_template("results.jinja2", results=files)

@bp.route('/completed/<name>')
def list_completed(name):
    path = "%s/%s" % (current_app.config["COMPLETED_FOLDER"], name)
    files = os.listdir(path)
    files.sort()
    return render_template("list_files.jinja2", files=files, path=path)