import os
import glob
from typing import List, Dict, Any
from mcp.server.fastmcp import FastMCP
from openai import OpenAI
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

# FastMCPサーバを初期化
mcp = FastMCP("test")

# OpenAIクライアントを初期化
client = OpenAI()


def get_files_from_directory(
    directory_path: str, file_patterns: List[str] = ["*.txt", "*.pdf", "*.docx", "*.md"]
) -> List[str]:
    """
    指定したディレクトリ内のファイルを取得する関数
    """
    all_files = []
    for pattern in file_patterns:
        files = glob.glob(os.path.join(directory_path, "**", pattern), recursive=True)
        all_files.extend(files)
    return all_files


def create_file(file_path: str):
    """
    指定したローカルのパスからファイルをアップロードする関数
    """
    # ローカルファイルを開いてアップロードする
    with open(file_path, "rb") as f:
        result = client.files.create(file=f, purpose="assistants")
    print(f"ファイル作成完了: {result.id}")
    return result.id


def create_vector_store(name: str = "local_knowledge"):
    """
    ベクトルストアを作成する関数
    """
    vector_store = client.vector_stores.create(name=name)
    print(f"ベクトルストア作成完了: {vector_store.id}")
    return vector_store.id


def add_file_to_vector_store(vector_store_id: str, file_id: str):
    """
    ベクトルストアにファイルを追加する関数
    """
    result = client.vector_stores.files.create(vector_store_id=vector_store_id, file_id=file_id)
    print(f"ベクトルストアにファイルを追加: {file_id}")
    return result


@mcp.tool()
def create_vector_db_from_directory(
    directory_path: str,
    vector_store_name: str = "local_knowledge",
    file_patterns: List[str] = ["*.txt", "*.pdf", "*.docx", "*.md"],
) -> Dict[str, Any]:
    """
    指定したディレクトリ内のファイルからベクトルDBを作成する。
    すでに同じファイルセットを持つベクトルストアが存在すれば、それを再利用する。

    Args:
        directory_path (str): ファイルを検索するディレクトリのパス
        vector_store_name (str, optional): ベクトルストアの名前。デフォルトは "local_knowledge"
        file_patterns (List[str], optional): 処理するファイルのパターン。デフォルトは ["*.txt", "*.pdf", "*.docx", "*.md"]

    Returns:
        Dict[str, Any]: 処理結果の情報
    """
    # ファイルの取得
    files = get_files_from_directory(directory_path, file_patterns)

    if not files:
        return {
            "status": "error",
            "message": f"指定したディレクトリ '{directory_path}' にパターン {file_patterns} に一致するファイルが見つかりませんでした。",
        }

    # ファイル名のリストを取得
    file_names = set(os.path.basename(file) for file in files)
    print(f"file_names:{file_names}")

    # 既存のベクトルストア一覧を取得
    try:
        vector_stores = client.vector_stores.list()

        # OpenAIにアップされているファイル一覧を取得し、file_id → filename のマッピングを作成
        all_files = client.files.list()
        file_id_to_name = {f.id: f.filename for f in all_files.data}

        for vs in vector_stores.data:
            vector_store_id = vs.id

            # それぞれのベクトルストアに含まれるファイルID一覧を取得して、ファイル名に変換
            vector_store_files = client.vector_stores.files.list(vector_store_id=vector_store_id)
            existing_files = {file_id_to_name[f.id] for f in vector_store_files.data if f.id in file_id_to_name}

            print(f"ベクトルストア内のファイル名: {existing_files}")

            # 現在のファイルセットと比較（完全一致するか）
            if file_names == existing_files:
                print(f"既存のベクトルストアを再利用: {vector_store_id}")
                return {
                    "status": "success",
                    "message": f"既存のベクトルストア '{vector_store_id}' を使用しました。",
                    "vector_store_id": vector_store_id,
                }

    except Exception as e:
        print(f"ベクトルストアの取得中にエラーが発生しました: {e}")

    # 一致するベクトルストアがない場合、新規作成
    vector_store_id = create_vector_store(vector_store_name)

    # 処理結果の統計情報
    stats = {
        "total_files": len(files),
        "processed_files": 0,
        "failed_files": 0,
        "vector_store_id": vector_store_id,
        "vector_store_name": vector_store_name,
        "file_ids": [],
    }

    # 各ファイルを処理
    for file_path in files:
        try:
            # ファイルをアップロード
            file_id = create_file(file_path)

            # ベクトルストアにファイルを追加
            add_file_to_vector_store(vector_store_id, file_id)

            stats["processed_files"] += 1
            stats["file_ids"].append(file_id)

        except Exception as e:
            stats["failed_files"] += 1
            print(f"ファイル {file_path} の処理中にエラーが発生しました: {e}")

    return {
        "status": "success",
        "message": f"{stats['processed_files']}個のファイルを処理し、ベクトルDBに追加しました。",
        "stats": stats,
    }


@mcp.tool()
def query_vector_db(query: str, vector_store_id: str, n_results: int = 10) -> Dict[str, Any]:
    """
    構築した内部知識DBを検索することで、情報を抽出する。

    Args:
        query (str): 検索クエリ
        vector_store_id (str): ベクトルストアのID
        n_results (int, optional): 返す結果の数。デフォルトは10

    Returns:
        Dict[str, Any]: 検索結果
    """
    try:
        # ベクトルストアを検索して、類似度の高いテキストを抽出
        results = client.vector_stores.search(vector_store_id=vector_store_id, query=query, max_num_results=n_results)

        # 結果を整形
        formatted_results = []

        if hasattr(results, "data") and results.data:
            for i, item in enumerate(results.data):
                result = {
                    "rank": i + 1,
                    "score": item.score,
                    "text": "\n".join(c.text for c in item.content),
                    "file_name": item.filename,
                }
                formatted_results.append(result)

        return {"status": "success", "query": query, "results": formatted_results}

    except Exception as e:
        return {"status": "error", "message": f"クエリの実行中にエラーが発生しました: {e}"}


if __name__ == "__main__":
    mcp.run(transport="stdio")
