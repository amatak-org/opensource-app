#!/usr/bin/env python3
import os
import subprocess
import sys
import socket
import shutil
from flask import Flask, render_template_string

app = Flask(__name__)

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    return output.decode('utf-8'), error.decode('utf-8')



def setup_venv():
    print("Setting up virtual environment...")
    run_command("python3 -m venv .venv")
    run_command("source .venv/bin/activate")

def clone_repo():
    print("Cloning repository...")
    run_command("git clone https://github.com/amatak-org/kpanel_v1.git")
    run_command("unzip kpanel_v1-main.zip")
    os.chdir("kpanel_v1")
    
def copy_and_rename_folder():
    source = 'kpanel_v1'
    destination = '/var/www/kpanel'

    # Copy folder
    shutil.copytree(source, destination)

    print(f"Copied {source} to {destination}")

def generate_nginx_config():
    nginx_config = """
server {
    listen 80;
    server_name demo.kpanel.amatak.cloud;

    root /var/www/kpanel;

    location / {
        try_files $uri $uri/ =404;
    }
}
"""
    config_path = '/etc/nginx/sites-available/kpanel.config'
    
    with open(config_path, 'w') as config_file:
        config_file.write(nginx_config)

    # Create symlink to sites-enabled
    os.system(f"ln -s {config_path} /etc/nginx/sites-enabled/kpanel")

    print("Nginx configuration generated and syml")


def install_requirements():
    print("Installing requirements...")
    run_command("pip install -r requirements.txt")

def start_kpanel():
    print("Starting kpanel...")
    run_command("python kpanel.py")

def main():
    setup_venv()
    clone_repo()
    copy_and_rename_folder()
    generate_nginx_config()
    install_requirements()
    start_kpanel()
    

#if __name__ == '__main__':
    #copy_and_rename_folder()
   # generate_nginx_config()
