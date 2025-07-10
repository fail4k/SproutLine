from logging import disable
import customtkinter as ctk
import socket
import threading
import time
from PIL import Image
from customtkinter import CTkImage
import json
import os
import ctypes as ct
import urllib.request
import random
import sys

def set_window_dark_title_bar(window):
    """Установка темной темы для заголовка окна Windows"""
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
        self.dialog.title("Лицензионное соглашение")
        self.dialog.geometry("600x400")
        self.dialog.resizable(False, False)
        
        # Делаем окно поверх всех других окон при первом показе
        self.dialog.transient(master)  # Привязываем к родительскому окну
        self.dialog.focus_force()  # Принудительно устанавливаем фокус
        
        # Центрируем окно
        x = master.winfo_x() + (master.winfo_width() - 600) // 2
        y = master.winfo_y() + (master.winfo_height() - 400) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # Текст соглашения с переносом по словам
        self.text = ctk.CTkTextbox(
            self.dialog, 
            width=550, 
            height=350,
            wrap="word"  # Добавляем перенос по словам
        )
        self.text.pack(padx=20, pady=20)
        self.text.insert("1.0", """Лицензионное соглашение

1. Общие положения
Данное программное обеспечение (SproutLine) предназначено исключительно для общения между пользователями.

2. Использование
- Программа предоставляется "как есть"
- Запрещается использование программы для распространения вредоносного ПО
- Запрещается использование программы для нарушения законодательства

3. Ответственность
Разработчики не несут ответственности за:
- Содержание переписки пользователей
- Возможные технические сбои
- Любой причиненный ущерб

4. Конфиденциальность
- Программа не собирает личные данные пользователей
- Вся переписка хранится только у участников чата и на сервере
- Мы не несем ответственности за утечку данных
""")
        self.text.configure(state="disabled")
        
        # Кнопка закрытия
        self.close_button = ctk.CTkButton(
            self.dialog,
            text="Закрыть",
            command=self.close_dialog
        )
        self.close_button.pack(pady=(0, 10))
        
        # Привязываем обработчик закрытия окна
        self.dialog.protocol("WM_DELETE_WINDOW", self.close_dialog)
        
    def close_dialog(self):
        self.dialog.destroy()

class InputWindow:
    def __init__(self, server, error=""):
        self.root = ctk.CTk()
        self.root.title("Регистрация SproutLine")
        self.root.geometry("700x450")
        self.root.resizable(False, False)
        self.server = server
        self.error = error
        self.isRegister = True # По умолчанию открывается окно регистрации
        
        # Центрируем окно
        center_window(self.root, 700, 450)
        
        # Основной фрейм с градиентным фоном
        self.main_frame = ctk.CTkFrame(self.root, fg_color="#1A1A1A")
        self.main_frame.pack(fill="both", expand=True)
        
        # Контейнер для содержимого с отступами
        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="#212121", corner_radius=15)
        self.content_frame.pack(fill="both", expand=True, padx=40, pady=20)
        
        # Заголовок
        self.title_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.title_frame.pack(pady=(12.5, 12.5))
        
        self.title_label = ctk.CTkLabel(
            self.title_frame,
            text="Регистрация",
            font=("Arial Bold", 28),
            text_color="#00ff88"
        )
        self.title_label.pack()
        
        self.subtitle_label = ctk.CTkLabel(
            self.title_frame,
            text="Создайте аккаунт для начала общения",
            font=("Arial", 13),
            text_color="#888888"
        )
        self.subtitle_label.pack()

        # Кнопка смены регистрации на вход
        self.change_type_button = ctk.CTkButton(
            self.title_frame,
            fg_color="transparent",
            text="Или войдите в существующий",
            corner_radius=7.5,
            hover_color="#2D2D2D",
            font=("Arial", 12),
            text_color="#00ccff",
            command=self.change_type_of_window
        )
        self.change_type_button.pack()
        
        # Поля ввода в отдельном фрейме
        self.inputs_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.inputs_frame.pack(pady=5)
        
        # Стилизованные поля ввода
        entry_width = 300
        entry_height = 35
        
        self.nickname_entry = ctk.CTkEntry(
            self.inputs_frame,
            placeholder_text="Никнейм",
            width=entry_width,
            height=entry_height,
            font=("Arial", 13),
            fg_color="#2A2A2A",
            text_color="#FFFFFF",
            border_color="#00ff88",
            corner_radius=8
        )
        
        self.nickname_entry.pack(pady=6)
        
        self.password_entry = ctk.CTkEntry(
            self.inputs_frame,
            placeholder_text="Пароль",
            show="•",
            width=entry_width,
            height=entry_height,
            font=("Arial", 13),
            fg_color="#2A2A2A",
            text_color="#FFFFFF",
            border_color="#00ff88",
            corner_radius=8
        )
        self.password_entry.pack(pady=6)
        
        self.confirm_password_entry = ctk.CTkEntry(
            self.inputs_frame,
            placeholder_text="Подтвердите пароль",
            show="•",
            width=entry_width,
            height=entry_height,
            font=("Arial", 13),
            fg_color="#2A2A2A",
            text_color="#FFFFFF",
            border_color="#00ff88",
            corner_radius=8
        )
        self.confirm_password_entry.pack(pady=6)
        
        # Лицензионное соглашение
        self.agreement_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.agreement_frame.pack(pady=6)
        
        self.agreement_var = ctk.BooleanVar()
        self.agreement_checkbox = ctk.CTkCheckBox(
            self.agreement_frame,
            text="Я согласен с",
            variable=self.agreement_var,
            checkbox_width=18,
            checkbox_height=18,
            font=("Arial", 12),
            fg_color="#00ff88",
            hover_color="#00cc6a",
            text_color="#888888"
        )
        self.agreement_checkbox.pack(side="left")
        
        self.agreement_button = ctk.CTkButton(
            self.agreement_frame,
            text="лицензионным соглашением",
            fg_color="transparent",
            hover_color="#2D2D2D",
            font=("Arial", 12),
            text_color="#00ccff",
            command=self.show_license
        )
        self.agreement_button.pack(side="left")
        
        # Кнопка ввода
        self.input_button = ctk.CTkButton(
            self.content_frame,
            text="Зарегистрироваться",
            width=250,
            height=40,
            font=("Arial Bold", 14),
            fg_color="#00ff88",
            text_color="#000000",
            hover_color="#00cc6a",
            corner_radius=8,
            command=self.inputFunc
        )
        self.input_button.pack(pady=10)

        # Кнопка возврата к выбору верверов
        self.return_button = ctk.CTkButton(
            self.content_frame,
            text="Вернуться к выбору серверов",
            width=150,
            height=20,
            font=("Arial Bold", 12),
            fg_color="#1A1A1A",
            hover_color="#212121",
            text_color="#00ff88",
            corner_radius=7.5,
            command=self.return_to_server_choose
        )
        self.return_button.pack()
        
        # Сообщение об ошибке
        self.error_label = ctk.CTkLabel(
            self.content_frame,
            text=self.error,
            text_color="#ff3333",
            font=("Arial", 12)
        )
        self.error_label.pack()

        try: # По умолчанию делаем регистрацию, если был недавний вход - покажется окно входе с прошлым ником входа, если нет - регистрация
            with open(os.path.join("assets", "config", "user_data.json"), "r") as f:
                user_data = json.load(f)
            
            if user_data:
                if user_data[self.server["server_id"]]:
                    if user_data[self.server["server_id"]]["nickname"]:
                        self.nickname_entry.insert(0, user_data[self.server["server_id"]]["nickname"])
                        self.change_type_of_window()

        except (FileNotFoundError, json.JSONDecodeError):
            pass # Если файла не оказалось - ничего страшного, при первом заходе он создастся
        
        self.root.mainloop()

    def change_type_of_window(self):
        if self.isRegister:
            self.root.title(f"Вход в аккаунт SproutLine")
            self.title_label.configure(text="Вход в аккаунт")
            self.subtitle_label.configure(text="Войдите в аккаунт для продолжения общения")
            self.change_type_button.configure(text="Или создайте новый")
            self.confirm_password_entry.pack_forget()
            self.agreement_frame.pack_forget()
            self.input_button.configure(text="Войти в аккаунт")
            self.isRegister = False
        else:
            self.root.title(f"Регистрация SproutLine")
            self.title_label.configure(text="Регистрация")
            self.subtitle_label.configure(text="Создайте аккаунт для начала общения")
            self.change_type_button.configure(text="Или войдите в существующий")
            self.nickname_entry.delete(0, "end")
            self.nickname_entry.configure(placeholder_text="Никнейм")
            self.confirm_password_entry.pack(pady=6)
            self.agreement_frame.pack(pady=6)
            self.input_button.pack_forget()
            self.input_button.pack(pady=10)
            self.return_button.pack_forget()
            self.return_button.pack()
            self.error_label.pack_forget()
            self.error_label.pack()
            self.input_button.configure(text="Зарегистрироваться")
            self.isRegister = True
        
    def show_license(self):
        LicenseAgreementWindow(self.root)

    def return_to_server_choose(self):
        self.root.destroy()
        ServerListWindow()
    
    def inputFunc(self): # То, что будет происходить после нажатия кнопки ввода
        nickname = self.nickname_entry.get().strip()
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        
        if not nickname or not password:
            self.error_label.configure(text="Заполните все поля")
            return
            
        if password != confirm_password and self.isRegister:
            self.error_label.configure(text="Пароли не совпадают")
            return
            
        if not self.agreement_var.get() and self.isRegister:
            self.error_label.configure(text="Примите лицензионное соглашение")
            return
        
        # # Генерируем уникальный ID на основе никнейма
        # seed = sum(ord(c) for c in nickname)
        # random.seed(seed)
        # user_id = ''.join([str(random.randint(0, 9)) for _ in range(9)])
        # random.seed()  # Сбрасываем seed
            
        # Сохраняем данные
        try:
            with open(os.path.join("assets", "config", "user_data.json"), "w") as f: # Сохраняем данные об отправке данных
                json.dump(
                {
                    self.server["server_id"]: {
                        "nickname": nickname,
                        }
                        
                }, f)

            self.root.destroy()

            try:

                # Создаем экземпляр мессенджера
                MessengerApp(self.server, nickname, password, self.isRegister)
                
                
            except Exception as e:
                # messagebox.showerror("Ошибка подключения", f"Не удалось подключиться к серверу: {str(e)}")
                InputWindow(self.server)

        except Exception as e:
            self.error_label.configure(text=f"Ошибка регистрации: {str(e)}")

class ServerListWindow:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Список серверов SproutLine")
        self.root.geometry("700x400")
        self.root.resizable(False, False)
        
        # Загружаем список серверов
        self.servers = self.load_servers()
        
        # Инициализируем переменную для отслеживания выбранного сервера
        self.selected_server = None
        
        # Добавляем флаг для отслеживания открытых окон
        self.dialog_open = False
        
        # Основной фрейм
        self.main_frame = ctk.CTkFrame(self.root, fg_color="#1A1A1A")
        self.main_frame.pack(fill="both", expand=True)
        
        # # Кнопка выхода из аккаунта
        # self.logout_button = ctk.CTkButton(
        #     self.main_frame,
        #     text="Выйти из аккаунта",
        #     width=120,
        #     font=("Arial Bold", 12),
        #     fg_color="#1E1E1E",
        #     hover_color="#2D2D2D",
        #     text_color="#ff3333",
        #     command=self.logout
        # )
        # self.logout_button.place(relx=0.05, rely=0.05)
        
        # Заголовок
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="Список серверов",
            font=("Arial Bold", 24),
            text_color="#00ff88"
        )
        self.title_label.pack(pady=(50, 10))
        
        # Список серверов
        self.servers_frame = ctk.CTkScrollableFrame(
            self.main_frame,
            fg_color="#1E1E1E",
            width=660,
            height=200  # Уменьшаем высоту, чтобы оставить место для кнопок
        )
        self.servers_frame.pack(pady=10, padx=20)
        
        # Обновляем список серверов
        self.update_server_list()
        
        # Кнопки управления (внизу окна)
        self.buttons_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.buttons_frame.pack(side="bottom", fill="x", padx=20, pady=20)
        
        # Увеличиваем ширину и высоту кнопок
        button_width = 200  # Было 200
        button_height = 35  # Добавляем высоту
        
        self.add_button = ctk.CTkButton(
            self.buttons_frame,
            text="Добавить сервер",
            width=button_width,
            height=button_height,
            font=("Arial Bold", 13),  # Немного увеличил шрифт
            fg_color="#242424",  # Сделал светлее (было #1E1E1E)
            hover_color="#2D2D2D",
            text_color="#00ff88",
            command=self.add_server
        )
        self.add_button.pack(side="left", padx=10)
        
        self.edit_button = ctk.CTkButton(
            self.buttons_frame,
            text="Изменить",
            width=button_width,
            height=button_height,
            font=("Arial Bold", 13),
            fg_color="#242424",
            hover_color="#2D2D2D",
            text_color="#00ff88",
            command=self.edit_server
        )
        self.edit_button.pack(side="left", padx=10)
        
        self.delete_button = ctk.CTkButton(
            self.buttons_frame,
            text="Удалить",
            width=button_width,
            height=button_height,
            font=("Arial Bold", 13),
            fg_color="#242424",
            hover_color="#2D2D2D",
            text_color="#00ff88",
            command=self.delete_server
        )
        self.delete_button.pack(side="left", padx=10)
        
        # Добавляем кнопку профиля в правом верхнем углу
        # self.profile_button = ctk.CTkButton(
        #     self.main_frame,
        #     text="Профиль",
        #     width=120,
        #     font=("Arial Bold", 12),
        #     fg_color="#1E1E1E",
        #     hover_color="#2D2D2D",
        #     text_color="#00ff88",
        #     command=self.show_profile
        # )
        # self.profile_button.place(relx=0.83, rely=0.05)
        
        self.root.mainloop()
        
    def load_servers(self):
        try:
            with open(os.path.join("assets", "config", "servers.json"), "r") as f:
                return json.load(f)
        except:
            return []
            
    def save_servers(self):
        with open(os.path.join("assets", "config", "servers.json"), "w") as f:
            json.dump(self.servers, f)
            
    def update_server_list(self):
        # Очищаем текущий список
        for widget in self.servers_frame.winfo_children():
            widget.destroy()
            
        # Добавляем серверы
        for server in self.servers:
            # Создаем фрейм для сервера
            server_frame = ctk.CTkFrame(
                self.servers_frame,
                fg_color="#2D2D2D",
                corner_radius=10,
                height=80
            )
            server_frame.pack(fill="x", pady=5, padx=5, ipady=10)
            server_frame.pack_propagate(False)
            
            # Добавляем обработчик клика для выбора сервера
            server_frame.bind("<Button-1>", lambda e, s=server: self.select_server(s, e))
            
            # Информация о сервере
            info_frame = ctk.CTkFrame(
                server_frame,
                fg_color="transparent"
            )
            info_frame.pack(side="left", padx=15, fill="both", expand=True)
            info_frame.bind("<Button-1>", lambda e, s=server: self.select_server(s, e))
            
            name_label = ctk.CTkLabel(
                info_frame,
                text=server["name"],
                font=("Arial Bold", 16),
                text_color="#00ff88"
            )
            name_label.pack(anchor="w", pady=(5, 0))
            name_label.bind("<Button-1>", lambda e, s=server: self.select_server(s, e))
            
            info_label = ctk.CTkLabel(
                info_frame,
                text=f"IP: {server['ip']}:{server['port']}",
                font=("Arial", 12),
                text_color="#888888"
            )
            info_label.pack(anchor="w")
            info_label.bind("<Button-1>", lambda e, s=server: self.select_server(s, e))
            
            # Кнопка подключения
            connect_button = ctk.CTkButton(
                server_frame,
                text="Подключиться",
                width=120,
                height=30,
                font=("Arial Bold", 12),
                fg_color="#1E1E1E",
                hover_color="#2D2D2D",
                text_color="#00ff88",
                command=lambda s=server: self.connect_to_server(s)
            )
            connect_button.pack(side="right", padx=15)
            
            # Если это выбранный сервер, меняем цвет фона
            if self.selected_server == server:
                server_frame.configure(fg_color="#3D3D3D")

    def select_server(self, server, event=None):
        """Выбор сервера при клике"""
        self.selected_server = server
        self.update_server_list()  # Обновляем отображение для подсветки выбранного сервера
    
    def add_server(self):
        if not self.dialog_open:
            self.dialog_open = True
            dialog = ServerDialog(self.root, "Добавить сервер")
            dialog.dialog.transient(self.root)  # Делаем окно поверх основного
            dialog.dialog.focus_force()  # Фокусируем окно
            result = dialog.show()
            self.dialog_open = False
            
            if result:
                self.servers.append(result)
                self.save_servers()
                self.update_server_list()
            
    def edit_server(self):
        if not self.selected_server:
            AlertFrame(self.root, f"Выберите сервер для редактирования", False)
            return
            
        if not self.dialog_open:
            self.dialog_open = True
            dialog = ServerDialog(self.root, "Изменить сервер")
            dialog.dialog.grab_set()  # Блокируем взаимодействие с основным окном
            dialog.dialog.transient(self.root)  # Делаем окно поверх основного
            dialog.dialog.focus_force()  # Фокусируем окно
            
            # Заполняем поля текущими значениями
            dialog.name_entry.insert(0, self.selected_server["name"])
            dialog.ip_entry.insert(0, self.selected_server["ip"])
            dialog.port_entry.insert(0, self.selected_server["port"])
            
            result = dialog.show()
            self.dialog_open = False
            
            if result:
                index = self.servers.index(self.selected_server)
                self.servers[index] = result
                self.save_servers()
                self.selected_server = result
                self.update_server_list()
    
    def delete_server(self):
        """Удаление выбранного сервера"""
        if not self.selected_server:
            AlertFrame(self.root, "Выберите сервер для удаления", False)
            return
            
        self.servers.remove(self.selected_server)
        self.save_servers()
        self.selected_server = None
        self.update_server_list()
        
    def connect_to_server(self, server):
        """Подключение к выбранному серверу"""
        self.root.destroy() 
        InputWindow(server)
        

    # def logout(self):
    #     """Выход из аккаунта"""
    #     if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите выйти из аккаунта?"):
    #         try:
    #             # Удаляем файл с данными пользователя
    #             if os.path.exists(os.path.join("assets", "config", "user_data.json")):
    #                 os.remove(os.path.join("assets", "config", "user_data.json"))
                
    #             # Закрываем текущее окно и открываем окно регистрации
    #             self.root.destroy()
    #             InputWindow()
    #         except Exception as e:
    #             messagebox.showerror("Ошибка", f"Не удалось выйти из аккаунта: {str(e)}")

    def show_profile(self):
        if not hasattr(self, 'profile_window') or not self.profile_window.winfo_exists():
            # Создаем поток для открытия окна профиля
            profile_thread = threading.Thread(target=self._create_profile_window)
            profile_thread.daemon = True
            profile_thread.start()

    def _create_profile_window(self):
        self.profile_window = ctk.CTkToplevel()
        self.profile_window.title("Профиль")
        self.profile_window.geometry("400x500")
        self.profile_window.resizable(False, False)
        
        # Добавляем обработчик закрытия окна
        self.profile_window.protocol("WM_DELETE_WINDOW", self.on_profile_window_close)
        
        # Устанавливаем темную тему
        self.profile_window.configure(fg_color="#1A1A1A")
        
        # Делаем окно поверх всех других окон при первом показе
        self.profile_window.transient(self.root)
        self.profile_window.focus_force()
        
        # Центрируем окно
        x = self.root.winfo_x() + (self.root.winfo_width() - 400) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 500) // 2
        self.profile_window.geometry(f"+{x}+{y}")
        
        # Создаем фрейм с темным фоном
        profile_frame = ctk.CTkFrame(
            self.profile_window,
            fg_color="#212121",
            corner_radius=10
        )
        profile_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Аватар пользователя (заглушка)
        avatar_frame = ctk.CTkFrame(
            profile_frame,
            width=120,
            height=120,
            corner_radius=60,
            fg_color="#2A2A2A"
        )
        avatar_frame.pack(pady=(30, 20))
        avatar_frame.pack_propagate(False)
        
        # Иконка пользователя
        avatar_label = ctk.CTkLabel(
            avatar_frame,
            text="👤",
            font=("Arial", 50),
            text_color="#888888"
        )
        avatar_label.place(relx=0.5, rely=0.5, anchor="center")
        
        try:
            with open(os.path.join("assets", "config", "user_data.json"), "r") as f:
                user_data = json.load(f)
                nickname = user_data["nickname"]
                user_id = user_data.get("user_id", "Неизвестно")  # Получаем сохраненный ID
        except:
            nickname = "Неизвестно"
            user_id = "Неизвестно"
        
        # Никнейм пользователя
        ctk.CTkLabel(
            profile_frame,
            text=nickname,
            font=("Arial Bold", 24),
            text_color="#ffffff"
        ).pack(pady=(0, 5))
        
        # ID пользователя (используем сохраненный ID)
        ctk.CTkLabel(
            profile_frame,
            text=f"ID: {user_id}",
            font=("Arial", 12),
            text_color="#888888"
        ).pack(pady=(0, 20))
        
        # Разделитель
        separator = ctk.CTkFrame(profile_frame, height=2, fg_color="#2A2A2A")
        separator.pack(fill="x", padx=30, pady=20)
        
        # Информация о пользователе
        info_frame = ctk.CTkFrame(profile_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=30)
        
        # Статус подключения
        status_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        status_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            status_frame,
            text="Статус:",
            font=("Arial", 14),
            text_color="#888888"
        ).pack(side="left")
        
        # Проверяем текущий статус подключения
        self.connected = check_internet_connection()
        
        ctk.CTkLabel(
            status_frame,
            text="В сети" if self.connected else "Не в сети",
            font=("Arial", 14),
            text_color="#00ff88" if self.connected else "#ff3333"
        ).pack(side="right")
        
        # IP адрес
        ip_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        ip_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            ip_frame,
            text="IP адрес:",
            font=("Arial", 14),
            text_color="#888888"
        ).pack(side="left")
        
        # Получаем внешний IP
        try:
            external_ip = urllib.request.urlopen('https://api.ipify.org').read().decode('utf-8')
        except:
            external_ip = "Недоступно"
        
        ctk.CTkLabel(
            ip_frame,
            text=external_ip,
            font=("Arial", 14),
            text_color="#ffffff"
        ).pack(side="right")
        
        # Дата регистрации
        reg_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        reg_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            reg_frame,
            text="Дата регистрации:",
            font=("Arial", 14),
            text_color="#888888"
        ).pack(side="left")
        
        try:
            reg_date = time.strftime("%d.%m.%Y", time.localtime(os.path.getctime(os.path.join("assets", "config", "user_data.json"))))
        except:
            reg_date = "Неизвестно"
        
        ctk.CTkLabel(
            reg_frame,
            text=reg_date,
            font=("Arial", 14),
            text_color="#ffffff"
        ).pack(side="right")
        
        # Разделитель
        separator2 = ctk.CTkFrame(profile_frame, height=2, fg_color="#2A2A2A")
        separator2.pack(fill="x", padx=30, pady=20)
        
        # Кнопки действий
        buttons_frame = ctk.CTkFrame(profile_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        # Кнопка изменения никнейма
        change_nick_btn = ctk.CTkButton(
            buttons_frame,
            text="Изменить никнейм",
            font=("Arial", 14),
            fg_color="#2A2A2A",
            hover_color="#333333",
            height=35
        )
        change_nick_btn.pack(fill="x", pady=5)
        
        # Кнопка выхода из аккаунта
        logout_btn = ctk.CTkButton(
            buttons_frame,
            text="Выйти из аккаунта",
            font=("Arial", 14),
            fg_color="#2A2A2A",
            hover_color="#333333",
            text_color="#ff3333",
            height=35
        )
        logout_btn.pack(fill="x", pady=5)

    def on_profile_window_close(self):
        """Обработчик закрытия окна профиля"""
        self.profile_window.destroy()
        if hasattr(self, 'profile_window'):
            delattr(self, 'profile_window')

class ServerDialog:
    def __init__(self, parent, title):
        self.dialog = ctk.CTkToplevel()
        self.dialog.title(title)
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)

        # Устанавливаем темную тему
        self.dialog.configure(fg_color="#1A1A1A")
        
        # Делаем окно поверх всех других окон при первом показе
        self.dialog.transient(parent)  # Привязываем к родительскому окну
        self.dialog.focus_force()  # Принудительно устанавливаем фокус
        
        # Центрируем окно
        x = parent.winfo_x() + (parent.winfo_width() - 400) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 300) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # Создаем основной фрейм с темным фоном
        main_frame = ctk.CTkFrame(
            self.dialog,
            fg_color="#212121",
            corner_radius=10
        )
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Поля ввода с темной темой
        self.name_entry = ctk.CTkEntry(
            main_frame,
            placeholder_text="Название сервера",
            fg_color="#2A2A2A",
            text_color="#ffffff",
            placeholder_text_color="#888888"
        )
        self.name_entry.pack(pady=10, padx=20, fill="x")
        
        self.ip_entry = ctk.CTkEntry(
            main_frame,
            placeholder_text="IP адрес",
            fg_color="#2A2A2A",
            text_color="#ffffff",
            placeholder_text_color="#888888"
        )
        self.ip_entry.pack(pady=10, padx=20, fill="x")
        
        self.port_entry = ctk.CTkEntry(
            main_frame,
            placeholder_text="Порт",
            fg_color="#2A2A2A",
            text_color="#ffffff",
            placeholder_text_color="#888888"
        )
        self.port_entry.pack(pady=10, padx=20, fill="x")
        
        # Кнопки с темной темой
        self.ok_button = ctk.CTkButton(
            main_frame,
            text="OK",
            fg_color="#1E1E1E",
            hover_color="#2D2D2D",
            text_color="#00ff88",
            command=self.on_ok
        )
        self.ok_button.pack(pady=10)
        
        self.cancel_button = ctk.CTkButton(
            main_frame,
            text="Отмена",
            fg_color="#1E1E1E",
            hover_color="#2D2D2D",
            text_color="#ff3333",
            command=self.dialog.destroy
        )
        self.cancel_button.pack(pady=5)
        
        self.result = None
        
    def on_ok(self):
        """Обработчик нажатия кнопки OK"""
        # Генерируем уникальный ID на основе названия сервера. ID используется только на стороне клиента
        seed = sum(ord(c) for c in self.name_entry.get())
        random.seed(seed)
        server_id = ''.join([str(random.randint(0, 9)) for _ in range(9)])
        random.seed()  # Сбрасываем seed

        self.result = {
            "name": self.name_entry.get(),
            "ip": self.ip_entry.get(),
            "port": self.port_entry.get(),
            "server_id": server_id
        }
        self.dialog.destroy()
        
    def show(self):
        """Показать диалог и вернуть результат"""
        self.dialog.wait_window()
        return self.result

class MessageFrame(): # Абстрактный класс для создания окон уведомлений
    def __init__(self, root, title, message_icon, message_color, message_text, hide_root=False):
        self.hide_root = hide_root

        master = ctk.CTkToplevel(root)

        if self.hide_root: # Проверяем, нужно ли удалить главное окно
            root.withdraw()
            master.protocol("WM_DELETE_WINDOW", root.destroy)

        # Задаем необходимые переменные
        self.title = title
        self.message_icon = message_icon
        self.message_color = message_color
        self.message_text = '\n'.join(message_text[i:i+55] for i in range(0, len(message_text), 55)) # Если строка слишком длинная - форматируем, расставляя переходы на новую строку

        def closeWindow():
            master.destroy()

            if self.hide_root: # Если главное окно было скрыто, значит его надо будет ещё и удалить
                root.destroy()

            ServerListWindow()
        
        # Настраиваем цвета
        master.configure(fg_color='#1A1A1A')   # Устанавливаем цвет фона главного окна
        
        # Устанавливаем размеры окна
        master.geometry('700x350')  # Устанавливаем размеры окна
        master.resizable(False, False)
        master.title(f"SproutLine - {self.title}")

        # Создаем внутренний фрейм для содержимого
        content_frame = ctk.CTkFrame(
            master,
            fg_color='#1E1E1E',  # Чуть светлее основного фона
            corner_radius=10,
            width=700,           # Указываем размеры при создании
            height=350
        )
        content_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Иконка Сообщения
        ban_label = ctk.CTkLabel(
            content_frame,
            text=self.message_icon,
            font=("Arial", 40),
            text_color=self.message_color
        )
        ban_label.pack(pady=(20, 5))
        
        # Текст сообщения
        message_label = ctk.CTkLabel(
            content_frame,
            text=self.message_text,
            font=("Arial Bold", 24),
            text_color=self.message_color,
        )
        message_label.pack(pady=5)
        
        # Кнопка закрытия
        close_button = ctk.CTkButton(
            content_frame,
            text="Закрыть",
            font=("Arial", 14),
            fg_color='#2A2A2A',
            hover_color='#3A3A3A',
            command=closeWindow,
            width=120
        )
        close_button.pack(pady=15)
        
        # # Растягиваем фрейм на все окно
        # master.pack(fill="both", expand=True)

class AlertFrame(MessageFrame):
    def __init__(self, master):
        self.title = "Alert window"
        self.message_icon = "⚠️"
        self.message_color = "#FFF133"
        self.message_text = "Вы были отключены от сервера"
        super().__init__(master, self.title, self.message_icon, self.message_color, self.message_text, True)


class BanFrame(MessageFrame):
    def __init__(self, master):
        self.title = "Ban Window"
        self.message_icon = "⛔"
        self.message_color = "#FF3333"
        self.message_text = "ВЫ ЗАБАНЕНЫ"
        super().__init__(master, self.title, self.message_icon, self.message_color, self.message_text, True)

class ErrorFrame(MessageFrame):
    def __init__(self, master, error_text, hide_root=True):
        self.title = "Error Window"
        self.message_icon = "☠️"
        self.message_color = "#FFFFFF"
        self.message_text = error_text
        super().__init__(master, self.title, self.message_icon, self.message_color, self.message_text, hide_root)

def check_internet_connection():
    """Проверка подключения к интернету"""
    try:
        # Пытаемся подключиться к надежному серверу Google
        urllib.request.urlopen('http://google.com', timeout=1)
        return True
    except:
        return False

class MessengerApp:
    def __init__(self, server, nickname, password, isRegister):
        # Создаем окно мессенджера
        self.root = ctk.CTk()

        self.nickname = nickname
        self.password = password
        self.isRegister = "R" if isRegister else "L" # Устанавливаем вид деятельности: регистрация или вход в аккаунт

        self.server = server
        self.ip = server['ip']
        self.port = int(server['port'])

        # Создаем сокет и устанавливаем параметры
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                
        # Устанавливаем размеры окна
        window_width = 750
        window_height = 340
        
        # Получаем размеры экрана
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Рассчитываем позицию для центрирования
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        
        # Устанавливаем размеры и позицию окна
        self.root.geometry(f'{window_width}x{window_height}+{x}+{y}')
        
        # Сначала отправляем никнейм
        try:
            # Пытаемся подключиться к серверу
            self.client_socket.connect((self.ip, self.port))

            self.client_socket.send(f"{self.isRegister};{nickname};{password}".encode('utf-8')) # Отправляем инициализационный запрос. Контракт выглядит следующим образом: <тип операции (регистрация или вход в аккаунт)><имя_пользователя>;<пароль>
            # Ждем ответ от сервера
            initial_response = self.client_socket.recv(1024).decode('utf-8')

            if initial_response == "ERROR:BANNED":
                self.root.after(0, self.show_ban_frame) # Если мы забанены - отображаем окно бана после инициализации компонента
                self.root.mainloop() # Инициализируем компонент
            
            if initial_response == "ERROR:NICKNAME_TAKEN":
                self.root.destroy()
                InputWindow(self.server, error="Пользователь с таким именем уже существует")

            if initial_response == "ERROR:NICKNAME_ONLINE":
                self.root.destroy()
                InputWindow(self.server, error="Пользователь с таким именем в данный момент находится в чате")
            
            if initial_response == "ERROR:WRONG_PASSWORD":
                self.root.destroy()
                InputWindow(self.server, error="Неверный пароль")
            
            if initial_response == "ERROR:WRONG_OPERATION":
                self.root.destroy()
                InputWindow(self.server, error="Неверная операция, ошибка приложения")

            if initial_response[:4] == "CCT:": # Получаем CCT:<время_между_сообщениями>;USERS:<список>,<всех>,<пользователей>
                response = initial_response[4:].split(";") # Разбиваем на массив из <время_между_сообщениями> и USERS:<список>,<всех>,<пользователей>

                self.message_cooldown = int(response[0]) # устанавливаем <время_между_сообщениями>

                self.init_userlist = [user.strip() for user in response[1][6:].split(",") if user.strip()] # Получаем начальный список пользователей

        except Exception as e:
            ErrorFrame(self.root, f"Ошибка при инициализации: {e}")
            return
            
        self.connected = True
        self.unsent_messages = []

        # Если не забанен, создаем интерфейс
        self.root.after(100, self.setup_interface) # Даем время инициализизоваться root интерфейсу, поэтому вызываем через after
        
        self.root.after(200, self.check_connection_status) # Начальная проверка статуса

        # Запускаем главный цикл
        self.root.mainloop()
        
        # self.start_time = time.time()
        # self.update_time_spent()

    def setup_interface(self):
        """Создание интерфейса приложения"""
        self.root.title(f"SproutLine - {self.nickname}")
        self.root.resizable(False, False)

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
            'black': {  # Новая тёмная тема
                'bg': '#000000',
                'fg': '#FFFFFF',
                'button': '#1A1A1A',
                'button_hover': '#2D2D2D',
                'frame': '#000000',
                'accent': '#00ff88',
                'text_box': '#1A1A1A'
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
        
        try:
            self.image_send = Image.open(os.path.join("assets", "images", "send.png"))
            self.image_send = self.image_send.resize((500, 500), Image.LANCZOS)

            self.image_exit = Image.open(os.path.join("assets", "images", "exit.png"))
            self.image_exit = self.image_exit.resize((50, 50), Image.LANCZOS)

            self.image_settings = Image.open(os.path.join("assets", "images", "settings.png"))
            self.image_settings = self.image_settings.resize((50, 50), Image.LANCZOS)

            self.image_message = Image.open(os.path.join("assets", "images", "message.png"))
            self.image_message = self.image_message.resize((50, 50), Image.LANCZOS)

            self.photo_send = CTkImage(light_image=None, dark_image=self.image_send)
            self.photo_exit = CTkImage(light_image=None, dark_image=self.image_exit)
            self.photo_settings = CTkImage(light_image=None, dark_image=self.image_settings)
            self.photo_message = CTkImage(light_image=None, dark_image=self.image_message)

        except Exception as e:
            ErrorFrame(self.root, f"Ошибка при загрузке изображения: {e}", False)
            self.photo_send = None
            self.photo_exit = None
        
        self.message_display = ctk.CTkTextbox(self.root, width=500, height=283, corner_radius=10, state="disabled")
        self.message_display.place(relx=0.07, rely=0.01)
        self.message_display.configure(font=("Arial", 14))
        
        self.profile_frame = ctk.CTkFrame(self.root, width=175, height=140, corner_radius=10, fg_color='#1B1B1B')
        self.profile_frame.place(relx=0.76, rely=0.01)
        
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
            text='     ◆ Версия: 2.0',
            font=('Arial', 13),
            text_color='#888888'
        )
        self.version_label.place(relx=0.05, rely=0.45)

        self.users_frame = ctk.CTkFrame(self.root, width=175, height=180, corner_radius=10, fg_color='#1B1B1B')
        self.users_frame.place(relx=0.76, rely=0.45)
        
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

        self.message_entry = ctk.CTkEntry(self.root, width=455, height=40)
        self.message_entry.place(relx=0.07, rely=0.86)
        self.message_entry.bind("<Return>", lambda event: self.send_message())

        self.send_button = ctk.CTkButton(self.root, image=self.photo_send, width=40, height=40, font=("Arial", 15), text="", fg_color='#1a1a1a', hover_color='#303030', command=self.send_message)
        self.send_button.place(relx=0.685, rely=0.86)

        # Кнопка настроек
        self.settings_button = ctk.CTkButton(
            self.root, 
            text="",
            image=self.photo_settings,
            width=40,
            height=40,
            fg_color='#2d2d2d',
            hover_color='#303030',
            font=('Arial', 12),
            command=self.show_settings
        )
        self.settings_button.place(relx=0.008, rely=0.86)
        
        # кнопка выйти(да0)
        self.disconnect_button = ctk.CTkButton(
            self.root,
            text="",
            image=self.photo_exit,
            width=40,
            height=40,
            fg_color='#2d2d2d',
            hover_color='#303030',
            font=('Arial', 12),
            command=self.disconnect_from_server
        )
        self.disconnect_button.place(relx=0.008, rely=0.72)
        
        # лс
        self.private_messages = ctk.CTkButton(
                self.root,
                text="",
                image=self.photo_message,
                width=40,
                height=40,
                fg_color='#2d2d2d',
                hover_color='#303030',
                font=("Arial", 12),
                command=self.show_private_messages
        )
        self.private_messages.place(relx=0.008, rely=0.01)

        self.receive_thread = threading.Thread(target=self.receive_messages)
        self.receive_thread.daemon = True
        self.receive_thread.start()

        self.keep_alive_thread = threading.Thread(target=self.keep_alive)
        self.keep_alive_thread.daemon = True
        self.keep_alive_thread.start()

        self.last_message_time = 0
        self.max_message_length = 300
        
        self.notification_label = ctk.CTkLabel(
            self.root,
            text="",
            text_color="#ff3333",
            font=('Arial', 12)
        )
        self.notification_label.place(relx=0.01, rely=0.8)

        self.update_users_list(self.init_userlist) # Выводим всех пользователей, которые были при инициализации
        self.apply_saved_settings()

    def send_message(self):
        message = self.message_entry.get().strip()
        current_time = time.time()
        
        if not message:
            self.message_entry.delete(0, "end")
            return
        
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
        try:

            while True:
                message = self.client_socket.recv(2048).decode('utf-8')

                if message == "ERROR:BANNED":
                    self.root.after(0, self.show_ban_frame)
                    break

                elif message == "KICKED":
                    self.root.after(0, self.disconnect_from_server)
                    break

                elif message.startswith("USERS:"):
                    users = [user.strip() for user in message[6:].split(",") if user.strip()]
                    self.update_users_list(users)
                    continue
                elif message.startswith("HISTORY:"):
                    message_list = message.split("HISTORY:") # Избавляемся от всех заголовков History
                    
                    message = "\n".join(message_list)

                    history_messages = message.split("\n")
                    for msg in history_messages:
                        if msg.strip() and not msg.startswith(("USERS:", "users:")):
                            self.display_message(msg.strip(), is_new=False)

                    continue

                elif message.strip():  # Проверяем, что сообщение не пустое
                    self.display_message(message)
                
        except Exception as e:
            # messagebox.showerror("Ошибка", f"Ошибка при получении сообщения: {e}")
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

            if "USERS:" in text and not is_new:
                text = text.split("USERS:")[0]
            
            if not self.settings['show_seconds'] and timestamp.count(':') == 2:
                time_parts = timestamp[1:-2].split(':')
                timestamp = f"[{time_parts[0]}:{time_parts[1]}] "
            
            formatted_message = timestamp + text.strip()
        else:
            formatted_message = message.strip()
        
        self.message_display.insert("end", formatted_message)
        
        if self.settings['auto_scroll']:
            self.message_display.see("end")
            
        # self.message_display.configure(state='disabled')
        
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
                self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
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
        self.root.after(3000, self.clear_notification)

    def clear_notification(self):
        self.notification_label.configure(text="")

    def center_toplevel(self, window, width, height):
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()
        
        x = main_x + (main_width - width) // 2
        y = main_y + (main_height - height) // 2
        
        window.geometry(f'{width}x{height}+{x}+{y}')

    def open_settings(self):
        settings_window = ctk.CTkToplevel(self.root)
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
        text_scale.set(self.settings.get('text_scale', 0.5))
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
            text="SproutLine 2.0",
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
            with open(os.path.join("assets", "config", "settings.json"), "r", encoding='utf-8') as f:
                saved_settings = json.load(f)
                self.settings.update(saved_settings)
        except FileNotFoundError:
            self.save_settings()
        except json.JSONDecodeError:
            AlertFrame(self.root, "Файл настроек поврежден. Используются настройки по умолчанию.", False)
            self.save_settings()
            
    def save_settings(self):
        try:
            with open(os.path.join("assets", "config", "settings.json"), "w", encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            ErrorFrame(self.root, f"Ошибка при сохранении настроек: {e}", False)

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
            ("Чёрная", "black"),  # Добавляем новую тему в список
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
        """Применение темы"""

        if theme_name in self.themes:
            self.current_theme = theme_name
            theme = self.themes[theme_name]
            
            self.root.configure(fg_color=theme['bg'])
            
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
                hover_color=settings_button_hover,
                text_color=theme['accent']
            )
            
            self.disconnect_button.configure(
                fg_color=settings_button_color,
                hover_color=settings_button_hover,
                text_color=theme['accent']
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

        # # Очищаем текущее окно
        # for widget in self.root.winfo_children():
        #     widget.destroy()
        
        # Показываем фрейм бана
        BanFrame(self.root)

    def disconnect_from_server(self):
        self.connected = False
        self.client_socket.close()

        # Очищаем текущее окно
        #for widget in self.root.winfo_children():
         #   widget.destroy()

        # Показываем фрейм дисконнекта
        AlertFrame(self.root)
           

    def show_settings(self):
        settings_window = ctk.CTkToplevel(self.root)
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
            text="SproutLine 2.0",
            font=('Arial', 11),
            text_color='#888888'
        )
        version_label.pack(side="bottom", pady=5)

    def close_settings(self):
        """Закрыть окно настроек"""
        if hasattr(self, 'settings_window'):
            self.settings_window.destroy()
            delattr(self, 'settings_window')

    def check_connection_status(self):
        """Проверка статуса подключения и обновление GUI"""
        self.connected = check_internet_connection()
        if hasattr(self, 'profile_window'):
            # Обновляем статус в окне профиля
            for widget in self.profile_window.winfo_children():
                if isinstance(widget, ctk.CTkFrame):
                    for inner_frame in widget.winfo_children():
                        if isinstance(inner_frame, ctk.CTkFrame):
                            for label in inner_frame.winfo_children():
                                if isinstance(label, ctk.CTkLabel) and label.cget("text") in ["В сети", "Не в сети"]:
                                    label.configure(
                                        text="В сети" if self.connected else "Не в сети",
                                        text_color="#00ff88" if self.connected else "#ff3333"
                                    )
        # Проверяем статус каждые 5 секунд
        self.root.after(5000, self.check_connection_status)

    def show_private_messages(self):
        pass

def center_window(window, width, height):
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')




class InitClass():
    def __init__(self):
        self.root = ctk.CTk()
        self.root.after(0, self.ensure_directories_and_files)
        self.root.mainloop()

    def ensure_directories_and_files(self): # Проверяем и создаем необходимые директории и файлы
        """Создание необходимых директорий и файлов"""

        try:
            # Получаем путь к директории, где находится скрипт
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Создаем пути относительно директории скрипта
            assets_dir = os.path.join(base_dir, "assets")
            config_dir = os.path.join(assets_dir, "config")
            images_dir = os.path.join(assets_dir, "images")
            
            # Создаем директории
            os.makedirs(config_dir, exist_ok=True)
            os.makedirs(images_dir, exist_ok=True)
            
            # Обновляем пути к файлам
            user_data_path = os.path.join(config_dir, "user_data.json")
            servers_path = os.path.join(config_dir, "servers.json")
            settings_path = os.path.join(config_dir, "settings.json")
            
            # Создаем файлы если они не существуют
            if not os.path.exists(user_data_path):
                with open(user_data_path, "w", encoding='utf-8') as f:
                    json.dump({}, f)
                    
            if not os.path.exists(servers_path):
                with open(servers_path, "w", encoding='utf-8') as f:
                    json.dump([], f)
                    
            if not os.path.exists(settings_path):
                default_settings = {
                    'show_seconds': True,
                    'message_sound': True,
                    'auto_scroll': True,
                    'font_size': 14,
                    'text_scale': 1.0,
                    'show_join_leave': True,
                    'current_theme': 'dark'
                }
                with open(settings_path, "w", encoding='utf-8') as f:
                    json.dump(default_settings, f, indent=4, ensure_ascii=False)
                    
        except PermissionError:
            ErrorFrame(self.root, "Отказано в доступе. Попробуйте запустить программу от имени администратора.")
            sys.exit(1)
        except Exception as e:
            ErrorFrame(self.root, f"Не удалось создать необходимые файлы и директории: {str(e)}")
            sys.exit(1)
        
        self.root.destroy()
        ServerListWindow()

if __name__ == "__main__":
    InitClass()
