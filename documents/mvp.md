# MVP Pattern

## クラス図
```mermaid
classDiagram
    class ViewInterface {
        <<interface>>
        +build()
    }
    
    class FirstView {
        -presenter
        +build()
    }
    
    class SecondView {
        -presenter
        +build()
    }
    
    class MainPresenter {
        -page
        -first_view
        -second_view
        -current_view
        +show_first_view()
        +show_second_view()
    }

    ViewInterface <|.. FirstView
    ViewInterface <|.. SecondView
    MainPresenter --> FirstView
    MainPresenter --> SecondView
```

## 処理フロー
```mermaid
sequenceDiagram
    participant User
    participant View
    participant Presenter
    participant Page

    User->>View: ボタンクリック
    View->>Presenter: イベント通知
    Presenter->>Page: ビュー切り替え要求
    Page-->>View: 新しいビューを表示
    View-->>User: UI更新
```

## MVPパターンの恩恵
```mermaid
mindmap
    root((MVPパターン))
        関心の分離
            ビューロジックの分離
            ビジネスロジックの分離
            テストの容易性
        保守性
            コードの再利用
            依存関係の明確化
            変更の影響範囲限定
        拡張性
            新規ビューの追加が容易
            インターフェースによる統一
            実装の柔軟性
```

## 説明

1. **構造的な特徴**:
   - `ViewInterface` を通じて一貫したビューの実装を強制
   - Presenter がビューとロジックの橋渡しを担当
   - 各コンポーネントの責務が明確

2. **処理フロー**:
   - ユーザーアクションはすべてPresenterを経由
   - ビューは表示のみに専念
   - Presenterがビジネスロジックを制御

3. **主な利点**:
   - テストが容易（ビューとロジックが分離）
   - コードの再利用性が高い
   - 新機能追加時の影響範囲が限定的
