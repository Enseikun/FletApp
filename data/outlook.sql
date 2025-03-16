-- Outlookアカウント情報（ログイン済みアカウントのみ）
CREATE TABLE IF NOT EXISTS accounts (
    entry_id TEXT PRIMARY KEY,
    store_id TEXT NOT NULL,
    displayname TEXT NOT NULL,
    email_address TEXT,
    is_default BOOLEAN DEFAULT 0,
    last_sync TEXT CHECK (
        last_sync IS NULL OR (
            datetime(last_sync) IS NOT NULL AND
            length(last_sync) = 19 AND
            last_sync LIKE '____-__-__ __:__:__'
        )
    ),
    created_at TIMESTAMP NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')),
    updated_at TIMESTAMP NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime'))
);

-- アカウントとフォルダの関連付け（items.sqlのfoldersテーブルと紐づける）
CREATE TABLE IF NOT EXISTS outlook_folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    folder_id TEXT NOT NULL,
    is_default_inbox BOOLEAN DEFAULT 0,
    is_default_sent BOOLEAN DEFAULT 0,
    is_favorite BOOLEAN DEFAULT 0,
    last_sync TEXT CHECK (
        last_sync IS NULL OR (
            datetime(last_sync) IS NOT NULL AND
            length(last_sync) = 19 AND
            last_sync LIKE '____-__-__ __:__:__'
        )
    ),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')),
    FOREIGN KEY (account_id) REFERENCES accounts(entry_id),
    FOREIGN KEY (folder_id) REFERENCES folders(entry_id),
    UNIQUE (account_id, folder_id)
);

-- フォルダのデフォルト設定に関する制約
-- 各アカウントに対して各タイプのデフォルトフォルダは１つ存在できる
CREATE TRIGGER IF NOT EXISTS ensure_single_default_inbox AFTER INSERT ON outlook_folders
WHEN NEW.is_default_inbox = 1
BEGIN
    UPDATE outlook_folders
    SET is_default_inbox = 0
    WHERE account_id = NEW.account_id AND id != NEW.id AND is_default_inbox = 1;
END;

CREATE TRIGGER IF NOT EXISTS ensure_single_default_sent AFTER INSERT ON outlook_folders
WHEN NEW.is_default_sent = 1
BEGIN
    UPDATE outlook_folders
    SET is_default_sent = 0
    WHERE account_id = NEW.account_id AND id != NEW.id AND is_default_sent = 1;
END;

-- アカウントの更新日時を自動更新するトリガー
CREATE TRIGGER IF NOT EXISTS update_account_timestamp AFTER UPDATE ON accounts
BEGIN
    UPDATE accounts
    SET updated_at = strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')
    WHERE entry_id = NEW.entry_id;
END;

-- インデックス
CREATE INDEX IF NOT EXISTS idx_accounts_email ON accounts(email_address);
CREATE INDEX IF NOT EXISTS idx_accounts_display_name ON accounts(displayname);
CREATE INDEX IF NOT EXISTS idx_outlook_folders_account_id ON outlook_folders(account_id);
CREATE INDEX IF NOT EXISTS idx_outlook_folders_folder_id ON outlook_folders(folder_id);