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
