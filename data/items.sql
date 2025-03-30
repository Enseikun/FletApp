/*
Outlookのメールアイテムとデータ抽出の進捗状況を保存するテーブル
outlook_snapshot: タスク作成時点のOutlookアカウントとフォルダ情報のスナップショット
mail_items: メールアイテム
participants: 会話参加者(to, cc, bcc)
attachments: 添付ファイル()
mail_tasks: メール取得の進捗状況
task_progress: タスクの進捗状況
*/

-- タスク作成時点のOutlookアカウントとフォルダ情報のスナップショット
CREATE TABLE IF NOT EXISTS outlook_snapshot (
    -- フォルダ情報
    entry_id TEXT PRIMARY KEY,
    store_id TEXT NOT NULL,
    name TEXT NOT NULL,
    path TEXT NOT NULL,
    parent_folder_id TEXT,
    folder_type TEXT,
    folder_class TEXT,
    item_count INTEGER DEFAULT 0,
    unread_count INTEGER DEFAULT 0,
    
    -- スナップショット管理
    snapshot_time TIMESTAMP NOT NULL CHECK (
        datetime(snapshot_time) IS NOT NULL AND
        snapshot_time LIKE '____-__-__ __:__:__'
    ),
    
    -- 制約
    FOREIGN KEY (parent_folder_id) REFERENCES outlook_snapshot(entry_id),
    UNIQUE (store_id, entry_id)
);

-- メールアイテム
CREATE TABLE IF NOT EXISTS mail_items (
    -- メタデータ
    entry_id TEXT PRIMARY KEY,
    store_id TEXT,
    folder_id TEXT NOT NULL, -- from_folder_id を所与、使わない
    conversation_id TEXT, -- OutlookのConversationID
    thread_id TEXT, -- このアプリケーションで付与
    message_type TEXT CHECK (message_type IN ('email', 'meeting', 'task')),
    parent_entry_id TEXT, -- 自身が添付ファイルの場合, 元メッセージのentry_id
    parent_folder_name TEXT, -- 自身が添付ファイルの場合, 元メッセージのフォルダ名
    message_size INTEGER DEFAULT 0,
    unread INTEGER DEFAULT 0,
    task_id TEXT, -- 関連するタスクID
    has_attachments INTEGER DEFAULT 0, -- 添付ファイルの有無（0=なし、1=あり）
    attachment_count INTEGER DEFAULT 0, -- 添付ファイルの個数

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

    -- コンテンツ関連
    body TEXT,
    
    -- 処理情報
    process_type TEXT, -- 特別な処理を行うためのタイプ判定（GUARDIAN）
    processed_at TIMESTAMP CHECK (
        datetime(processed_at) IS NOT NULL AND
        processed_at LIKE '____-__-__ __:__:__'
    ),
    
    -- 制約
    FOREIGN KEY (parent_entry_id) REFERENCES mail_items(entry_id),
    FOREIGN KEY (folder_id) REFERENCES outlook_snapshot(entry_id)
);

-- ユーザー情報
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    display_name TEXT,
    company TEXT,
    office_location TEXT,
    smtp_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP CHECK (
        datetime(created_at) IS NOT NULL AND
        created_at LIKE '____-__-__ __:__:__'
    ),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP CHECK (
        datetime(updated_at) IS NOT NULL AND
        updated_at LIKE '____-__-__ __:__:__'
    )
);

-- 会話参加者
CREATE TABLE IF NOT EXISTS participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mail_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    participant_type TEXT NOT NULL,
    address_type TEXT,
    FOREIGN KEY (mail_id) REFERENCES mail_items(entry_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE (mail_id, user_id, participant_type)
);

-- 添付ファイル
CREATE TABLE IF NOT EXISTS attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mail_id TEXT NOT NULL,
    name TEXT NOT NULL,
    path TEXT NOT NULL,
    FOREIGN KEY (mail_id) REFERENCES mail_items(entry_id),
    UNIQUE (mail_id, path)
);

-- AI評価（conversation単位）
CREATE TABLE IF NOT EXISTS ai_reviews (
    conversation_id TEXT PRIMARY KEY,
    result JSON,
    FOREIGN KEY (conversation_id) REFERENCES mail_items(conversation_id)
);

-- styled_body（本文中のキーワードを装飾）
CREATE TABLE IF NOT EXISTS styled_body (
    entry_id TEXT PRIMARY KEY,
    styled_body TEXT,
    keywords TEXT, -- キーワード
    FOREIGN KEY (entry_id) REFERENCES mail_items(entry_id)
);

-- Chat View（会話のチャット形式表示）
CREATE TABLE IF NOT EXISTS chat_view (
    conversation_id TEXT PRIMARY KEY,
    chat_view JSON,
    FOREIGN KEY (conversation_id) REFERENCES mail_items(conversation_id)
);


-- メールごとの処理状況
CREATE TABLE IF NOT EXISTS mail_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,  -- task_infoのidを参照
    message_id TEXT NOT NULL, -- 未完遂プロセスの仮ID（mail_itemsのentry_id）
    mail_id TEXT UNIQUE,    -- 処理完了後に合格の証として付与されるメールID（mail_itemsのentry_id）
    
    -- メール情報
    subject TEXT,
    sent_time TEXT CHECK (
        sent_time IS NULL OR (
            datetime(sent_time) IS NOT NULL AND
            sent_time LIKE '____-__-__ __:__:__'
        )
    ),
    
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
    created_at TIMESTAMP CHECK (
        datetime(created_at) IS NOT NULL AND
        created_at LIKE '____-__-__ __:__:__'
    ),
    started_at TIMESTAMP CHECK (
        started_at IS NULL OR (
            datetime(started_at) IS NOT NULL AND
            started_at LIKE '____-__-__ __:__:__'
        )
    ),
    completed_at TIMESTAMP CHECK (
        completed_at IS NULL OR (
            datetime(completed_at) IS NOT NULL AND
            completed_at LIKE '____-__-__ __:__:__'
        )
    ),
    
    -- 処理結果情報
    error_message TEXT,
    
    -- インデックス用
    UNIQUE (task_id, message_id)
);

-- タスク処理全体の進捗状況
CREATE TABLE IF NOT EXISTS task_progress (
    task_id TEXT PRIMARY KEY,
    total_messages INTEGER DEFAULT 0,
    processed_messages INTEGER DEFAULT 0,
    successful_messages INTEGER DEFAULT 0,
    failed_messages INTEGER DEFAULT 0,
    skipped_messages INTEGER DEFAULT 0,
    
    -- 処理状態
    status TEXT DEFAULT 'pending' CHECK (
        status IN ('pending', 'processing', 'completed', 'error', 'paused', 'not_required')
    ),
    
    -- 処理時間
    started_at TIMESTAMP CHECK (
        started_at IS NULL OR (
            datetime(started_at) IS NOT NULL AND
            started_at LIKE '____-__-__ __:__:__'
        )
    ),
    last_updated_at TIMESTAMP CHECK (
        datetime(last_updated_at) IS NOT NULL AND
        last_updated_at LIKE '____-__-__ __:__:__'
    ),
    completed_at TIMESTAMP CHECK (
        completed_at IS NULL OR (
            datetime(completed_at) IS NOT NULL AND
            completed_at LIKE '____-__-__ __:__:__'
        )
    ),
    
    -- エラー情報
    last_error TEXT
);

-- 抽出条件
CREATE TABLE IF NOT EXISTS extraction_conditions (
    task_id TEXT PRIMARY KEY,
    from_folder_id TEXT NOT NULL,
    from_folder_name TEXT NOT NULL,
    start_date TIMESTAMP NOT NULL CHECK (
        datetime(start_date) IS NOT NULL AND
        start_date LIKE '____-__-__ __:__:__'
    ),
    end_date TIMESTAMP NOT NULL CHECK (
        datetime(end_date) IS NOT NULL AND
        end_date LIKE '____-__-__ __:__:__' AND
        end_date >= start_date
    ),
    exclude_extensions TEXT,
    created_at TIMESTAMP NOT NULL CHECK (
        datetime(created_at) IS NOT NULL AND
        created_at LIKE '____-__-__ __:__:__'
    ),
    FOREIGN KEY (from_folder_id) REFERENCES outlook_snapshot(entry_id)
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_outlook_snapshot_store ON outlook_snapshot(store_id);
CREATE INDEX IF NOT EXISTS idx_outlook_snapshot_parent ON outlook_snapshot(parent_folder_id);
CREATE INDEX IF NOT EXISTS idx_outlook_snapshot_path ON outlook_snapshot(path);
CREATE INDEX IF NOT EXISTS idx_outlook_snapshot_time ON outlook_snapshot(snapshot_time);
CREATE INDEX IF NOT EXISTS idx_mail_items_store ON mail_items(store_id);
CREATE INDEX IF NOT EXISTS idx_mail_items_folder ON mail_items(folder_id);
CREATE INDEX IF NOT EXISTS idx_mail_items_conversation ON mail_items(conversation_id);
CREATE INDEX IF NOT EXISTS idx_mail_items_thread ON mail_items(thread_id);
CREATE INDEX IF NOT EXISTS idx_mail_items_parent ON mail_items(parent_entry_id);
CREATE INDEX IF NOT EXISTS idx_mail_items_sent_time ON mail_items(sent_time);
CREATE INDEX IF NOT EXISTS idx_mail_items_received_time ON mail_items(received_time);
CREATE INDEX IF NOT EXISTS idx_mail_items_subject ON mail_items(subject);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_participants_user ON participants(user_id);
CREATE INDEX IF NOT EXISTS idx_attachments_mail ON attachments(mail_id);
CREATE INDEX IF NOT EXISTS idx_mail_tasks_task_id ON mail_tasks(task_id);
CREATE INDEX IF NOT EXISTS idx_mail_tasks_status ON mail_tasks(status);
CREATE INDEX IF NOT EXISTS idx_mail_tasks_message_id ON mail_tasks(message_id);
CREATE INDEX IF NOT EXISTS idx_mail_tasks_mail_fetch ON mail_tasks(mail_fetch_status);
CREATE INDEX IF NOT EXISTS idx_mail_tasks_attachment ON mail_tasks(attachment_status);
CREATE INDEX IF NOT EXISTS idx_mail_tasks_ai_review ON mail_tasks(ai_review_status);
CREATE INDEX IF NOT EXISTS idx_extraction_conditions_folder ON extraction_conditions(from_folder_id);
CREATE INDEX IF NOT EXISTS idx_extraction_conditions_dates ON extraction_conditions(start_date, end_date);

-- フォルダのitem_count更新用トリガー
CREATE TRIGGER IF NOT EXISTS update_folder_item_count_insert AFTER INSERT ON mail_items
BEGIN
    UPDATE outlook_snapshot
    SET item_count = item_count + 1
    WHERE entry_id = NEW.folder_id;
END;

CREATE TRIGGER IF NOT EXISTS update_folder_item_count_delete AFTER DELETE ON mail_items
BEGIN
    UPDATE outlook_snapshot
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
        status,
        last_updated_at
    ) VALUES (
        NEW.task_id,
        (SELECT COUNT(*) FROM mail_tasks WHERE task_id = NEW.task_id),
        'pending',
        CURRENT_TIMESTAMP
    );
END;

-- メール取得成功時にmail_idを更新するトリガー
CREATE TRIGGER IF NOT EXISTS update_mail_id_on_success AFTER UPDATE ON mail_tasks
WHEN NEW.mail_fetch_status = 'success' AND OLD.mail_fetch_status != 'success' AND NEW.mail_id IS NULL
BEGIN
    UPDATE mail_tasks
    SET mail_id = (
        SELECT entry_id FROM mail_items 
        WHERE entry_id = NEW.message_id
        ORDER BY processed_at DESC LIMIT 1
    )
    WHERE id = NEW.id;
END;

-- GUARDIAN処理タイプのメールがエラーになった場合は特殊処理を行うトリガー
-- 注意: mail_tasksテーブルにprocess_typeカラムがないため一時的に無効化
/*
CREATE TRIGGER IF NOT EXISTS handle_guardian_mail_error AFTER UPDATE ON mail_tasks
WHEN NEW.mail_fetch_status = 'error' AND OLD.mail_fetch_status != 'error' AND NEW.process_type = 'GUARDIAN'
BEGIN
    UPDATE mail_tasks
    SET 
        mail_fetch_status = 'success',
        status = 'completed',
        error_message = 'GUARDIANタイプのため自動成功扱い',
        completed_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;
*/

-- process_typeを同期させるトリガー（mail_itemsのprocess_type更新時）
-- 注意: mail_tasksテーブルにprocess_typeカラムがないため一時的に無効化
/*
CREATE TRIGGER IF NOT EXISTS sync_process_type_on_mail_items_update AFTER UPDATE ON mail_items
WHEN NEW.process_type IS NOT NULL AND (OLD.process_type IS NULL OR NEW.process_type != OLD.process_type)
BEGIN
    UPDATE mail_tasks
    SET process_type = NEW.process_type
    WHERE message_id = NEW.entry_id;
END;
*/

-- process_typeを同期させるトリガー（mail_items挿入時）
-- 注意: mail_tasksテーブルにprocess_typeカラムがないため一時的に無効化
/*
CREATE TRIGGER IF NOT EXISTS sync_process_type_on_mail_items_insert AFTER INSERT ON mail_items
WHEN NEW.process_type IS NOT NULL
BEGIN
    UPDATE mail_tasks
    SET process_type = NEW.process_type
    WHERE message_id = NEW.entry_id;
END;
*/
