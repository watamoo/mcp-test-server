# MCP テストサーバー

Model Context Protocol (MCP) を使用したPythonサーバーで、OpenAIのベクトルストア機能を活用したRAG（Retrieval Augmented Generation）システムを提供します。

## 機能

このMCPサーバーは以下の機能を提供します：

1. **ベクトルDBの作成**: 指定したディレクトリ内のファイル（テキスト、PDF、DOCX、マークダウン）からOpenAIのベクトルストアを構築します。
2. **ベクトルDBの検索**: 構築したベクトルDBに対してクエリを実行し、関連性の高い情報を取得します。

## 必要条件

- Python 3.11以上
- OpenAI API キー

## インストール方法

### 1. プロジェクトの初期化と仮想環境の作成

```bash
# プロジェクトを初期化
uv init mcp-test-server
cd mcp-test-server

# 仮想環境を作成して有効化
uv venv .venv
source .venv/bin/activate
```

### 2. 必要なパッケージのインストール

```bash
# 必要なパッケージをインストール
uv sync
```

### 3. 環境変数の設定

`.env`ファイルを作成し、OpenAI APIキーを設定します：

```
OPENAI_API_KEY="your-api-key"
```

## MCPサーバーのテスト（任意）

### MCP Inspectorを使用したテスト

MCP Inspectorを使用して、サーバーの動作を確認できます：

```bash
# MCP Inspectorを起動
npx @modelcontextprotocol/inspector uv run server.py
```

MCP Inspectorでの操作手順：

1. 左ペインで"Connect"を選択
2. 中央のタブで"Tools"を選択
3. "List Tools"を実行
4. 検証したいツールを選択
5. 右ペインで引数を設定して"Run Tool"を実行
6. 応答内容がResultに表示されます（unicodeエスケープされるため、適宜decodeして確認）
7. 終了後は、CLIでInspectorの実行を終了してポートを解放

## Claudeアプリへの統合

Claudeデスクトップアプリのコンフィグファイルに以下の設定を追加します：

```json
"test_calc": {
  "command": "uv",
  "args": [
      "--directory",
      "/abs/path/to/your/mcp-test-server",
      "run",
      "server.py"
  ]
}
```

`/abs/path/to/your/mcp-test-server`は、実際のプロジェクトパスに置き換えてください。

設定後、Claudeアプリを再起動すると、MCPサーバーが利用可能になります。

## 提供されるツール

このMCPサーバーは以下のツールを提供します：

### 1. create_vector_db_from_directory

指定したディレクトリ内のファイルからベクトルDBを作成します。

**引数**:
- `directory_path`: ファイルを検索するディレクトリのパス（必須）
- `vector_store_name`: ベクトルストアの名前（デフォルト: "local_knowledge"）
- `file_patterns`: 処理するファイルのパターン（デフォルト: ["*.txt", "*.pdf", "*.docx", "*.md"]）

**戻り値**:
- 処理結果の情報（ステータス、メッセージ、統計情報など）

### 2. query_vector_db

構築したベクトルDBを検索して、関連情報を取得します。

**引数**:
- `query`: 検索クエリ（必須）
- `vector_store_id`: ベクトルストアのID（必須）
- `n_results`: 返す結果の数（デフォルト: 10）

**戻り値**:
- 検索結果（ステータス、クエリ、結果リストなど）