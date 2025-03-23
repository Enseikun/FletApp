import sys
import os

# プロジェクトのルートディレクトリをPYTHONPATHに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.outlook.outlook_service import OutlookService
from src.core.logger import get_logger


def test_get_accounts():
    """Outlookアカウントの一覧を取得するテスト"""
    logger = get_logger()
    print("\n=== Outlookアカウントのテスト ===")

    try:
        # OutlookServiceのインスタンスを作成
        outlook_service = OutlookService()

        # アカウント一覧を取得
        accounts = outlook_service.get_accounts()

        # アカウント情報を表示
        print(f"アカウント数: {len(accounts)}")

        for account in accounts:
            try:
                print("\nアカウント情報:")
                print(f"  ├─ DisplayName: {account.DisplayName}")
                print(f"  ├─ SmtpAddress: {getattr(account, 'SmtpAddress', 'N/A')}")
                print(f"  └─ UserName: {getattr(account, 'UserName', 'N/A')}")
            except Exception as e:
                print(
                    f"[エラー] アカウント情報の取得中にエラーが発生しました: {str(e)}"
                )

    except Exception as e:
        print(f"[エラー] テスト実行中にエラーが発生しました: {str(e)}")
        raise

    print("\nアカウントのテストが完了しました")


def test_get_root_folder():
    """Outlookのルートフォルダとサブフォルダを取得するテスト"""
    logger = get_logger()
    print("\n=== Outlookフォルダ構造のテスト ===")

    try:
        # OutlookServiceのインスタンスを作成
        outlook_service = OutlookService()

        # ルートフォルダを取得
        root_folders = outlook_service.get_root_folder()

        # ルートフォルダの情報を表示
        print(f"\nルートフォルダ数: {len(root_folders)}")

        for i, root_folder in enumerate(root_folders, 1):
            try:
                is_last_root = i == len(root_folders)
                root_prefix = "└─" if is_last_root else "├─"
                sub_prefix = "   " if is_last_root else "│  "

                print(f"\n{root_prefix} {root_folder.Name}")
                print(
                    f"{sub_prefix}├─ FolderPath: {getattr(root_folder, 'FolderPath', 'N/A')}"
                )
                print(f"{sub_prefix}├─ EntryID: {root_folder.EntryID}")
                print(f"{sub_prefix}└─ DefaultItemType: {root_folder.DefaultItemType}")

                # サブフォルダを取得
                sub_folders = outlook_service.get_folders(root_folder)
                if sub_folders:
                    print(f"{sub_prefix}   サブフォルダ数: {len(sub_folders)}")

                    # サブフォルダの情報を表示
                    for j, sub_folder in enumerate(sub_folders, 1):
                        try:
                            is_last_sub = j == len(sub_folders)
                            sub_folder_prefix = (
                                f"{sub_prefix}   {'└─' if is_last_sub else '├─'}"
                            )
                            deeper_prefix = (
                                f"{sub_prefix}   {'   ' if is_last_sub else '│  '}"
                            )

                            print(f"\n{sub_folder_prefix} {sub_folder.Name}")
                            print(
                                f"{deeper_prefix}├─ FolderPath: {getattr(sub_folder, 'FolderPath', 'N/A')}"
                            )
                            print(f"{deeper_prefix}├─ EntryID: {sub_folder.EntryID}")
                            print(
                                f"{deeper_prefix}└─ DefaultItemType: {sub_folder.DefaultItemType}"
                            )

                            # さらに深いサブフォルダの数を表示
                            try:
                                deeper_folders = outlook_service.get_folders(sub_folder)
                                if deeper_folders:
                                    print(
                                        f"{deeper_prefix}   下位フォルダ数: {len(deeper_folders)}"
                                    )
                            except Exception:
                                print(f"{deeper_prefix}   下位フォルダ: なし")

                        except Exception as e:
                            print(
                                f"[エラー] サブフォルダ情報の取得中にエラーが発生しました: {str(e)}"
                            )
                else:
                    print(f"{sub_prefix}   サブフォルダ: なし")

            except Exception as e:
                print(f"[エラー] フォルダ情報の取得中にエラーが発生しました: {str(e)}")

    except Exception as e:
        print(f"[エラー] テスト実行中にエラーが発生しました: {str(e)}")
        raise

    print("\nフォルダ構造のテストが完了しました")


if __name__ == "__main__":
    test_get_accounts()
    test_get_root_folder()
