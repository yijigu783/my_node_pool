import requests
import base64
import re
import sys

# 这是一个调试用的 URL 列表
URLS = [
    "https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/refs/heads/main/all_extracted_configs.txt",
    "https://raw.githubusercontent.com/anaer/Sub/main/clash.yaml",
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
    "https://raw.githubusercontent.com/crossxx-labs/free-proxy/main/clash/vmess.yml"
]

def get_content(url):
    try:
        # flush=True 强制立即输出日志，防止在 Actions 里看不到
        print(f"[-] 正在下载: {url}...", flush=True)
        
        # timeout=10: 如果10秒没连上，直接报错，不再等待
        # stream=True: 防止下载几百MB的大文件把内存撑爆
        resp = requests.get(url, timeout=10, stream=True)
        
        if resp.status_code != 200:
            print(f"    [!] 下载失败，状态码: {resp.status_code}", flush=True)
            return ""

        # 限制下载大小，超过 5MB 的文件直接丢弃，防止卡死
        content = ""
        size_limit = 5 * 1024 * 1024 # 5MB
        downloaded = 0
        
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                downloaded += len(chunk)
                if downloaded > size_limit:
                    print(f"    [!] 文件过大 (>5MB)，跳过", flush=True)
                    return ""
                content += chunk.decode('utf-8', errors='ignore')
                
        print(f"    [+] 下载成功，长度: {len(content)} 字符", flush=True)
        return content

    except requests.exceptions.Timeout:
        print(f"    [!] 超时: 该链接响应太慢，已跳过", flush=True)
        return ""
    except Exception as e:
        print(f"    [!] 发生异常: {str(e)}", flush=True)
        return ""

def safe_base64_decode(s):
    s = s.strip().replace('\n', '').replace('\r', '').replace(' ', '')
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
    print("=== 任务开始 ===", flush=True)
    all_nodes = set()

    for url in URLS:
        content = get_content(url)
        if not content:
            continue
        
        # 1. 正则提取
        nodes = re.findall(r'(vmess|vless|ss|trojan|hysteria2?)://[a-zA-Z0-9\-\._~%!$&\'()*+,;=:@/?#]+', content)
        for node in nodes:
            # 重新完整匹配链接
            full_links = re.findall(r'((?:vmess|vless|ss|trojan|hysteria2?)://[a-zA-Z0-9\-\._~%!$&\'()*+,;=:@/?#]+)', content)
            for link in full_links:
                all_nodes.add(link)
        
        # 2. Base64 解码尝试
        decoded = safe_base64_decode(content)
        if decoded:
            for line in decoded.splitlines():
                line = line.strip()
                if re.match(r'^(vmess|vless|ss|trojan|hysteria)://', line):
                    all_nodes.add(line)

    print(f"=== 抓取完成 ===", flush=True)
    print(f"共去重节点: {len(all_nodes)} 个", flush=True)

    final_text = ""
    if all_nodes:
        final_text = "\n".join(all_nodes)
    
    with open("nodes_plain.txt", "w", encoding="utf-8") as f:
        f.write(final_text)

    final_base64 = base64.b64encode(final_text.encode('utf-8')).decode('utf-8')
    with open("subscribe.txt", "w", encoding="utf-8") as f:
        f.write(final_base64)

if __name__ == "__main__":
    main()
