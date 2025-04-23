import asyncio
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypedDict, Union

from src.core.database import DatabaseManager
from src.core.logger import get_logger
from src.models.azure.ai_config_loader import AIConfigLoader, ModelConfig
from src.models.azure.model_manager import ModelConfigDict, ModelManager
from src.models.azure.openai_client import OpenAIClient
from src.models.azure.task_manager import TaskManager, TaskManagerConfig


class ThreadData(TypedDict):
    thread_id: str
    content: str


class AIReviewResult(TypedDict, total=False):
    success: bool
    thread_id: str
    result: Optional[Dict[str, Any]]
    error: Optional[str]


class AIReview:
    def __init__(self):
        self._logger = get_logger()
        self._lock = asyncio.Lock()
        self.clients: Dict[str, OpenAIClient] = {}
        self.manager: Optional[TaskManager] = None
        self.system_prompt: str = ""
        self.threads: List[ThreadData] = []

    def _load_system_prompt(self, path: Path) -> str:
        """システムプロンプトを読み込む"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()  # 前後の空白を削除
        except FileNotFoundError:
            self._logger.error(f"プロンプトファイルが見つかりません: {path}")
            raise FileNotFoundError(f"プロンプトファイルが見つかりません: {path}")
        except Exception as e:
            self._logger.error(f"システムプロンプトの読み込みに失敗しました: {e}")
            raise Exception(f"システムプロンプトの読み込みに失敗しました: {e}")

    def _create_threads(self) -> List[ThreadData]:
        """
        【開発中】
        items.dbのmail_itemsテーブルからスレッドデータを作成する
        - thread_idごとに会話を取得し、ThreadDataを作成
        """
        threads: List[ThreadData] = []
        try:
            # items.dbへの接続
            db_manager = DatabaseManager("data/items.db")

            # メールテーブルからthread_idのリストを取得
            thread_query = """
                SELECT DISTINCT thread_id 
                FROM mail_items 
                WHERE thread_id IS NOT NULL
                ORDER BY thread_id
            """
            thread_rows = db_manager.execute_query(thread_query)

            # 各thread_idに対して処理
            for thread_row in thread_rows:
                thread_id = thread_row["thread_id"]

                # スレッドに含まれるメールを取得（送信日時順）
                mail_query = """
                    SELECT entry_id, subject, body, sent_time
                    FROM mail_items
                    WHERE thread_id = ?
                    ORDER BY sent_time
                """
                mail_rows = db_manager.execute_query(mail_query, (thread_id,))

                if not mail_rows:
                    continue

                # スレッド内のメールをJSON化して content に格納
                thread_content = {
                    "mails": [],
                    "summary": {
                        "subject": mail_rows[0]["subject"],  # 最初のメールの件名
                        "mail_count": len(mail_rows),
                        "start_time": mail_rows[0]["sent_time"],  # 最初のメール
                        "end_time": mail_rows[-1]["sent_time"],  # 最後のメール
                    },
                }

                for mail in mail_rows:
                    # 送信者情報を取得
                    sender_query = """
                        SELECT u.email, u.name, u.company
                        FROM participants p
                        JOIN users u ON p.user_id = u.id
                        WHERE p.mail_id = ? AND p.participant_type = 'from'
                        LIMIT 1
                    """
                    sender_rows = db_manager.execute_query(
                        sender_query, (mail["entry_id"],)
                    )
                    sender = (
                        sender_rows[0]
                        if sender_rows
                        else {"email": "unknown", "name": "Unknown User"}
                    )

                    # 宛先情報を取得
                    recipients_query = """
                        SELECT u.email, u.name, u.company, p.participant_type
                        FROM participants p
                        JOIN users u ON p.user_id = u.id
                        WHERE p.mail_id = ? AND p.participant_type IN ('to', 'cc', 'bcc')
                    """
                    recipient_rows = db_manager.execute_query(
                        recipients_query, (mail["entry_id"],)
                    )

                    recipients = {"to": [], "cc": [], "bcc": []}

                    for recipient in recipient_rows:
                        recipient_type = recipient["participant_type"]
                        recipients[recipient_type].append(
                            {
                                "email": recipient["email"],
                                "name": recipient["name"],
                                "company": recipient.get("company"),
                            }
                        )

                    # メール情報をまとめる
                    mail_data = {
                        "entry_id": mail["entry_id"],
                        "subject": mail["subject"],
                        "body": mail["body"],
                        "sent_time": mail["sent_time"],
                        "sender": sender,
                        "recipients": recipients,
                    }

                    thread_content["mails"].append(mail_data)

                # ThreadDataを作成
                thread_data: ThreadData = {
                    "thread_id": thread_id,
                    "content": json.dumps(thread_content, ensure_ascii=False),
                }

                threads.append(thread_data)

            self._logger.info(f"{len(threads)}件のスレッドデータを作成しました")
            return threads

        except Exception as e:
            self._logger.error(f"スレッドデータの作成に失敗しました: {e}")
            return []

    def _initialize_clients(self) -> None:
        """AIクライアントを初期化"""
        try:
            config = AIConfigLoader()
            if not config.models:
                raise ValueError("AIモデルの設定が見つかりません")

            # 各モデルのクライアントを初期化
            for model in config.models:
                self.clients[model.model_id] = OpenAIClient(
                    system_prompt=self.system_prompt, model_id=model.model_id
                )

            # モデルマネージャを初期化
            model_configs: Dict[str, ModelConfigDict] = {
                model.model_id: {
                    "rate_limits_tpm": model.rate_limits_tpm,
                    "rate_limits_rpm": model.rate_limits_rpm,
                }
                for model in config.models
            }

            model_manager = ModelManager(model_configs)

            # タスクマネージャを初期化
            task_config: TaskManagerConfig = {
                "mode": "loadbalance",
                "timeout": 30,
                "retry_count": 2,
            }
            self.manager = TaskManager(self.clients, model_manager, task_config)

        except Exception as e:
            self._logger.error(f"AIクライアントの初期化に失敗しました: {e}")
            raise RuntimeError(f"AIクライアントの初期化に失敗しました: {e}")

    async def review(
        self, threads: Optional[List[ThreadData]] = None
    ) -> List[AIReviewResult]:
        """AIレビューを実行"""
        results: List[AIReviewResult] = []

        try:
            # スレッドデータを準備
            if threads is None:
                self.threads = self._create_threads()
            else:
                self.threads = threads

            if not self.threads:
                self._logger.warning("レビュー対象のスレッドがありません")
                return results

            # システムプロンプトを読み込み
            self.system_prompt = self._load_system_prompt(Path("config/prompt.txt"))

            # クライアントを初期化
            self._initialize_clients()

            if not self.manager:
                raise RuntimeError("タスクマネージャが初期化されていません")

            # リクエスト用プロンプトを準備
            prompts: List[str] = []
            thread_map: Dict[str, ThreadData] = {}

            for thread in self.threads:
                thread_json = json.dumps(thread)
                prompts.append(thread_json)
                # プロンプトの内容からスレッドを逆引きするためのマップ
                thread_map[thread_json] = thread

            # コールバック関数を定義
            async def callback(prompt: str, result: Optional[str]) -> None:
                """AIレビューのコールバック関数"""
                async with self._lock:
                    review_result: AIReviewResult = {"success": False}

                    try:
                        thread = thread_map.get(prompt)
                        if not thread:
                            self._logger.warning(f"未知のプロンプト: {prompt[:50]}...")
                            return

                        review_result["thread_id"] = thread["thread_id"]

                        if result is None:
                            self._logger.warning(
                                f"スレッド {thread['thread_id']} のAIレビュー結果がNoneです"
                            )
                            review_result["error"] = "AIレビュー結果がありません"
                            results.append(review_result)
                            return

                        # 結果をパース
                        result_dict = json.loads(result)
                        review_result["success"] = True
                        review_result["result"] = result_dict
                        results.append(review_result)

                        # DBへの書き込み処理
                        try:
                            # AI評価結果をDBに保存
                            db_manager = DatabaseManager("data/items.db")

                            # thread_idが既に存在するか確認
                            check_query = (
                                "SELECT thread_id FROM ai_reviews WHERE thread_id = ?"
                            )
                            existing = db_manager.execute_query(
                                check_query, (thread["thread_id"],)
                            )

                            if existing:
                                # 既存データを更新
                                update_query = """
                                    UPDATE ai_reviews 
                                    SET result = ? 
                                    WHERE thread_id = ?
                                """
                                db_manager.execute_update(
                                    update_query,
                                    (
                                        json.dumps(result_dict, ensure_ascii=False),
                                        thread["thread_id"],
                                    ),
                                )
                                self._logger.info(
                                    f"スレッド {thread['thread_id']} のAI評価結果を更新しました"
                                )
                            else:
                                # 新規データを挿入
                                insert_query = """
                                    INSERT INTO ai_reviews (thread_id, result) 
                                    VALUES (?, ?)
                                """
                                db_manager.execute_update(
                                    insert_query,
                                    (
                                        thread["thread_id"],
                                        json.dumps(result_dict, ensure_ascii=False),
                                    ),
                                )
                                self._logger.info(
                                    f"スレッド {thread['thread_id']} のAI評価結果を保存しました"
                                )

                        except Exception as db_error:
                            self._logger.error(
                                f"AI評価結果のDB保存に失敗しました: {db_error}"
                            )
                            # DB保存エラーでもAIレビュー自体は成功とみなす

                    except json.JSONDecodeError as e:
                        self._logger.error(
                            f"APIレスポンスのJSONパースに失敗しました: {e}"
                        )
                        review_result["error"] = f"レスポンスのパースに失敗: {str(e)}"
                        results.append(review_result)
                    except Exception as e:
                        self._logger.error(
                            f"コールバック処理でエラーが発生しました: {e}"
                        )
                        review_result["error"] = f"処理エラー: {str(e)}"
                        results.append(review_result)

            # タスクを実行
            await self.manager.execute_tasks(prompts, callback)

            return results

        except Exception as e:
            self._logger.error(f"AIレビュー実行中にエラーが発生しました: {e}")
            raise RuntimeError(f"AIレビュー実行中にエラーが発生しました: {e}")
