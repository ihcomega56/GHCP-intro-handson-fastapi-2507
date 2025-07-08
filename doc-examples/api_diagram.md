# 家計簿API（Chaos Kakeibo API）の構造図

このドキュメントでは、`main.py`に実装された家計簿APIの構造をMermaid記法を用いて視覚化しています。

## 1. エンドポイント構造図

この図はAPIのエンドポイント構造を表しています。各エンドポイントの関係性とHTTPメソッドを確認できます。

```mermaid
flowchart TD
    Client([クライアント]) --> Root["/"]
    Client --> Entries["/entries"]
    Client --> EntriesUpload["/entries/upload"]
    Client --> Summary["/summary/{year_month}"]
    Client --> Sample["/sample"]
    Client --> ClearData["/clear_data"]
    Client --> Health["/healthz"]
    
    Root -->|GET - リダイレクト| Entries
    Root -->|POST| CreateEntries[エントリー作成]
    
    Entries -->|GET| FilterEntries[エントリー検索/フィルタリング]
    Entries -->|GET| ExportCSV[CSVエクスポート]
    Entries -->|POST| CreateEntries
    
    EntriesUpload -->|POST| UploadCSV[CSVアップロード]
    UploadCSV --> CreateEntries
    
    Summary -->|GET| MonthSummary[月次サマリー取得]
    
    Sample -->|POST| SeedSample[サンプルデータ追加]
    ClearData -->|POST| ClearAllData[全データ削除]
    
    subgraph "データストア"
        DATA[(インメモリデータ)]
    end
    
    FilterEntries --> DATA
    ExportCSV --> DATA
    CreateEntries --> DATA
    MonthSummary --> DATA
    SeedSample --> DATA
    ClearAllData --> DATA
    Health -->|GET| DATA
```

## 2. リクエスト/レスポンスフロー図

この図は主要なエンドポイントにおけるリクエスト/レスポンスの流れを表しています。

```mermaid
sequenceDiagram
    participant Client as クライアント
    participant API as FastAPI アプリ
    participant Data as インメモリデータ
    participant Disk as data.json
    
    Note over API: 起動時
    Disk ->>+ API: データロード (存在する場合)
    API ->>- Data: メモリに格納
    
    Note over Client,Data: エントリー作成
    Client ->>+ API: POST /entries
    API ->> API: エントリーバリデーション
    API ->>+ Data: インメモリデータに追加
    Data -->>- API: 保存確認
    API -->>- Client: 作成されたエントリーを返却
    
    Note over Client,Data: エントリー取得
    Client ->>+ API: GET /entries
    API ->>+ Data: エントリーフィルタリング
    Data -->>- API: フィルタリングされたエントリー返却
    API -->>- Client: 結果返却
    
    Note over Client,Data: CSVエクスポート
    Client ->>+ API: GET /entries (CSVエクスポート)
    API ->>+ Data: エントリーフィルタリング
    Data -->>- API: フィルタリングされたエントリー返却
    API ->> API: CSV形式に変換
    API -->>- Client: CSVファイル返却
    
    Note over Client,Data: 月次サマリー
    Client ->>+ API: GET /summary/{year_month}
    API ->>+ Data: 月次データフィルタリング
    Data -->>- API: 対象月のデータ返却
    API ->> API: カテゴリ別集計
    API -->>- Client: サマリー情報返却
    
    Note over API: 終了時
    API ->>+ Data: 全データ取得
    Data -->>- API: 全データ返却
    API ->> Disk: data.jsonに保存
```

## 3. データモデル図

この図はAPIで扱われるデータモデルを表しています。

```mermaid
classDiagram
    class Entry {
        id: str
        date: str
        category: str
        description: str
        amount: str
    }
    
    class API {
        DATA: List[Dict]
        load_data()
        save_data()
        filter_entries()
        create_entries()
        export_entries_csv()
        get_summary()
        seed_sample()
        clear_data()
    }
    
    API "1" --> "*" Entry: 管理
```

## 4. アプリケーションライフサイクル図

この図はアプリケーションのライフサイクルを表しています。

```mermaid
stateDiagram-v2
    [*] --> 起動
    起動 --> データロード: on_event("startup")
    データロード --> 実行中: データロード成功/失敗
    
    実行中 --> APIリクエスト処理: リクエスト受信
    APIリクエスト処理 --> 実行中: レスポンス送信
    
    実行中 --> データ保存: on_event("shutdown")
    データ保存 --> [*]: アプリ終了
    
    state APIリクエスト処理 {
        [*] --> バリデーション
        バリデーション --> データ操作: 成功
        バリデーション --> エラーレスポンス: 失敗
        データ操作 --> レスポンス作成
        エラーレスポンス --> [*]
        レスポンス作成 --> [*]
    }
```

## 5. エントリーのフィルタリングフロー図

この図は`/entries`エンドポイントでのフィルタリング処理を表しています。

```mermaid
flowchart TD
    Start([開始]) --> LoadData[全データ取得]
    LoadData --> CheckDateFrom{date_from指定あり?}
    
    CheckDateFrom -->|Yes| FilterDateFrom[日付下限でフィルタリング]
    CheckDateFrom -->|No| CheckDateTo{date_to指定あり?}
    
    FilterDateFrom --> CheckDateTo
    
    CheckDateTo -->|Yes| FilterDateTo[日付上限でフィルタリング]
    CheckDateTo -->|No| CheckCategory{category指定あり?}
    
    FilterDateTo --> CheckCategory
    
    CheckCategory -->|Yes| FilterCategory[カテゴリでフィルタリング]
    CheckCategory -->|No| CalculateTotal[合計金額計算]
    
    FilterCategory --> CalculateTotal
    
    CalculateTotal --> CategorySummary[カテゴリ別集計]
    CategorySummary --> CreateResponse[レスポンス作成]
    CreateResponse --> End([終了])
```

## 6. データ永続化図

この図はアプリケーションのデータ永続化のフローを表しています。

```mermaid
flowchart TD
    subgraph "アプリケーション起動時"
        Start([アプリ起動]) --> CheckFile{data.jsonは存在する?}
        CheckFile -->|Yes| LoadFile[ファイルからデータ読み込み]
        CheckFile -->|No| EmptyData[空のデータで開始]
        
        LoadFile --> CheckLoadSuccess{読み込み成功?}
        CheckLoadSuccess -->|Yes| StoreData[メモリにデータ格納]
        CheckLoadSuccess -->|No| LogError[エラーログ出力] --> EmptyData
        EmptyData --> StoreData
    end
    
    subgraph "アプリケーション実行中"
        API[APIエンドポイント] <-->|読み書き| InMemoryData[(インメモリデータ)]
    end
    
    subgraph "アプリケーション終了時"
        End([アプリ終了]) --> GetAllData[全データ取得]
        GetAllData --> SerializeJSON[JSONシリアライズ]
        SerializeJSON --> SaveFile[data.jsonに保存]
        SaveFile --> AppExit([プロセス終了])
    end
    
    StoreData --> InMemoryData
```

これらの図を通じて、家計簿APIの構造と動作を様々な角度から視覚的に理解することができます。
