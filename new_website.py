#!/usr/bin/env python3

import sys
import os
import subprocess
import argparse
import platform
import psutil
import configparser
import getpass
import re
import shutil

CONFIG_FILE = 'kpanel_config.ini'
NGINX_SITES_AVAILABLE = '/etc/nginx/sites-available/'
NGINX_SITES_ENABLED = '/etc/nginx/sites-enabled/'

def load_config():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
    else:
        config['USER'] = {'username': 'admin', 'password': 'password'}
        config['SERVER'] = {'bind_ip': '0.0.0.0'}
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
    return config

def save_config(config):
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

def start_server():
    print("Starting KPanel server...")
    subprocess.Popen(["python3", "server.py"])
    print("KPanel server started.")

def stop_server():
    print("Stopping KPanel server...")
    subprocess.run(["pkill", "-f", "server.py"])
    print("KPanel server stopped.")

def restart_panel():
    print("Restarting KPanel...")
    stop_server()
    start_server()

def repair_panel():
    print("Repairing KPanel...")
    
    # Update system packages
    print("Updating system packages...")
    subprocess.run(["sudo", "apt", "update"])
    subprocess.run(["sudo", "apt", "upgrade", "-y"])
    
    # Reinstall dependencies
    print("Reinstalling dependencies...")
    subprocess.run(["pip3", "install", "--upgrade", "pip"])
    subprocess.run(["pip3", "install", "-r", "requirements.txt"])
    
    # Check configurations
    print("Checking configurations...")
    config_files = ["server.py", CONFIG_FILE]
    for file in config_files:
        if os.path.exists(file):
            print(f"{file} exists.")
        else:
            print(f"Warning: {file} not found.")
    
    # Check permissions
    print("Checking permissions...")
    subprocess.run(["sudo", "chown", "-R", os.getenv("USER"), "."])
    subprocess.run(["sudo", "chmod", "-R", "755", "."])
    
    print("Repair completed.")

def reload_panel():
    print("Reloading KPanel configuration...")
    
    # For Gunicorn
    if subprocess.run(["pgrep", "-f", "gunicorn"]).returncode == 0:
        print("Reloading Gunicorn...")
        subprocess.run(["sudo", "systemctl", "reload", "gunicorn"])
    
    # For uWSGI
    elif subprocess.run(["pgrep", "-f", "uwsgi"]).returncode == 0:
        print("Reloading uWSGI...")
        subprocess.run(["sudo", "systemctl", "reload", "uwsgi"])
    
    # For Apache (mod_wsgi)
    elif subprocess.run(["pgrep", "-f", "apache2"]).returncode == 0:
        print("Reloading Apache...")
        subprocess.run(["sudo", "systemctl", "reload", "apache2"])
    
    else:
        print("No known WSGI server found. Attempting to restart the Python script...")
        restart_panel()

def panel_information():
    print("KPanel Information:")
    
    config = load_config()
    
    print(f"Username: {config['USER']['username']}")
    print(f"Bind IP: {config['SERVER']['bind_ip']}")
    
    # OS Information
    print(f"Operating System: {platform.system()} {platform.release()}")
    print(f"Distribution: {platform.dist()[0]} {platform.dist()[1]}")
    
    # Python Version
    print(f"Python Version: {platform.python_version()}")
    
    # CPU Information
    cpu_info = f"{psutil.cpu_count()} cores, {psutil.cpu_percent()}% utilized"
    print(f"CPU: {cpu_info}")
    
    # Memory Information
    memory = psutil.virtual_memory()
    memory_info = f"Total: {memory.total / (1024**3):.2f} GB, Used: {memory.percent}%"
    print(f"Memory: {memory_info}")
    
    # Disk Information
    disk = psutil.disk_usage('/')
    disk_info = f"Total: {disk.total / (1024**3):.2f} GB, Used: {disk.percent}%"
    print(f"Disk: {disk_info}")
    
    # KPanel Status
    if subprocess.run(["pgrep", "-f", "server.py"]).returncode == 0:
        print("KPanel Status: Running")
    else:
        print("KPanel Status: Stopped")

def reset_username():
    config = load_config()
    new_username = input("Enter new username: ")
    config['USER']['username'] = new_username
    save_config(config)
    print("Username updated successfully.")

def reset_password():
    config = load_config()
    new_password = getpass.getpass("Enter new password: ")
    confirm_password = getpass.getpass("Confirm new password: ")
    if new_password == confirm_password:
        config['USER']['password'] = new_password
        save_config(config)
        print("Password updated successfully.")
    else:
        print("Passwords do not match. Password not updated.")

def bind_ip_address():
    config = load_config()
    while True:
        new_ip = input("Enter new IP address to bind (or 'cancel' to abort): ")
        if new_ip.lower() == 'cancel':
            print("Operation cancelled.")
            return
        if re.match(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$", new_ip):
            config['SERVER']['bind_ip'] = new_ip
            save_config(config)
            print(f"Server will now bind to IP: {new_ip}")
            print("Please restart the server for changes to take effect.")
            break
        else:
            print("Invalid IP address format. Please try again.")

def create_website():
    domain = input("Enter the domain name for the new website: ")
    environment = input("Select environment (nodejs/python/other): ").lower()

    # Create website directory
    web_dir = f"/var/www/{domain}"
    os.makedirs(web_dir, exist_ok=True)

    # Set up environment
    if environment == "nodejs":
        setup_nodejs(web_dir)
    elif environment == "python":
        setup_python(web_dir)
    else:
        print(f"Setting up a basic environment for {environment}")
        with open(f"{web_dir}/index.html", 'w') as f:
            f.write(f"<h1>Welcome to {domain}</h1>")

    # Set up Nginx configuration
    nginx_config = f"""
    server {{
        listen 80;
        server_name {domain};
        root {web_dir};
        index index.html index.htm;

        location / {{
            try_files $uri $uri/ =404;
        }}
    }}
    """

    with open(f"{NGINX_SITES_AVAILABLE}{domain}", 'w') as f:
        f.write(nginx_config)

    # Enable the site
    os.symlink(f"{NGINX_SITES_AVAILABLE}{domain}", f"{NGINX_SITES_ENABLED}{domain}")

    # Reload Nginx
    subprocess.run(["sudo", "nginx", "-s", "reload"])

    print(f"Website {domain} created successfully!")

def setup_nodejs(web_dir):
    if shutil.which("node") is None:
        print("Node.js not found. Installing...")
        subprocess.run(["sudo", "apt", "update"])
        subprocess.run(["sudo", "apt", "install", "nodejs", "npm", "-y"])
    
    # Initialize a new Node.js project
    os.chdir(web_dir)
    subprocess.run(["npm", "init", "-y"])
    
    # Install Express.js
    subprocess.run(["npm", "install", "express"])
    
    # Create a basic Express.js app
    with open(f"{web_dir}/app.js", 'w') as f:
        f.write('''
const express = require('express');
const app = express();
const port = 3000;

app.get('/', (req, res) => {
  res.send('Hello World!');
});

app.listen(port, () => {
  console.log(`App listening at http://localhost:${port}`);
});
        ''')

def setup_python(web_dir):
    if shutil.which("python3") is None:
        print("Python3 not found. Installing...")
        subprocess.run(["sudo", "apt", "update"])
        subprocess.run(["sudo", "apt", "install", "python3", "python3-pip", "-y"])
    
    # Create a virtual environment
    subprocess.run(["python3", "-m", "venv", f"{web_dir}/venv"])
    
    # Activate the virtual environment and install Flask
    activate_this = f"{web_dir}/venv/bin/activate_this.py"
    exec(open(activate_this).read(), {'__file__': activate_this})
    
    subprocess.run(["pip", "install", "flask"])
    
    # Create a basic Flask app
    with open(f"{web_dir}/app.py", 'w') as f:
        f.write('''
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

if __name__ == '__main__':
    app.run(host='0.0.0.0')
        ''')

def main():
    parser = argparse.ArgumentParser(description="KPanel Management Tool")
    parser.add_argument("command", nargs="?", help="Command to execute")

    args = parser.parse_args()

    if args.command == "server":
        subcommand = input("Enter subcommand (start/stop): ")
        if subcommand == "start":
            start_server()
        elif subcommand == "stop":
            stop_server()
        else:
            print("Invalid subcommand. Use 'start' or 'stop'.")
    elif not args.command:
        while True:
            print("\nKPanel Management Options:")
            print("1. Start server")
            print("2. Stop server")
            print("3. Restart panel")
            print("4. Repair panel")
            print("5. Reload panel")
            print("6. Panel information")
            print("7. Reset username")
            print("8. Reset password")
            print("9. Bind IP address")
            print("10. Create new website")
            print("0. Exit")

            choice = input("Enter your choice (0-10): ")

            if choice == "1":
                start_server()
            elif choice == "2":
                stop_server()
            elif choice == "3":
                restart_panel()
            elif choice == "4":
                repair_panel()
            elif choice == "5":
                reload_panel()
            elif choice == "6":
                panel_information()
            elif choice == "7":
                reset_username()
            elif choice == "8":
                reset_password()
            elif choice == "9":
                bind_ip_address()
            elif choice == "10":
                create_website()
            elif choice == "0":
                print("Exiting KPanel Management Tool.")
                break
            else:
                print("Invalid choice. Please try again.")
    else:
        print(f"Unknown command: {args.command}")

if __name__ == "__main__":
    main()
