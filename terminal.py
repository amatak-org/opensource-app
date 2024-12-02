from flask import Flask, request, redirect, url_for, flash, render_template_string, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import os
import stat
import shutil
import zipfile
import subprocess
import json
import requests
import pty
import select
import termios
import struct
import fcntl

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit max upload size to 16MB
app.config['WEBSITE_ROOT'] = '/var/www/html'

socketio = SocketIO(app)

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
        <title>Website Management System</title>
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
            #terminal {
                background-color: #000;
                color: #fff;
                padding: 10px;
                font-family: monospace;
                height: 300px;
                overflow-y: scroll;
            }
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    </head>
    <body>
        <header>
            <h1>Website Management System</h1>
        </header>
        <div class="container">
            <div class="sidebar">
                <h3>Manage Websites</h3>
                <a href="#" onclick="showContent('files')">Files</a>
                <a href="#" onclick="showContent('nginx')">Nginx</a>
                <a href="#" onclick="showContent('python')">Python</a>
                <a href="#" onclick="showContent('nodejs')">Node.js</a>
                <a href="#" onclick="showContent('ufw')">UFW</a>
                <a href="#" onclick="showContent('terminal')">Terminal</a>
            </div>
            <div class="content">
                <div id="files" class="tabcontent">
                    <h2>Website Files</h2>
                    <select id="website-select" onchange="loadWebsiteFiles()">
                        {% for website in websites %}
                            <option value="{{ website }}">{{ website }}</option>
                        {% endfor %}
                    </select>
                    <div id="website-files"></div>
                </div>
                
                <div id="nginx" class="tabcontent">
                    <h2>Nginx Configuration</h2>
                    <button onclick="editNginxConfig()">Edit Nginx Config</button>
                    <button onclick="manageSSL()">Manage SSL</button>
                </div>
                
                <div id="python" class="tabcontent">
                    <h2>Python Environment</h2>
                    <select id="python-website-select">
                        {% for website in websites %}
                            <option value="{{ website }}">{{ website }}</option>
                        {% endfor %}
                    </select>
                    <button onclick="setupPythonEnv()">Setup Python Environment</button>
                </div>
                
                <div id="nodejs" class="tabcontent">
                    <h2>Node.js Installation</h2>
                    <select id="nodejs-version-select">
                        {% for version in nodejs_versions %}
                            <option value="{{ version }}">{{ version }}</option>
                        {% endfor %}
                    </select>
                    <button onclick="installNodejs()">Install Node.js</button>
                </div>
                
                <div id="ufw" class="tabcontent">
                    <h2>UFW Firewall</h2>
                    <input type="text" id="port-number" placeholder="Enter port number">
                    <button onclick="allowPort()">Allow Port</button>
                </div>

                <div id="terminal" class="tabcontent">
                    <h2>Linux Terminal</h2>
                    <div id="terminal-output"></div>
                    <input type="text" id="terminal-input" placeholder="Enter command">
                    <button onclick="sendCommand()">Send</button>
                </div>
            </div>
        </div>
        <footer>
            &copy; 2023 Website Management System
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
            var socket = io();
            
            socket.on('terminal_output', function(data) {
                var terminal = document.getElementById('terminal-output');
                terminal.innerHTML += data;
                terminal.scrollTop = terminal.scrollHeight;
            });

            function showContent(contentId) {
                var tabcontent = document.getElementsByClassName("tabcontent");
                for (var i = 0; i < tabcontent.length; i++) {
                    tabcontent[i].style.display = "none";
                }
                document.getElementById(contentId).style.display = "block";
            }

            function loadWebsiteFiles() {
                var website = document.getElementById("website-select").value;
                // Add logic to load and display website files
                document.getElementById("website-files").innerHTML = "Loading files for " + website + "...";
            }

            function editNginxConfig() {
                // Add logic to edit Nginx config
                alert("Editing Nginx config...");
            }

            function manageSSL() {
                // Add logic to manage SSL
                alert("Managing SSL...");
            }

            function setupPythonEnv() {
                var website = document.getElementById("python-website-select").value;
                // Add logic to setup Python environment
                alert("Setting up Python environment for " + website + "...");
            }

            function installNodejs() {
                var version = document.getElementById("nodejs-version-select").value;
                // Add logic to install Node.js
                alert("Installing Node.js version " + version + "...");
            }

            function allowPort() {
                var port = document.getElementById("port-number").value;
                // Add logic to allow port in UFW
                alert("Allowing port " + port + " in UFW...");
            }

            function sendCommand() {
                var command = document.getElementById('terminal-input').value;
                socket.emit('terminal_input', {data: command});
                document.getElementById('terminal-input').value = '';
            }

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
    ''', items=items, websites=WEBSITES, nodejs_versions=NODEJS_VERSIONS, notification=notification)

@socketio.on('terminal_input')
def terminal_input(data):
    command = data['data']
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        emit('terminal_output', output.decode())
    except subprocess.CalledProcessError as e:
        emit('terminal_output', e.output.decode())

# Your existing route handlers here

if __name__ == '__main__':
    socketio.run(app, debug=True)
