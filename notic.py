from flask import Flask, request, redirect, url_for, flash, render_template_string, jsonify, send_from_directory
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

@app.route('/')
def index():
    items = get_files_and_folders(app.config['UPLOAD_FOLDER'])
    notification = get_notification()

    return render_template_string('''
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>File Management and Database System</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                flex-direction: column;
                min-height: 100vh;
            }
            header {
                background: #2c3e50;
                color: white;
                padding: 10px;
                text-align: center;
            }
            .container {
                display: flex;
                flex-grow: 1;
            }
            .sidebar {
                background-color: #ecf0f1;
                width: 200px;
                padding: 20px;
            }
            .sidebar a {
                color: #333;
                text-decoration: none;
                padding: 10px;
                display: block;
                margin: 5px 0;
                border-radius: 4px;
            }
            .sidebar a:hover {
                background-color: #ddd;
            }
            .content {
                padding: 20px;
                flex-grow: 1;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            th, td {
                padding: 10px;
                border: 1px solid #ddd;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
            .app-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 20px;
                padding: 20px;
            }
            .app-card {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            }
            .app-card img {
                max-width: 100%;
                height: auto;
            }
            .install-btn {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 4px;
            }
            .tab {
                overflow: hidden;
                border: 1px solid #ccc;
                background-color: #f1f1f1;
            }
            .tab button {
                background-color: inherit;
                float: left;
                border: none;
                outline: none;
                cursor: pointer;
                padding: 14px 16px;
                transition: 0.3s;
            }
            .tab button:hover {
                background-color: #ddd;
            }
            .tab button.active {
                background-color: #ccc;
            }
            .tabcontent {
                display: none;
                padding: 6px 12px;
                border: 1px solid #ccc;
                border-top: none;
            }
            footer {
                background-color: #2c3e50;
                color: white;
                text-align: center;
                padding: 10px;
                position: relative;
            }
            #notification-btn {
                position: absolute;
                right: 10px;
                bottom: 10px;
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                cursor: pointer;
                border-radius: 4px;
            }
            .modal {
                display: none;
                position: fixed;
                z-index: 1;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                overflow: auto;
                background-color: rgba(0,0,0,0.4);
            }
            .modal-content {
                background-color: #fefefe;
                margin: 15% auto;
                padding: 20px;
                border: 1px solid #888;
                width: 80%;
            }
            .close {
                color: #aaa;
                float: right;
                font-size: 28px;
                font-weight: bold;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <header>
            <h1>File Management and Database System</h1>
        </header>
        <div class="container">
            <div class="sidebar">
                <h3>Manage Files</h3>
                <a href="{{ url_for('index') }}">Home</a>
                <a href="{{ url_for('upload_file_action') }}">Upload File</a>
                <a href="#" onclick="showAppStore()">App Store</a>
                <a href="#" onclick="showDatabaseManager()">Database Manager</a>
            </div>
            <div class="content">
                <!-- Content of your application -->
            </div>
        </div>
        <footer>
            &copy; 2023 File Management and Database System
            <button id="notification-btn" onclick="showNotification()">Notification</button>
        </footer>

        <div id="notificationModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeNotification()">&times;</span>
                <p id="notification-text"></p>
                <a href="https://github.com/amatak-org/opensource-app" target="_blank">More information</a>
            </div>
        </div>

        <script>
            // Your existing JavaScript functions here

            function showNotification() {
                var modal = document.getElementById("notificationModal");
                var notificationText = document.getElementById("notification-text");
                notificationText.innerHTML = `{{ notification|safe }}`;
                modal.style.display = "block";
            }

            function closeNotification() {
                var modal = document.getElementById("notificationModal");
                modal.style.display = "none";
            }

            window.onload = function() {
                setTimeout(showNotification, 3000);
            }

            window.onclick = function(event) {
                var modal = document.getElementById("notificationModal");
                if (event.target == modal) {
                    modal.style.display = "none";
                }
            }
        </script>
    </body>
    </html>
    ''', items=items, appstore=APPSTORE, websites=WEBSITES, notification=notification)

# Your existing route handlers here

if __name__ == '__main__':
    app.run(debug=True)
