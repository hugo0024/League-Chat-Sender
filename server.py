import os
import subprocess
import threading
import webbrowser
from tkinter import Tk, Label, Button
from flask import Flask, request, render_template_string, jsonify

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
            }
          });
        });
      });
    </script>
  </body>
</html>
"""

def send_message(message, all_chat):
    ahk_script = f"""
    #Persistent
    SetTitleMatchMode, 2
    IfWinExist, League of Legends
    {{
        WinActivate
        Send, {{Enter}}
        Send, {'/all ' if all_chat else ''}{message}
        Send, {{Enter}}
    }}
    ExitApp
    """
    ahk_temp_file = 'temp_send_message.exe'
    with open(ahk_temp_file, 'wb') as file:
        # Write the BOM for UTF-8
        file.write(b'\xef\xbb\xbf')
        # Write the rest of the script in UTF-8
        file.write(ahk_script.encode('utf-8'))
    subprocess.Popen(['C:\\Program Files\\AutoHotkey\\v1.1.37.01\\AutoHotkeyU64.exe', ahk_temp_file])

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
    flask_thread = threading.Thread(target=start_server)
    flask_thread.start()

def stop_flask():
    os._exit(0)

def create_gui():
    window = Tk()
    window.title("League Chat Sender")
    window.geometry("300x150")

    url_label = Label(window, text="URL: http://localhost:5000")
    url_label.pack(pady=10)

    start_button = Button(window, text="Start Server", command=start_flask)
    start_button.pack(pady=5)

    open_button = Button(window, text="Open in Browser", command=open_browser)
    open_button.pack(pady=5)

    stop_button = Button(window, text="Stop Server", command=stop_flask)
    stop_button.pack(pady=5)

    window.mainloop()

if __name__ == "__main__":
    create_gui()