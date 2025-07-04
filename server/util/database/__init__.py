# Uchat/server/util/database/__init__.py
import sqlite3
import json
from contextlib import contextmanager

DB_PATH = 'server/database.db'

@contextmanager
def db_cursor():
    """数据库连接的上下文管理器，自动处理提交、回滚和关闭。"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    """使用 main.sql 脚本初始化数据库表。"""
    try:
        with open('server/main.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        with db_cursor() as cursor:
            cursor.executescript(sql_script)
        print("数据库已初始化。")
    except Exception as e:
        print(f"数据库初始化失败: {e}")

# --- 用户 (User) 函数 ---
def create_user(username, password_hash, email, sex, age, pk):
    with db_cursor() as cursor:
        cursor.execute(
            "INSERT INTO users (username, password, email, sex, age, pk) VALUES (?, ?, ?, ?, ?, ?)",
            (username, password_hash, email, sex, age, pk)
        )
        return cursor.lastrowid
    
def update_user_signature(user_id, signature):
    """【新增】更新用户的个性签名"""
    with db_cursor() as cursor:
        cursor.execute("UPDATE users SET signature = ? WHERE id = ?", (signature, user_id))
        return cursor.rowcount > 0

def update_user_avatar(user_id, avatar_filename):
    """【新增】更新用户的头像文件名"""
    with db_cursor() as cursor:
        cursor.execute("UPDATE users SET avatar = ? WHERE id = ?", (avatar_filename, user_id))
        return cursor.rowcount > 0    

def get_user_by_name(username):
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        return cursor.fetchone()

def get_user_by_id(user_id):
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cursor.fetchone()

# --- 好友 (Friend) 函数 ---
def add_friend_request(from_user_id, to_user_id):
    with db_cursor() as cursor:
        cursor.execute("SELECT id FROM friends WHERE (from_user_id = ? AND to_user_id = ?) OR (from_user_id = ? AND to_user_id = ?)", (from_user_id, to_user_id, to_user_id, from_user_id))
        if cursor.fetchone():
            return None
        cursor.execute("INSERT INTO friends (from_user_id, to_user_id, accepted) VALUES (?, ?, 0)", (from_user_id, to_user_id))
        return cursor.lastrowid

def are_friends(user1_id, user2_id):
    with db_cursor() as cursor:
        cursor.execute("SELECT id FROM friends WHERE ((from_user_id = ? AND to_user_id = ?) OR (from_user_id = ? AND to_user_id = ?)) AND accepted = 1", (user1_id, user2_id, user2_id, user1_id))
        return cursor.fetchone() is not None

def accept_friend_request(from_user_id, to_user_id):
    with db_cursor() as cursor:
        cursor.execute("UPDATE friends SET accepted = 1 WHERE from_user_id = ? AND to_user_id = ? AND accepted = 0", (from_user_id, to_user_id))
        return cursor.rowcount > 0

def delete_friendship(user1_id, user2_id):
     with db_cursor() as cursor:
        cursor.execute("DELETE FROM friends WHERE (from_user_id = ? AND to_user_id = ?) OR (from_user_id = ? AND to_user_id = ?)", (user1_id, user2_id, user2_id, user1_id))
        return cursor.rowcount > 0
        
def get_all_friends(user_id):
    with db_cursor() as cursor:
        cursor.execute("""
            SELECT u.* FROM users u JOIN friends f ON u.id = f.to_user_id
            WHERE f.from_user_id = ? AND f.accepted = 1
            UNION
            SELECT u.* FROM users u JOIN friends f ON u.id = f.from_user_id
            WHERE f.to_user_id = ? AND f.accepted = 1
        """, (user_id, user_id))
        return cursor.fetchall()
        
def get_pending_friend_requests(user_id):
    with db_cursor() as cursor:
        cursor.execute("SELECT u.id, u.username FROM users u JOIN friends f ON u.id = f.from_user_id WHERE f.to_user_id = ? AND f.accepted = 0", (user_id,))
        return cursor.fetchall()

# --- 群组 (Room) 函数 ---
def create_room(room_name, owner_id):
    with db_cursor() as cursor:
        cursor.execute("INSERT INTO rooms (room_name, owner_id) VALUES (?, ?)", (room_name, owner_id))
        room_id = cursor.lastrowid
        cursor.execute("INSERT INTO room_user (room_id, user_id) VALUES (?, ?)", (room_id, owner_id))
        return room_id

def get_room_by_name(room_name):
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM rooms WHERE room_name = ?", (room_name,))
        return cursor.fetchone()

# 【补充】添加 get_room_by_id 函数
def get_room_by_id(room_id):
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM rooms WHERE id = ?", (room_id,))
        return cursor.fetchone()

def add_user_to_room(user_id, room_id):
    with db_cursor() as cursor:
        try:
            cursor.execute("INSERT INTO room_user (room_id, user_id) VALUES (?, ?)", (room_id, user_id))
            return True
        except sqlite3.IntegrityError:
            return False

def get_user_rooms(user_id):
    with db_cursor() as cursor:
        cursor.execute("SELECT r.* FROM rooms r JOIN room_user ru ON r.id = ru.room_id WHERE ru.user_id = ?", (user_id,))
        return cursor.fetchall()
        
def get_room_member_ids(room_id):
    with db_cursor() as cursor:
        cursor.execute("SELECT user_id FROM room_user WHERE room_id = ?", (room_id,))
        return [row['user_id'] for row in cursor.fetchall()]
    
def is_user_in_room(user_id, room_id):
    with db_cursor() as cursor:
        cursor.execute("SELECT id FROM room_user WHERE user_id = ? AND room_id = ?", (user_id, room_id))
        return cursor.fetchone() is not None    

# 【补充】添加 leave_room 和 get_room_owner_id 函数
def leave_room(user_id, room_id):
    """用户主动或被动退出群聊"""
    with db_cursor() as cursor:
        cursor.execute("DELETE FROM room_user WHERE user_id = ? AND room_id = ?", (user_id, room_id))
        return cursor.rowcount > 0

def get_room_owner_id(room_id):
    """获取群主ID"""
    with db_cursor() as cursor:
        cursor.execute("SELECT owner_id FROM rooms WHERE id = ?", (room_id,))
        row = cursor.fetchone()
        return row['owner_id'] if row else None    

# --- 聊天记录 (Chat History) 函数 ---
def add_to_chat_history(sender_id, sender_name, target_id, target_type, data, timestamp):
    with db_cursor() as cursor:
        cursor.execute(
            "INSERT INTO chat_history (sender_id, sender_name, target_id, target_type, data, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (sender_id, sender_name, target_id, target_type, json.dumps(data), timestamp)
        )
        return cursor.lastrowid

def get_offline_messages(user_id):
    with db_cursor() as cursor:
        user_rooms, friends = get_user_rooms(user_id), get_all_friends(user_id)
        room_ids, friend_ids = [r['id'] for r in user_rooms], [f['id'] for f in friends]
        query_parts, params = [], []
        if friend_ids:
            placeholders = ','.join('?' for _ in friend_ids)
            query_parts.append(f"((target_type = 'user' AND target_id = ? AND sender_id IN ({placeholders})) OR (target_type = 'user' AND sender_id = ? AND target_id IN ({placeholders})))")
            params.extend([user_id] + friend_ids + [user_id] + friend_ids)
        if room_ids:
            placeholders = ','.join('?' for _ in room_ids)
            query_parts.append(f"(target_type = 'room' AND target_id IN ({placeholders}))")
            params.extend(room_ids)
        if not query_parts: return []
        full_query = f"SELECT * FROM chat_history WHERE {' OR '.join(query_parts)} ORDER BY timestamp DESC LIMIT 50"
        cursor.execute(full_query, params)
        rows = cursor.fetchall()
        return sorted(rows, key=lambda x: x['timestamp'])

# --- 动态 (Moments) 相关函数 ---
def create_moment(user_id, content, timestamp, image_filename=None):
    with db_cursor() as cursor:
        cursor.execute("INSERT INTO moments (user_id, content, image_filename, timestamp) VALUES (?, ?, ?, ?)", (user_id, content, image_filename, timestamp))
        return cursor.lastrowid

def get_friends_moments(user_id):
    friends = get_all_friends(user_id)
    all_ids = [friend['id'] for friend in friends] + [user_id]
    if not all_ids: return []
    with db_cursor() as cursor:
        placeholders = ','.join('?' for _ in all_ids)
        query = f"""
            SELECT m.id, m.content, m.image_filename, m.timestamp, u.username 
            FROM moments m JOIN users u ON m.user_id = u.id
            WHERE m.user_id IN ({placeholders}) ORDER BY m.timestamp DESC LIMIT 50
        """
        cursor.execute(query, all_ids)
        moments = cursor.fetchall()
    full_moments_data = []
    for moment in moments:
        moment_dict = dict(moment)
        moment_id = moment['id']
        moment_dict['likes'] = get_likes_for_moment(moment_id)
        moment_dict['comments'] = [dict(row) for row in get_comments_for_moment(moment_id)]
        full_moments_data.append(moment_dict)
    return full_moments_data

def add_like_to_moment(moment_id, user_id, username):
    with db_cursor() as cursor:
        try:
            cursor.execute("INSERT INTO moment_likes (moment_id, user_id, username) VALUES (?, ?, ?)", (moment_id, user_id, username))
            return True
        except sqlite3.IntegrityError: return False

def add_comment_to_moment(moment_id, user_id, username, content, timestamp):
    with db_cursor() as cursor:
        cursor.execute("INSERT INTO moment_comments (moment_id, user_id, username, content, timestamp) VALUES (?, ?, ?, ?, ?)", (moment_id, user_id, username, content, timestamp))
        return cursor.lastrowid

def get_likes_for_moment(moment_id):
    with db_cursor() as cursor:
        cursor.execute("SELECT username FROM moment_likes WHERE moment_id = ?", (moment_id,))
        return [row['username'] for row in cursor.fetchall()]

def get_comments_for_moment(moment_id):
    with db_cursor() as cursor:
        cursor.execute("SELECT username, content FROM moment_comments WHERE moment_id = ? ORDER BY timestamp ASC", (moment_id,))
        return cursor.fetchall()

def get_moment_by_id(moment_id):
    with db_cursor() as cursor:
        cursor.execute("SELECT m.id, m.content, m.image_filename, m.timestamp, m.user_id, u.username FROM moments m JOIN users u ON m.user_id = u.id WHERE m.id = ?", (moment_id,))
        moment = cursor.fetchone()
        if not moment: return None
        moment_dict = dict(moment)
        moment_dict['likes'] = get_likes_for_moment(moment_id)
        moment_dict['comments'] = [dict(row) for row in get_comments_for_moment(moment_id)]
        return moment_dict