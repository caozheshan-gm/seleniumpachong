import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import random
import os

# 随机延时（你也可以放到循环里每次重新生成）
sleep_time = random.uniform(5, 7)
small_time = random.uniform(4, 6)

# ===== 1. 初始化 WebDriver =====
options = webdriver.EdgeOptions()
options.debugger_address = "localhost:9222"
driver = webdriver.Edge(options=options)

driver.get("https://www.amazon.com")
print("已成功连接")

input("按回车继续（确保可以正常访问商品详情页）...")
time.sleep(small_time)

main_window = driver.current_window_handle

# ===== 2. 读取你现有的 300+ ASIN 列表 =====
with open("asins_link.json", "r", encoding="utf-8") as f:
    data = json.load(f)

base_asins = list(data)
print(f"从文件中读取到基础 ASIN 数量：{len(base_asins)}")

# ===== 2.1 初始化/恢复进度 =====
# all_asins: 全部已知 ASIN（包含新发现的）
all_asins = set(base_asins)

# 专门记录“这次新发现的”
new_asins = set()

# 已经处理过的 base ASIN（无论是否有变体都记）
processed_base_asins = set()

# 已经处理过的“家族 ASIN”（只要属于这个家族就无需再单独进页面）
processed_family_asins = set()

# 尝试从历史进度恢复（如果之前跑过一次）
if os.path.exists("all_asins_expanded.json"):
    try:
        with open("all_asins_expanded.json", "r", encoding="utf-8") as f:
            prev_all = json.load(f)
        all_asins.update(prev_all)
        print(f"从 all_asins_expanded.json 恢复已有 ASIN 数量：{len(prev_all)}")
    except Exception as e:
        print("读取 all_asins_expanded.json 失败，忽略：", e)

if os.path.exists("new_asins_found.json"):
    try:
        with open("new_asins_found.json", "r", encoding="utf-8") as f:
            prev_new = json.load(f)
        new_asins.update(prev_new)
        print(f"从 new_asins_found.json 恢复历史新发现 ASIN 数量：{len(prev_new)}")
    except Exception as e:
        print("读取 new_asins_found.json 失败，忽略：", e)

if os.path.exists("processed_base_asins.json"):
    try:
        with open("processed_base_asins.json", "r", encoding="utf-8") as f:
            prev_processed = json.load(f)
        processed_base_asins.update(prev_processed)
        print(f"从 processed_base_asins.json 恢复已处理 base ASIN 数量：{len(prev_processed)}")
    except Exception as e:
        print("读取 processed_base_asins.json 失败，忽略：", e)

# processed_family_asins 不保存也没关系，可选
if os.path.exists("processed_family_asins.json"):
    try:
        with open("processed_family_asins.json", "r", encoding="utf-8") as f:
            prev_family = json.load(f)
        processed_family_asins.update(prev_family)
        print(f"从 processed_family_asins.json 恢复已处理“家族” ASIN 数量：{len(prev_family)}")
    except Exception as e:
        print("读取 processed_family_asins.json 失败，忽略：", e)

# ===== 2.2 定义一个保存进度的函数 =====
def save_progress():
    """每处理完一个 base ASIN 就调用，避免意外中断损失太多。"""
    with open("all_asins_expanded.json", "w", encoding="utf-8") as f:
        json.dump(sorted(all_asins), f, ensure_ascii=False, indent=2)

    with open("new_asins_found.json", "w", encoding="utf-8") as f:
        json.dump(sorted(new_asins), f, ensure_ascii=False, indent=2)

    with open("processed_base_asins.json", "w", encoding="utf-8") as f:
        json.dump(sorted(processed_base_asins), f, ensure_ascii=False, indent=2)

    with open("processed_family_asins.json", "w", encoding="utf-8") as f:
        json.dump(sorted(processed_family_asins), f, ensure_ascii=False, indent=2)

    print("💾 进度已保存。当前已处理 base ASIN 数量：", len(processed_base_asins))


# ===== 3. 遍历每个基础 ASIN，进入 /dp/ASIN 页面抓变体 =====
try:
    for idx, asin in enumerate(base_asins, start=1):
        # 如果这个 base ASIN 之前已经完整处理过，直接跳过
        if asin in processed_base_asins:
            print(f"\n[{idx}/{len(base_asins)}] base ASIN {asin} 已处理过，跳过。")
            continue

        # 如果这个 asin 已经被当作“变体家族”里的成员处理过，也可以跳过
        if asin in processed_family_asins:
            print(f"\n[{idx}/{len(base_asins)}] base ASIN {asin} 已在某个规格家族中处理过，跳过。")
            # 这里也记入 processed_base_asins，避免下次重复判断
            processed_base_asins.add(asin)
            save_progress()
            continue

        url = f"https://www.amazon.com/dp/{asin}"
        print(f"\n[{idx}/{len(base_asins)}] 打开主 ASIN: {asin} -> {url}")
        driver.get(url)
        time.sleep(small_time)

        # 在详情页查找规格 li：所有有 data-asin 的规格按钮
        try:
            li_elements = driver.find_elements(
                By.XPATH,
                "//li[contains(@class,'inline-twister-swatch') and @data-asin!='']"
            )
        except Exception as e:
            print(f"⚠️ 查找规格 li 失败（{asin}）：{e}")
            # 即便失败也把这个 ASIN 记录为已处理，避免死循环
            processed_base_asins.add(asin)
            save_progress()
            continue

        page_variant_asins = set()

        for li in li_elements:
            try:
                variant_asin = li.get_attribute("data-asin")
            except Exception:
                variant_asin = None

            if variant_asin:
                page_variant_asins.add(variant_asin)

        if not page_variant_asins:
            print("  - 该页面没有找到任何规格 ASIN（可能是无变体商品）")
        else:
            print(f"  - 该页面共发现 {len(page_variant_asins)} 个规格 ASIN：{page_variant_asins}")

        # 当前这个 base_asin 自己也属于这个“家族”
        page_variant_asins.add(asin)

        # 计算这页“新发现”的 ASIN（之前没在 all_asins 里）
        newly_found_here = [v for v in page_variant_asins if v not in all_asins]

        if newly_found_here:
            print(f"  ✅ 新发现 {len(newly_found_here)} 个 ASIN: {newly_found_here}")
            for v in newly_found_here:
                new_asins.add(v)

        # 更新总集合（包括旧 + 新）
        all_asins.update(page_variant_asins)

        # 更新“家族”集合：以后遇到这些 ASIN 就知道它们已经作为某个家族处理过
        processed_family_asins.update(page_variant_asins)

        # 标记这个 base ASIN 作为“已处理”
        processed_base_asins.add(asin)

        # 每处理完一个 base ASIN 就保存一次进度
        save_progress()

        # 休息一下，避免太快（你也可以改成每轮重新生成随机值）
        time.sleep(sleep_time)

except KeyboardInterrupt:
    print("\n⛔ 检测到手动中断（Ctrl+C）。正在保存当前进度...")

finally:
    # ===== 4. 最终汇总信息并关闭浏览器 =====
    print("\n====== 扫描结束（正常结束 / 异常结束都会到这里）======")
    print(f"基础 ASIN 总数量：{len(base_asins)}")
    print(f"已处理 base ASIN 数量：{len(processed_base_asins)}")
    print(f"扩展后总 ASIN 数量：{len(all_asins)}")
    print(f"其中本次新发现 ASIN 数量：{len(new_asins)}")

    # 再保存一次保险
    save_progress()

    driver.quit()
    print("浏览器已关闭。你可以根据 processed_base_asins.json 知道已经跑到哪里了。")
