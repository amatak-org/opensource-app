from flask import Flask, request, redirect, url_for, flash, render_template_string, jsonify
from werkzeug.utils import secure_filename
import os
import stat
import shutil
import zipfile
import subprocess

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit max upload size to 16MB

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

ALLOWED_EXTENSIONS = {'txt', 'py', 'html', 'css', 'js', 'md', 'xlsm', 'pdf'}

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

def get_ufw_status():
    try:
        output = subprocess.check_output(['sudo', 'ufw', 'status', 'numbered']).decode('utf-8')
        return output
    except subprocess.CalledProcessError:
        return "Unable to get UFW status"

@app.route('/')
def index():
    items = get_files_and_folders(app.config['UPLOAD_FOLDER'])
    ufw_status = get_ufw_status()

    return render_template_string('''
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>File Management and Firewall System</title>
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
            }
            .close:hover,
            .close:focus {
                color: black;
                text-decoration: none;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <header>
            <h1>File Management and Firewall System</h1>
        </header>
        <div class="container">
            <div class="sidebar">
                <h3>Manage Files</h3>
                <a href="{{ url_for('index') }}">Home</a>
                <a href="{{ url_for('upload_file_action') }}">Upload File</a>
                <a href="#" onclick="openFirewallModal()">Firewall Settings</a>
            </div>
            <div class="content">
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
        </div>

        <div id="firewallModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeFirewallModal()">&times;</span>
                <h2>Firewall Settings</h2>
                <pre id="ufwStatus">{{ ufw_status }}</pre>
                <button onclick="refreshUfwStatus()">Refresh Status</button>
            </div>
        </div>

        <script>
            function openFirewallModal() {
                document.getElementById('firewallModal').style.display = 'block';
            }

            function closeFirewallModal() {
                document.getElementById('firewallModal').style.display = 'none';
            }

            function refreshUfwStatus() {
                fetch('/ufw_status')
                    .then(response => response.text())
                    .then(data => {
                        document.getElementById('ufwStatus').textContent = data;
                    });
            }

            window.onclick = function(event) {
                if (event.target == document.getElementById('firewallModal')) {
                    closeFirewallModal();
                }
            }
        </script>
    </body>
    </html>
    ''', items=items, ufw_status=ufw_status)

@app.route('/ufw_status')
def ufw_status():
    return get_ufw_status()

@app.route('/', methods=['POST'])
def upload_file_action():
    if 'file' not in request.files:
        flash('No file selected. Please choose a file to upload.')
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        flash('No file selected. Please choose a file to upload.')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash('File successfully uploaded')
        return redirect(url_for('index'))
    else:
        flash('File type not allowed. Please upload a valid file.')
        return redirect(request.url)

@app.route('/perform_action', methods=['POST'])
def perform_action():
    action = request.form['action']
    selected_items = request.form.getlist('selected_items')

    if action == 'Delete':
        for name in selected_items:
            item_path = os.path.join(app.config['UPLOAD_FOLDER'], name)
            if os.path.isfile(item_path):
                os.remove(item_path)
                flash(f'File {name} successfully deleted.')
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
                flash(f'Folder {name} successfully deleted.')

    return redirect(url_for('index'))

@app.route('/view/<path:filename>')
def view_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/view_folder/<path:foldername>')
def view_folder(foldername):
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], foldername)
    items = get_files_and_folders(folder_path)
    return render_template_string('''
    <!doctype html>
    <title>Folder Details</title>
    <h1>Details of Folder: {{ foldername }}</h1>
    <table border="1">
        <tr>
            <th>#</th>
            <th>Type</th>
            <th>Name</th>
            <th>File Extension</th>
            <th>Permissions</th>
        </tr>
        {% for item in items %}
        <tr>
            <td>{{ loop.index }}</td>
            <td>{{ item.type }}</td>
            <td>{{ item.name }}</td>
            <td>{{ item.extension if item.type == 'file' else '-' }}</td>
            <td>{{ item.permissions }}</td>
        </tr>
        {% endfor %}
    </table>
    <a href="{{ url_for('index') }}">Back to Main</a>
    ''', items=items, foldername=foldername)

@app.route('/zip/<path:filename>', methods=['POST'])
def zip_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    zip_path = f"{file_path}.zip"
    
    with zipfile.ZipFile(zip_path, 'w') as zip_file:
        zip_file.write(file_path, os.path.basename(file_path))

    flash(f'File {filename} successfully zipped.')
    return redirect(url_for('index'))

@app.route('/unzip/<path:filename>', methods=['POST'])
def unzip_file(filename):
    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    extract_folder = os.path.splitext(zip_path)[0]  # Removing .zip extension

    with zipfile.ZipFile(zip_path, 'r') as zip_file:
        zip_file.extractall(extract_folder)

    flash(f'File {filename} successfully unzipped.')
    return redirect(url_for('index'))

@app.route('/download/<path:filename>', methods=['POST'])
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
