import json
from openai import OpenAI

# 配置本地大模型API
client = OpenAI(base_url="", api_key="")

# 读取JSON文件
input_file = "childrencompany.json"
output_file = "test.json"

# 用户自定义查询关键词
query_keyword = ""  # 你可以修改此关键词

# 定义system prompt
SYSTEM_PROMPT = "你是一个商业分析助手。请根据公司业务介绍判断该公司是否与'{keyword}'相关。如果相关，请回答'是'，否则回答'否'。你必须只回答'是'或者'否'"

# 连接本地大模型并执行查询
def query_local_model(intro_text, keyword):

    response = client.chat.completions.create(
        model="local-model",  # 替换为你的本地模型名称
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.format(keyword=keyword)},
            {"role": "user", "content": f"公司业务介绍：{intro_text}"} 
        ],
        temperature=0.2,
        stream=True,
    )
    last_char = ''
    for chunk in response:
        if chunk.choices[0].delta.content: 
            text = chunk.choices[0].delta.content # 只打印实际的文本内容
            print(text, end="", flush=True)
            last_char = text[-1]
    print("\n=== 结束 ===")  # 打印换行，标识结束

    return last_char

# 处理数据
def filter_companies():
    with open(input_file, "r", encoding="utf-8") as f:
        companies = json.load(f)

    filtered_companies = {}

    total = len(companies)
    processed = len(filtered_companies) 

    print(f"🔹 共有 {total} 家公司，已处理 {processed} 家，开始执行...")

    for index, (company_name, details) in enumerate(companies.items(), start=1):
        if company_name in filtered_companies:
            print(f"✅ [{index}/{total}] {company_name} 已处理，跳过")
            continue  # 跳过已处理的公司

        print(f"🔄 [{index}/{total}] 正在处理：{company_name}...")
        intro = details.get("intro", "")
        english_name = details.get("english_name", "")

        # 调用本地大模型
        result = query_local_model(intro, query_keyword)

        if result == "是":
            filtered_companies[company_name] = {
                "english_name": english_name,
                "intro": intro
            }

        # **每处理完一家公司，就保存一次进度**
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(filtered_companies, f, indent=4, ensure_ascii=False)

        print(f"✅ [{index}/{total}] {company_name} 处理完成，当前筛选出 {len(filtered_companies)} 家相关公司")

    print(f"\n🎉 任务完成，已筛选出 {len(filtered_companies)} 家相关公司，结果已保存至 {output_file}")

# 运行程序
if __name__ == "__main__":
    filter_companies()
