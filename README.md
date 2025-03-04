# Basic Flet App

## MVVMパターン

- プロジェクト構造
  - `src/`
    - `models/` : データモデルとビジネスロジック
    - `viewmodels/` : ViewとModelの橋渡し役
    - `views/` : UIコンポーネント
    - `services/` : 外部サービス連携
  - `tests/` : テストコード
  
## MVVMパターンの実装要件

### Model

- アプリケーションのデータと状態を管理
- ビジネスロジックを実装
- ViewModelに依存しない
- データの永続化や外部サービスとの連携

### ViewModel

- ModelとViewの橋渡し役
- ModelのデータをViewが表示できる形に変換
- ViewからのアクションをModelに伝達
- 状態管理とデータバインディング
- Fletの`Page`オブジェクトを操作

### View

- UIコンポーネントの実装
- ユーザーインタラクションの受付
- ViewModelを通じてのみModelとやり取り
- Fletのウィジェットを使用したUI構築

## 設計原則

- 各レイヤーの責務を明確に分離
- 依存関係は一方向（View → ViewModel → Model）
- テスト容易性の確保
- コードの再利用性と保守性の向上

## Fletの機能を活用したMVVM実装

### データバインディング

- Fletの`ref`を使用した双方向バインディング
- コントロールの`value`プロパティと`on_change`イベントの活用
- ViewModelでの`Observable`パターンの実装

### 状態管理

- Fletの`CustomControl`を活用したコンポーネント化
- `page.update()`による効率的な画面更新
- ViewModelでの状態管理とイベント通知

### 推奨プラクティス

- ViewModelは純粋なPythonクラスとして実装
- Viewは`CustomControl`を継承して実装
- ModelとViewModelの間でのデータ更新は非同期処理を考慮
- コンポーネント間の通信はイベントベース
- 状態更新は最小限に抑えてパフォーマンスを確保
