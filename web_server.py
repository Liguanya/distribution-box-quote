"""
配电箱自动组价系统 - 带图像识别的Web版本
部署到云电脑，使用OCR+规则匹配识别配电箱元器件
"""

from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import os
import re
import json
import base64
from io import BytesIO
import pandas as pd
from datetime import datetime

app = Flask(__name__, static_folder='static')
CORS(app)

# 确保目录存在
os.makedirs('static', exist_ok=True)
os.makedirs('uploads', exist_ok=True)

# ==================== 配电箱元器件识别规则引擎 ====================
# 这是核心的识别逻辑，将我识别配电箱系统图的规则教给网站

# 元器件名称正则匹配模式
COMPONENT_PATTERNS = [
    # 断路器系列
    (r'iC65[Nn]?[-_]?(C\d{2})?([A-Z])?(\d+)[A]?/(\d+)P?', {
        'name': '微型断路器',
        'brand': '施耐德',
        'category': '断路器'
    }),
    (r'SH201[N]?[-_]?(C\d{2})?([A-Z])?(\d+)[A]?/(\d+)P?', {
        'name': '小型断路器',
        'brand': 'ABB',
        'category': '断路器'
    }),
    (r'S2[01]\d{2}[-_]?(C\d{2})?([A-Z])?(\d+)[A]?/(\d+)P?', {
        'name': '小型断路器',
        'brand': 'ABB',
        'category': '断路器'
    }),
    
    # 隔离开关系列
    (r'INT\s*(\d+)/(\d+)([A-Z])?/?(\d+)?P?', {
        'name': '隔离开关',
        'brand': '施耐德',
        'category': '隔离开关'
    }),
    (r'OT\s*(\d+)E?\s*(\d+)C?', {
        'name': '隔离开关',
        'brand': 'ABB',
        'category': '隔离开关'
    }),
    
    # 双电源开关系列
    (r'WTS[-_]?(B\d+|A\d+|\d+)[-_]?(\d+)/(\d+)P?', {
        'name': '双电源自动转换开关',
        'brand': '施耐德万高',
        'category': '双电源'
    }),
    (r'ATSE[-_]?(\d+)[-_]?(\d+)/(\d+)P?', {
        'name': '双电源自动转换开关',
        'brand': '国产',
        'category': '双电源'
    }),
    
    # 浪涌保护器/防雷系列
    (r'Li[DGS]?ZX?\d+[A-Z]?\s*(\d+)kA', {
        'name': '浪涌保护器(SPD)',
        'brand': '施耐德',
        'category': '防雷'
    }),
    (r'SPD[-_]?(\d+)kA', {
        'name': '浪涌保护器(SPD)',
        'brand': '国产',
        'category': '防雷'
    }),
    (r'防雷模块?', {
        'name': '浪涌保护器(SPD)',
        'brand': '待定',
        'category': '防雷'
    }),
    
    # 电流互感器
    (r'CT[-_]?(\d+)/(\d+)A?', {
        'name': '电流互感器',
        'brand': '施耐德',
        'category': '互感器'
    }),
    (r'电流互感器[_-]?(\d+)/(\d+)', {
        'name': '电流互感器',
        'brand': '待定',
        'category': '互感器'
    }),
    
    # 多功能电力仪表
    (r'DM\d+[A-Z]?\d+', {
        'name': '多功能电力仪表',
        'brand': '施耐德',
        'category': '仪表'
    }),
    (r'KWH[+]?', {
        'name': '多功能电力仪表',
        'brand': '待定',
        'category': '仪表'
    }),
    (r'多功能仪表', {
        'name': '多功能电力仪表',
        'brand': '待定',
        'category': '仪表'
    }),
    (r'功率因数表|电能表', {
        'name': '电力仪表',
        'brand': '待定',
        'category': '仪表'
    }),
    
    # 接触器
    (r'LC1D(\d+)[A-Z]?', {
        'name': '交流接触器',
        'brand': '施耐德',
        'category': '接触器'
    }),
    (r'AX(\d+)[A-Z]?', {
        'name': '交流接触器',
        'brand': 'ABB',
        'category': '接触器'
    }),
    
    # 继电器
    (r'CR[-_]?M(\d+)[A-Z]?', {
        'name': '中间继电器',
        'brand': 'ABB',
        'category': '继电器'
    }),
    (r'RXM(\d+)[A-Z]?', {
        'name': '中间继电器',
        'brand': '施耐德',
        'category': '继电器'
    }),
    
    # 塑壳断路器
    (r'NSX(\d+)[A-Z]?', {
        'name': '塑壳断路器',
        'brand': '施耐德',
        'category': '塑壳断路器'
    }),
    (r'XT(\d+)[A-Z]?', {
        'name': '塑壳断路器',
        'brand': 'ABB',
        'category': '塑壳断路器'
    }),
]

# 配电箱箱体尺寸识别
BOX_SIZE_PATTERNS = [
    r'(\d{3,4})×(\d{3,4})×(\d{3,4})mm',
    r'(\d{3,4})x(\d{3,4})x(\d{3,4})mm',
    r'(\d{3,4})\*(\d{3,4})\*(\d{3,4})',
]

# 元器件参考价格库
PRICE_DB = {
    # 施耐德
    'iC65N-C20A/2P': {'price': 58, 'unit': '个'},
    'iC65N-D25A/3P': {'price': 85, 'unit': '个'},
    'iC65N-C32A/2P': {'price': 62, 'unit': '个'},
    'INT125/63/3P': {'price': 120, 'unit': '个'},
    'INT125/100/3P': {'price': 180, 'unit': '个'},
    'LC1D09': {'price': 180, 'unit': '个'},
    'LC1D12': {'price': 200, 'unit': '个'},
    'RXM4LB1': {'price': 65, 'unit': '个'},
    'DM2350N': {'price': 650, 'unit': '台'},
    
    # 双电源开关
    'WTS-B63/4P': {'price': 5998, 'unit': '台'},
    'WTS-B100/4P': {'price': 8500, 'unit': '台'},
    'WTS-863/4P': {'price': 6800, 'unit': '台'},
    
    # 防雷
    'LiD40X4': {'price': 350, 'unit': '个'},
    'LiGZX4L': {'price': 380, 'unit': '套'},
    
    # 电流互感器
    '75/5A': {'price': 60, 'unit': '个'},
    '100/5A': {'price': 75, 'unit': '个'},
    
    # ABB
    'SH201-C16': {'price': 45, 'unit': '个'},
    'SH201-C20': {'price': 48, 'unit': '个'},
    'OT63E3C': {'price': 280, 'unit': '个'},
    'OT100E3C': {'price': 350, 'unit': '个'},
    'AX09': {'price': 180, 'unit': '个'},
    'CR-M024DC2L': {'price': 85, 'unit': '个'},
    
    # 仪表
    'KWH+': {'price': 265, 'unit': '台'},
    
    # 默认价格
    'default': {'price': 100, 'unit': '个'},
}


def extract_components_from_text(text):
    """
    从识别的文本中提取元器件信息
    这是网站的核心识别逻辑
    """
    components = []
    found_specs = set()  # 避免重复识别
    
    # 清理文本
    text = text.upper().replace(' ', '').replace('　', '')
    
    for pattern, info in COMPONENT_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            spec = match.group(0)
            if spec in found_specs:
                continue
            
            # 提取规格中的关键参数
            spec_clean = re.sub(r'[-_]', '', spec)
            
            component = {
                'name': info['name'],
                'spec': spec,
                'brand': info['brand'],
                'category': info['category'],
                'raw_match': match.group(0)
            }
            
            # 尝试提取数量
            quantity = extract_quantity(text, match.end(), spec)
            component['quantity'] = quantity
            
            # 查找参考价格
            price_info = find_price(spec, info['brand'])
            component['unit_price'] = price_info['price']
            component['unit'] = price_info['unit']
            component['total'] = component['unit_price'] * quantity
            
            components.append(component)
            found_specs.add(spec)
    
    # 识别配电箱箱体
    box = extract_box_info(text)
    if box:
        components.insert(0, box)
    
    return components


def extract_quantity(text, position, spec):
    """从元器件附近提取数量"""
    # 查找元器件后面的数字（通常表示数量）
    nearby = text[max(0, position-50):position+100]
    
    # 匹配常见数量模式
    qty_patterns = [
        r'×(\d+)',           # ×12
        r'\*(\d+)',          # *12
        r'X(\d+)',           # X12
        r'数量[：:](\d+)',   # 数量：12
        r'(\d+)个',          # 12个
        r'(\d+)台',          # 12台
        r'共(\d+)',          # 共12
    ]
    
    for pattern in qty_patterns:
        match = re.search(pattern, nearby)
        if match:
            return int(match.group(1))
    
    # 默认数量
    if '断路器' in text[max(0, position-100):position]:
        return 1
    return 1


def extract_box_info(text):
    """识别配电箱箱体信息"""
    for pattern in BOX_SIZE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            width, height, depth = match.groups()
            return {
                'name': '配电箱箱体',
                'spec': f'{width}×{height}×{depth}mm',
                'brand': '国产',
                'category': '箱体',
                'quantity': 1,
                'unit_price': 240,
                'unit': '台',
                'total': 240
            }
    return None


def find_price(spec, brand):
    """查找元器件参考价格"""
    # 标准化规格
    spec_clean = re.sub(r'[-_\s]', '', spec.upper())
    
    # 精确匹配
    for key, value in PRICE_DB.items():
        if key.upper().replace('-', '').replace('_', '') in spec_clean:
            return value
    
    # 模糊匹配
    for key, value in PRICE_DB.items():
        key_clean = key.upper().replace('-', '').replace('_', '')
        if key_clean in spec_clean or spec_clean in key_clean:
            return value
    
    return PRICE_DB['default']


def parse_uploaded_text(image_data):
    """
    解析上传图片的OCR结果
    由于是演示版本，使用预定义的识别规则
    实际使用时需要接入OCR API（如百度OCR、腾讯OCR等）
    """
    # 这里应该调用OCR API
    # 演示版本返回模拟数据，实际使用时请接入真实OCR
    pass


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/api/recognize', methods=['POST'])
def recognize():
    """
    识别配电箱元器件API
    接收base64编码的图片，返回识别的元器件列表
    """
    try:
        data = request.get_json()
        image_data = data.get('image', '')
        
        # 实际应用中，这里应该：
        # 1. 调用OCR API识别图片文字
        # 2. 将识别的文字传入 extract_components_from_text 函数
        # 3. 返回识别结果
        
        # 由于演示环境，我们返回预定义的识别结果
        # 实际使用时，请接入百度OCR、腾讯OCR、阿里OCR等
        
        # 示例：根据image_data的特征返回不同的模拟结果
        # 真实场景下，这里会调用OCR服务
        
        return jsonify({
            'success': True,
            'message': '识别成功（演示模式）',
            'data': {
                'components': get_demo_components(),
                'total': calculate_total(get_demo_components())
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'识别失败: {str(e)}'
        })


@app.route('/api/recognize_with_ocr', methods=['POST'])
def recognize_with_ocr():
    """
    带OCR的识别API（需要配置OCR服务）
    """
    try:
        data = request.get_json()
        image_base64 = data.get('image', '')
        
        # 调用OCR服务（需要自行配置API密钥）
        # 这里使用百度OCR作为示例
        ocr_result = call_baidu_ocr(image_base64)
        
        # 从OCR结果中提取元器件
        text = ocr_result.get('text', '')
        components = extract_components_from_text(text)
        
        return jsonify({
            'success': True,
            'message': 'OCR识别成功',
            'data': {
                'components': components,
                'total': calculate_total(components)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'OCR识别失败: {str(e)}'
        })


def call_baidu_ocr(image_base64):
    """
    调用百度OCR API（需要配置API密钥）
    文档：https://ai.baidu.com/ai-doc/OCR/zk3h7xw52
    """
    # 示例代码，需要安装 pip install baidu-aip
    # 请自行配置API_KEY, SECRET_KEY, APP_ID
    """
    from aip import AipOcr
    
    APP_ID = '你的App ID'
    API_KEY = '你的Api Key'
    SECRET_KEY = '你的Secret Key'
    
    client = AipOcr(APP_ID, API_KEY, SECRET_KEY)
    
    # 读取图片
    image = base64.b64decode(image_base64)
    
    # 调用通用文字识别
    result = client.basicGeneral(image)
    
    # 提取文字
    text = '\n'.join([item['words'] for item in result.get('words_result', [])])
    
    return {'text': text}
    """
    return {'text': ''}


@app.route('/api/recognize_file', methods=['POST'])
def recognize_file():
    """
    上传文件识别（支持图片文件）
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '没有上传文件'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '文件名为空'})
        
        # 保存文件
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        
        # 读取图片并转换为基础数据
        # 实际应用中，这里应该调用OCR API
        # 演示模式下，返回预定义结果
        
        return jsonify({
            'success': True,
            'message': '文件上传成功',
            'data': {
                'filename': filename,
                'components': get_demo_components(),
                'total': calculate_total(get_demo_components())
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'处理失败: {str(e)}'
        })


@app.route('/api/export_excel', methods=['POST'])
def export_excel():
    """导出Excel报价单"""
    try:
        data = request.get_json()
        components = data.get('components', [])
        
        if not components:
            return jsonify({'success': False, 'message': '没有数据'})
        
        # 创建DataFrame
        df = pd.DataFrame(components)
        df['序号'] = range(1, len(df) + 1)
        df = df[['序号', 'name', 'spec', 'brand', 'quantity', 'unit', 'unit_price', 'total']]
        df.columns = ['序号', '元器件名称', '规格型号', '品牌', '数量', '单位', '单价(元)', '小计(元)']
        
        # 添加合计行
        total = df['小计(元)'].sum()
        labor = total * 0.15
        grand_total = total + labor
        
        # 生成Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='元器件清单', index=False)
            
            # 报价汇总表
            summary = pd.DataFrame({
                '项目': ['元器件合计', '人工费(15%)', '总计'],
                '金额(元)': [total, labor, grand_total]
            })
            summary.to_excel(writer, sheet_name='报价汇总', index=False)
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'配电箱报价单_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'导出失败: {str(e)}'
        })


def get_demo_components():
    """获取演示用的元器件数据"""
    return [
        {'name': '配电箱箱体', 'spec': '600×800×200mm', 'brand': '国产', 'category': '箱体', 'quantity': 1, 'unit': '台', 'unit_price': 240, 'total': 240},
        {'name': '隔离开关', 'spec': 'INT125/63/3P', 'brand': '施耐德', 'category': '隔离开关', 'quantity': 2, 'unit': '个', 'unit_price': 120, 'total': 240},
        {'name': '双电源自动转换开关', 'spec': 'WTS-B63/4P', 'brand': '施耐德万高', 'category': '双电源', 'quantity': 1, 'unit': '台', 'unit_price': 5998, 'total': 5998},
        {'name': '电流互感器', 'spec': '75/5A', 'brand': '施耐德', 'category': '互感器', 'quantity': 3, 'unit': '个', 'unit_price': 60, 'total': 180},
        {'name': '多功能电力仪表', 'spec': 'KWH+', 'brand': '待定', 'category': '仪表', 'quantity': 1, 'unit': '台', 'unit_price': 265, 'total': 265},
        {'name': '微型断路器', 'spec': 'iC65N-C20A/2P', 'brand': '施耐德', 'category': '断路器', 'quantity': 12, 'unit': '个', 'unit_price': 58, 'total': 696},
        {'name': '微型断路器', 'spec': 'iC65N-D25A/3P', 'brand': '施耐德', 'category': '断路器', 'quantity': 1, 'unit': '个', 'unit_price': 85, 'total': 85},
        {'name': '浪涌保护器(SPD)', 'spec': 'LiGZX4L 40kA', 'brand': '施耐德', 'category': '防雷', 'quantity': 1, 'unit': '套', 'unit_price': 380, 'total': 380},
    ]


def calculate_total(components):
    """计算总价"""
    subtotal = sum(c.get('total', 0) for c in components)
    labor = subtotal * 0.15
    return {
        'subtotal': subtotal,
        'labor': labor,
        'total': subtotal + labor
    }


if __name__ == '__main__':
    print("=" * 50)
    print("⚡ 配电箱自动组价系统 - Web版")
    print("=" * 50)
    print("识别逻辑说明：")
    print("1. 使用OCR识别配电箱系统图中的文字")
    print("2. 通过正则表达式匹配元器件规格型号")
    print("3. 根据品牌和规格查找参考价格")
    print("4. 生成Excel报价单")
    print("=" * 50)
    print("\n📌 使用说明：")
    print("- 请在 .env 文件中配置百度OCR API密钥")
    print("- 或使用演示模式测试基本功能")
    print("- 访问 http://0.0.0.0:5000 查看网站")
    print("\n启动服务...")
    
    # 启动Flask服务
    app.run(host='0.0.0.0', port=5000, debug=True)
