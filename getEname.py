import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import random



sleep_time = random.uniform(5, 7)
small_time = random.uniform(4, 6)
# 初始化 WebDriver
options = webdriver.EdgeOptions()
options.debugger_address = "localhost:9222"
driver = webdriver.Edge(options=options)

driver.get("https://www.qcc.com/")
print("已成功连接")

# 等待扫码
input("请扫描二维码并登录企查查，然后按回车继续...")
time.sleep(small_time)  # 确保登录状态

# 记录主窗口
main_window = driver.current_window_handle

# 要搜索的公司列表
companies_to_search = []

result = {}
t = 1
# 循环搜索每家公司
for company_name in companies_to_search:
    print(f"正在搜索第{t}家：{company_name}")
    time.sleep(small_time)
    driver.get(f"https://www.qcc.com/search?key={company_name}")
    time.sleep(sleep_time)  # 等待页面加载
    
    # 获取第一个搜索结果并点击进入详情页（新标签页打开）
    try:
        first_result = driver.find_element(By.CSS_SELECTOR, "span.copy-title a")
        action = ActionChains(driver)
        action.move_to_element(first_result).click().perform()
        time.sleep(small_time)  # 等待详情页加载
        print(f"✅ 成功点击 '{company_name}' 的第一个搜索结果！")
    except Exception as e:
        print(f"❌ '{company_name}' 未找到搜索结果:", e)
        continue

    # 等待新窗口加载并切换
    all_windows = driver.window_handles
    new_window = [w for w in all_windows if w != main_window]
    if new_window:
        driver.switch_to.window(new_window[-1])
        print("切换新页面...")
        time.sleep(small_time)
    else:
        print(f"❌ '{company_name}' 页面未成功打开新窗口，跳过")
        continue

    # 获取公司英文名
    try:
        company_english_name = driver.find_element(By.CSS_SELECTOR, "#cominfo > div.cominfo-normal > table > tr:nth-child(8) > td:nth-child(4) > span > span:nth-child(1) > span").text
        print(f"✅ '{company_name}' 的英文名: {company_english_name}")
    except Exception:
        company_english_name = ""
        print(f"⚠️ '{company_name}' 没有找到英文名")

    
    # 获取公司介绍
    try:
        
        company_intro = driver.find_element(By.XPATH, "//td[@colspan='5']/span/span[@class='copy-value']").text.strip()
        print(f"✅ '{company_name}' 的介绍: {company_intro}")
    except Exception:
        company_intro = ""
        print(f"⚠️ '{company_name}' 没有找到介绍")

    # 存储数据
    result[company_name] = {
        "english_name": company_english_name,
        "intro": company_intro
    }

    t = t+1
    # 处理完数据后返回主窗口
    driver.switch_to.window(main_window)
    time.sleep(small_time)  # 确保切换稳定

# 保存结果
with open("company_intro7.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=4)

print("✅ 所有结果已保存")
driver.quit()
