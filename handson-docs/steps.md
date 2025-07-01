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

### ドキュメントを出力し、理解に役立てる

1. Copilot Chat で OpenAPI ドキュメントを出力してみましょう。（※FastAPIには自動生成の仕組みが備わっていますが、演習として実施します）
    - 💬 `#file:'main.app' からOpenAPIドキュメントを出力してください。`
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
    - `filter_entries` のユニットテストを書き足します。 💬 `リファクタリングのため、 #sym:test_filter_entries を改善したいです。 #sym:filter_entries に実装されている分岐を網羅できるようなテストケースにしてください。`
    - `filter_entries` の現状をビジュアライズします。 💬 `この関数の処理を Mermaid 記法でフローチャートにしてください。`
1. （※実行したい方のみ） テストを実行します。 `python -m pytest`
1. インラインチャットを立ち上げます。 `Ctrl + i / Cmd + i`
1. `filter_entries` 関数を改善します。 💬 `この関数の可読性を上げるリファクタリングを行ってください。`
1. リファクタリング後のコードに対し、Copilot Code Review を実行します。
1. 再度テスト実行やフローチャート化を実施し、リファクタリングの成功を確認します。

### ワーク：リファクタリング

Copilot と相談しながら、 `main.py` を改善しましょう。

#### 改善活動の例

- `main.py` の改善点を Copilot Chat に聞く 💬 `#file:main.py にリファクタリングの余地はありますか？` `#file:main.py に性能上の問題はありますか？`
- `main.py` 全体に対し Copilot Code Review を実施する
- 自分でコードを改修し、Copilot Code Review を実施する
- Copilot Edits で適宜方針を指示しながら修正を実施する
- Copilot Agent Mode で修正を実施する
- 単体テストを拡充する

ちなみに…  
そもそも処理の中身が分からない箇所や Copilot からの理解できないアドバイスはどんどん Copilot に質問するのがオススメです。

#### ヒント： こんな改善ができます

- エンドポイントについて、同じパス・メソッドを重複定義しているルートを解消する
- 非推奨（deprecated）の関数を現行APIへ置き換える
- I/O用の専用モジュール `data_store.py` を作成し、グローバル変数 `DATA` へのアクセスをカプセル化する
- `main.py` を分割し、Router・Service・Utils など小さい単位で切り出す
