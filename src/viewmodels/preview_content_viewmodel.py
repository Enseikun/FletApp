"""
プレビューコンテンツのビューモデル
メールプレビュー画面のデータ処理を担当
"""

from typing import Any, Dict, List, Optional, Union

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

        self.logger.info("PreviewContentViewModel: 初期化完了")

    def get_task_info(self) -> Optional[Dict]:
        """タスク情報を取得"""
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

    def get_folders(self) -> List[Dict]:
        """フォルダ一覧を取得"""
        self.logger.debug("PreviewContentViewModel: フォルダ一覧取得開始")
        folders = self.model.get_folders()
        self.logger.debug(
            "PreviewContentViewModel: フォルダ一覧取得完了", folder_count=len(folders)
        )
        return folders

    def load_folder_mails(self, folder_id: str) -> List[Dict]:
        """指定フォルダのメール一覧を取得"""
        self.logger.info(
            "PreviewContentViewModel: フォルダメール取得開始", folder_id=folder_id
        )
        self.current_folder_id = folder_id
        self.cached_mail_list = self.model.load_folder_mails(folder_id)
        self.logger.info(
            "PreviewContentViewModel: フォルダメール取得完了",
            folder_id=folder_id,
            mail_count=len(self.cached_mail_list),
        )
        return self.cached_mail_list

    def get_all_mails(self, sort_order: str = "date_desc") -> List[Dict]:
        """
        すべてのメールを取得し、指定された順序でソートする

        Args:
            sort_order: ソート順（"date_desc", "date_asc", "subject", "sender"）

        Returns:
            ソートされたメールリスト
        """
        self.logger.info(
            "PreviewContentViewModel: すべてのメール取得開始", sort_order=sort_order
        )

        # 実際のデータを取得
        self.cached_mail_list = self.model.get_all_mails()

        # データの整合性チェックと補完
        formatted_mails = []
        for mail in self.cached_mail_list:
            formatted_mail = self._ensure_mail_fields(mail)
            formatted_mails.append(formatted_mail)

        # 常に新しい順でソート
        sorted_mails = sorted(formatted_mails, key=lambda x: x["date"], reverse=True)

        self.logger.info(
            "PreviewContentViewModel: すべてのメール取得完了",
            mail_count=len(sorted_mails),
        )
        return sorted_mails

    def search_mails(
        self, search_term: str, sort_order: str = "date_desc"
    ) -> List[Dict]:
        """
        メールを検索し、指定された順序でソートする

        Args:
            search_term: 検索語句
            sort_order: ソート順（"date_desc", "date_asc", "subject", "sender"）

        Returns:
            ソートされた検索結果
        """
        self.logger.info(
            "PreviewContentViewModel: メール検索開始",
            search_term=search_term,
            sort_order=sort_order,
        )

        # 実際のデータを検索
        result = self.model.search_mails(search_term)

        # データの整合性チェックと補完
        formatted_results = []
        for mail in result:
            formatted_mail = self._ensure_mail_fields(mail)
            formatted_results.append(formatted_mail)

        # 検索結果をソート
        sorted_result = self._sort_mails(formatted_results, sort_order)

        self.logger.info(
            "PreviewContentViewModel: メール検索完了",
            search_term=search_term,
            result_count=len(sorted_result),
        )
        return sorted_result

    def get_mail_content(self, entry_id: str) -> Optional[Dict]:
        """メールの内容を取得"""
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

    def _ensure_mail_fields(self, mail: Dict) -> Dict:
        """
        メールデータに必要なフィールドがすべて存在するか確認し、
        ない場合は適切なデフォルト値を設定する

        Args:
            mail: 確認するメールデータ

        Returns:
            補完されたメールデータ
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

    def mark_as_read(self, entry_id: str) -> bool:
        """メールを既読にする"""
        self.logger.debug("PreviewContentViewModel: メール既読設定", entry_id=entry_id)

        # 実際のデータを更新
        result = self.model.mark_as_read(entry_id)
        if result:
            self.logger.debug(
                "PreviewContentViewModel: メール既読設定成功", entry_id=entry_id
            )
        else:
            self.logger.error(
                "PreviewContentViewModel: メール既読設定失敗", entry_id=entry_id
            )
        return result

    def set_mail_flag(self, entry_id: str, flagged: bool) -> bool:
        """メールのフラグ状態を設定"""
        self.logger.debug(
            "PreviewContentViewModel: メールフラグ設定",
            entry_id=entry_id,
            flagged=flagged,
        )

        # 実際のデータを更新
        # 注: 実際のモデルにこのメソッドを実装する必要があります
        if hasattr(self.model, "set_mail_flag"):
            result = self.model.set_mail_flag(entry_id, flagged)
            if result:
                self.logger.debug(
                    "PreviewContentViewModel: メールフラグ設定成功",
                    entry_id=entry_id,
                    flagged=flagged,
                )
            else:
                self.logger.error(
                    "PreviewContentViewModel: メールフラグ設定失敗", entry_id=entry_id
                )
            return result
        else:
            self.logger.error(
                "PreviewContentViewModel: メールフラグ設定メソッドが実装されていません"
            )
            return False

    def download_attachment(self, file_id: str) -> bool:
        """添付ファイルをダウンロード"""
        self.logger.info(
            "PreviewContentViewModel: 添付ファイルダウンロード", file_id=file_id
        )

        # 実際のデータを処理
        # 注: 実際のモデルにこのメソッドを実装する必要があります
        if hasattr(self.model, "download_attachment"):
            result = self.model.download_attachment(file_id)
            if result:
                self.logger.debug(
                    "PreviewContentViewModel: 添付ファイルダウンロード成功",
                    file_id=file_id,
                )
            else:
                self.logger.error(
                    "PreviewContentViewModel: 添付ファイルダウンロード失敗",
                    file_id=file_id,
                )
            return result
        else:
            self.logger.error(
                "PreviewContentViewModel: 添付ファイルダウンロードメソッドが実装されていません"
            )
            return False

    def close(self):
        """リソースを解放"""
        self.logger.info("PreviewContentViewModel: リソース解放")
        self.model.close()

    def get_conversation_risk_score(self, mails: List[Dict]) -> Dict:
        """会話のリスクスコアを取得

        Args:
            mails: 会話に含まれるメールのリスト

        Returns:
            リスク評価情報を含む辞書
        """
        self.logger.debug(
            "PreviewContentViewModel: 会話リスクスコア取得",
            mail_count=len(mails) if mails else 0,
        )

        # メールがない場合はデフォルト値を返す
        if not mails:
            return {
                "label": "不明",
                "color": ft.colors.GREY,
                "score": 0,
                "tooltip": "リスク評価が利用できません",
            }

        # 会話IDを取得
        conversation_id = None
        for mail in mails:
            if mail.get("conversation_id"):
                conversation_id = mail["conversation_id"]
                break

        # 会話IDがない場合はデフォルト値を返す
        if not conversation_id:
            return {
                "label": "不明",
                "color": ft.colors.GREY,
                "score": 0,
                "tooltip": "会話IDがないためリスク評価が利用できません",
            }

        # modelからAIレビュー結果を取得
        ai_review = self.model.get_ai_review_for_conversation(conversation_id)

        # すでにメールに含まれているAIレビュー結果を使用
        if not ai_review and mails and mails[0].get("ai_review"):
            ai_review = mails[0]["ai_review"]

        # AIレビュー結果がない場合はデフォルト値を返す
        if not ai_review:
            return {
                "label": "評価なし",
                "color": ft.colors.GREY,
                "score": 0,
                "tooltip": "AIによる評価が実施されていません",
            }

        # AIレビュー結果からリスクスコアを取得
        try:
            # 新しい形式のAIレビュー情報からスコアを取得
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
