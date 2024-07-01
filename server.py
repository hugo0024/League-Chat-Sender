import os
import threading
import webbrowser
from tkinter import Tk, Label, Button
from flask import Flask, request, render_template_string, jsonify
import ctypes
import time
import pygetwindow as gw
import pywinauto
import atexit
import socket

app = Flask(__name__)

# HTML template for the web page with improved styling and responsiveness
html_template = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>League Chat Sender</title>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <style>
      body {
        font-family: Arial, sans-serif;
        background-color: #f4f4f9;
        margin: 0;
        padding: 0;
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
      }
      .container {
        background-color: #fff;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        width: 90%;
        max-width: 400px;
        text-align: center;
        box-sizing: border-box;
      }
      h1 {
        font-size: 24px;
        margin-bottom: 20px;
      }
      label {
        display: block;
        margin-bottom: 8px;
        font-weight: bold;
      }
      input[type="text"] {
        width: 100%;
        padding: 12px;
        margin-bottom: 10px;
        border: 1px solid #ccc;
        border-radius: 4px;
        font-size: 16px;
        box-sizing: border-box;
      }
      input[type="checkbox"] {
        margin-right: 8px;
      }
      input[type="submit"] {
        background-color: #007bff;
        color: #fff;
        border: none;
        padding: 12px 20px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 16px;
      }
      input[type="submit"]:hover {
        background-color: #0056b3;
      }
      #responseMessage {
        margin-top: 20px;
        color: green;
        font-weight: bold;
      }
      @media (max-width: 600px) {
        h1 {
          font-size: 20px;
        }
        input[type="text"] {
          padding: 10px;
          font-size: 14px;
        }
        input[type="submit"] {
          padding: 10px 16px;
          font-size: 14px;
        }
      }
    </style>
  </head>
  <body>
    <div class="container">
      <h1>Send Message to League Chat</h1>
      <form id="messageForm">
        <label for="message">Message:</label>
        <input type="text" id="message" name="message" required>
        <input type="checkbox" id="allChat" name="allChat" checked>
        <label for="allChat">Send to all chat</label><br><br>
        <input type="submit" value="Send">
      </form>
      <p id="responseMessage"></p>
    </div>
    <script>
      $(document).ready(function() {
        $('#messageForm').on('submit', function(event) {
          event.preventDefault();
          $.ajax({
            type: 'POST',
            url: '/send',
            data: $(this).serialize(),
            success: function(response) {
              $('#responseMessage').text(response.message);
              $('#message').val('');  // Clear the message input field
            }
          });
        });
      });
    </script>
  </body>
</html>
"""

# C struct redefinitions
PUL = ctypes.POINTER(ctypes.c_ulong)

class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time",ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]

# Actual Functions
def press_key(hexKeyCode):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, hexKeyCode, 0x0008, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def release_key(hexKeyCode):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, hexKeyCode, 0x0008 | 0x0002, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def send_message(message, all_chat):
    # Find the League of Legends window
    windows = gw.getWindowsWithTitle('League of Legends')
    if windows:
        league_window = windows[0]
        # Ensure the window is activated
        league_window.activate()
        time.sleep(0.1)  # Add a small delay to ensure the window is focused
        app = pywinauto.Application().connect(handle=league_window._hWnd)
        window = app.window(handle=league_window._hWnd)
        window.set_focus()
        
        # Open chat
        window.type_keys('{ENTER}', with_spaces=True, pause=0.01)
        
        # Type /all if all_chat is enabled
        if all_chat:
            window.type_keys('/all ', with_spaces=True, pause=0.01)
        
        # Type the message
        window.type_keys(message, with_spaces=True, pause=0.01)
        
        # Send the message
        window.type_keys('{ENTER}', with_spaces=True, pause=0.01)
    else:
        print("League of Legends window not found.")

@app.route('/')
def index():
    return render_template_string(html_template)

@app.route('/send', methods=['POST'])
def send():
    message = request.form['message']
    all_chat = 'allChat' in request.form
    send_message(message, all_chat)
    return jsonify({'message': 'Message sent!'})

def start_server():
    app.run(host='0.0.0.0', port=5000)

def open_browser():
    webbrowser.open('http://localhost:5000')

def start_flask():
    global flask_thread
    flask_thread = threading.Thread(target=start_server)
    flask_thread.start()

def stop_flask():
    os._exit(0)

def toggle_server(button):
    if button["text"] == "Start Server":
        start_flask()
        button["text"] = "Stop Server"
    else:
        stop_flask()
        button["text"] = "Start Server"

def on_closing():
    stop_flask()
    window.destroy()

def get_local_network_ip():
    hostname = socket.gethostname()
    ip_addresses = socket.gethostbyname_ex(hostname)[2]
    local_network_ips = [ip for ip in ip_addresses if not ip.startswith("127.")]
    return local_network_ips

def create_gui():
    global window
    window = Tk()
    window.title("League Chat Sender")
    window.geometry("300x200")

    url_label = Label(window, text="URL: http://localhost:5000")
    url_label.pack(pady=10)

    local_network_ips = get_local_network_ip()
    if local_network_ips:
        ip_urls = "\n".join([f"Running on http://{ip}:5000" for ip in local_network_ips])
    else:
        ip_urls = "No local network IP found."
    ip_label = Label(window, text=ip_urls, justify="left")
    ip_label.pack(pady=10)

    toggle_button = Button(window, text="Start Server", command=lambda: toggle_server(toggle_button))
    toggle_button.pack(pady=5)

    open_button = Button(window, text="Open in Browser", command=open_browser)
    open_button.pack(pady=5)

    window.after(1000, lambda: toggle_server(toggle_button))  # Start the server automatically after 1 second

    window.protocol("WM_DELETE_WINDOW", on_closing)  # Handle window close event

    window.mainloop()

if __name__ == "__main__":
    atexit.register(stop_flask)  # Ensure the server stops when the program exits
    create_gui()