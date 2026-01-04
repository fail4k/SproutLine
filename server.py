import hashlib
import socket
import threading
import time
import signal
import sys
from datetime import datetime, timezone, timedelta
from threading import Lock, Semaphore
import sqlite3
from questionary import select
import os
import base64
from PIL import Image
import io


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
client_timezones = {}
client_timezones_lock = Lock()
messages = []
messages_lock = Lock()
admin = None
suppress_console_output = False
typing_lock = Lock()
typing_users = set()

def safe_print(*args, **kwargs):
    if not suppress_console_output:
        print(*args, **kwargs)

def get_current_time():
    return datetime.now().strftime('%H:%M:%S')

def get_current_time_utc():
    return datetime.now(timezone.utc).strftime('%H:%M:%S')

def convert_time_to_timezone(time_str, timezone_offset_hours):
    try:
        time_parts = time_str.split(':')
        if len(time_parts) != 3:
            return time_str
        hours = int(time_parts[0])
        minutes = int(time_parts[1])
        seconds = int(time_parts[2])
        now_utc = datetime.now(timezone.utc)
        utc_time = now_utc.replace(hour=hours, minute=minutes, second=seconds, microsecond=0)
        local_time = utc_time + timedelta(hours=timezone_offset_hours)
        return local_time.strftime('%H:%M:%S')
    except Exception as e:
        safe_print(f'Ошибка конвертации времени: {e}')
        return time_str

def broadcast_message(message, sender_conn):

    def do_broadcast():
        with clients_lock:
            clients_to_send = [c for c in clients.copy() if c != sender_conn]
        with client_timezones_lock:
            timezones_copy = client_timezones.copy()
        disconnected_clients = []
        for client in clients_to_send:
            try:
                adjusted_message = message
                if message.startswith('[') and '] ' in message:
                    time_end = message.find('] ')
                    time_str = message[1:time_end]
                    client_tz = timezones_copy.get(client, 0)
                    adjusted_time = convert_time_to_timezone(time_str, client_tz)
                    adjusted_message = f'[{adjusted_time}]{message[time_end + 1:]}'
                data = adjusted_message.encode('utf-8')
                data_len = len(data)
                total_sent = 0
                while total_sent < data_len:
                    try:
                        sent = client.send(data[total_sent:])
                        if sent == 0:
                            raise ConnectionError('Socket connection broken')
                        total_sent += sent
                    except (socket.error, ConnectionError, OSError, BrokenPipeError):
                        disconnected_clients.append(client)
                        break
            except (socket.error, ConnectionError, OSError, BrokenPipeError):
                disconnected_clients.append(client)
        if disconnected_clients:
            with clients_lock:
                for client in disconnected_clients:
                    if client in clients:
                        remove(client)
    try:
        broadcast_thread = threading.Thread(target=do_broadcast, daemon=True)
        broadcast_thread.start()
    except Exception as e:
        safe_print(f'Ошибка broadcast: {e}')

def send_system_message(client_socket, message):
    try:
        data = message.encode('utf-8')
        total_sent = 0
        while total_sent < len(data):
            try:
                sent = client_socket.send(data[total_sent:])
                if sent == 0:
                    raise ConnectionError('Socket connection broken')
                total_sent += sent
            except (socket.error, ConnectionError, OSError, BrokenPipeError) as e:
                safe_print(f'Ошибка отправки системного сообщения: {e}')
                with clients_lock:
                    if client_socket in clients:
                        remove(client_socket)
                raise
    except Exception as e:
        safe_print(f'Ошибка отправки системного сообщения: {e}')

def broadcast_users_list():
    if clients:
        users_list = 'USERS:' + ','.join([name.strip() for name in clients.values()])
        try:
            broadcast_message(users_list + '\n', None)
        except Exception as e:
            safe_print(f'Ошибка отправки системного сообщения со списком пользователей: {e}')

def broadcast_typing_users():
    with clients_lock, typing_lock:
        if not clients:
            return
        if typing_users:
            users_str = ','.join(sorted(typing_users))
        else:
            users_str = ''
        message = f'TYPING_USERS:{users_str}\n'
    try:
        broadcast_message(message, None)
    except Exception as e:
        safe_print(f'Ошибка отправки списка печатающих пользователей: {e}')

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
            result += '\n' + '\n'.join((indent + line for line in lines[1:]))
    else:
        result = '\n'.join(lines)
    return result

def check_user_exists_db(username):
    with db_lock:
        try:
            cursor.execute('SELECT 1 FROM Users WHERE username = ? LIMIT 1', (username,))
            return cursor.fetchone() is not None
        except Exception as e:
            safe_print('Ошибка базы данных: ', e)
            return False

def auth_db(username, password):
    with db_lock:
        try:
            cursor.execute('SELECT password FROM Users WHERE username = ? LIMIT 1', (username,))
            result = cursor.fetchone()
            return result is not None and result[0] == password
        except Exception as e:
            safe_print('Ошибка базы данных: ', e)
            return False

def check_is_banned(username, ip=None):
    with db_lock:
        try:
            if ip:
                cursor.execute('SELECT 1 FROM Banned_Users WHERE ip = ? LIMIT 1', (ip,))
            else:
                cursor.execute('SELECT 1 FROM Banned_Users WHERE username = ? LIMIT 1', (username,))
            return cursor.fetchone() is not None
        except Exception as e:
            safe_print('Ошибка базы данных: ', e)
            return False

def compress_image(img_b64_data, max_size_mb=1, max_dimension=960, quality=50, min_size_to_compress_kb=300):
    try:
        img_bytes = base64.b64decode(img_b64_data)
        size_mb = len(img_bytes) / (1024 * 1024)
        size_kb = len(img_bytes) / 1024
        if size_mb > max_size_mb:
            return None
        if size_kb < min_size_to_compress_kb:
            return img_b64_data
        img = Image.open(io.BytesIO(img_bytes))
        original_format = img.format or 'JPEG'
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        width, height = img.size
        if width > max_dimension or height > max_dimension:
            if width > height:
                new_width = max_dimension
                new_height = int(height * (max_dimension / width))
            else:
                new_height = max_dimension
                new_width = int(width * (max_dimension / height))
            img = img.resize((new_width, new_height), Image.LANCZOS)
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        compressed_bytes = output.getvalue()
        compressed_size_mb = len(compressed_bytes) / (1024 * 1024)
        max_target_size_mb = 0.2
        if compressed_size_mb > max_target_size_mb:
            for attempt_quality in [40, 30, 25]:
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=attempt_quality, optimize=True)
                test_bytes = output.getvalue()
                test_size_mb = len(test_bytes) / (1024 * 1024)
                if test_size_mb <= max_target_size_mb:
                    compressed_bytes = test_bytes
                    compressed_size_mb = test_size_mb
                    break
            if compressed_size_mb > max_target_size_mb:
                current_width, current_height = img.size
                if current_width > 720 or current_height > 720:
                    if current_width > current_height:
                        new_width = 720
                        new_height = int(current_height * (720 / current_width))
                    else:
                        new_height = 720
                        new_width = int(current_width * (720 / current_height))
                    img = img.resize((new_width, new_height), Image.LANCZOS)
                    for attempt_quality in [35, 30, 25]:
                        output = io.BytesIO()
                        img.save(output, format='JPEG', quality=attempt_quality, optimize=True)
                        test_bytes = output.getvalue()
                        test_size_mb = len(test_bytes) / (1024 * 1024)
                        if test_size_mb <= max_target_size_mb:
                            compressed_bytes = test_bytes
                            compressed_size_mb = test_size_mb
                            break
        compressed_b64 = base64.b64encode(compressed_bytes).decode('ascii')
        return compressed_b64
    except Exception as e:
        safe_print(f'✗ Ошибка при сжатии изображения: {e}')
        import traceback
        safe_print(traceback.format_exc())
        return None

def handle_client(client_socket, addr):
    try:
        client_socket.settimeout(5.0)
        try:
            init_message = client_socket.recv(1024).decode('utf-8').strip()
            parts = init_message.split(';')
            operation_type = parts[0]
            nickname = parts[1]
            password = hashlib.sha256(parts[2].encode('utf-8')).hexdigest()
            timezone_offset = 0
            if len(parts) > 3:
                try:
                    timezone_offset = int(parts[3])
                except (ValueError, IndexError):
                    timezone_offset = 0
            with client_timezones_lock:
                client_timezones[client_socket] = timezone_offset
            if check_is_banned(nickname, addr[0]):
                try:
                    send_system_message(client_socket, 'ERROR:BANNED')
                except:
                    pass
                client_socket.close()
                return
            if operation_type == 'R':
                if check_user_exists_db(nickname) == False:
                    with db_lock:
                        cursor.execute('INSERT INTO Users (username, password) VALUES (?, ?)', (nickname, password))
                        connection.commit()
                    safe_print('Добавлен пользователь: ', nickname)
                else:
                    safe_print(f'Пользователь {nickname} уже существует')
                    send_system_message(client_socket, 'ERROR:NICKNAME_TAKEN')
                    client_socket.close()
                    return
            elif operation_type == 'L':
                if not auth_db(nickname, password):
                    safe_print(f'Пользователь {nickname} не прошёл аутентефикацию')
                    send_system_message(client_socket, 'ERROR:WRONG_PASSWORD')
                    client_socket.close()
                    return
            else:
                send_system_message(client_socket, 'ERROR:WRONG_OPERATION')
                client_socket.close()
                return
            with clients_lock:
                existing_socket = None
                for sock, nick in clients.items():
                    if nick == nickname:
                        existing_socket = sock
                        break
                if existing_socket is not None:
                    is_active = False
                    try:
                        if existing_socket in clients:
                            existing_socket.settimeout(0.1)
                            existing_socket.getpeername()
                            existing_socket.settimeout(None)
                            is_active = True
                    except (socket.error, OSError, AttributeError):
                        if existing_socket in clients:
                            remove(existing_socket)
                    if is_active:
                        try:
                            send_system_message(client_socket, 'ERROR:NICKNAME_ONLINE')
                        except:
                            pass
                        client_socket.close()
                        return
                initial_users = [name.strip() for name in clients.values()]
                initial_users.append(nickname.strip())
                initial_users_list = 'USERS:' + ','.join(initial_users)
            send_system_message(client_socket, f'CCT:0;{initial_users_list}')
        except socket.timeout:
            safe_print('Ошибка подключения пользователя: ', 'вышло время ожидания сокета')
            client_socket.close()
            return
        except Exception as e:
            safe_print('Ошибка подключения пользователя: ', e)
            client_socket.close()
            return
        client_socket.settimeout(None)
        if messages:
            chunk_size = 10

            def send_history(messages, chunk_size):
                with client_timezones_lock:
                    client_tz = client_timezones.get(client_socket, 0)
                for i in range(0, len(messages), chunk_size):
                    chunk = messages[i:i + chunk_size]
                    adjusted_chunk = []
                    for msg in chunk:
                        if msg.startswith('[') and '] ' in msg:
                            time_end = msg.find('] ')
                            time_str = msg[1:time_end]
                            adjusted_time = convert_time_to_timezone(time_str, client_tz)
                            adjusted_msg = f'[{adjusted_time}]{msg[time_end + 1:]}'
                            adjusted_chunk.append(adjusted_msg)
                        else:
                            adjusted_chunk.append(msg)
                    history_message = 'HISTORY:' + '\n'.join(adjusted_chunk) + '\n'
                    try:
                        send_system_message(client_socket, history_message)
                    except Exception as e:
                        safe_print(f'Ошибка при отправке истории: {str(e)}')
                        return
            send_history(messages, chunk_size)
        try:
            send_system_message(client_socket, 'HISTORY_END\n')
        except Exception as e:
            safe_print(f'Ошибка при отправке завершения истории: {str(e)}')
            return
        with clients_lock:
            clients[client_socket] = nickname
            users_list = 'USERS:' + ','.join([name.strip() for name in clients.values()])
        send_system_message(client_socket, users_list + '\n')
        connect_message = f'[{get_current_time_utc()}] {nickname} присоединился к чату'

        def add_connect_to_history():
            try:
                with messages_lock:
                    messages.append(connect_message)
            except Exception as e:
                safe_print(f'Ошибка добавления в историю: {e}')
        threading.Thread(target=add_connect_to_history, daemon=True).start()
        broadcast_message(connect_message + '\n', None)
        broadcast_users_list()
        buffer = ''
        MAX_BUFFER_SIZE = 10 * 1024 * 1024
        while True:
            try:
                try:
                    data = client_socket.recv(65536)
                except (socket.error, OSError, ConnectionResetError, ConnectionAbortedError) as e:
                    safe_print(f'Клиент {nickname} отключился: {e}')
                    break
                except Exception as e:
                    safe_print(f'Ошибка получения данных от {nickname}: {e}')
                    break
                if not data:
                    safe_print(f'Клиент {nickname} отключился (пустое сообщение)')
                    break
                try:
                    chunk = data.decode('utf-8')
                except UnicodeDecodeError:
                    safe_print(f'Ошибка декодирования сообщения от {nickname}')
                    continue
                chunk_len = len(chunk)
                if len(buffer) + chunk_len > MAX_BUFFER_SIZE:
                    safe_print(f'Буфер переполнен для клиента {nickname}, очищаем')
                    buffer = ''
                    continue
                buffer += chunk
                while '\n' in buffer:
                    raw_line, buffer = buffer.split('\n', 1)
                    message = raw_line.strip()
                    if not message:
                        continue
                    if len(message) > 10000:
                        safe_print(f'Получено большое сообщение от {nickname}, размер: {len(message)} символов')
                    if message.startswith('CHANGE_NICKNAME:'):
                        new_nickname = message[len('CHANGE_NICKNAME:'):].strip()
                        if len(new_nickname) < 3 or len(new_nickname) > MAX_NICKNAME_LENGTH:
                            send_system_message(client_socket, 'ERROR:NICKNAME_INVALID\n')
                            continue
                        with clients_lock:
                            if new_nickname in clients.values() and new_nickname != nickname:
                                send_system_message(client_socket, 'ERROR:NICKNAME_TAKEN\n')
                                continue
                        with db_lock:
                            cursor.execute('SELECT username FROM Users WHERE username = ?', (new_nickname,))
                            if cursor.fetchone() is not None and new_nickname != nickname:
                                send_system_message(client_socket, 'ERROR:NICKNAME_TAKEN\n')
                                continue
                        old_nickname = nickname
                        with db_lock:
                            cursor.execute('UPDATE Users SET username = ? WHERE username = ?', (new_nickname, old_nickname))
                            connection.commit()
                        with clients_lock:
                            clients[client_socket] = new_nickname
                        send_system_message(client_socket, 'SUCCESS:NICKNAME_CHANGED\n')
                        broadcast_users_list()
                        nickname_change_message = f'[{get_current_time_utc()}] {old_nickname} изменил никнейм на {new_nickname}'

                        def add_nickname_change_to_history():
                            try:
                                with messages_lock:
                                    messages.append(nickname_change_message)
                            except Exception as e:
                                safe_print(f'Ошибка добавления в историю: {e}')
                        threading.Thread(target=add_nickname_change_to_history, daemon=True).start()
                        broadcast_message(nickname_change_message + '\n', None)
                        nickname = new_nickname
                        continue
                    if message.startswith('CHANGE_PASSWORD:'):
                        parts = message[len('CHANGE_PASSWORD:'):].strip().split(';')
                        if len(parts) != 2:
                            send_system_message(client_socket, 'ERROR:INVALID_FORMAT\n')
                            continue
                        old_password_hash = parts[0].strip()
                        new_password_hash = parts[1].strip()
                        with db_lock:
                            cursor.execute('SELECT password FROM Users WHERE username = ?', (nickname,))
                            result = cursor.fetchone()
                            if result and result[0] != old_password_hash:
                                send_system_message(client_socket, 'ERROR:WRONG_PASSWORD\n')
                                continue
                            cursor.execute('UPDATE Users SET password = ? WHERE username = ?', (new_password_hash, nickname))
                            connection.commit()
                        send_system_message(client_socket, 'SUCCESS:PASSWORD_CHANGED\n')
                        continue
                    if message.startswith('TYPING:'):
                        state = message[len('TYPING:'):].strip()
                        is_typing = state == '1'
                        with typing_lock:
                            if is_typing:
                                typing_users.add(nickname)
                            else:
                                typing_users.discard(nickname)
                        threading.Thread(target=broadcast_typing_users, daemon=True).start()
                        continue
                    if message.startswith(('USERS:', 'HISTORY:')) or message == nickname:
                        continue
                    original_message = message
                    if message.startswith(f'{nickname}: '):
                        message = message[len(f'{nickname}: '):]
                    if not message:
                        safe_print(f'Предупреждение: пустое сообщение от {nickname} после обработки')
                        continue
                    is_image = message.startswith('IMG:')
                    if is_image:
                        safe_print(f'📷 Изображение от {nickname}')
                        try:
                            parts = message.split(':', 2)
                            if len(parts) == 3:
                                prefix, filename, img_b64 = parts
                                img_size_bytes = len(img_b64) * 3 / 4
                                img_size_mb = img_size_bytes / (1024 * 1024)
                                safe_print(f'  └─ Файл: {filename}, размер: {img_size_mb:.2f} МБ')
                                if img_size_mb > 1.0:
                                    safe_print(f'  └─ ❌ Слишком большое (максимум 1 МБ)')
                                    send_system_message(client_socket, 'ERROR:IMAGE_TOO_LARGE\n')
                                    continue
                                img_size_kb = img_size_mb * 1024
                                if img_size_kb >= 300:
                                    safe_print(f'  └─ 🔄 Сжимаем (размер: {img_size_kb:.1f} КБ)')
                                    compressed_b64 = compress_image(img_b64, max_size_mb=1.0, max_dimension=960, quality=50, min_size_to_compress_kb=300)
                                    if compressed_b64 is None:
                                        safe_print(f'  └─ ❌ Ошибка обработки')
                                        send_system_message(client_socket, 'ERROR:IMAGE_PROCESSING_FAILED\n')
                                        continue
                                    if compressed_b64 != img_b64:
                                        old_size = len(message)
                                        message = f'IMG:{filename}:{compressed_b64}'
                                        new_size = len(message)
                                        compressed_size_mb = len(compressed_b64) * 3 / 4 / (1024 * 1024)
                                        safe_print(f'  └─ ✅ Сжато: {img_size_mb:.2f} → {compressed_size_mb:.2f} МБ ({(old_size - new_size) / old_size * 100:.1f}%)')
                                    else:
                                        safe_print(f'  └─ ✓ Размер уже оптимальный, сжатие не требуется')
                                else:
                                    safe_print(f'  └─ ✓ Размер небольшой ({img_size_kb:.1f} КБ), сжатие не требуется')
                            else:
                                safe_print(f'  └─ ❌ Неверный формат')
                                send_system_message(client_socket, 'ERROR:IMAGE_PROCESSING_FAILED\n')
                                continue
                        except Exception as e:
                            safe_print(f'  └─ ❌ Ошибка: {e}')
                            send_system_message(client_socket, 'ERROR:IMAGE_PROCESSING_FAILED\n')
                            continue
                    if is_image:
                        try:
                            parts = message.split(':', 2)
                            if len(parts) == 3:
                                _, filename, img_b64 = parts
                                img_size_kb = len(img_b64) * 3 / 4 / 1024
                                log_message = f'IMG:{filename} ({img_size_kb:.1f} КБ)'
                            else:
                                log_message = 'IMG:[изображение]'
                        except:
                            log_message = 'IMG:[изображение]'
                        timestamped_message = f'[{get_current_time_utc()}] {nickname}: {message}'
                        timestamped_log = f'[{get_current_time()}] {nickname}: {log_message}'
                    else:
                        timestamped_message = f'[{get_current_time_utc()}] {nickname}: {message}'
                        timestamped_log = timestamped_message

                    def add_to_history_async(msg):
                        try:
                            with messages_lock:
                                messages.append(msg)
                        except Exception as e:
                            safe_print(f'Ошибка добавления в историю: {e}')
                    threading.Thread(target=add_to_history_async, args=(timestamped_message,), daemon=True).start()
                    safe_print(timestamped_log)
                    if is_image:
                        try:
                            with client_timezones_lock:
                                sender_tz = client_timezones.get(client_socket, 0)
                            adjusted_message_for_sender = timestamped_message
                            if timestamped_message.startswith('[') and '] ' in timestamped_message:
                                time_end = timestamped_message.find('] ')
                                time_str = timestamped_message[1:time_end]
                                adjusted_time = convert_time_to_timezone(time_str, sender_tz)
                                adjusted_message_for_sender = f'[{adjusted_time}]{timestamped_message[time_end + 1:]}'
                            send_system_message(client_socket, adjusted_message_for_sender + '\n')
                            safe_print(f'✅ Сжатое изображение отправлено отправителю {nickname}')
                        except Exception as e:
                            safe_print(f'⚠️ Ошибка отправки сжатого изображения отправителю: {e}')
                        broadcast_message(timestamped_message + '\n', client_socket)
                    else:
                        broadcast_message(timestamped_message + '\n', client_socket)
                if message.startswith('/'):
                    with db_lock:
                        cursor.execute('SELECT username FROM Admins WHERE username = ?', (nickname,))
                        is_admin = cursor.fetchone() is not None
                    if not is_admin:
                        send_system_message(client_socket, f'[{get_current_time()}] {nickname}: Недостаточно прав для использования команд.\n')
                        continue
                    else:
                        command = message.split(' ')[0][1:]
                        if command == 'kick':
                            user_to_kick = message.split(' ')[1]
                            if user_to_kick == nickname:
                                send_system_message(client_socket, f'[{get_current_time()}] {nickname}: Вы не можете кикнуть себя.\n')
                                continue
                            kick_user(user_to_kick)
                            result = f'[{get_current_time()}] {nickname}: User {user_to_kick} kicked.'
                            send_system_message(client_socket, result)
                            continue
                        elif command == 'list_admins':
                            with db_lock:
                                cursor.execute('SELECT username FROM Admins')
                                admins = cursor.fetchall()
                                admins = [admin[0] for admin in admins]
                            result = f"[{get_current_time()}] System: Admins: {', '.join(admins)}"
                            send_system_message(client_socket, result)
                            continue
                        elif command == 'list_banned':
                            with db_lock:
                                cursor.execute('SELECT username FROM Banned_Users')
                                banned_users = cursor.fetchall()
                                banned_users = [user[0] for user in banned_users]
                            result = f"[{get_current_time()}] System: Banned users: {', '.join(banned_users)}"
                            send_system_message(client_socket, result)
                            continue
                        elif command == 'set_admin':
                            user_to_set_admin = message.split(' ')[1]
                            add_admin(user_to_set_admin)
                            result = f'[{get_current_time()}] {nickname}: User {user_to_set_admin} added as admin.'
                            send_system_message(client_socket, result)
                            continue
                        elif command == 'remove_admin':
                            remove_admin(message.split(' ')[1])
                            result = f"[{get_current_time()}] {nickname}: User {message.split(' ')[1]} removed from admins."
                            send_system_message(client_socket, result)
                            continue
                        elif command == 'ban':
                            user_to_ban = message.split(' ')[1]
                            if user_to_ban == nickname:
                                send_system_message(client_socket, f'[{get_current_time()}] {nickname}: Вы не можете забанить себя.')
                                continue
                            ban_user(user_to_ban)
                            result = f'[{get_current_time()}] {nickname}: User {user_to_ban} banned.'
                            send_system_message(client_socket, result)
                        elif command == 'unban':
                            user_to_unban = message.split(' ')[1]
                            unban_user(user_to_unban)
                            result = f'[{get_current_time()}] {nickname}: User {user_to_unban} unbanned.'
                            send_system_message(client_socket, result)
                        continue
            except (socket.error, OSError, ConnectionResetError, ConnectionAbortedError) as e:
                safe_print(f'Клиент {nickname} отключился: {str(e)}')
                break
            except Exception as e:
                safe_print(f'Ошибка получения сообщения от {nickname}: {str(e)}')
                continue
    except Exception as e:
        safe_print(f'Критическая ошибка для {addr}: {str(e)}')
    finally:
        remove(client_socket)

def remove(client_socket):
    try:
        with clients_lock:
            if client_socket in clients:
                nickname = clients[client_socket]
                del clients[client_socket]
                with typing_lock:
                    typing_users.discard(nickname)
        with client_timezones_lock:
            if client_socket in client_timezones:
                del client_timezones[client_socket]
                try:
                    client_socket.close()
                except:
                    pass
                disconnect_message = f'[{get_current_time_utc()}] {nickname} покинул чат'

                def add_disconnect_to_history():
                    try:
                        with messages_lock:
                            messages.append(disconnect_message)
                    except Exception as e:
                        safe_print(f'Ошибка добавления в историю: {e}')
                threading.Thread(target=add_disconnect_to_history, daemon=True).start()
                threading.Thread(target=lambda: broadcast_message(disconnect_message + '\n', None), daemon=True).start()
                threading.Thread(target=broadcast_users_list, daemon=True).start()
    except Exception as e:
        safe_print(f'Ошибка при удалении клиента: {e}')

def graceful_shutdown(signum, frame):
    safe_print('\nЗавершение работы сервера...')
    with clients_lock:
        for client in clients.copy():
            send_system_message(client, 'SERVER_SHUTDOWN')
            client.close()
    sys.exit(0)

def kick_user(nickname):
    with clients_lock:
        for sock, nick in clients.items():
            if nick == nickname:
                try:
                    send_system_message(sock, 'KICKED')
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
                    send_system_message(sock_to_ban, 'ERROR:BANNED')
                except:
                    pass
                remove(sock_to_ban)
        with db_lock:
            cursor.execute('INSERT INTO Banned_Users (username, ip) VALUES (?, ?)', (nickname, client_ip))
            connection.commit()
        return True
    except Exception as e:
        safe_print(f'Ошибка при бане пользователя {nickname}: {e}')
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
            safe_print(f'Ошибка при добавлении админа: {e}')
            return False

def remove_admin(username):
    with db_lock:
        try:
            cursor.execute('DELETE FROM Admins WHERE username = ?', (username,))
            connection.commit()
            return True
        except Exception as e:
            safe_print(f'Ошибка при удалении админа: {e}')
            return False

def list_admins():
    with db_lock:
        cursor.execute('SELECT username FROM Admins')
        admins = cursor.fetchall()
        safe_print('\nСписок админов:')
        for row in admins:
            safe_print(f'- {row[0]}')
        safe_print()

def list_users():
    with clients_lock:
        safe_print('\nТекущие участники:')
        for nick in clients.values():
            safe_print(f'- {nick}')
        safe_print()

def list_banned():
    with db_lock:
        cursor.execute('SELECT * FROM Banned_Users')
        banned_users_list = cursor.fetchall()
        safe_print('\nЗабаненные пользователи:')
        for row in banned_users_list:
            safe_print(f'- {row[0]} (ip: {row[1]})')
        safe_print()

def set_admin():
    global admin
    with clients_lock:
        safe_print('\nВыберите никнейм для назначения админом:')
        nicks = list(clients.values())
        for i, nick in enumerate(nicks):
            safe_print(f'{i + 1}. {nick}')
        idx = input('Введите номер пользователя: ')
        try:
            idx = int(idx) - 1
            if 0 <= idx < len(nicks):
                admin = nicks[idx]
                safe_print(f'Пользователь {admin} назначен админом.\n')
            else:
                safe_print('Некорректный номер.\n')
        except:
            safe_print('Ошибка ввода.\n')

def save_chat_history():
    try:
        with open('chat.txt', 'w', encoding='utf-8') as f:
            for message in messages:
                f.write(f'{message}\n')
        safe_print('История чата сохранена в chat.txt\n')
    except Exception as e:
        safe_print(f'Ошибка при сохранении истории чата: {e}\n')

def show_history():
    safe_print('\n===== История сообщений =====')
    if not messages:
        safe_print('История пуста.')
    else:
        for msg in messages:
            if 'IMG:' in msg:
                try:
                    img_pos = msg.find('IMG:')
                    if img_pos != -1:
                        prefix = msg[:img_pos]
                        img_part = msg[img_pos + 4:]
                        colon_pos = img_part.find(':')
                        if colon_pos != -1:
                            filename = img_part[:colon_pos]
                            img_b64 = img_part[colon_pos + 1:]
                            img_size_kb = len(img_b64) * 3 / 4 / 1024
                            msg = f'{prefix}IMG:{filename} ({img_size_kb:.1f} КБ)'
                except:
                    pass
            safe_print(msg)
    safe_print('============================\n')

def server_command_loop():
    while True:
        main_options = ['Users', 'Admins', 'Chat', 'Exit']
        global suppress_console_output
        suppress_console_output = True
        main_cmd = select('Select category:', choices=main_options).ask()
        suppress_console_output = False
        os.system('cls' if os.name == 'nt' else 'clear')
        if main_cmd == 'Users':
            while True:
                user_options = ['List users', 'Kick user', 'Ban user', 'Unban user', 'List banned users', 'Back']
                suppress_console_output = True
                user_cmd = select('User actions:', choices=user_options).ask()
                suppress_console_output = False
                os.system('cls' if os.name == 'nt' else 'clear')
                if user_cmd == 'List users':
                    list_users()
                elif user_cmd == 'Kick user':
                    with clients_lock:
                        nicks = list(clients.values())
                    if not nicks:
                        safe_print('No active users.\n')
                        continue
                    for i, nick in enumerate(nicks):
                        safe_print(f'{i + 1}. {nick}')
                    idx = input('Enter the number of the user to kick: ')
                    try:
                        idx = int(idx) - 1
                        if 0 <= idx < len(nicks):
                            kick_user(nicks[idx])
                            safe_print(f'User {nicks[idx]} kicked.\n')
                        else:
                            safe_print('Invalid number.\n')
                    except:
                        safe_print('Input error.\n')
                elif user_cmd == 'Ban user':
                    with clients_lock:
                        nicks = list(clients.values())
                    if not nicks:
                        safe_print('No active users.\n')
                        continue
                    for i, nick in enumerate(nicks):
                        safe_print(f'{i + 1}. {nick}')
                    idx = input('Enter the number of the user to ban: ')
                    try:
                        idx = int(idx) - 1
                        if 0 <= idx < len(nicks):
                            ban_user(nicks[idx])
                            safe_print(f'User {nicks[idx]} banned.\n')
                        else:
                            safe_print('Invalid number.\n')
                    except:
                        safe_print('Input error.\n')
                elif user_cmd == 'Unban user':
                    with db_lock:
                        cursor.execute('SELECT * FROM Banned_Users')
                        banned_users_list = cursor.fetchall()
                    if not banned_users_list:
                        safe_print('No banned users.\n')
                        continue
                    for i, row in enumerate(banned_users_list):
                        safe_print(f'{i + 1}. {row[0]}')
                    idx = input('Enter the number of the user to unban: ')
                    try:
                        idx = int(idx) - 1
                        if 0 <= idx < len(banned_users_list):
                            unban_user(banned_users_list[idx][0])
                            safe_print(f'User {banned_users_list[idx][0]} unbanned.\n')
                        else:
                            safe_print('Invalid number.\n')
                    except:
                        safe_print('Input error.\n')
                elif user_cmd == 'List banned users':
                    list_banned()
                elif user_cmd == 'Back':
                    break
        elif main_cmd == 'Admins':
            while True:
                admin_options = ['Add admin', 'Remove admin', 'List admins', 'Back']
                suppress_console_output = True
                admin_cmd = select('Admin actions:', choices=admin_options).ask()
                suppress_console_output = False
                os.system('cls' if os.name == 'nt' else 'clear')
                if admin_cmd == 'Add admin':
                    with clients_lock:
                        nicks = list(clients.values())
                    if not nicks:
                        safe_print('No active users.\n')
                        continue
                    for i, nick in enumerate(nicks):
                        safe_print(f'{i + 1}. {nick}')
                    idx = input('Enter the number of the user to add as admin: ')
                    try:
                        idx = int(idx) - 1
                        if 0 <= idx < len(nicks):
                            add_admin(nicks[idx])
                            safe_print(f'User {nicks[idx]} added as admin.\n')
                        else:
                            safe_print('Invalid number.\n')
                    except:
                        safe_print('Input error.\n')
                elif admin_cmd == 'Remove admin':
                    with db_lock:
                        cursor.execute('SELECT username FROM Admins')
                        admins = cursor.fetchall()
                    if not admins:
                        safe_print('No admins to remove.\n')
                        continue
                    for i, row in enumerate(admins):
                        safe_print(f'{i + 1}. {row[0]}')
                    idx = input('Enter the number of the admin to remove: ')
                    try:
                        idx = int(idx) - 1
                        if 0 <= idx < len(admins):
                            remove_admin(admins[idx][0])
                            safe_print(f'User {admins[idx][0]} removed from admins.\n')
                        else:
                            safe_print('Invalid number.\n')
                    except:
                        safe_print('Input error.\n')
                elif admin_cmd == 'List admins':
                    list_admins()
                elif admin_cmd == 'Back':
                    break
        elif main_cmd == 'Chat':
            while True:
                chat_options = ['Show history', 'Save chat history', 'Back']
                suppress_console_output = True
                chat_cmd = select('Chat actions:', choices=chat_options).ask()
                suppress_console_output = False
                os.system('cls' if os.name == 'nt' else 'clear')
                if chat_cmd == 'Show history':
                    show_history()
                elif chat_cmd == 'Save chat history':
                    save_chat_history()
                elif chat_cmd == 'Back':
                    break
        elif main_cmd == 'Exit':
            graceful_shutdown(None, None)
        else:
            safe_print('Неизвестная команда.\n')

def start_server():
    safe_print('=== SproutLine Server ===')
    host = input('Введите IP-адрес (по умолчанию 127.0.0.1): ').strip() or '127.0.0.1'
    while True:
        port_str = input('Введите порт (1024-65535, по умолчанию 1604): ').strip() or '1604'
        try:
            port = int(port_str)
            if 1024 <= port <= 65535:
                break
            else:
                safe_print('Порт вне диапазона.')
        except:
            safe_print('Некорректный порт.')
    global HOST, PORT
    HOST, PORT = (host, port)
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        safe_print(f'Сервер запущен на {HOST}:{PORT}\n')

        def accept_connections():
            while True:
                try:
                    client_socket, addr = server_socket.accept()
                    client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True).start()
                except Exception as e:
                    safe_print(f'Ошибка при принятии подключения: {e}')
                    continue
        accept_thread = threading.Thread(target=accept_connections, daemon=True)
        accept_thread.start()
        server_command_loop()
    except Exception as e:
        safe_print(f'Ошибка запуска сервера: {str(e)}')
        return
if __name__ == '__main__':
    os.system('cls' if os.name == 'nt' else 'clear')
    start_server()