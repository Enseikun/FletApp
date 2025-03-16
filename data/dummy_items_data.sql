-- フォルダデータの挿入
INSERT INTO folders (entry_id, store_id, name, path, item_count, unread_count, parent_folder_id, updated_at) VALUES
('fold_001', 'store_001', 'メールボックス', '/メールボックス', 0, 0, NULL, '2023-01-01 00:00:00'),
('fold_002', 'store_001', '受信トレイ', '/メールボックス/受信トレイ', 0, 0, 'fold_001', '2023-01-01 00:00:00'),
('fold_003', 'store_001', 'アーカイブ', '/メールボックス/アーカイブ', 0, 0, 'fold_001', '2023-01-01 00:00:00'),
('fold_004', 'store_001', '過去メール', '/メールボックス/過去メール', 0, 0, 'fold_001', '2023-01-01 00:00:00'),
('fold_005', 'store_002', '仕事', '/メールボックス/仕事', 0, 0, 'fold_001', '2023-01-01 00:00:00'),
('fold_006', 'store_002', '重要', '/メールボックス/仕事/重要', 0, 0, 'fold_005', '2023-01-01 00:00:00'),
('fold_007', 'store_002', '保管', '/メールボックス/保管', 0, 0, 'fold_001', '2023-01-01 00:00:00'),
('fold_008', 'store_002', '個人', '/メールボックス/個人', 0, 0, 'fold_001', '2023-01-01 00:00:00'),
('fold_009', 'store_002', 'バックアップ', '/メールボックス/バックアップ', 0, 0, 'fold_001', '2023-01-01 00:00:00'),
('fold_010', 'store_003', '重要', '/メールボックス/重要', 0, 0, 'fold_001', '2023-01-01 00:00:00'),
('fold_011', 'store_003', '会議', '/メールボックス/会議', 0, 0, 'fold_001', '2023-01-01 00:00:00'),
('fold_012', 'store_003', '保存', '/メールボックス/保存', 0, 0, 'fold_001', '2023-01-01 00:00:00');

-- メールアイテムの挿入
INSERT INTO mail_items (
    entry_id, conversation_id, conversation_index, thread_id, thread_depth,
    message_type, parent_entry_id, parent_folder_name, destination, message_size, unread,
    subject, sent_time, received_time, importance, body, attachments_count, folder_id
) VALUES
-- 受信トレイのメール
('mail_001', 'conv_001', 'idx_001', 'thread_001', 0, 'email', NULL, NULL, 'user@example.com', 1024, 1, '会議のお知らせ', '2023-01-10 09:00:00', '2023-01-10 09:01:00', 1, 'こんにちは、明日の会議について連絡します。', 0, 'fold_002'),
('mail_002', 'conv_002', 'idx_002', 'thread_002', 0, 'email', NULL, NULL, 'user@example.com', 2048, 0, 'プロジェクト進捗報告', '2023-01-15 13:30:00', '2023-01-15 13:31:00', 2, 'プロジェクトの進捗状況をお知らせします。', 1, 'fold_002'),
('mail_003', 'conv_003', 'idx_003', 'thread_003', 0, 'email', NULL, NULL, 'user@example.com', 3072, 1, '重要：システムメンテナンス', '2023-01-20 15:45:00', '2023-01-20 15:46:00', 3, '明日システムメンテナンスを実施します。', 0, 'fold_002'),

-- アーカイブのメール
('mail_004', 'conv_004', 'idx_004', 'thread_004', 0, 'email', NULL, NULL, 'user@example.com', 4096, 0, '過去の議事録', '2022-12-05 10:15:00', '2022-12-05 10:16:00', 1, '先月の会議の議事録を添付します。', 1, 'fold_003'),
('mail_005', 'conv_005', 'idx_005', 'thread_005', 0, 'email', NULL, NULL, 'user@example.com', 5120, 0, '年末報告書', '2022-12-28 16:20:00', '2022-12-28 16:21:00', 2, '年末の報告書をご確認ください。', 2, 'fold_003'),

-- 仕事フォルダのメール
('mail_006', 'conv_006', 'idx_006', 'thread_006', 0, 'email', NULL, NULL, 'user@example.com', 6144, 0, 'クライアントミーティング', '2023-02-03 11:00:00', '2023-02-03 11:01:00', 2, 'クライアントとのミーティングスケジュールです。', 0, 'fold_005'),
('mail_007', 'conv_007', 'idx_007', 'thread_007', 0, 'meeting', NULL, NULL, 'user@example.com', 7168, 0, '週次ミーティング', '2023-02-10 14:30:00', '2023-02-10 14:31:00', 1, '週次ミーティングの議題です。', 0, 'fold_005'),

-- スレッド付きメール
('mail_008', 'conv_008', 'idx_008', 'thread_008', 0, 'email', NULL, NULL, 'user@example.com', 8192, 0, 'Re: プロジェクト計画', '2023-03-01 09:45:00', '2023-03-01 09:46:00', 2, 'プロジェクト計画について返信します。', 0, 'fold_006'),
('mail_009', 'conv_008', 'idx_009', 'thread_008', 1, 'email', 'mail_008', '重要', 'user@example.com', 9216, 1, 'Re: Re: プロジェクト計画', '2023-03-01 10:30:00', '2023-03-01 10:31:00', 2, 'さらに詳細な情報を追加します。', 1, 'fold_006');

-- 参加者の挿入
INSERT INTO participants (mail_id, name, email, participant_type, display_name) VALUES
('mail_001', '山田太郎', 'yamada@example.com', 'from', '山田 太郎'),
('mail_001', '佐藤花子', 'sato@example.com', 'to', '佐藤 花子'),
('mail_001', '鈴木一郎', 'suzuki@example.com', 'cc', '鈴木 一郎'),
('mail_002', '田中次郎', 'tanaka@example.com', 'from', '田中 次郎'),
('mail_002', '佐藤花子', 'sato@example.com', 'to', '佐藤 花子'),
('mail_003', 'システム管理者', 'admin@example.com', 'from', 'システム管理者'),
('mail_003', '全社員', 'all@example.com', 'to', '全社員'),
('mail_004', '会議事務局', 'meeting@example.com', 'from', '会議事務局'),
('mail_004', '部門メンバー', 'team@example.com', 'to', '部門メンバー'),
('mail_005', '経理部', 'accounting@example.com', 'from', '経理部'),
('mail_005', '部門長', 'manager@example.com', 'to', '部門長'),
('mail_006', '営業部', 'sales@example.com', 'from', '営業部'),
('mail_006', 'プロジェクトチーム', 'project@example.com', 'to', 'プロジェクトチーム'),
('mail_007', '会議室予約システム', 'room@example.com', 'from', '会議室予約システム'),
('mail_007', 'チームメンバー', 'members@example.com', 'to', 'チームメンバー'),
('mail_008', '開発リーダー', 'dev@example.com', 'from', '開発リーダー'),
('mail_008', 'エンジニアチーム', 'engineers@example.com', 'to', 'エンジニアチーム'),
('mail_009', 'プロダクトマネージャー', 'pm@example.com', 'from', 'プロダクトマネージャー'),
('mail_009', '開発リーダー', 'dev@example.com', 'to', '開発リーダー');

-- 添付ファイルの挿入
INSERT INTO attachments (mail_id, name, path, size) VALUES
('mail_002', '進捗報告.pdf', '/attachments/mail_002/progress.pdf', 512000),
('mail_004', '議事録.docx', '/attachments/mail_004/minutes.docx', 256000),
('mail_005', '年末報告書.xlsx', '/attachments/mail_005/report1.xlsx', 384000),
('mail_005', '財務データ.xlsx', '/attachments/mail_005/finance.xlsx', 512000),
('mail_009', '計画書.pdf', '/attachments/mail_009/plan.pdf', 768000);

-- ダウンロード計画の挿入
INSERT INTO download_plans (created_at, target_folder_id, status, total_count, completed_count) VALUES
('2023-01-05 08:00:00', 'fold_002', 'completed', 3, 3),
('2023-02-10 09:30:00', 'fold_005', 'completed', 2, 2),
('2023-03-15 14:00:00', 'fold_006', 'in_progress', 2, 1),
('2023-04-20 10:45:00', 'fold_003', 'pending', 2, 0);

-- ダウンロードタスクの挿入
INSERT INTO download_tasks (mail_id, plan_id, message_id, priority, created_at, mail_fetch_status, mail_fetch_at, attachment_status, attachment_at, ai_review_status, ai_review_at) VALUES
('mail_001', 1, 'msg_001', 1, '2023-01-05 08:01:00', 'success', '2023-01-05 08:05:00', 'success', '2023-01-05 08:06:00', 'success', '2023-01-05 08:07:00'),
('mail_002', 1, 'msg_002', 2, '2023-01-05 08:01:00', 'success', '2023-01-05 08:10:00', 'success', '2023-01-05 08:12:00', 'success', '2023-01-05 08:15:00'),
('mail_003', 1, 'msg_003', 3, '2023-01-05 08:01:00', 'success', '2023-01-05 08:20:00', 'not_needed', NULL, 'success', '2023-01-05 08:22:00'),
('mail_006', 2, 'msg_006', 1, '2023-02-10 09:31:00', 'success', '2023-02-10 09:35:00', 'not_needed', NULL, 'success', '2023-02-10 09:37:00'),
('mail_007', 2, 'msg_007', 2, '2023-02-10 09:31:00', 'success', '2023-02-10 09:40:00', 'not_needed', NULL, 'success', '2023-02-10 09:42:00'),
('mail_008', 3, 'msg_008', 1, '2023-03-15 14:01:00', 'success', '2023-03-15 14:05:00', 'not_needed', NULL, 'success', '2023-03-15 14:07:00'),
('mail_009', 3, 'msg_009', 2, '2023-03-15 14:01:00', 'in_progress', NULL, 'pending', NULL, 'pending', NULL),
('mail_004', 4, 'msg_004', 1, '2023-04-20 10:46:00', 'pending', NULL, 'pending', NULL, 'pending', NULL),
('mail_005', 4, 'msg_005', 2, '2023-04-20 10:46:00', 'pending', NULL, 'pending', NULL, 'pending', NULL); 