import os
import shutil
import time
from typing import Any, Dict, List, Optional, Tuple

from src.core.database import DatabaseManager
from src.core.logger import get_logger
from src.models.outlook.outlook_extraction_service import OutlookExtractionService
from src.util.object_util import get_safe


class HomeContentModel:
    """
    ホーム画面のコンテンツ用モデル
    tasks.dbからデータを取得・操作する
    """

    def __init__(self, db_path: str = None):
        """初期化"""
        self.logger = get_logger()

        # デフォルトのデータベースパスを設定
        if db_path is None:
            # プロジェクトのルートディレクトリを基準にデータベースパスを設定
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "data",
                "tasks.db",
            )
            self.logger.debug(
                "HomeContentModel: デフォルトデータベースパス設定", db_path=db_path
            )
        else:
            self.logger.debug(
                "HomeContentModel: 指定されたデータベースパス使用", db_path=db_path
            )

        self.db_manager = DatabaseManager(db_path)
        self.logger.info("HomeContentModel: 初期化完了", db_path=db_path)

    def create_task_directory_and_database(self, task_id: str) -> bool:
        """
        タスクフォルダとデータベースを作成する

        Args:
            task_id: タスクID

        Returns:
            bool: 作成が成功したかどうか
        """
        try:
            # タスクフォルダのパスを設定
            task_dir = os.path.join("data", "tasks", str(task_id))

            # フォルダが存在しない場合のみ作成
            if not os.path.exists(task_dir):
                os.makedirs(task_dir)
                self.logger.info(
                    f"HomeContentModel: タスクフォルダを作成しました - {task_dir}"
                )

            # items.dbのパスを設定
            items_db_path = os.path.join(task_dir, "items.db")

            # items.dbが存在しない場合のみ作成
            if not os.path.exists(items_db_path):
                # データベースを作成
                db_manager = DatabaseManager(items_db_path)

                # 外部キー制約を一時的に無効化
                db_manager.execute_update("PRAGMA foreign_keys = OFF")

                # items.sqlの内容を読み込んで実行
                sql_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                    "data",
                    "items.sql",
                )
                with open(sql_path, "r", encoding="utf-8") as f:
                    sql_script = f.read()

                # SQLスクリプトを実行
                db_manager.execute_script(sql_script)
                db_manager.commit()

                # 外部キー制約を再度有効化
                db_manager.execute_update("PRAGMA foreign_keys = ON")
                db_manager.commit()

                db_manager.disconnect()

                self.logger.info(
                    f"HomeContentModel: items.dbを作成し、スキーマを適用しました - {items_db_path}"
                )

            return True
        except Exception as e:
            self.logger.error(
                f"HomeContentModel: タスクフォルダまたはデータベースの作成に失敗しました - {e}"
            )
            return False

    def get_tasks_data(self) -> List[Tuple[int, str]]:
        """
        tasks.dbからタスクデータを取得する

        Returns:
            List[Tuple[int, str]]: (id, from_folder_name)のリスト
        """
        try:
            self.logger.debug("HomeContentModel: タスクデータ取得開始")
            # DatabaseManagerを使用してクエリを実行
            query = "SELECT id, from_folder_name FROM task_info"
            results = self.db_manager.execute_query(query)

            # 辞書のリストをタプルのリストに変換
            task_data = [
                (get_safe(item, "id"), get_safe(item, "from_folder_name"))
                for item in results
            ]
            self.logger.info(
                "HomeContentModel: タスクデータ取得成功", task_count=len(task_data)
            )
            return task_data
        except Exception as e:
            self.logger.error("HomeContentModel: タスクデータ取得エラー", error=str(e))
            return []

    def delete_task(self, task_id: str) -> bool:
        """
        指定されたIDのタスクをデータベースから削除する

        Args:
            task_id: 削除するタスクのID

        Returns:
            bool: 削除が成功したかどうか
        """
        try:
            # タスクディレクトリのパスを設定
            task_dir = os.path.join("data", "tasks", str(task_id))
            items_db_path = os.path.join(task_dir, "items.db")

            # タスクディレクトリが存在しない場合のチェック
            if not os.path.exists(task_dir):
                self.logger.warning(
                    f"HomeContentModel: 削除対象のタスクディレクトリが存在しません - {task_dir}"
                )
                # タスクディレクトリがない場合はtask_infoテーブルからのみ削除
                self.db_manager.execute_update(
                    "DELETE FROM task_info WHERE id = ?", (task_id,)
                )
                self.db_manager.commit()
                self.db_manager.disconnect()
                return True

            # PreviewContentの参照を探して、リソースを解放する
            try:
                # 循環参照を避けるためにここでインポート
                from src.views.contents.content_factory import get_current_contents

                # 現在のコンテンツを取得
                current_contents = get_current_contents()
                if current_contents:
                    # PreviewContentのインスタンスを探す
                    preview_content = None

                    for content in current_contents:
                        if (
                            hasattr(content, "__class__")
                            and content.__class__.__name__ == "PreviewContent"
                        ):
                            preview_content = content
                            break

                    # PreviewContentが見つかった場合、リソースを解放
                    if preview_content:
                        if (
                            hasattr(preview_content, "viewmodel")
                            and preview_content.viewmodel
                        ):
                            preview_content.viewmodel.close()
                            preview_content.viewmodel = None
                            self.logger.info(
                                f"HomeContentModel: 既存のPreviewContentのViewModelをクローズしました - {task_id}"
                            )

                            # 会話コンテナのリセット
                            if hasattr(preview_content, "conversation_containers"):
                                preview_content.conversation_containers.clear()

                            # メールリストとメールコンテンツビューアーのリセット
                            if hasattr(preview_content, "mail_list_component"):
                                if hasattr(
                                    preview_content.mail_list_component, "reset"
                                ):
                                    preview_content.mail_list_component.reset()

                            if hasattr(preview_content, "mail_content_viewer"):
                                if hasattr(
                                    preview_content.mail_content_viewer, "reset"
                                ):
                                    preview_content.mail_content_viewer.reset()

                            # タスクIDをクリア
                            preview_content.task_id = None

                            # 少し待機
                            time.sleep(1.0)
                        else:
                            self.logger.warning(
                                f"HomeContentModel: PreviewContentのViewModelが見つかりません - {task_id}"
                            )
                    else:
                        self.logger.warning(
                            f"HomeContentModel: PreviewContentが見つかりません - {task_id}"
                        )
                else:
                    self.logger.warning(
                        f"HomeContentModel: 現在のコンテンツが見つかりません - {task_id}"
                    )
            except Exception as preview_ex:
                self.logger.warning(
                    f"HomeContentModel: PreviewContentのリソース解放中にエラー - {str(preview_ex)}"
                )
                # エラーが発生してもタスク削除は続行する
                # フォールバックとして新しいViewModelを作成して閉じる
                try:
                    from src.viewmodels.preview_content_viewmodel import (
                        PreviewContentViewModel,
                    )

                    preview_viewmodel = PreviewContentViewModel(task_id)
                    preview_viewmodel.close()
                    self.logger.info(
                        f"HomeContentModel: フォールバックでPreviewContentViewModelをクローズしました - {task_id}"
                    )

                    # 追加の待機時間
                    time.sleep(1.0)
                except Exception as fallback_ex:
                    self.logger.warning(
                        f"HomeContentModel: フォールバックリソース解放中にエラー - {str(fallback_ex)}"
                    )

            # ファイルの使用状況を確認 - items.dbが存在する場合
            if os.path.exists(items_db_path):
                # リソース解放のための試行を行う
                self._release_resources(items_db_path)

            # 添付ファイルやその他のリソースを解放するために再度試行
            attachments_dir = os.path.join(task_dir, "attachments")
            if os.path.exists(attachments_dir):
                self._release_directory_resources(attachments_dir)

            # タスク固有のitems.dbに最終的な解放処理
            if os.path.exists(items_db_path):
                self._release_resources(items_db_path)

            # ディレクトリ削除を先に試みる
            if os.path.exists(task_dir):
                directory_deleted = self._try_remove_directory(task_dir)
                if not directory_deleted:
                    self.logger.error(
                        f"タスクディレクトリの削除に失敗しました: {task_dir}。tasks.dbからの削除も中止します。"
                    )
                    # ディレクトリ削除に失敗した場合は、tasks.dbからの削除も行わない
                    return False

            # ディレクトリ削除が成功した場合のみ、tasks.dbからの削除を実行
            self.db_manager.execute_update(
                "DELETE FROM task_info WHERE id = ?", (task_id,)
            )
            self.db_manager.commit()
            self.db_manager.disconnect()
            self.logger.info(f"タスクID: {task_id} を完全に削除しました")

            return True
        except Exception as e:
            self.logger.error(f"タスク削除エラー: {str(e)}")
            return False

    def _release_resources(self, db_path: str) -> None:
        """
        指定されたデータベースファイルのリソースを解放する

        Args:
            db_path: データベースファイルのパス
        """
        try:
            # 複数回接続解放を試みる
            for attempt in range(3):
                try:
                    # 一時的なデータベース接続を作成して閉じる（既存の接続を強制的にクローズするため）
                    tmp_db = DatabaseManager(db_path)
                    # 明示的にVACUUMを実行してリソースを解放
                    tmp_db.execute_update("VACUUM")
                    tmp_db.disconnect()
                    self.logger.info(
                        f"データベース接続解放試行 {attempt+1}/3 成功: {db_path}"
                    )
                    break
                except Exception as db_ex:
                    self.logger.warning(
                        f"データベース接続解放試行 {attempt+1}/3 失敗: {str(db_ex)}"
                    )
                    # 少し長めに待機
                    time.sleep(0.5)
        except Exception as e:
            self.logger.warning(f"リソース解放中にエラー: {str(e)}")

        # 接続解放後に追加の待機時間
        time.sleep(0.5)

    def _release_directory_resources(self, directory_path: str) -> None:
        """
        指定されたディレクトリのリソースを解放する（特に添付ファイルなど）

        Args:
            directory_path: ディレクトリのパス
        """
        try:
            # ディレクトリ内のファイルを列挙
            if os.path.exists(directory_path) and os.path.isdir(directory_path):
                for root, dirs, files in os.walk(directory_path):
                    for file in files:
                        try:
                            file_path = os.path.join(root, file)
                            # ファイルのロックを解除する試み（Windows特有の方法）
                            # このロジックはプラットフォーム依存のため、追加の処理が必要な場合がある
                            if os.path.exists(file_path):
                                with open(file_path, "a"):
                                    pass  # ファイルを開いて閉じるだけでロックが解除されることがある
                        except Exception as file_ex:
                            self.logger.warning(
                                f"ファイルのロック解除試行に失敗: {file_path}, エラー: {str(file_ex)}"
                            )
        except Exception as e:
            self.logger.warning(f"ディレクトリリソース解放中にエラー: {str(e)}")

    def _try_remove_directory(self, directory_path: str) -> bool:
        """
        ディレクトリを削除する試行を複数回行う

        Args:
            directory_path: 削除するディレクトリのパス

        Returns:
            bool: 削除が成功したかどうか
        """
        # 最大試行回数
        max_attempts = 3

        for attempt in range(max_attempts):
            try:
                # ディレクトリが存在する場合のみ削除
                if os.path.exists(directory_path):
                    shutil.rmtree(directory_path)
                    self.logger.info(f"ディレクトリ削除成功: {directory_path}")
                    return True
                else:
                    # 既に削除されている場合は成功とみなす
                    return True
            except PermissionError:
                # ファイルが使用中の場合は少し待ってから再試行
                self.logger.warning(
                    f"ディレクトリ削除試行 {attempt+1}/{max_attempts} 失敗(PermissionError): {directory_path}"
                )
                time.sleep(1.0)  # 待機時間を長めに設定
            except OSError as os_ex:
                # その他のOSエラー
                self.logger.warning(
                    f"ディレクトリ削除試行 {attempt+1}/{max_attempts} 失敗(OSError): {directory_path}, エラー: {str(os_ex)}"
                )
                time.sleep(1.0)
            except Exception as ex:
                # 予期せぬエラー
                self.logger.error(
                    f"ディレクトリ削除試行 {attempt+1}/{max_attempts} 失敗(Exception): {directory_path}, エラー: {str(ex)}"
                )
                time.sleep(1.0)

        # 全ての試行が失敗
        self.logger.error(
            f"ディレクトリ削除に失敗しました（{max_attempts}回試行）: {directory_path}"
        )
        return False

    def check_snapshot_and_extraction_plan(self, task_id: str) -> Dict[str, bool]:
        """
        スナップショットと抽出計画の存在を確認する

        Args:
            task_id: タスクID

        Returns:
            Dict[str, bool]: スナップショットと抽出計画の存在状況
        """
        result = {
            "has_snapshot": False,
            "has_extraction_plan": False,
            "extraction_in_progress": False,
            "extraction_completed": False,
        }

        try:
            # items.dbに接続
            items_db_path = os.path.join("data", "tasks", str(task_id), "items.db")
            if not os.path.exists(items_db_path):
                self.logger.warning(
                    f"HomeContentModel: items.dbが見つかりません - {items_db_path}"
                )
                return result

            items_db = DatabaseManager(items_db_path)

            # スナップショットの存在確認
            snapshot_query = "SELECT COUNT(*) as count FROM outlook_snapshot"
            snapshot_result = items_db.execute_query(snapshot_query)
            if snapshot_result and snapshot_result[0].get("count", 0) > 0:
                result["has_snapshot"] = True

            # 抽出計画の存在確認
            plan_query = "SELECT COUNT(*) as count FROM mail_tasks WHERE task_id = ?"
            plan_result = items_db.execute_query(plan_query, (task_id,))
            if plan_result and plan_result[0].get("count", 0) > 0:
                result["has_extraction_plan"] = True

            # 抽出進捗の確認
            progress_query = """
            SELECT status FROM task_progress 
            WHERE task_id = ? 
            ORDER BY last_updated_at DESC LIMIT 1
            """
            progress_result = items_db.execute_query(progress_query, (task_id,))

            if progress_result:
                status = progress_result[0].get("status")
                if status == "processing":
                    result["extraction_in_progress"] = True
                elif status == "completed":
                    result["extraction_completed"] = True

            items_db.disconnect()

            self.logger.info(
                "HomeContentModel: スナップショットと抽出計画の確認完了",
                task_id=task_id,
                result=result,
            )
            return result

        except Exception as e:
            self.logger.error(
                "HomeContentModel: スナップショットと抽出計画の確認エラー",
                task_id=task_id,
                error=str(e),
            )
            return result

    def create_outlook_snapshot(self, task_id: str) -> bool:
        """
        outlook.dbのfoldersテーブルの状態をitems.dbのoutlook_snapshotテーブルに記録する

        Args:
            task_id: タスクID

        Returns:
            bool: 記録が成功したかどうか
        """
        try:
            # OutlookExtractionServiceを使用してスナップショットを作成
            extraction_service = OutlookExtractionService(task_id)

            # 初期化に失敗した場合
            if not extraction_service.initialize():
                self.logger.error(
                    "HomeContentModel: OutlookExtractionServiceの初期化に失敗しました",
                    task_id=task_id,
                )
                return False

            try:
                # スナップショット作成を実行
                success = extraction_service.create_snapshot()
                return success
            except Exception as e:
                self.logger.error(
                    "HomeContentModel: スナップショット作成中にエラーが発生しました",
                    task_id=task_id,
                    error=str(e),
                )
                return False
            finally:
                # 必ずリソースを解放
                extraction_service.cleanup()

        except Exception as e:
            self.logger.error(
                "HomeContentModel: Outlookスナップショット作成エラー",
                task_id=task_id,
                error=str(e),
            )
            return False

    def start_mail_extraction(self, task_id: str) -> bool:
        """
        メール抽出作業を開始する

        Args:
            task_id: タスクID

        Returns:
            bool: 開始が成功したかどうか
        """
        try:
            # まずスナップショットと抽出計画の状態を確認
            status = self.check_snapshot_and_extraction_plan(task_id)

            # 既に抽出が完了している場合は成功として返す
            if status["extraction_completed"]:
                self.logger.info(
                    "HomeContentModel: メール抽出は既に完了しています",
                    task_id=task_id,
                )
                return True

            # 抽出が進行中の場合は進行中として返す（UIでProgressDialogを表示するため）
            if status["extraction_in_progress"]:
                self.logger.info(
                    "HomeContentModel: メール抽出は既に進行中です", task_id=task_id
                )
                # 現在の仕様ではUIで進捗を監視するため、進行中の状態を返す
                return True

            # OutlookExtractionServiceを使用して抽出を開始
            extraction_service = OutlookExtractionService(task_id)

            # 初期化に失敗した場合
            if not extraction_service.initialize():
                self.logger.error(
                    "HomeContentModel: OutlookExtractionServiceの初期化に失敗しました",
                    task_id=task_id,
                )
                return False

            try:
                # 抽出作業を開始（このメソッド内でスナップショットの重複チェックを行う）
                success = extraction_service.start_extraction()
                return success
            except Exception as e:
                self.logger.error(
                    "HomeContentModel: メール抽出作業中にエラーが発生しました",
                    task_id=task_id,
                    error=str(e),
                )
                return False
            finally:
                # 必ずリソースを解放
                extraction_service.cleanup()

        except Exception as e:
            self.logger.error(
                "HomeContentModel: メール抽出作業エラー", task_id=task_id, error=str(e)
            )
            return False
