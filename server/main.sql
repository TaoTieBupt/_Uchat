-- Uchat/server/main.sql
-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    email TEXT UNIQUE,
    sex TEXT,
    age INTEGER,
    pk TEXT,
    signature TEXT DEFAULT '这个人很懒，什么都没留下~', -- 【新增】个性签名，带默认值
    avatar TEXT DEFAULT 'default.png'             -- 【新增】头像文件名，带默认值
);

-- 好友关系表
CREATE TABLE IF NOT EXISTS friends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_user_id INTEGER NOT NULL,
    to_user_id INTEGER NOT NULL,
    accepted BOOLEAN NOT NULL DEFAULT 0, -- 0 for pending, 1 for accepted
    FOREIGN KEY(from_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(to_user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(from_user_id, to_user_id)
);

-- 聊天室/群组表
CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_name TEXT NOT NULL UNIQUE,
    owner_id INTEGER NOT NULL, -- 【修改】将 creator_id 重命名为 owner_id，语义更清晰
    FOREIGN KEY(owner_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 房间-用户关系表
CREATE TABLE IF NOT EXISTS room_user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    FOREIGN KEY(room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(room_id, user_id)
);

-- 聊天记录表
CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER NOT NULL,
    sender_name TEXT NOT NULL,
    target_id INTEGER NOT NULL,
    target_type TEXT NOT NULL, -- 'user' or 'room'
    data TEXT NOT NULL,        -- JSON-serialized message dictionary
    timestamp REAL NOT NULL
);
-- 【新增】动态/朋友圈表 (Moments Table)
CREATE TABLE IF NOT EXISTS moments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,         -- 动态的文本内容
    image_filename TEXT,           -- 【新增】用于存储动态图片的唯一文件名，可以为NULL
    timestamp REAL NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 【修改】动态点赞表 (Moment Likes Table)
CREATE TABLE IF NOT EXISTS moment_likes (
    moment_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL, -- 点赞的用户ID
    username TEXT NOT NULL,   -- 点赞的用户名 (冗余存储，方便查询)
    FOREIGN KEY(moment_id) REFERENCES moments(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    PRIMARY KEY (moment_id, user_id)
);

-- 【修改】动态评论表 (Moment Comments Table)
CREATE TABLE IF NOT EXISTS moment_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    moment_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,   -- 评论的用户ID
    username TEXT NOT NULL,     -- 评论的用户名 (冗余存储)
    content TEXT NOT NULL,
    timestamp REAL NOT NULL,
    FOREIGN KEY(moment_id) REFERENCES moments(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);