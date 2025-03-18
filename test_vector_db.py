import asyncio
from mcp.client import Client


async def main():
    # MCPクライアントを初期化
    client = Client()

    # MCPサーバーに接続
    await client.connect("stdio")

    try:
        # 利用可能なツールを表示
        tools = await client.list_tools()
        print("利用可能なツール:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")

        print("\n" + "=" * 50 + "\n")

        # create_vector_db_from_directoryツールを呼び出す
        print("ベクトルDBの作成を開始...")
        result = await client.call_tool(
            "create_vector_db_from_directory",
            {
                "directory_path": "/Users/watamoo/dev/sample-data",
                "vector_store_name": "sample_data_store",
                "file_patterns": ["*.pdf"],
            },
        )

        print("\nベクトルDB作成結果:")
        print(f"ステータス: {result.get('status')}")
        print(f"メッセージ: {result.get('message')}")

        if result.get("stats"):
            stats = result["stats"]
            print("\n統計情報:")
            print(f"合計ファイル数: {stats.get('total_files')}")
            print(f"処理済みファイル数: {stats.get('processed_files')}")
            print(f"失敗したファイル数: {stats.get('failed_files')}")
            print(f"ベクトルストアID: {stats.get('vector_store_id')}")
            print(f"ベクトルストア名: {stats.get('vector_store_name')}")
            print(f"ファイルID: {stats.get('file_ids')}")

            # ベクトルストアIDを取得
            vector_store_id = stats.get("vector_store_id")

            if vector_store_id:
                # クエリを実行
                print("\n" + "=" * 50 + "\n")
                print("ベクトルDBに対してクエリを実行...")

                query_result = await client.call_tool(
                    "query_vector_db",
                    {"query": "AIの最新動向について教えてください", "vector_store_id": vector_store_id, "n_results": 3},
                )

                print("\nクエリ結果:")
                print(f"ステータス: {query_result.get('status')}")
                print(f"クエリ: {query_result.get('query')}")

                if query_result.get("results"):
                    print("\n検索結果:")
                    for i, result_item in enumerate(query_result["results"]):
                        print(f"\n結果 {i + 1}:")
                        print(f"ランク: {result_item.get('rank')}")
                        print(f"スコア: {result_item.get('score')}")
                        print(f"ファイルID: {result_item.get('file_id')}")

                        # テキストが長い場合は最初の200文字だけ表示
                        text = result_item.get("text", "")
                        if text:
                            print(f"テキスト: {text[:200]}..." if len(text) > 200 else f"テキスト: {text}")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

    finally:
        # クライアントを閉じる
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
