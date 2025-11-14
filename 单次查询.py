from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import random
import re


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
    try:
        breadcrumb_ul = driver.find_element(
            By.XPATH,
            "(//div[@id='wayfinding-breadcrumbs_feature_div']//ul[contains(@class,'a-horizontal')])[1]"
        )

        li_elements = breadcrumb_ul.find_elements(By.XPATH, ".//li//a")

        categories = [li.text.strip() for li in li_elements if li.text.strip()]

        result = {
            "full_path": categories,
            "final_category": categories[-1] if categories else ""
        }
        return result

    except Exception:
        return {"full_path": [], "final_category": ""}

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

if __name__ == "__main__":
    # === 配置 WebDriver（复用已打开的 Edge）===
    options = webdriver.EdgeOptions()
    options.debugger_address = "localhost:9222"
    driver = webdriver.Edge(options=options)

    asin = "B07MWZRBDS"  # 示例 ASIN
    url = f"https://www.amazon.com/dp/{asin}"
    driver.get(url)
    print(f"已打开商品页面: {url}")

    time.sleep(random.uniform(3, 5))  # 简单等待页面渲染

    # ---- 抓标题 ----
    title = extract_title(driver)
    print(f"✅ 商品标题: {title}")

    # ---- 抓分类路径 ----
    cat = extract_categories(driver)
    print("✅ 商品分类路径:", " > ".join(cat["full_path"]))
    print("✅ 最终分类:", cat["final_category"])

    # ---- 抓价格 ----
    price = extract_price(driver)
    print(f"✅ 商品价格: {price}")

    # ---- 抓 overview 表（上面的简要参数表）----
    overview_specs = extract_overview_specs(driver)
    print(f"✅ 概览信息 overview: {overview_specs}")

    # ---- 抓 About this item ----
    bullets = extract_about_bullets(driver)
    print("✅ 关于商品 About this item:")
    for b in bullets:
        print("-", b)

    # ---- 抓 prodDetails 里更详细的参数表 ----
    prod_details = extract_all_prod_details(driver)
    print("✅ 详细信息 prodDetails:")
    for k, v in prod_details.items():
        print(k, "=>", v)

    driver.quit()
