import os
import tkinter as tk
from tkinter import ttk, messagebox
import pygetwindow as gw
import pywinauto
import keyboard
import time
from functools import partial

# Directory to store message files
MESSAGE_DIR = 'message_profiles'

def get_message_files():
    if not os.path.exists(MESSAGE_DIR):
        os.makedirs(MESSAGE_DIR)
    return [f for f in os.listdir(MESSAGE_DIR) if os.path.isfile(os.path.join(MESSAGE_DIR, f)) and not f.endswith('.hotkey')]

def read_messages(file_name):
    file_path = os.path.join(MESSAGE_DIR, file_name)
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r', encoding='utf-8') as file:
        messages = file.readlines()
    return [msg.strip() for msg in messages]

def write_messages(file_name, messages):
    file_path = os.path.join(MESSAGE_DIR, file_name)
    with open(file_path, 'w', encoding='utf-8') as file:
        for msg in messages:
            file.write(msg + '\n')

def read_hotkey(file_name):
    hotkey_file = os.path.join(MESSAGE_DIR, f"{file_name}.hotkey")
    if os.path.exists(hotkey_file):
        with open(hotkey_file, 'r') as file:
            return file.read().strip()
    return ""

def write_hotkey(file_name, hotkey):
    hotkey_file = os.path.join(MESSAGE_DIR, f"{file_name}.hotkey")
    with open(hotkey_file, 'w') as file:
        file.write(hotkey)

def add_message(file_name, message):
    messages = read_messages(file_name)
    messages.append(message)
    write_messages(file_name, messages)
    setup_hotkeys()

def delete_message(file_name, index):
    messages = read_messages(file_name)
    if 0 <= index < len(messages):
        messages.pop(index)
        write_messages(file_name, messages)
        setup_hotkeys()
    else:
        print("Invalid index")

def delete_profile(profile_name):
    file_path = os.path.join(MESSAGE_DIR, profile_name)
    hotkey_file = os.path.join(MESSAGE_DIR, f"{profile_name}.hotkey")
    if os.path.exists(file_path):
        os.remove(file_path)
    if os.path.exists(hotkey_file):
        os.remove(hotkey_file)
    setup_hotkeys()

def send_message(message):
    windows = gw.getWindowsWithTitle('League of Legends')
    if windows:
        league_window = windows[0]
        league_window.activate()
        time.sleep(0.1)
        app = pywinauto.Application().connect(handle=league_window._hWnd)
        window = app.window(handle=league_window._hWnd)
        window.set_focus()
        window.type_keys('{ENTER}', with_spaces=True, pause=0.01)
        if include_all_var.get():
            window.type_keys('/all ', with_spaces=True, pause=0.01)
        window.type_keys(message, with_spaces=True, pause=0.01)
        window.type_keys('{ENTER}', with_spaces=True, pause=0.01)
    else:
        print("League of Legends window not found.")

def setup_hotkeys():
    profiles = get_message_files()
    hotkeys = set()
    for profile in profiles:
        hotkey = read_hotkey(profile)
        if hotkey:
            if hotkey in hotkeys:
                messagebox.showerror("Error", f"Duplicate hotkey detected: {hotkey} for profile {profile}. Please assign a unique hotkey.")
                return
            hotkeys.add(hotkey)
            messages = read_messages(profile)
            if messages: # Ensure there are messages to send
                for msg in messages:
                    if use_left_ctrl.get():
                        keyboard.add_hotkey(f'ctrl+{hotkey}', partial(send_message, msg))
                    else:
                        keyboard.add_hotkey(hotkey, partial(send_message, msg))

def on_profile_select(event):
    current_profile = profile_var.get()
    if current_profile:
        message_list.delete(0, tk.END)
        messages = read_messages(current_profile)
        for msg in messages:
            message_list.insert(tk.END, msg)
        hotkey_entry.delete(0, tk.END)
        hotkey_entry.insert(0, read_hotkey(current_profile))

def on_add_message():
    new_message = new_message_entry.get()
    if new_message and profile_var.get():
        add_message(profile_var.get(), new_message)
        new_message_entry.delete(0, tk.END)
        on_profile_select(None) # Automatically update the textbox

def on_delete_message():
    selected_index = message_list.curselection()
    if selected_index and profile_var.get():
        if messagebox.askokcancel("Confirm", "Are you sure you want to delete this message?"):
            delete_message(profile_var.get(), selected_index[0])
            on_profile_select(None)

def on_set_hotkey():
    new_hotkey = hotkey_entry.get()
    if new_hotkey and profile_var.get():
        write_hotkey(profile_var.get(), new_hotkey)
        setup_hotkeys()

def on_create_profile():
    new_profile = new_profile_entry.get()
    if new_profile:
        new_profile_path = os.path.join(MESSAGE_DIR, new_profile)
        if not os.path.exists(new_profile_path):
            open(new_profile_path, 'w').close() # Create an empty file
        profile_var.set(new_profile)
        profile_combo['values'] = get_message_files()
        new_profile_entry.delete(0, tk.END)
        on_profile_select(None) # Automatically update the textbox

def on_delete_profile():
    if profile_var.get():
        if messagebox.askokcancel("Confirm", "Are you sure you want to delete this profile?"):
            delete_profile(profile_var.get())
            profile_var.set("")
            profile_combo['values'] = get_message_files()
            message_list.delete(0, tk.END)
            hotkey_entry.delete(0, tk.END)

def on_message_list_double_click(event):
    selected_message = message_list.get(message_list.curselection())
    send_message(selected_message)

def on_use_left_ctrl_change():
    setup_hotkeys()

root = tk.Tk()
root.title("Message Manager")

profile_var = tk.StringVar()
include_all_var = tk.BooleanVar(value=True)

profile_frame = ttk.Frame(root, padding=10)
profile_frame.grid(row=0, column=0, sticky="ew")

ttk.Label(profile_frame, text="Select Profile:").grid(row=0, column=0)

profile_combo = ttk.Combobox(profile_frame, textvariable=profile_var, values=get_message_files(), state="readonly")
profile_combo.grid(row=0, column=1)
profile_combo.bind("<<ComboboxSelected>>", on_profile_select)

ttk.Checkbutton(profile_frame, text="All Chat", variable=include_all_var).grid(row=0, column=2, padx=(180, 0))

message_frame = ttk.Frame(root, padding=10)
message_frame.grid(row=1, column=0, sticky="nsew")

message_list = tk.Listbox(message_frame, height=10)
message_list.grid(row=0, column=0, sticky="nsew")
message_list.bind("<Double-1>", on_message_list_double_click)

message_scrollbar = ttk.Scrollbar(message_frame, orient="vertical", command=message_list.yview)
message_scrollbar.grid(row=0, column=1, sticky="ns")
message_list.configure(yscrollcommand=message_scrollbar.set)

new_message_frame = ttk.Frame(root, padding=10)
new_message_frame.grid(row=2, column=0, sticky="ew")

new_message_entry = ttk.Entry(new_message_frame, width=50)
new_message_entry.grid(row=0, column=0)
ttk.Button(new_message_frame, text="Add Message", command=on_add_message).grid(row=0, column=1)
ttk.Button(new_message_frame, text="Delete Message", command=on_delete_message).grid(row=0, column=2)

hotkey_frame = ttk.Frame(root, padding=10)
hotkey_frame.grid(row=3, column=0, sticky="ew")

ttk.Label(hotkey_frame, text="Set Hotkey:").grid(row=0, column=0)
hotkey_entry = ttk.Entry(hotkey_frame, width=10)
hotkey_entry.grid(row=0, column=1)
ttk.Button(hotkey_frame, text="Set Hotkey", command=on_set_hotkey).grid(row=0, column=2)

use_left_ctrl = tk.BooleanVar(value=False)
ttk.Checkbutton(hotkey_frame, text="Use Left Control Key as Combo Key", variable=use_left_ctrl, command=on_use_left_ctrl_change).grid(row=0, column=3, padx=(20, 0))

new_profile_frame = ttk.Frame(root, padding=10)
new_profile_frame.grid(row=4, column=0, sticky="ew")

ttk.Label(new_profile_frame, text="Profile Name:").grid(row=0, column=0)
new_profile_entry = ttk.Entry(new_profile_frame, width=20)
new_profile_entry.grid(row=0, column=1)
ttk.Button(new_profile_frame, text="Create Profile", command=on_create_profile).grid(row=0, column=2)
ttk.Button(new_profile_frame, text="Delete Profile", command=on_delete_profile).grid(row=0, column=3)

root.columnconfigure(0, weight=1)
root.rowconfigure(1, weight=1)
message_frame.columnconfigure(0, weight=1)
message_frame.rowconfigure(0, weight=1)

# Set the first profile as the default selection
profiles = get_message_files()
if profiles:
    profile_var.set(profiles[0])
    on_profile_select(None)

setup_hotkeys()
root.mainloop()