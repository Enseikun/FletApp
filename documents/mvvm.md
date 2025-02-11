# MVVM

## MVVMのパターンの特徴

- ViewModel は View　と Model の橋渡しを行い、View　のステートを管理する
- データバインディングを使用して View と ViewModel を疎結合に保つ
- ViewModel は Model のデータを加工して View 用のデータ形式に変換する責務を持つ

## Model と ViewModel

- 責務の範囲
    - Model: ビジネスロジックとデータ管理
    - ViewModel: UI状態管理とデータ変換
- 依存関係
    - Model: 完全に独立
    - ViewModel: Modelに依存するが、Viewには依存しない
- データの形式
    - Model: 生のデータ形式
    - ViewModel: UI表示に最適化されたデータ形式
- 状態管理
    - Model: ビジネスデータの状態
    - ViewModel: UI関連の状態（ローディング、エラー等）

## インターフェース

### 依存性逆転の原則（DIP）の実現

- 依存性逆転の原則（DIP）の実現
    - 高レベルのモジュールは低レベルのモジュールに依存しない
    - 低レベルのモジュールは高レベルのモジュールに依存する
-　インターフェースを使用することで具象クラス間の直接的な依存を避けることができる
-　テスト容易性が向上する
-　コンポーネントの交換が容易になる

### 各レイヤーでのインターフェースの役割

```python
# ViewModelのインターフェース例
class ViewModelInterface(ABC):
    @abstractmethod
    def bind_view(self, view: ViewInterface) -> None:
        """Viewとのバインディングを設定"""
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """初期化処理"""
        pass

    @abstractmethod
    def get_view_state(self) -> Any:
        """Viewの状態を取得"""
        pass

    @abstractmethod
    def update_view_state(self, state: Any) -> None:
        """Viewの状態を更新"""
        pass
```

### MVP のインターフェースとの違い

- インターフェースの目的
    - MVP: ViewとPresenterの1対1の関係を定義
    - MVVM: データバインディングとプロパティ変更通知の仕組みを定義
- 通信方法
    - MVP: インターフェースを通じた直接的なメソッド呼び出し
    - MVVM: データバインディングを通じた間接的な通信
- 責務の範囲
    - MVP: PresenterがViewの更新を直接制御
    - MVVM: ViewModelが状態を変更し、バインディングを通じて自動的にViewが更新

```py
# Presenterのインターフェース
class PresenterInterface(ABC):
    @abstractmethod
    def set_view(self, view: ViewInterface) -> None:
        pass

    @abstractmethod
    def handle_user_action(self, action: str) -> None:
        pass

# ViewModelのインターフェース
class ViewModelInterface(ABC):
    @abstractmethod
    def bind_property(self, property_name: str, binding: Callable) -> None:
        pass

    @abstractmethod
    def notify_property_changed(self, property_name: str) -> None:
        pass
```

## 実装

### ディレクトリ構成

```sh
src/
├── viewmodels/
│   ├── interfaces/
│   │   ├── view_model_interface.py
│   │   └── binding_interface.py
├── views/
│   ├── interfaces/
│   │   └── view_interface.py
└── models/
    ├── interfaces/
        └── model_interface.py
```

### Flet における検討

- ViewModel は Presenter に相当する
    - 既存の Presenter は ViewModel に移行させる
- View は Page に相当する
- Model は Model に相当する

### 検討事項

- Fletでのデータバインディングの実装方法
- 既存のPresenterのロジックをViewModelに移行する方針
- 非同期処理の扱い方
- 状態管理の方法