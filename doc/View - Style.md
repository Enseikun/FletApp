# StyleManager

アプリケーション全体のスタイルを一元管理するクラス

異なるコンポーネントに対して同じスタイルを適用するために使用

## 基本構造

```python
class StyleManager:
    @staticmethod
    def get_default_styles() -> Dict[ComponentState, ComponentStyle]:
        # 基本スタイルを返す
        
    @staticmethod
    def get_button_styles() -> Dict[ComponentState, ComponentStyle]:
        # ボタン用スタイルを返す
        
    @staticmethod
    def get_card_styles() -> Dict[ComponentState, ComponentStyle]:
        # カード用スタイルを返す
        
    # その他のコンポーネント用スタイルメソッド...
```

## 主要メソッド

### get_default_styles()

ComponentState (NORMAL, HOVERED, PRESSED, DISABLED, ERROR, ACTIVE）に対応するスタイルを定義

### get_button_styles()

```python
class Button(BaseComponent):
    def __init__(self, text="", **kwargs):
        super().__init__(text=text, **kwargs)
        # ボタン特有のスタイルを取得
        self._styles = StyleManager.get_button_styles()
```

## 内部構造

スタイル辞書の作成

```py
   styles = {state: ComponentStyle() for state in ComponentState}
```