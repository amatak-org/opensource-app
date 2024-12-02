from flask import Flask, request, redirect, url_for, flash, render_template_string, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
import stat
import shutil
import zipfile
import subprocess
import json

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

@app.route('/')
def index():
    items = get_files_and_folders(app.config['UPLOAD_FOLDER'])

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
                height: 100vh;
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
                height: 100%;
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
                <div id="file-management">
                    <h2>Files and Folders</h2>
                    <form method="post" enctype="multipart/form-data" action="{{ url_for('upload_file_action') }}">
                        <input type="file" name="file" required>
                        <input type="submit" value="Upload">
                    </form>
                    <table>
                        <tr>
                            <th>#</th>
                            <th>Type</th>
                            <th>Name</th>
                            <th>File Extension</th>
                            <th>Permissions</th>
                            <th>Actions</th>
                        </tr>
                        {% for item in items %}
                        <tr>
                            <td>{{ loop.index }}</td>
                            <td>{{ item.type }}</td>
                            <td>
                                {% if item.type == 'file' %}
                                    <a href="{{ url_for('view_file', filename=item.name) }}">{{ item.name }}</a>
                                {% else %}
                                    <a href="{{ url_for('view_folder', foldername=item.name) }}">{{ item.name }}</a>
                                {% endif %}
                            </td>
                            <td>{{ item.extension if item.type == 'file' else '-' }}</td>
                            <td>{{ item.permissions }}</td>
                            <td>
                                <form method="POST" action="{{ url_for('perform_action') }}" style="display:inline;">
                                    <input type="checkbox" name="selected_items" value="{{ item.name }}" style="display:none;">
                                    <input type="submit" name="action" value="Delete" onclick="return confirm('Are you sure you want to delete this item?');">
                                </form>
                                {% if item.type == 'file' %}
                                    <form method="POST" action="{{ url_for('zip_file', filename=item.name) }}" style="display:inline;">
                                        <input type="submit" value="Zip">
                                    </form>
                                    <form method="POST" action="{{ url_for('unzip_file', filename=item.name) }}" style="display:inline;">
                                        <input type="submit" value="Unzip">
                                    </form>
                                    <form method="POST" action="{{ url_for('download_file', filename=item.name) }}" style="display:inline;">
                                        <input type="submit" value="Download">
                                    </form>
                                {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </table>
                </div>
                <div id="app-store" style="display:none;">
                    <h2>App Store</h2>
                    <div class="app-grid">
                        {% for app in appstore %}
                        <div class="app-card">
                            <img src="{{ app.image }}" alt="{{ app.title }}">
                            <h3>{{ app.title }}</h3>
                            <p>{{ app.description }}</p>
                            <button class="install-btn" onclick="installApp('{{ app.install_command }}')">Install</button>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                <div id="database-manager" style="display:none;">
                    <h2>Database Manager</h2>
                    <div class="tab">
                        <button class="tablinks" onclick="openTab(event, 'Create')">Create</button>
                        <button class="tablinks" onclick="openTab(event, 'Delete')">Delete</button>
                        <button class="tablinks" onclick="openTab(event, 'UpdatePassword')">Update Password</button>
                        <button class="tablinks" onclick="openTab(event, 'ResetRoot')">Reset Root Password</button>
                        <button class="tablinks" onclick="openTab(event, 'SSL')">SSL</button>
                    </div>

                    <div id="Create" class="tabcontent">
                        <h3>Create Database</h3>
                        <input type="text" id="create-db-name" placeholder="Database Name">
                        <button onclick="createDatabase()">Create</button>
                    </div>

                    <div id="Delete" class="tabcontent">
                        <h3>Delete Database</h3>
                        <input type="text" id="delete-db-name" placeholder="Database Name">
                        <button onclick="deleteDatabase()">Delete</button>
                    </div>

                    <div id="UpdatePassword" class="tabcontent">
                        <h3>Update Password</h3>
                        <input type="text" id="update-password-db" placeholder="Database Name">
                        <input type="password" id="new-password" placeholder="New Password">
                        <button onclick="updatePassword()">Update</button>
                    </div>

                    <div id="ResetRoot" class="tabcontent">
                        <h3>Reset Root Password</h3>
                        <input type="password" id="new-root-password" placeholder="New Root Password">
                        <button onclick="resetRootPassword()">Reset</button>
                    </div>

                    <div id="SSL" class="tabcontent">
                        <h3>SSL Configuration</h3>
                        <button onclick="configureSSL()">Configure SSL</button>
                    </div>

                    <h3>Apply to Website</h3>
                    <select id="website-select">
                        {% for website in websites %}
                            <option value="{{ website }}">{{ website }}</option>
                        {% endfor %}
                    </select>
                    <button onclick="applyToWebsite()">Apply</button>
                </div>
            </div>
        </div>
        <script>
            function showAppStore() {
                document.getElementById('file-management').style.display = 'none';
                document.getElementById('app-store').style.display = 'block';
                document.getElementById('database-manager').style.display = 'none';
            }

            function showDatabaseManager() {
                document.getElementById('file-management').style.display = 'none';
                document.getElementById('app-store').style.display = 'none';
                document.getElementById('database-manager').style.display = 'block';
            }

            function installApp(command) {
                fetch('/install_app', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({command: command}),
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                })
                .catch((error) => {
                    console.error('Error:', error);
                });
            }

            function openTab(evt, tabName) {
                var i, tabcontent, tablinks;
                tabcontent = document.getElementsByClassName("tabcontent");
                for (i = 0; i < tabcontent.length; i++) {
                    tabcontent[i].style.display = "none";
                }
                tablinks = document.getElementsByClassName("tablinks");
                for (i = 0; i < tablinks.length; i++) {
                    tablinks[i].className = tablinks[i].className.replace(" active", "");
                }
                document.getElementById(tabName).style.display = "block";
                evt.currentTarget.className += " active";
            }

            function createDatabase() {
                var dbName = document.getElementById('create-db-name').value;
                // Add logic to create database
                alert('Creating database: ' + dbName);
            }

            function deleteDatabase() {
                var dbName = document.getElementById('delete-db-name').value;
                // Add logic to delete database
                alert('Deleting database: ' + dbName);
            }

            function updatePassword() {
                var dbName = document.getElementById('update-password-db').value;
                var newPassword = document.getElementById('new-password').value;
                // Add logic to update password
                alert('Updating password for database: ' + dbName);
            }

            function resetRootPassword() {
                var newRootPassword = document.getElementById('new-root-password').value;
                // Add logic to reset root password
                alert('Resetting root password');
            }

            function configureSSL() {
                // Add logic to configure SSL
                alert('Configuring SSL');
            }

            function applyToWebsite() {
                var website = document.getElementById('website-select').value;
                // Add logic to apply database changes to selected website
                alert('Applying changes to website: ' + website);
            }
        </script>
    </body>
    </html>
    ''', items=items, appstore=APPSTORE, websites=WEBSITES)

@app.route('/install_app', methods=['POST'])
def install_app():
    data = request.json
    command = data.get('comman
