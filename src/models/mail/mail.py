# 取得したメールデータの加工

from typing import List

import ref


class Bcc:
    @staticmethod
    def extract_brackets(body_text: str) -> List[str]:
        """
        メール本文から<>で囲まれた文字列を抽出する
        """
        # 正規表現を使用して[]で囲まれた文字列を抽出
        pattern = r"<([^>]*)>"
        matches = re.findall(pattern, body_text)
        return matches

    @staticmethod
    def extract_bcc_addresses(recipient: str, address_list: List[str]) -> List[str]:
        """
        メール本文からBCCアドレスを抽出する
        """
        bcc_addresses = []
        unique_address_list = list(set(address_list))
        for address in unique_address_list:
            if address not in recipient:
                bcc_addresses.append(address)
        return bcc_addresses

    @staticmethod
    def create(body_text: str, recipient: str) -> List[str]:
        address_list = Bcc.extract_brackets(body_text)
        bcc_addresses = Bcc.extract_bcc_addresses(recipient, address_list)
        return bcc_addresses


class ToCC:
    def __init__(self):
        pass

    def get_address_by_type(self, address_type: str):
        pass

    def _remove_chars(self, text: str) -> str:
        """
        テキストから不要な文字を削除する
        """
        return text.replace("'", "").replace(" ", "").replace("　", "")

    def get_to_addresses(self):
        return self.get_address_by_type("To")

    def get_cc_addresses(self):
        return self.get_address_by_type("Cc")
