import logging
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


def get_safe(
    obj: Union[Any, Dict[str, Any]], property_name: str, default_value: Any = None
) -> Any:
    """
    オブジェクトのプロパティを安全に取得する
    辞書、CDispatchオブジェクト、その他のオブジェクトに対応

    Args:
        obj (Union[Any, Dict[str, Any]]): 対象オブジェクト
        property_name (str): 取得するプロパティ名
        default_value (Any, optional): プロパティが存在しない場合のデフォルト値. Defaults to None.

    Returns:
        Any: プロパティの値。存在しない場合はデフォルト値
    """
    try:
        # 辞書型の場合
        if isinstance(obj, dict):
            return obj.get(property_name, default_value)

        # オブジェクトの場合
        if not hasattr(obj, property_name):
            return default_value

        value = getattr(obj, property_name)
        return value if value is not None else default_value
    except Exception as e:
        logger.warning(f"プロパティ '{property_name}' の取得に失敗しました: {str(e)}")
        return default_value


def set_safe(obj: Union[Any, Dict[str, Any]], property_name: str, value: Any) -> bool:
    """
    オブジェクトのプロパティを安全に設定する
    辞書、CDispatchオブジェクト、その他のオブジェクトに対応

    Args:
        obj (Union[Any, Dict[str, Any]]): 対象オブジェクト
        property_name (str): 設定するプロパティ名
        value (Any): 設定する値

    Returns:
        bool: 設定が成功した場合はTrue
    """
    try:
        # 辞書型の場合
        if isinstance(obj, dict):
            obj[property_name] = value
            return True

        # オブジェクトの場合
        if hasattr(obj, property_name):
            setattr(obj, property_name, value)
            return True

        return False
    except Exception as e:
        logger.warning(f"プロパティ '{property_name}' の設定に失敗しました: {str(e)}")
        return False


def has_property(obj: Union[Any, Dict[str, Any]], property_name: str) -> bool:
    """
    オブジェクトが指定されたプロパティを持っているか確認する
    辞書、CDispatchオブジェクト、その他のオブジェクトに対応

    Args:
        obj (Union[Any, Dict[str, Any]]): 対象オブジェクト
        property_name (str): 確認するプロパティ名

    Returns:
        bool: プロパティが存在する場合はTrue
    """
    try:
        # 辞書型の場合
        if isinstance(obj, dict):
            return property_name in obj

        # オブジェクトの場合
        return hasattr(obj, property_name)
    except Exception as e:
        logger.warning(f"プロパティ '{property_name}' の確認に失敗しました: {str(e)}")
        return False


def get_properties(
    obj: Union[Any, Dict[str, Any]], exclude_private: bool = True
) -> List[str]:
    """
    オブジェクトのプロパティ名一覧を取得する
    辞書、CDispatchオブジェクト、その他のオブジェクトに対応

    Args:
        obj (Union[Any, Dict[str, Any]]): 対象オブジェクト
        exclude_private (bool, optional): プライベートプロパティ（_で始まる）を除外するかどうか. Defaults to True.

    Returns:
        List[str]: プロパティ名のリスト
    """
    try:
        # 辞書型の場合
        if isinstance(obj, dict):
            return [
                key
                for key in obj.keys()
                if not (exclude_private and key.startswith("_"))
            ]

        # オブジェクトの場合
        return [
            attr
            for attr in dir(obj)
            if not (exclude_private and attr.startswith("_"))
            and not callable(getattr(obj, attr))
        ]
    except Exception as e:
        logger.warning(f"プロパティ一覧の取得に失敗しました: {str(e)}")
        return []


def to_dict(
    obj: Any,
    exclude_private: bool = True,
    exclude_none: bool = True,
) -> Dict[str, Any]:
    """
    オブジェクトを辞書に変換する
    プライベートプロパティやNone値の除外が可能

    Args:
        obj (Any): 対象オブジェクト
        exclude_private (bool, optional): プライベートプロパティ（_で始まる）を除外するかどうか. Defaults to True.
        exclude_none (bool, optional): None値のプロパティを除外するかどうか. Defaults to True.

    Returns:
        Dict[str, Any]: 変換された辞書
    """
    try:
        result = {}
        for attr in dir(obj):
            # プライベートプロパティの除外
            if exclude_private and attr.startswith("_"):
                continue

            # メソッドの除外
            if callable(getattr(obj, attr)):
                continue

            value = getattr(obj, attr)

            # None値の除外
            if exclude_none and value is None:
                continue

            result[attr] = value

        return result
    except Exception as e:
        logger.warning(f"オブジェクトの辞書変換に失敗しました: {str(e)}")
        return {}


def debug_print_mail_item(mail_item: Any, title: str = "メールアイテムの詳細"):
    """
    メールアイテムオブジェクトの全プロパティとその値をデバッグ出力する

    Args:
        mail_item (Any): 検証対象のメールアイテムオブジェクト
        title (str, optional): 出力時のタイトル. Defaults to "メールアイテムの詳細".
    """
    print(f"\n==== {title} ====")

    if mail_item is None:
        print("メールアイテムがNoneです")
        return

    print(f"オブジェクトの型: {type(mail_item)}")

    # プロパティの取得と出力
    properties = get_properties(mail_item, exclude_private=False)

    print(f"\n合計プロパティ数: {len(properties)}")

    if len(properties) == 0:
        print("プロパティが見つかりません")
        return

    # 重要なOutlookメールプロパティのリスト
    important_props = [
        "Subject",
        "SenderName",
        "SenderEmailAddress",
        "To",
        "CC",
        "BCC",
        "ReceivedTime",
        "SentOn",
        "Body",
        "HTMLBody",
        "Attachments",
        "EntryID",
        "ConversationID",
        "Categories",
    ]

    # 重要なプロパティを先に出力
    print("\n--- 重要なプロパティ ---")
    for prop in important_props:
        if prop in properties:
            value = get_safe(mail_item, prop)
            print(f"{prop}: {value}")

    # その他のプロパティを出力
    print("\n--- その他のプロパティ ---")
    for prop in sorted(properties):
        if prop not in important_props:
            try:
                value = get_safe(mail_item, prop)
                # 関数かどうかを確認
                if callable(value):
                    print(f"{prop}: <メソッド>")
                else:
                    print(f"{prop}: {value}")
            except Exception as e:
                print(f"{prop}: <取得エラー: {str(e)}>")

    print("\n==== デバッグ出力終了 ====")


def debug_print_mail_methods(
    mail_item: Any, title: str = "MSGファイルから復元したメールアイテムのメソッド"
):
    """
    メールアイテムオブジェクトのメソッドとその情報をデバッグ出力する

    Args:
        mail_item (Any): 検証対象のメールアイテムオブジェクト
        title (str, optional): 出力時のタイトル. Defaults to "MSGファイルから復元したメールアイテムのメソッド".
    """
    print(f"\n==== {title} ====")

    if mail_item is None:
        print("メールアイテムがNoneです")
        return

    print(f"オブジェクトの型: {type(mail_item)}")

    # メソッドの取得
    methods = []
    try:
        for attr in dir(mail_item):
            try:
                value = getattr(mail_item, attr)
                if callable(value):
                    methods.append(attr)
            except Exception as e:
                print(f"メソッド '{attr}' の取得に失敗しました: {str(e)}")
    except Exception as e:
        print(f"メソッド一覧の取得に失敗しました: {str(e)}")

    print(f"\n合計メソッド数: {len(methods)}")

    if len(methods) == 0:
        print("メソッドが見つかりません")
        return

    # 重要な可能性のあるメソッドのリスト
    important_methods = [
        "GetAssociatedTask",
        "GetConversation",
        "GetRecurrencePattern",
        "GetInspector",
        "Move",
        "Reply",
        "ReplyAll",
        "Forward",
        "Send",
        "Save",
        "SaveAs",
        "Close",
    ]

    # 重要なメソッドを先に出力
    print("\n--- 重要なメソッド ---")
    for method in important_methods:
        if method in methods:
            print(f"{method}")
            try:
                # メソッドの詳細情報（引数なしで呼び出せるかどうかなど）を取得
                method_obj = getattr(mail_item, method)
                print(f"  型: {type(method_obj)}")
                # メソッドの文字列表現
                print(f"  詳細: {str(method_obj)}")
            except Exception as e:
                print(f"  詳細取得エラー: {str(e)}")

    # その他のメソッドを出力
    print("\n--- その他のメソッド ---")
    for method in sorted(methods):
        if method not in important_methods:
            print(f"{method}")

    print("\n==== デバッグ出力終了 ====")
