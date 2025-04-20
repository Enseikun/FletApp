"""
プレビューコンテンツのビューモデル
メールプレビュー画面のデータ処理を担当
"""

import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import flet as ft  # サンプルコードの色設定用

from src.core.logger import get_logger
from src.models.preview_content_model import PreviewContentModel
from src.util.object_util import get_safe


class PreviewContentViewModel:
    """プレビューコンテンツのビューモデル"""

    def __init__(self, task_id: Optional[str] = None):
        """
        初期化

        Args:
            task_id: タスクID
        """
        self.logger = get_logger()
        self.logger.info("PreviewContentViewModel: 初期化開始", task_id=task_id)
        self.task_id = task_id
        # モデルのインスタンス化
        self.model = PreviewContentModel(task_id)

        # 現在選択されているフォルダID
        self.current_folder_id = None

        # キャッシュされたメールリスト
        self.cached_mail_list = []

        # サンプルデータフラグ - task_idが指定されていない場合のみサンプルデータを使用
        self.use_sample_data = False
        self.logger.debug(
            f"PreviewContentViewModel: サンプルデータ使用フラグ設定 - {self.use_sample_data}"
        )

        # サンプルデータ
        self.sample_mails = []

        # フラグ状態の変更を記録する辞書
        self.pending_flag_changes = {}
        # 既読状態の変更を記録する辞書
        self.pending_read_changes = {}
        # 最後にDBに変更をコミットした時間
        self.last_commit_time = time.time()  # 初期値を現在時刻に設定
        # 自動コミットの間隔（秒）
        self.auto_commit_interval = 5.0

        self.logger.info("PreviewContentViewModel: 初期化完了")

    def get_task_info(self) -> Optional[Dict[str, Any]]:
        """
        タスク情報を取得

        Returns:
            Optional[Dict[str, Any]]: タスク情報、取得できない場合はNone
        """
        self.logger.debug("PreviewContentViewModel: タスク情報取得開始")
        result = self.model.get_task_info()
        if result:
            self.logger.debug(
                "PreviewContentViewModel: タスク情報取得成功", task_info=result
            )
        else:
            self.logger.warning(
                "PreviewContentViewModel: タスク情報が見つかりません",
                task_id=self.task_id,
            )
        return result

    def get_folders(self) -> List[Dict[str, Any]]:
        """
        フォルダ一覧を取得

        Returns:
            List[Dict[str, Any]]: フォルダ情報のリスト
        """
        self.logger.debug("PreviewContentViewModel: フォルダ一覧取得開始")
        folders = self.model.get_folders()
        self.logger.debug(
            "PreviewContentViewModel: フォルダ一覧取得完了", folder_count=len(folders)
        )
        return folders

    def load_folder_mails(self, folder_id: str) -> List[Dict[str, Any]]:
        """
        指定フォルダのメール一覧を取得

        Args:
            folder_id: フォルダID

        Returns:
            List[Dict[str, Any]]: メール情報のリスト
        """
        self.logger.info(
            "PreviewContentViewModel: フォルダメール取得開始", folder_id=folder_id
        )
        self.current_folder_id = folder_id

        # モデルからデータを取得
        mail_list = self.model.load_folder_mails(folder_id)

        # データの整合性を確保
        formatted_mails = [self._ensure_mail_fields(mail) for mail in mail_list]

        # キャッシュに保存
        self.cached_mail_list = formatted_mails

        self.logger.info(
            "PreviewContentViewModel: フォルダメール取得完了",
            folder_id=folder_id,
            mail_count=len(self.cached_mail_list),
        )
        return self.cached_mail_list

    def get_all_mails(self, sort_order: str = "date_desc") -> List[Dict[str, Any]]:
        """
        すべてのメールを取得し、指定された順序でソートする

        Args:
            sort_order: ソート順（"date_desc", "date_asc", "subject", "sender"）

        Returns:
            List[Dict[str, Any]]: ソートされたメールリスト
        """
        self.logger.info(
            "PreviewContentViewModel: すべてのメール取得開始", sort_order=sort_order
        )

        # 実際のデータを取得
        mail_list = self.model.get_all_mails()

        # データの整合性チェックと補完
        formatted_mails = [self._ensure_mail_fields(mail) for mail in mail_list]

        # キャッシュに保存
        self.cached_mail_list = formatted_mails

        # ソート
        sorted_mails = self.sort_mails(formatted_mails, sort_order)

        self.logger.info(
            "PreviewContentViewModel: すべてのメール取得完了",
            mail_count=len(sorted_mails),
        )
        return sorted_mails

    def search_mails(
        self, search_term: str, sort_order: str = "date_desc"
    ) -> List[Dict[str, Any]]:
        """
        メールを検索し、指定された順序でソートする

        Args:
            search_term: 検索語句
            sort_order: ソート順（"date_desc", "date_asc", "subject", "sender"）

        Returns:
            List[Dict[str, Any]]: ソートされた検索結果
        """
        self.logger.info(
            "PreviewContentViewModel: メール検索開始",
            search_term=search_term,
            sort_order=sort_order,
        )

        # 実際のデータを検索
        result = self.model.search_mails(search_term)

        # データの整合性チェックと補完
        formatted_results = [self._ensure_mail_fields(mail) for mail in result]

        # 検索結果をソート
        sorted_result = self.sort_mails(formatted_results, sort_order)

        self.logger.info(
            "PreviewContentViewModel: メール検索完了",
            search_term=search_term,
            result_count=len(sorted_result),
        )
        return sorted_result

    def get_mail_content(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """
        メールの内容を取得

        Args:
            entry_id: メールID

        Returns:
            Optional[Dict[str, Any]]: メール情報、取得できない場合はNone
        """
        self.logger.debug("PreviewContentViewModel: メール内容取得", entry_id=entry_id)

        # 実際のデータを取得
        result = self.model.get_mail_content(entry_id)

        if result:
            # データの整合性チェックと補完
            result = self._ensure_mail_fields(result)
            self.logger.debug(
                "PreviewContentViewModel: メール内容取得成功", entry_id=entry_id
            )
        else:
            self.logger.warning(
                "PreviewContentViewModel: メール内容が見つかりません", entry_id=entry_id
            )
        return result

    def _ensure_mail_fields(self, mail: Dict[str, Any]) -> Dict[str, Any]:
        """
        メールデータに必要なフィールドがすべて存在するか確認し、
        ない場合は適切なデフォルト値を設定する

        Args:
            mail: 確認するメールデータ

        Returns:
            Dict[str, Any]: 補完されたメールデータ
        """
        # 必須フィールドとデフォルト値のマッピング
        required_fields = {
            "id": lambda: mail.get("entry_id", ""),
            "subject": "(件名なし)",
            "sender": "不明 <unknown@example.com>",
            "recipient": "不明 <unknown@example.com>",
            "date": "不明な日時",
            "content": "",
            "unread": 0,
            "attachments": [],
            "flagged": False,
        }

        # すべての必須フィールドを確認し、なければデフォルト値を設定
        for field, default_value in required_fields.items():
            if field not in mail or mail[field] is None:
                # デフォルト値が関数の場合は呼び出す
                if callable(default_value):
                    mail[field] = default_value()
                else:
                    mail[field] = default_value

        return mail

    def mark_as_read(self, entry_id: str) -> Tuple[bool, str]:
        """
        メールを既読にする

        Args:
            entry_id: メールID

        Returns:
            Tuple[bool, str]: (成功したかどうか, メッセージ)
        """
        self.logger.debug("PreviewContentViewModel: メール既読設定", entry_id=entry_id)

        # キャッシュ内のメールの既読状態を更新
        mail = self._get_mail_from_cache(entry_id)
        if mail and mail.get("unread", 0) > 0:
            # キャッシュを更新
            self._update_mail_read_status_in_cache(entry_id)

            # 保留中の既読変更に追加
            self.pending_read_changes[entry_id] = True

            # 自動コミットの判断
            self._check_auto_commit()

            return True, "メールを既読に設定しました"

        # すでに既読か、キャッシュにメールがない場合は直接DBを更新
        success, message = self.model.mark_as_read(entry_id)

        if success and mail:
            mail["unread"] = 0

        return success, message

    def _update_mail_read_status_in_cache(self, entry_id: str) -> None:
        """
        キャッシュ内のメールの既読状態を更新

        Args:
            entry_id: メールID
        """
        for mail in self.cached_mail_list:
            if mail.get("id") == entry_id:
                mail["unread"] = 0
                break

    def get_mail_flag(self, entry_id: str) -> bool:
        """
        メールのフラグ状態を取得

        Args:
            entry_id: メールID

        Returns:
            bool: フラグ状態（立っていればTrue）
        """
        self.logger.debug(
            "PreviewContentViewModel: メールフラグ状態取得", entry_id=entry_id
        )
        mail = self._get_mail_from_cache(entry_id)
        return mail.get("flagged", False) if mail else False

    def set_mail_flag(self, entry_id: str, flagged: bool) -> Tuple[bool, str]:
        """
        メールのフラグ状態を設定（UIのみの更新）

        Args:
            entry_id: メールID
            flagged: フラグを立てるかどうか

        Returns:
            Tuple[bool, str]: (成功したかどうか, メッセージ)
        """
        self.logger.debug(
            "PreviewContentViewModel: メールフラグ設定(UI)",
            entry_id=entry_id,
            flagged=flagged,
        )

        # 現在のフラグ状態を取得
        current_mail = self._get_mail_from_cache(entry_id)
        if not current_mail:
            return False, "指定されたメールが見つかりません"

        current_flagged = current_mail.get("flagged", False)

        # 現在の状態と目的の状態が同じなら何もしない
        if current_flagged == flagged:
            return True, f"フラグ状態は既に{'オン' if flagged else 'オフ'}です"

        # キャッシュ内のメールのフラグ状態を更新
        self._update_mail_flag_in_cache(entry_id, flagged)

        # 変更を保留リストに追加
        self.pending_flag_changes[entry_id] = flagged

        # 自動コミットの判断
        self._check_auto_commit()

        return True, f"フラグを{'追加' if flagged else '解除'}しました"

    def _check_auto_commit(self):
        """自動コミットが必要かチェックし、必要ならコミットを実行する"""
        try:
            # 保留中の変更がなければ何もしない
            if not self.pending_flag_changes and not self.pending_read_changes:
                return

            now = time.time()
            elapsed = now - self.last_commit_time
            if elapsed >= self.auto_commit_interval:
                self.logger.debug(
                    f"自動コミット実行: フラグ{len(self.pending_flag_changes)}件、既読{len(self.pending_read_changes)}件の変更"
                )

                # 別スレッドでコミットを実行（UIブロッキングを防止）
                commit_thread = threading.Thread(
                    target=self._commit_changes, name="AutoCommitThread"
                )
                commit_thread.daemon = True  # メインスレッド終了時に強制終了
                commit_thread.start()

                # 最終コミット時間を更新
                self.last_commit_time = now
        except Exception as e:
            self.logger.error(f"自動コミットチェック中にエラー: {e}")

    def _commit_changes(self):
        """保留中のフラグと既読変更をデータベースにコミット"""
        # フラグ変更をコミット
        if self.pending_flag_changes:
            self.commit_flag_changes()

        # 既読変更をコミット
        if self.pending_read_changes:
            self.commit_read_changes()

    def commit_read_changes(self):
        """保留中の既読変更をデータベースにコミット"""
        if not self.pending_read_changes:
            self.logger.debug("コミット対象の既読変更がありません")
            return True

        try:
            self.logger.info(
                f"既読変更コミット開始: {len(self.pending_read_changes)}件"
            )

            # 現在の保留変更をコピーしてローカル変数に保存
            changes_to_commit = self.pending_read_changes.copy()
            success_count = 0
            failed_ids = []

            # 各既読変更を個別に処理
            for mail_id in changes_to_commit:
                try:
                    # モデルに既読変更を通知
                    success, _ = self.model.mark_as_read(mail_id)

                    if success:
                        # コミット成功したアイテムをリストから削除
                        if mail_id in self.pending_read_changes:
                            del self.pending_read_changes[mail_id]
                        success_count += 1
                    else:
                        # 失敗したIDを記録
                        failed_ids.append(mail_id)
                except Exception as e:
                    self.logger.error(f"メールID {mail_id} の既読更新に失敗: {e}")
                    failed_ids.append(mail_id)

            # 結果をログに記録
            if failed_ids:
                self.logger.warning(
                    f"既読変更コミット: {success_count}件成功, {len(failed_ids)}件失敗"
                )
            else:
                self.logger.info(f"既読変更コミット完了: {success_count}件すべて成功")

            return len(failed_ids) == 0

        except Exception as e:
            self.logger.error(f"既読変更コミット中にエラー: {e}")
            return False

    def commit_flag_changes(self):
        """保留中のフラグ変更をデータベースにコミット"""
        if not self.pending_flag_changes:
            self.logger.debug("コミット対象の変更がありません")
            return True

        try:
            self.logger.info(
                f"フラグ変更コミット開始: {len(self.pending_flag_changes)}件"
            )

            # 現在の保留変更をコピーしてローカル変数に保存
            changes_to_commit = self.pending_flag_changes.copy()
            success_count = 0
            failed_ids = []

            # 各フラグ変更を個別に処理
            for mail_id, flag_value in changes_to_commit.items():
                try:
                    # モデルにフラグ変更を通知
                    success, _, _ = self.model.toggle_flag(mail_id, flag_value)

                    if success:
                        # コミット成功したアイテムをリストから削除
                        if mail_id in self.pending_flag_changes:
                            del self.pending_flag_changes[mail_id]
                        success_count += 1
                    else:
                        # 失敗したIDを記録
                        failed_ids.append(mail_id)
                except Exception as e:
                    self.logger.error(f"メールID {mail_id} のフラグ更新に失敗: {e}")
                    failed_ids.append(mail_id)

            # 結果をログに記録
            if failed_ids:
                self.logger.warning(
                    f"フラグ変更コミット: {success_count}件成功, {len(failed_ids)}件失敗"
                )
            else:
                self.logger.info(f"フラグ変更コミット完了: {success_count}件すべて成功")

            return len(failed_ids) == 0

        except Exception as e:
            self.logger.error(f"フラグ変更コミット中にエラー: {e}")
            return False

    def _get_mail_from_cache(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """キャッシュからメール情報を取得"""
        for mail in self.cached_mail_list:
            if mail.get("id") == entry_id:
                return mail
        return None

    def _update_mail_flag_in_cache(self, entry_id: str, flagged: bool) -> None:
        """
        キャッシュ内のメールのフラグ状態を更新

        Args:
            entry_id: メールID
            flagged: フラグ状態
        """
        for mail in self.cached_mail_list:
            if mail.get("id") == entry_id:
                mail["flagged"] = flagged
                break

    def download_attachment(self, file_id: str) -> Tuple[bool, str, Optional[str]]:
        """
        添付ファイルをダウンロード

        Args:
            file_id: 添付ファイルID

        Returns:
            Tuple[bool, str, Optional[str]]: (成功したかどうか, メッセージ, 保存されたパス)
        """
        self.logger.info(
            "PreviewContentViewModel: 添付ファイルダウンロード", file_id=file_id
        )

        # モデルにメソッドが実装されているか確認
        if not hasattr(self.model, "download_attachment"):
            error_msg = "添付ファイルダウンロードメソッドが実装されていません"
            self.logger.error(f"PreviewContentViewModel: {error_msg}")
            return False, error_msg, None

        # 実際のデータを処理
        success, message, file_path = self.model.download_attachment(file_id)

        if success:
            self.logger.debug(
                "PreviewContentViewModel: 添付ファイルダウンロード成功",
                file_id=file_id,
                file_path=file_path,
                message=message,
            )
        else:
            self.logger.error(
                "PreviewContentViewModel: 添付ファイルダウンロード失敗",
                file_id=file_id,
                message=message,
            )

        return success, message, file_path

    def close(self) -> bool:
        """リソースを解放して終了準備を行う"""
        try:
            self.logger.info("PreviewContentViewModel: クローズ処理開始")

            # 保留中の変更があれば強制的にコミット
            has_pending_changes = bool(
                self.pending_flag_changes or self.pending_read_changes
            )
            if has_pending_changes:
                self.logger.info(
                    f"クローズ前の最終コミット: フラグ{len(self.pending_flag_changes)}件、既読{len(self.pending_read_changes)}件"
                )
                # まずフラグ変更をコミット
                if self.pending_flag_changes:
                    flag_commit_success = self.commit_flag_changes()
                    if flag_commit_success:
                        self.logger.info("フラグ最終コミット: 成功")
                    else:
                        self.logger.warning("フラグ最終コミット: 失敗")

                # 次に既読変更をコミット
                if self.pending_read_changes:
                    read_commit_success = self.commit_read_changes()
                    if read_commit_success:
                        self.logger.info("既読最終コミット: 成功")
                    else:
                        self.logger.warning("既読最終コミット: 失敗")

            # リソース解放
            if hasattr(self, "model") and self.model:
                self.model.close()

            # 保留中変更リストをクリア
            self.pending_flag_changes.clear()
            self.pending_read_changes.clear()

            self.logger.info("PreviewContentViewModel: クローズ処理完了")
            return True
        except Exception as e:
            self.logger.error(f"PreviewContentViewModel クローズ中にエラー: {e}")
            return False

    def get_thread_risk_score(self, mails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        会話のリスクスコアを取得

        Args:
            mails: 会話に含まれるメールのリスト

        Returns:
            Dict[str, Any]: リスク評価情報を含む辞書
        """
        self.logger.debug(
            "PreviewContentViewModel: 会話リスクスコア取得",
            mail_count=len(mails) if mails else 0,
        )

        # メールがない場合はデフォルト値を返す
        if not mails:
            return self._create_default_risk_score("不明", "リスク評価が利用できません")

        # 会話IDを取得
        thread_id = self._get_thread_id_from_mails(mails)

        # 会話IDがない場合はデフォルト値を返す
        if not thread_id:
            return self._create_default_risk_score(
                "不明", "会話IDがないためリスク評価が利用できません"
            )

        # AIレビュー結果を取得
        ai_review = self._get_ai_review_for_thread(thread_id, mails)

        # AIレビュー結果がない場合はデフォルト値を返す
        if not ai_review:
            return self._create_default_risk_score(
                "評価なし", "AIによる評価が実施されていません"
            )

        # スコアに基づくリスクレベルを計算
        return self._calculate_risk_level_from_score(ai_review)

    def _get_thread_id_from_mails(self, mails: List[Dict[str, Any]]) -> Optional[str]:
        """会話IDを取得"""
        for mail in mails:
            if mail.get("thread_id"):
                return mail["thread_id"]
        return None

    def _get_ai_review_for_thread(
        self, thread_id: str, mails: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """AIレビュー結果を取得"""
        # モデルからAIレビュー結果を取得
        ai_review = self.model.get_ai_review_for_thread(thread_id)

        # モデルから取得できない場合は、メールに含まれているAIレビュー結果を使用
        if not ai_review and mails and mails[0].get("ai_review"):
            ai_review = mails[0]["ai_review"]

        return ai_review

    def _create_default_risk_score(self, label: str, tooltip: str) -> Dict[str, Any]:
        """デフォルトのリスクスコアを作成"""
        return {
            "label": label,
            "color": ft.colors.GREY,
            "score": 0,
            "tooltip": tooltip,
        }

    def _calculate_risk_level_from_score(
        self, ai_review: Dict[str, Any]
    ) -> Dict[str, Any]:
        """スコアからリスクレベルを計算"""
        try:
            # AIレビュー情報からスコアを取得
            score = get_safe(ai_review, "score", 0)

            # スコアに応じてリスクレベルを設定
            if score > 3:
                return {
                    "label": "高",
                    "color": ft.colors.RED,
                    "score": 3,
                    "tooltip": get_safe(
                        ai_review,
                        "review",
                        "複数の注意点があります。内容を慎重に確認してください。",
                    ),
                }
            elif score > 1:
                return {
                    "label": "中",
                    "color": ft.colors.ORANGE,
                    "score": 2,
                    "tooltip": get_safe(
                        ai_review,
                        "review",
                        "いくつかの注意点があります。確認を推奨します。",
                    ),
                }
            elif score > 0:
                return {
                    "label": "低",
                    "color": ft.colors.YELLOW,
                    "score": 1,
                    "tooltip": get_safe(
                        ai_review, "review", "軽微な注意点があります。"
                    ),
                }
            else:
                return {
                    "label": "なし",
                    "color": ft.colors.GREEN,
                    "score": 0,
                    "tooltip": get_safe(
                        ai_review, "review", "特に問題は見つかりませんでした。"
                    ),
                }
        except Exception as e:
            self.logger.error(f"リスクスコア取得エラー: {e}")
            return {
                "label": "エラー",
                "color": ft.colors.GREY,
                "score": 0,
                "tooltip": f"リスク評価の取得中にエラーが発生しました: {str(e)}",
            }

    def parse_sender_info(self, sender: str) -> Tuple[str, str]:
        """
        送信者情報を解析して名前とメールアドレスに分割する

        Args:
            sender: 送信者情報文字列（例: "山田太郎 <yamada@example.com>"）

        Returns:
            Tuple[str, str]: (sender_name, sender_email)のタプル
        """
        self.logger.debug("PreviewContentViewModel: 送信者情報解析", sender=sender)

        if not sender or not isinstance(sender, str):
            return "不明", "unknown@example.com"

        try:
            return self._extract_name_and_email_from_sender(sender)
        except Exception as e:
            self.logger.error(f"送信者情報解析エラー: {str(e)}", sender=sender)
            return "不明", "unknown@example.com"

    def _extract_name_and_email_from_sender(self, sender: str) -> Tuple[str, str]:
        """送信者文字列から名前とメールアドレスを抽出"""
        if "<" in sender:
            sender_name = sender.split("<")[0].strip()
            sender_email = sender.split("<")[1].replace(">", "").strip()
        else:
            sender_name = ""
            sender_email = sender.strip()

        # 名前が空の場合はメールアドレスを名前として使用
        if not sender_name:
            sender_name = sender_email

        return sender_name, sender_email

    def sort_mails(
        self, mails: List[Dict[str, Any]], sort_order: str = "date_desc"
    ) -> List[Dict[str, Any]]:
        """
        メールを指定された順序でソートする

        Args:
            mails: ソートするメールのリスト
            sort_order: ソート順（"date_desc", "date_asc", "subject", "sender"）

        Returns:
            List[Dict[str, Any]]: ソートされたメールリスト
        """
        self.logger.debug(
            "PreviewContentViewModel: メールソート", sort_order=sort_order
        )

        if not mails:
            return []

        try:
            return self._sort_mails_by_order(mails, sort_order)
        except Exception as e:
            self.logger.error(f"メールソートエラー: {str(e)}")
            return mails  # エラーが発生した場合は元のリストを返す

    def _sort_mails_by_order(
        self, mails: List[Dict[str, Any]], sort_order: str
    ) -> List[Dict[str, Any]]:
        """指定された順序でメールをソート"""
        if sort_order == "date_asc":
            return sorted(mails, key=lambda x: x.get("date", ""))
        elif sort_order == "date_desc":
            return sorted(mails, key=lambda x: x.get("date", ""), reverse=True)
        elif sort_order == "subject":
            return sorted(mails, key=lambda x: x.get("subject", "").lower())
        elif sort_order == "sender":
            return sorted(mails, key=lambda x: x.get("sender", "").lower())
        else:
            # デフォルトは日付降順
            return sorted(mails, key=lambda x: x.get("date", ""), reverse=True)

    def group_mails_by_thread(
        self, mails: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        メールを会話ID（thread_id）でグループ化する

        Args:
            mails: グループ化するメールのリスト

        Returns:
            Dict[str, List[Dict[str, Any]]]: 会話IDをキー、メールリストを値とする辞書
        """
        self.logger.debug("PreviewContentViewModel: メールのグループ化")

        threads = {}

        # スレッドIDでグループ化
        for mail in mails:
            thread_key = self._get_thread_key_for_mail(mail)

            if thread_key not in threads:
                threads[thread_key] = []
            threads[thread_key].append(mail)

        # 各グループ内でメールを日付順にソート
        for thread_id in threads:
            threads[thread_id] = self.sort_mails(threads[thread_id], "date_desc")

        return threads

    def _get_thread_key_for_mail(self, mail: Dict[str, Any]) -> str:
        """メールのスレッドキーを取得"""
        # thread_idがない場合は単独のメールとして扱う
        if not mail.get("thread_id"):
            # メールIDをキーとして使用
            return f"single_{mail['id']}"

        # thread_id全体をそのまま使用
        return mail["thread_id"]

    def get_thread_summary(self, mails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        会話グループの概要情報を取得する

        Args:
            mails: 会話に含まれるメールのリスト

        Returns:
            Dict[str, Any]: 会話の概要情報を含む辞書
        """
        if not mails:
            return self._create_empty_thread_summary()

        # メールリストを日付の新しい順にソート
        sorted_mails = self.sort_mails(mails, "date_desc")

        # 最新のメール
        latest_mail = sorted_mails[0]

        # 最新のメールの件名を取得
        subject = latest_mail.get("subject") or "(件名なし)"

        # 未読メール数
        unread_count = sum(1 for mail in sorted_mails if mail.get("unread", 0))

        # 添付ファイルの有無
        has_attachments = any(mail.get("attachments") for mail in sorted_mails)

        # リスクスコア
        risk_score = self.get_thread_risk_score(sorted_mails)

        return {
            "subject": subject,
            "latest_date": latest_mail.get("date", "不明な日時"),
            "mail_count": len(sorted_mails),
            "unread_count": unread_count,
            "has_attachments": has_attachments,
            "risk_score": risk_score,
        }

    def _create_empty_thread_summary(self) -> Dict[str, Any]:
        """空の会話概要情報を作成"""
        return {
            "subject": "(件名なし)",
            "latest_date": "不明な日時",
            "mail_count": 0,
            "unread_count": 0,
            "has_attachments": False,
            "risk_score": self._create_default_risk_score(
                "不明", "リスク評価が利用できません"
            ),
        }
