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
    task_id TEXT NOT NULL,  -- どのタスクで取得されたかを記録
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
    
    -- 処理情報
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
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

-- タスク処理管理テーブル
CREATE TABLE IF NOT EXISTS mail_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,  -- task_infoのidを参照
    message_id TEXT NOT NULL,
    mail_id TEXT UNIQUE,    -- 処理後に設定されるメールID
    
    -- 処理状態
    status TEXT DEFAULT 'pending' CHECK (
        status IN ('pending', 'processing', 'completed', 'error', 'skipped')
    ),
    
    -- 処理ステップのステータス
    mail_fetch_status TEXT DEFAULT 'pending' CHECK (
        mail_fetch_status IN ('pending', 'processing', 'success', 'error', 'not_required')
    ),
    attachment_status TEXT DEFAULT 'pending' CHECK (
        attachment_status IN ('pending', 'processing', 'success', 'error', 'not_required')
    ),
    ai_review_status TEXT DEFAULT 'pending' CHECK (
        ai_review_status IN ('pending', 'processing', 'success', 'error', 'not_required')
    ),
    
    -- 処理時間記録
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- 処理結果情報
    error_message TEXT,
    ai_review_result TEXT,
    
    -- インデックス用
    UNIQUE (task_id, message_id)
);

-- タスク処理の進捗状況テーブル
CREATE TABLE IF NOT EXISTS task_progress (
    task_id TEXT PRIMARY KEY,
    total_messages INTEGER DEFAULT 0,
    processed_messages INTEGER DEFAULT 0,
    successful_messages INTEGER DEFAULT 0,
    failed_messages INTEGER DEFAULT 0,
    skipped_messages INTEGER DEFAULT 0,
    
    -- 処理状態
    status TEXT DEFAULT 'pending' CHECK (
        status IN ('pending', 'processing', 'completed', 'error', 'paused')
    ),
    
    -- 処理時間
    started_at TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- エラー情報
    last_error TEXT
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_folders_path ON folders(path);
CREATE INDEX IF NOT EXISTS idx_mail_items_task_id ON mail_items(task_id);
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
CREATE INDEX IF NOT EXISTS idx_mail_tasks_task_id ON mail_tasks(task_id);
CREATE INDEX IF NOT EXISTS idx_mail_tasks_status ON mail_tasks(status);
CREATE INDEX IF NOT EXISTS idx_mail_tasks_message_id ON mail_tasks(message_id);
CREATE INDEX IF NOT EXISTS idx_mail_tasks_mail_fetch ON mail_tasks(mail_fetch_status);
CREATE INDEX IF NOT EXISTS idx_mail_tasks_attachment ON mail_tasks(attachment_status);
CREATE INDEX IF NOT EXISTS idx_mail_tasks_ai_review ON mail_tasks(ai_review_status);

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

-- タスク進捗状況の自動更新トリガー
CREATE TRIGGER IF NOT EXISTS update_task_progress AFTER UPDATE ON mail_tasks
BEGIN
    UPDATE task_progress
    SET 
        processed_messages = (SELECT COUNT(*) FROM mail_tasks WHERE task_id = NEW.task_id AND status != 'pending'),
        successful_messages = (SELECT COUNT(*) FROM mail_tasks WHERE task_id = NEW.task_id AND status = 'completed'),
        failed_messages = (SELECT COUNT(*) FROM mail_tasks WHERE task_id = NEW.task_id AND status = 'error'),
        skipped_messages = (SELECT COUNT(*) FROM mail_tasks WHERE task_id = NEW.task_id AND status = 'skipped'),
        last_updated_at = CURRENT_TIMESTAMP,
        status = CASE
            WHEN (SELECT COUNT(*) FROM mail_tasks WHERE task_id = NEW.task_id AND status IN ('pending', 'processing')) = 0 THEN 'completed'
            WHEN (SELECT COUNT(*) FROM mail_tasks WHERE task_id = NEW.task_id AND status = 'error') > 0 THEN 'error'
            ELSE 'processing'
        END,
        completed_at = CASE
            WHEN (SELECT COUNT(*) FROM mail_tasks WHERE task_id = NEW.task_id AND status IN ('pending', 'processing')) = 0 
            THEN CURRENT_TIMESTAMP
            ELSE completed_at
        END
    WHERE task_id = NEW.task_id;
END;

-- 新しいタスクが追加されたときにtask_progressを初期化するトリガー
CREATE TRIGGER IF NOT EXISTS initialize_task_progress AFTER INSERT ON mail_tasks
WHEN NOT EXISTS (SELECT 1 FROM task_progress WHERE task_id = NEW.task_id)
BEGIN
    INSERT INTO task_progress (
        task_id, 
        total_messages, 
        status
    ) VALUES (
        NEW.task_id,
        (SELECT COUNT(*) FROM mail_tasks WHERE task_id = NEW.task_id),
        'pending'
    );
END;

-- メール取得成功時にmail_idを更新するトリガー
CREATE TRIGGER IF NOT EXISTS update_mail_id_on_success AFTER UPDATE ON mail_tasks
WHEN NEW.mail_fetch_status = 'success' AND OLD.mail_fetch_status != 'success' AND NEW.mail_id IS NULL
BEGIN
    UPDATE mail_tasks
    SET mail_id = (
        SELECT entry_id FROM mail_items 
        WHERE task_id = NEW.task_id 
        ORDER BY processed_at DESC LIMIT 1
    )
    WHERE id = NEW.id;
END;
