from logging import disable
import customtkinter as ctk
import socket
import threading
import time
from datetime import datetime, timezone
from collections import deque
from PIL import Image, ImageTk, ImageDraw, ImageGrab
from customtkinter import CTkImage
import json
import os
import ctypes as ct
import urllib.request
import random
import sys
import hashlib
import base64
import io
import tkinter as tk
from tkinter import filedialog
import asyncio
from concurrent.futures import ThreadPoolExecutor
try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    print('Предупреждение: библиотека plyer не установлена. Системные уведомления недоступны.')

def set_window_dark_title_bar(window):
    try:
        window.update()
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        set_window_attribute = ct.windll.dwmapi.DwmSetWindowAttribute
        get_parent = ct.windll.user32.GetParent
        hwnd = get_parent(window.winfo_id())
        rendering_policy = DWMWA_USE_IMMERSIVE_DARK_MODE
        value = 2
        value = ct.c_int(value)
        set_window_attribute(hwnd, rendering_policy, ct.byref(value), ct.sizeof(value))
    except:
        pass

class LicenseAgreementWindow:

    def __init__(self, master):
        self.dialog = ctk.CTkToplevel(master)
        self.dialog.title('Лицензионное соглашение')
        self.dialog.geometry('600x400')
        self.dialog.resizable(False, False)
        self.dialog.transient(master)
        self.dialog.focus_force()
        x = master.winfo_x() + (master.winfo_width() - 600) // 2
        y = master.winfo_y() + (master.winfo_height() - 400) // 2
        self.dialog.geometry(f'+{x}+{y}')
        self.text = ctk.CTkTextbox(self.dialog, width=550, height=350, wrap='word')
        self.text.pack(padx=20, pady=20)
        self.text.insert('1.0')
        self.text.configure(state='disabled')
        self.close_button = ctk.CTkButton(self.dialog, text='Закрыть', command=self.close_dialog)
        self.close_button.pack(pady=(0, 10))
        self.dialog.protocol('WM_DELETE_WINDOW', self.close_dialog)

    def close_dialog(self):
        self.dialog.destroy()

class InputWindow:

    def __init__(self, server, error=''):
        self.root = ctk.CTk()
        self.root.title('Регистрация SproutLine')
        self.root.geometry('700x450')
        self.root.resizable(False, False)
        self.server = server
        self.error = error
        self.isRegister = True
        center_window(self.root, 700, 450)
        self.main_frame = ctk.CTkFrame(self.root, fg_color='#1A1A1A')
        self.main_frame.pack(fill='both', expand=True)
        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color='#212121', corner_radius=15)
        self.content_frame.pack(fill='both', expand=True, padx=40, pady=20)
        self.title_frame = ctk.CTkFrame(self.content_frame, fg_color='transparent')
        self.title_frame.pack(pady=(12.5, 12.5))
        self.title_label = ctk.CTkLabel(self.title_frame, text='Регистрация', font=('Arial Bold', 28), text_color='#00ff88')
        self.title_label.pack()
        self.subtitle_label = ctk.CTkLabel(self.title_frame, text='Создайте аккаунт для начала общения', font=('Arial', 13), text_color='#888888')
        self.subtitle_label.pack()
        self.change_type_button = ctk.CTkButton(self.title_frame, fg_color='transparent', text='Или войдите в существующий', corner_radius=7.5, hover_color='#2D2D2D', font=('Arial', 12), text_color='#00ccff', command=self.change_type_of_window)
        self.change_type_button.pack()
        self.inputs_frame = ctk.CTkFrame(self.content_frame, fg_color='transparent')
        self.inputs_frame.pack(pady=5)
        entry_width = 300
        entry_height = 35
        self.nickname_entry = ctk.CTkEntry(self.inputs_frame, placeholder_text='Никнейм', width=entry_width, height=entry_height, font=('Arial', 13), fg_color='#2A2A2A', text_color='#FFFFFF', border_color='#00ff88', corner_radius=8)
        self.nickname_entry.pack(pady=6)
        self.password_entry = ctk.CTkEntry(self.inputs_frame, placeholder_text='Пароль', show='•', width=entry_width, height=entry_height, font=('Arial', 13), fg_color='#2A2A2A', text_color='#FFFFFF', border_color='#00ff88', corner_radius=8)
        self.password_entry.pack(pady=6)
        self.confirm_password_entry = ctk.CTkEntry(self.inputs_frame, placeholder_text='Подтвердите пароль', show='•', width=entry_width, height=entry_height, font=('Arial', 13), fg_color='#2A2A2A', text_color='#FFFFFF', border_color='#00ff88', corner_radius=8)
        self.confirm_password_entry.pack(pady=6)
        self.agreement_frame = ctk.CTkFrame(self.content_frame, fg_color='transparent')
        self.agreement_frame.pack(pady=6)
        self.agreement_var = ctk.BooleanVar()
        self.agreement_checkbox = ctk.CTkCheckBox(self.agreement_frame, text='Я согласен с', variable=self.agreement_var, checkbox_width=18, checkbox_height=18, font=('Arial', 12), fg_color='#00ff88', hover_color='#00cc6a', text_color='#888888')
        self.agreement_checkbox.pack(side='left')
        self.agreement_button = ctk.CTkButton(self.agreement_frame, text='лицензионным соглашением', fg_color='transparent', hover_color='#2D2D2D', font=('Arial', 12), text_color='#00ccff', command=self.show_license)
        self.agreement_button.pack(side='left')
        self.input_button = ctk.CTkButton(self.content_frame, text='Зарегистрироваться', width=250, height=40, font=('Arial Bold', 14), fg_color='#00ff88', text_color='#000000', hover_color='#00cc6a', corner_radius=8, command=self.inputFunc)
        self.input_button.pack(pady=10)
        self.return_button = ctk.CTkButton(self.content_frame, text='Вернуться к выбору серверов', width=150, height=20, font=('Arial Bold', 12), fg_color='#1A1A1A', hover_color='#212121', text_color='#00ff88', corner_radius=7.5, command=self.return_to_server_choose)
        self.return_button.pack()
        self.error_label = ctk.CTkLabel(self.content_frame, text=self.error, text_color='#ff3333', font=('Arial', 12))
        self.error_label.pack()
        try:
            with open(os.path.join('assets', 'config', 'user_data.json'), 'r') as f:
                user_data = json.load(f)
            if user_data:
                server_id = self.server.get('server_id')
                if server_id and server_id in user_data:
                    server_data = user_data[server_id]
                    if server_data and server_data.get('nickname'):
                        self.nickname_entry.insert(0, server_data['nickname'])
                        self.change_type_of_window()
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            pass
        self.root.mainloop()

    def change_type_of_window(self):
        if self.isRegister:
            self.root.title(f'Вход в аккаунт SproutLine')
            self.title_label.configure(text='Вход в аккаунт')
            self.subtitle_label.configure(text='Войдите в аккаунт для продолжения общения')
            self.change_type_button.configure(text='Или создайте новый')
            self.confirm_password_entry.pack_forget()
            self.agreement_frame.pack_forget()
            self.input_button.configure(text='Войти в аккаунт')
            self.isRegister = False
        else:
            self.root.title(f'Регистрация SproutLine')
            self.title_label.configure(text='Регистрация')
            self.subtitle_label.configure(text='Создайте аккаунт для начала общения')
            self.change_type_button.configure(text='Или войдите в существующий')
            self.nickname_entry.delete(0, 'end')
            self.nickname_entry.configure(placeholder_text='Никнейм')
            self.confirm_password_entry.pack(pady=6)
            self.agreement_frame.pack(pady=6)
            self.input_button.pack_forget()
            self.input_button.pack(pady=10)
            self.return_button.pack_forget()
            self.return_button.pack()
            self.error_label.pack_forget()
            self.error_label.pack()
            self.input_button.configure(text='Зарегистрироваться')
            self.isRegister = True

    def show_license(self):
        LicenseAgreementWindow(self.root)

    def return_to_server_choose(self):
        self.root.destroy()
        ServerListWindow()

    def inputFunc(self):
        nickname = self.nickname_entry.get().strip()
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        if not nickname or not password:
            self.error_label.configure(text='Заполните все поля')
            return
        if password != confirm_password and self.isRegister:
            self.error_label.configure(text='Пароли не совпадают')
            return
        if not self.agreement_var.get() and self.isRegister:
            self.error_label.configure(text='Примите лицензионное соглашение')
            return
        try:
            with open(os.path.join('assets', 'config', 'user_data.json'), 'w') as f:
                json.dump({self.server['server_id']: {'nickname': nickname}}, f)
            self.root.destroy()
            try:
                MessengerApp(self.server, nickname, password, self.isRegister)
            except Exception as e:
                InputWindow(self.server)
        except Exception as e:
            self.error_label.configure(text=f'Ошибка регистрации: {str(e)}')

class ServerListWindow:

    def __init__(self):
        self.root = ctk.CTk()
        self.root.title('Список серверов SproutLine')
        self.root.geometry('700x400')
        self.root.resizable(False, False)
        self.servers = self.load_servers()
        self.selected_server = None
        self.dialog_open = False
        self.main_frame = ctk.CTkFrame(self.root, fg_color='#1A1A1A')
        self.main_frame.pack(fill='both', expand=True)
        self.title_label = ctk.CTkLabel(self.main_frame, text='Список серверов', font=('Arial Bold', 24), text_color='#00ff88')
        self.title_label.pack(pady=(50, 10))
        self.servers_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color='#1E1E1E', width=660, height=200)
        self.servers_frame.pack(pady=10, padx=20)
        self.update_server_list()
        self.buttons_frame = ctk.CTkFrame(self.main_frame, fg_color='transparent')
        self.buttons_frame.pack(side='bottom', fill='x', padx=20, pady=20)
        button_width = 200
        button_height = 35
        self.add_button = ctk.CTkButton(self.buttons_frame, text='Добавить сервер', width=button_width, height=button_height, font=('Arial Bold', 13), fg_color='#242424', hover_color='#2D2D2D', text_color='#00ff88', command=self.add_server)
        self.add_button.pack(side='left', padx=10)
        self.edit_button = ctk.CTkButton(self.buttons_frame, text='Изменить', width=button_width, height=button_height, font=('Arial Bold', 13), fg_color='#242424', hover_color='#2D2D2D', text_color='#00ff88', command=self.edit_server)
        self.edit_button.pack(side='left', padx=10)
        self.delete_button = ctk.CTkButton(self.buttons_frame, text='Удалить', width=button_width, height=button_height, font=('Arial Bold', 13), fg_color='#242424', hover_color='#2D2D2D', text_color='#00ff88', command=self.delete_server)
        self.delete_button.pack(side='left', padx=10)
        self.root.mainloop()

    def load_servers(self):
        try:
            with open(os.path.join('assets', 'config', 'servers.json'), 'r') as f:
                return json.load(f)
        except:
            return []

    def save_servers(self):
        with open(os.path.join('assets', 'config', 'servers.json'), 'w') as f:
            json.dump(self.servers, f)

    def update_server_list(self):
        for widget in self.servers_frame.winfo_children():
            widget.destroy()
        for server in self.servers:
            server_frame = ctk.CTkFrame(self.servers_frame, fg_color='#2D2D2D', corner_radius=10, height=80)
            server_frame.pack(fill='x', pady=5, padx=5, ipady=10)
            server_frame.pack_propagate(False)
            server_frame.bind('<Button-1>', lambda e, s=server: self.select_server(s, e))
            info_frame = ctk.CTkFrame(server_frame, fg_color='transparent')
            info_frame.pack(side='left', padx=15, fill='both', expand=True)
            info_frame.bind('<Button-1>', lambda e, s=server: self.select_server(s, e))
            name_label = ctk.CTkLabel(info_frame, text=server['name'], font=('Arial Bold', 16), text_color='#00ff88')
            name_label.pack(anchor='w', pady=(5, 0))
            name_label.bind('<Button-1>', lambda e, s=server: self.select_server(s, e))
            info_label = ctk.CTkLabel(info_frame, text=f"IP: {server['ip']}:{server['port']}", font=('Arial', 12), text_color='#888888')
            info_label.pack(anchor='w')
            info_label.bind('<Button-1>', lambda e, s=server: self.select_server(s, e))
            connect_button = ctk.CTkButton(server_frame, text='Подключиться', width=120, height=30, font=('Arial Bold', 12), fg_color='#1E1E1E', hover_color='#2D2D2D', text_color='#00ff88', command=lambda s=server: self.connect_to_server(s))
            connect_button.pack(side='right', padx=15)
            if self.selected_server == server:
                server_frame.configure(fg_color='#3D3D3D')

    def select_server(self, server, event=None):
        self.selected_server = server
        self.update_server_list()

    def add_server(self):
        if not self.dialog_open:
            self.dialog_open = True
            dialog = ServerDialog(self.root, 'Добавить сервер')
            dialog.dialog.transient(self.root)
            dialog.dialog.focus_force()
            result = dialog.show()
            self.dialog_open = False
            if result:
                self.servers.append(result)
                self.save_servers()
                self.update_server_list()

    def edit_server(self):
        if not self.selected_server:
            AlertFrame(self.root, f'Выберите сервер для редактирования', False)
            return
        if not self.dialog_open:
            self.dialog_open = True
            dialog = ServerDialog(self.root, 'Изменить сервер')
            dialog.dialog.grab_set()
            dialog.dialog.transient(self.root)
            dialog.dialog.focus_force()
            dialog.name_entry.insert(0, self.selected_server['name'])
            dialog.ip_entry.insert(0, self.selected_server['ip'])
            dialog.port_entry.insert(0, self.selected_server['port'])
            result = dialog.show()
            self.dialog_open = False
            if result:
                index = self.servers.index(self.selected_server)
                self.servers[index] = result
                self.save_servers()
                self.selected_server = result
                self.update_server_list()

    def delete_server(self):
        if not self.selected_server:
            AlertFrame(self.root, 'Выберите сервер для удаления', False)
            return
        self.servers.remove(self.selected_server)
        self.save_servers()
        self.selected_server = None
        self.update_server_list()

    def connect_to_server(self, server):
        self.root.destroy()
        InputWindow(server)

    async def _load_external_ip_async_internal(self):
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(None, lambda: urllib.request.urlopen('https://api.ipify.org', timeout=5).read().decode('utf-8'))
            return result
        except:
            return 'Недоступно'

    def _load_external_ip_async(self, ip_label):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            external_ip = loop.run_until_complete(self._load_external_ip_async_internal())
            loop.close()
            if ip_label.winfo_exists():
                ip_label.configure(text=external_ip)
        except:
            if ip_label.winfo_exists():
                ip_label.configure(text='Недоступно')

    def show_profile(self):
        if not hasattr(self, 'profile_window') or not self.profile_window.winfo_exists():
            profile_thread = threading.Thread(target=self._create_profile_window)
            profile_thread.daemon = True
            profile_thread.start()

    def _create_profile_window(self):
        self.profile_window = ctk.CTkToplevel()
        self.profile_window.title('Профиль')
        self.profile_window.geometry('400x500')
        self.profile_window.resizable(False, False)
        self.profile_window.protocol('WM_DELETE_WINDOW', self.on_profile_window_close)
        self.profile_window.configure(fg_color='#1A1A1A')
        self.profile_window.transient(self.root)
        self.profile_window.focus_force()
        x = self.root.winfo_x() + (self.root.winfo_width() - 400) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 500) // 2
        self.profile_window.geometry(f'+{x}+{y}')
        profile_frame = ctk.CTkFrame(self.profile_window, fg_color='#212121', corner_radius=10)
        profile_frame.pack(padx=20, pady=20, fill='both', expand=True)
        avatar_frame = ctk.CTkFrame(profile_frame, width=120, height=120, corner_radius=60, fg_color='#2A2A2A')
        avatar_frame.pack(pady=(30, 20))
        avatar_frame.pack_propagate(False)
        avatar_label = ctk.CTkLabel(avatar_frame, text='👤', font=('Arial', 50), text_color='#888888')
        avatar_label.place(relx=0.5, rely=0.5, anchor='center')
        try:
            with open(os.path.join('assets', 'config', 'user_data.json'), 'r') as f:
                user_data = json.load(f)
                nickname = user_data['nickname']
                user_id = user_data.get('user_id', 'Неизвестно')
        except:
            nickname = 'Неизвестно'
            user_id = 'Неизвестно'
        ctk.CTkLabel(profile_frame, text=nickname, font=('Arial Bold', 24), text_color='#ffffff').pack(pady=(0, 5))
        ctk.CTkLabel(profile_frame, text=f'ID: {user_id}', font=('Arial', 12), text_color='#888888').pack(pady=(0, 20))
        separator = ctk.CTkFrame(profile_frame, height=2, fg_color='#2A2A2A')
        separator.pack(fill='x', padx=30, pady=20)
        info_frame = ctk.CTkFrame(profile_frame, fg_color='transparent')
        info_frame.pack(fill='x', padx=30)
        status_frame = ctk.CTkFrame(info_frame, fg_color='transparent')
        status_frame.pack(fill='x', pady=5)
        ctk.CTkLabel(status_frame, text='Статус:', font=('Arial', 14), text_color='#888888').pack(side='left')
        self.connected = check_internet_connection()
        ctk.CTkLabel(status_frame, text='В сети' if self.connected else 'Не в сети', font=('Arial', 14), text_color='#00ff88' if self.connected else '#ff3333').pack(side='right')
        ip_frame = ctk.CTkFrame(info_frame, fg_color='transparent')
        ip_frame.pack(fill='x', pady=5)
        ctk.CTkLabel(ip_frame, text='IP адрес:', font=('Arial', 14), text_color='#888888').pack(side='left')
        ip_label = ctk.CTkLabel(ip_frame, text='Загрузка...', font=('Arial', 14), text_color='#ffffff')
        ip_label.pack(side='right')
        threading.Thread(target=self._load_external_ip_async, args=(ip_label,), daemon=True).start()
        reg_frame = ctk.CTkFrame(info_frame, fg_color='transparent')
        reg_frame.pack(fill='x', pady=5)
        ctk.CTkLabel(reg_frame, text='Дата регистрации:', font=('Arial', 14), text_color='#888888').pack(side='left')
        try:
            reg_date = time.strftime('%d.%m.%Y', time.localtime(os.path.getctime(os.path.join('assets', 'config', 'user_data.json'))))
        except:
            reg_date = 'Неизвестно'
        ctk.CTkLabel(reg_frame, text=reg_date, font=('Arial', 14), text_color='#ffffff').pack(side='right')
        separator2 = ctk.CTkFrame(profile_frame, height=2, fg_color='#2A2A2A')
        separator2.pack(fill='x', padx=30, pady=20)
        buttons_frame = ctk.CTkFrame(profile_frame, fg_color='transparent')
        buttons_frame.pack(fill='x', padx=30, pady=(0, 20))
        change_nick_btn = ctk.CTkButton(buttons_frame, text='Изменить никнейм', font=('Arial', 14), fg_color='#2A2A2A', hover_color='#333333', height=35)
        change_nick_btn.pack(fill='x', pady=5)
        logout_btn = ctk.CTkButton(buttons_frame, text='Выйти из аккаунта', font=('Arial', 14), fg_color='#2A2A2A', hover_color='#333333', text_color='#ff3333', height=35)
        logout_btn.pack(fill='x', pady=5)

    def on_profile_window_close(self):
        self.profile_window.destroy()
        if hasattr(self, 'profile_window'):
            delattr(self, 'profile_window')

class ServerDialog:

    def __init__(self, parent, title):
        self.dialog = ctk.CTkToplevel()
        self.dialog.title(title)
        self.dialog.geometry('400x300')
        self.dialog.resizable(False, False)
        self.dialog.configure(fg_color='#1A1A1A')
        self.dialog.transient(parent)
        self.dialog.focus_force()
        x = parent.winfo_x() + (parent.winfo_width() - 400) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 300) // 2
        self.dialog.geometry(f'+{x}+{y}')
        main_frame = ctk.CTkFrame(self.dialog, fg_color='#212121', corner_radius=10)
        main_frame.pack(padx=20, pady=20, fill='both', expand=True)
        self.name_entry = ctk.CTkEntry(main_frame, placeholder_text='Название сервера', fg_color='#2A2A2A', text_color='#ffffff', placeholder_text_color='#888888')
        self.name_entry.pack(pady=10, padx=20, fill='x')
        self.ip_entry = ctk.CTkEntry(main_frame, placeholder_text='IP адрес', fg_color='#2A2A2A', text_color='#ffffff', placeholder_text_color='#888888')
        self.ip_entry.pack(pady=10, padx=20, fill='x')
        self.port_entry = ctk.CTkEntry(main_frame, placeholder_text='Порт', fg_color='#2A2A2A', text_color='#ffffff', placeholder_text_color='#888888')
        self.port_entry.pack(pady=10, padx=20, fill='x')
        self.ok_button = ctk.CTkButton(main_frame, text='OK', fg_color='#1E1E1E', hover_color='#2D2D2D', text_color='#00ff88', command=self.on_ok)
        self.ok_button.pack(pady=10)
        self.cancel_button = ctk.CTkButton(main_frame, text='Отмена', fg_color='#1E1E1E', hover_color='#2D2D2D', text_color='#ff3333', command=self.dialog.destroy)
        self.cancel_button.pack(pady=5)
        self.result = None

    def on_ok(self):
        seed = sum((ord(c) for c in self.name_entry.get()))
        random.seed(seed)
        server_id = ''.join([str(random.randint(0, 9)) for _ in range(9)])
        random.seed()
        self.result = {'name': self.name_entry.get(), 'ip': self.ip_entry.get(), 'port': self.port_entry.get(), 'server_id': server_id}
        self.dialog.destroy()

    def show(self):
        self.dialog.wait_window()
        return self.result

class MessageFrame:

    def __init__(self, root, title, message_icon, message_color, message_text, hide_root=False):
        self.hide_root = hide_root
        master = ctk.CTkToplevel(root)
        if self.hide_root:
            root.withdraw()
            master.protocol('WM_DELETE_WINDOW', root.destroy)
        self.title = title
        self.message_icon = message_icon
        self.message_color = message_color
        self.message_text = '\n'.join((message_text[i:i + 55] for i in range(0, len(message_text), 55)))

        def closeWindow():
            master.destroy()
            if self.hide_root:
                root.destroy()
            ServerListWindow()
        master.configure(fg_color='#1A1A1A')
        master.geometry('700x350')
        master.resizable(False, False)
        master.title(f'SproutLine - {self.title}')
        content_frame = ctk.CTkFrame(master, fg_color='#1E1E1E', corner_radius=10, width=700, height=350)
        content_frame.place(relx=0.5, rely=0.5, anchor='center')
        ban_label = ctk.CTkLabel(content_frame, text=self.message_icon, font=('Arial', 40), text_color=self.message_color)
        ban_label.pack(pady=(20, 5))
        message_label = ctk.CTkLabel(content_frame, text=self.message_text, font=('Arial Bold', 24), text_color=self.message_color)
        message_label.pack(pady=5)
        close_button = ctk.CTkButton(content_frame, text='Закрыть', font=('Arial', 14), fg_color='#2A2A2A', hover_color='#3A3A3A', command=closeWindow, width=120)
        close_button.pack(pady=15)

class AlertFrame(MessageFrame):

    def __init__(self, master):
        self.title = 'Alert window'
        self.message_icon = '⚠️'
        self.message_color = '#FFF133'
        self.message_text = 'Вы были отключены от сервера'
        super().__init__(master, self.title, self.message_icon, self.message_color, self.message_text, True)

class BanFrame(MessageFrame):

    def __init__(self, master):
        self.title = 'Ban Window'
        self.message_icon = '⛔'
        self.message_color = '#FF3333'
        self.message_text = 'ВЫ ЗАБАНЕНЫ'
        super().__init__(master, self.title, self.message_icon, self.message_color, self.message_text, True)

class ErrorFrame(MessageFrame):

    def __init__(self, master, error_text, hide_root=True):
        self.title = 'Error Window'
        self.message_icon = '☠️'
        self.message_color = '#FFFFFF'
        self.message_text = error_text
        super().__init__(master, self.title, self.message_icon, self.message_color, self.message_text, hide_root)

async def check_internet_connection_async():
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: urllib.request.urlopen('http://google.com', timeout=1))
        return True
    except:
        return False

def check_internet_connection():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(check_internet_connection_async())
        loop.close()
        return result
    except:
        try:
            urllib.request.urlopen('http://google.com', timeout=1)
            return True
        except:
            return False

class MessengerApp:

    def __init__(self, server, nickname, password, isRegister):
        self.root = ctk.CTk()
        self.nickname = nickname
        self.password = password
        self.isRegister = 'R' if isRegister else 'L'
        self.server = server
        self.ip = server['ip']
        self.port = int(server['port'])
        self.client_socket = None
        self.connected = False
        self.unsent_messages = []
        self.send_lock = threading.Lock()
        self.message_queue = deque()
        self.message_queue_lock = threading.Lock()
        self.gui_update_pending = False
        self.pending_local_messages = set()
        self.max_pending_messages = 500
        self.is_loading_history = False
        self.history_buffer = []
        self.history_timeout_id = None
        self.history_display_index = 0
        self.history_display_task = None
        self.user_cards = []
        self.nickname_history = {nickname: nickname}
        self.users_online_status = {}
        self.init_userlist = []
        self.message_cooldown = 0
        self.after_ids = []
        self.is_closing = False
        window_width = 900
        window_height = 450
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width // 2 - window_width // 2
        y = screen_height // 2 - window_height // 2
        self.root.geometry(f'{window_width}x{window_height}+{x}+{y}')
        self.root.protocol('WM_DELETE_WINDOW', self.on_closing)
        threading.Thread(target=self._async_connect_wrapper, daemon=True).start()
        self.root.after(100, self.setup_interface)
        self.root.after(200, self.check_connection_status)
        self.root.mainloop()

    def on_closing(self):
        self.is_closing = True
        if hasattr(self, 'after_ids'):
            for task_id in self.after_ids:
                try:
                    self.root.after_cancel(task_id)
                except:
                    pass
        if hasattr(self, 'history_timeout_id') and self.history_timeout_id:
            try:
                self.root.after_cancel(self.history_timeout_id)
            except:
                pass
        if hasattr(self, 'typing_timeout_id') and self.typing_timeout_id:
            try:
                self.root.after_cancel(self.typing_timeout_id)
            except:
                pass
        try:
            if self.client_socket:
                self.client_socket.close()
        except:
            pass
        try:
            self.root.destroy()
        except:
            pass

    def safe_after(self, delay_ms, callback, *args):
        if self.is_closing or not hasattr(self, 'root'):
            return None
        try:
            if not self.root.winfo_exists():
                return None
        except:
            return None

        def safe_callback(*cb_args):
            if self.is_closing or not hasattr(self, 'root'):
                return
            try:
                if not self.root.winfo_exists():
                    return
            except:
                return
            try:
                callback(*cb_args)
            except Exception:
                pass
        task_id = self.root.after(delay_ms, lambda: safe_callback(*args))
        if hasattr(self, 'after_ids'):
            self.after_ids.append(task_id)
        return task_id

    async def _async_connect(self):
        loop = asyncio.get_event_loop()

        def create_socket():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            return sock
        self.client_socket = await loop.run_in_executor(None, create_socket)

        def connect_socket():
            self.client_socket.connect((self.ip, self.port))
            return True
        await loop.run_in_executor(None, connect_socket)

        def send_auth():
            local_tz = datetime.now(timezone.utc).astimezone().utcoffset()
            timezone_offset = int(local_tz.total_seconds() / 3600)
            self.client_socket.send(f'{self.isRegister};{self.nickname};{self.password};{timezone_offset}'.encode('utf-8'))
            return True
        await loop.run_in_executor(None, send_auth)

        def recv_response():
            return self.client_socket.recv(1024).decode('utf-8')
        initial_response = await loop.run_in_executor(None, recv_response)
        return initial_response

    def _async_connect_wrapper(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            initial_response = loop.run_until_complete(self._async_connect())
            loop.close()
            self.root.after(0, lambda: self._handle_initial_response(initial_response))
        except Exception as e:
            self.root.after(0, lambda: ErrorFrame(self.root, f'Ошибка при инициализации: {e}'))

    def _handle_initial_response(self, initial_response):
        try:
            if initial_response == 'ERROR:BANNED':
                self.show_ban_frame()
                return
            if initial_response == 'ERROR:NICKNAME_TAKEN':
                self.root.destroy()
                InputWindow(self.server, error='Пользователь с таким именем уже существует')
                return
            if initial_response == 'ERROR:NICKNAME_ONLINE':
                self.root.destroy()
                InputWindow(self.server, error='Пользователь с таким именем в данный момент находится в чате')
                return
            if initial_response == 'ERROR:WRONG_PASSWORD':
                self.root.destroy()
                InputWindow(self.server, error='Неверный пароль')
                return
            if initial_response == 'ERROR:WRONG_OPERATION':
                self.root.destroy()
                InputWindow(self.server, error='Неверная операция, ошибка приложения')
                return
            if initial_response[:4] == 'CCT:':
                response = initial_response[4:].split(';')
                self.message_cooldown = int(response[0])
                self.init_userlist = [user.strip() for user in response[1][6:].split(',') if user.strip()]
            self.connected = True
        except Exception as e:
            ErrorFrame(self.root, f'Ошибка при обработке ответа: {e}')

    def setup_interface(self):
        if self.is_closing or not hasattr(self, 'root'):
            return
        try:
            if not self.root.winfo_exists():
                return
        except:
            return
        self.root.title(f'SproutLine - {self.nickname}')
        self.root.resizable(False, False)
        self.themes = {'dark': {'bg': '#1A1A1A', 'fg': '#FFFFFF', 'button': '#2D2D2D', 'button_hover': '#3D3D3D', 'frame': '#1A1A1A', 'accent': '#00ff88', 'text_box': '#2D2D2D'}, 'black': {'bg': '#000000', 'fg': '#FFFFFF', 'button': '#1A1A1A', 'button_hover': '#2D2D2D', 'frame': '#000000', 'accent': '#00ff88', 'text_box': '#1A1A1A'}, 'dark_blue': {'bg': '#1A1A2D', 'fg': '#FFFFFF', 'button': '#2D2D40', 'button_hover': '#3D3D50', 'frame': '#1A1A2D', 'accent': '#00bfff', 'text_box': '#2D2D40'}, 'dark_red': {'bg': '#2D1A1A', 'fg': '#FFFFFF', 'button': '#402D2D', 'button_hover': '#503D3D', 'frame': '#2D1A1A', 'accent': '#ff4444', 'text_box': '#402D2D'}, 'dark_purple': {'bg': '#2D1A2D', 'fg': '#FFFFFF', 'button': '#402D40', 'button_hover': '#503D50', 'frame': '#2D1A2D', 'accent': '#bf5fff', 'text_box': '#402D40'}, 'dark_green': {'bg': '#1A2D1A', 'fg': '#FFFFFF', 'button': '#2D402D', 'button_hover': '#3D503D', 'frame': '#1A2D1A', 'accent': '#44ff44', 'text_box': '#2D402D'}, 'dark_gold': {'bg': '#2D2D1A', 'fg': '#FFFFFF', 'button': '#40402D', 'button_hover': '#50503D', 'frame': '#2D2D1A', 'accent': '#ffd700', 'text_box': '#40402D'}, 'dark_cyan': {'bg': '#1A2D2D', 'fg': '#FFFFFF', 'button': '#2D4040', 'button_hover': '#3D5050', 'frame': '#1A2D2D', 'accent': '#00ffff', 'text_box': '#2D4040'}, 'dark_pink': {'bg': '#2D1A24', 'fg': '#FFFFFF', 'button': '#402D37', 'button_hover': '#503D47', 'frame': '#2D1A24', 'accent': '#ff69b4', 'text_box': '#402D37'}, 'midnight_blue': {'bg': '#151B2D', 'fg': '#FFFFFF', 'button': '#1D2540', 'button_hover': '#2D3550', 'frame': '#151B2D', 'accent': '#4169E1', 'text_box': '#1D2540'}, 'deep_purple': {'bg': '#2D1B40', 'fg': '#FFFFFF', 'button': '#402D53', 'button_hover': '#503D63', 'frame': '#2D1B40', 'accent': '#9370DB', 'text_box': '#402D53'}}
        self.settings = {'show_seconds': True, 'message_sound': True, 'auto_scroll': True, 'font_size': 14, 'text_scale': 1.0, 'show_join_leave': True, 'current_theme': 'black'}
        self.load_settings()
        self.current_theme = self.settings.get('current_theme', 'black')
        try:
            self.image_send = Image.open(os.path.join('assets', 'images', 'send.png'))
            self.image_send = self.image_send.resize((500, 500), Image.LANCZOS)
            self.image_exit = Image.open(os.path.join('assets', 'images', 'exit.png'))
            self.image_exit = self.image_exit.resize((50, 50), Image.LANCZOS)
            self.image_settings = Image.open(os.path.join('assets', 'images', 'settings.png'))
            self.image_settings = self.image_settings.resize((50, 50), Image.LANCZOS)
            self.image_message = Image.open(os.path.join('assets', 'images', 'message.png'))
            self.image_message = self.image_message.resize((50, 50), Image.LANCZOS)
            self.image_photo = Image.open(os.path.join('assets', 'images', 'photo.png'))
            self.image_photo = self.image_photo.resize((50, 50), Image.LANCZOS)
            self.photo_send = CTkImage(light_image=None, dark_image=self.image_send)
            self.photo_exit = CTkImage(light_image=None, dark_image=self.image_exit)
            self.photo_settings = CTkImage(light_image=None, dark_image=self.image_settings)
            self.photo_message = CTkImage(light_image=None, dark_image=self.image_message)
            self.photo_photo = CTkImage(light_image=None, dark_image=self.image_photo)
        except Exception as e:
            ErrorFrame(self.root, f'Ошибка при загрузке изображения: {e}', False)
            self.photo_send = None
            self.photo_exit = None
        self.current_users = []
        self.typing_users = set()
        self.is_typing = False
        self.last_typing_time = 0
        self.typing_timeout_id = None
        self.message_display = ctk.CTkScrollableFrame(self.root, width=630, height=373, corner_radius=10, fg_color='#1E1E1E')
        self.message_display.place(relx=0.06, rely=0.01)
        self.message_widgets = []
        self.message_data = []
        self.visible_range = [0, 50]
        self.max_visible_messages = 50
        self.image_cache = []
        self.pending_local_messages = set()
        self.users_frame = ctk.CTkFrame(self.root, width=175, height=440, corner_radius=10, fg_color='#1B1B1B')
        self.users_frame.place(relx=0.8, rely=0.01)
        self.users_label = ctk.CTkLabel(self.users_frame, text='👥 Участники', text_color='#00ff88', font=('Arial Bold', 14), anchor='w')
        self.users_label.place(relx=0.08, rely=0.02)
        self.users_separator = ctk.CTkFrame(self.users_frame, height=2, fg_color='#00ff88', corner_radius=1)
        self.users_separator.place(relx=0.08, rely=0.095, relwidth=0.84)
        self.users_list = ctk.CTkScrollableFrame(self.users_frame, width=155, height=395, fg_color='#1B1B1B', corner_radius=5)
        self.users_list.place(relx=0.03, rely=0.12)
        self.input_frame = ctk.CTkFrame(self.root, fg_color='#2D2D2D', corner_radius=25, border_width=1, border_color='#00ff88', height=40)
        self.input_frame.place(relx=0.06, rely=0.89, relwidth=0.73)
        self.send_image_button = ctk.CTkButton(self.input_frame, image=self.photo_photo if hasattr(self, 'photo_photo') else None, width=35, height=35, font=('Arial', 20), text='', fg_color='#1a1a1a', hover_color='#303030', corner_radius=30, command=self.send_image)
        self.send_image_button.pack(side='left', padx=(12, 12), pady=2.5)
        self.message_entry = ctk.CTkEntry(self.input_frame, width=450, height=35, font=('Arial', 13), fg_color='transparent', border_width=0, placeholder_text='Сообщение...')
        self.message_entry.pack(side='left', padx=1, pady=2.5)
        self.message_entry.bind('<Return>', lambda event: self.send_message())
        self.message_entry.bind('<KeyRelease>', self._on_message_typing)
        self.message_entry.bind('<Key>', self._on_message_key)
        self.root.bind_all('<Control-v>', self._handle_paste_event)
        self.root.bind_all('<Control-V>', self._handle_paste_event)
        self.message_entry.bind('<Control-v>', self._handle_paste_event)
        self.message_entry.bind('<Control-V>', self._handle_paste_event)
        self.message_entry.bind('<KeyPress>', self._handle_keypress_for_paste)
        self.message_entry.bind('<Button-2>', self._handle_paste)
        self.message_entry.bind('<Button-3>', self._handle_paste)
        self.mention_list_frame = None
        self.mention_list = None
        self.current_mention_start = None
        self.send_button = ctk.CTkButton(self.input_frame, image=self.photo_send if hasattr(self, 'photo_send') else None, width=35, height=35, font=('Arial', 15), text='', fg_color='#1a1a1a', hover_color='#303030', corner_radius=30, command=self.send_message)
        self.send_button.pack(side='right', padx=(43, 12), pady=2.5)
        self.settings_button = ctk.CTkButton(self.root, text='', image=self.photo_settings, width=40, height=40, fg_color='#2d2d2d', hover_color='#303030', font=('Arial', 12), command=self.show_settings)
        self.settings_button.place(relx=0.008, rely=0.89)
        self.disconnect_button = ctk.CTkButton(self.root, text='', image=self.photo_exit, width=40, height=40, fg_color='#2d2d2d', hover_color='#303030', font=('Arial', 12), command=self.disconnect_from_server)
        self.disconnect_button.place(relx=0.008, rely=0.79)
        self.private_messages = ctk.CTkButton(self.root, text='', image=self.photo_message, width=40, height=40, fg_color='#2d2d2d', hover_color='#303030', font=('Arial', 12), command=self.show_private_messages)
        self.private_messages.place(relx=0.008, rely=0.01)
        self.receive_thread = threading.Thread(target=self.receive_messages)
        self.receive_thread.daemon = True
        self.receive_thread.start()
        self.keep_alive_thread = threading.Thread(target=self.keep_alive)
        self.keep_alive_thread.daemon = True
        self.keep_alive_thread.start()
        self.last_message_time = 0
        self.local_message_cooldown = 1.0
        self.max_message_length = 10000000
        self.reply_to_message = None
        self.messages_by_hash = {}
        self.mention_list_frame = None
        self.mention_list = None
        self.current_mention_start = None
        self.mentioned_users = set()
        self.mention_selection_blocked = False
        self.cooldown_animation_id = None
        self.cooldown_container = ctk.CTkFrame(self.root, fg_color='transparent', corner_radius=0)
        self.cooldown_notification = ctk.CTkLabel(self.cooldown_container, text='', text_color='#00ff88', font=('Arial', 12), fg_color='#1a5a3a', corner_radius=0, height=28, width=100, anchor='center', padx=12, pady=4)
        self.cooldown_notification.pack()
        self.cooldown_container.place(relx=0.4, rely=0.82, anchor='center')
        self.cooldown_container.place_forget()
        self.update_users_list(self.init_userlist)
        self.apply_saved_settings()
        self.reply_indicator_frame = None
        self.reply_indicator_label = None
        self.reply_cancel_button = None

    def _select_message_for_reply(self, message_hash, username, text, timestamp):
        self.reply_to_message = {'hash': message_hash, 'username': username, 'text': text[:50] + '...' if len(text) > 50 else text, 'timestamp': timestamp}
        self._show_reply_indicator()

    def _show_reply_indicator(self):
        if not self.reply_to_message:
            return
        if self.reply_indicator_frame:
            self.reply_indicator_frame.destroy()
        self.reply_indicator_frame = ctk.CTkFrame(self.root, fg_color='#2B2B2B', corner_radius=10, height=50)
        window_height = self.root.winfo_height()
        input_y = int(window_height * 0.89)
        reply_y = input_y - 22 - 10
        if reply_y < 10:
            reply_y = 10
        self.reply_indicator_frame.place(relx=0.06, y=reply_y, relwidth=0.73)
        reply_text = f"Ответ на {self.reply_to_message['username']}: {self.reply_to_message['text']}"
        self.reply_indicator_label = ctk.CTkLabel(self.reply_indicator_frame, text=reply_text, font=('Arial', 11), text_color='#FFFFFF', anchor='w')
        self.reply_indicator_label.pack(side='left', padx=10, fill='x', expand=True)
        self.reply_cancel_button = ctk.CTkButton(self.reply_indicator_frame, text='✕', width=30, height=30, font=('Arial', 12), fg_color='transparent', hover_color='#3D3D3D', command=self._cancel_reply)
        self.reply_cancel_button.pack(side='right', padx=5)

    def _cancel_reply(self):
        self.reply_to_message = None
        if self.reply_indicator_frame:
            self.reply_indicator_frame.destroy()
            self.reply_indicator_frame = None

    def send_message(self):
        message = self.message_entry.get().strip()
        current_time = time.time()
        if not message:
            self.message_entry.delete(0, 'end')
            return
        time_since_last = current_time - self.last_message_time
        if time_since_last < self.local_message_cooldown:
            self.show_cooldown_notification('Подождите')
            return
        if message:
            self.message_entry.delete(0, 'end')
            if getattr(self, 'is_typing', False):
                self.is_typing = False
                self._send_typing_state(False)
            if hasattr(self, 'typing_timeout_id') and self.typing_timeout_id is not None:
                try:
                    self.root.after_cancel(self.typing_timeout_id)
                except Exception:
                    pass
                self.typing_timeout_id = None
            if self.connected:
                self.last_message_time = current_time
                if self.reply_to_message:
                    message = f"REPLY:{self.reply_to_message['hash']}:{message}"
                    self._cancel_reply()
                threading.Thread(target=self._send_message_thread, args=(message,)).start()
                self.clear_notification()
            else:
                self.last_message_time = current_time
                self.unsent_messages.append(message)
                threading.Thread(target=self.reconnect).start()

    def send_image(self):
        if not self.connected:
            self.show_notification('Нет соединения с сервером')
            return
        threading.Thread(target=self._send_image_async, daemon=True).start()

    def _send_image_async(self):
        try:
            file_path = filedialog.askopenfilename(title='Выберите изображение', filetypes=(('Изображения', '*.png *.jpg *.jpeg *.gif *.webp'), ('Все файлы', '*.*')))
            if not file_path:
                return
            try:
                pil_img = Image.open(file_path)
            except Exception:
                self.root.after(0, lambda: self.show_notification('Не удалось открыть выбранное изображение'))
                return
            try:
                filename = os.path.basename(file_path)
                buffer = io.BytesIO()
                pil_img.save(buffer, format=pil_img.format or 'PNG')
                raw_data = buffer.getvalue()
                encoded = base64.b64encode(raw_data).decode('ascii')
                successful_payload = f'IMG:{filename}:{encoded}'
                payload_size = len(successful_payload.encode('utf-8'))
                if payload_size > 10 * 1024 * 1024:
                    self.root.after(0, lambda: self.show_notification('Изображение слишком большое (максимум 10 МБ)'))
                    return
                if self.connected:
                    threading.Thread(target=self._send_message_thread, args=(successful_payload,), daemon=True).start()
                    self.root.after(0, self.clear_notification)
                else:
                    self.root.after(0, lambda: self.show_notification('Нет соединения с сервером'))
            except Exception as e:
                print(f'Ошибка при подготовке изображения: {e}')
                self.root.after(0, lambda: self.show_notification(f'Ошибка при отправке изображения: {str(e)}'))
        except Exception as e:
            self.root.after(0, lambda: self.show_notification(f'Ошибка: {str(e)}'))

    def _send_image_from_clipboard(self, pil_img=None):
        if not self.connected:
            self.root.after(0, lambda: self.show_notification('Нет соединения с сервером'))
            return
        if pil_img is None:
            pil_img = self._check_clipboard_for_image()
            if pil_img is None:
                print('Не удалось получить изображение из буфера обмена')
                return
        threading.Thread(target=self._send_image_from_clipboard_async, args=(pil_img,), daemon=True).start()

    def _send_image_from_clipboard_async(self, pil_img):
        try:
            if pil_img is None:
                print('Изображение не передано в функцию')
                return
            if not isinstance(pil_img, Image.Image):
                print(f'Переданный объект не является изображением: {type(pil_img)}')
                return
            try:
                size = pil_img.size
                if not size or len(size) != 2 or size[0] <= 0 or (size[1] <= 0):
                    print(f'Изображение пустое или некорректное: {size}')
                    return
                print(f'Обработка изображения: размер {size}, режим {pil_img.mode}')
            except Exception as e:
                print(f'Ошибка при проверке размера изображения: {e}')
                return
            try:
                timestamp = int(time.time())
                filename = f'clipboard_{timestamp}.png'
                buffer = io.BytesIO()
                pil_img.save(buffer, format='PNG')
                raw_data = buffer.getvalue()
                encoded = base64.b64encode(raw_data).decode('ascii')
                successful_payload = f'IMG:{filename}:{encoded}'
                payload_size = len(successful_payload.encode('utf-8'))
                if payload_size > 10 * 1024 * 1024:
                    self.root.after(0, lambda: self.show_notification('Изображение слишком большое (максимум 10 МБ)'))
                    return
                if self.connected:
                    threading.Thread(target=self._send_message_thread, args=(successful_payload,), daemon=True).start()
                    self.root.after(0, self.clear_notification)
                else:
                    self.root.after(0, lambda: self.show_notification('Нет соединения с сервером'))
            except Exception as e:
                print(f'Ошибка при подготовке изображения из буфера обмена: {e}')
                import traceback
                traceback.print_exc()
                self.root.after(0, lambda: self.show_notification(f'Ошибка при отправке изображения: {str(e)}'))
        except Exception as e:
            print(f'Критическая ошибка при отправке изображения: {e}')
            import traceback
            traceback.print_exc()

    def _send_message_thread(self, message):
        with self.send_lock:
            try:
                message_to_send = f'{self.nickname}: {message}\n'.encode('utf-8')
                message_len = len(message_to_send)
                total_sent = 0
                if message.startswith('IMG:'):
                    print(f'Отправка изображения, размер: {message_len} байт')
                chunk_size = 8192
                while total_sent < message_len:
                    try:
                        chunk = message_to_send[total_sent:total_sent + chunk_size]
                        if not chunk:
                            break
                        sent = self.client_socket.send(chunk)
                        if sent == 0:
                            raise ConnectionError('Socket connection broken')
                        total_sent += sent
                        if message_len > 100000 and total_sent < message_len:
                            time.sleep(0.001)
                    except (socket.error, ConnectionError, OSError) as e:
                        self.unsent_messages.append(message)
                        self.root.after(0, lambda: self.show_notification(f'Ошибка отправки: {str(e)}'))
                        threading.Thread(target=self.reconnect).start()
                        return
                if total_sent == message_len:
                    if message.startswith('IMG:'):
                        print(f'Изображение успешно отправлено: {total_sent}/{message_len} байт')
                    timestamp = time.strftime('%H:%M:%S')
                    formatted_message = f'[{timestamp}] {self.nickname}: {message}'
                    if not message.startswith('IMG:'):
                        message_content = formatted_message
                        if formatted_message.startswith('[') and '] ' in formatted_message:
                            message_content = formatted_message.split('] ', 1)[1]
                        local_hash = hashlib.md5(message_content.encode('utf-8')).hexdigest()
                        self.pending_local_messages.add(local_hash)
                        if len(self.pending_local_messages) > self.max_pending_messages:
                            to_remove = list(self.pending_local_messages)[:100]
                            for msg_hash in to_remove:
                                self.pending_local_messages.discard(msg_hash)
                        self.root.after(0, lambda msg=formatted_message: self.display_message(msg, is_new=True, skip_local_dedup=True))
                    else:
                        print(f'Изображение отправлено, ожидаем ответ от сервера...')
                else:
                    print(f'Ошибка: отправлено только {total_sent}/{message_len} байт')
                    self.root.after(0, lambda: self.show_notification('Не удалось отправить сообщение полностью'))
                    self.unsent_messages.append(message)
            except Exception as e:
                print(f'Ошибка в _send_message_thread: {e}')
                self.unsent_messages.append(message)
                self.root.after(0, lambda: self.show_notification(f'Ошибка отправки сообщения'))
                threading.Thread(target=self.reconnect).start()

    def receive_messages(self):
        try:
            buffer = ''
            MAX_BUFFER_SIZE = 10 * 1024 * 1024
            while True:
                try:
                    data = self.client_socket.recv(65536).decode('utf-8')
                except (socket.error, OSError, ConnectionResetError, ConnectionAbortedError, ConnectionError) as e:
                    self.root.after(0, lambda: self.update_connection_status(False))
                    self.connected = False
                    self.unsent_messages.clear()
                    threading.Thread(target=self.reconnect, daemon=True).start()
                    return
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    self.root.after(0, lambda: self.update_connection_status(False))
                    self.connected = False
                    threading.Thread(target=self.reconnect, daemon=True).start()
                    return
                if not data:
                    self.root.after(0, lambda: self.update_connection_status(False))
                    self.connected = False
                    threading.Thread(target=self.reconnect, daemon=True).start()
                    return
                if len(buffer) + len(data) > MAX_BUFFER_SIZE:
                    buffer = ''
                    continue
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    if not line:
                        continue
                    if line == 'ERROR:BANNED':
                        self.root.after(0, self.show_ban_frame)
                        return
                    elif line == 'KICKED':
                        self.root.after(0, self.disconnect_from_server)
                        return
                    elif line == 'SUCCESS:NICKNAME_CHANGED':
                        self.root.after(0, lambda: self.show_notification('Никнейм успешно изменен'))
                        continue
                    elif line == 'ERROR:NICKNAME_TAKEN':
                        self.root.after(0, lambda: ErrorFrame(self.root, 'Этот никнейм уже занят', False))
                        continue
                    elif line == 'ERROR:NICKNAME_INVALID':
                        self.root.after(0, lambda: ErrorFrame(self.root, 'Некорректный никнейм', False))
                        continue
                    elif line == 'SUCCESS:PASSWORD_CHANGED':
                        if hasattr(self, 'settings_window') and self.settings_window.winfo_exists():
                            self.root.after(0, lambda: self.show_notification('Пароль успешно изменен'))
                        continue
                    elif line == 'ERROR:WRONG_PASSWORD':
                        self.root.after(0, lambda: ErrorFrame(self.root, 'Неверный старый пароль', False))
                        continue
                    elif line == 'ERROR:INVALID_FORMAT':
                        self.root.after(0, lambda: ErrorFrame(self.root, 'Неверный формат данных', False))
                        continue
                    elif line == 'ERROR:LENGTH':
                        self.root.after(0, lambda: self.show_notification('Сообщение слишком длинное! Максимум 300 символов'))
                        continue
                    elif line == 'ERROR:IMAGE_TOO_LARGE':
                        self.root.after(0, lambda: ErrorFrame(self.root, 'Изображение слишком большое (максимум 1 МБ)', False))
                        continue
                    elif line == 'ERROR:IMAGE_PROCESSING_FAILED':
                        self.root.after(0, lambda: ErrorFrame(self.root, 'Ошибка обработки изображения на сервере', False))
                        continue
                    elif line.startswith('ERROR:COOLDOWN:'):
                        continue
                    elif line.startswith('TYPING_USERS:'):
                        users_str = line[len('TYPING_USERS:'):].strip()
                        typing_users = [u.strip() for u in users_str.split(',') if u.strip()]
                        self.root.after(0, lambda u=typing_users: self._update_typing_users(u))
                        continue
                    elif line.startswith('USERS:'):
                        users_str = line[6:].strip()
                        users = []
                        for user in users_str.split(','):
                            user = user.strip()
                            if user and (not user.startswith(('SUCCESS:', 'ERROR:', 'HISTORY:', 'CCT:'))):
                                if '[' in user:
                                    user = user.split('[')[0].strip()
                                if 'изменил никнейм на' in user:
                                    user = user.split('изменил никнейм на')[0].strip()
                                if user and (not any((char in user for char in [':', ']', '[', 'изменил']))):
                                    self.users_online_status[user] = True
                                    users.append(user)
                        self.root.after(0, lambda u=users: self.update_users_list(u))
                        continue
                    elif line.startswith('HISTORY:'):
                        if not self.is_loading_history:
                            self.is_loading_history = True
                            self.history_buffer = []
                            self.history_display_index = 0
                            self.root.after(0, self._start_history_loading)
                        if self.history_timeout_id is not None:
                            try:
                                self.root.after_cancel(self.history_timeout_id)
                            except:
                                pass
                            self.history_timeout_id = None
                        history_content = line[8:]
                        history_messages = []
                        if history_content.strip():
                            history_messages = [h.strip() for h in history_content.split('\n') if h.strip()]
                        for msg in history_messages:
                            if msg and (not msg.startswith(('USERS:', 'users:', 'ERROR:', 'KICKED'))):
                                if 'USERS:' in msg:
                                    msg = msg.split('USERS:')[0].strip()
                                if msg:
                                    self.history_buffer.append(msg)
                        self.history_timeout_id = self.root.after(2200, self._display_history_smoothly)
                        continue
                    elif line == 'HISTORY_END':
                        self.is_loading_history = False
                        if self.history_timeout_id is not None:
                            try:
                                self.root.after_cancel(self.history_timeout_id)
                            except Exception:
                                pass
                            self.history_timeout_id = None
                        self.root.after(0, self._display_history_smoothly)
                        continue
                    else:
                        if self.is_loading_history:
                            if not line.startswith(('USERS:', 'ERROR:', 'KICKED', 'CCT:')):
                                if line and (not line.startswith(('USERS:', 'users:'))):
                                    if 'USERS:' in line:
                                        line = line.split('USERS:')[0].strip()
                                    if line:
                                        self.history_buffer.append(line)
                                    if self.history_timeout_id is not None:
                                        try:
                                            self.root.after_cancel(self.history_timeout_id)
                                        except:
                                            pass
                                    self.history_timeout_id = self.root.after(2200, self._display_history_smoothly)
                            continue
                        if 'USERS:' in line:
                            line = line.split('USERS:')[0].strip()
                        if line:
                            if 'изменил никнейм на' in line:
                                try:
                                    if '] ' in line:
                                        message_part = line.split('] ', 1)[1]
                                        if 'изменил никнейм на' in message_part:
                                            parts = message_part.split('изменил никнейм на')
                                            if len(parts) == 2:
                                                old_nick = parts[0].strip()
                                                new_nickname = parts[1].strip()
                                                for key in list(self.nickname_history.keys()):
                                                    if self.nickname_history[key] == old_nick:
                                                        self.nickname_history[key] = new_nickname
                                                self.nickname_history[new_nickname] = new_nickname
                                                if old_nick == self.nickname:
                                                    self.root.after(0, lambda n=new_nickname: self._update_nickname(n))
                                                self.root.after(0, lambda m=line: self._display_system_message(m))
                                                continue
                                except Exception as e:
                                    pass
                            if line.startswith('[') and '] ' in line:
                                timestamp_end = line.find('] ') + 2
                                message_content = line[timestamp_end:]
                                if ': ' in message_content:
                                    candidate_username = message_content.split(': ', 1)[0].strip()
                                    if candidate_username and candidate_username in self.typing_users:
                                        new_typing = [u for u in self.typing_users if u != candidate_username]
                                        self.root.after(0, lambda u=new_typing: self._update_typing_users(u))
                            self.display_message(line)
        except Exception as e:
            self.is_loading_history = False
            self.history_buffer = []
            self.root.after(0, self.disconnect_from_server)

    def keep_alive(self):
        while True:
            time.sleep(30)
            if self.connected:
                try:
                    self.client_socket.send(b'')
                except Exception:
                    self.connected = False
                    threading.Thread(target=self.reconnect).start()

    def clear_messages(self):
        for widget in self.message_widgets:
            widget.destroy()
        self.message_widgets.clear()

    def _on_message_key(self, event):
        if event.char == '@':
            self._show_mention_list()
        elif event.keysym == 'Escape':
            self._hide_mention_list()

    def _handle_keypress_for_paste(self, event):
        if event.state & 4:
            try:
                if event.keysym in ['м', 'М'] or (hasattr(event, 'char') and event.char in ['м', 'М']):
                    pil_img = self._check_clipboard_for_image()
                    if pil_img is not None:
                        self.root.after(0, lambda: self.show_notification('Отправка изображения из буфера обмена...'))
                        self._send_image_from_clipboard(pil_img)
                        return 'break'
                    self._handle_paste(event)
                    return 'break'
            except:
                pass
        return None

    def _check_clipboard_for_image(self):
        try:
            pil_img = ImageGrab.grabclipboard()
            print(f'grabclipboard вернул: {type(pil_img)}')
            if pil_img is not None and isinstance(pil_img, Image.Image):
                try:
                    size = pil_img.size
                    print(f'Размер изображения: {size}')
                    if size and isinstance(size, tuple) and (len(size) == 2) and (size[0] > 0) and (size[1] > 0):
                        return pil_img
                    else:
                        print(f'Некорректный размер: {size}')
                except Exception as e:
                    print(f'Ошибка при получении размера: {e}')
                    pass
            else:
                print(f'В буфере обмена не изображение или None: {type(pil_img)}')
        except Exception as e:
            print(f'Ошибка при проверке буфера обмена: {e}')
            import traceback
            traceback.print_exc()
        return None

    def _handle_paste_event(self, event=None):
        print('!!! _handle_paste_event ВЫЗВАН !!!')
        try:
            focused_widget = self.root.focus_get()
            print(f'Фокус на виджете: {focused_widget}, message_entry: {self.message_entry}')
            if focused_widget != self.message_entry:
                print('Фокус не на поле ввода, выходим')
                return None
        except Exception as e:
            print(f'Ошибка при проверке фокуса: {e}')
            pass
        print('Проверяю буфер обмена на наличие изображения...')
        pil_img = self._check_clipboard_for_image()
        if pil_img is not None:
            print(f'Изображение найдено! Размер: {pil_img.size}')
            self.root.after(0, lambda: self.show_notification('Отправка изображения из буфера обмена...'))
            self._send_image_from_clipboard(pil_img)
            return 'break'
        else:
            print('В буфере обмена нет изображения, вставляю текст')
        self._handle_paste(event)
        return 'break'

    def _handle_paste(self, event=None):
        try:
            clipboard_text = self.root.clipboard_get()
            if clipboard_text:
                try:
                    cursor_pos = self.message_entry.index('insert')
                except:
                    cursor_pos = len(self.message_entry.get())
                current_text = self.message_entry.get()
                new_text = current_text[:cursor_pos] + clipboard_text + current_text[cursor_pos:]
                self.message_entry.delete(0, 'end')
                self.message_entry.insert(0, new_text)
                try:
                    self.message_entry.icursor(cursor_pos + len(clipboard_text))
                except:
                    pass
                self.root.after(10, self._on_message_typing)
        except Exception as e:
            try:
                self.message_entry.event_generate('<<Paste>>')
            except:
                pass
        return 'break'

    def _on_message_typing(self, event=None):
        try:
            content = self.message_entry.get()
        except Exception:
            return
        now = time.time()
        if '@' in content:
            self._check_mentions(content)
        else:
            self._hide_mention_list()
        if content and (not getattr(self, 'is_typing', False)):
            self.is_typing = True
            self.last_typing_time = now
            self._send_typing_state(True)
            self._schedule_typing_timeout()
        elif content:
            self.last_typing_time = now
            self._schedule_typing_timeout()
        elif getattr(self, 'is_typing', False):
            self.is_typing = False
            self._send_typing_state(False)

    def _check_mentions(self, content):
        if getattr(self, 'mention_selection_blocked', False):
            return
        last_at = content.rfind('@')
        if last_at != -1:
            after_at = content[last_at + 1:]
            import re
            match = re.match('^(\\w+)(\\s|$)', after_at)
            if match:
                username_part = match.group(1)
                if hasattr(self, 'current_users') and username_part in self.current_users:
                    self._hide_mention_list()
                    return
            if ' ' in after_at:
                if len(after_at.strip()) == 0 or after_at.strip() == ' ':
                    self._show_mention_list()
                else:
                    text_before_space = after_at.split(' ')[0]
                    if hasattr(self, 'current_users') and text_before_space in self.current_users:
                        self._hide_mention_list()
                    elif text_before_space:
                        self._filter_mention_list(text_before_space)
                    else:
                        self._show_mention_list()
            elif len(after_at) == 0:
                self._show_mention_list()
            else:
                self._filter_mention_list(after_at)
        else:
            self._hide_mention_list()

    def _show_mention_list(self):
        if self.mention_list_frame:
            self.mention_list_frame.destroy()
        self.mention_list_frame = ctk.CTkFrame(self.root, fg_color='#1E1E1E', corner_radius=12, width=180, height=120, border_width=1, border_color='#3A3A3A')
        window_height = self.root.winfo_height()
        input_y = int(window_height * 0.89)
        mention_y = input_y - 140 - 120
        if mention_y < 10:
            mention_y = 10
        self.mention_list_frame.place(relx=0.06, y=mention_y)
        self.mention_list_frame.lift()
        self.mention_list_frame.update()
        title_label = ctk.CTkLabel(self.mention_list_frame, text='Упоминания', font=('Segoe UI', 10, 'bold'), text_color='#FFFFFF', anchor='w')
        title_label.pack(anchor='w', padx=10, pady=(8, 3))
        self.mention_list = ctk.CTkScrollableFrame(self.mention_list_frame, fg_color='transparent')
        self.mention_list.pack(fill='both', expand=True, padx=6, pady=(0, 6))
        if hasattr(self, 'current_users'):
            users_added = False
            for user in self.current_users:
                if user != self.nickname and user.strip():
                    self._add_mention_user(user)
                    users_added = True
            if not users_added:
                no_users_label = ctk.CTkLabel(self.mention_list, text='Нет пользователей', font=('Segoe UI', 10), text_color='#888888')
                no_users_label.pack(pady=10)

    def _add_mention_user(self, username):
        user_btn = ctk.CTkButton(self.mention_list, text=username, font=('Segoe UI', 10), fg_color='#2A2A2A', hover_color='#3A7ECC', height=28, anchor='w', corner_radius=6, command=lambda u=username: self._select_mention_user(u))
        user_btn.pack(fill='x', padx=2, pady=1)

    def _filter_mention_list(self, filter_text):
        if not self.mention_list:
            self._show_mention_list()
            return
        if self.mention_list_frame:
            window_height = self.root.winfo_height()
            input_y = int(window_height * 0.89)
            mention_y = input_y - 130 - 120
            if mention_y < 10:
                mention_y = 10
            self.mention_list_frame.place(relx=0.06, y=mention_y)
            self.mention_list_frame.lift()
            self.mention_list_frame.update()
        for widget in self.mention_list.winfo_children():
            widget.destroy()
        filter_lower = filter_text.lower()
        users_added = False
        if hasattr(self, 'current_users'):
            for user in self.current_users:
                if user != self.nickname and user.strip() and (filter_lower in user.lower()):
                    self._add_mention_user(user)
                    users_added = True
        if not users_added:
            no_users_label = ctk.CTkLabel(self.mention_list, text='Не найдено', font=('Segoe UI', 10), text_color='#888888')
            no_users_label.pack(pady=10)

    def _select_mention_user(self, username):
        try:
            content = self.message_entry.get()
            last_at = content.rfind('@')
            if last_at != -1:
                before_at = content[:last_at + 1]
                after_at = content[last_at + 1:]
                if ' ' in after_at:
                    space_pos = after_at.find(' ')
                    new_content = before_at + username + ' ' + after_at[space_pos + 1:]
                else:
                    new_content = before_at + username + ' '
                self.message_entry.delete(0, 'end')
                self.message_entry.insert(0, new_content)
                self.mentioned_users.add(username)
                self.message_entry.icursor('end')
        except Exception as e:
            print(f'Ошибка при выборе пользователя: {e}')
        self._hide_mention_list()
        self.mention_selection_blocked = True
        self.root.after(300, lambda: setattr(self, 'mention_selection_blocked', False))

    def _hide_mention_list(self):
        if hasattr(self, 'mention_list_frame') and self.mention_list_frame:
            self.mention_list_frame.destroy()
            self.mention_list_frame = None
            self.mention_list = None

    def _check_message_mentions(self, text, message_container):
        try:
            import re
            mentions = re.findall('@(\\w+)', text)
            if mentions and hasattr(self, 'nickname') and self.nickname:
                if self.nickname in mentions:
                    self.root.after(100, lambda: self._highlight_mentioned_message(message_container))
        except Exception as e:
            print(f'Ошибка в _check_message_mentions: {e}')

    def _show_mention_notification(self, message_text):
        pass

    def _highlight_mentioned_message(self, message_container):
        if not message_container or not message_container.winfo_exists():
            print('DEBUG: message_container не существует')
            return
        msg_frame = None
        for widget in message_container.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkFrame):
                        try:
                            fg_color = child.cget('fg_color')
                            if fg_color in ['#3A7ECC', '#2B2B2B']:
                                msg_frame = child
                                break
                        except:
                            continue
                if msg_frame:
                    break
        if not msg_frame:

            def find_msg_frame_recursive(widget):
                if isinstance(widget, ctk.CTkFrame):
                    try:
                        fg_color = widget.cget('fg_color')
                        if fg_color in ['#3A7ECC', '#2B2B2B']:
                            return widget
                    except:
                        pass
                    for child in widget.winfo_children():
                        result = find_msg_frame_recursive(child)
                        if result:
                            return result
                return None
            msg_frame = find_msg_frame_recursive(message_container)
            if not msg_frame:
                return
        try:
            original_color = msg_frame.cget('fg_color')
        except:
            return
        if hasattr(message_container, '_highlighting_in_progress'):
            return
        message_container._highlighting_in_progress = True
        green_color = '#4CAF50'
        steps = 40
        duration_ms = 2000

        def interpolate_color(color1, color2, factor):

            def hex_to_rgb(hex_color):
                hex_color = hex_color.lstrip('#')
                return tuple((int(hex_color[i:i + 2], 16) for i in (0, 2, 4)))

            def rgb_to_hex(rgb):
                return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
            rgb1 = hex_to_rgb(color1)
            rgb2 = hex_to_rgb(color2)
            r = int(rgb1[0] + (rgb2[0] - rgb1[0]) * factor)
            g = int(rgb1[1] + (rgb2[1] - rgb1[1]) * factor)
            b = int(rgb1[2] + (rgb2[2] - rgb1[2]) * factor)
            return rgb_to_hex((r, g, b))

        def animate(step=0):
            if not msg_frame.winfo_exists():
                message_container._highlighting_in_progress = False
                return
            try:
                if step < steps:
                    factor = step / steps
                    current_color = interpolate_color(original_color, green_color, factor)
                    msg_frame.configure(fg_color=current_color)
                    delay = duration_ms // steps
                    message_container.mention_highlight_id = self.root.after(delay, lambda s=step + 1: animate(s))
                else:
                    msg_frame.configure(fg_color=original_color)
                    message_container._highlighting_in_progress = False
            except Exception as e:
                message_container._highlighting_in_progress = False
        animate(0)

    def _restore_message_colors(self, msg_frame, original_color):
        if not msg_frame or not msg_frame.winfo_exists():
            return
        try:
            msg_frame.configure(fg_color=original_color)
        except:
            pass

    def _schedule_typing_timeout(self):
        if hasattr(self, 'typing_timeout_id') and self.typing_timeout_id is not None:
            try:
                self.root.after_cancel(self.typing_timeout_id)
            except Exception:
                pass
        self.typing_timeout_id = self.root.after(2000, self._typing_timeout_check)

    def _typing_timeout_check(self):
        if getattr(self, 'is_typing', False):
            now = time.time()
            if now - getattr(self, 'last_typing_time', 0) >= 2:
                self.is_typing = False
                self._send_typing_state(False)
                self.typing_timeout_id = None
            else:
                self._schedule_typing_timeout()

    def _send_typing_state(self, is_typing: bool):
        if not self.connected:
            return
        threading.Thread(target=self._send_typing_state_thread, args=(is_typing,), daemon=True).start()

    def _send_typing_state_thread(self, is_typing: bool):
        try:
            state = '1' if is_typing else '0'
            with self.send_lock:
                self.client_socket.send(f'TYPING:{state}\n'.encode('utf-8'))
        except Exception:
            pass

    def _load_image_async(self, msg_frame, placeholder_label, img_bytes, img_filename):
        try:
            pil_img = Image.open(io.BytesIO(img_bytes))
            pil_img.thumbnail((220, 220), Image.LANCZOS)

            def add_corners(img, radius=18):
                mask = Image.new('L', img.size, 0)
                draw = ImageDraw.Draw(mask)
                draw.rounded_rectangle([(0, 0), img.size], radius=radius, fill=255)
                output = Image.new('RGBA', img.size, (0, 0, 0, 0))
                if img.mode == 'RGBA':
                    output.paste(img, (0, 0), mask)
                else:
                    img_rgba = img.convert('RGBA')
                    output.paste(img_rgba, (0, 0), mask)
                return output
            pil_img = add_corners(pil_img, radius=18)
            img_width, img_height = pil_img.size
            preview_img = CTkImage(light_image=None, dark_image=pil_img, size=(img_width, img_height))
            self.image_cache.append(preview_img)
            if len(self.image_cache) > 50:
                self.image_cache.pop(0)

            def update_gui():
                try:
                    if placeholder_label.winfo_exists():
                        placeholder_label.destroy()
                    img_container = ctk.CTkFrame(msg_frame, fg_color='transparent', corner_radius=18)
                    img_container.pack(padx=4, pady=4, anchor='w')
                    img_label = ctk.CTkLabel(img_container, text='', image=preview_img, fg_color='transparent')
                    img_label.pack()
                    img_label.bind('<Button-1>', lambda e, data=img_bytes, name=img_filename: self.open_image_viewer(data, name))
                except Exception:
                    pass
            self.root.after(0, update_gui)
        except Exception:

            def show_error():
                try:
                    if placeholder_label.winfo_exists():
                        placeholder_label.configure(text='[Не удалось отобразить изображение]', text_color='#FF6666')
                except Exception:
                    pass
            self.root.after(0, show_error)

    def _start_history_loading(self):
        self.clear_messages()

    def _update_typing_users(self, typing_users):
        self.typing_users = set(typing_users)
        if hasattr(self, 'current_users') and self.current_users:
            self.update_users_list(self.current_users)

    def _display_history_smoothly(self):
        try:
            if not self.history_buffer:
                self.is_loading_history = False
                return
            for msg in self.history_buffer:
                self.display_message(msg, is_new=False)
            self.message_display.update_idletasks()
            self.is_loading_history = False
            self.history_buffer = []
            self.history_display_index = 0
            self.root.after(100, self._scroll_to_bottom)
        except Exception:
            self.is_loading_history = False
            self.history_buffer = []
            self.history_display_index = 0

    def _scroll_to_bottom(self):
        try:
            canvas = self.message_display._parent_canvas
            canvas.yview_moveto(1.0)
        except:
            pass

    def _process_message_queue(self):
        scroll_needed = False
        while True:
            with self.message_queue_lock:
                if not self.message_queue:
                    self.gui_update_pending = False
                    break
                message, is_new, skip_local_dedup = self.message_queue.popleft()
            try:
                self._display_message_direct(message, is_new, skip_local_dedup)
                scroll_needed = True
            except Exception:
                continue
        if scroll_needed and self.settings.get('auto_scroll', True):
            self.root.after(10, self._scroll_to_bottom)

    def _display_message_direct(self, message, is_new=True, skip_local_dedup=False):
        if 'USERS:' in message:
            message = message.split('USERS:')[0].strip()
        if not message or not message.strip():
            return
        self.display_message_internal(message, is_new, skip_local_dedup)

    def display_message(self, message, is_new=True, skip_local_dedup=False):
        with self.message_queue_lock:
            self.message_queue.append((message, is_new, skip_local_dedup))
            if not self.gui_update_pending:
                self.gui_update_pending = True
                self.root.after(0, self._process_message_queue)

    def display_message_internal(self, message, is_new=True, skip_local_dedup=False):
        if 'USERS:' in message:
            message = message.split('USERS:')[0].strip()
        if not message or not message.strip():
            return
        message_hash = None
        if not skip_local_dedup:
            message_content = message
            if message.startswith('[') and '] ' in message:
                message_content = message.split('] ', 1)[1] if '] ' in message else message
            message_hash = hashlib.md5(message_content.encode('utf-8')).hexdigest()
        if is_new and (not self.settings['show_join_leave']) and ('присоединился к чату' in message or 'покинул чат' in message):
            return
        timestamp = None
        username = None
        text = message
        is_system = False
        reply_to_hash = None
        if message.startswith('[') and '] ' in message:
            timestamp_end = message.find('] ') + 2
            timestamp_str = message[1:timestamp_end - 2]
            remaining = message[timestamp_end:].strip()
            if not self.settings['show_seconds'] and timestamp_str.count(':') == 2:
                time_parts = timestamp_str.split(':')
                timestamp_str = f'{time_parts[0]}:{time_parts[1]}'
            timestamp = timestamp_str
            if 'присоединился к чату' in remaining or 'покинул чат' in remaining or 'изменил никнейм на' in remaining:
                is_system = True
                text = remaining
            elif ': ' in remaining:
                colon_pos = remaining.find(': ')
                candidate_username = remaining[:colon_pos].strip()
                candidate_text = remaining[colon_pos + 2:].strip()
                if candidate_text.startswith('REPLY:'):
                    reply_parts = candidate_text.split(':', 2)
                    if len(reply_parts) == 3:
                        reply_to_hash = reply_parts[1]
                        candidate_text = reply_parts[2]
                        print(f'DEBUG: Найден ответ, хеш: {reply_to_hash[:8]}..., текст: {candidate_text[:20]}...')
                if candidate_text and candidate_username and (len(candidate_username) < 30) and (' ' not in candidate_username):
                    username = candidate_username
                    text = candidate_text
                    if not text:
                        return
                else:
                    username = None
                    text = remaining.strip()
                    if not text:
                        return
            else:
                text = remaining.strip()
                if not text:
                    return
        elif ': ' in message:
            colon_pos = message.find(': ')
            potential_username = message[:colon_pos].strip()
            potential_text = message[colon_pos + 2:].strip()
            if potential_text and len(potential_username) < 30 and (' ' not in potential_username):
                username = potential_username
                text = potential_text
        elif not is_system:
            if not ('присоединился' in message or 'покинул' in message):
                pass
        if not skip_local_dedup and username == self.nickname and message_hash:
            if message_hash in self.pending_local_messages:
                self.pending_local_messages.discard(message_hash)
                return
        is_image_message = False
        img_bytes = None
        img_filename = None
        if text and isinstance(text, str) and text.startswith('IMG:'):
            parts = text.split(':', 2)
            if len(parts) == 3:
                _, img_filename, img_b64 = parts
                try:
                    img_bytes = base64.b64decode(img_b64)
                    is_image_message = True
                except Exception:
                    is_image_message = False
        message_container = ctk.CTkFrame(self.message_display, fg_color='transparent')
        message_container.pack(fill='x', padx=5, pady=2)
        original_text_for_hash = text
        if reply_to_hash is None and text and text.startswith('REPLY:'):
            reply_parts = text.split(':', 2)
            if len(reply_parts) == 3:
                reply_to_hash = reply_parts[1]
                original_text_for_hash = reply_parts[2]
                text = original_text_for_hash
                print(f"DEBUG: Извлечен reply_to_hash из текста: {(reply_to_hash[:8] if reply_to_hash else 'None')}...")
        print(f"DEBUG: reply_to_hash перед отображением: {(reply_to_hash[:8] if reply_to_hash else 'None')}...")
        message_hash = hashlib.md5(f'{username}:{original_text_for_hash}'.encode('utf-8')).hexdigest() if username and original_text_for_hash else None
        if message_hash and username and text and (not is_system):
            self.messages_by_hash[message_hash] = {'username': username, 'text': text, 'timestamp': timestamp}
            print(f'DEBUG: Сохранено сообщение в словарь, хеш: {message_hash[:8]}..., username: {username}, text: {text[:30]}...')
        if is_system:
            system_frame = ctk.CTkFrame(message_container, fg_color='#2A2A2A', corner_radius=12, height=30)
            system_frame.pack(anchor='center', padx=10, pady=2)
            system_label = ctk.CTkLabel(system_frame, text=text, font=('Arial', 11), text_color='#888888', wraplength=400)
            system_label.pack(padx=10, pady=5)
            self.message_widgets.append(message_container)
        else:
            if not username and text:
                username = None
                is_my_message = False
            elif username:
                if username == self.nickname:
                    is_my_message = True
                else:
                    current_nick_for_username = self.nickname_history.get(username, username)
                    is_my_message = current_nick_for_username == self.nickname
            else:
                is_my_message = False
            if is_my_message:
                right_frame = ctk.CTkFrame(message_container, fg_color='transparent')
                right_frame.pack(side='right', anchor='e', padx=(10, 5), pady=2)
                msg_frame = ctk.CTkFrame(right_frame, fg_color='#3A7ECC', corner_radius=18, width=300, border_width=0)
                msg_frame.pack(anchor='e')
                if message_hash and (not is_system):
                    msg_frame.bind('<Button-1>', lambda e, h=message_hash, u=username, t=text, ts=timestamp: self._select_message_for_reply(h, u, t, ts))
                    for widget in msg_frame.winfo_children():
                        widget.bind('<Button-1>', lambda e, h=message_hash, u=username, t=text, ts=timestamp: self._select_message_for_reply(h, u, t, ts))
                if reply_to_hash:
                    reply_container = ctk.CTkFrame(msg_frame, fg_color='transparent')
                    reply_container.pack(fill='x', padx=8, pady=(4, 0))
                    reply_line = ctk.CTkFrame(reply_container, fg_color='#5FC9F8', width=3, height=20, corner_radius=0)
                    reply_line.pack(side='left', padx=(0, 6), pady=0)
                    reply_text_frame = ctk.CTkFrame(reply_container, fg_color='transparent')
                    reply_text_frame.pack(side='left', fill='x', expand=True)
                    original_msg = self.messages_by_hash.get(reply_to_hash, None)
                    if original_msg:
                        reply_text_preview = original_msg['text'][:30] + '...' if len(original_msg['text']) > 30 else original_msg['text']
                        reply_full_text = f"{original_msg['username']}: {reply_text_preview}"
                        reply_text_label = ctk.CTkLabel(reply_text_frame, text=reply_full_text, font=('Segoe UI', 11), text_color='#FFFFFF', anchor='w', wraplength=180, justify='left')
                        reply_text_label.pack(anchor='w', pady=0)
                    else:
                        reply_info_label = ctk.CTkLabel(reply_text_frame, text='Ответ на сообщение', font=('Segoe UI', 10), text_color='#B0B0B0', anchor='w')
                        reply_info_label.pack(anchor='w')
                if is_image_message and img_bytes:
                    placeholder_label = ctk.CTkLabel(msg_frame, text='Загрузка изображения...', font=('Arial', 11), text_color='#CCCCCC', wraplength=280, justify='left', anchor='w')
                    placeholder_label.pack(padx=10, pady=5, anchor='w')
                    threading.Thread(target=self._load_image_async, args=(msg_frame, placeholder_label, img_bytes, img_filename), daemon=True).start()
                else:
                    is_long_message = len(text) > 30 or '\n' in text
                    if is_long_message:
                        text_time_frame = ctk.CTkFrame(msg_frame, fg_color='transparent')
                        text_time_frame.pack(fill='x', padx=12, pady=(8, 6))
                        text_container = ctk.CTkFrame(text_time_frame, fg_color='transparent')
                        text_container.pack(side='left', fill='both', expand=True)
                        text_label = ctk.CTkLabel(text_container, text=text, font=('Segoe UI', 13), text_color='#FFFFFF', wraplength=220, justify='left', anchor='nw')
                        text_label.pack(anchor='nw')
                        if timestamp:
                            display_time = timestamp
                            if display_time.count(':') == 2:
                                time_parts = display_time.split(':')
                                display_time = f'{time_parts[0]}:{time_parts[1]}'
                            time_label = ctk.CTkLabel(text_time_frame, text=display_time, font=('Segoe UI', 10), text_color='#B0D8FF')
                            time_label.pack(side='right', anchor='s', padx=(8, 0))
                    else:
                        text_time_frame = ctk.CTkFrame(msg_frame, fg_color='transparent')
                        top_padding = 2 if reply_to_hash else 8
                        text_time_frame.pack(fill='x', padx=12, pady=(top_padding, 6))
                        text_label = ctk.CTkLabel(text_time_frame, text=text, font=('Segoe UI', 13), text_color='#FFFFFF', wraplength=220, justify='left', anchor='nw')
                        text_label.pack(side='left', anchor='nw', pady=(6, 0))
                        if timestamp:
                            display_time = timestamp
                            if display_time.count(':') == 2:
                                time_parts = display_time.split(':')
                                display_time = f'{time_parts[0]}:{time_parts[1]}'
                            time_label = ctk.CTkLabel(text_time_frame, text=display_time, font=('Segoe UI', 10), text_color='#B0D8FF')
                            time_label.pack(side='right', padx=(8, 0))
                if text and (not is_system) and is_new:
                    try:
                        self.root.after(50, lambda: self._check_message_mentions(text, message_container))
                    except Exception as e:
                        print(f'Ошибка при проверке упоминаний: {e}')
                self.message_widgets.append(message_container)
            else:
                left_frame = ctk.CTkFrame(message_container, fg_color='transparent')
                left_frame.pack(side='left', anchor='w', padx=(5, 10), pady=2)
                if username:
                    name_label = ctk.CTkLabel(left_frame, text=username, font=('Segoe UI Bold', 11), text_color='#A0A0A0', anchor='w')
                    name_label.pack(anchor='w', padx=5, pady=(0, 2))
                msg_frame = ctk.CTkFrame(left_frame, fg_color='#2B2B2B', corner_radius=18, width=300, border_width=0)
                msg_frame.pack(anchor='w')
                if message_hash and (not is_system):
                    msg_frame.bind('<Button-1>', lambda e, h=message_hash, u=username, t=text, ts=timestamp: self._select_message_for_reply(h, u, t, ts))
                    for widget in msg_frame.winfo_children():
                        widget.bind('<Button-1>', lambda e, h=message_hash, u=username, t=text, ts=timestamp: self._select_message_for_reply(h, u, t, ts))
                if reply_to_hash:
                    reply_container = ctk.CTkFrame(msg_frame, fg_color='transparent')
                    reply_container.pack(fill='x', padx=8, pady=(4, 0))
                    reply_line = ctk.CTkFrame(reply_container, fg_color='#5FC9F8', width=3, height=20, corner_radius=0)
                    reply_line.pack(side='left', padx=(0, 6), pady=0)
                    reply_text_frame = ctk.CTkFrame(reply_container, fg_color='transparent')
                    reply_text_frame.pack(side='left', fill='x', expand=True)
                    original_msg = self.messages_by_hash.get(reply_to_hash, None)
                    if original_msg:
                        reply_text_preview = original_msg['text'][:30] + '...' if len(original_msg['text']) > 30 else original_msg['text']
                        reply_full_text = f"{original_msg['username']}: {reply_text_preview}"
                        reply_text_label = ctk.CTkLabel(reply_text_frame, text=reply_full_text, font=('Segoe UI', 11), text_color='#FFFFFF', anchor='w', wraplength=180, justify='left')
                        reply_text_label.pack(anchor='w', pady=0)
                    else:
                        reply_info_label = ctk.CTkLabel(reply_text_frame, text='Ответ на сообщение', font=('Segoe UI', 10), text_color='#B0B0B0', anchor='w')
                        reply_info_label.pack(anchor='w')
                if is_image_message and img_bytes:
                    placeholder_label = ctk.CTkLabel(msg_frame, text='Загрузка изображения...', font=('Arial', 11), text_color='#CCCCCC', wraplength=280, justify='left', anchor='w')
                    placeholder_label.pack(padx=10, pady=5, anchor='w')
                    threading.Thread(target=self._load_image_async, args=(msg_frame, placeholder_label, img_bytes, img_filename), daemon=True).start()
                else:
                    is_long_message = len(text) > 30 or '\n' in text
                    if is_long_message:
                        text_time_frame = ctk.CTkFrame(msg_frame, fg_color='transparent')
                        text_time_frame.pack(fill='x', padx=12, pady=(8, 6))
                        text_container = ctk.CTkFrame(text_time_frame, fg_color='transparent')
                        text_container.pack(side='left', fill='both', expand=True)
                        text_label = ctk.CTkLabel(text_container, text=text, font=('Segoe UI', 13), text_color='#FFFFFF', wraplength=220, justify='left', anchor='nw')
                        text_label.pack(anchor='nw')
                        if timestamp:
                            display_time = timestamp
                            if display_time.count(':') == 2:
                                time_parts = display_time.split(':')
                                display_time = f'{time_parts[0]}:{time_parts[1]}'
                            time_label = ctk.CTkLabel(text_time_frame, text=display_time, font=('Segoe UI', 10), text_color='#999999')
                            time_label.pack(side='right', anchor='s', padx=(8, 0))
                    else:
                        text_time_frame = ctk.CTkFrame(msg_frame, fg_color='transparent')
                        top_padding = 2 if reply_to_hash else 8
                        text_time_frame.pack(fill='x', padx=12, pady=(top_padding, 6))
                        text_label = ctk.CTkLabel(text_time_frame, text=text, font=('Segoe UI', 13), text_color='#FFFFFF', wraplength=220, justify='left', anchor='nw')
                        text_label.pack(side='left', anchor='nw', pady=(6, 0))
                        if timestamp:
                            display_time = timestamp
                            if display_time.count(':') == 2:
                                time_parts = display_time.split(':')
                                display_time = f'{time_parts[0]}:{time_parts[1]}'
                            time_label = ctk.CTkLabel(text_time_frame, text=display_time, font=('Segoe UI', 10), text_color='#999999')
                            time_label.pack(side='right', padx=(8, 0))
                if text and (not is_system) and is_new:
                    try:
                        self.root.after(50, lambda: self._check_message_mentions(text, message_container))
                    except Exception as e:
                        print(f'Ошибка при проверке упоминаний: {e}')
                self.message_widgets.append(message_container)
        if not self.is_loading_history and self.settings['auto_scroll'] and is_new:

            def scroll_to_bottom():
                try:
                    canvas = self.message_display._parent_canvas
                    canvas.update_idletasks()
                    canvas.yview_moveto(1.0)
                except:
                    pass
            self.root.after(50, scroll_to_bottom)
        if is_new and self.settings['message_sound']:
            pass
        self._store_message_data(message, timestamp, username, text, is_system, is_image_message, img_bytes, img_filename)
        self._limit_visible_widgets()

    def _store_message_data(self, message, timestamp, username, text, is_system, is_image_message, img_bytes, img_filename):
        message_info = {'original_message': message, 'timestamp': timestamp, 'username': username, 'text': text, 'is_system': is_system, 'is_image_message': is_image_message, 'img_bytes': img_bytes, 'img_filename': img_filename}
        self.message_data.append(message_info)

    def _limit_visible_widgets(self):
        if len(self.message_widgets) > self.max_visible_messages:
            widgets_to_remove = len(self.message_widgets) - self.max_visible_messages
            for i in range(widgets_to_remove):
                try:
                    widget = self.message_widgets[i]
                    widget.destroy()
                except:
                    pass
            self.message_widgets = self.message_widgets[widgets_to_remove:]

    def get_message_history(self):
        return self.message_data.copy()

    def _load_message_history_on_scroll(self, direction='up'):
        pass

    def open_image_viewer(self, img_bytes, title=None):
        try:
            pil_img = Image.open(io.BytesIO(img_bytes))
        except Exception:
            self.show_notification('Не удалось открыть изображение')
            return
        viewer = ctk.CTkToplevel(self.root)
        viewer.title(title or 'Просмотр изображения')
        viewer.geometry('800x600')
        try:
            self.root.update_idletasks()
            root_x = self.root.winfo_x()
            root_y = self.root.winfo_y()
            root_w = self.root.winfo_width()
            root_h = self.root.winfo_height()
            win_w, win_h = (800, 600)
            x = root_x + (root_w - win_w) // 2
            y = root_y + (root_h - win_h) // 2
            viewer.geometry(f'{win_w}x{win_h}+{x}+{y}')
        except Exception:
            pass
        viewer.lift()
        viewer.attributes('-topmost', True)
        viewer.after(500, lambda: viewer.attributes('-topmost', False))
        canvas = tk.Canvas(viewer, bg='#000000', highlightthickness=0)
        canvas.pack(fill='both', expand=True)
        viewer.original_image = pil_img
        viewer.zoom_scale = 1.0
        viewer.canvas = canvas
        viewer.photo_image = None
        viewer.image_id = None

        def redraw_image():
            if viewer.original_image is None:
                return
            try:
                w, h = viewer.original_image.size
                scale = max(0.1, min(5.0, viewer.zoom_scale))
                new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
                resized = viewer.original_image.resize(new_size, Image.LANCZOS)
                viewer.photo_image = ImageTk.PhotoImage(resized, master=canvas)
                canvas.delete('all')
                viewer.image_id = canvas.create_image(canvas.winfo_width() // 2, canvas.winfo_height() // 2, image=viewer.photo_image, anchor='center')
            except Exception:
                pass

        def on_configure(event):
            redraw_image()

        def on_mouse_wheel(event):
            if not event.state & 4:
                return
            delta = event.delta
            if delta > 0:
                viewer.zoom_scale *= 1.1
            else:
                viewer.zoom_scale /= 1.1
            redraw_image()

        def on_button_press(event):
            canvas.scan_mark(event.x, event.y)

        def on_mouse_drag(event):
            canvas.scan_dragto(event.x, event.y, gain=1)
        canvas.bind('<Configure>', on_configure)
        canvas.bind('<ButtonPress-1>', on_button_press)
        canvas.bind('<B1-Motion>', on_mouse_drag)
        canvas.bind('<Control-MouseWheel>', on_mouse_wheel)
        viewer.after(100, redraw_image)

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
                try:
                    self.client_socket.close()
                except:
                    pass
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                self.client_socket.settimeout(10.0)
                self.client_socket.connect((self.ip, self.port))
                self.client_socket.settimeout(None)
                password_hash = hashlib.sha256(self.password.encode('utf-8')).hexdigest()
                local_tz = datetime.now(timezone.utc).astimezone().utcoffset()
                timezone_offset = int(local_tz.total_seconds() / 3600)
                self.client_socket.send(f'{self.isRegister};{self.nickname};{password_hash};{timezone_offset}'.encode('utf-8'))
                initial_response = self.client_socket.recv(1024).decode('utf-8')
                if initial_response == 'ERROR:BANNED':
                    self.root.after(0, self.show_ban_frame)
                    return
                if initial_response in ['ERROR:NICKNAME_TAKEN', 'ERROR:NICKNAME_ONLINE', 'ERROR:WRONG_PASSWORD', 'ERROR:WRONG_OPERATION']:
                    self.root.after(0, lambda: self.show_notification('Ошибка авторизации при переподключении'))
                    return
                if initial_response[:4] != 'CCT:':
                    time.sleep(2)
                    continue
                self.connected = True
                response = initial_response[4:].split(';')
                self.message_cooldown = int(response[0])
                self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
                self.receive_thread.start()
                while self.unsent_messages:
                    unsent_message = self.unsent_messages.pop(0)
                    self._send_message_thread(unsent_message)
                self.update_connection_status(True)
                self.root.after(0, lambda: self.show_notification('Переподключение успешно'))
            except socket.timeout:
                time.sleep(5)
            except (socket.error, OSError, ConnectionError) as e:
                time.sleep(5)
            except Exception as e:
                time.sleep(5)

    def update_connection_status(self, status):
        if hasattr(self, 'connection_status') and self.connection_status.winfo_exists():
            if status:
                self.connection_status.configure(text='● Статус: Онлайн', text_color='#00ff88')
            else:
                self.connection_status.configure(text='○ Статус: Оффлайн', text_color='#ff3333')

    def _display_system_message(self, message):
        if message.startswith('[') and '] ' in message:
            timestamp_end = message.find('] ') + 2
            text = message[timestamp_end:].strip()
        else:
            text = message
        message_container = ctk.CTkFrame(self.message_display, fg_color='transparent')
        message_container.pack(fill='x', padx=5, pady=2)
        system_frame = ctk.CTkFrame(message_container, fg_color='#2A2A2A', corner_radius=12, height=30)
        system_frame.pack(anchor='center', padx=10, pady=2)
        system_frame.pack_propagate(False)
        system_label = ctk.CTkLabel(system_frame, text=text, font=('Arial', 11), text_color='#888888', wraplength=400)
        system_label.pack(padx=10, pady=5)
        self.message_widgets.append(message_container)
        self.message_display.update_idletasks()
        if self.settings['auto_scroll']:

            def scroll_to_bottom():
                try:
                    canvas = self.message_display._parent_canvas
                    canvas.update_idletasks()
                    canvas.yview_moveto(1.0)
                except:
                    pass
            self.root.after(50, scroll_to_bottom)

    def _update_nickname(self, new_nickname):
        old_nickname = self.nickname
        self.nickname = new_nickname
        self.root.title(f'SproutLine - {self.nickname}')
        if hasattr(self, 'nickname_label'):
            self.nickname_label.configure(text=self.nickname)
        self.nickname_history[new_nickname] = new_nickname
        for key in list(self.nickname_history.keys()):
            if self.nickname_history[key] == old_nickname:
                self.nickname_history[key] = new_nickname
        if hasattr(self, 'settings_window') and self.settings_window.winfo_exists():
            try:
                if self.settings_window.winfo_exists():
                    if hasattr(self, 'profile_nickname_label'):
                        try:
                            self.profile_nickname_label.configure(text=self.nickname)
                        except:
                            pass
            except:
                pass

    def update_users_list(self, users):
        self.current_users = [user.strip() for user in users if user.strip()]
        new_users_set = set(self.current_users)
        for user in list(self.users_online_status.keys()):
            if user not in new_users_set:
                self.users_online_status[user] = False
        for card in self.user_cards:
            try:
                card.destroy()
            except:
                pass
        self.user_cards.clear()
        if self.current_users:
            self._create_user_cards_batched(0)
        else:
            self.users_list.update_idletasks()

    def _create_user_cards_batched(self, start_index):
        BATCH_SIZE = 10
        end_index = min(start_index + BATCH_SIZE, len(self.current_users))
        for i in range(start_index, end_index):
            user_name = self.current_users[i]
            if user_name:
                self._create_user_card(user_name)
        if end_index < len(self.current_users):
            self.root.after(1, lambda idx=end_index: self._create_user_cards_batched(idx))
        else:
            self.users_list.update_idletasks()

    def _create_user_card(self, user_name):
        try:
            self.users_online_status[user_name] = True
            user_card = ctk.CTkFrame(self.users_list, fg_color='#2D2D2D', corner_radius=10, height=50, border_width=1, border_color='#3D3D3D')
            user_card.pack(fill='x', padx=2, pady=3)
            user_card.pack_propagate(False)

            def on_enter(e):
                user_card.configure(fg_color='#3A3A3A', border_color='#4A4A4A')

            def on_leave(e):
                user_card.configure(fg_color='#2D2D2D', border_color='#3D3D3D')
            user_card.bind('<Enter>', on_enter)
            user_card.bind('<Leave>', on_leave)
            card_content = ctk.CTkFrame(user_card, fg_color='transparent')
            card_content.pack(fill='both', expand=True, padx=10, pady=8)
            indicator_frame = ctk.CTkFrame(card_content, fg_color='transparent', width=12, height=12)
            indicator_frame.pack(side='left', padx=(0, 10))
            indicator_frame.pack_propagate(False)
            is_online = self.users_online_status.get(user_name, True)
            indicator_color = '#00ff88' if is_online else '#ff3333'
            online_indicator = ctk.CTkFrame(indicator_frame, width=10, height=10, fg_color=indicator_color, corner_radius=5)
            online_indicator.place(relx=0.5, rely=0.5, anchor='center')
            is_typing = hasattr(self, 'typing_users') and user_name in self.typing_users
            user_label = ctk.CTkLabel(card_content, text=user_name, font=('Arial', 12), text_color='#FFFFFF', anchor='w')
            user_label.pack(side='left', fill='x', expand=True)
            if is_typing:
                typing_label = ctk.CTkLabel(card_content, text=' печатает...', font=('Arial', 11), text_color='#888888', anchor='w')
                typing_label.pack(side='left')
            for widget in [card_content, user_label, indicator_frame, online_indicator]:
                widget.bind('<Enter>', on_enter)
                widget.bind('<Leave>', on_leave)
            self.user_cards.append(user_card)
        except Exception:
            pass

    def show_notification(self, text):
        pass

    def clear_notification(self):
        pass

    def show_cooldown_notification(self, text='Подождите'):
        if hasattr(self, 'cooldown_animation_id') and self.cooldown_animation_id:
            self.root.after_cancel(self.cooldown_animation_id)
        self.cooldown_notification.configure(text=text)
        self._animate_cooldown_show()

    def _animate_cooldown_show(self, rely=0.78):
        if rely <= 0.82:
            self.cooldown_container.place(relx=0.4, rely=rely, anchor='center')
            rely += 0.01
            self.cooldown_animation_id = self.root.after(15, lambda: self._animate_cooldown_show(rely))
        else:
            self.cooldown_container.place(relx=0.4, rely=0.82, anchor='center')
            self.cooldown_animation_id = self.root.after(2000, self._animate_cooldown_hide)

    def _animate_cooldown_hide(self, rely=0.82):
        if rely >= 0.78:
            self.cooldown_container.place(relx=0.4, rely=rely, anchor='center')
            rely -= 0.01
            self.cooldown_animation_id = self.root.after(15, lambda: self._animate_cooldown_hide(rely))
        else:
            self.cooldown_container.place_forget()
            self.cooldown_animation_id = None

    def hide_cooldown_notification(self):
        if hasattr(self, 'cooldown_animation_id') and self.cooldown_animation_id:
            self.root.after_cancel(self.cooldown_animation_id)
        if hasattr(self, 'cooldown_container'):
            self.cooldown_container.place_forget()
        self.cooldown_animation_id = None

    def center_toplevel(self, window, width, height):
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()
        x = main_x + (main_width - width) // 2
        y = main_y + (main_height - height) // 2
        window.geometry(f'{width}x{height}+{x}+{y}')

    def update_setting(self, setting_name, value):
        self.settings[setting_name] = value
        self.save_settings()

    def reset_settings(self):
        default_settings = {'show_seconds': True, 'auto_scroll': True, 'text_scale': 1.0, 'show_join_leave': True, 'current_theme': 'black'}
        self.settings.update(default_settings)
        self.apply_theme('black')
        self.seconds_var.set(True)
        self.auto_scroll_var.set(True)
        self.join_leave_var.set(True)
        self.save_settings()

    def load_settings(self):
        try:
            with open(os.path.join('assets', 'config', 'settings.json'), 'r', encoding='utf-8') as f:
                saved_settings = json.load(f)
                self.settings.update(saved_settings)
        except FileNotFoundError:
            self.save_settings()
        except json.JSONDecodeError:
            AlertFrame(self.root, 'Файл настроек поврежден. Используются настройки по умолчанию.', False)
            self.save_settings()

    def save_settings(self):
        try:
            with open(os.path.join('assets', 'config', 'settings.json'), 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            ErrorFrame(self.root, f'Ошибка при сохранении настроек: {e}', False)

    def apply_saved_settings(self):
        if 'current_theme' in self.settings:
            self.apply_theme(self.settings['current_theme'])

    def open_theme_window(self, parent_window):
        theme_window = ctk.CTkToplevel(parent_window)
        theme_window.title('Выбор темы')
        theme_window.resizable(False, False)
        theme_window.transient(parent_window)
        theme_window.attributes('-topmost', True)
        theme_window.focus_force()
        parent_window.attributes('-topmost', False)

        def on_theme_window_close():
            parent_window.attributes('-topmost', True)
            theme_window.destroy()
        theme_window.protocol('WM_DELETE_WINDOW', on_theme_window_close)
        self.center_toplevel(theme_window, 250, 400)
        current_theme = self.themes[self.current_theme]
        theme_window.configure(fg_color=current_theme['bg'])
        themes = [('Классическая', 'dark'), ('Чёрная', 'black'), ('Тёмно-синяя', 'dark_blue'), ('Тёмно-красная', 'dark_red'), ('Тёмно-фиолетовая', 'dark_purple'), ('Тёмно-зелёная', 'dark_green'), ('Тёмно-золотая', 'dark_gold'), ('Тёмно-голубая', 'dark_cyan'), ('Тёмно-розовая', 'dark_pink'), ('Полночь', 'midnight_blue'), ('Глубокий пурпур', 'deep_purple')]
        buttons_frame = ctk.CTkFrame(theme_window, fg_color=current_theme['text_box'])
        buttons_frame.pack(padx=15, pady=15, fill='both', expand=True)
        for theme_name, theme_id in themes:
            theme_colors = self.themes[theme_id]
            btn = ctk.CTkButton(buttons_frame, text=theme_name, command=lambda t=theme_id: self.apply_theme(t), fg_color=theme_colors['button'], hover_color=theme_colors['button_hover'], width=200, height=35)
            btn.pack(pady=5, padx=10)

    def apply_theme(self, theme_name):
        if theme_name in self.themes:
            self.current_theme = theme_name
            theme = self.themes[theme_name]
            self.root.configure(fg_color=theme['bg'])
            if hasattr(self, 'message_display'):
                self.message_display.configure(fg_color=theme['text_box'])
            if hasattr(self, 'profile_frame'):
                self.profile_frame.configure(fg_color=theme['text_box'])
            if hasattr(self, 'users_frame'):
                self.users_frame.configure(fg_color=theme['text_box'])
            if hasattr(self, 'input_frame'):
                self.input_frame.configure(fg_color=theme['text_box'], border_color=theme['accent'])
            if hasattr(self, 'cooldown_notification'):
                self.cooldown_notification.configure(fg_color='#1a5a3a', text_color=theme['accent'])
            if hasattr(self, 'message_entry'):
                self.message_entry.configure(fg_color=theme['text_box'], text_color=theme['fg'])
            if hasattr(self, 'send_button'):
                self.send_button.configure(fg_color='#1a1a1a', hover_color='#303030')
            if hasattr(self, 'send_image_button'):
                self.send_image_button.configure(fg_color='#1a1a1a', hover_color='#303030')
            settings_button_color = self.darken_color(theme['button'], 0.8)
            settings_button_hover = self.darken_color(theme['button_hover'], 0.8)
            if hasattr(self, 'settings_button'):
                self.settings_button.configure(fg_color=settings_button_color, hover_color=settings_button_hover, text_color=theme['accent'])
            if hasattr(self, 'disconnect_button'):
                self.disconnect_button.configure(fg_color=settings_button_color, hover_color=settings_button_hover, text_color=theme['accent'])
            if hasattr(self, 'profile_label'):
                self.profile_label.configure(text_color=theme['accent'])
            if hasattr(self, 'users_label'):
                self.users_label.configure(text_color=theme['accent'])
            if hasattr(self, 'nickname_label'):
                self.nickname_label.configure(text_color=theme['accent'])
            if hasattr(self, 'users_separator'):
                self.users_separator.configure(fg_color=theme['accent'])
            if hasattr(self, 'connection_status') and self.connection_status.winfo_exists():
                self.connection_status.configure(text_color='#00ff88' if self.connected else '#ff3333')
            if hasattr(self, 'version_label') and self.version_label.winfo_exists():
                self.version_label.configure(text_color='#888888')
            if hasattr(self, 'users_list'):
                self.users_list.configure(fg_color=theme['text_box'])
            darker_button = self.darken_color(theme['button'], 0.9)
            darker_border = self.darken_color(theme['button'], 0.8)
            if hasattr(self, 'user_cards'):
                for card in self.user_cards:
                    card.configure(fg_color=darker_button, border_color=darker_border)

                    def update_card_children(widget):
                        if isinstance(widget, ctk.CTkLabel):
                            text = widget.cget('text')
                            if text and (not any((char in text for char in ['●', '○']))):
                                widget.configure(text_color=theme['fg'])
                        elif isinstance(widget, ctk.CTkFrame) and widget.cget('fg_color') == 'transparent':
                            for child in widget.winfo_children():
                                update_card_children(child)
                    for child in card.winfo_children():
                        update_card_children(child)

            def update_widget_colors(widget):
                if isinstance(widget, ctk.CTkFrame):
                    widget.configure(fg_color=theme['text_box'])
                    for child in widget.winfo_children():
                        update_widget_colors(child)
                elif isinstance(widget, ctk.CTkLabel):
                    if any((text in str(widget.cget('text')) for text in ['• Отображение', '• Персонализация'])):
                        widget.configure(text_color=theme['accent'])
                    elif 'SproutLine' in str(widget.cget('text')):
                        widget.configure(text_color='#888888')
                    else:
                        widget.configure(text_color=theme['fg'])
                elif isinstance(widget, ctk.CTkButton):
                    button_color = self.darken_color(theme['button'], 0.8)
                    button_hover = self.darken_color(theme['button_hover'], 0.8)
                    widget.configure(fg_color=button_color, hover_color=button_hover, text_color=theme['fg'])
                elif isinstance(widget, ctk.CTkSwitch):
                    widget.configure(text_color=theme['fg'], progress_color=theme['accent'], button_color=theme['accent'], button_hover_color=theme['accent'])
                elif isinstance(widget, ctk.CTkSlider):
                    widget.configure(button_color=theme['accent'], button_hover_color=theme['accent'], progress_color=theme['accent'])
            for window in self.root.winfo_children():
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

    def show_ban_frame(self):
        self.connected = False
        self.client_socket.close()
        BanFrame(self.root)

    def disconnect_from_server(self):
        self.is_loading_history = False
        self.history_buffer = []
        if self.history_timeout_id is not None:
            try:
                self.root.after_cancel(self.history_timeout_id)
            except:
                pass
        self.connected = False
        self.client_socket.close()
        AlertFrame(self.root)

    def show_settings(self):
        if hasattr(self, 'settings_window') and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus_force()
            return
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title('Настройки')
        settings_window.resizable(False, False)
        settings_window.attributes('-topmost', True)
        settings_window.focus_force()
        self.center_toplevel(settings_window, 500, 360)
        theme = self.themes[self.current_theme]
        settings_window.configure(fg_color=theme['bg'])
        self.settings_window = settings_window
        if not hasattr(self, 'current_settings_tab'):
            self.current_settings_tab = 'profile'
        main_container = ctk.CTkFrame(settings_window, fg_color=theme['text_box'], corner_radius=10)
        main_container.pack(fill='both', expand=True, padx=8, pady=8)
        header_frame = ctk.CTkFrame(main_container, fg_color='transparent')
        header_frame.pack(fill='x', padx=10, pady=(8, 4))
        title_label = ctk.CTkLabel(header_frame, text='⚙️ Настройки', font=('Arial Bold', 16), text_color=theme['accent'])
        title_label.pack(side='left')
        separator = ctk.CTkFrame(main_container, height=1, fg_color=theme['accent'], corner_radius=1)
        separator.pack(fill='x', padx=10, pady=(0, 6))
        sidebar = ctk.CTkFrame(main_container, fg_color=self.darken_color(theme['button'], 0.95), width=120, corner_radius=8)
        sidebar.pack(side='left', fill='y', padx=(8, 6), pady=(4, 8))
        sidebar.pack_propagate(False)
        content_frame = ctk.CTkFrame(main_container, fg_color='transparent')
        content_frame.pack(side='right', fill='both', expand=True, padx=(2, 8), pady=(4, 8))
        self.settings_content_frame = content_frame
        self.settings_tabs = {}

        def switch_tab(tab_name):
            self.current_settings_tab = tab_name
            for widget in content_frame.winfo_children():
                widget.destroy()
            for name, (btn, _) in self.settings_tabs.items():
                if name == tab_name:
                    btn.configure(fg_color=theme['accent'], hover_color=theme['accent'], text_color=theme['bg'])
                else:
                    btn.configure(fg_color='transparent', hover_color=self.darken_color(theme['button'], 0.9), text_color=theme['fg'])
            if tab_name == 'profile':
                self._render_profile_tab()
        profile_btn = ctk.CTkButton(sidebar, text='👤 Профиль', width=110, height=32, font=('Arial', 11, 'bold'), fg_color=theme['accent'] if self.current_settings_tab == 'profile' else 'transparent', hover_color=theme['accent'] if self.current_settings_tab == 'profile' else self.darken_color(theme['button'], 0.9), text_color=theme['bg'] if self.current_settings_tab == 'profile' else theme['fg'], corner_radius=8, command=lambda: switch_tab('profile'))
        profile_btn.pack(pady=(8, 4), padx=6)
        self.settings_tabs['profile'] = (profile_btn, None)
        switch_tab(self.current_settings_tab)

        def on_closing():
            if hasattr(self, 'settings_window'):
                delattr(self, 'settings_window')
            settings_window.destroy()
        settings_window.protocol('WM_DELETE_WINDOW', on_closing)

    def _render_profile_tab(self):
        theme = self.themes[self.current_theme]
        card_color = self.darken_color(theme['button'], 0.9)
        button_color = self.darken_color(theme['accent'], 0.85)
        button_hover = self.darken_color(button_color, 0.9)
        profile_card = ctk.CTkFrame(self.settings_content_frame, fg_color=card_color, corner_radius=10, border_width=1, border_color=self.darken_color(theme['accent'], 0.3))
        profile_card.pack(fill='x', padx=8, pady=(6, 8))
        card_header = ctk.CTkFrame(profile_card, fg_color='transparent')
        card_header.pack(fill='x', padx=10, pady=(8, 4))
        card_title = ctk.CTkLabel(card_header, text='👤 Информация профиля', font=('Arial Bold', 13), text_color=theme['accent'])
        card_title.pack(side='left')
        nickname_frame = ctk.CTkFrame(profile_card, fg_color='transparent')
        nickname_frame.pack(fill='x', padx=10, pady=(2, 8))
        nickname_label_text = ctk.CTkLabel(nickname_frame, text='Никнейм:', font=('Arial', 9), text_color=theme['fg'])
        nickname_label_text.pack(side='left')
        current_nickname_label = ctk.CTkLabel(nickname_frame, text=self.nickname, font=('Arial Bold', 12), text_color=theme['accent'])
        current_nickname_label.pack(side='left', padx=(10, 0))
        self.profile_nickname_label = current_nickname_label
        buttons_container = ctk.CTkFrame(profile_card, fg_color='transparent')
        buttons_container.pack(fill='x', padx=10, pady=(0, 8))
        change_nickname_btn = ctk.CTkButton(buttons_container, text='✏️ Изменить никнейм', width=185, height=32, font=('Arial', 11, 'bold'), fg_color=button_color, hover_color=button_hover, text_color=theme['bg'], corner_radius=10, command=self.open_change_nickname_window)
        change_nickname_btn.pack(pady=(0, 6))
        change_password_btn = ctk.CTkButton(buttons_container, text='🔒 Изменить пароль', width=185, height=32, font=('Arial', 11, 'bold'), fg_color=button_color, hover_color=button_hover, text_color=theme['bg'], corner_radius=10, command=self.open_change_password_window)
        change_password_btn.pack()

    def open_change_nickname_window(self):
        import hashlib
        dialog = ctk.CTkToplevel(self.settings_window)
        dialog.title('Изменить никнейм')
        dialog.resizable(False, False)
        dialog.transient(self.settings_window)
        dialog.attributes('-topmost', True)
        dialog.focus_force()
        theme = self.themes[self.current_theme]
        dialog.configure(fg_color=theme['bg'])
        x = self.settings_window.winfo_x() + 50
        y = self.settings_window.winfo_y() + 50
        dialog.geometry(f'320x180+{x}+{y}')
        main_frame = ctk.CTkFrame(dialog, fg_color=theme['text_box'])
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        nickname_entry = ctk.CTkEntry(main_frame, placeholder_text='Новый никнейм', width=280, height=30, font=('Arial', 11))
        nickname_entry.pack(pady=(15, 5))
        nickname_entry.focus()
        error_label = ctk.CTkLabel(main_frame, text='', font=('Arial', 10), text_color='#ff3333', wraplength=280)
        error_label.pack(pady=(0, 10))

        def change_nickname():
            new_nickname = nickname_entry.get().strip()
            error_label.configure(text='')
            if not new_nickname:
                error_label.configure(text='Введите новый никнейм')
                return
            if len(new_nickname) < 3:
                error_label.configure(text='Никнейм должен содержать минимум 3 символа')
                return
            if len(new_nickname) > 20:
                error_label.configure(text='Никнейм не должен превышать 20 символов')
                return
            try:
                self.client_socket.send(f'CHANGE_NICKNAME:{new_nickname}\n'.encode('utf-8'))
                dialog.destroy()
            except Exception as e:
                error_label.configure(text=f'Ошибка отправки запроса: {e}')
        button_color = self.darken_color(theme['button'], 0.8)
        button_hover = self.darken_color(theme['button_hover'], 0.8)
        buttons_frame = ctk.CTkFrame(main_frame, fg_color='transparent')
        buttons_frame.pack(pady=5)
        ok_btn = ctk.CTkButton(buttons_frame, text='Изменить', width=100, height=30, font=('Arial', 11), fg_color=button_color, hover_color=button_hover, command=change_nickname)
        ok_btn.pack(side='left', padx=5)
        cancel_btn = ctk.CTkButton(buttons_frame, text='Отмена', width=100, height=30, font=('Arial', 11), fg_color=button_color, hover_color=button_hover, command=dialog.destroy)
        cancel_btn.pack(side='left', padx=5)
        nickname_entry.bind('<Return>', lambda e: change_nickname())

        def on_closing():
            dialog.destroy()
        dialog.protocol('WM_DELETE_WINDOW', on_closing)

    def open_change_password_window(self):
        import hashlib
        dialog = ctk.CTkToplevel(self.settings_window)
        dialog.title('Изменить пароль')
        dialog.resizable(False, False)
        dialog.transient(self.settings_window)
        dialog.attributes('-topmost', True)
        dialog.focus_force()
        theme = self.themes[self.current_theme]
        dialog.configure(fg_color=theme['bg'])
        x = self.settings_window.winfo_x() + 50
        y = self.settings_window.winfo_y() + 50
        dialog.geometry(f'320x250+{x}+{y}')
        main_frame = ctk.CTkFrame(dialog, fg_color=theme['text_box'])
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        old_password_entry = ctk.CTkEntry(main_frame, placeholder_text='Старый пароль', width=280, height=30, font=('Arial', 11), show='*')
        old_password_entry.pack(pady=(10, 5))
        old_password_entry.focus()
        new_password_entry = ctk.CTkEntry(main_frame, placeholder_text='Новый пароль', width=280, height=30, font=('Arial', 11), show='*')
        new_password_entry.pack(pady=(5, 5))
        error_label = ctk.CTkLabel(main_frame, text='', font=('Arial', 10), text_color='#ff3333', wraplength=280)
        error_label.pack(pady=(0, 10))

        def change_password():
            old_password = old_password_entry.get()
            new_password = new_password_entry.get()
            error_label.configure(text='')
            if not old_password or not new_password:
                error_label.configure(text='Заполните все поля')
                return
            if len(new_password) < 4:
                error_label.configure(text='Пароль должен содержать минимум 4 символа')
                return
            old_password_hash = hashlib.sha256(old_password.encode('utf-8')).hexdigest()
            new_password_hash = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
            try:
                self.client_socket.send(f'CHANGE_PASSWORD:{old_password_hash};{new_password_hash}\n'.encode('utf-8'))
                dialog.destroy()
            except Exception as e:
                error_label.configure(text=f'Ошибка отправки запроса: {e}')
        button_color = self.darken_color(theme['button'], 0.8)
        button_hover = self.darken_color(theme['button_hover'], 0.8)
        buttons_frame = ctk.CTkFrame(main_frame, fg_color='transparent')
        buttons_frame.pack(pady=5)
        ok_btn = ctk.CTkButton(buttons_frame, text='Изменить', width=100, height=30, font=('Arial', 11), fg_color=button_color, hover_color=button_hover, command=change_password)
        ok_btn.pack(side='left', padx=5)
        cancel_btn = ctk.CTkButton(buttons_frame, text='Отмена', width=100, height=30, font=('Arial', 11), fg_color=button_color, hover_color=button_hover, command=dialog.destroy)
        cancel_btn.pack(side='left', padx=5)
        old_password_entry.bind('<Return>', lambda e: new_password_entry.focus())
        new_password_entry.bind('<Return>', lambda e: change_password())

        def on_closing():
            dialog.destroy()
        dialog.protocol('WM_DELETE_WINDOW', on_closing)

    def close_settings(self):
        if hasattr(self, 'settings_window'):
            self.settings_window.destroy()
            delattr(self, 'settings_window')

    def check_connection_status(self):
        if self.is_closing or not hasattr(self, 'root'):
            return
        try:
            if not self.root.winfo_exists():
                return
        except:
            return
        threading.Thread(target=self._check_connection_status_async, daemon=True).start()
        task_id = self.root.after(5000, self.check_connection_status)
        if hasattr(self, 'after_ids'):
            self.after_ids.append(task_id)

    def _check_connection_status_async(self):
        if self.is_closing:
            return
        try:
            is_connected = check_internet_connection()
            if not self.is_closing and hasattr(self, 'root'):
                try:
                    if self.root.winfo_exists():
                        self.root.after(0, lambda: self._update_connection_status_ui(is_connected))
                except:
                    pass
        except Exception:
            pass

    def _update_connection_status_ui(self, is_connected):
        if self.is_closing or not hasattr(self, 'root'):
            return
        try:
            if not self.root.winfo_exists():
                return
        except:
            return
        self.connected = is_connected
        if hasattr(self, 'connection_status'):
            try:
                if self.connection_status.winfo_exists():
                    self.connection_status.configure(text_color='#00ff88' if is_connected else '#ff3333')
            except:
                pass
        if hasattr(self, 'profile_window'):
            try:
                if self.profile_window.winfo_exists():
                    for widget in self.profile_window.winfo_children():
                        if isinstance(widget, ctk.CTkFrame):
                            for inner_frame in widget.winfo_children():
                                if isinstance(inner_frame, ctk.CTkFrame):
                                    for label in inner_frame.winfo_children():
                                        if isinstance(label, ctk.CTkLabel) and label.cget('text') in ['В сети', 'Не в сети']:
                                            label.configure(text='В сети' if is_connected else 'Не в сети', text_color='#00ff88' if is_connected else '#ff3333')
            except Exception:
                pass

    def show_private_messages(self):
        pass

def center_window(window, width, height):
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = screen_width // 2 - width // 2
    y = screen_height // 2 - height // 2
    window.geometry(f'{width}x{height}+{x}+{y}')

class InitClass:

    def __init__(self):
        self.root = ctk.CTk()
        self.root.after(0, self.ensure_directories_and_files)
        self.root.mainloop()

    def ensure_directories_and_files(self):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            assets_dir = os.path.join(base_dir, 'assets')
            config_dir = os.path.join(assets_dir, 'config')
            images_dir = os.path.join(assets_dir, 'images')
            os.makedirs(config_dir, exist_ok=True)
            os.makedirs(images_dir, exist_ok=True)
            user_data_path = os.path.join(config_dir, 'user_data.json')
            servers_path = os.path.join(config_dir, 'servers.json')
            settings_path = os.path.join(config_dir, 'settings.json')
            if not os.path.exists(user_data_path):
                with open(user_data_path, 'w', encoding='utf-8') as f:
                    json.dump({}, f)
            if not os.path.exists(servers_path):
                with open(servers_path, 'w', encoding='utf-8') as f:
                    json.dump([], f)
            if not os.path.exists(settings_path):
                default_settings = {'show_seconds': True, 'message_sound': True, 'auto_scroll': True, 'font_size': 14, 'text_scale': 1.0, 'show_join_leave': True, 'current_theme': 'black'}
                with open(settings_path, 'w', encoding='utf-8') as f:
                    json.dump(default_settings, f, indent=4, ensure_ascii=False)
        except PermissionError:
            ErrorFrame(self.root, 'Отказано в доступе. Попробуйте запустить программу от имени администратора.')
            sys.exit(1)
        except Exception as e:
            ErrorFrame(self.root, f'Не удалось создать необходимые файлы и директории: {str(e)}')
            sys.exit(1)
        self.root.destroy()
        ServerListWindow()
if __name__ == '__main__':
    InitClass()