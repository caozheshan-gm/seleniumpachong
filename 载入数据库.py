import json
import sqlite3
from pathlib import Path

JSONL_PATH = "products.jsonl"
DB_PATH = "products.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS amazon_products (
        asin TEXT PRIMARY KEY,
        title TEXT,
        price TEXT,
        final_category TEXT,
        brand TEXT,
        pitch TEXT,
        chain_type TEXT,
        item_length TEXT,
        overview_json TEXT,
        about_json TEXT,
        details_json TEXT,
        category_path_json TEXT
    );
    """)

    inserted = 0

    with open(JSONL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            obj = json.loads(line)

            asin  = obj.get("asin")
            title = obj.get("title")

            # price 只有一个字段
            price = (obj.get("price") or {}).get("value") or ""

            final_category = obj.get("final_category", "")

            # overview：可能不存在、可能不是字典
            raw_overview = obj.get("overview")
            overview = raw_overview if isinstance(raw_overview, dict) else {}

            
            brand = overview.get("Brand") or details.get("Manufacturer") or ""
            pitch       = overview.get("Item Pitch", "")
            chain_type  = overview.get("Chain Type", "")
            item_length = overview.get("Item Length", "")

            # about：正常是列表，异常情况归一成 []
            raw_about = obj.get("about")
            about = raw_about if isinstance(raw_about, list) else []

            # details：正常是 dict
            raw_details = obj.get("details")
            details = raw_details if isinstance(raw_details, dict) else {}

            # category_path：正常是 list
            raw_cat_path = obj.get("category_path")
            category_path = raw_cat_path if isinstance(raw_cat_path, list) else []

            overview_json      = json.dumps(overview, ensure_ascii=False)
            about_json         = json.dumps(about, ensure_ascii=False)
            details_json       = json.dumps(details, ensure_ascii=False)
            category_path_json = json.dumps(category_path, ensure_ascii=False)

            cur.execute("""
                INSERT OR REPLACE INTO amazon_products
                (asin, title, price, final_category, brand, pitch, chain_type, item_length,
                 overview_json, about_json, details_json, category_path_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                asin, title, price, final_category, brand, pitch, chain_type, item_length,
                overview_json, about_json, details_json, category_path_json
            ))
            inserted += 1

    conn.commit()
    conn.close()

    print(f"✅ 导入完成，共处理 {inserted} 条记录")
    print(f"📦 数据库文件位置: {Path(DB_PATH).resolve()}")

if __name__ == "__main__":
    main()
