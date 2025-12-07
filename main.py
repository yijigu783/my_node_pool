import requests
import base64
import re
import os

# 这里换成了真实可用的 2025 年活跃订阅源
URLS = [
    # EbraSha: 更新频率极高，含 SS/VLESS/VMess
    "https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/refs/heads/main/all_extracted_configs.txt",
    # Anaer: 经典的 Clash 订阅源
    "https://raw.githubusercontent.com/anaer/Sub/main/clash.yaml",
    # Pawdroid: 6小时更新一次
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
    # Crossxx: 包含大量免费 SSR/Hysteria
    "https://raw.githubusercontent.com/crossxx-labs/free-proxy/main/clash/vmess.yml"
]

def get_content(url):
    try:
        print(f"正在下载: {url}...")
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            return resp.text
        else:
            print(f"下载失败，状态码: {resp.status_code}")
            return ""
    except Exception as e:
        print(f"下载异常: {e}")
        return ""

def safe_base64_decode(s):
    s = s.strip().replace('\n', '').replace('\r', '').replace(' ', '')
    # 有些链接包含 URL 编码，先解码
    if '%' in s:
        try:
            from urllib.parse import unquote
            s = unquote(s)
        except: pass
        
    missing_padding = len(s) % 4
    if missing_padding:
        s += '=' * (4 - missing_padding)
    try:
        return base64.b64decode(s).decode('utf-8', errors='ignore')
    except:
        return ""

def main():
    all_nodes = set()

    for url in URLS:
        content = get_content(url)
        if not content:
            continue
        
        # 1. 尝试直接正则提取 (针对 Clash yaml 或直接文本)
        # 提取 vmess://, vless://, ss://, trojan://, hysteria2://
        nodes = re.findall(r'(vmess|vless|ss|trojan|hysteria2?)://[a-zA-Z0-9\-\._~%!$&\'()*+,;=:@/?#]+', content)
        if nodes:
            print(f"  > 直接发现 {len(nodes)} 个节点")
            for node in nodes: # findall 返回的是 tuple 或 string，需注意
                # 正则匹配整段链接
                full_links = re.findall(r'((?:vmess|vless|ss|trojan|hysteria2?)://[a-zA-Z0-9\-\._~%!$&\'()*+,;=:@/?#]+)', content)
                for link in full_links:
                    all_nodes.add(link)
        
        # 2. 尝试 Base64 解码 (针对传统订阅链接)
        decoded = safe_base64_decode(content)
        if decoded:
            for line in decoded.splitlines():
                line = line.strip()
                if re.match(r'^(vmess|vless|ss|trojan|hysteria)://', line):
                    all_nodes.add(line)

    print(f"---------------------------")
    print(f"抓取完成，去重后共 {len(all_nodes)} 个节点。")

    # 【关键修改】无论有没有节点，都创建文件，防止 Git 报错
    final_text = ""
    if all_nodes:
        final_text = "\n".join(all_nodes)
    
    # 保存明文节点
    with open("nodes_plain.txt", "w", encoding="utf-8") as f:
        f.write(final_text)

    # 保存 Base64 订阅格式
    final_base64 = base64.b64encode(final_text.encode('utf-8')).decode('utf-8')
    with open("subscribe.txt", "w", encoding="utf-8") as f:
        f.write(final_base64)
    
    print("文件已生成: subscribe.txt, nodes_plain.txt")

if __name__ == "__main__":
    main()
