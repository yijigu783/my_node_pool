import requests
import base64
import re
import json
import urllib.parse

# 这是一个调试用的 URL 列表
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

# 关键词映射表：把关键词映射到Emoji和国家代码
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
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.text
        return ""
    except Exception as e:
        print(f"    [!] 下载异常: {e}", flush=True)
        return ""

def identify_country(text):
    """根据文本内容(名字或地址)猜测国家"""
    text = text.lower()
    for code, keywords in KEYWORD_MAP.items():
        for kw in keywords:
            if kw in text:
                return code
    return 'UNKNOWN'

def rename_vmess(link):
    """处理 VMess 协议的重命名 (Base64 -> JSON -> Modify -> Base64)"""
    try:
        # 去掉 vmess:// 前缀
        b64_str = link[8:]
        # 解码
        missing_padding = len(b64_str) % 4
        if missing_padding: b64_str += '=' * (4 - missing_padding)
        json_str = base64.b64decode(b64_str).decode('utf-8', errors='ignore')
        
        # 解析 JSON
        config = json.loads(json_str)
        
        # 获取原始名字和地址
        original_ps = config.get('ps', '')
        address = config.get('add', '')
        
        # 识别国家
        country = identify_country(original_ps)
        if country == 'UNKNOWN':
            country = identify_country(address) # 如果名字里没有，就查地址
            
        flag = FLAG_MAP.get(country, '🏳️')
        
        # 生成新名字： "🇭🇰 HK 01 | 原始名" 这样的格式
        # 简单清理一下原始名字，去掉太长的杂乱字符
        clean_ps = original_ps[:20] 
        new_ps = f"{flag} {country} {clean_ps}"
        
        # 更新 JSON
        config['ps'] = new_ps
        
        # 重新编码
        new_json = json.dumps(config, ensure_ascii=False)
        new_b64 = base64.b64encode(new_json.encode('utf-8')).decode('utf-8')
        return f"vmess://{new_b64}"
    except:
        return link # 如果出错，返回原链接

def rename_url_struct(link):
    """处理 VLESS/Trojan/SS 等 URL 结构 (scheme://uuid@host:port#name)"""
    try:
        # 解析 URL
        parsed = urllib.parse.urlparse(link)
        
        # 获取原始名字 (URL Fragment)
        original_name = urllib.parse.unquote(parsed.fragment)
        host = parsed.hostname or ""
        
        # 识别
        country = identify_country(original_name)
        if country == 'UNKNOWN':
            country = identify_country(host)
            
        flag = FLAG_MAP.get(country, '🏳️')
        
        # 生成新名字
        new_name = f"{flag} {country} {original_name[:15]}"
        
        # 替换 Fragment
        new_parsed = parsed._replace(fragment=urllib.parse.quote(new_name))
        return urllib.parse.urlunparse(new_parsed)
    except:
        return link

def process_nodes(content):
    """提取并处理所有节点"""
    processed_nodes = set()
    
    # 提取所有链接
    raw_links = re.findall(r'(vmess|vless|ss|trojan|hysteria2?)://[a-zA-Z0-9\-\._~%!$&\'()*+,;=:@/?#]+', content)
    
    for link in raw_links:
        new_link = link
        if link.startswith("vmess://"):
            new_link = rename_vmess(link)
        else:
            new_link = rename_url_struct(link)
        
        processed_nodes.add(new_link)

    # 同时也尝试解码 Base64 的订阅内容
    try:
        # 简单的 Base64 清洗和解码
        clean_content = content.replace(' ', '').replace('\n', '')
        if len(clean_content) % 4 != 0:
            clean_content += '=' * (4 - len(clean_content) % 4)
        decoded = base64.b64decode(clean_content).decode('utf-8', errors='ignore')
        
        # 递归处理解码后的内容
        decoded_links = re.findall(r'(vmess|vless|ss|trojan|hysteria2?)://[a-zA-Z0-9\-\._~%!$&\'()*+,;=:@/?#]+', decoded)
        for link in decoded_links:
            if link.startswith("vmess://"):
                new_link = rename_vmess(link)
            else:
                new_link = rename_url_struct(link)
            processed_nodes.add(new_link)
    except:
        pass

    return processed_nodes

def main():
    print("=== 开始抓取与重命名 ===", flush=True)
    all_nodes = set()

    for url in URLS:
        content = get_content(url)
        if not content: continue
        
        nodes = process_nodes(content)
        if nodes:
            print(f"    > 提取并重命名了 {len(nodes)} 个节点")
            all_nodes.update(nodes)

    print(f"=== 完成 ===")
    print(f"共获取 {len(all_nodes)} 个节点")

    final_text = "\n".join(all_nodes)
    
    # 保存明文
    with open("nodes_plain.txt", "w", encoding="utf-8") as f:
        f.write(final_text)

    # 保存 Base64 订阅
    final_base64 = base64.b64encode(final_text.encode('utf-8')).decode('utf-8')
    with open("subscribe.txt", "w", encoding="utf-8") as f:
        f.write(final_base64)

if __name__ == "__main__":
    main()
