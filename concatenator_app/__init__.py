import os

from flask import Flask
from flask import render_template
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename
from itertools import zip_longest

UPLOAD_FOLDER = './data/uploads'
RESULTS_FOLDER = './data/results'
COMPLETED_FOLDER = './data/completed'
ALLOWED_EXTENSIONS = {'csv'}


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    upload = os.environ.get("UPLOAD_FOLDER", UPLOAD_FOLDER)
    results = os.environ.get("RESULTS_FOLDER", RESULTS_FOLDER)
    completed = os.environ.get("COMPLETED_FOLDER", COMPLETED_FOLDER)
    app.config['UPLOAD_FOLDER'] = upload
    app.config['RESULTS_FOLDER'] = results
    app.config['COMPLETED_FOLDER'] = completed
    app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError as ose:
        pass
    try:
        os.makedirs(UPLOAD_FOLDER)
    except OSError:
        pass
    try:
        os.makedirs(RESULTS_FOLDER)
    except OSError:
        pass

    from . import concatenate
    from . import files
    app.register_blueprint(concatenate.bp)
    app.register_blueprint(files.bp)

    @app.route("/")
    def home():
        files = os.listdir(app.config["UPLOAD_FOLDER"])
        files.sort()
        results = os.listdir(app.config["RESULTS_FOLDER"])
        results.sort()
        #print(files, results)
        completed_folders = os.listdir(app.config["COMPLETED_FOLDER"])
        completed_folders.sort()
        return render_template("index.jinja2", zipped_files=zip_longest(files, results, completed_folders, fillvalue=""))

    return app


