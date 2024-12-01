import os
import stat
import shutil
import zipfile
import requests
import socket
import subprocess
from datetime import datetime
from flask import Flask, request, redirect, url_for, flash, render_template_string, send_from_directory,render_template,render_template, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash




app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 1600 * 1024 * 1024  # Limit max upload size to 16MB

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

ALLOWED_EXTENSIONS = {'txt', 'py', 'html', 'css', 'js', 'md', 'xlsm', 'md','pdf','zip', 'jpg', 'jpeg', 'png', 'gif'}


CURRENT_VERSION = '1.0.1'
GITHUB_API_URL = "https://api.github.com/repos/yourusername/yourrepo/releases/latest"  # Update with your repo

###FOR DEMO ####
# Mock user data for testing
app.config['USER_DATA'] = {
    'user1': generate_password_hash('password1'),
    'user2': generate_password_hash('password2')
}

# Mock file system structure for testing
mock_files = [
    {'type': 'file', 'name': 'document1.txt', 'extension': 'txt', 'permissions': '-rw-r--r--'},
    {'type': 'file', 'name': 'script.py', 'extension': 'py', 'permissions': '-rw-r--r--'},
    {'type': 'folder', 'name': 'Subfolder1', 'permissions': 'drwxr-xr-x'},
    {'type': 'folder', 'name': 'Subfolder2', 'permissions': 'drwxr-xr-x'},
]

def get_files_and_folders(base_folder):
    return mock_files  # Return mock data inst

@app.route('/demo')
def demo():
    items = get_files_and_folders(app.config['UPLOAD_FOLDER'])
    return render_template('demo.html', items=items)
#### END DEMO SET

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
    server_ip = get_server_ip()
    server_info = get_server_info()
    return render_template('index.html' ,server_ip=get_server_ip(), server_info=get_server_info() ,items=items, current_year=datetime.now().year) 



    ## server detail
def get_server_ip():
    return socket.gethostbyname(socket.gethostname())

def get_server_info():
    # For demonstration purposes, return mock data
    #cpu_info = subprocess.check_output("lscpu", shell=True).decode()
   # memory_info = subprocess.check_output("free -m", shell=True).decode()
    #disk_usage = subprocess.check_output("df -h", shell=True).decode()
   
   return {
        'mock_files'
    }
   ## end server detail mock_files
   
   ### use this on liver server for real live server
    #return {
        #'cpu_info': cpu_info,
        #'memory_info': memory_info,
        #'disk_usage': disk_usage
    #}
      ## end server detail mock_files
    

    
#user
@app.route('/user')
def user():
    logged_in = 'username' in session
    items = get_files_and_folders(app.config['UPLOAD_FOLDER'])
    return render_template('user.html',items=items)

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    password = request.form['password']

    if username in app.config['USER_DATA']:
        flash('User already exists.')
    else:
        hashed_password = generate_password_hash(password)
        app.config['USER_DATA'][username] = hashed_password
        flash('User successfully created. Please verify your email.')

    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if username in app.config['USER_DATA'] and check_password_hash(app.config['USER_DATA'][username], password):
        session['username'] = username
        flash('Login successful.')
        return redirect(url_for('index'))
    else:
        flash('Invalid username or password.')
    
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/profile')
def profile():
    username = session.get('username')
    if not username:
        flash('You must be logged in to view your profile.')
        return redirect(url_for('login'))

    return render_template_string('''
    <!doctype html>
    <title>User Profile</title>
    <h2>User Profile for {{ username }}</h2>
    <p>Manage your settings and account details here.</p>
    <a href="{{ url_for('index') }}">Back to Home</a>
    ''', username=username)

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
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if os.path.exists(file_path):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    else:
        flash('File not found.')
        return redirect(url_for('index'))

@app.route('/view_folder/<path:foldername>')
def view_folder(foldername):
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], foldername)

    if os.path.exists(folder_path):
        items = get_files_and_folders(folder_path)
        return render_template_string('''
        <!doctype html>
        <title>Folder Details</title>
        <h1>Details of Folder: {{ foldername }}</h1>

        <h2>Files and Subfolders</h2>
        <table border="1">
            <tr>
                <th>#</th>
                <th>Type</th>
                <th>Name</th>
                <th>File Extension</th>
                <th>Path</th>
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
                        <input type="submit" name="action" value="Delete" onclick="return confirm('Are you sure you want to delete this item?');">
                    </form>
                </td>
            </tr>
            {% endfor %}
        </table>

        <a href="{{ url_for('index') }}">Back to Main</a>
        ''', items=items, foldername=foldername)
    else:
        flash('Folder not found.')
        return redirect(url_for('index'))

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

##### end user


# Nginx App
@app.route('/control_nginx', methods=['POST'])
def control_nginx():
    action = request.form['action']
    try:
        if action == 'Start Nginx':
            subprocess.run(['sudo', 'systemctl', 'start', 'nginx'], check=True)
            flash('Nginx started successfully.')
        elif action == 'Stop Nginx':
            subprocess.run(['sudo', 'systemctl', 'stop', 'nginx'], check=True)
            flash('Nginx stopped successfully.')
        elif action == 'Restart Nginx':
            subprocess.run(['sudo', 'systemctl', 'restart', 'nginx'], check=True)
            flash('Nginx restarted successfully.')
    except Exception as e:
        flash(f'Error controlling Nginx: {str(e)}')

    return redirect(url_for('index'))

# end Nginx


###Console App
@app.route('/console')
def console():
    items = get_files_and_folders(app.config['UPLOAD_FOLDER'])

    return render_template_string('''
    
               
    ''', items=items)
### End console

### Check update
@app.route('/new_version')
def new_version():
    items = get_files_and_folders(app.config['UPLOAD_FOLDER'])
    new_version = check_for_updates()

    return render_template('check_update.html', items=items, new_version=check_for_updates())

@app.route('/check_for_updates')
def check_for_updates():
    # Replace with your real GitHub repository URL
    response = requests.get("https://api.github.com/repos/yourusername/yourrepo/releases/latest")
    if response.status_code == 200:
        latest_version = response.json()['tag_name']
        return latest_version if latest_version != CURRENT_VERSION else None
    return None

## end check update.

if __name__ == '__main__':
    app.run(debug=True)
