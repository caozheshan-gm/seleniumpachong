

import json
import time
import random
import os
import re

from selenium import webdriver
from selenium.webdriver.common.by import By


# ========== 工具函数区域 ==========

def extract_title(driver):
    """抓商品标题"""
    try:
        title_el = driver.find_element(
            By.XPATH,
            "(//span[@id='productTitle' and "
            " not(ancestor-or-self::*[@aria-hidden='true' "
            "   or contains(@class,'aok-hidden') "
            "   or contains(@style,'display:none')])])[1]"
        )
        return title_el.text.strip()
    except Exception as e:
        print("❌ 未能找到标题:", e)
        return ""

def extract_categories(driver):
    """
    提取商品的分类路径（breadcrumb）
    永远返回:
    {
        "full_path": [...],
        "final_category": "..."
    }
    """
    categories = []  # 默认空列表
    final_category = ""  # 默认空字符串

    try:
        # 只取第一个 breadcrumb（Amazon 页面一般只有一个）
        breadcrumb_ul = driver.find_element(
            By.XPATH,
            "(//div[@id='wayfinding-breadcrumbs_feature_div']//ul[contains(@class,'a-horizontal')])[1]"
        )

        li_elements = breadcrumb_ul.find_elements(By.XPATH, ".//li//a")

        # 提取类别文字
        categories = [li.text.strip() for li in li_elements if li.text.strip()]

        # 最后一个类别
        if categories:
            final_category = categories[-1]

    except Exception as e:
        print("  ❌ 未能获取商品分类路径 (页面可能没有 breadcrumbs):", e)

    # 无论成功或失败，都确保输出这两个字段
    return {
        "full_path": categories,
        "final_category": final_category
    }

def extract_price(driver):
    """抓商品价格（优先 corePrice_feature_div + a-offscreen）"""
    xpaths = [
        "(//*[@id='corePrice_feature_div']//span[contains(@class,'a-offscreen')])[1]",
        # 兜底：有些页面价格在 apex_desktop
        "(//*[@id='apex_desktop']//span[contains(@class,'a-offscreen')])[1]",
        # 再兜底一层：任意 a-price 下第一个 offscreen
        "(//span[contains(@class,'a-price')]//span[contains(@class,'offscreen')])[1]",
    ]
    for xp in xpaths:
        try:
            el = driver.find_element(By.XPATH, xp)
            text = (el.get_attribute("textContent") or "").strip()
            if text:
                return text
        except Exception:
            continue
    print("❌ 未能找到价格（所有候选 XPath 失败）")
    return ""

def extract_overview_specs(driver):
    """
    抓 productOverview_feature_div 里的表格参数
    位置：上面的“Brand / Chain Type / Item Pitch / Length 等”
    """
    specs = {}
    try:
        table = driver.find_element(
            By.XPATH,
            "(//div[@id='productOverview_feature_div']"
            "//table[contains(@class,'a-normal') and contains(@class,'a-spacing-micro')])[1]"
        )
        rows = table.find_elements(By.XPATH, "./tbody/tr")

        for row in rows:
            tds = row.find_elements(By.TAG_NAME, "td")
            if len(tds) >= 2:
                key = tds[0].text.strip()
                val = tds[1].text.strip()
                if key:
                    specs[key] = val

    except Exception as e:
        print("❌ 未能找到 overview 信息:", e)

    return specs

def extract_about_bullets(driver):
    """抓 About this item 的 bullet 列表"""
    bullets = []
    try:
        ul_element = driver.find_element(
            By.XPATH,
            "("
            "//div[@id='feature-bullets' or @id='feature-bullets_feature_div']"
            "//ul[contains(@class,'a-unordered-list')]"
            ")[1]"
        )

        li_elements = ul_element.find_elements(By.XPATH, ".//li")

        for li in li_elements:
            text = li.text.strip()
            if text:
                bullets.append(text)

    except Exception as e:
        print("❌ 未能找到 About this item:", e)

    return bullets

def extract_all_prod_details(driver):
    """
    从 #prodDetails 下面所有满足条件的 table 中
    抓取 key/value 形式的详细参数：
    - class 包含 a-keyvalue 和 prodDetTable
    - id 不包含 warranty / feedback
    """
    details = {}

    try:
        tables = driver.find_elements(
            By.XPATH,
            (
                "//div[@id='prodDetails']//table"
                "[contains(@class,'a-keyvalue') "
                " and contains(@class,'prodDetTable') "
                " and not(contains(@id,'warranty')) "
                " and not(contains(@id,'feedback'))]"
            )
        )

        for table in tables:
            rows = table.find_elements(By.XPATH, ".//tr")

            for row in rows:
                # 取 key（th）
                try:
                    key = row.find_element(By.TAG_NAME, "th").text.strip()
                except Exception:
                    continue

                # 特殊字段：Best Sellers Rank（里面是 <ul><li> 列表）
                if "Best Sellers Rank" in key:
                    lis = row.find_elements(By.XPATH, ".//li")
                    vals = []
                    for li in lis:
                        t = li.text.strip()
                        if not t:
                            continue
                        # 去掉 "(See Top 100 in ...)" 这样的尾巴
                        t = re.sub(r"\s*\(See Top 100.*?\)", "", t)
                        t = t.strip()
                        if t:
                            vals.append(t)
                    if vals:
                        details[key] = "; ".join(vals)
                    continue

                # 普通字段：td 里的 text
                try:
                    val = row.find_element(By.TAG_NAME, "td").text.strip()
                except Exception:
                    val = ""

                if key and val:
                    details[key] = val

    except Exception as e:
        print("❌ 在 prodDetails 中查找表格失败:", e)

    return details

# ========== 主流程区域 ==========

def parse_product(driver, asin):
    """
    解析单个 ASIN，返回一个 dict：
    {
        asin, url, title, category_path, final_category,
        price: {raw, value, currency},
        overview: {...},
        about: [...],
        details: {...}
    }
    """
    url = f"https://www.amazon.com/dp/{asin}"

    print(f"\n=== 解析 ASIN {asin} ===")
    print(f"  URL: {url}")

    driver.get(url)
    time.sleep(random.uniform(3, 6))  # 简单防一下加载问题 & 反爬

    # 标题
    title = extract_title(driver)
    print(f"  标题: {title}")

    # 分类
    cat_info = extract_categories(driver)
    full_path = cat_info.get("full_path", [])
    final_cat = cat_info.get("final_category", "")
    print("分类路径:", " > ".join(full_path) if full_path else "[无]")
    print("最终分类:", final_cat)

    # 价格
    price = extract_price(driver)
    print(f"  价格原文: {price}")

    # overview 表
    overview = extract_overview_specs(driver)
    print(f"  Overview 字段数: {len(overview)}")

    # About this item
    about = extract_about_bullets(driver)
    print(f"  About 条数: {len(about)}")

    # prodDetails 大表
    details = extract_all_prod_details(driver)
    print(f"  prodDetails 字段数: {len(details)}")

    product = {
        "asin": asin,
        "url": url,
        "title": title,

        "category_path": cat_info["full_path"],
        "final_category": cat_info["final_category"],

        "price": {
            "value": price,
        },

        "overview": overview,
        "about": about,
        "details": details
    }

    return product


# ========== 主程序：遍历 1500+ ASIN，写入 JSONL ==========

ASIN_FILE = "all_asins_expanded.json"   # 你的总 ASIN 列表
OUTPUT_JSONL = "products.jsonl"         # 输出文件（JSON Lines）


if __name__ == "__main__":
    # 1. 读取所有 ASIN
    with open(ASIN_FILE, "r", encoding="utf-8") as f:
        all_asins = json.load(f)

    print(f"共读取到 ASIN 数量: {len(all_asins)}")

    # 2. 如果 products.jsonl 已存在，读取里面已经处理过的 ASIN，避免重复
    done_asins = set()
    if os.path.exists(OUTPUT_JSONL):
        print(f"检测到已有输出文件 {OUTPUT_JSONL}，将跳过已爬取 ASIN...")
        with open(OUTPUT_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if "asin" in obj:
                        done_asins.add(obj["asin"])
                except Exception:
                    continue
        print(f"已完成 ASIN 数量: {len(done_asins)}")

    # 3. 配置 WebDriver（连接已打开的 Edge 调试端口）
    options = webdriver.EdgeOptions()
    options.debugger_address = "localhost:9222"
    driver = webdriver.Edge(options=options)

    try:
        # 4. 逐个遍历 ASIN
        total = len(all_asins)
        for idx, asin in enumerate(all_asins, start=1):
            if asin in done_asins:
                print(f"\n[{idx}/{total}] ASIN {asin} 已存在，跳过。")
                continue

            print(f"\n[{idx}/{total}] 开始处理 ASIN: {asin}")

            try:
                product = parse_product(driver, asin)
            except Exception as e:
                print(f"  ❌ 解析 ASIN {asin} 失败，错误：{e}")
                continue

            # 5. 每个 ASIN 解析完就立刻写入一行 JSONL
            try:
                with open(OUTPUT_JSONL, "a", encoding="utf-8") as f:
                    f.write(json.dumps(product, ensure_ascii=False) + "\n")
                print(f"  ✅ 已写入 {OUTPUT_JSONL}")
            except Exception as e:
                print(f"  ❌ 写入 JSONL 失败：{e}")

            # 6. 随机 sleep 一下，降低被封风险
            time.sleep(random.uniform(2, 5))

    finally:
        driver.quit()
        print("\n爬取结束，浏览器已关闭。")