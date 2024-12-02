from flask import Flask, request, redirect, url_for, flash, render_template, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
import stat
import shutil
import zipfile
import subprocess
import json
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit max upload size to 16MB
app.config['WEBSITE_ROOT'] = '/var/www/html'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

ALLOWED_EXTENSIONS = {'txt', 'py', 'html', 'css', 'js', 'md', 'xlsm', 'pdf'}

# Sample app store data
APPSTORE = [
    {
        'title': 'Nginx',
        'image': 'https://nginx.org/nginx.png',
        'description': 'High-performance HTTP server and reverse proxy',
        'install_command': 'sudo apt-get install nginx'
    },
    {
        'title': 'MySQL',
        'image': 'https://www.mysql.com/common/logos/logo-mysql-170x115.png',
        'description': 'Open-source relational database management system',
        'install_command': 'sudo apt-get install mysql-server'
    },
    {
        'title': 'PHP',
        'image': 'https://www.php.net/images/logos/new-php-logo.svg',
        'description': 'Popular general-purpose scripting language',
        'install_command': 'sudo apt-get install php'
    }
]

# Sample websites data
WEBSITES = ['example.com', 'test.com', 'mysite.org']

# Sample Node.js versions
NODEJS_VERSIONS = ['14.x', '16.x', '18.x']

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_files_and_folders(base_folder):
    items = []
    for root, dirs, files in os.walk(base_folder):
        for dir_name in dirs:
            folder_path = os.path.relpath(os.path.join(root, dir_name), base_folder)
            folder_perm = stat.filemode(os.stat(os.path.join(root, dir_name)).st_mode)
            items.append({'type': 'folder', 'name': folder_path, 'permissions': folder_perm})
        for filename in files:
            file_path = os.path.relpath(os.path.join(root, filename), base_folder)
            file_ext = os.path.splitext(filename)[1][1:]
            file_perm = stat.filemode(os.stat(os.path.join(root, filename)).st_mode)
            items.append({'type': 'file', 'name': file_path, 'extension': file_ext, 'permissions': file_perm})
    return items

def get_notification():
    try:
        response = requests.get("https://github.com/amatak-org/opensource-app/blob/main/kpanel_notic")
        if response.status_code == 200:
            return response.text
        else:
            return "Failed to fetch notification"
    except:
        return "Failed to fetch notification"

@app.route('/website')
def website():
    items = get_files_and_folders(app.config['UPLOAD_FOLDER'])
    notification = get_notification()

    return render_template('website.html'
    , items=items, websites=WEBSITES, nodejs_versions=NODEJS_VERSIONS, notification=notification)

# Your existing route handlers here

if __name__ == '__main__':
    app.run(debug=True)
