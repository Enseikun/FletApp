-- アーカイブ情報テーブル
CREATE TABLE IF NOT EXISTS task_info (
    -- PRIMARY KEYの制約を強化
    id TEXT PRIMARY KEY CHECK (
        length(id) = 14 AND
        id GLOB '[0-9]*' AND
        cast(substr(id, 1, 4) as integer) BETWEEN 2000 AND 2100 AND
        cast(substr(id, 5, 2) as integer) BETWEEN 1 AND 12 AND
        cast(substr(id, 7, 2) as integer) BETWEEN 1 AND 31 AND
        cast(substr(id, 9, 2) as integer) BETWEEN 0 AND 23 AND
        cast(substr(id, 11, 2) as integer) BETWEEN 0 AND 59 AND
        cast(substr(id, 13, 2) as integer) BETWEEN 0 AND 59
    ),
    account_id TEXT NOT NULL,
    folder_id TEXT NOT NULL,
    from_folder_id TEXT NOT NULL,
    from_folder_name TEXT NOT NULL,
    from_folder_path TEXT NOT NULL,
    to_folder_id TEXT,
    to_folder_name TEXT,
    to_folder_path TEXT,
    
    -- TIMESTAMP型の制約を強化
    start_date TIMESTAMP NOT NULL CHECK (
        datetime(start_date) IS NOT NULL AND
        start_date LIKE '____-__-__ __:__:__'
    ),
    end_date TIMESTAMP NOT NULL CHECK (
        datetime(end_date) IS NOT NULL AND
        end_date LIKE '____-__-__ __:__:__' AND
        end_date >= start_date
    ),

    mail_count INTEGER DEFAULT 0 CHECK (mail_count >= 0),
    ai_review BOOLEAN DEFAULT 1,
    file_download BOOLEAN DEFAULT 1,
    exclude_extensions TEXT,

    created_at TIMESTAMP CHECK (
        datetime(created_at) IS NOT NULL AND
        created_at LIKE '____-__-__ __:__:__'
    ),
    updated_at TIMESTAMP CHECK (
        datetime(updated_at) IS NOT NULL AND
        updated_at LIKE '____-__-__ __:__:__'
    ),

    -- ステータスの制約を追加
    status TEXT DEFAULT 'created' CHECK (
        status IN ('created', 'processing', 'completed', 'error')
    ),

    -- エラーメッセージの制約を追加
    error_message TEXT,

    -- 外部キー制約
    FOREIGN KEY (account_id) REFERENCES accounts(store_id),
    FOREIGN KEY (folder_id) REFERENCES folders(entry_id),
    FOREIGN KEY (from_folder_id) REFERENCES folders(entry_id),
    FOREIGN KEY (to_folder_id) REFERENCES folders(entry_id)
);

-- 既存のインデックスに加えて作成日時のインデックスを追加
CREATE INDEX IF NOT EXISTS idx_task_info_created_at ON task_info (created_at);

-- 複合インデックスの追加
CREATE INDEX IF NOT EXISTS idx_task_info_account_status ON task_info (account_id, status);   
