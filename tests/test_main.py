import pytest
from fastapi.testclient import TestClient
from app.main import app
import io
import csv


@pytest.fixture
def client():
    with TestClient(app) as client:
        # テスト前にデータをクリア
        client.post("/clear_data?confirm=true")
        yield client


def test_health_check(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "ok"


def test_root_redirect(client):
    """ルートパスが/docsにリダイレクトされることを確認"""
    response = client.get("/", allow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/docs"


def test_create_entries(client):
    """エントリの作成をテスト"""
    entries = [
        {"date": "2023-04-01", "category": "食費", "description": "スーパー", "amount": "1500"}
    ]
    response = client.post("/entries", json=entries)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert len(response.json()["entries"]) == 1
    assert response.json()["entries"][0]["category"] == "食費"


def test_create_entries_root_endpoint(client):
    """ルートPOSTエンドポイントを使ったエントリ作成をテスト（リダイレクト）"""
    entries = [
        {"date": "2023-04-01", "category": "食費", "description": "スーパー", "amount": "1500"}
    ]
    response = client.post("/", json=entries)
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_get_summary(client):
    """年月別サマリーのテスト - サンプルデータが必要"""
    # サンプルデータを追加
    client.post("/sample")
    
    # 2023-01の月別サマリーを取得
    response = client.get("/summary/2023-01")
    assert response.status_code == 200
    assert "year_month" in response.json()
    assert response.json()["year_month"] == "2023-01"
    assert "total_entries" in response.json()
    assert "categories" in response.json()


def test_export_csv(client):
    """CSVエクスポート機能のテスト"""
    response = client.get("/export")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "attachment" in response.headers["content-disposition"]

def test_filter_entries(client):
    """entriesフィルタリング機能のテスト"""
    # サンプルデータを追加（まだなければ）
    client.post("/sample")
    
    # カテゴリによるフィルタリングをテスト
    response = client.get("/entries?category=食費")
    assert response.status_code == 200
    assert "total" in response.json()
    assert "entries" in response.json()
    
    # すべてのエントリが「食費」カテゴリであることを確認
    entries = response.json()["entries"]
    if entries:  # 空でない場合のみチェック
        for entry in entries:
            assert entry["category"] == "食費"


def test_sample_data(client):
    """サンプルデータ投入機能のテスト"""
    response = client.post("/sample")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "success"
    assert "added" in response.json()
    assert response.json()["added"] == 9  # 9件のサンプルデータ

def test_csv_upload(client):
    """CSVアップロード機能のテスト"""
    # テスト用のCSVデータを作成
    csv_content = "date,category,description,amount\n2023-05-01,テスト,CSVアップロードテスト,2000"
    
    # ファイルをアップロード
    files = {
        "file": ("test.csv", csv_content, "text/csv")
    }
    response = client.post("/entries/upload", files=files)
    
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "success"
    assert "entries" in response.json()
    assert len(response.json()["entries"]) == 1
    assert response.json()["entries"][0]["category"] == "テスト"
    assert response.json()["entries"][0]["amount"] == "2000"