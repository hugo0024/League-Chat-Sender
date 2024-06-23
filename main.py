import os
import subprocess
import PySimpleGUI as sg

# Directory to store message files
MESSAGE_DIR = 'message_profiles'
AHK_SCRIPT_FILE = 'send_messages.exe'
AHK_PROCESS = None

# Set the location for the settings file
sg.user_settings_filename(filename='settings.json')

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
    hotkey = sg.user_settings_get_entry(f'{file_name}_hotkey') # Removed default hotkey
    return hotkey

def write_hotkey(file_name, hotkey):
    sg.user_settings_set_entry(f'{file_name}_hotkey', hotkey)

def add_message(file_name, message):
    messages = read_messages(file_name)
    messages.append(message)
    write_messages(file_name, messages)
    generate_ahk_script()
    restart_ahk_script()

def delete_message(file_name, index):
    messages = read_messages(file_name)
    if 0 <= index < len(messages):
        messages.pop(index)
        write_messages(file_name, messages)
        generate_ahk_script()
        restart_ahk_script()
    else:
        print("Invalid index")

def delete_profile(profile_name):
    file_path = os.path.join(MESSAGE_DIR, profile_name)
    if os.path.exists(file_path):
        os.remove(file_path)
        sg.user_settings_delete_entry(f'{profile_name}_hotkey')
        generate_ahk_script()
        restart_ahk_script()

def generate_ahk_script():
    profiles = get_message_files()
    hotkeys = set()
    with open(AHK_SCRIPT_FILE, 'wb') as file:
        # Write the BOM for UTF-8
        file.write(b'\xef\xbb\xbf')
        # Write the rest of the script in UTF-8
        script_content = (
            '; AutoHotkey Script to send multiple predetermined messages in all chat in League of Legends\n'
        )
        for profile in profiles:
            hotkey = read_hotkey(profile)
            print(f"Profile: {profile}, Hotkey: {hotkey}") # Debugging information
            if hotkey in hotkeys:
                sg.popup_error(f"Duplicate hotkey detected: {hotkey} for profile {profile}. Please assign a unique hotkey.")
                return
            hotkeys.add(hotkey)
            messages = read_messages(profile)
            script_content += (
                f'; Define the hotkey (Control & {hotkey} for {profile})\n'
                f'Control & {hotkey}::\n' # Control & represents Ctrl, + represents Shift
                ' ; Activate the League of Legends window\n'
                ' IfWinExist, League of Legends\n'
                ' {\n'
                ' ; Make the League of Legends window active\n'
                ' WinActivate\n'
            )
            for msg in messages:
                if sg.user_settings_get_entry('include_all_prefix', True):
                    script_content += (
                        ' Send, {Enter}\n'
                        f' Send, /all {msg}\n'
                        ' Send, {Enter}\n'
                    )
                else:
                    script_content += (
                        ' Send, {Enter}\n'
                        f' Send, {msg}\n'
                        ' Send, {Enter}\n'
                    )
            script_content += ' }\n return\n'
        file.write(script_content.encode('utf-8'))

def start_ahk_script():
    global AHK_PROCESS
    AHK_PROCESS = subprocess.Popen(['C:\\Program Files\\AutoHotkey\\v1.1.37.01\\AutoHotkeyU64.exe', AHK_SCRIPT_FILE])

def stop_ahk_script():
    global AHK_PROCESS
    if AHK_PROCESS:
        AHK_PROCESS.terminate()
        AHK_PROCESS = None

def restart_ahk_script():
    stop_ahk_script()
    start_ahk_script()

def send_message(message):
    include_all_prefix = sg.user_settings_get_entry('include_all_prefix', True)
    ahk_script = f"""
    #Persistent
    SetTitleMatchMode, 2
    IfWinExist, League of Legends
    {{
    WinActivate
    Send, {{Enter}}
    Send, {'/all ' if include_all_prefix else ''}{message}
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

def main():
    global current_profile
    current_profile = None
    layout = [
        [sg.Text('Message Manager')],
        [sg.Text('Select Profile:'), sg.Combo(get_message_files(), key='-PROFILE-', enable_events=True), sg.Checkbox('Include /all prefix', default=True, key='-INCLUDE_ALL-', enable_events=True)],
        [sg.Listbox(values=[], size=(80, 10), key='-MESSAGE_LIST-', bind_return_key=True)],
        [sg.InputText(key='-NEW_MESSAGE-' , size=(50, 10)), sg.Button('Add Message'), sg.Button('Delete Message')],
        [sg.Text('Set Hotkey:'), sg.InputText(key='-HOTKEY-', size=(10, 1)), sg.Button('Set Hotkey')],
        [sg.Text('New Profile Name:'), sg.InputText(key='-NEW_PROFILE-', size=(10, 10)), sg.Button('Create Profile'), sg.Button('Delete Profile')],
        [],  # Added button for deleting profile
        [sg.Button('Start AHK Script'), sg.Button('Stop AHK Script')],
        [sg.Button('Exit')]
    ]

    window = sg.Window('Message Manager', layout)

    # Generate and start the AHK script on startup
    generate_ahk_script()
    start_ahk_script()

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED or event == 'Exit':
            stop_ahk_script()
            break
        elif event == '-PROFILE-':
            current_profile = values['-PROFILE-']
            if current_profile:
                window['-MESSAGE_LIST-'].update(read_messages(current_profile))
                window['-HOTKEY-'].update(read_hotkey(current_profile))
        elif event == 'Add Message':
            new_message = values['-NEW_MESSAGE-']
            if new_message and current_profile:
                add_message(current_profile, new_message)
                window['-MESSAGE_LIST-'].update(read_messages(current_profile))
        elif event == 'Delete Message':
            selected_message = values['-MESSAGE_LIST-']
            if selected_message and current_profile:
                index = read_messages(current_profile).index(selected_message[0])
                if sg.popup_ok_cancel('Are you sure you want to delete this message?') == 'OK':
                    delete_message(current_profile, index)
                    window['-MESSAGE_LIST-'].update(read_messages(current_profile))
        elif event == 'Set Hotkey':
            new_hotkey = values['-HOTKEY-']
            if new_hotkey and current_profile:
                write_hotkey(current_profile, new_hotkey)
                generate_ahk_script()
                restart_ahk_script()
        elif event == 'Create Profile':
            new_profile = values['-NEW_PROFILE-']
            if new_profile:
                new_profile_path = os.path.join(MESSAGE_DIR, new_profile)
                if not os.path.exists(new_profile_path):
                    open(new_profile_path, 'w').close() # Create an empty file
                window['-PROFILE-'].update(values=get_message_files())
                window['-NEW_PROFILE-'].update('')
        elif event == 'Delete Profile':  # Handle delete profile event
            if current_profile:
                if sg.popup_ok_cancel('Are you sure you want to delete this profile?') == 'OK':
                    delete_profile(current_profile)
                    window['-PROFILE-'].update(values=get_message_files())
                    window['-MESSAGE_LIST-'].update([])
                    window['-HOTKEY-'].update('')
                    current_profile = None
        elif event == 'Start AHK Script':
            start_ahk_script()
        elif event == 'Stop AHK Script':
            stop_ahk_script()
        elif event == '-MESSAGE_LIST-':
            if values['-MESSAGE_LIST-']:
                selected_message = values['-MESSAGE_LIST-'][0]
                send_message(selected_message)
        elif event == '-INCLUDE_ALL-':
            sg.user_settings_set_entry('include_all_prefix', values['-INCLUDE_ALL-'])
            generate_ahk_script()
            restart_ahk_script()

    window.close()

if __name__ == "__main__":
    main()