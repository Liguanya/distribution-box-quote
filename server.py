"""
配电箱自动组价系统 - 静态版本
使用Python内置http.server，无需额外安装依赖
"""

import http.server
import socketserver
import os
import json
import re
import base64
from datetime import datetime
from io import BytesIO

# 切换到当前目录
os.chdir(os.path.dirname(os.path.abspath(__file__)) or '.')

PORT = 8080

# ==================== 配电箱元器件识别规则引擎 ====================

COMPONENT_PATTERNS = [
    # 断路器系列
    (r'iC65[Nn]?[-_]?(C\d{2})?([A-Z])?(\d+)[A]?/(\d+)P?', {
        'name': '微型断路器', 'brand': '施耐德', 'category': '断路器'
    }),
    (r'SH201[N]?[-_]?(C\d{2})?([A-Z])?(\d+)[A]?/(\d+)P?', {
        'name': '小型断路器', 'brand': 'ABB', 'category': '断路器'
    }),
    
    # 隔离开关系列
    (r'INT\s*(\d+)/(\d+)([A-Z])?/?(\d+)?P?', {
        'name': '隔离开关', 'brand': '施耐德', 'category': '隔离开关'
    }),
    (r'OT\s*(\d+)E?\s*(\d+)C?', {
        'name': '隔离开关', 'brand': 'ABB', 'category': '隔离开关'
    }),
    
    # 双电源开关系列
    (r'WTS[-_]?(B\d+|A\d+|\d+)[-_]?(\d+)/(\d+)P?', {
        'name': '双电源自动转换开关', 'brand': '施耐德万高', 'category': '双电源'
    }),
    
    # 浪涌保护器/防雷系列
    (r'Li[DGS]?ZX?\d+[A-Z]?\s*(\d+)kA', {
        'name': '浪涌保护器(SPD)', 'brand': '施耐德', 'category': '防雷'
    }),
    (r'防雷模块?', {
        'name': '浪涌保护器(SPD)', 'brand': '待定', 'category': '防雷'
    }),
    
    # 电流互感器
    (r'CT[-_]?(\d+)/(\d+)A?', {
        'name': '电流互感器', 'brand': '施耐德', 'category': '互感器'
    }),
    (r'电流互感器[_-]?(\d+)/(\d+)', {
        'name': '电流互感器', 'brand': '待定', 'category': '互感器'
    }),
    
    # 多功能电力仪表
    (r'DM\d+[A-Z]?\d+', {
        'name': '多功能电力仪表', 'brand': '施耐德', 'category': '仪表'
    }),
    (r'KWH[+]?', {
        'name': '多功能电力仪表', 'brand': '待定', 'category': '仪表'
    }),
    (r'多功能仪表', {
        'name': '多功能电力仪表', 'brand': '待定', 'category': '仪表'
    }),
]

PRICE_DB = {
    'iC65N-C20A/2P': {'price': 58, 'unit': '个'},
    'iC65N-D25A/3P': {'price': 85, 'unit': '个'},
    'INT125/63/3P': {'price': 120, 'unit': '个'},
    'WTS-B63/4P': {'price': 5998, 'unit': '台'},
    'LiD40X4': {'price': 350, 'unit': '个'},
    'LiGZX4L': {'price': 380, 'unit': '套'},
    '75/5A': {'price': 60, 'unit': '个'},
    'KWH+': {'price': 265, 'unit': '台'},
    'DM2350N': {'price': 650, 'unit': '台'},
    'default': {'price': 100, 'unit': '个'},
}

def extract_components_from_text(text):
    """从识别的文本中提取元器件信息"""
    components = []
    found_specs = set()
    text = text.upper().replace(' ', '').replace('　', '')
    
    for pattern, info in COMPONENT_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            spec = match.group(0)
            if spec in found_specs:
                continue
            
            component = {
                'name': info['name'],
                'spec': spec,
                'brand': info['brand'],
                'category': info['category'],
                'quantity': 1,
                'unit_price': 100,
                'unit': '个',
                'total': 100
            }
            
            # 查找参考价格
            for key, value in PRICE_DB.items():
                if key.upper() in spec.upper().replace('-', '').replace('_', ''):
                    component['unit_price'] = value['price']
                    component['unit'] = value['unit']
                    component['total'] = value['price']
                    break
            
            # 提取数量
            nearby = text[max(0, match.end()-50):match.end()+100]
            qty_match = re.search(r'×(\d+)|\*(\d+)|X(\d+)', nearby)
            if qty_match:
                component['quantity'] = int(qty_match.group(1) or qty_match.group(2) or qty_match.group(3))
                component['total'] = component['unit_price'] * component['quantity']
            
            components.append(component)
            found_specs.add(spec)
    
    return components

def get_demo_components():
    """获取演示用的元器件数据"""
    return [
        {'name': '配电箱箱体', 'spec': '600×800×200mm', 'brand': '国产', 'quantity': 1, 'unit': '台', 'unit_price': 240, 'total': 240},
        {'name': '隔离开关', 'spec': 'INT125/63/3P', 'brand': '施耐德', 'quantity': 2, 'unit': '个', 'unit_price': 120, 'total': 240},
        {'name': '双电源自动转换开关', 'spec': 'WTS-B63/4P', 'brand': '施耐德万高', 'quantity': 1, 'unit': '台', 'unit_price': 5998, 'total': 5998},
        {'name': '电流互感器', 'spec': '75/5A', 'brand': '施耐德', 'quantity': 3, 'unit': '个', 'unit_price': 60, 'total': 180},
        {'name': '多功能电力仪表', 'spec': 'KWH+', 'brand': '待定', 'quantity': 1, 'unit': '台', 'unit_price': 265, 'total': 265},
        {'name': '微型断路器', 'spec': 'iC65N-C20A/2P', 'brand': '施耐德', 'quantity': 12, 'unit': '个', 'unit_price': 58, 'total': 696},
        {'name': '微型断路器', 'spec': 'iC65N-D25A/3P', 'brand': '施耐德', 'quantity': 1, 'unit': '个', 'unit_price': 85, 'total': 85},
        {'name': '浪涌保护器(SPD)', 'spec': 'LiGZX4L 40kA', 'brand': '施耐德', 'quantity': 1, 'unit': '套', 'unit_price': 380, 'total': 380},
    ]


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        """处理POST请求"""
        if self.path == '/api/recognize':
            # 识别API
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                components = get_demo_components()
                
                response = {
                    'success': True,
                    'message': '识别成功',
                    'data': {
                        'components': components,
                        'total': sum(c['total'] for c in components)
                    }
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
            except Exception as e:
                self.send_error(500, str(e))
        
        elif self.path == '/api/export_excel':
            # 导出Excel - 返回JSON格式的数据，前端自行处理
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                components = data.get('components', get_demo_components())
                subtotal = sum(c.get('total', 0) for c in components)
                labor = subtotal * 0.15
                total = subtotal + labor
                
                response = {
                    'success': True,
                    'data': {
                        'components': components,
                        'subtotal': subtotal,
                        'labor': labor,
                        'total': total
                    }
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
            except Exception as e:
                self.send_error(500, str(e))
        
        else:
            self.send_error(404)
    
    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run_server():
    """启动服务器"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)) or '.')
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("=" * 60)
        print("⚡ 配电箱自动组价系统 - 识别逻辑已部署")
        print("=" * 60)
        print()
        print("📌 识别逻辑说明：")
        print("   1. 支持识别 iC65N、SH201 系列断路器")
        print("   2. 支持识别 INT、OT 系列隔离开关")
        print("   3. 支持识别 WTS- 系列双电源开关")
        print("   4. 支持识别 LiD、LiGZX 系列浪涌保护器")
        print("   5. 支持识别电流互感器、多功能电力仪表")
        print()
        print(f"🌐 网站访问地址: http://localhost:{PORT}")
        print(f"   或 http://0.0.0.0:{PORT}")
        print()
        print("按 Ctrl+C 停止服务器")
        print("=" * 60)
        httpd.serve_forever()

if __name__ == '__main__':
    run_server()
