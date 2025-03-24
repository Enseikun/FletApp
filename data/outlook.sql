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

-- アカウントとフォルダの関連付け（items.sqlのfoldersテーブルと紐づける）
CREATE TABLE IF NOT EXISTS outlook_folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    folder_id TEXT NOT NULL,
    parent_folder_id TEXT,
    name TEXT NOT NULL,
    folder_path TEXT NOT NULL,
    last_sync TEXT CHECK (
        last_sync IS NULL OR (
            datetime(last_sync) IS NOT NULL AND
            length(last_sync) = 19 AND
            last_sync LIKE '____-__-__ __:__:__'
        )
    ),
    created_at TEXT NOT NULL CHECK (
        datetime(created_at) IS NOT NULL AND
        created_at LIKE '____-__-__ __:__:__'
    ),
    FOREIGN KEY (account_id) REFERENCES accounts(store_id),
    FOREIGN KEY (folder_id) REFERENCES folders(entry_id),
    FOREIGN KEY (parent_folder_id) REFERENCES outlook_folders(folder_id),
    UNIQUE (account_id, folder_id)
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
CREATE INDEX IF NOT EXISTS idx_outlook_folders_account_id ON outlook_folders(account_id);
CREATE INDEX IF NOT EXISTS idx_outlook_folders_folder_id ON outlook_folders(folder_id);
CREATE INDEX IF NOT EXISTS idx_outlook_folders_parent_id ON outlook_folders(parent_folder_id);
CREATE INDEX IF NOT EXISTS idx_outlook_folders_name ON outlook_folders(name);
CREATE INDEX IF NOT EXISTS idx_outlook_folders_path ON outlook_folders(folder_path);