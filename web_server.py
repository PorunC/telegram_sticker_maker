#!/usr/bin/env python3
"""
Telegram 表情包制作器 Web 服务器

提供完整的Web界面用于：
- 配置管理 (.env文件编辑)
- 文件上传和表情包制作
- 表情包CRUD管理
- 实时进度显示
"""

import os
import json
import time
import asyncio
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.parse import unquote

from flask import Flask, request, jsonify, render_template, send_file, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename

from telegram_sticker_maker import TelegramStickerMaker, StickerConfig
from telegram_api_uploader import TelegramStickerUploader, load_env_file
from telegram_sticker_manager import TelegramStickerManager

app = Flask(__name__)
CORS(app)

# 配置
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'webm', 'tgs'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 全局状态管理
processing_status = {}
active_connections = {}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_env_config():
    """读取.env配置"""
    env_vars = load_env_file()
    return {
        'TELEGRAM_BOT_TOKEN': env_vars.get('TELEGRAM_BOT_TOKEN', ''),
        'TELEGRAM_USER_ID': env_vars.get('TELEGRAM_USER_ID', ''),
        'PACK_NAME_PREFIX': env_vars.get('PACK_NAME_PREFIX', ''),
        'DEFAULT_EMOJI': env_vars.get('DEFAULT_EMOJI', '😀'),
        # 代理设置
        'PROXY_ENABLED': env_vars.get('PROXY_ENABLED', 'false'),
        'PROXY_TYPE': env_vars.get('PROXY_TYPE', 'http'),
        'PROXY_HOST': env_vars.get('PROXY_HOST', ''),
        'PROXY_PORT': env_vars.get('PROXY_PORT', ''),
        'PROXY_AUTH_ENABLED': env_vars.get('PROXY_AUTH_ENABLED', 'false'),
        'PROXY_USERNAME': env_vars.get('PROXY_USERNAME', ''),
        'PROXY_PASSWORD': env_vars.get('PROXY_PASSWORD', '')
    }

def convert_file_to_sticker_format(maker: TelegramStickerMaker, input_path: str) -> Optional[str]:
    """将输入文件转换为表情包格式"""
    try:
        # 分析输入文件
        analysis = maker.analyze_input(input_path)
        
        # 生成输出文件名
        input_file = Path(input_path)
        timestamp = str(int(time.time()))
        
        # 根据分析结果选择格式
        recommended_format = maker._recommend_format(analysis)
        
        if recommended_format == "static":
            # 转换为静态表情包
            output_path = os.path.join(UPLOAD_FOLDER, f"converted_{timestamp}_{input_file.stem}.png")
            result = maker.create_static_sticker(input_path, output_path)
            
            if result.get('success'):
                return output_path
        else:
            # 转换为WebM表情包
            output_path = os.path.join(UPLOAD_FOLDER, f"converted_{timestamp}_{input_file.stem}.webm")
            result = maker.create_webm_sticker(input_path, output_path)
            
            if result.get('success'):
                return output_path
        
        return None
        
    except Exception as e:
        print(f"转换文件失败 {input_path}: {e}")
        return None

def save_env_config(config: Dict[str, str]) -> bool:
    """保存.env配置"""
    try:
        env_lines = []
        
        # 定义配置项的顺序和处理规则
        config_order = [
            'TELEGRAM_BOT_TOKEN',
            'TELEGRAM_USER_ID', 
            'PACK_NAME_PREFIX',
            'DEFAULT_EMOJI',
            'PROXY_ENABLED',
            'PROXY_TYPE',
            'PROXY_HOST',
            'PROXY_PORT',
            'PROXY_AUTH_ENABLED',
            'PROXY_USERNAME',
            'PROXY_PASSWORD'
        ]
        
        # 按顺序写入配置
        for key in config_order:
            value = config.get(key, '')
            
            # 必需配置项或已启用的可选项才写入
            if key in ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_USER_ID'] and value:
                env_lines.append(f"{key}={value}")
            elif key in ['PACK_NAME_PREFIX', 'DEFAULT_EMOJI'] and value:
                env_lines.append(f"{key}={value}")
            elif key == 'PROXY_ENABLED':
                env_lines.append(f"{key}={value}")
            elif key.startswith('PROXY_') and key != 'PROXY_ENABLED':
                if config.get('PROXY_ENABLED') == 'true' and value:
                    env_lines.append(f"{key}={value}")
        
        with open('.env', 'w', encoding='utf-8') as f:
            f.write('\n'.join(env_lines) + '\n')
        
        return True
    except Exception as e:
        print(f"保存.env配置失败: {e}")
        return False

def get_proxy_config(config: Dict[str, str]) -> Optional[Dict]:
    """根据配置生成代理配置"""
    if config.get('PROXY_ENABLED') != 'true':
        return None
    
    proxy_type = config.get('PROXY_TYPE', 'http')
    proxy_host = config.get('PROXY_HOST', '')
    proxy_port = config.get('PROXY_PORT', '')
    
    if not proxy_host or not proxy_port:
        return None
    
    # 构建代理URL
    if config.get('PROXY_AUTH_ENABLED') == 'true':
        username = config.get('PROXY_USERNAME', '')
        password = config.get('PROXY_PASSWORD', '')
        if username and password:
            if proxy_type == 'http':
                proxy_url = f"http://{username}:{password}@{proxy_host}:{proxy_port}"
            else:
                proxy_url = f"{proxy_type}://{username}:{password}@{proxy_host}:{proxy_port}"
        else:
            proxy_url = f"{proxy_type}://{proxy_host}:{proxy_port}"
    else:
        proxy_url = f"{proxy_type}://{proxy_host}:{proxy_port}"
    
    # 返回requests库格式的代理配置
    return {
        'http': proxy_url,
        'https': proxy_url
    }

def validate_bot_token(token: str, proxy_config: Dict = None) -> Dict[str, Any]:
    """验证Bot Token"""
    if not token:
        return {'valid': False, 'error': 'Token不能为空'}
    
    try:
        # 创建临时的TelegramStickerUploader实例来测试连接
        import requests
        
        # 构建测试API请求
        url = f"https://api.telegram.org/bot{token}/getMe"
        
        # 使用代理进行请求
        response = requests.get(url, proxies=proxy_config, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        if result.get('ok'):
            return {'valid': True, 'bot_info': result['result']}
        else:
            return {'valid': False, 'error': result.get('description', 'Unknown error')}
            
    except requests.exceptions.ProxyError as e:
        return {'valid': False, 'error': f'代理连接失败: {str(e)}'}
    except requests.exceptions.ConnectTimeout as e:
        return {'valid': False, 'error': f'连接超时: {str(e)}'}
    except requests.exceptions.ConnectionError as e:
        return {'valid': False, 'error': f'连接错误: {str(e)}'}
    except Exception as e:
        return {'valid': False, 'error': str(e)}

# ========== 路由定义 ==========

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    """获取配置信息"""
    config = get_env_config()
    
    # 验证Bot Token
    bot_valid = False
    bot_info = None
    if config['TELEGRAM_BOT_TOKEN']:
        proxy_config = get_proxy_config(config)
        validation = validate_bot_token(config['TELEGRAM_BOT_TOKEN'], proxy_config)
        bot_valid = validation['valid']
        bot_info = validation.get('bot_info')
    
    return jsonify({
        'config': config,
        'bot_valid': bot_valid,
        'bot_info': bot_info
    })

@app.route('/api/config', methods=['POST'])
def save_config():
    """保存配置信息"""
    data = request.json
    
    # 验证必需字段
    if not data.get('TELEGRAM_BOT_TOKEN'):
        return jsonify({'success': False, 'error': 'Bot Token是必需的'}), 400
    
    # 验证Bot Token（使用代理配置）
    proxy_config = get_proxy_config(data)
    validation = validate_bot_token(data['TELEGRAM_BOT_TOKEN'], proxy_config)
    if not validation['valid']:
        return jsonify({'success': False, 'error': f"无效的Bot Token: {validation['error']}"}), 400
    
    # 保存配置
    if save_env_config(data):
        return jsonify({'success': True, 'bot_info': validation['bot_info']})
    else:
        return jsonify({'success': False, 'error': '保存配置失败'}), 500

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """上传文件"""
    if 'files' not in request.files:
        return jsonify({'success': False, 'error': '没有选择文件'}), 400
    
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({'success': False, 'error': '没有选择文件'}), 400
    
    uploaded_files = []
    errors = []
    
    for file in files:
        if file and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                # 添加时间戳避免文件名冲突
                timestamp = str(int(time.time()))
                name, ext = os.path.splitext(filename)
                unique_filename = f"{name}_{timestamp}{ext}"
                
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                
                # 获取文件信息
                file_size = os.path.getsize(file_path)
                uploaded_files.append({
                    'filename': filename,
                    'unique_filename': unique_filename,
                    'file_path': file_path,
                    'size': file_size,
                    'type': Path(filename).suffix.lower()
                })
                
            except Exception as e:
                errors.append(f"上传 {file.filename} 失败: {str(e)}")
        else:
            errors.append(f"不支持的文件类型: {file.filename}")
    
    return jsonify({
        'success': len(uploaded_files) > 0,
        'files': uploaded_files,
        'errors': errors
    })

@app.route('/api/create-sticker-pack', methods=['POST'])
def create_sticker_pack():
    """创建表情包"""
    data = request.json
    
    # 验证参数
    required_fields = ['pack_name', 'pack_title', 'files']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'缺少必需参数: {field}'}), 400
    
    config = get_env_config()
    if not config['TELEGRAM_BOT_TOKEN'] or not config['TELEGRAM_USER_ID']:
        return jsonify({'success': False, 'error': '请先配置Bot Token和用户ID'}), 400
    
    # 创建任务ID用于跟踪进度
    task_id = str(int(time.time() * 1000))
    processing_status[task_id] = {
        'status': 'starting',
        'progress': 0,
        'message': '正在开始处理...',
        'total_files': len(data['files']),
        'processed_files': 0
    }
    
    # 异步处理表情包创建
    def process_sticker_pack():
        try:
            processing_status[task_id]['status'] = 'processing'
            processing_status[task_id]['message'] = '正在转换文件...'
            
            # 转换文件
            converted_files = []
            sticker_config = StickerConfig(
                output_dir=UPLOAD_FOLDER,
                auto_format=True
            )
            maker = TelegramStickerMaker(sticker_config)
            
            for i, file_info in enumerate(data['files']):
                processing_status[task_id]['progress'] = (i / len(data['files'])) * 50  # 转换占50%
                processing_status[task_id]['message'] = f"正在转换 {file_info['filename']}..."
                
                input_path = file_info['file_path']
                if os.path.exists(input_path):
                    output_path = convert_file_to_sticker_format(maker, input_path)
                    if output_path and os.path.exists(output_path):
                        converted_files.append(output_path)
                        processing_status[task_id]['processed_files'] = i + 1
            
            if not converted_files:
                processing_status[task_id]['status'] = 'error'
                processing_status[task_id]['message'] = '没有成功转换的文件'
                return
            
            # 上传到Telegram
            processing_status[task_id]['progress'] = 50
            processing_status[task_id]['message'] = '正在上传到Telegram...'
            
            proxy_config = get_proxy_config(config)
            uploader = TelegramStickerUploader(config['TELEGRAM_BOT_TOKEN'], proxy_config)
            user_id = int(config['TELEGRAM_USER_ID'])
            
            # 生成唯一的表情包名称
            pack_name = data['pack_name']
            if not pack_name.endswith(f"_by_{uploader.bot_username}"):
                pack_name = uploader.generate_pack_name(pack_name, user_id)
            
            # 准备emoji列表
            emojis = data.get('emojis', [])
            if not emojis:
                emojis = [config.get('DEFAULT_EMOJI', '😀')] * len(converted_files)
            
            # 上传表情包
            result = uploader.upload_sticker_pack(
                user_id=user_id,
                pack_name=pack_name,
                pack_title=data['pack_title'],
                sticker_files=converted_files,
                emojis=emojis
            )
            
            processing_status[task_id]['progress'] = 100
            
            if result['success']:
                processing_status[task_id]['status'] = 'completed'
                processing_status[task_id]['message'] = '表情包创建成功!'
                processing_status[task_id]['result'] = result
            else:
                processing_status[task_id]['status'] = 'error'
                processing_status[task_id]['message'] = f"创建失败: {'; '.join(result['errors'])}"
            
            # 清理临时文件
            for file_path in converted_files:
                try:
                    os.remove(file_path)
                except:
                    pass
            
        except Exception as e:
            processing_status[task_id]['status'] = 'error'
            processing_status[task_id]['message'] = f'处理错误: {str(e)}'
    
    # 启动后台处理线程
    thread = threading.Thread(target=process_sticker_pack)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'task_id': task_id
    })

@app.route('/api/task-status/<task_id>')
def get_task_status(task_id):
    """获取任务状态"""
    if task_id not in processing_status:
        return jsonify({'error': '任务不存在'}), 404
    
    return jsonify(processing_status[task_id])

@app.route('/api/sticker-packs')
def list_sticker_packs():
    """列出表情包（需要手动提供包名）"""
    # 注意：Telegram API没有列出所有表情包的方法
    # 这里返回一些常见的包名模式供用户选择
    config = get_env_config()
    
    if not config['TELEGRAM_BOT_TOKEN']:
        return jsonify({'success': False, 'error': '请先配置Bot Token'}), 400
    
    try:
        proxy_config = get_proxy_config(config)
        uploader = TelegramStickerUploader(config['TELEGRAM_BOT_TOKEN'], proxy_config)
        bot_username = uploader.bot_username
        
        # 返回命名约定信息
        return jsonify({
            'success': True,
            'bot_username': bot_username,
            'naming_pattern': f"*_by_{bot_username}",
            'message': 'Telegram API不支持列出所有表情包，请手动输入包名进行管理'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/sticker-pack/<pack_name>')
def get_sticker_pack(pack_name):
    """获取表情包详情"""
    config = get_env_config()
    if not config['TELEGRAM_BOT_TOKEN']:
        return jsonify({'success': False, 'error': '请先配置Bot Token'}), 400
    
    try:
        pack_name = unquote(pack_name)  # URL解码
        proxy_config = get_proxy_config(config)
        uploader = TelegramStickerUploader(config['TELEGRAM_BOT_TOKEN'], proxy_config)
        analysis = uploader.analyze_sticker_set(pack_name)
        
        if 'error' in analysis:
            return jsonify({'success': False, 'error': analysis['error']}), 404
        
        return jsonify({'success': True, 'pack': analysis})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sticker-pack/<pack_name>/sticker/<file_id>/emoji', methods=['PUT'])
def update_sticker_emoji(pack_name, file_id):
    """更新贴纸emoji"""
    config = get_env_config()
    if not config['TELEGRAM_BOT_TOKEN']:
        return jsonify({'success': False, 'error': '请先配置Bot Token'}), 400
    
    data = request.json
    emoji_list = data.get('emoji_list', [])
    
    if not emoji_list:
        return jsonify({'success': False, 'error': 'emoji列表不能为空'}), 400
    
    try:
        file_id = unquote(file_id)
        proxy_config = get_proxy_config(config)
        uploader = TelegramStickerUploader(config['TELEGRAM_BOT_TOKEN'], proxy_config)
        success = uploader.set_sticker_emoji_list(file_id, emoji_list)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': '更新emoji失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sticker-pack/<pack_name>/sticker/<file_id>', methods=['DELETE'])
def delete_sticker(pack_name, file_id):
    """删除贴纸"""
    config = get_env_config()
    if not config['TELEGRAM_BOT_TOKEN']:
        return jsonify({'success': False, 'error': '请先配置Bot Token'}), 400
    
    try:
        file_id = unquote(file_id)
        proxy_config = get_proxy_config(config)
        uploader = TelegramStickerUploader(config['TELEGRAM_BOT_TOKEN'], proxy_config)
        success = uploader.delete_sticker_from_set(file_id)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': '删除贴纸失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sticker-pack/<pack_name>', methods=['DELETE'])
def delete_sticker_pack(pack_name):
    """删除表情包"""
    config = get_env_config()
    if not config['TELEGRAM_BOT_TOKEN']:
        return jsonify({'success': False, 'error': '请先配置Bot Token'}), 400
    
    try:
        pack_name = unquote(pack_name)
        proxy_config = get_proxy_config(config)
        uploader = TelegramStickerUploader(config['TELEGRAM_BOT_TOKEN'], proxy_config)
        success = uploader.delete_sticker_set(pack_name)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': '删除表情包失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """获取上传的文件"""
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

if __name__ == '__main__':
    print("🌐 启动 Telegram 表情包制作器 Web 服务...")
    print("🔗 访问地址: http://localhost:5000")
    print("📁 上传目录:", os.path.abspath(UPLOAD_FOLDER))
    
    app.run(debug=True, host='0.0.0.0', port=5000)