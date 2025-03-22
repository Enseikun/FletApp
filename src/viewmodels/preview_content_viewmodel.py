"""
プレビューコンテンツのビューモデル
メールプレビュー画面のデータ処理を担当
"""

from typing import Any, Dict, List, Optional, Union

import flet as ft  # サンプルコードの色設定用

from src.core.logger import get_logger
from src.models.preview_content_model import PreviewContentModel


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

        # サンプルデータフラグ
        self.use_sample_data = True

        # サンプルデータ
        self.sample_mails = [
            {
                "id": 1,
                "subject": "プロジェクト進捗報告",
                "sender": "田中太郎 <tanaka@example.com>",
                "recipient": "山田花子 <yamada@example.com>",
                "date": "2023-11-15 14:30",
                "content": "山田さん\n\n先日のミーティングでお話しした件について進捗をご報告します。\n\n現在、システム設計の最終段階に入っており、来週には実装フェーズに移行できる見込みです。\n\n添付資料に詳細な進捗状況をまとめましたので、ご確認ください。\n\n何かご質問があればお知らせください。\n\n田中",
                "preview": "先日のミーティングでお話しした件について進捗をご報告します。",
                "unread": 1,
                "attachments": [
                    {"id": 101, "name": "プロジェクト進捗報告.pdf"},
                    {"id": 102, "name": "スケジュール.xlsx"},
                ],
                "risk_level": "中",
                "risk_factors": ["期限が近い", "重要な決定事項あり"],
            },
            {
                "id": 2,
                "subject": "週次会議の議事録",
                "sender": "佐藤一郎 <sato@example.com>",
                "recipient": "プロジェクトチーム <project-team@example.com>",
                "date": "2023-11-14 17:45",
                "content": "プロジェクトチームの皆様\n\n本日の週次会議の議事録を送付いたします。\n\n【議題】\n1. 前回のタスク進捗確認\n2. 新機能の要件定義\n3. テスト計画の策定\n\n【決定事項】\n・11月末までに要件定義を完了させる\n・12月第1週からテスト計画の策定を開始する\n\n詳細は添付ファイルをご確認ください。\n\n佐藤",
                "preview": "本日の週次会議の議事録を送付いたします。",
                "unread": 0,
                "attachments": [{"id": 103, "name": "週次会議議事録_20231114.docx"}],
                "risk_level": "低",
                "risk_factors": ["定期的な報告"],
            },
            {
                "id": 3,
                "subject": "新機能のフィードバック依頼",
                "sender": "鈴木健太 <suzuki@example.com>",
                "recipient": "山田花子 <yamada@example.com>",
                "date": "2023-11-13 10:15",
                "content": "山田さん\n\n先日リリースした新機能について、ユーザーからのフィードバックを集めています。\n\n特に以下の点についてご意見をいただけると助かります：\n\n1. UI/UXの使いやすさ\n2. 処理速度\n3. 追加して欲しい機能\n\n来週の金曜日までにご回答いただけますと幸いです。\n\nよろしくお願いいたします。\n\n鈴木",
                "preview": "先日リリースした新機能について、ユーザーからのフィードバックを集めています。",
                "unread": 0,
                "attachments": [],
                "risk_level": "なし",
                "risk_factors": [],
            },
            {
                "id": 4,
                "subject": "セキュリティアップデートのお知らせ",
                "sender": "システム管理者 <admin@example.com>",
                "recipient": "全社員 <all-staff@example.com>",
                "date": "2023-11-12 09:00",
                "content": "全社員の皆様\n\n重要なセキュリティアップデートのお知らせです。\n\n本日15時より、社内システムのセキュリティアップデートを実施します。\nアップデート中（約30分間）はシステムにアクセスできなくなりますので、ご注意ください。\n\n作業完了後、改めてご連絡いたします。\n\nご不便をおかけしますが、ご協力のほどよろしくお願いいたします。\n\nシステム管理者",
                "preview": "重要なセキュリティアップデートのお知らせです。",
                "unread": 1,
                "attachments": [],
                "flagged": True,
                "risk_level": "高",
                "risk_factors": ["セキュリティ関連", "全社員向け重要通知"],
            },
            {
                "id": 5,
                "subject": "クライアントミーティングの日程調整",
                "sender": "高橋美咲 <takahashi@example.com>",
                "recipient": "山田花子 <yamada@example.com>",
                "date": "2023-11-10 13:20",
                "content": "山田さん\n\nABC株式会社との次回ミーティングの日程調整をお願いします。\n\n先方から以下の候補日が挙がっています：\n・11月20日（月）14:00-16:00\n・11月22日（水）10:00-12:00\n・11月24日（金）15:00-17:00\n\nご都合の良い日をお知らせください。\n\n高橋",
                "preview": "ABC株式会社との次回ミーティングの日程調整をお願いします。",
                "unread": 0,
                "attachments": [],
                "risk_level": "中",
                "risk_factors": ["クライアント関連", "日程調整必要"],
            },
            {
                "id": 6,
                "subject": "年末パーティーのお知らせ",
                "sender": "総務部 <soumu@example.com>",
                "recipient": "全社員 <all-staff@example.com>",
                "date": "2023-11-08 11:30",
                "content": "社員の皆様\n\n恒例の年末パーティーについてお知らせいたします。\n\n【日時】2023年12月22日（金）18:30～21:00\n【場所】ホテルグランドパレス 2階「クリスタルルーム」\n【会費】5,000円（当日受付にてお支払いください）\n\n出欠確認のため、11月30日までに添付のフォームにてご回答ください。\n\n皆様のご参加をお待ちしております。\n\n総務部",
                "preview": "恒例の年末パーティーについてお知らせいたします。",
                "unread": 0,
                "attachments": [{"id": 104, "name": "年末パーティー出欠フォーム.xlsx"}],
                "risk_level": "低",
                "risk_factors": ["社内イベント", "回答期限あり"],
            },
            {
                "id": 7,
                "subject": "予算超過の件について",
                "sender": "財務部 <finance@example.com>",
                "recipient": "プロジェクトマネージャー <pm@example.com>",
                "date": "2023-11-07 09:45",
                "content": "プロジェクトマネージャー各位\n\n第3四半期のプロジェクト予算について、複数のプロジェクトで予算超過が発生しています。\n\n特に以下のプロジェクトについては、早急な対応が必要です：\n・プロジェクトA（予算超過率: 15%）\n・プロジェクトC（予算超過率: 23%）\n\n各プロジェクトマネージャーは、今週中に予算修正計画を提出してください。\n\n財務部",
                "preview": "第3四半期のプロジェクト予算について、複数のプロジェクトで予算超過が発生しています。",
                "unread": 1,
                "attachments": [{"id": 105, "name": "予算超過状況.xlsx"}],
                "flagged": True,
                "risk_level": "高",
                "risk_factors": ["予算超過", "早急な対応必要", "経営影響大"],
            },
        ]

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

        # サンプルデータを使用する場合
        if self.use_sample_data:
            self.logger.debug("PreviewContentViewModel: サンプルデータを返却")
            mails = self.sample_mails.copy()
            # 常に新しい順でソート
            return sorted(mails, key=lambda x: x["date"], reverse=True)

        # 実際のデータを取得
        self.cached_mail_list = self.model.get_all_mails()
        # 常に新しい順でソート
        sorted_mails = sorted(
            self.cached_mail_list, key=lambda x: x["date"], reverse=True
        )

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

        # サンプルデータを使用する場合
        if self.use_sample_data:
            self.logger.debug("PreviewContentViewModel: サンプルデータで検索")
            # 単純な部分文字列検索
            result = [
                mail
                for mail in self.sample_mails
                if search_term.lower() in mail["subject"].lower()
                or search_term.lower() in mail["content"].lower()
                or search_term.lower() in mail["sender"].lower()
                or search_term.lower() in mail.get("recipient", "").lower()
            ]

            # 検索結果をソート
            sorted_result = self._sort_mails(result, sort_order)

            self.logger.info(
                "PreviewContentViewModel: サンプルデータ検索完了",
                search_term=search_term,
                result_count=len(sorted_result),
            )
            return sorted_result

        # 実際のデータを検索
        result = self.model.search_mails(search_term)
        sorted_result = self._sort_mails(result, sort_order)

        self.logger.info(
            "PreviewContentViewModel: メール検索完了",
            search_term=search_term,
            result_count=len(sorted_result),
        )
        return sorted_result

    def get_mail_content(self, entry_id: str) -> Optional[Dict]:
        """メールの内容を取得"""
        self.logger.debug("PreviewContentViewModel: メール内容取得", entry_id=entry_id)

        # サンプルデータを使用する場合
        if self.use_sample_data:
            # IDを整数に変換
            mail_id = int(entry_id) if isinstance(entry_id, str) else entry_id
            # サンプルデータから該当するメールを検索
            mail = next((m for m in self.sample_mails if m["id"] == mail_id), None)
            if mail:
                self.logger.debug(
                    "PreviewContentViewModel: サンプルメール内容取得成功",
                    entry_id=entry_id,
                )
                return mail.copy()
            else:
                self.logger.warning(
                    "PreviewContentViewModel: サンプルメール内容が見つかりません",
                    entry_id=entry_id,
                )
                return None

        # 実際のデータを取得
        result = self.model.get_mail_content(entry_id)
        if result:
            self.logger.debug(
                "PreviewContentViewModel: メール内容取得成功", entry_id=entry_id
            )
        else:
            self.logger.warning(
                "PreviewContentViewModel: メール内容が見つかりません", entry_id=entry_id
            )
        return result

    def mark_as_read(self, entry_id: str) -> bool:
        """メールを既読にする"""
        self.logger.debug("PreviewContentViewModel: メール既読設定", entry_id=entry_id)

        # サンプルデータを使用する場合
        if self.use_sample_data:
            # IDを整数に変換
            mail_id = int(entry_id) if isinstance(entry_id, str) else entry_id
            # サンプルデータの該当するメールを既読に設定
            for mail in self.sample_mails:
                if mail["id"] == mail_id:
                    mail["unread"] = 0
                    self.logger.debug(
                        "PreviewContentViewModel: サンプルメール既読設定成功",
                        entry_id=entry_id,
                    )
                    return True

            self.logger.error(
                "PreviewContentViewModel: サンプルメール既読設定失敗", entry_id=entry_id
            )
            return False

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

        # サンプルデータを使用する場合
        if self.use_sample_data:
            # IDを整数に変換
            mail_id = int(entry_id) if isinstance(entry_id, str) else entry_id
            # サンプルデータの該当するメールのフラグを設定
            for mail in self.sample_mails:
                if mail["id"] == mail_id:
                    mail["flagged"] = flagged
                    self.logger.debug(
                        "PreviewContentViewModel: サンプルメールフラグ設定成功",
                        entry_id=entry_id,
                        flagged=flagged,
                    )
                    return True

            self.logger.error(
                "PreviewContentViewModel: サンプルメールフラグ設定失敗",
                entry_id=entry_id,
            )
            return False

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

        # サンプルデータを使用する場合は常に成功とする
        if self.use_sample_data:
            self.logger.debug(
                "PreviewContentViewModel: サンプル添付ファイルダウンロード成功",
                file_id=file_id,
            )
            return True

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

        # サンプルデータを使用する場合
        if self.use_sample_data:
            # フラグが立っているメールがあれば高リスク
            if any(mail.get("flagged", False) for mail in mails):
                return {
                    "label": "高",
                    "color": ft.colors.RED,
                    "score": 3,
                    "tooltip": "この会話には重要な問題が含まれています",
                }

            # 添付ファイルがあれば中リスク
            if any(mail.get("attachments") for mail in mails):
                return {
                    "label": "中",
                    "color": ft.colors.ORANGE,
                    "score": 2,
                    "tooltip": "この会話には注意が必要な項目があります",
                }

            # 未読メールがあれば低リスク
            if any(mail.get("unread", 0) for mail in mails):
                return {
                    "label": "低",
                    "color": ft.colors.GREEN,
                    "score": 1,
                    "tooltip": "この会話にはリスクの低い項目が含まれています",
                }

            # それ以外は問題なし
            return {
                "label": "なし",
                "color": ft.colors.GREY,
                "score": 0,
                "tooltip": "この会話には特に問題はありません",
            }

        # 実際のアプリではAI評価モデルを呼び出す処理を実装
        # ...

        # デフォルト値を返す
        return {
            "label": "不明",
            "color": ft.colors.GREY,
            "score": 0,
            "tooltip": "リスク評価が利用できません",
        }
