import hashlib
import socket
import threading
import time
import signal
import sys
from datetime import datetime
from threading import Lock, Semaphore
import customtkinter as ctk
import sqlite3
connection = sqlite3.connect('testDB.db', check_same_thread=False) # Грузим БД из файла
cursor = connection.cursor() # Курсор - интерфейс взаимодействия с БД

cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
username TEXT PRIMARY KEY,
password TEXT NOT NULL
)
''') # Создаем таблицу пользователей, ник у каждого уникальный, поэтому задается как ключ, защита от создания существующего пользователя на уровне БД

cursor.execute('''
CREATE TABLE IF NOT EXISTS Banned_Users (
username TEXT PRIMARY KEY,
ip TEXT
)
''') # Создаем таблицу забаненных пользователей c ником и ip адресом (адрес не обязателен)

MAX_NICKNAME_LENGTH = 20
SOCKET_TIMEOUT = 604800
# clients_lock = Lock()
clients_lock = Semaphore(2) # Заменил замок на семафор, обеспечивая работу двух потоков одновременно без блокирования данных
db_lock = Lock() # Замок для безопасного доступа к БД

clients = {}  # Словарь {сокет: никнейм}
messages = []

# Добавляем глобальные переменные
server_gui = None  # Ссылка на GUI сервера

# Глобальные переменные, связанные с баном, упразднены из-за появления БД с забаннеными пользователями
# banned_users = set()  # Множество забаненных никнеймов
# banned_ips = set()  # Множество забаненных IP-адресов
# banned_users_ips = {}  # {nickname: ip_address}


def get_current_time():
    return datetime.now().strftime("%H:%M:%S")

def broadcast_message(message, sender_conn):

    def do_broadcast():
        with clients_lock:
            disconnected_clients = []
            for client in clients.copy():  # Используем copy() для избежания ошибок при изменении словаря
                if client != sender_conn:
                    try:
                        client.send(message.encode('utf-8'))
                    except:
                        disconnected_clients.append(client)
            
            # Удаляем отключившихся клиентов
            for client in disconnected_clients:
                remove(client)
    
    try:
        # Запускаем рассылку в отдельном потоке
        broadcast_thread = threading.Thread(target=do_broadcast, daemon=True)
        broadcast_thread.start()
        broadcast_thread.join(timeout=2.5) # Уменьшаем таймаут до 2.5 секунд

    except Exception as e:
        print(f"Ошибка broadcast: {e}")

    # Обновляем GUI через очередь событий
    if server_gui:
        server_gui.root.after(100, server_gui.update_chat_history)

def send_system_message(client_socket, message):
    """Отправка системного сообщения клиенту"""
    try:
        client_socket.send(message.encode('utf-8'))
    except Exception as e:
        print(f"Ошибка отправки системного сообщения: {e}")

def broadcast_users_list():
    # with clients_lock:  # Добавляем блокировку для безопасного доступа к clients
        time.sleep(1)
        if clients:
            users_list = "USERS:" + ",".join([name.strip() for name in clients.values()])
            # for client in clients.copy():  # Используем copy() для избежания ошибок при изменении словаря
            try:
                broadcast_message(users_list, None)
                # client.send(users_list.encode('utf-8'))
            except Exception as e:
                print(f"Ошибка отправки системного сообщения со списком пользователей: {e}")

# def update_users_periodically():
#     global broadcast_lock 
#     broadcast_lock = False

#     while True:
#         time.sleep(2.5)  # Ждем согласно указанному времени ожидания
#         if not broadcast_lock:
#             broadcast_users_list()

def wrap_message(message, max_width=70):
    """Форматирует сообщение с переносом по словам"""
    # Разделяем сообщение на временную метку и текст
    if message.startswith('[') and '] ' in message:
        timestamp_end = message.find('] ') + 2
        timestamp = message[:timestamp_end]
        text = message[timestamp_end:]
        # Учитываем отступ для выравнивания текста под временной меткой
        indent = ' ' * len(timestamp)
    else:
        timestamp = ''
        text = message
        indent = ''

    # Разбиваем текст на слова
    words = text.split()
    lines = []
    current_line = []
    current_length = 0

    for word in words:
        if current_length + len(word) + (1 if current_line else 0) <= max_width:
            if current_line:
                current_length += 1  # Пробел
            current_line.append(word)
            current_length += len(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_length = len(word)

    if current_line:
        lines.append(' '.join(current_line))

    # Собираем результат с учетом временной метки
    if timestamp:
        result = timestamp + lines[0] if lines else timestamp
        if len(lines) > 1:
            result += '\n' + '\n'.join(indent + line for line in lines[1:])
    else:
        result = '\n'.join(lines)

    return result

def check_user_exists_db(username):
    """Проверяем: есть ли уже такой пользователь в БД"""

    with db_lock:
        try:
            cursor.execute('SELECT * FROM Users WHERE username = ?', (username,))
            user = cursor.fetchone()
            return True if user else False
        except Exception as e:
            print("Ошибка базы данных: ", e)

def auth_db(username, password):
    """Проводим аутентефикацию пользователя"""

    with db_lock:
        try:
            cursor.execute('SELECT * FROM Users WHERE username = ?', (username,))
            user = cursor.fetchone()
            if user:
                if user[1] == password:
                    return True
                else:
                    return False
            else:
                return False
        except Exception as e:
            print("Ошибка базы данных: ", e)

def check_is_banned(username, ip=None):
    """Проводим проверку пользователя на наличие бана на сервере по нику или ip"""

    with db_lock:
        try:
            if ip: # Если есть ip, то нет смысла проверять по нику
                cursor.execute('SELECT * FROM Banned_Users WHERE ip = ?', (ip,))
            else:
                cursor.execute('SELECT * FROM Banned_Users WHERE username = ?', (username,))
            user = cursor.fetchone()
            return True if user else False
        except Exception as e:
            print("Ошибка базы данных: ", e)


def handle_client(client_socket, addr):
    """Обработка клиента"""

    message_cooldown = 3 # Указываем время кулдауна между сообщениями

    try:
        # Устанавливаем таймаут для сокета
        client_socket.settimeout(5.0)  # 5 секунд для начальной авторизации

        try: 
            init_message = client_socket.recv(1024).decode('utf-8').strip() # Получаем инициализационное сообщение от пользвоателя по следующему контракту: <тип операции (регистрация или вход в аккаунт)><имя_пользователя>;<пароль>
            operation_type = init_message.split(";")[0]
            nickname = init_message.split(";")[1]
            password = hashlib.sha256(init_message.split(";")[2].encode("utf-8")).hexdigest()

            # Проверяем на наличие бана
            if check_is_banned(nickname, addr[0]):
                try:
                    send_system_message(client_socket, "ERROR:BANNED")
                except:
                    pass
                client_socket.close()
                return

            if operation_type == "R": # Регистрация
                if check_user_exists_db(nickname) == False: # Только если позователя нет
                    with db_lock:
                        cursor.execute('INSERT INTO Users (username, password) VALUES (?, ?)', (nickname, password,)) # Добавляем нашего пользователя
                        connection.commit() # Применяем изменения в БД
                    print("Добавлен пользователь: ", nickname)
                else:
                    print(f"Пользователь {nickname} уже существует")
                    send_system_message(client_socket, "ERROR:NICKNAME_TAKEN")
                    client_socket.close()
                    return

            elif operation_type == "L": # Вход в аккаунт                
                if not auth_db(nickname, password):
                    print(f"Пользователь {nickname} не прошёл аутентефикацию")
                    send_system_message(client_socket, "ERROR:WRONG_PASSWORD")
                    client_socket.close()
                    return

            else:
                send_system_message(client_socket, "ERROR:WRONG_OPERATION")
                client_socket.close()
                return

            # Проверка на на онлайн: если аккаунт уже в чате, но с ещё одного входа не пустит
            with clients_lock:
                if nickname in clients.values():
                    try:
                        send_system_message(client_socket, "ERROR:NICKNAME_ONLINE")
                    except:
                        pass

                    client_socket.close()
                    return
                    
                # Добавление клиента
                clients[client_socket] = nickname
                
                users_list = "USERS:" + ",".join([name.strip() for name in clients.values()]) # Получаем список пользователей
                send_system_message(client_socket, f"CCT:{message_cooldown};{users_list}") # Отправляем время кд между сообщениями и список пользователей


        except socket.timeout:
            print("Ошибка подключения пользователя: ", "вышло время ожидания сокета")
            client_socket.close()
            return
        except Exception as e:
            print("Ошибка подключения пользователя: ", e)
            client_socket.close()
            return
            
        # После получения никнейма убираем таймаут
        client_socket.settimeout(None)

        # Обновляем GUI в главном потоке
        if server_gui:
            server_gui.root.after(0, server_gui.update_users_list)
            server_gui.root.after(0, server_gui.update_chat_history)

        # Даем клиенту время на инициализацию
        time.sleep(0.1)

        # Отправляем историю частями
        if messages:
            chunk_size = 10  # Отправляем по 10 сообщений

            def send_history(messages, chunk_size): # Создаем блокирующуя функцию отправки истории
                for i in range(0, len(messages), chunk_size):
                    chunk = messages[i:i + chunk_size]
                    history_message = "HISTORY:" + "\n".join(chunk) + "\n"
                    try:
                        send_system_message(client_socket, history_message)
                        # client_socket.send(history_message.encode('utf-8'))
                        time.sleep(0.1)  # Небольшая пауза между чанками

                    except Exception as e:
                        print(f"Ошибка при отправке истории: {str(e)}")
                        return

            
            send_history(messages, chunk_size)
        
        # Отправляем сообщение о подключении
        connect_message = f"[{get_current_time()}] {nickname} присоединился к чату"
        messages.append(connect_message)
        broadcast_message(connect_message + "\n", None)
        broadcast_users_list()

        # Начинаем обработку сообщений
        last_message_time = 0
        max_message_length = 300
        
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8').strip()
                if not message:
                    print(f"Клиент {nickname} отключился (пустое сообщение)")
                    broadcast_users_list()
                    break

                # Игнорируем системные сообщения и сам ник
                if message.startswith(("USERS:", "HISTORY:")) or message == nickname:
                    continue

                current_time = time.time()
                time_since_last = current_time - last_message_time

                if len(message) > max_message_length:
                    send_system_message(client_socket, "ERROR:LENGTH")
                    continue
                
                if time_since_last < message_cooldown:
                    send_system_message(client_socket, f"ERROR:COOLDOWN:{int(message_cooldown - time_since_last)}")
                    continue

                last_message_time = current_time
                
                # Убираем повторение ника из сообщения если оно начинается с него
                if message.startswith(f"{nickname}: "):
                    message = message[len(f"{nickname}: "):]
                
                timestamped_message = f"[{get_current_time()}] {nickname}: {message}"
                print(timestamped_message)
                messages.append(timestamped_message)
                broadcast_message(timestamped_message + "\n", client_socket)
                
            except Exception as e:
                print(f"Ошибка получения сообщения от {nickname}: {str(e)}")
                break

    except Exception as e:
        print(f"Критическая ошибка для {addr}: {str(e)}")
    finally:
        remove(client_socket)

def remove(client_socket):
    """Безопасное удаление клиента"""
    def do_remove():
        try:
            with clients_lock:
                if client_socket in clients:
                    nickname = clients[client_socket]
                    del clients[client_socket]
                    try:
                        client_socket.close()
                    except:
                        pass
                    
                    disconnect_message = f"[{get_current_time()}] {nickname} покинул чат"
                    messages.append(disconnect_message)
                    broadcast_message(disconnect_message + "\n", None)
                    broadcast_users_list()
                    
                    # Обновляем GUI через очередь событий
                    if server_gui:
                        server_gui.root.after(100, server_gui.update_users_list)
                        server_gui.root.after(100, server_gui.update_chat_history)
        except Exception as e:
            print(f"Ошибка при удалении клиента: {e}")
    
    # Запускаем удаление в отдельном потоке
    threading.Thread(target=do_remove, daemon=True).start()

def graceful_shutdown(signum, frame):
    """Корректное завершение работы сервера"""
    print("\nЗавершение работы сервера...")
    with clients_lock:
        for client in clients.copy():
            send_system_message(client, "SERVER_SHUTDOWN")
            client.close()
    sys.exit(0)

def kick_user(nickname):
    """Кикнуть пользователя по никнейму"""
    with clients_lock:
        for sock, nick in clients.items():
            if nick == nickname:
                try:
                    send_system_message(sock, "KICKED")
                    remove(sock)
                except:
                    pass
                break
    return True

def ban_user(nickname):
    """Забанить пользователя по никнейму"""
    try:
        with clients_lock:
            sock_to_ban = None
            client_ip = None
            for sock, nick in clients.items():
                if nick == nickname:
                    sock_to_ban = sock
                    try:
                        client_ip = sock.getpeername()[0]
                    except:
                        pass
                    break
            
            if sock_to_ban:
                try:
                    send_system_message(sock_to_ban, "ERROR:BANNED")
                except:
                    pass
                
                # Удаляем клиента через remove() вместо прямого удаления
                remove(sock_to_ban)
        
        with db_lock:
            cursor.execute('INSERT INTO Banned_Users (username, ip) VALUES (?, ?)', (nickname, client_ip,)) # Добавляем нашего забаненного пользователя
            connection.commit() # Применяем изменения в БД
        return True
    except Exception as e:
        print(f"Ошибка при бане пользователя {nickname}: {e}")
        return False

def unban_user(nickname):
    """Разбанить пользователя"""
    if check_is_banned(nickname):
        with db_lock:
            cursor.execute('DELETE FROM Banned_Users WHERE username = ?', (nickname,)) # Удаляем нашего забаненного пользователя
            connection.commit() # Применяем изменения в БД

        # # Удаляем IP из banned_ips если он был связан с этим пользователем
        # if nickname in banned_users_ips:
        #     ip = banned_users_ips[nickname]
        #     if ip in banned_ips:
        #         banned_ips.remove(ip)
        #     del banned_users_ips[nickname]
        return True
    return False

# def ban_ip(ip):
#     """Забанить IP-адрес"""
#     def do_ban():
#         try:
#             banned_ips.add(ip)  # Добавляем IP в список забаненных
#             with clients_lock:
#                 for sock in list(clients.keys()):
#                     try:
#                         if sock.getpeername()[0] == ip:
#                             send_system_message(sock, "ERROR:BANNED")  # Уведомляем клиента о бане
#                             remove(sock)  # Удаляем клиента
#                     except Exception as e:
#                         print(f"Ошибка при проверке IP: {e}")
            
#             # Обновляем GUI в главном потоке
#             server_gui.root.after(0, lambda: server_gui.show_notification(f"IP {ip} забанен", 'success'))
#             server_gui.root.after(0, server_gui.update_users_list)
#             server_gui.root.after(0, server_gui.update_banned_list)
            
#         except Exception as e:
#             server_gui.root.after(0, lambda: server_gui.show_notification(f"Ошибка при бане: {str(e)}", 'error'))
    
#     # Запускаем бан в отдельном потоке
#     ban_thread = threading.Thread(target=do_ban, daemon=True)
#     ban_thread.start()

def change_nickname(client_socket, new_nickname):
    """Смена никнейма пользователя"""
    with clients_lock:
        if new_nickname in clients.values():
            send_system_message(client_socket, "ERROR:NICKNAME_TAKEN")
            return False
        
        old_nickname = clients[client_socket]
        clients[client_socket] = new_nickname
        
        # Уведомляем всех о смене никнейма
        message = f"[{get_current_time()}] {old_nickname} сменил ник на {new_nickname}"
        broadcast_message(message + "\n", client_socket)
        
        return True

class UserSelectionDialog:
    def __init__(self, parent_gui, title, users, action_type):
        self.dialog = ctk.CTkToplevel(parent_gui.root)
        self.dialog.title(title)
        self.dialog.geometry("300x400")
        self.dialog.resizable(False, False)
        
        # Делаем окно модальным
        self.dialog.transient(parent_gui.root)
        self.dialog.wait_visibility()
        self.dialog.grab_set()
        self.dialog.focus_force()
        
        # Центрируем окно относительно родителя
        x = parent_gui.root.winfo_x() + (parent_gui.root.winfo_width() - 300) // 2
        y = parent_gui.root.winfo_y() + (parent_gui.root.winfo_height() - 400) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # Используем тему из parent_gui
        self.theme = parent_gui.theme
        self.dialog.configure(fg_color=self.theme['bg'])
        
        # Заголовок
        title_label = ctk.CTkLabel(
            self.dialog,
            text=title,
            font=("Arial Bold", 14),
            text_color=self.theme['accent']
        )
        title_label.pack(pady=10)
        
        # Фрейм для чекбоксов
        self.checkbox_frame = ctk.CTkScrollableFrame(
            self.dialog,
            fg_color=self.theme['frame_bg'],
            width=250,
            height=280
        )
        self.checkbox_frame.pack(pady=10, padx=20)
        
        # Создаем чекбоксы для каждого пользователя
        self.checkboxes = {}
        for user in users:
            checkbox = ctk.CTkCheckBox(
                self.checkbox_frame,
                text=user,
                font=("Arial", 12),
                text_color=self.theme['text'],
                fg_color=self.theme['accent'],
                hover_color=self.theme['accent'],
                checkbox_width=20,
                checkbox_height=20
            )
            checkbox.pack(pady=5, padx=10, anchor="w")
            self.checkboxes[user] = checkbox
        
        # Кнопки
        button_text = "Разбанить" if action_type == "unban" else "Кикнуть"
        
        self.action_button = ctk.CTkButton(
            self.dialog,
            text=button_text,
            command=self.on_action,
            fg_color=self.theme['button'],
            hover_color=self.theme['button_hover'],
            text_color=self.theme['text']
        )
        self.action_button.pack(pady=10)
        
        self.cancel_button = ctk.CTkButton(
            self.dialog,
            text="Отмена",
            command=self.on_cancel,
            fg_color=self.theme['button'],
            hover_color=self.theme['button_hover'],
            text_color=self.theme['text']
        )
        self.cancel_button.pack(pady=5)
        
        self.result = None
    
    def on_action(self):
        selected = [user for user, checkbox in self.checkboxes.items() if checkbox.get()]
        if selected:
            self.result = selected[0]  # Берем первого выбранного пользователя
        self.dialog.destroy()
    
    def on_cancel(self):
        self.dialog.destroy()
    
    def show(self):
        self.dialog.wait_window()
        return self.result

class BanDialog:
    def __init__(self, parent_gui, users):
        self.dialog = ctk.CTkToplevel(parent_gui.root)
        self.dialog.title("Бан пользователя")
        self.dialog.geometry("300x400")
        self.dialog.resizable(False, False)
        
        # Делаем окно модальным
        self.dialog.transient(parent_gui.root)
        self.dialog.wait_visibility()
        self.dialog.grab_set()
        self.dialog.focus_force()
        
        # Центрируем окно
        x = parent_gui.root.winfo_x() + (parent_gui.root.winfo_width() - 300) // 2
        y = parent_gui.root.winfo_y() + (parent_gui.root.winfo_height() - 400) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        self.theme = parent_gui.theme
        self.dialog.configure(fg_color=self.theme['bg'])
        
        # Заголовок
        title_label = ctk.CTkLabel(
            self.dialog,
            text="Бан пользователя",
            font=("Arial Bold", 14),
            text_color=self.theme['accent']
        )
        title_label.pack(pady=10)
        
        # Фрейм для чекбоксов пользователей
        self.checkbox_frame = ctk.CTkScrollableFrame(
            self.dialog,
            fg_color=self.theme['frame_bg'],
            width=250,
            height=280
        )
        self.checkbox_frame.pack(pady=10, padx=20)
        
        # Создаем чекбоксы для каждого пользователя
        self.checkboxes = {}
        for user in users:
            checkbox = ctk.CTkCheckBox(
                self.checkbox_frame,
                text=user,
                font=("Arial", 12),
                text_color=self.theme['text'],
                fg_color=self.theme['accent'],
                hover_color=self.theme['accent'],
                checkbox_width=20,
                checkbox_height=20
            )
            checkbox.pack(pady=5, padx=10, anchor="w")
            self.checkboxes[user] = checkbox
        
        # Кнопки
        self.action_button = ctk.CTkButton(
            self.dialog,
            text="Забанить",
            command=self.on_action,
            fg_color=self.theme['button'],
            hover_color=self.theme['button_hover'],
            text_color=self.theme['text']
        )
        self.action_button.pack(pady=10)
        
        self.cancel_button = ctk.CTkButton(
            self.dialog,
            text="Отмена",
            command=self.on_cancel,
            fg_color=self.theme['button'],
            hover_color=self.theme['button_hover'],
            text_color=self.theme['text']
        )
        self.cancel_button.pack(pady=5)
        
        self.result = None
    
    def on_action(self):
        selected = [user for user, checkbox in self.checkboxes.items() if checkbox.get()]
        if selected:
            user = selected[0]
            self.result = user
        self.dialog.destroy()
    
    def on_cancel(self):
        self.dialog.destroy()
    
    def show(self):
        self.dialog.wait_window()
        return self.result

class ServerGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("SproutLine Server")
        self.root.geometry("1000x500")
        self.root.resizable(False, False)
        
        # Обновленная тема
        self.theme = {
            'bg': '#0A0A0A',
            'frame_bg': '#141414',
            'text': '#E0E0E0',
            'accent': '#00CC66',
            'button': '#1A1A1A',
            'button_hover': '#252525',
            'error': '#FF4444',
            'success': '#00CC66',
            'secondary_text': '#888888'
        }
        
        self.setup_gui()
        
        # Запускаем периодическое обновление GUI
        self.root.after(1000, self.update_gui)
        
        global server_gui
        server_gui = self
        
    def setup_gui(self):
        # Настраиваем цвет фона основного окна
        self.root.configure(fg_color=self.theme['bg'])
        
        # Основной контейнер с отступами
        main_frame = ctk.CTkFrame(self.root, fg_color=self.theme['bg'])
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)  # Уменьшили отступы
        
        # Левая панель (чат) - 70% ширины
        left_panel = ctk.CTkFrame(main_frame, fg_color=self.theme['frame_bg'])
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))  # Уменьшили отступ справа
        
        # История чата
        chat_frame = ctk.CTkFrame(left_panel, fg_color=self.theme['frame_bg'])
        chat_frame.pack(fill="both", expand=True, pady=5, padx=8)
        
        chat_label = ctk.CTkLabel(
            chat_frame,
            text="История чата",
            font=("Arial Bold", 14),
            text_color=self.theme['accent']
        )
        chat_label.pack(pady=5)
        
        self.chat_display = ctk.CTkTextbox(
            chat_frame,
            wrap="word",
            fg_color=self.theme['button'],
            text_color=self.theme['text'],
            font=("Arial", 12),
            state="disabled"  # Делаем поле только для чтения
        )
        self.chat_display.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        # Кнопка сохранения истории
        save_button = ctk.CTkButton(
            left_panel,
            text="💾 Сохранить историю чата",
            command=self.save_chat_history,
            fg_color=self.theme['button'],
            hover_color=self.theme['button_hover'],
            text_color=self.theme['text'],
            font=("Arial", 12)
        )
        save_button.pack(pady=(0, 8), padx=8, fill="x")
        
        # Статус бар для уведомлений
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="✅ Сервер работает",
            font=("Arial", 12),
            text_color=self.theme['accent']
        )
        self.status_label.pack(side="bottom", pady=5)
        
        # Правая панель (пользователи и баны) - 30% ширины
        right_panel = ctk.CTkFrame(main_frame, fg_color=self.theme['frame_bg'])
        right_panel.pack(side="right", fill="both", padx=(8, 0))
        
        # Активные пользователи
        users_frame = ctk.CTkFrame(right_panel, fg_color=self.theme['frame_bg'])
        users_frame.pack(fill="both", pady=5, padx=8)
        
        users_label = ctk.CTkLabel(
            users_frame,
            text="👥 Активные пользователи",
            font=("Arial Bold", 14),
            text_color=self.theme['accent']
        )
        users_label.pack(pady=5)
        
        self.users_list = ctk.CTkTextbox(
            users_frame,
            fg_color=self.theme['button'],
            text_color=self.theme['text'],
            font=("Arial", 12),
            height=120,
            state="disabled"
        )
        self.users_list.pack(fill="x", pady=(0, 5))
        
        # Кнопки управления
        controls_frame = ctk.CTkFrame(right_panel, fg_color=self.theme['frame_bg'])
        controls_frame.pack(fill="x", pady=5, padx=8)
        
        kick_button = ctk.CTkButton(
            controls_frame,
            text="🚫 Кикнуть",
            command=self.kick_selected_user,
            fg_color=self.theme['button'],
            hover_color=self.theme['button_hover'],
            text_color=self.theme['text'],
            font=("Arial", 12)
        )
        kick_button.pack(pady=(0, 2), fill="x")
        
        ban_button = ctk.CTkButton(
            controls_frame,
            text="⛔ Забанить",
            command=self.ban_selected_user,
            fg_color=self.theme['button'],
            hover_color=self.theme['button_hover'],
            text_color=self.theme['text'],
            font=("Arial", 12)
        )
        ban_button.pack(pady=(0, 5), fill="x")
        
        # Забаненные пользователи
        banned_frame = ctk.CTkFrame(right_panel, fg_color=self.theme['frame_bg'])
        banned_frame.pack(fill="x", pady=(0, 5), padx=8)
        
        banned_label = ctk.CTkLabel(
            banned_frame,
            text="🚫 Забаненные пользователи",
            font=("Arial Bold", 14),
            text_color=self.theme['accent']
        )
        banned_label.pack(pady=5)
        
        self.banned_list = ctk.CTkTextbox(
            banned_frame,
            fg_color=self.theme['button'],
            text_color=self.theme['text'],
            font=("Arial", 12),
            height=80,
            state="disabled"  # Делаем поле только для чтения
        )
        self.banned_list.pack(fill="x", pady=(0, 5))
        
        # Кнопка разбана
        unban_button = ctk.CTkButton(
            banned_frame,
            text="✅ Разблокировать",
            command=self.unban_selected_user,
            fg_color=self.theme['button'],
            hover_color=self.theme['button_hover'],
            text_color=self.theme['text'],
            font=("Arial", 12)
        )
        unban_button.pack(pady=(0, 5), fill="x")
    
    def update_gui(self):
        """Периодическое обновление GUI"""
        try:
            self.root.after(1000, self.update_gui)  # Планируем следующее обновление сразу
            self.update_users_list()
            self.update_banned_list()
            self.update_chat_history()
        except Exception as e:
            print(f"Ошибка обновления GUI: {e}")
        
    def update_users_list(self):
        """Обновление списка активных пользователей"""
        try:
            self.users_list.configure(state="normal")
            self.users_list.delete("1.0", "end")
            with clients_lock:
                for nickname in clients.values():
                    self.users_list.insert("end", f"{nickname}\n")
            self.users_list.configure(state="disabled")
        except Exception as e:
            print(f"Ошибка обновления списка пользователей: {e}")
        
    def update_banned_list(self):
        """Обновление списка забаненных пользователей"""
        try:
            self.banned_list.configure(state="normal")
            self.banned_list.delete("1.0", "end")

            # Получаем всех забаненных пользователей из БД
            with db_lock:
                cursor.execute('SELECT * FROM Banned_Users')
            banned_users_list = cursor.fetchall()
            banned_users = []
            if banned_users_list:
                for i in banned_users_list:
                    banned_users.append(i[0])
            
            # Добавляем людей в бане из БД в локальную переменную
            if banned_users:
                for nickname in banned_users:
                    self.banned_list.insert("end", f"{nickname}\n")
            self.banned_list.configure(state="disabled")
        except Exception as e:
            print(f"Ошибка обновления списка забаненных пользователей: {e}")
        
    def update_chat_history(self):
        """Обновление истории чата"""
        self.chat_display.configure(state="normal")  # Временно разрешаем запись
        self.chat_display.delete("1.0", "end")
        for message in messages:
            self.chat_display.insert("end", f"{message}\n")
        self.chat_display.configure(state="disabled")  # Возвращаем только для чтения
        self.chat_display.see("end")  # Прокручиваем к последнему сообщению
        
    def get_selected_user(self, widget):
        """Получение выбранного пользователя из текстового виджета"""
        try:
            cursor_pos = widget.index("insert")
            line_start = cursor_pos.split('.')[0] + '.0'
            line_end = cursor_pos.split('.')[0] + '.end'
            selected_line = widget.get(line_start, line_end).strip()
            return selected_line
        except Exception as e:
            print(f"Ошибка при получении выбранного пользователя: {e}")
            return None
        
    def kick_selected_user(self):
        """Кикнуть выбранного пользователя"""
        with clients_lock:
            users = list(clients.values())
        
        if not users:
            self.show_notification("Нет активных пользователей", 'error')
            return
        
        dialog = UserSelectionDialog(self, "Кик пользователя", users, "kick")
        selected_user = dialog.show()
        
        if selected_user:
            def do_kick():
                if kick_user(selected_user):
                    self.show_notification(f"Пользователь {selected_user} кикнут", 'success')
                    # self.root.after(0, lambda: self.show_notification(f"Пользователь {selected_user} кикнут", 'success'))
                else:
                    self.show_notification(f"Не удалось кикнуть пользователя {selected_user}", 'error')
                    # self.root.after(0, lambda: self.show_notification(f"Не удалось кикнуть пользователя {selected_user}", 'error'))
            
            # Запускаем кик в отдельном потоке
            threading.Thread(target=do_kick, daemon=True).start()
    
    def ban_selected_user(self):
        """Забанить выбранного пользователя"""
        try:
            with clients_lock:
                users = list(clients.values())  # Получаем список активных пользователей
                
            if not users:
                self.show_notification("Нет активных пользователей", 'error')
                return
                
            dialog = UserSelectionDialog(self, "Забанить пользователя", users, "ban")
            selected_user = dialog.show()
            
            if selected_user:
                def do_ban():
                    if ban_user(selected_user):
                        self.root.after(0, lambda: self.show_notification(f"Пользователь {selected_user} забанен", 'success'))
                        self.root.after(0, self.update_banned_list)  # Обновляем список забаненных
                    else:
                        self.root.after(0, lambda: self.show_notification(f"Не удалось забанить пользователя {selected_user}", 'error'))
                
                # Запускаем бан в отдельном потоке
                threading.Thread(target=do_ban, daemon=True).start()
        
        except Exception as e:
            self.show_notification(f"Ошибка: {str(e)}", 'error')
    
    def unban_selected_user(self):
        """Разбанить выбранного пользователя"""

        # Получаем всех забаненных пользователей из БД
        with db_lock:
            cursor.execute('SELECT * FROM Banned_Users')
        banned_users_list = cursor.fetchall()
        banned_users = []
        if banned_users_list:
            for i in banned_users_list:
                banned_users.append(i[0])

        if not banned_users:
            self.show_notification("Нет забаненных пользователей", 'error')
            return
        
        dialog = UserSelectionDialog(self, "Разбан пользователя", list(banned_users), "unban")
        selected_user = dialog.show()
        
        if selected_user:
            def do_unban():
                if unban_user(selected_user):
                    self.root.after(0, lambda: self.show_notification(f"Пользователь {selected_user} разбанен", 'success'))
                    self.root.after(0, self.update_banned_list)
                else:
                    self.root.after(0, lambda: self.show_notification(f"Не удалось разбанить пользователя {selected_user}", 'error'))
            
            # Запускаем разбан в отдельном потоке
            threading.Thread(target=do_unban, daemon=True).start()
    
    def show_notification(self, message, type_='info'):
        """Показать уведомление"""
        try:
            if hasattr(self, 'status_label'):
                color = self.theme['success'] if type_ == 'success' else self.theme['error']
                self.status_label.configure(text=message, text_color=color)
                self.root.after(3000, lambda: self.status_label.configure(
                    text="✅ Сервер работает",
                    text_color=self.theme['accent']
                ))
            else:
                print(f"Уведомление: {message}")
        except Exception as e:
            print(f"Ошибка отображения уведомления: {e}")
    
    def save_chat_history(self):
        """Сохранить историю чата в файл"""
        try:
            with open("chat.txt", "w", encoding="utf-8") as f:
                for message in messages:
                    f.write(f"{message}\n")
            self.show_notification("История чата сохранена в chat.txt", 'success')
        except Exception as e:
            self.show_notification(f"Ошибка при сохранении истории чата: {e}", 'error')
            
    def run(self):
        """Запуск GUI"""
        self.root.mainloop()

class ServerStartDialog:
    def __init__(self):
        self.dialog = ctk.CTk()
        self.dialog.title("Запуск сервера SproutLine")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        
        self.theme = {
            'bg': '#0A0A0A',
            'frame_bg': '#141414',
            'text': '#E0E0E0',
            'accent': '#00CC66',
            'button': '#1A1A1A',
            'button_hover': '#252525',
            'error': '#FF4444',
            'success': '#00CC66',
            'secondary_text': '#888888'
        }
        
        self.dialog.configure(fg_color=self.theme['bg'])
        
        # Логотип или заголовок
        logo_label = ctk.CTkLabel(
            self.dialog,
            text="🌱 SproutLine",
            font=("Arial Bold", 24),
            text_color=self.theme['accent']
        )
        logo_label.pack(pady=10)
        
        description = ctk.CTkLabel(
            self.dialog,
            text="Настройка сервера",
            font=("Arial", 14),
            text_color=self.theme['text']
        )
        description.pack(pady=(0, 10))
        
        # Основной фрейм для настроек
        settings_frame = ctk.CTkFrame(
            self.dialog,
            fg_color=self.theme['frame_bg'],
            height=180  # Немного уменьшили высоту фрейма
        )
        settings_frame.pack(padx=30, pady=5, fill="x")
        settings_frame.pack_propagate(False)
        
        # IP адрес
        ip_label = ctk.CTkLabel(
            settings_frame,
            text="IP адрес:",
            font=("Arial", 12),
            text_color=self.theme['text']
        )
        ip_label.pack(padx=25, pady=(10), anchor="w")
        
        self.ip_entry = ctk.CTkEntry(
            settings_frame,
            placeholder_text="127.0.0.1",
            font=("Arial", 12),
            fg_color=self.theme['button'],
            text_color=self.theme['text'],
            border_color=self.theme['accent']
        )
        self.ip_entry.pack(padx=25, pady=(0, 20), fill="x")
        self.ip_entry.insert(0, "127.0.0.1")
        
        # Порт
        port_label = ctk.CTkLabel(
            settings_frame,
            text="Порт:",
            font=("Arial", 12),
            text_color=self.theme['text']
        )
        port_label.pack(padx=25, pady=(0, 5), anchor="w")
        
        self.port_entry = ctk.CTkEntry(
            settings_frame,
            placeholder_text="1604",
            font=("Arial", 12),
            fg_color=self.theme['button'],
            text_color=self.theme['text'],
            border_color=self.theme['accent']
        )
        self.port_entry.pack(padx=25, pady=(0, 25), fill="x")
        self.port_entry.insert(0, "1604")
        
        # Статус
        self.status_label = ctk.CTkLabel(
            self.dialog,
            text="",
            font=("Arial", 12),
            text_color=self.theme['error']
        )
        self.status_label.pack(pady=10)
        
        # Кнопка запуска
        self.start_button = ctk.CTkButton(
            self.dialog,
            text="Запустить сервер",
            command=self.start_server,
            font=("Arial Bold", 14),
            fg_color=self.theme['accent'],
            hover_color="#00AA55",
            height=40,
            width=200
        )
        self.start_button.pack(pady=(5, 15))
        
        self.result = None
    
    def validate_input(self):
        ip = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()
        
        # Проверка IP
        try:
            socket.inet_aton(ip)
        except socket.error:
            self.status_label.configure(text="Некорректный IP адрес")
            return False
        
        # Проверка порта
        try:
            port = int(port)
            if not (1024 <= port <= 65535):
                self.status_label.configure(text="Порт должен быть между 1024 и 65535")
                return False
        except ValueError:
            self.status_label.configure(text="Некорректный порт")
            return False
        
        return True
    
    def start_server(self):
        if self.validate_input():
            self.result = (self.ip_entry.get().strip(), int(self.port_entry.get().strip()))
            self.dialog.quit()
    
    def show(self):
        self.dialog.mainloop()
        self.dialog.destroy()
        return self.result

def start_server():
    # Показываем диалог настройки
    dialog = ServerStartDialog()
    result = dialog.show()
    
    if not result:
        return
    
    global HOST, PORT
    HOST, PORT = result
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        print(f"Сервер запущен на {HOST}:{PORT}")
        
        # Создаем и запускаем GUI в основном потоке
        gui = ServerGUI()
        
        # Функция для принятия подключений в отдельном потоке
        def accept_connections():
            while True:
                try:
                    client_socket, addr = server_socket.accept()
                    client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    # Запускаем обработку клиента в отдельном потоке
                    threading.Thread(target=handle_client, 
                                  args=(client_socket, addr),
                                  daemon=True).start()
                except Exception as e:
                    print(f"Ошибка при принятии подключения: {e}")
                    continue
        
        # Запускаем прием подключений в отдельном потоке
        accept_thread = threading.Thread(target=accept_connections, daemon=True)
        accept_thread.start()
        
        # Запускаем поток обновления списка пользователей
        # update_thread = threading.Thread(target=update_users_periodically, daemon=True)
        # update_thread.start()
        
        # Запускаем GUI в основном потоке
        gui.run()
            
    except Exception as e:
        print(f"Ошибка запуска сервера: {str(e)}")
        return

if __name__ == "__main__":
    start_server() 
