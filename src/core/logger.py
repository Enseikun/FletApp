import inspect
import json
import logging
import logging.config
import logging.handlers
import re
from datetime import datetime
from pathlib import Path

import pytz
import yaml


class CustomLogger(logging.Logger):
    """カスタムロガークラス"""

    def makeRecord(
        self,
        name,
        level,
        fn,
        lno,
        msg,
        args,
        exc_info,
        func=None,
        extra=None,
        sinfo=None,
    ):
        if extra is None:
            extra = {}

        # カスタムフィールドをextraに追加
        if "location" not in extra:
            extra["location"] = "Unknown"
        if "details" not in extra:
            extra["details"] = "{}"

        # 標準のmakeRecordを呼び出す
        record = super().makeRecord(
            name, level, fn, lno, msg, args, exc_info, func, extra, sinfo
        )
        return record


class Applogger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # インスタンス生成時に一度だけ初期化を実行
            cls._instance._initialize()
        return cls._instance

    def __init__(self):
        # __init__では何もしない
        pass

    def _initialize(self) -> None:
        """ロガーの初期化を行う"""
        try:
            # カスタムロガークラスを設定
            logging.setLoggerClass(CustomLogger)

            project_root = Path(__file__).parent.parent.parent.absolute()
            log_dir = project_root / "data" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)

            log_file_name = "app.log"
            log_file_path = log_dir / log_file_name

            config_path = project_root / "config" / "logging.yaml"

            if config_path.exists():
                with config_path.open("r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    config["handlers"]["time_rotating_file"]["filename"] = str(
                        log_file_path
                    )
                    logging.config.dictConfig(config)
            else:
                # 設定ファイルがない場合のフォールバック設定
                handler = logging.handlers.TimedRotatingFileHandler(
                    filename=str(log_file_path),
                    when="midnight",
                    interval=1,
                    backupCount=30,
                    encoding="utf-8",
                )
                formatter = logging.Formatter(
                    "%(asctime)s - %(levelname)s\n"
                    "%(message)s\n"
                    "Location: %(location)s\n"
                    "Details: %(details)s\n"
                    "--------------------------------\n"
                )
                # JSTに設定
                jst = pytz.timezone("Asia/Tokyo")
                formatter.converter = lambda *args: datetime.datetime.now(
                    tz=jst
                ).timetuple()

                handler.setFormatter(formatter)
                self.logger = logging.getLogger("app_logger")
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)

            self.logger = logging.getLogger("app_logger")
            self.logger.info(
                "ロガーの初期化が完了しました。",
                extra={"location": "Applogger._initialize", "details": "{}"},
            )

        except Exception as e:
            print(f"ロガーの初期化に失敗しました: {e}")
            raise

    def _clean_unicode_text(self, text) -> str:
        """
        無効なUnicode文字（サロゲートペア文字）を削除または置換する

        Args:
            text: 処理するテキスト（str型以外も受け付ける）

        Returns:
            str: 無効な文字を削除したテキスト
        """
        if not isinstance(text, str):
            return str(text)

        try:
            # サロゲートペア文字をチェック
            # 文字列をUTF-8で一度エンコードしてデコードし、エラーは置換する
            cleaned_text = text.encode("utf-8", "replace").decode("utf-8")

            # パターンD800-DFFF（サロゲート領域）の文字を削除
            # サロゲートペアになっていない不正なサロゲート文字を削除
            cleaned_text = re.sub(r"[\uD800-\uDFFF]", "", cleaned_text)

            return cleaned_text
        except Exception as e:
            # エラーが発生した場合は、可能な限りエンコード可能な部分だけを返す
            print(f"Unicode文字列のクリーニングに失敗: {str(e)}")
            return text.encode("ascii", "ignore").decode("ascii")

    def _get_caller_info(self) -> str:
        """呼び出し元の情報を取得する"""
        try:
            caller_frame = inspect.currentframe()
            frame = None
            if caller_frame:
                # 適切な呼び出し階層を取得
                frame = caller_frame.f_back.f_back
            if frame:
                return f"{frame.f_code.co_filename}:{frame.f_code.co_name}:{frame.f_lineno}"
        finally:
            # 循環参照を防ぐためにフレームを削除
            del caller_frame
            if "frame" in locals():
                del frame
        return "Unknown"

    def log(self, message: str, level: str = "INFO", **kwargs) -> None:
        """ログを記録する

        Args:
            message (str): ログメッセージ
            level (str): ログレベル (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            **kwargs: ログに含めるオプションのキーワード引数
        """
        try:
            log_level = getattr(logging, level.upper(), logging.INFO)

            caller_info = self._get_caller_info()

            # メッセージの無効なUnicode文字を処理
            message = self._clean_unicode_text(message)

            # CDispatchやその他のシリアライズできないオブジェクトを安全に処理
            safe_kwargs = {}
            for key, value in kwargs.items():
                try:
                    # 文字列値の場合はUnicodeクリーニングを適用
                    if isinstance(value, str):
                        value = self._clean_unicode_text(value)

                    # 試験的にJSON化してみる
                    json.dumps({key: value})
                    safe_kwargs[key] = value
                except (TypeError, OverflowError):
                    # JSON化できない場合は文字列化して保存
                    try:
                        # 文字列化してからUnicodeクリーニングを適用
                        value_str = self._clean_unicode_text(str(value))
                        safe_kwargs[key] = value_str
                    except Exception:
                        # それでも失敗する場合は安全な値に置き換え
                        safe_kwargs[key] = "<エンコードできない値>"

            log_details = {
                "timestamp": datetime.now().isoformat(),
                **safe_kwargs,
            }

            # detailsのJSON文字列化時にエラーが発生しないようにする
            try:
                details_json = json.dumps(log_details, ensure_ascii=False, indent=4)
            except Exception:
                # JSON化できない場合は最小限の情報だけを含める
                details_json = json.dumps(
                    {"timestamp": log_details["timestamp"]}, ensure_ascii=False
                )

            self.logger.log(
                log_level,
                message,
                extra={
                    "location": caller_info,
                    "details": details_json,
                },
            )
        except Exception as e:
            # 再帰を避けるため、標準出力のみに出力
            print(f"ログ記録に失敗しました: {e}")

    def debug(self, message: str, **kwargs) -> None:
        """デバッグレベルのログを記録する"""
        self.log(message, "DEBUG", **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """INFOレベルのログを記録する"""
        self.log(message, "INFO", **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """WARNINGレベルのログを記録する"""
        self.log(message, "WARNING", **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        """ERRORレベルのログを記録する

        標準ロガーとの互換性のために*argsを受け入れる
        """
        if args:  # 標準ロガー形式での呼び出し
            # メッセージの無効なUnicode文字を処理
            message = self._clean_unicode_text(message)

            # 標準ロガー形式の場合は、extraを明示的に追加
            self.logger.error(
                message,
                *args,
                extra={"location": self._get_caller_info(), "details": "{}"},
            )
        else:  # カスタム形式での呼び出し
            self.log(message, "ERROR", **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """CRITICALレベルのログを記録する"""
        self.log(message, "CRITICAL", **kwargs)

    def cleanup(self) -> None:
        try:
            if hasattr(self, "logger"):
                for handler in self.logger.handlers[:]:
                    handler.close()
                    self.logger.removeHandler(handler)
        except Exception as e:
            print(f"ロガーのクリーンアップに失敗しました: {e}")


def get_logger() -> Applogger:
    """ロガーのインスタンスを取得する"""
    return Applogger()
