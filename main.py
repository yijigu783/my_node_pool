import requests
import base64
import re
import json
import urllib.parse
import random

# 【已更新】你指定的 8 个订阅源
URLS = [
    "https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/refs/heads/main/all_extracted_configs.txt",
    "https://raw.githubusercontent.com/anaer/Sub/main/clash.yaml",
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
    "https://raw.githubusercontent.com/free-nodes/v2rayfree/main/v2",
    "https://raw.githubusercontent.com/free-nodes/clashfree/main/clash.yml",
    "https://bulinkbulink.com/freefq/free/master/v2",
    "https://raw.githubusercontent.com/chengaopan/AutoMergePublicNodes/master/list.txt",
    "https://raw.githubusercontent.com/crossxx-labs/free-proxy/main/clash/vmess.yml"
]

# 关键词映射：自动识别国家
KEYWORD_MAP = {
    'HK': ['hk', 'hongkong', 'hong kong', '香', '港'],
    'JP': ['jp', 'japan', 'tokyo', 'osaka', '日'],
    'US': ['us', 'united states', 'america', '美', 'los angeles'],
    'SG': ['sg', 'singapore', '新', '狮城'],
    'TW': ['tw', 'taiwan', 'taipei', '台'],
    'KR': ['kr', 'korea', 'seoul', '韩'],
    'DE': ['de', 'germany', 'frankfurt', '德'],
    'GB': ['uk', 'gb', 'united kingdom', 'london', '英'],
    'RU': ['ru', 'russia', 'moscow', '俄'],
    'FR': ['fr', 'france', 'paris', '法'],
    'CA': ['ca', 'canada', '加'],
}

FLAG_MAP = {
    'HK': '🇭🇰', 'JP': '🇯🇵', 'US': '🇺🇸', 'SG': '🇸🇬', 'TW': '🇹🇼',
    'KR': '🇰🇷', 'DE': '🇩🇪', 'GB': '🇬🇧', 'RU': '🇷🇺', 'FR': '🇫🇷', 'CA': '🇨',
    'UNKNOWN': '🏳️'
}

def get_content(url):
    try:
        print(f"[-] 下载中: {url}...", flush=True)
        # bulinkbulink 这种非 GitHub 链接有时候响应慢，设置 15 秒超时
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            return resp.text
        return ""
    except Exception as e:
        print(f"    [!] 下载异常: {e}", flush=True)
        return ""

def identify_country(text):
    text = text.lower()
    for code, keywords in KEYWORD_MAP.items():
        for kw in keywords:
            if kw in text:
                return code
    return 'UNKNOWN'

def rename_vmess(link):
    try:
        if not link.startswith("vmess://"): return link
        b64_str = link[8:]
        missing_padding = len(b64_str) % 4
        if missing_padding: b64_str += '=' * (4 - missing_padding)
        json_str = base64.b64decode(b64_str).decode('utf-8', errors='ignore')
        config = json.loads(json_str)
        original_ps = config.get('ps', '')
        address = config.get('add', '')
        country = identify_country(original_ps)
        if country == 'UNKNOWN': country = identify_country(address)
        flag = FLAG_MAP.get(country, '🏳️')
        clean_ps = original_ps[:20] if original_ps else "Node"
        new_ps = f"{flag} {country} {clean_ps}"
        config['ps'] = new_ps
        new_json = json.dumps(config, ensure_ascii=False)
        new_b64 = base64.b64encode(new_json.encode('utf-8')).decode('utf-8')
        return f"vmess://{new_b64}"
    except:
        return link

def rename_url_struct(link):
    try:
        parsed = urllib.parse.urlparse(link)
        original_name = urllib.parse.unquote(parsed.fragment)
        host = parsed.hostname or ""
        country = identify_country(original_name)
        if country == 'UNKNOWN': country = identify_country(host)
        flag = FLAG_MAP.get(country, '🏳️')
        name_clean = original_name[:20] if original_name else "Node"
        new_name = f"{flag} {country} {name_clean}"
        new_parsed = parsed._replace(fragment=urllib.parse.quote(new_name))
        return urllib.parse.urlunparse(new_parsed)
    except:
        return link

def process_nodes(content):
    processed_nodes = set()
    # 1. 使用修复后的正则提取所有链接
    raw_links = re.findall(r'(?:vmess|vless|ss|trojan|hysteria2?)://[a-zA-Z0-9\-\._~%!$&\'()*+,;=:@/?#]+', content)
    
    for link in raw_links:
        if len(link) < 15: continue
        processed_nodes.add(link)

    # 2. 尝试 Base64 解码并提取
    try:
        clean_content = content.replace(' ', '').replace('\n', '')
        if len(clean_content) % 4 != 0:
            clean_content += '=' * (4 - len(clean_content) % 4)
        decoded = base64.b64decode(clean_content).decode('utf-8', errors='ignore')
        decoded_links = re.findall(r'(?:vmess|vless|ss|trojan|hysteria2?)://[a-zA-Z0-9\-\._~%!$&\'()*+,;=:@/?#]+', decoded)
        for link in decoded_links:
            if len(link) < 15: continue
            processed_nodes.add(link)
    except:
        pass

    return processed_nodes

def main():
    print("=== 增强版脚本开始运行 ===", flush=True)
    all_nodes = set()

    # 1. 抓取阶段
    for url in URLS:
        content = get_content(url)
        if not content: continue
        
        nodes = process_nodes(content)
        if nodes:
            print(f"    > 抓取到 {len(nodes)} 个原始节点")
            all_nodes.update(nodes)

    total = len(all_nodes)
    print(f"--- 抓取结束，共 {total} 个节点 ---")

    # 2. 熔断与随机阶段
    # 设定最大保留节点数，建议 3000，超过这个数手机会卡
    MAX_NODES = 3000
    node_list = list(all_nodes)
    
    if total > MAX_NODES:
        print(f"⚠️ 节点爆炸 (> {MAX_NODES})，正在执行随机抽样...", flush=True)
        random.shuffle(node_list) # 彻底打乱
        node_list = node_list[:MAX_NODES] # 只取前 3000 个
        print(f"✅ 已保留随机的 {MAX_NODES} 个节点")
    
    # 3. 重命名阶段 (只处理选中的节点，节省时间)
    print("正在进行重命名处理...", flush=True)
    final_nodes = []
    for link in node_list:
        if link.startswith("vmess://"):
            final_nodes.append(rename_vmess(link))
        else:
            final_nodes.append(rename_url_struct(link))

    # 4. 保存阶段
    final_text = "\n".join(final_nodes)
    
    with open("nodes_plain.txt", "w", encoding="utf-8") as f:
        f.write(final_text)

    final_base64 = base64.b64encode(final_text.encode('utf-8')).decode('utf-8')
    with open("subscribe.txt", "w", encoding="utf-8") as f:
        f.write(final_base64)
    
    print("=== 成功生成 subscribe.txt ===")

if __name__ == "__main__":
    main()
