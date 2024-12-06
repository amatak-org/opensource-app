import sys
import tkinter as tk
from tkinter import messagebox
import subprocess
from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Kpanel server is running!"

def run_kpanel():
    app.run(host='0.0.0.0', port=5000)

def run_command(command):
    try:
        subprocess.run(command, shell=True, check=True)
        messagebox.showinfo("Success", f"Command '{command}' executed successfully.")
    except subprocess.CalledProcessError:
        messagebox.showerror("Error", f"Failed to execute command: {command}")

def stop_apache2_systemctl():
    run_command("sudo systemctl stop apache2")

def stop_apache2_service():
    run_command("sudo service apache2 stop")

def reload_apache2_service():
    run_command("sudo service apache2 reload")

def start_kpanel_server():
    threading.Thread(target=run_kpanel, daemon=True).start()
    messagebox.showinfo("Success", "Kapanel server started on port 5000")

root = tk.Tk()
root.title("Apache2 and Flask Control")
root.geometry("300x250")

tk.Button(root, text="Stop Apache2 (systemctl)", command=stop_apache2_systemctl).pack(pady=10)
tk.Button(root, text="Stop Apache2 (service)", command=stop_apache2_service).pack(pady=10)
tk.Button(root, text="Reload Apache2 (service)", command=reload_apache2_service).pack(pady=10)
tk.Button(root, text="Start kpanel Server", command=start_kpanel_server).pack(pady=10)

root.mainloop()
