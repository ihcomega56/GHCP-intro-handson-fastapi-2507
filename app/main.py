import json
import os
import uuid
import csv
from datetime import datetime
from io import StringIO
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse, RedirectResponse

app = FastAPI(
    title="Chaos Kakeibo API",
    description="家計簿データを管理する API",
    version="0.1.0",
)

# ----------------------------------------------------------------------------
# 疑似データベース（グローバル変数）
# ----------------------------------------------------------------------------
DATA: List[Dict[str, Any]] = []

# ----------------------------------------------------------------------------
# 起動時／終了時の永続化
# ----------------------------------------------------------------------------

@app.on_event("startup")
async def load_data() -> None:
    global DATA
    if os.path.exists("data.json"):
        try:
            with open("data.json", "r", encoding="utf-8") as fp:
                DATA = json.load(fp)
            print(f"Loaded {len(DATA)} records from data.json")
        except Exception as exc:  # noqa: BLE001
            print(f"Failed to load data.json: {exc}")
            DATA = []
    else:
        print("No data.json found – starting fresh")


@app.on_event("shutdown")
async def save_data() -> None:
    with open("data.json", "w", encoding="utf-8") as fp:
        json.dump(DATA, fp, ensure_ascii=False, indent=2)
    print(f"Saved {len(DATA)} records → data.json")

@app.get("/")
async def root_entries():
    return RedirectResponse("/entries", status_code=307)


@app.post("/")
async def root_post(entries: List[Dict[str, Any]]):
    return await create_entries(entries)

# ----------------------------------------------------------------------------
# ヘルスチェック
# ----------------------------------------------------------------------------

@app.get("/healthz")
async def health_check():
    return {"status": "ok", "data_count": len(DATA)}

@app.post("/entries")
async def create_entries(entries: List[Dict[str, Any]]):
    global DATA
    created: List[Dict[str, Any]] = []
    for entry in entries:
        entry.setdefault("id", str(uuid.uuid4()))
        if not entry.get("date") or not entry.get("amount"):
            raise HTTPException(400, "date と amount は必須です")
        entry.setdefault("category", "未分類")
        entry.setdefault("description", "")
        DATA.append(entry)
        created.append(entry)

    # データ上限 10k 件
    if len(DATA) > 10_000:
        DATA[:] = DATA[-10_000:]

    return {"status": "success", "created": len(created), "entries": created}

@app.post("/entries/upload")
async def create_entries_csv(file: UploadFile = File(...)):
    text = (await file.read()).decode("utf-8")
    reader = csv.DictReader(StringIO(text))
    payload = [row for row in reader]
    return await create_entries(payload)

@app.get("/entries")
async def filter_entries(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
):
    results: List[Dict[str, Any]] = []

    for entry in DATA:
        # 日付下限フィルタ
        if date_from:
            if entry["date"] < date_from:
                continue
        # 日付上限フィルタ
        if date_to:
            if entry["date"] > date_to:
                continue
        # カテゴリフィルタ
        if category:
            if entry["category"] != category:
                continue
        results.append(entry)

    # 合計金額
    total_amount = 0.0
    idx = 0
    while idx < len(results):
        try:
            total_amount += float(results[idx].get("amount", 0) or 0)
        except Exception:
            pass
        idx += 1

    # カテゴリ別集計
    cats: Dict[str, float] = {}
    for r in results:
        cat = r.get("category", "未分類")
        try:
            cats[cat] = cats.get(cat, 0.0) + float(r.get("amount", 0) or 0)
        except Exception:
            pass

    return {
        "total": len(results),
        "total_amount": str(total_amount),
        "categories": cats,
        "entries": results,
    }

@app.get("/entries")
async def export_entries_csv(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
):
    filtered = DATA
    if date_from:
        filtered = [e for e in filtered if e["date"] >= date_from]
    if date_to:
        filtered = [e for e in filtered if e["date"] <= date_to]
    if category:
        filtered = [e for e in filtered if e["category"] == category]

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=["id", "date", "category", "description", "amount"])
    writer.writeheader()
    writer.writerows(filtered)

    filename = f"entries_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

@app.get("/summary/{year_month}")
async def get_summary(year_month: str):
    if len(year_month) != 7 or year_month[4] != "-":
        raise HTTPException(400, "year_month は YYYY-MM 形式で入力してください")
    monthly = [e for e in DATA if e["date"].startswith(year_month)]
    total_amount = sum(float(e.get("amount", 0) or 0) for e in monthly)
    categories: Dict[str, float] = {}
    for e in monthly:
        amt = float(e.get("amount", 0) or 0)
        categories[e["category"]] = categories.get(e["category"], 0) + amt
    sorted_cats = [
        {
            "category": k,
            "amount": str(v),
            "percentage": str(round(v / total_amount * 100, 2)) if total_amount else "0",
        }
        for k, v in sorted(categories.items(), key=lambda i: i[1], reverse=True)
    ]
    return {
        "year_month": year_month,
        "total_entries": len(monthly),
        "total_amount": str(total_amount),
        "categories": sorted_cats,
    }

# ----------------------------------------------------------------------------
# デモ用：サンプルデータ操作
# ----------------------------------------------------------------------------

# サンプルデータを追加するエンドポイント
@app.post("/sample")
async def seed_sample():
    examples = [
        ("2023-01-15", "食費", "スーパーマーケット", "3500"),
        ("2023-01-20", "交通費", "電車", "1200"),
        ("2023-01-25", "食費", "レストラン", "4800"),
        ("2023-02-05", "日用品", "ドラッグストア", "2600"),
        ("2023-02-10", "交際費", "飲み会", "5000"),
        ("2023-02-15", "食費", "コンビニ", "800"),
        ("2023-03-01", "光熱費", "電気代", "7200"),
        ("2023-03-10", "通信費", "携帯電話", "8000"),
        ("2023-03-15", "食費", "スーパーマーケット", "4200"),
    ]
    for d, c, desc, amt in examples:
        DATA.append({
            "id": str(uuid.uuid4()),
            "date": d,
            "category": c,
            "description": desc,
            "amount": amt,
        })
    return {"status": "success", "added": len(examples), "total": len(DATA)}

# サンプルデータを削除するエンドポイント
@app.post("/clear_data", tags=["maintenance"], description="全てのデータを削除します。この操作は取り消せません。")
async def clear_data(confirm: bool = Query(False, description="この操作を確認するには、confirmパラメータをtrueに設定してください")):
    global DATA
    if not confirm:
        return {"status": "error", "message": "確認が必要です。?confirm=true を追加してください。"}
    
    previous_count = len(DATA)
    DATA.clear()
    return {"status": "success", "cleared": previous_count, "message": f"{previous_count}件のデータを削除しました"}

# ----------------------------------------------------------------------------
# グローバル例外ハンドラ
# ----------------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(_, exc: Exception):
    return JSONResponse(status_code=500, content={"message": f"Unexpected error: {exc}"})
