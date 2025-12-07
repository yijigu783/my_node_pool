import requests
import base64
import re

# 1. 这里放入你搜集到的订阅源链接 (可以是 GitHub 上的 raw 链接，也可以是其他机场订阅)
# 技巧：在 GitHub 搜 "v2ray free", "clash subscribe" 找那种 raw/master/xxx.txt 的链接
URLS = [
    "https://raw.githubusercontent.com/example/repo/main/nodes.txt", 
    "https://raw.githubusercontent.com/other-user/free-nodes/master/subscribe",
    # 你可以加几十个链接
]

def get_content(url):
    try:
        resp = requests.get(url, timeout=10)
        return resp.text
    except:
        return ""

def safe_base64_decode(s):
    # 处理 Base64 填充问题，防止报错
    s = s.strip().replace('\n', '').replace('\r', '')
    missing_padding = len(s) % 4
    if missing_padding:
        s += '=' * (4 - missing_padding)
    try:
        return base64.b64decode(s).decode('utf-8')
    except:
        return ""

def main():
    all_nodes = set() # 使用集合自动去重

    print("开始抓取订阅源...")
    for url in URLS:
        content = get_content(url)
        if not content:
            continue
        
        # 尝试解码 (大多数订阅链接是 Base64 编码的)
        decoded = safe_base64_decode(content)
        
        # 如果解码失败或解码后为空，可能原始内容就是明文节点 (vmess://...)
        if not decoded: 
            decoded = content
            
        # 按行分割，提取 vmess/vless/ss/trojan 开头的节点
        for line in decoded.splitlines():
            line = line.strip()
            if line and re.match(r'^(vmess|vless|ss|trojan|hysteria)://', line):
                all_nodes.add(line)

    print(f"抓取完成，共获取 {len(all_nodes)} 个唯一节点。")

    # 结果输出
    if all_nodes:
        # 将节点合并回 Base64 编码，这是通用订阅格式
        final_text = "\n".join(all_nodes)
        final_base64 = base64.b64encode(final_text.encode('utf-8')).decode('utf-8')
        
        # 写入文件
        with open("subscribe.txt", "w", encoding="utf-8") as f:
            f.write(final_base64)
            
        # 同时也保存一份明文的，方便自己检查
        with open("nodes_plain.txt", "w", encoding="utf-8") as f:
            f.write(final_text)

if __name__ == "__main__":
    main()
