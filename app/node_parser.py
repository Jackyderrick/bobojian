# 文件路径: live-stream-project/app/node_parser.py
# 作用: 解析各种节点链接（SS, Vmess, VLESS, Trojan）

import base64
import json
import logging
from urllib.parse import urlparse, unquote, parse_qs

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_ss_link(link):
    """解析SS链接"""
    try:
        # 移除协议前缀
        link = link[5:]
        
        # 处理包含#的情况
        if '#' in link:
            link, tag = link.split('#', 1)
            tag = unquote(tag)
        else:
            tag = ""
            
        # 解码
        if len(link) % 4 != 0:
            link += '=' * (4 - len(link) % 4)
            
        decoded = base64.urlsafe_b64decode(link).decode('utf-8')
        
        # 解析加密方式、密码、地址和端口
        if '@' in decoded:
            method_pass, addr_port = decoded.split('@', 1)
            method, password = method_pass.split(':', 1)
            if ':' in addr_port:
                server, port = addr_port.split(':', 1)
                port = int(port)
            else:
                server = addr_port
                port = 8388  # 默认端口
        else:
            # 处理旧格式
            server_port, method_pass = decoded.split(':', 1)
            server, port = server_port.split(':', 1)
            port = int(port)
            method, password = method_pass.split(':', 1)
            
        return {
            'type': 'ss',
            'server': server,
            'port': port,
            'method': method,
            'password': password,
            'tag': tag
        }
    except Exception as e:
        logging.error(f"解析SS链接失败: {link[:50]}..., 错误: {e}")
        return None

def parse_vmess_link(link):
    """解析VMess链接"""
    try:
        # 移除协议前缀并解码
        link = link[8:]
        if len(link) % 4 != 0:
            link += '=' * (4 - len(link) % 4)
            
        decoded = base64.urlsafe_b64decode(link).decode('utf-8')
        data = json.loads(decoded)
        
        return {
            'type': 'vmess',
            'server': data.get('add', ''),
            'port': data.get('port', 443),
            'id': data.get('id', ''),
            'alterId': data.get('aid', 0),
            'security': data.get('scy', 'auto'),
            'network': data.get('net', 'tcp'),
            'tag': data.get('ps', '')
        }
    except Exception as e:
        logging.error(f"解析VMess链接失败: {link[:50]}..., 错误: {e}")
        return None

def parse_vless_link(link):
    """解析VLESS链接"""
    try:
        # 移除协议前缀
        parsed = urlparse(link)
        userinfo = parsed.netloc.split('@')[0] if '@' in parsed.netloc else ''
        netloc = parsed.netloc.split('@')[1] if '@' in parsed.netloc else parsed.netloc
        
        server = netloc.split(':')[0] if ':' in netloc else netloc
        port = int(netloc.split(':')[1]) if ':' in netloc else 443
        
        # 解析查询参数
        params = parse_qs(parsed.query)
        
        return {
            'type': 'vless',
            'server': server,
            'port': port,
            'id': userinfo,
            'encryption': params.get('encryption', ['none'])[0],
            'network': params.get('net', ['tcp'])[0],
            'tag': unquote(parsed.fragment) if parsed.fragment else ''
        }
    except Exception as e:
        logging.error(f"解析VLESS链接失败: {link[:50]}..., 错误: {e}")
        return None

def parse_trojan_link(link):
    """解析Trojan链接"""
    try:
        # 移除协议前缀
        parsed = urlparse(link)
        password = parsed.netloc.split('@')[0] if '@' in parsed.netloc else ''
        netloc = parsed.netloc.split('@')[1] if '@' in parsed.netloc else parsed.netloc
        
        server = netloc.split(':')[0] if ':' in netloc else netloc
        port = int(netloc.split(':')[1]) if ':' in netloc else 443
        
        return {
            'type': 'trojan',
            'server': server,
            'port': port,
            'password': password,
            'tag': unquote(parsed.fragment) if parsed.fragment else ''
        }
    except Exception as e:
        logging.error(f"解析Trojan链接失败: {link[:50]}..., 错误: {e}")
        return None

def parse_link(link):
    """根据链接前缀选择合适的解析器"""
    link = link.strip()
    if not link or link.startswith('#'):
        return None
        
    if link.startswith('ss://'):
        return parse_ss_link(link)
    elif link.startswith('vmess://'):
        return parse_vmess_link(link)
    elif link.startswith('vless://'):
        return parse_vless_link(link)
    elif link.startswith('trojan://'):
        return parse_trojan_link(link)
    else:
        logging.warning(f"不支持的链接格式: {link[:30]}...")
        return None
