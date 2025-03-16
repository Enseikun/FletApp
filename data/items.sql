-- フォルダ一覧
CREATE TABLE IF NOT EXISTS folders (
    entry_id TEXT PRIMARY KEY,
    store_id TEXT NOT NULL,
    name TEXT NOT NULL,
    path TEXT NOT NULL,
    item_count INTEGER DEFAULT 0,
    unread_count INTEGER DEFAULT 0,
    parent_folder_id TEXT,
    updated_at TIMESTAMP NOT NULL CHECK (
        datetime(updated_at) IS NOT NULL AND
        updated_at LIKE '____-__-__ __:__:__'
    ),
    FOREIGN KEY (parent_folder_id) REFERENCES folders(entry_id)  
);

-- メールアイテム
CREATE TABLE IF NOT EXISTS mail_items (
    -- メタデータ
    entry_id TEXT PRIMARY KEY,
    conversation_id TEXT,
    conversation_index TEXT,
    thread_id TEXT,
    thread_depth INTEGER DEFAULT 0,
    message_type TEXT CHECK (message_type IN ('email', 'meeting', 'task')),
    parent_entry_id TEXT,
    parent_folder_name TEXT,
    destination TEXT,
    message_size INTEGER DEFAULT 0,
    unread INTEGER DEFAULT 0,

    -- メッセージヘッダー
    subject TEXT NOT NULL,
    sent_time TEXT NOT NULL CHECK (
        datetime(sent_time) IS NOT NULL AND
        length(sent_time) = 19 AND
        sent_time LIKE '____-__-__ __:__:__'
    ),
    received_time TEXT NOT NULL CHECK (
        datetime(received_time) IS NOT NULL AND
        length(received_time) = 19 AND
        received_time LIKE '____-__-__ __:__:__'
    ),
    importance INTEGER,

    -- コンテンツ関連
    body TEXT,
    attachments_count INTEGER DEFAULT 0,

    -- 関連テーブルの外部キー
    folder_id TEXT NOT NULL,

    FOREIGN KEY (folder_id) REFERENCES folders(entry_id),
    FOREIGN KEY (parent_entry_id) REFERENCES mail_items(entry_id)
);

-- 添付メッセージ
CREATE TABLE IF NOT EXISTS attachments_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_mail_id TEXT NOT NULL,
    message_entry_id TEXT NOT NULL,
    FOREIGN KEY (parent_mail_id) REFERENCES mail_items(entry_id),
    FOREIGN KEY (message_entry_id) REFERENCES mail_items(entry_id),
    UNIQUE (parent_mail_id, message_entry_id)
);

-- 参加者
CREATE TABLE IF NOT EXISTS participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mail_id TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    participant_type TEXT NOT NULL,
    address_type TEXT,
    display_name TEXT,
    alias TEXT,
    company TEXT,
    office_location TEXT,
    smtp_address TEXT,
    FOREIGN KEY (mail_id) REFERENCES mail_items(entry_id),
    UNIQUE (mail_id, email, participant_type)
);

-- 添付ファイル
CREATE TABLE IF NOT EXISTS attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mail_id TEXT NOT NULL,
    name TEXT NOT NULL,
    path TEXT NOT NULL,
    size INTEGER NOT NULL,
    FOREIGN KEY (mail_id) REFERENCES mail_items(entry_id),
    UNIQUE (mail_id, path)
);

-- ダウンロード計画テーブル
CREATE TABLE IF NOT EXISTS download_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    target_folder_id TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    total_count INTEGER DEFAULT 0,
    completed_count INTEGER DEFAULT 0,
    FOREIGN KEY (target_folder_id) REFERENCES folders(entry_id)
);

-- タスク管理テーブル
CREATE TABLE IF NOT EXISTS download_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mail_id TEXT UNIQUE,
    plan_id INTEGER NOT NULL,
    message_id TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- メール情報取得の結果
    mail_fetch_status TEXT DEFAULT 'pending',
    mail_fetch_at TIMESTAMP,

    -- 添付ファイル取得の結果
    attachment_status TEXT DEFAULT 'pending',
    attachment_at TIMESTAMP,

    -- AIレビューの結果
    ai_review_status TEXT DEFAULT 'pending',
    ai_review_at TIMESTAMP,

    FOREIGN KEY (plan_id) REFERENCES download_plans(id),
    FOREIGN KEY (mail_id) REFERENCES mail_items(entry_id)
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_folders_path ON folders(path);
CREATE INDEX IF NOT EXISTS idx_mail_items_conversation ON mail_items(conversation_id);
CREATE INDEX IF NOT EXISTS idx_mail_items_thread ON mail_items(thread_id);
CREATE INDEX IF NOT EXISTS idx_mail_items_parent ON mail_items(parent_entry_id);
CREATE INDEX IF NOT EXISTS idx_mail_items_folder ON mail_items(folder_id);
CREATE INDEX IF NOT EXISTS idx_mail_items_sent_time ON mail_items(sent_time);
CREATE INDEX IF NOT EXISTS idx_mail_items_received_time ON mail_items(received_time);
CREATE INDEX IF NOT EXISTS idx_mail_items_subject ON mail_items(subject);
CREATE INDEX IF NOT EXISTS idx_attached_messages_parent ON attachments_messages(parent_mail_id);
CREATE INDEX IF NOT EXISTS idx_participants_mail ON participants(mail_id);
CREATE INDEX IF NOT EXISTS idx_participants_email ON participants(email);
CREATE INDEX IF NOT EXISTS idx_attachments_mail ON attachments(mail_id);
CREATE INDEX IF NOT EXISTS idx_download_tasks_plan ON download_tasks(plan_id);
CREATE INDEX IF NOT EXISTS idx_download_tasks_mail_fetch ON download_tasks(mail_fetch_status);
CREATE INDEX IF NOT EXISTS idx_download_tasks_attachment ON download_tasks(attachment_status);
CREATE INDEX IF NOT EXISTS idx_download_tasks_ai_review ON download_tasks(ai_review_status);
CREATE INDEX IF NOT EXISTS idx_download_plans_status ON download_plans(status);
CREATE INDEX IF NOT EXISTS idx_download_tasks_message_id ON download_tasks(message_id);
CREATE INDEX IF NOT EXISTS idx_download_tasks_mail_id ON download_tasks(mail_id);

-- フォルダのitem_count更新用トリガー
CREATE TRIGGER IF NOT EXISTS update_folder_item_count_insert AFTER INSERT ON mail_items
    BEGIN
        UPDATE folders
        SET item_count = item_count + 1
        WHERE entry_id = NEW.folder_id;
    END;

CREATE TRIGGER IF NOT EXISTS update_folder_item_count_delete AFTER DELETE ON mail_items
    BEGIN
        UPDATE folders
        SET item_count = item_count - 1
        WHERE entry_id = OLD.folder_id;
    END;

-- download_plans completed_count更新用トリガー
CREATE TRIGGER IF NOT EXISTS update_plan_completed_count_insert AFTER UPDATE ON download_tasks
WHEN NEW.mail_fetch_status = 'success' AND OLD.mail_fetch_status != 'success'
BEGIN
    UPDATE download_plans
    SET completed_count = completed_count + 1
    WHERE id = NEW.plan_id;
END;

CREATE TRIGGER IF NOT EXISTS update_plan_completed_count_delete AFTER UPDATE ON download_tasks
WHEN NEW.mail_fetch_status != 'success' AND OLD.mail_fetch_status = 'success'
BEGIN
    UPDATE download_plans
    SET completed_count = completed_count - 1
    WHERE id = NEW.plan_id;
END;
