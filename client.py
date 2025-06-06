#set "TCL_LIBRARY=C:\Users\sereg\AppData\Local\Programs\Python\Python313\tcl\tcl8.6"
#set "TK_LIBRARY=C:\Users\sereg\AppData\Local\Programs\Python\Python313\tcl\tk8.6"

import customtkinter as ctk
import socket
import threading
import time
from PIL import Image
import json
from CTkMessagebox import CTkMessagebox



class MessengerApp:
    def __init__(self, master, client_socket, nickname):
        self.master = master
        self.client_socket = client_socket
        self.nickname = nickname
        self.connected = True
        self.unsent_messages = []
        
        self.themes = {
            'dark': {
                'bg': '#1A1A1A',
                'fg': '#FFFFFF',
                'button': '#2D2D2D',
                'button_hover': '#3D3D3D',
                'frame': '#1A1A1A',
                'accent': '#00ff88',
                'text_box': '#2D2D2D'
            },
            'dark_blue': {
                'bg': '#1A1A2D',
                'fg': '#FFFFFF',
                'button': '#2D2D40',
                'button_hover': '#3D3D50',
                'frame': '#1A1A2D',
                'accent': '#00bfff',
                'text_box': '#2D2D40'
            },
            'dark_red': {
                'bg': '#2D1A1A',
                'fg': '#FFFFFF',
                'button': '#402D2D',
                'button_hover': '#503D3D',
                'frame': '#2D1A1A',
                'accent': '#ff4444',
                'text_box': '#402D2D'
            },
            'dark_purple': {
                'bg': '#2D1A2D',
                'fg': '#FFFFFF',
                'button': '#402D40',
                'button_hover': '#503D50',
                'frame': '#2D1A2D',
                'accent': '#bf5fff',
                'text_box': '#402D40'
            },
            'dark_green': {
                'bg': '#1A2D1A',
                'fg': '#FFFFFF',
                'button': '#2D402D',
                'button_hover': '#3D503D',
                'frame': '#1A2D1A',
                'accent': '#44ff44',
                'text_box': '#2D402D'
            },
            'dark_gold': {
                'bg': '#2D2D1A',
                'fg': '#FFFFFF',
                'button': '#40402D',
                'button_hover': '#50503D',
                'frame': '#2D2D1A',
                'accent': '#ffd700',
                'text_box': '#40402D'
            },
            'dark_cyan': {
                'bg': '#1A2D2D',
                'fg': '#FFFFFF',
                'button': '#2D4040',
                'button_hover': '#3D5050',
                'frame': '#1A2D2D',
                'accent': '#00ffff',
                'text_box': '#2D4040'
            },
            'dark_pink': {
                'bg': '#2D1A24',
                'fg': '#FFFFFF',
                'button': '#402D37',
                'button_hover': '#503D47',
                'frame': '#2D1A24',
                'accent': '#ff69b4',
                'text_box': '#402D37'
            },
            'midnight_blue': {
                'bg': '#151B2D',
                'fg': '#FFFFFF',
                'button': '#1D2540',
                'button_hover': '#2D3550',
                'frame': '#151B2D',
                'accent': '#4169E1',
                'text_box': '#1D2540'
            },
            'deep_purple': {
                'bg': '#2D1B40',
                'fg': '#FFFFFF',
                'button': '#402D53',
                'button_hover': '#503D63',
                'frame': '#2D1B40',
                'accent': '#9370DB',
                'text_box': '#402D53'
            }
        }
        
        self.settings = {
            'show_seconds': True,      
            'message_sound': True,     
            'auto_scroll': True,       
            'font_size': 14,          
            'text_scale': 1.0,        
            'show_join_leave': True,
            'current_theme': 'dark'    
        }
        
        self.load_settings()
        
        self.current_theme = self.settings.get('current_theme', 'dark')
        
        master.title(f"SproutLine - {nickname}")
        master.geometry('700x350')
        master.resizable(False, False)

        try:
            self.image_send = Image.open("img/send.png")
            self.image_send = self.image_send.resize((50, 50), Image.LANCZOS)

            self.photo_send = ctk.CTkImage(light_image=self.image_send, dark_image=self.image_send)

            self.image_file = Image.open("img/file.png")
            self.image_file = self.image_file.resize((50, 50), Image.LANCZOS)

            self.photo_file = ctk.CTkImage(light_image=self.image_file, dark_image=self.image_file)
        except Exception as e:
            print(f"Ошибка при загрузке изображения: {e}")
            self.photo_send = None
            self.photo_file = None
        
        self.message_display = ctk.CTkTextbox(master, width=500, height=300, corner_radius=10, state='disabled')
        self.message_display.place(relx=0.01, rely=0.01)
        self.message_display.configure(font=("Arial", 14))
        
        self.profile_frame = ctk.CTkFrame(master, width=175, height=150, corner_radius=10, fg_color='#1B1B1B')
        self.profile_frame.place(relx=0.74, rely=0.01)
        
        self.profile_label = ctk.CTkLabel(
            self.profile_frame, 
            text='• Профиль', 
            text_color='#00ff88',
            font=('Arial Bold', 14)
        )
        self.profile_label.place(relx=0.05, rely=0.001)
        
        self.nickname_label = ctk.CTkLabel(
            self.profile_frame,
            text=f'     ★ Ник: {self.nickname}',
            font=('Arial', 13),
            text_color='#00bfff'
        )
        self.nickname_label.place(relx=0.05, rely=0.15)

        self.connection_status = ctk.CTkLabel(
            self.profile_frame,
            text='     ● Статус: Онлайн',
            font=('Arial', 13),
            text_color='#00ff88'
        )
        self.connection_status.place(relx=0.05, rely=0.3)

        self.version_label = ctk.CTkLabel(
            self.profile_frame,
            text='     ◆ Версия: 1.0',
            font=('Arial', 13),
            text_color='#888888'
        )
        self.version_label.place(relx=0.05, rely=0.45)

        self.users_frame = ctk.CTkFrame(master, width=175, height=180, corner_radius=10, fg_color='#1B1B1B')
        self.users_frame.place(relx=0.74, rely=0.45)
        
        self.users_label = ctk.CTkLabel(
            self.users_frame,
            text='• Участники',
            text_color='#00ff88',
            font=('Arial Bold', 13)
        )
        self.users_label.place(relx=0.05, rely=0.001)
        
        self.users_list = ctk.CTkTextbox(
            self.users_frame,
            width=155,
            height=100,
            fg_color='#1B1B1B',
            text_color='#ffffff',
            font=('Arial', 12)
        )
        self.users_list.place(relx=0.1, rely=0.2)
        self.users_list.configure(state='disabled')

        self.message_entry = ctk.CTkEntry(master, width=455)
        self.message_entry.place(relx=0.01, rely=0.885)
        self.message_entry.bind("<Return>", lambda event: self.send_message())

        self.send_button = ctk.CTkButton(master, image=self.photo_send, width=30, height=25, text="", fg_color='#1a1a1a', hover_color='#303030', command=self.send_message)
        self.send_button.place(relx=0.67, rely=0.885)

        self.receive_thread = threading.Thread(target=self.receive_messages)
        self.receive_thread.daemon = True
        self.receive_thread.start()

        self.keep_alive_thread = threading.Thread(target=self.keep_alive)
        self.keep_alive_thread.daemon = True
        self.keep_alive_thread.start()

        self.last_message_time = 0
        self.message_cooldown = 3
        self.max_message_length = 300
        
        self.notification_label = ctk.CTkLabel(
            master,
            text="",
            text_color="#ff3333",
            font=('Arial', 12)
        )
        self.notification_label.place(relx=0.01, rely=0.8)

        self.settings_button = ctk.CTkButton(
            self.profile_frame,
            text="⚙️ Настройки",
            width=120,
            height=25,
            font=('Arial', 12),
            fg_color='#1a1a1a',
            hover_color='#2a2a2a',
            command=self.open_settings
        )
        self.settings_button.place(relx=0.15, rely=0.7)
        
        self.apply_saved_settings()

    def send_message(self):
        message = self.message_entry.get()
        current_time = time.time()
        
        if len(message) > self.max_message_length:
            self.show_notification(f"Сообщение слишком длинное! Максимум {self.max_message_length} символов")
            return
        
        time_since_last = current_time - self.last_message_time
        if time_since_last < self.message_cooldown:
            remaining = int(self.message_cooldown - time_since_last)
            self.show_notification(f"Подождите {remaining} сек. перед отправкой")
            return

        if message:
            self.message_entry.delete(0, "end")
            if self.connected:
                self.last_message_time = current_time
                threading.Thread(target=self._send_message_thread, args=(message,)).start()
                self.clear_notification()
            else:
                self.unsent_messages.append(message)
                threading.Thread(target=self.reconnect).start()

    def _send_message_thread(self, message):
        try:
            self.client_socket.send(f"{self.nickname}: {message}".encode('utf-8'))
            self.display_message(f"[{time.strftime('%H:%M:%S')}] [{self.nickname}] {message}")
        except Exception:
            self.unsent_messages.append(message)
            threading.Thread(target=self.reconnect).start()

    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if message.startswith("USERS:"):
                    users = [user.strip() for user in message[6:].split(",") if user.strip()]
                    self.update_users_list(users)
                    continue
                elif not message.startswith("users:"):
                    self.display_message(message)
            except Exception:
                self.connected = False
                break

    def keep_alive(self):
        while True:
            time.sleep(30)
            if self.connected:
                try:
                    self.client_socket.send(b'')
                except Exception:
                    self.connected = False
                    threading.Thread(target=self.reconnect).start()

    def display_message(self, message, is_new=True):
        self.message_display.configure(state='normal')
        
        if is_new and not self.settings['show_join_leave'] and ("присоединился к чату" in message or "покинул чат" in message):
            self.message_display.configure(state='disabled')
            return
        
        if self.message_display.get("1.0", "end-1c"):
            self.message_display.insert("end", "\n")
        
        if message.startswith('[') and '] ' in message:
            timestamp_end = message.find('] ') + 2
            timestamp = message[:timestamp_end]
            text = message[timestamp_end:]
            
            if not self.settings['show_seconds'] and timestamp.count(':') == 2:
                time_parts = timestamp[1:-2].split(':')
                timestamp = f"[{time_parts[0]}:{time_parts[1]}] "
            
            formatted_message = timestamp + text.strip()
        else:
            formatted_message = message.strip()
        
        self.message_display.insert("end", formatted_message)
        
        if self.settings['auto_scroll']:
            self.message_display.see("end")
            
        self.message_display.configure(state='disabled')
        
        if is_new and self.settings['message_sound']:
            pass

    def load_chat_history(self, chat_history):
        messages = chat_history.strip().split('\n')
        for msg in messages:
            if msg.strip():
                self.display_message(msg.strip())

    def reconnect(self):
        self.update_connection_status(False)
        self.connected = False

        while not self.connected:
            try:
                self.client_socket.close()
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.setsockopt(socket.SOL_TCP, socket.SO_KEEPALIVE, 1)
                self.client_socket.connect((self.ip, self.port))
                self.connected = True

                self.receive_thread = threading.Thread(target=self.receive_messages)
                self.receive_thread.daemon = True
                self.receive_thread.start()

                while self.unsent_messages:
                    unsent_message = self.unsent_messages.pop(0)
                    self._send_message_thread(unsent_message)

                self.update_connection_status(True)

            except Exception:
                time.sleep(5)

    def update_connection_status(self, status):
        if status:
            self.connection_status.configure(text='● Статус: Онлайн', text_color='#00ff88')
        else:
            self.connection_status.configure(text='○ Статус: Оффлайн', text_color='#ff3333')

    def update_users_list(self, users):
        self.users_list.configure(state='normal')
        self.users_list.delete('1.0', 'end')
        for user in users:
            if user.strip():
                self.users_list.insert('end', f"• {user.strip()}\n")
        self.users_list.configure(state='disabled')

    def show_notification(self, text):
        self.notification_label.configure(text=text)
        self.master.after(3000, self.clear_notification)

    def clear_notification(self):
        self.notification_label.configure(text="")

    def center_toplevel(self, window, width, height):
        main_x = self.master.winfo_x()
        main_y = self.master.winfo_y()
        main_width = self.master.winfo_width()
        main_height = self.master.winfo_height()
        
        x = main_x + (main_width - width) // 2
        y = main_y + (main_height - height) // 2
        
        window.geometry(f'{width}x{height}+{x}+{y}')

    def open_settings(self):
        settings_window = ctk.CTkToplevel(self.master)
        settings_window.title("Настройки")
        settings_window.resizable(False, False)
        
        settings_window.attributes('-topmost', True)
        settings_window.focus_force()
        
        self.center_toplevel(settings_window, 500, 300)
        
        theme = self.themes[self.current_theme]
        settings_window.configure(fg_color=theme['bg'])
        
        button_color = self.darken_color(theme['button'], 0.8)
        button_hover = self.darken_color(theme['button_hover'], 0.8)
        
        settings_frame = ctk.CTkFrame(settings_window, fg_color=theme['text_box'])
        settings_frame.pack(padx=15, pady=15, fill="both", expand=True)
        
        display_frame = ctk.CTkFrame(settings_frame, fg_color=theme['text_box'])
        display_frame.pack(side="left", padx=10, pady=10, fill="both", expand=True)
        
        display_label = ctk.CTkLabel(display_frame, text="• Отображение", font=('Arial Bold', 13), text_color=theme['accent'])
        display_label.pack(pady=(0,10))
        
        self.seconds_var = ctk.BooleanVar(value=self.settings['show_seconds'])
        seconds_switch = ctk.CTkSwitch(
            display_frame,
            text="Отображать секунды",
            variable=self.seconds_var,
            command=lambda: self.update_setting('show_seconds', self.seconds_var.get())
        )
        seconds_switch.pack(pady=5, padx=10, anchor="w")
        
        self.auto_scroll_var = ctk.BooleanVar(value=self.settings['auto_scroll'])
        auto_scroll_switch = ctk.CTkSwitch(
            display_frame,
            text="Автопрокрутка",
            variable=self.auto_scroll_var,
            command=lambda: self.update_setting('auto_scroll', self.auto_scroll_var.get())
        )
        auto_scroll_switch.pack(pady=5, padx=10, anchor="w")
        
        self.join_leave_var = ctk.BooleanVar(value=self.settings['show_join_leave'])
        join_leave_switch = ctk.CTkSwitch(
            display_frame,
            text="Сообщения входа/выхода",
            variable=self.join_leave_var,
            command=lambda: self.update_setting('show_join_leave', self.join_leave_var.get())
        )
        join_leave_switch.pack(pady=5, padx=10, anchor="w")
        
        personalization_frame = ctk.CTkFrame(settings_frame, fg_color=theme['text_box'])
        personalization_frame.pack(side="right", padx=10, pady=10, fill="both", expand=True)
        
        personalization_label = ctk.CTkLabel(personalization_frame, text="• Персонализация", font=('Arial Bold', 13), text_color=theme['accent'])
        personalization_label.pack(pady=(0,10))
        
        scale_label = ctk.CTkLabel(personalization_frame, text="Масштаб текста чата:", font=('Arial', 12))
        scale_label.pack(pady=(5,0))
        
        text_scale = ctk.CTkSlider(
            personalization_frame,
            from_=0.8,
            to=1.4,
            number_of_steps=6,
            command=lambda value: self.update_setting('text_scale', value)
        )
        text_scale.set(self.settings.get('text_scale', 1.0))
        text_scale.pack(pady=(0,10), padx=10)
        
        theme_button = ctk.CTkButton(
            personalization_frame,
            text="🎨 Сменить тему",
            width=180,
            height=30,
            font=('Arial', 12),
            fg_color=button_color,
            hover_color=button_hover,
            command=lambda: self.open_theme_window(settings_window)
        )
        theme_button.pack(pady=5)
        
        reset_button = ctk.CTkButton(
            personalization_frame,
            text="↺ Сбросить настройки",
            width=180,
            height=30,
            font=('Arial', 12),
            fg_color=button_color,
            hover_color=button_hover,
            command=self.reset_settings
        )
        reset_button.pack(pady=5)
        
        version_label = ctk.CTkLabel(
            settings_frame,
            text="SproutLine 1.0",
            font=('Arial', 11),
            text_color='#888888'
        )
        version_label.pack(side="bottom", pady=5)

    def update_setting(self, setting_name, value):
        self.settings[setting_name] = value
        
        if setting_name == 'text_scale':
            new_font_size = int(14 * value)
            self.message_display.configure(font=("Arial", new_font_size))
            
        self.save_settings()

    def reset_settings(self):
        default_settings = {
            'show_seconds': True,
            'auto_scroll': True,
            'text_scale': 1.0,
            'show_join_leave': True,
            'current_theme': 'dark'
        }
        
        self.settings.update(default_settings)
        
        self.apply_theme('dark')
        self.seconds_var.set(True)
        self.auto_scroll_var.set(True)
        self.join_leave_var.set(True)
        
        self.save_settings()

    def load_settings(self):
        try:
            with open('settings.json', 'r', encoding='utf-8') as f:
                saved_settings = json.load(f)
                self.settings.update(saved_settings)
        except FileNotFoundError:
            self.save_settings()
        except json.JSONDecodeError:
            print("Файл настроек поврежден. Используются настройки по умолчанию.")
            self.save_settings()
            
    def save_settings(self):
        try:
            with open('settings.json', 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка при сохранении настроек: {e}")

    def apply_saved_settings(self):
        if 'current_theme' in self.settings:
            self.apply_theme(self.settings['current_theme'])
        
        if 'text_scale' in self.settings:
            new_font_size = int(14 * self.settings['text_scale'])
            self.message_display.configure(font=("Arial", new_font_size))

    def open_theme_window(self, parent_window):
        theme_window = ctk.CTkToplevel(parent_window)
        theme_window.title("Выбор темы")
        theme_window.resizable(False, False)
        
        theme_window.transient(parent_window)
        theme_window.attributes('-topmost', True)
        theme_window.focus_force()
        
        parent_window.attributes('-topmost', False)
        
        def on_theme_window_close():
            parent_window.attributes('-topmost', True)
            theme_window.destroy()
        
        theme_window.protocol("WM_DELETE_WINDOW", on_theme_window_close)
        
        self.center_toplevel(theme_window, 250, 400)
        
        current_theme = self.themes[self.current_theme]
        theme_window.configure(fg_color=current_theme['bg'])
        
        themes = [
            ("Классическая", "dark"),
            ("Тёмно-синяя", "dark_blue"),
            ("Тёмно-красная", "dark_red"),
            ("Тёмно-фиолетовая", "dark_purple"),
            ("Тёмно-зелёная", "dark_green"),
            ("Тёмно-золотая", "dark_gold"),
            ("Тёмно-голубая", "dark_cyan"),
            ("Тёмно-розовая", "dark_pink"),
            ("Полночь", "midnight_blue"),
            ("Глубокий пурпур", "deep_purple")
        ]
        
        buttons_frame = ctk.CTkFrame(theme_window, fg_color=current_theme['text_box'])
        buttons_frame.pack(padx=15, pady=15, fill="both", expand=True)
        
        for theme_name, theme_id in themes:
            theme_colors = self.themes[theme_id]
            btn = ctk.CTkButton(
                buttons_frame,
                text=theme_name,
                command=lambda t=theme_id: self.apply_theme(t),
                fg_color=theme_colors['button'],
                hover_color=theme_colors['button_hover'],
                width=200,
                height=35
            )
            btn.pack(pady=5, padx=10)

    def apply_theme(self, theme_name):
        theme = self.themes[theme_name]
        self.current_theme = theme_name
        
        self.master.configure(fg_color=theme['bg'])
        
        self.message_display.configure(
            fg_color=theme['text_box'],
            text_color=theme['fg']
        )
        
        self.profile_frame.configure(fg_color=theme['text_box'])
        self.users_frame.configure(fg_color=theme['text_box'])
        
        self.message_entry.configure(
            fg_color=theme['text_box'],
            text_color=theme['fg']
        )
        
        self.send_button.configure(
            fg_color=theme['button'],
            hover_color=theme['button_hover']
        )
        
        settings_button_color = self.darken_color(theme['button'], 0.8)
        settings_button_hover = self.darken_color(theme['button_hover'], 0.8)
        
        self.settings_button.configure(
            fg_color=settings_button_color,
            hover_color=settings_button_hover
        )
        
        self.profile_label.configure(text_color=theme['accent'])
        self.users_label.configure(text_color=theme['accent'])
        self.nickname_label.configure(text_color=theme['accent'])
        self.connection_status.configure(text_color='#00ff88' if self.connected else '#ff3333')
        self.version_label.configure(text_color='#888888')
        
        self.users_list.configure(
            fg_color=theme['text_box'],
            text_color=theme['fg']
        )
        
        def update_widget_colors(widget):
            if isinstance(widget, ctk.CTkFrame):
                widget.configure(fg_color=theme['text_box'])
                for child in widget.winfo_children():
                    update_widget_colors(child)
                
            elif isinstance(widget, ctk.CTkLabel):
                if any(text in str(widget.cget("text")) for text in ["• Отображение", "• Персонализация"]):
                    widget.configure(text_color=theme['accent'])
                elif "SproutLine" in str(widget.cget("text")):
                    widget.configure(text_color='#888888')
                else:
                    widget.configure(text_color=theme['fg'])
                
            elif isinstance(widget, ctk.CTkButton):
                button_color = self.darken_color(theme['button'], 0.8)
                button_hover = self.darken_color(theme['button_hover'], 0.8)
                widget.configure(
                    fg_color=button_color,
                    hover_color=button_hover,
                    text_color=theme['fg']
                )
                
            elif isinstance(widget, ctk.CTkSwitch):
                widget.configure(
                    text_color=theme['fg'],
                    progress_color=theme['accent'],
                    button_color=theme['accent'],
                    button_hover_color=theme['accent']
                )
                
            elif isinstance(widget, ctk.CTkSlider):
                widget.configure(
                    button_color=theme['accent'],
                    button_hover_color=theme['accent'],
                    progress_color=theme['accent']
                )
        
        for window in self.master.winfo_children():
            if isinstance(window, ctk.CTkToplevel):
                window.configure(fg_color=theme['bg'])
                for child in window.winfo_children():
                    update_widget_colors(child)
        
        self.settings['current_theme'] = theme_name
        self.save_settings()

    def darken_color(self, hex_color, factor):
        hex_color = hex_color.lstrip('#')
        
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)
        
        r = min(max(0, r), 255)
        g = min(max(0, g), 255)
        b = min(max(0, b), 255)
        
        return f'#{r:02x}{g:02x}{b:02x}'

def center_window(window, width, height):
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')


def enter_server_info():
    server_info_window = ctk.CTk()
    server_info_window.title("Enter Server Info")
    server_info_window.geometry('400x275')

    center_window(server_info_window, 400, 275)

    ip_label = ctk.CTkLabel(server_info_window, text="Введите айпи:")
    ip_label.pack(pady=10)

    ip_entry = ctk.CTkEntry(server_info_window)
    ip_entry.pack(pady=10)

    port_label = ctk.CTkLabel(server_info_window, text="Введите порт:")
    port_label.pack(pady=10)

    port_entry = ctk.CTkEntry(server_info_window)
    port_entry.pack(pady=10)

    def on_server_info_enter():
        global ip, port_str
        ip = ip_entry.get()
        port_str = port_entry.get()

        checking_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Инициализируем настройки сокета
        checking_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        try: # Проверяем значение порта на валидность
            port = int(port_str)
        except ValueError:
            CTkMessagebox(title="ERROR", message="Invalid port number. Please enter a valid number.", icon="cancel")

        try:
            # Проверяем сервер на доступность, если доступен, то прерываем обращения дальше
            checking_socket.connect((ip, port))
            checking_socket.close()

            server_info_window.destroy()
            nickname_enter()
        except:
            CTkMessagebox(title="ERROR", message="Сервер не доступен!", icon="cancel")

       

    enter_button = ctk.CTkButton(server_info_window, text="Enter", command=on_server_info_enter)
    enter_button.pack(pady=10)

    server_info_window.mainloop()

def nickname_enter():
    global isAuth # Выбор опции авторизация/аутентефикация (1/0)
    isAuth = 1

    nickname_window = ctk.CTk()
    nickname_window.title("AuthWindow")
    nickname_window.geometry('400x275')
    nickname_window.grid_columnconfigure((0, 1), weight=1)

    center_window(nickname_window, 400, 275)

    def chosen_auth(): # Нажата кнопка авторизации
        auth_button.configure(state="disabled")
        login_button.configure(state="normal")
        global isAuth
        isAuth = 1
    
    def chosen_login(): # Нажата кнопка аутентефикации
        auth_button.configure(state="normal")
        login_button.configure(state="disabled")
        global isAuth
        isAuth = 0

    auth_button = ctk.CTkButton(nickname_window, text="Авторизация", command=chosen_auth)
    auth_button.grid(row=0, column=0, pady=1, sticky="ew")
    auth_button.configure(state="disabled")

    login_button = ctk.CTkButton(nickname_window, text="Аутентификация", command=chosen_login)
    login_button.grid(row=0, column=1, pady=1, sticky="ew")

    nickname_label = ctk.CTkLabel(nickname_window, text="Введите логин:")
    nickname_label.grid(pady=10, columnspan=2)

    nickname_entry = ctk.CTkEntry(nickname_window)
    nickname_entry.grid(pady=10, columnspan=2)

    password_label = ctk.CTkLabel(nickname_window, text="Введите пароль:")
    password_label.grid(pady=10, columnspan=2)

    password_entry = ctk.CTkEntry(nickname_window)
    password_entry.grid(pady=10, columnspan=2)



    def on_nickname_enter():
        nickname = nickname_entry.get()
        password = password_entry.get()

        if nickname:
            try:
                port = int(port_str)

                # Отправляем запрос на сервер и получаем ответ от него
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Инициализируем настройки сокета
                client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

                try:
                    # Сначала повторно проверяем сервер на доступность, если доступен, то начинаем передачу данных
                    client_socket.connect((ip, port))
                except:
                    CTkMessagebox(title="ERROR", message="Сервер не доступен!", icon="cancel")

                client_socket.send(f"{nickname};{password};{isAuth}".encode('utf-8'))
                response = client_socket.recv(3).decode('utf-8') # Получаем статус запроса
                print(response)

                if response == "200": # Если прошли аутентефикацию
                    nickname_window.destroy()

                    root = ctk.CTk()
                    app = MessengerApp(root, client_socket, nickname)
                    app.ip = ip
                    app.port = port
                
                    root.mainloop()
                elif response == "201":
                    CTkMessagebox(title="Server Response", message="Аккаунт успешно авторизирован", icon="check")
                    client_socket.close()

                elif response == "409":
                    CTkMessagebox(title="ERROR", message="Пользователь с таким именем уже существует!", icon="warning")
                    client_socket.close()
                
                elif response == "401":
                    CTkMessagebox(title="ERROR", message="Неверный логин или пароль!", icon="cancel")
                    client_socket.close()

            except ValueError:
                CTkMessagebox(title="ERROR", message="Invalid port number. Please enter a valid number.", icon="cancel")
    
    enter_button = ctk.CTkButton(nickname_window, text="Enter", command=on_nickname_enter)
    enter_button.grid(pady=10, columnspan=2)

    nickname_window.mainloop()

if __name__ == "__main__":
    enter_server_info()
