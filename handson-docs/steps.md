ハンズオン手順です。 Visual Studio Code でソースコードを開いた状態で始めます。独力で進められる方は講師を待たずに次の手順へ進んで構いません。  
💬の絵文字がついている箇所はプロンプトの例です。いずれも一言一句同じである必要はありません。

## プロジェクトの分析

### プロジェクト全体を把握する

1. Copilot Chat でプロジェクトについて質問してみましょう。 `/` でコマンド、 `#` でチャット変数、 `@` でチャット参加者が使えます。
    - 💬 `これはどのようなアプリですか？`
    - 💬 `アプリケーションの実行手順を教えて下さい。`
    - 💬 `/explain #file:main.py` :bulb: ディレクトリ、ファイル、シンボルは `#` の後に名前を入力すると補完されます
    - 💬 `#sym:get_summary ではどのような処理をしていますか？`
    - 💬 `@workspace モデルクラスはどこにありますか？`
    - その他、皆さんが気になることを何でも質問してみてください。紹介していないコマンドやチャット変数も試してみましょう。

ちなみに…  
今回は1ファイルに処理がまとまってしまっている例ですが、ディレクトリやファイルが分割されている場合は次のような質問も有効です: `モデルクラスはどこにありますか？` `xxxする処理のビジネスロジックはどこにどのように実装されていますか？`

### ドキュメントを出力し、理解に役立てる（当日はスキップ。 [doc-examplesディレクトリ](../doc-examples)参照）]

1. Copilot Chat で OpenAPI ドキュメントを出力してみましょう。（※FastAPIには自動生成の仕組みが備わっていますが、演習として実施します）
    - 💬 `#file:'main.app' を分析しOpenAPIドキュメントを作成してください。`
1. 出力したドキュメントを https://editor.swagger.io/ で確認します。
1. Copilot Chat で Mermaid記法を使ったドキュメントを出力してみましょう。
    - 💬 `Mermaid記法で #file:main.py のシーケンス図を描いてください。` 
1. 出力したドキュメントを https://mermaid.live/ で確認します。

## コメントの付与

1. Copilot Chat を使って docstring を書きましょう。
    - `main.py` を開きます（ `#` とは異なるコンテキストの渡し方です）。
    - 💬 `docstringを書いてください` 
    - `Apply in Editor` ボタンでソースコードに反映し、差分を確認したら1度棄却しましょう。
1. Custom Instructions を反映させたのち docstring を書きましょう。
    - `.github/copilot-instructions.md` に次の内容をペーストし、同じプロンプトを入力しましょう。 :bulb: プロンプトは`↑``↓`キーで履歴を行き来できます

    ```markdown
    ## codingStyle

    ### 📝 コメントと言語
    - **コメントは必ず日本語**。ただし変数・関数名などコード識別子は英語スネークケース。  
    - コミットメッセージは「Add: 〜」「Fix: 〜」など命令形英語で開始。

    ### ルーティング規約
    - すべてのルートは `APIRouter` で **`/api/v{N}`** プレフィックス配下に置く。  
    - パスは複数形の名詞のみ: `/users` `/receipts/{receipt_id}`。動詞・camelCase は禁止。  
    - `tags` と `summary` を必ず指定。  
    - HTTP ステータスは POST=201, 非同期=202, DELETE=204 を明示。

    ### モデル & スキーマ
    - Pydantic: `XxxIn` / `XxxOut` / `XxxDB` 接尾辞で区別。レスポンスに SQLModel は直接使わない。  
    - `Config` は `orm_mode=True`, `extra="forbid"`。  
    - snake⇄camel 変換は `field_alias` を使う。

    ### 非同期・DB
    - Service 層は **`async def`**。DB は `AsyncSession` を `Depends` で注入。  
    - 同期 SQLAlchemy 呼び出しは `await session.run_sync(lambda s: ...)` でラップ。

    ### 例外・エラーハンドリング
    - `HTTPException` の `detail` に社内エラーコード (`E1001_USER_NOT_FOUND` 等) を含める。  
    - グローバルハンドラでその他例外を 500 → `{code, message}` 形式に変換。

    ### ドキュメンテーション & 型ヒント
    - モジュール冒頭 Docstring は一行概要＋空行。  
    - 公開関数は **Google スタイル Docstring**（Args / Returns / Raises）。  
    - 新規コードに `Any` を使わない。定数には `Final` を付与。

    ### 6. コード構造
    - import ブロック順: **標準 → サードパーティ → ローカル**。次行に **FastAPI 関連** を配置。  
    - 関数本体は **40 行以内**。超える場合はヘルパーへ抽出。  
    - 追加機能には必ず **pytest-asyncio** で単体テストを同時に作成（`tests/api/test_*.py`）。  
    - サンプルデータ・定数は別モジュールに切り出し、コードと混在させない。

## エンドポイント追加

1. コード補完を使って `/categories` エンドポイントを追加しましょう。
1. `main.py` の190行目あたり（他関数の中でなければどこでもOK）で `@app.get("/categories"`... と入力を始めます。
1. 次のように実装を完了させましょう。
```python
@app.get("/categories")
async def list_categories():
    """登録済みレシートのカテゴリー名を昇順で返す。"""
    categories = set(entry["category"] for entry in DATA if "category" in entry)
    return {"categories": sorted(categories)}
```

## リファクタリング

### `filter_entries` の可読性を上げる

1. `main.py` を開きます。
1. Copilot Chat でリファクタリングの準備をします。 :bulb: 余裕のある方は Copilot Edits を試すのもオススメです
    - `filter_entries` のユニットテストを書き足します。 💬 `#sym:filter_entries のリファクタリングのため、 #sym:test_filter_entries を改善したいです。 この関数で実装されている分岐を網羅するにはどのようなユニットテストが必要ですか？` `ユニットテストを作成してください。また、 #file:doc-examples 内に作成したケースについてまとめたドキュメントを作成してください。`
    - `filter_entries` の現状をビジュアライズします。 💬 `この関数の処理を Mermaid 記法でフローチャートにしてください。`
1. （※実行したい方のみ） テストを実行します。 `python -m pytest`
1. インラインチャットを立ち上げます。 `Ctrl + i / Cmd + i`
1. `filter_entries` 関数を改善します。 💬 `この関数の可読性を上げるリファクタリングを行ってください。`
1. リファクタリング後のコードに対し、Copilot Code Review を実行します。
1. 再度テスト実行やフローチャート化を実施し、リファクタリングの成功を確認します。

### ワーク：リファクタリング

Copilot と相談しながら、 `main.py` を改善しましょう。

#### 改善活動の例

- `main.py` の改善点を Copilot Chat に聞く 💬 `#file:main.py を分析し、モダンなFastAPIアプリケーションとして改善すべき点を3つ挙げてください。` `#file:main.py に性能上の問題はありますか？`
- `main.py` 全体に対し Copilot Code Review を実施する
- 自分でコードを改修し、Copilot Code Review を実施する
- Copilot Edits で適宜方針を指示しながら修正を実施する
- Copilot Agent Mode で修正を実施する
- 単体テストを拡充する

ちなみに…  
そもそも処理の中身が分からない箇所や Copilot からの理解できないアドバイスはどんどん Copilot に質問するのがオススメです。

#### ヒント： こんな改善ができます

- エンドポイントについて、同じパス・メソッドを重複定義しているルートを解消する
    - 💬 `@workspace main.py 内の重複しているエンドポイント定義を修正してください。`
- 非推奨（deprecated）の関数を現行APIへ置き換える
    - 💬 `@workspace #file:main.py 内で非推奨（deprecated）とマークされている関数や、非推奨と思われる古いAPIの使用パターンを特定し、最新のFastAPI推奨パターンに置き換えてください。特に以下の点に注意し、置き換え前後のコード例と変更理由を示してください。：
        1. FastAPIの古いバージョンの機能で非推奨になったもの
        2. Pythonの標準ライブラリで非推奨になった関数や方法
        3. 型ヒントやパスパラメータの古い指定方法`
- CSV出力をバックグラウンドタスク化する
    - 💬 `@workspace FastAPIのBackgroundTasksを使って、CSVエクスポート処理を非同期に実行するよう改善してください。`
- モジュールを分割しアプリケーションの構造を改善する
    - 💬 `@workspace 現在の main.py を複数のモジュールに分割するための最適な方法を提案してください。以下の観点で検討してください：
        - APIルーターの分離
        - データアクセス層の分離
        - ビジネスロジックの分離
        - モデル/スキーマの定義`
    - 💬 `@workspace app/models/ ディレクトリを作成し、家計簿エントリー用のPydanticモデルを実装してください。`
    - 💬 `@workspace app/api/ ディレクトリを作成し、エントリー用のAPIルーターを実装してください。`
- I/O用の専用モジュール `data_store.py` を作成し、グローバル変数 `DATA` へのアクセスをカプセル化する
    - 💬 `@workspace データアクセス用の依存性を作成し、グローバル変数への直接アクセスを排除してください。`
- 非同期処理を最適化する
    - 💬 `#file:main.py の関数で、I/O処理を含むものをリストアップしてください。それぞれが非同期関数として適切に実装されているかを評価してください。`
    - 💬 `@workspace filter_entries 関数のパフォーマンスを最適化してください。現在のループ処理を、より効率的な方法に置き換えてください。`
