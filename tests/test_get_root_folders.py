from src.models.outlook.outlook_account_model import OutlookAccountModel
from src.core.logger import get_logger


def main():
    logger = get_logger()
    try:
        # OutlookAccountModelのインスタンスを作成
        logger.info("OutlookAccountModelのインスタンスを作成します")
        model = OutlookAccountModel()

        # サービスの状態を確認
        logger.debug("Outlookサービスの状態を確認します")
        if model._service is None:
            logger.error("Outlookサービスが初期化されていません")
            return

        # アカウントオブジェクトを直接確認
        logger.debug("アカウントオブジェクトを確認します")
        account = model._service.get_account()
        if account is None:
            logger.error("アカウントオブジェクトが取得できません")
            return

        logger.debug(f"アカウントオブジェクトの型: {type(account)}")
        logger.debug(f"利用可能なプロパティ: {dir(account)}")

        # アカウント名を取得
        logger.info("アカウント名を取得します")
        account_name = model.get_account()
        logger.info(f"アカウント名を取得しました: {account_name}")

        # ルートフォルダを取得
        logger.info("ルートフォルダを取得します")
        folders = model.get_root_folders()
        logger.info("ルートフォルダを取得しました")
        for folder_id in folders:
            logger.info(f"フォルダID: {folder_id}")

    except Exception as e:
        logger.error(f"テスト実行中にエラーが発生しました: {e}")


if __name__ == "__main__":
    main()
