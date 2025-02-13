import socket
import threading
import time
import signal
import sys
from datetime import datetime
from threading import Lock

HOST = '127.0.0.1'
PORT = 1604
MAX_NICKNAME_LENGTH = 20
SOCKET_TIMEOUT = 604800
clients_lock = Lock()

clients = {}  # Словарь {сокет: никнейм}
messages = []

def get_current_time():
    return datetime.now().strftime("%H:%M:%S")

def broadcast_message(message, sender_conn):
    with clients_lock:
        disconnected_clients = []
        for client in clients:
            if client != sender_conn:
                try:
                    client.send(message.encode('utf-8'))
                except Exception as e:
                    print(f"Ошибка отправки сообщения: {str(e)}")
                    disconnected_clients.append(client)
    
        for client in disconnected_clients:
            remove(client)

def send_system_message(client_socket, message):
    """Отправка системного сообщения конкретному клиенту"""
    try:
        # Добавляем символ новой строки к системному сообщению
        client_socket.send((message + "\n").encode('utf-8'))
    except Exception:
        remove(client_socket)

def broadcast_users_list():
    with clients_lock:  # Добавляем блокировку для безопасного доступа к clients
        if clients:
            users_list = "USERS:" + ",".join([name.strip() for name in clients.values()])
            for client in clients.copy():  # Используем copy() для избежания ошибок при изменении словаря
                try:
                    send_system_message(client, users_list)
                except Exception:
                    remove(client)

def update_users_periodically():
    while True:
        broadcast_users_list()
        time.sleep(1)  # Обновляем каждую секунду

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

def handle_client(client_socket, addr):
    try:
        client_socket.settimeout(SOCKET_TIMEOUT)
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 16384)
        
        try:
            nickname = client_socket.recv(1024).decode('utf-8').strip()
            if not nickname or len(nickname) > MAX_NICKNAME_LENGTH:
                send_system_message(client_socket, "ERROR:INVALID_NICKNAME")
                return
                
            with clients_lock:
                if nickname in clients.values():
                    send_system_message(client_socket, "ERROR:NICKNAME_TAKEN")
                    return
                clients[client_socket] = nickname
        except Exception as e:
            print(f"Ошибка при получении никнейма от {addr}: {str(e)}")
            return
            
        print(f"Подключен клиент: {nickname} ({addr})")
        
        # Отправляем историю сообщений
        if messages:
            for msg in messages:
                # Проверяем, что сообщение не является системным
                if not msg.startswith(("USERS:", "users:")):
                    try:
                        client_socket.send(f"{msg}\n".encode('utf-8'))
                    except Exception as e:
                        print(f"Ошибка при отправке истории: {str(e)}")
                        break
        
        connect_message = f"[{get_current_time()}] {nickname} присоединился к чату"
        messages.append(connect_message)
        broadcast_message(connect_message + "\n", None)
        
        last_message_time = 0
        message_cooldown = 3
        max_message_length = 300
        
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8').strip()
                if not message:
                    print(f"Клиент {nickname} отключился (пустое сообщение)")
                    break

                # Игнорируем системные сообщения от клиентов
                if message.startswith("USERS:"):
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
                
                # Форматируем сообщение с переносом по словам
                formatted_message = wrap_message(message)
                timestamped_message = f"[{get_current_time()}] {formatted_message}"
                
                print(timestamped_message)
                messages.append(timestamped_message)
                broadcast_message(timestamped_message + "\n", client_socket)
                
            except UnicodeDecodeError as e:
                print(f"Ошибка декодирования от {nickname}: {str(e)}")
                continue
            except Exception as e:
                print(f"Ошибка получения сообщения от {nickname}: {str(e)}")
                break

    except Exception as e:
        print(f"Критическая ошибка для {addr}: {str(e)}")
    finally:
        remove(client_socket)

def remove(client_socket):
    if client_socket in clients:
        nickname = clients[client_socket]
        del clients[client_socket]
        client_socket.close()
        
        disconnect_message = f"[{get_current_time()}] {nickname} покинул чат"
        broadcast_message(disconnect_message, None)
        messages.append(disconnect_message)

def graceful_shutdown(signum, frame):
    """Корректное завершение работы сервера"""
    print("\nЗавершение работы сервера...")
    with clients_lock:
        for client in clients.copy():
            send_system_message(client, "SERVER_SHUTDOWN")
            client.close()
    sys.exit(0)

def start_server():
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        print("Сервер запущен и ожидает подключения...")
    except Exception as e:
        print(f"Ошибка запуска сервера: {str(e)}")
        return

    # Запускаем поток обновления списка пользователей
    update_thread = threading.Thread(target=update_users_periodically)
    update_thread.daemon = True  # Поток завершится вместе с основной программой
    update_thread.start()

    while True:
        client_socket, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket, addr)).start()

if __name__ == "__main__":
    start_server()