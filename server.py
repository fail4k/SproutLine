import hashlib
import socket
import threading
import time
import signal
import sys
from datetime import datetime
from threading import Lock, Semaphore
import sqlite3  
from questionary import select
import os

connection = sqlite3.connect('testDB.db', check_same_thread=False)
cursor = connection.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
username TEXT PRIMARY KEY,
password TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Banned_Users (
username TEXT PRIMARY KEY,
ip TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Admins (
username TEXT PRIMARY KEY
)
''')

MAX_NICKNAME_LENGTH = 20
SOCKET_TIMEOUT = 604800
clients_lock = Semaphore(2)
db_lock = Lock()
clients = {}
messages = []
admin = None  # Никнейм текущего админа

# --- Вспомогательные функции ---
def get_current_time():
    return datetime.now().strftime("%H:%M:%S")

def broadcast_message(message, sender_conn):
    def do_broadcast():
        with clients_lock:
            disconnected_clients = []
            for client in clients.copy():
                if client != sender_conn:
                    try:
                        client.send(message.encode('utf-8'))
                    except:
                        disconnected_clients.append(client)
            for client in disconnected_clients:
                remove(client)
    try:
        broadcast_thread = threading.Thread(target=do_broadcast, daemon=True)
        broadcast_thread.start()
        broadcast_thread.join(timeout=2.5)
    except Exception as e:
        print(f"Ошибка broadcast: {e}")

def send_system_message(client_socket, message):
    try:
        client_socket.send(message.encode('utf-8'))
    except Exception as e:
        print(f"Ошибка отправки системного сообщения: {e}")

def broadcast_users_list():
    time.sleep(1)
    if clients:
        users_list = "USERS:" + ",".join([name.strip() for name in clients.values()])
        try:
            broadcast_message(users_list, None)
        except Exception as e:
            print(f"Ошибка отправки системного сообщения со списком пользователей: {e}")

def wrap_message(message, max_width=70):
    if message.startswith('[') and '] ' in message:
        timestamp_end = message.find('] ') + 2
        timestamp = message[:timestamp_end]
        text = message[timestamp_end:]
        indent = ' ' * len(timestamp)
    else:
        timestamp = ''
        text = message
        indent = ''
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    for word in words:
        if current_length + len(word) + (1 if current_line else 0) <= max_width:
            if current_line:
                current_length += 1
            current_line.append(word)
            current_length += len(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_length = len(word)
    if current_line:
        lines.append(' '.join(current_line))
    if timestamp:
        result = timestamp + lines[0] if lines else timestamp
        if len(lines) > 1:
            result += '\n' + '\n'.join(indent + line for line in lines[1:])
    else:
        result = '\n'.join(lines)
    return result

def check_user_exists_db(username):
    with db_lock:
        try:
            cursor.execute('SELECT * FROM Users WHERE username = ?', (username,))
            user = cursor.fetchone()
            return True if user else False
        except Exception as e:
            print("Ошибка базы данных: ", e)

def auth_db(username, password):
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
    with db_lock:
        try:
            if ip:
                cursor.execute('SELECT * FROM Banned_Users WHERE ip = ?', (ip,))
            else:
                cursor.execute('SELECT * FROM Banned_Users WHERE username = ?', (username,))
            user = cursor.fetchone()
            return True if user else False
        except Exception as e:
            print("Ошибка базы данных: ", e)

def handle_client(client_socket, addr):
    message_cooldown = 2
    try:
        client_socket.settimeout(5.0)
        try:
            init_message = client_socket.recv(1024).decode('utf-8').strip()
            operation_type = init_message.split(";")[0]
            nickname = init_message.split(";")[1]
            password = hashlib.sha256(init_message.split(";")[2].encode("utf-8")).hexdigest()
            if check_is_banned(nickname, addr[0]):
                try:
                    send_system_message(client_socket, "ERROR:BANNED")
                except:
                    pass
                client_socket.close()
                return
            if operation_type == "R":
                if check_user_exists_db(nickname) == False:
                    with db_lock:
                        cursor.execute('INSERT INTO Users (username, password) VALUES (?, ?)', (nickname, password,))
                        connection.commit()
                    print("Добавлен пользователь: ", nickname)
                else:
                    print(f"Пользователь {nickname} уже существует")
                    send_system_message(client_socket, "ERROR:NICKNAME_TAKEN")
                    client_socket.close()
                    return
            elif operation_type == "L":
                if not auth_db(nickname, password):
                    print(f"Пользователь {nickname} не прошёл аутентефикацию")
                    send_system_message(client_socket, "ERROR:WRONG_PASSWORD")
                    client_socket.close()
                    return
            else:
                send_system_message(client_socket, "ERROR:WRONG_OPERATION")
                client_socket.close()
                return
            with clients_lock:
                if nickname in clients.values():
                    try:
                        send_system_message(client_socket, "ERROR:NICKNAME_ONLINE")
                    except:
                        pass
                    client_socket.close()
                    return
                clients[client_socket] = nickname
                users_list = "USERS:" + ",".join([name.strip() for name in clients.values()])
                send_system_message(client_socket, f"CCT:{message_cooldown};{users_list}")
        except socket.timeout:
            print("Ошибка подключения пользователя: ", "вышло время ожидания сокета")
            client_socket.close()
            return
        except Exception as e:
            print("Ошибка подключения пользователя: ", e)
            client_socket.close()
            return
        client_socket.settimeout(None)
        time.sleep(0.1)
        if messages:
            chunk_size = 10
            def send_history(messages, chunk_size):
                for i in range(0, len(messages), chunk_size):
                    chunk = messages[i:i + chunk_size]
                    history_message = "HISTORY:" + "\n".join(chunk) + "\n"
                    try:
                        send_system_message(client_socket, history_message)
                        time.sleep(0.1)
                    except Exception as e:
                        print(f"Ошибка при отправке истории: {str(e)}")
                        return
            send_history(messages, chunk_size)
        connect_message = f"[{get_current_time()}] {nickname} присоединился к чату"
        messages.append(connect_message)
        broadcast_message(connect_message + "\n", None)
        broadcast_users_list()
        last_message_time = 0
        max_message_length = 300
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8').strip()
                if not message:
                    print(f"Клиент {nickname} отключился (пустое сообщение)")
                    broadcast_users_list()
                    break
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
                if message.startswith(f"{nickname}: "):
                    message = message[len(f"{nickname}: ") :]
                timestamped_message = f"[{get_current_time()}] {nickname}: {message}"
                messages.append(timestamped_message)
                broadcast_message(timestamped_message + "\n", client_socket)
                if message.startswith("/"):
                    # Проверка на админа
                    with db_lock:
                        cursor.execute('SELECT username FROM Admins WHERE username = ?', (nickname,))
                        is_admin = cursor.fetchone() is not None
                    if not is_admin:
                        send_system_message(client_socket, f"[{get_current_time()}] {nickname}: Недостаточно прав для использования команд.\n")
                        continue
                    else:
                        command = message.split(" ")[0][1:]
                        if command == "kick":
                            user_to_kick = message.split(" ")[1]
                            if user_to_kick == nickname:
                                send_system_message(client_socket, f"[{get_current_time()}] {nickname}: Вы не можете кикнуть себя.\n")
                                continue
                            kick_user(user_to_kick)
                            result = f"[{get_current_time()}] {nickname}: User {user_to_kick} kicked."
                            send_system_message(client_socket, result)
                            # broadcast_message(result + "\n", client_socket)  # Больше не рассылаем всем
                            continue
                        elif command == "list_admins":
                            with db_lock:
                                cursor.execute('SELECT username FROM Admins')
                                admins = cursor.fetchall()
                                admins = [admin[0] for admin in admins]
                            result = f"[{get_current_time()}] System: Admins: {', '.join(admins)}"
                            send_system_message(client_socket, result)
                            # broadcast_message(result + "\n", client_socket)
                            continue
                        elif command == "list_banned":
                            with db_lock:
                                cursor.execute('SELECT username FROM Banned_Users')
                                banned_users = cursor.fetchall()
                                banned_users = [user[0] for user in banned_users]
                            result = f"[{get_current_time()}] System: Banned users: {', '.join(banned_users)}"
                            send_system_message(client_socket, result)
                            # broadcast_message(result + "\n", client_socket)
                            continue
                        elif command == "set_admin":
                            user_to_set_admin = message.split(" ")[1]
                            add_admin(user_to_set_admin)
                            result = f"[{get_current_time()}] {nickname}: User {user_to_set_admin} added as admin."
                            send_system_message(client_socket, result)
                            # broadcast_message(result + "\n", client_socket)
                            continue
                        elif command == "remove_admin":
                            remove_admin(message.split(" ")[1])
                            result = f"[{get_current_time()}] {nickname}: User {message.split(' ')[1]} removed from admins."
                            send_system_message(client_socket, result)
                            # broadcast_message(result + "\n", client_socket)
                            continue
                        elif command == "ban":
                            user_to_ban = message.split(" ")[1]
                            if user_to_ban == nickname:
                                send_system_message(client_socket, f"[{get_current_time()}] {nickname}: Вы не можете забанить себя.")
                                continue
                            ban_user(user_to_ban)
                            result = f"[{get_current_time()}] {nickname}: User {user_to_ban} banned."
                            send_system_message(client_socket, result)
                            # broadcast_message(result + "\n", client_socket)
                        elif command == "unban":
                            user_to_unban = message.split(" ")[1]
                            unban_user(user_to_unban)
                            result = f"[{get_current_time()}] {nickname}: User {user_to_unban} unbanned."
                            send_system_message(client_socket, result)
                            # broadcast_message(result + "\n", client_socket)
                        continue
            except Exception as e:
                print(f"Ошибка получения сообщения от {nickname}: {str(e)}")
                break
    except Exception as e:
        print(f"Критическая ошибка для {addr}: {str(e)}")
    finally:
        remove(client_socket)

def remove(client_socket):
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
        except Exception as e:
            print(f"Ошибка при удалении клиента: {e}")
    threading.Thread(target=do_remove, daemon=True).start()

def graceful_shutdown(signum, frame):
    print("\nЗавершение работы сервера...")
    with clients_lock:
        for client in clients.copy():
            send_system_message(client, "SERVER_SHUTDOWN")
            client.close()
    sys.exit(0)

def kick_user(nickname):
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
                remove(sock_to_ban)
        with db_lock:
            cursor.execute('INSERT INTO Banned_Users (username, ip) VALUES (?, ?)', (nickname, client_ip,))
            connection.commit()
        return True
    except Exception as e:
        print(f"Ошибка при бане пользователя {nickname}: {e}")
        return False

def unban_user(nickname):
    if check_is_banned(nickname):
        with db_lock:
            cursor.execute('DELETE FROM Banned_Users WHERE username = ?', (nickname,))
            connection.commit()
        return True
    return False

def add_admin(username):
    with db_lock:
        try:
            cursor.execute('INSERT OR IGNORE INTO Admins (username) VALUES (?)', (username,))
            connection.commit()
            return True
        except Exception as e:
            print(f"Ошибка при добавлении админа: {e}")
            return False

def remove_admin(username):
    with db_lock:
        try:
            cursor.execute('DELETE FROM Admins WHERE username = ?', (username,))
            connection.commit()
            return True
        except Exception as e:
            print(f"Ошибка при удалении админа: {e}")
            return False

def list_admins():
    with db_lock:
        cursor.execute('SELECT username FROM Admins')
        admins = cursor.fetchall()
        print("\nСписок админов:")
        for row in admins:
            print(f"- {row[0]}")
        print()

def list_users():
    with clients_lock:
        print("\nТекущие участники:")
        for nick in clients.values():
            print(f"- {nick}")
        print()

def list_banned():
    with db_lock:
        cursor.execute('SELECT * FROM Banned_Users')
        banned_users_list = cursor.fetchall()
        print("\nЗабаненные пользователи:")
        for row in banned_users_list:
            print(f"- {row[0]} (ip: {row[1]})")
        print()

def set_admin():
    global admin
    with clients_lock:
        print("\nВыберите никнейм для назначения админом:")
        nicks = list(clients.values())
        for i, nick in enumerate(nicks):
            print(f"{i+1}. {nick}")
        idx = input("Введите номер пользователя: ")
        try:
            idx = int(idx) - 1
            if 0 <= idx < len(nicks):
                admin = nicks[idx]
                print(f"Пользователь {admin} назначен админом.\n")
            else:
                print("Некорректный номер.\n")
        except:
            print("Ошибка ввода.\n")

def save_chat_history():
    try:
        with open("chat.txt", "w", encoding="utf-8") as f:
            for message in messages:
                f.write(f"{message}\n")
        print("История чата сохранена в chat.txt\n")
    except Exception as e:
        print(f"Ошибка при сохранении истории чата: {e}\n")

def show_history():
    print("\n===== История сообщений =====")
    if not messages:
        print("История пуста.")
    else:
        for msg in messages:
            print(msg)
    print("============================\n")

def server_command_loop():
    while True:
        main_options = [
            "Users",
            "Admins",
            "Chat",
            "Exit"
        ]
        main_cmd = select("Select category:", choices=main_options).ask()
        os.system('cls' if os.name == 'nt' else 'clear')
        if main_cmd == "Users":
            while True:
                user_options = [
                    "List users",
                    "Kick user",
                    "Ban user",
                    "Unban user",
                    "List banned users",
                    "Back"
                ]
                user_cmd = select("User actions:", choices=user_options).ask()
                os.system('cls' if os.name == 'nt' else 'clear')
                if user_cmd == "List users":
                    list_users()
                elif user_cmd == "Kick user":
                    with clients_lock:
                        nicks = list(clients.values())
                    if not nicks:
                        print("No active users.\n")
                        continue
                    for i, nick in enumerate(nicks):
                        print(f"{i+1}. {nick}")
                    idx = input("Enter the number of the user to kick: ")
                    try:
                        idx = int(idx) - 1
                        if 0 <= idx < len(nicks):
                            kick_user(nicks[idx])
                            print(f"User {nicks[idx]} kicked.\n")
                        else:
                            print("Invalid number.\n")
                    except:
                        print("Input error.\n")
                elif user_cmd == "Ban user":
                    with clients_lock:
                        nicks = list(clients.values())
                    if not nicks:
                        print("No active users.\n")
                        continue
                    for i, nick in enumerate(nicks):
                        print(f"{i+1}. {nick}")
                    idx = input("Enter the number of the user to ban: ")
                    try:
                        idx = int(idx) - 1
                        if 0 <= idx < len(nicks):
                            ban_user(nicks[idx])
                            print(f"User {nicks[idx]} banned.\n")
                        else:
                            print("Invalid number.\n")
                    except:
                        print("Input error.\n")
                elif user_cmd == "Unban user":
                    with db_lock:
                        cursor.execute('SELECT * FROM Banned_Users')
                        banned_users_list = cursor.fetchall()
                    if not banned_users_list:
                        print("No banned users.\n")
                        continue
                    for i, row in enumerate(banned_users_list):
                        print(f"{i+1}. {row[0]}")
                    idx = input("Enter the number of the user to unban: ")
                    try:
                        idx = int(idx) - 1
                        if 0 <= idx < len(banned_users_list):
                            unban_user(banned_users_list[idx][0])
                            print(f"User {banned_users_list[idx][0]} unbanned.\n")
                        else:
                            print("Invalid number.\n")
                    except:
                        print("Input error.\n")
                elif user_cmd == "List banned users":
                    list_banned()
                elif user_cmd == "Back":
                    break
        elif main_cmd == "Admins":
            while True:
                admin_options = [
                    "Add admin",
                    "Remove admin",
                    "List admins",
                    "Back"
                ]
                admin_cmd = select("Admin actions:", choices=admin_options).ask()
                os.system('cls' if os.name == 'nt' else 'clear')
                if admin_cmd == "Add admin":
                    with clients_lock:
                        nicks = list(clients.values())
                    if not nicks:
                        print("No active users.\n")
                        continue
                    for i, nick in enumerate(nicks):
                        print(f"{i+1}. {nick}")
                    idx = input("Enter the number of the user to add as admin: ")
                    try:
                        idx = int(idx) - 1
                        if 0 <= idx < len(nicks):
                            add_admin(nicks[idx])
                            print(f"User {nicks[idx]} added as admin.\n")
                        else:
                            print("Invalid number.\n")
                    except:
                        print("Input error.\n")
                elif admin_cmd == "Remove admin":
                    with db_lock:
                        cursor.execute('SELECT username FROM Admins')
                        admins = cursor.fetchall()
                    if not admins:
                        print("No admins to remove.\n")
                        continue
                    for i, row in enumerate(admins):
                        print(f"{i+1}. {row[0]}")
                    idx = input("Enter the number of the admin to remove: ")
                    try:
                        idx = int(idx) - 1
                        if 0 <= idx < len(admins):
                            remove_admin(admins[idx][0])
                            print(f"User {admins[idx][0]} removed from admins.\n")
                        else:
                            print("Invalid number.\n")
                    except:
                        print("Input error.\n")
                elif admin_cmd == "List admins":
                    list_admins()
                elif admin_cmd == "Back":
                    break
        elif main_cmd == "Chat":
            while True:
                chat_options = [
                    "Show history",
                    "Save chat history",
                    "Back"
                ]
                chat_cmd = select("Chat actions:", choices=chat_options).ask()
                os.system('cls' if os.name == 'nt' else 'clear')
                if chat_cmd == "Show history":
                    show_history()
                elif chat_cmd == "Save chat history":
                    save_chat_history()
                elif chat_cmd == "Back":
                    break
        elif main_cmd == "Exit":
            graceful_shutdown(None, None)
        else:
            print("Неизвестная команда.\n")

def start_server():
    print("=== SproutLine Server ===")
    host = input("Введите IP-адрес (по умолчанию 127.0.0.1): ").strip() or "127.0.0.1"
    while True:
        port_str = input("Введите порт (1024-65535, по умолчанию 1604): ").strip() or "1604"
        try:
            port = int(port_str)
            if 1024 <= port <= 65535:
                break
            else:
                print("Порт вне диапазона.")
        except:
            print("Некорректный порт.")
    global HOST, PORT
    HOST, PORT = host, port
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        print(f"Сервер запущен на {HOST}:{PORT}\n")
        def accept_connections():
            while True:
                try:
                    client_socket, addr = server_socket.accept()
                    client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True).start()
                except Exception as e:
                    print(f"Ошибка при принятии подключения: {e}")
                    continue
        accept_thread = threading.Thread(target=accept_connections, daemon=True)
        accept_thread.start()
        server_command_loop()
    except Exception as e:
        print(f"Ошибка запуска сервера: {str(e)}")
        return

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    start_server() 
