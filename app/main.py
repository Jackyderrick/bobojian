# 文件路径: app/main.py
# 最终服务器部署版，优化了启动逻辑，增强了稳定性。

import os
import time
import subprocess
import base64
from io import BytesIO
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright
import qrcode
import logging
import requests
import threading
from node_parser import parse_link

# 导入 FastAPI 相关库
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import List

# --- 1. 从环境变量加载配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

YOUTUBE_STREAM_KEY = os.getenv('YOUTUBE_STREAM_KEY')
API_KEY = os.getenv('API_KEY')
UPDATE_INTERVAL_SECONDS = int(os.getenv('UPDATE_INTERVAL_SECONDS', 300))
STATE_FILE_PATH = os.getenv('STATE_FILE_PATH', 'last_index.txt')

RTMP_URL = f"rtmp://a.rtmp.youtube.com/live2/{YOUTUBE_STREAM_KEY}"
SCREENSHOT_PATH = "output.png"
NODES_FILE_PATH = "nodes.txt"

# --- 2. 启动前安全检查 ---
if not YOUTUBE_STREAM_KEY or YOUTUBE_STREAM_KEY == 'xxxx-xxxx-xxxx-xxxx-xxxx':
    raise ValueError("致命错误：请在 docker-compose.yml 中设置有效的 YOUTUBE_STREAM_KEY")
if not API_KEY or API_KEY == 'YOUR_SUPER_SECRET_API_KEY':
    raise ValueError("致命错误：请在 docker-compose.yml 中设置一个安全的 API_KEY")

# --- 3. FastAPI 应用与 API 端点 ---
app = FastAPI()

class NodeUpdateRequest(BaseModel):
    nodes: List[str]

@app.post("/api/update_nodes")
async def update_nodes(request: Request, payload: NodeUpdateRequest):
    if request.headers.get("X-API-KEY") != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid API Key")
    
    try:
        with open(NODES_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write('\n'.join(payload.nodes))
        logging.info(f"成功通过 API 更新了 {len(payload.nodes)} 个节点。")
        return {"status": "success", "message": f"Updated {len(payload.nodes)} nodes."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 4. 直播核心逻辑 (已优化) ---
def run_livestream_loop():
    ffmpeg_process = None
    
    # 【优化】不再单独生成初始画面，直接进入主循环
    # 循环内的 try...except 机制足以处理所有错误
    while True:
        try:
            logging.info("开始新一轮画面更新...")
            node_data = get_node_data()
            qr_base_64 = generate_qr_code_base64(node_data['qr_content'])
            node_data['qr_code_base64'] = qr_base_64
            html = render_html('template.html', node_data)
            take_screenshot(html, SCREENSHOT_PATH)
            
            if ffmpeg_process is None or ffmpeg_process.poll() is not None:
                if ffmpeg_process: 
                    logging.warning(f"检测到 FFmpeg 进程已退出，返回码: {ffmpeg_process.returncode}。正在重启...")
                ffmpeg_process = start_ffmpeg_stream()
            else:
                logging.info("FFmpeg 进程正在稳定运行中...")
        except Exception as e:
            logging.error(f"直播主循环发生严重错误: {e}", exc_info=True)
        
        logging.info(f"本轮更新完成，将休眠 {UPDATE_INTERVAL_SECONDS} 秒。")
        time.sleep(UPDATE_INTERVAL_SECONDS)

# --- 5. 各功能函数 (完整实现) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')

def get_node_data():
    logging.info(f"开始从 {NODES_FILE_PATH} 读取和筛选节点数据...")
    all_nodes = []
    try:
        with open(NODES_FILE_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                node_data = parse_link(line)
                if node_data: all_nodes.append(node_data)
    except FileNotFoundError:
        return {"server_address": "节点文件未找到", "location": "N/A", "node_type": "N/A", "test_time": time.strftime("%Y-%m-%d %H:%M:%S"), "qr_content": "nodes.txt not found"}
    
    if not all_nodes:
        return {"server_address": "请先添加节点", "location": "N/A", "node_type": "N/A", "test_time": time.strftime("%Y-%m-%d %H:%M:%S"), "qr_content": "Please add nodes in nodes.txt"}
    
    usable_nodes = []
    for node in all_nodes:
        if check_node_from_china(node["host"], node["port"]):
            usable_nodes.append(node)
        time.sleep(2)
    
    if not usable_nodes:
        return {"server_address": "暂无可用节点", "location": "N/A", "node_type": "N/A", "test_time": time.strftime("%Y-%m-%d %H:%M:%S"), "qr_content": "No nodes available"}
    else:
        last_index = -1
        try:
            with open(STATE_FILE_PATH, 'r') as f: content = f.read().strip(); last_index = int(content) if content else -1
        except (IOError, ValueError): last_index = -1
        next_index = (last_index + 1) % len(usable_nodes)
        selected_node = usable_nodes[next_index]
        logging.info(f"筛选到 {len(usable_nodes)} 个可用节点，轮询选择了第 {next_index + 1} 个: {selected_node.get('location')}")
        with open(STATE_FILE_PATH, 'w') as f: f.write(str(next_index))
        return {"server_address": selected_node["host"], "location": selected_node["location"], "node_type": selected_node["type"], "test_time": time.strftime("%Y-%m-%d %H:%M:%S"), "qr_content": selected_node["qr_content"]}

def check_node_from_china(host, port):
    api_url = f"https://api.boce.com/v3/task/tcping?host={host}&port={port}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(api_url, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        china_nodes = [node for node in data.get('data', []) if node.get('country') == '中国']
        if not china_nodes: return False
        connected_count = sum(1 for node in china_nodes if node.get('status') == 'success')
        return connected_count / len(china_nodes) >= 0.5
    except Exception: return False

def generate_qr_code_base64(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def render_html(template_name, data):
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template(template_name)
    return template.render(data)

def take_screenshot(html_content, output_path):
    temp_output_path = output_path + ".tmp"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_content)
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.wait_for_timeout(2000)
        page.screenshot(path=temp_output_path, type='png')
        browser.close()
    os.rename(temp_output_path, output_path)

def start_ffmpeg_stream():
    command = [
        'ffmpeg', '-re', '-framerate', '10', '-loop', '1', '-i', SCREENSHOT_PATH,
        '-c:v', 'libx264', '-preset', 'veryfast', '-pix_fmt', 'yuv420p',
        '-s', '1920x1080', '-b:v', '2500k', '-maxrate', '3000k', '-bufsize', '5000k',
        '-g', '50', '-c:a', 'aac', '-b:a', '128k', '-ar', '44100', '-f', 'flv', RTMP_URL
    ]
    return subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# --- 6. 程序主入口 ---
if __name__ == "__main__":
    if not os.path.exists(STATE_FILE_PATH):
        with open(STATE_FILE_PATH, 'w') as f: f.write('-1')
    
    livestream_thread = threading.Thread(target=run_livestream_loop, daemon=True)
    livestream_thread.start()
    
    logging.info(f"API 服务器将在 http://0.0.0.0:8000 上启动")
    uvicorn.run(app, host="0.0.0.0", port=8000)
