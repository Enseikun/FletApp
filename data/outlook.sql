-- フォルダ一覧
CREATE TABLE IF NOT EXISTS folders (
    entry_id TEXT PRIMARY KEY,
    store_id TEXT NOT NULL,
    name TEXT NOT NULL,
    path TEXT NOT NULL,
    item_count INTEGER DEFAULT 0,
    unread_count INTEGER DEFAULT 0,
    parent_folder_id TEXT,
    folder_type TEXT,
    folder_class TEXT,
    last_sync TEXT CHECK (
        last_sync IS NULL OR (
            datetime(last_sync) IS NOT NULL AND
            length(last_sync) = 19 AND
            last_sync LIKE '____-__-__ __:__:__'
        )
    ),
    created_at TIMESTAMP NOT NULL CHECK (
        datetime(created_at) IS NOT NULL AND
        created_at LIKE '____-__-__ __:__:__'
    ),
    updated_at TIMESTAMP NOT NULL CHECK (
        datetime(updated_at) IS NOT NULL AND
        updated_at LIKE '____-__-__ __:__:__'
    ),
    FOREIGN KEY (parent_folder_id) REFERENCES folders(entry_id),
    FOREIGN KEY (store_id) REFERENCES accounts(store_id),
    UNIQUE (store_id, entry_id)
);

-- Outlookアカウント情報（ログイン済みアカウントのみ）
CREATE TABLE IF NOT EXISTS accounts (
    store_id TEXT PRIMARY KEY,
    displayname TEXT NOT NULL,
    email_address TEXT,
    last_sync TEXT CHECK (
        last_sync IS NULL OR (
            datetime(last_sync) IS NOT NULL AND
            length(last_sync) = 19 AND
            last_sync LIKE '____-__-__ __:__:__'
        )
    ),
    created_at TIMESTAMP NOT NULL CHECK (
        datetime(created_at) IS NOT NULL AND
        created_at LIKE '____-__-__ __:__:__'
    ),
    updated_at TIMESTAMP NOT NULL CHECK (
        datetime(updated_at) IS NOT NULL AND
        updated_at LIKE '____-__-__ __:__:__'
    )
);

-- アカウントの更新日時を自動更新するトリガー
CREATE TRIGGER IF NOT EXISTS update_account_timestamp AFTER UPDATE ON accounts
BEGIN
    UPDATE accounts
    SET updated_at = strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')
    WHERE store_id = NEW.store_id;
END;

-- インデックス
CREATE INDEX IF NOT EXISTS idx_accounts_email ON accounts(email_address);
CREATE INDEX IF NOT EXISTS idx_accounts_display_name ON accounts(displayname);
CREATE INDEX IF NOT EXISTS idx_folders_store_id ON folders(store_id);
CREATE INDEX IF NOT EXISTS idx_folders_parent_id ON folders(parent_folder_id);
CREATE INDEX IF NOT EXISTS idx_folders_name ON folders(name);
CREATE INDEX IF NOT EXISTS idx_folders_path ON folders(path);