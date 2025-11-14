import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import random

sleep_time = random.uniform(5, 7)
small_time = random.uniform(4, 6)

# 初始化 WebDriver
options = webdriver.EdgeOptions()
options.debugger_address = "localhost:9222"
driver = webdriver.Edge(options=options)

driver.get("https://www.amazon.com/s?k=chainsaw+chain&page=1")
print("已成功连接")

# 等待扫码
input("按回车继续...")
time.sleep(small_time)

# 记录主窗口
main_window = driver.current_window_handle

all_asins = set()

for page in range(1, 21):
    url = f"https://www.amazon.com/s?k=chainsaw+chain&page={page}"
    print(f"\n====== 正在抓第 {page} 页：{url} ======")
    driver.get(url)
    time.sleep(small_time)

    items = driver.find_elements(
        By.XPATH,
        "//div[@role='listitem' and @data-component-type='s-search-result' and string(@data-asin)!='']"
    )

    print(f"本页找到 {len(items)} 个结果块")

    for it in items:
        asin = it.get_attribute("data-asin")
        if asin:
            all_asins.add(asin)

    time.sleep(sleep_time)

asin_list = sorted(all_asins)
print(f"\n共抓到去重后 ASIN 数量：{len(asin_list)}")

with open("asins_link.json", "w", encoding="utf-8") as f:
    json.dump(asin_list, f, ensure_ascii=False, indent=2)

print("✅ 所有结果已保存到 asins_chainsaw_chain.json")

driver.quit()



