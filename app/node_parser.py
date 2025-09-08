import base64
import json
import logging
from urllib.parse import urlparse, unquote, parse_qs

def robust_b64decode(s):
    """
    一个更健壮的 Base64 解码函数，可以处理常见的 padding 错误。
    """
    # 尝试直接解码
    try:
        return base64.urlsafe_b64decode(s)
    except (base64.binascii.Error, ValueError):
        # 如果失败，尝试补全 padding 再解码
        padding = '=' * (-len(s) % 4)
        return base64.urlsafe_b64decode(s + padding)
import base64
import json
import logging
from urllib.parse import urlparse, unquote, parse_qs

def robust_b64decode(s):
    """
    一个更健壮的 Base64 解码函数，可以处理常见的 padding 错误。
    """
    # 尝试直接解码
    try:
        return base64.urlsafe_b64decode(s)
    except (base64.binascii.Error, ValueError):
        # 如果失败，尝试补全 padding 再解码
        padding = '=' * (-len(s) % 4)
        return base64.urlsafe_b64decode(s + padding)

def parse_ss_link(link):
    """解析 SS 链接"""
    try:
        link_body = link[5:]
        parts = link_body.split('#')
        main_part = parts[0]
        remark = unquote(parts[1]) if len(parts) > 1 else "Unknown"

        if '@' not in main_part:
             decoded_part = robust_b64decode(main_part).decode('utf-8', errors='ignore')
        else:
            decoded_part = main_part

        creds_part, server_part = decoded_part.split('@')
        host, port = server_part.split(':')
        
        return {"host": host, "port": int(port), "type": "SS", "location": remark, "qr_content": link}
    except Exception as e:
        logging.error(f"解析 SS 链接失败: {link[:30]}..., 错误: {e}")
        return None

def parse_vmess_link(link):
    """解析 Vmess 链接"""
    try:
        base64_str = link[8:]
        decoded_json = robust_b64decode(base64_str).decode('utf-8', errors='ignore')
        data = json.loads(decoded_json)
        
        return {"host": data.get('add', ''), "port": int(data.get('port', 0)), "type": "Vmess", "location": data.get('ps', 'Unknown'), "qr_content": link}
    except Exception as e:
        logging.error(f"解析 VMess 链接失败: {link[:30]}..., 错误: {e}")
        return None

# ... (parse_vless_link 和 parse_trojan_link 保持不变, 但为完整性也一并提供) ...

def parse_vless_link(link):
    try:
        parsed_url = urlparse(link); query_params = parse_qs(parsed_url.query); host = parsed_url.hostname; port = parsed_url.port; remark = unquote(parsed_url.fragment) if parsed_url.fragment else "Unknown"
        if 'host' in query_params: host = query_params['host'][0]
        elif 'sni' in query_params: host = query_params['sni'][0]
        return {"host": host, "port": int(port), "type": "VLESS", "location": remark, "qr_content": link}
    except Exception as e:
        logging.error(f"解析 VLESS 链接失败: {link[:30]}..., 错误: {e}")
        return None

def parse_trojan_link(link):
    try:
        parsed_url = urlparse(link); query_params = parse_qs(parsed_url.query); host = parsed_url.hostname; port = parsed_url.port; remark = unquote(parsed_url.fragment) if parsed_url.fragment else "Unknown"; host_for_ping = query_params.get('sni', [host])[0]
        return {"host": host_for_ping, "port": int(port), "type": "Trojan", "location": remark, "qr_content": link}
    except Exception as e:
        logging.error(f"解析 Trojan 链接失败: {link[:30]}..., 错误: {e}")
        return None

def parse_link(link):
    link = link.strip()
    if not link or link.startswith('#'): return None
    if link.startswith('ss://'): return parse_ss_link(link)
    if link.startswith('vmess://'): return parse_vmess_link(link)
    if link.startswith('vless://'): return parse_vless_link(link)
    if link.startswith('trojan://'): return parse_trojan_link(link)
    logging.warning(f"检测到不支持的链接格式: {link[:30]}...")
    return None
def parse_ss_link(link):
    """解析 SS 链接"""
    try:
        link_body = link[5:]
        parts = link_body.split('#')
        main_part = parts[0]
        remark = unquote(parts[1]) if len(parts) > 1 else "Unknown"

        if '@' not in main_part:
             decoded_part = robust_b64decode(main_part).decode('utf-8', errors='ignore')
        else:
            decoded_part = main_part

        creds_part, server_part = decoded_part.split('@')
        host, port = server_part.split(':')
        
        return {"host": host, "port": int(port), "type": "SS", "location": remark, "qr_content": link}
    except Exception as e:
        logging.error(f"解析 SS 链接失败: {link[:30]}..., 错误: {e}")
        return None

def parse_vmess_link(link):
    """解析 Vmess 链接"""
    try:
        base64_str = link[8:]
        decoded_json = robust_b64decode(base64_str).decode('utf-8', errors='ignore')
        data = json.loads(decoded_json)
        
        return {"host": data.get('add', ''), "port": int(data.get('port', 0)), "type": "Vmess", "location": data.get('ps', 'Unknown'), "qr_content": link}
    except Exception as e:
        logging.error(f"解析 VMess 链接失败: {link[:30]}..., 错误: {e}")
        return None

# ... (parse_vless_link 和 parse_trojan_link 保持不变, 但为完整性也一并提供) ...

def parse_vless_link(link):
    try:
        parsed_url = urlparse(link); query_params = parse_qs(parsed_url.query); host = parsed_url.hostname; port = parsed_url.port; remark = unquote(parsed_url.fragment) if parsed_url.fragment else "Unknown"
        if 'host' in query_params: host = query_params['host'][0]
        elif 'sni' in query_params: host = query_params['sni'][0]
        return {"host": host, "port": int(port), "type": "VLESS", "location": remark, "qr_content": link}
    except Exception as e:
        logging.error(f"解析 VLESS 链接失败: {link[:30]}..., 错误: {e}")
        return None

def parse_trojan_link(link):
    try:
        parsed_url = urlparse(link); query_params = parse_qs(parsed_url.query); host = parsed_url.hostname; port = parsed_url.port; remark = unquote(parsed_url.fragment) if parsed_url.fragment else "Unknown"; host_for_ping = query_params.get('sni', [host])[0]
        return {"host": host_for_ping, "port": int(port), "type": "Trojan", "location": remark, "qr_content": link}
    except Exception as e:
        logging.error(f"解析 Trojan 链接失败: {link[:30]}..., 错误: {e}")
        return None

def parse_link(link):
    link = link.strip()
    if not link or link.startswith('#'): return None
    if link.startswith('ss://'): return parse_ss_link(link)
    if link.startswith('vmess://'): return parse_vmess_link(link)
    if link.startswith('vless://'): return parse_vless_link(link)
    if link.startswith('trojan://'): return parse_trojan_link(link)
    logging.warning(f"检测到不支持的链接格式: {link[:30]}...")
    return None
