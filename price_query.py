"""
询价模块
在指定渠道查询元器件价格
"""

import requests
import time
import random
from config import PRICE_CHANNELS, COMPONENT_TYPE_MAPPING
import re


def query_price(component_name, spec, brand_preference="ABB + 施耐德"):
    """
    查询元器件价格
    
    Args:
        component_name: 元器件名称
        spec: 规格型号
        brand_preference: 品牌偏好
    
    Returns:
        dict: 包含价格、渠道、链接等信息
    """
    # 清理规格型号
    spec_clean = clean_spec(spec)
    
    # 按优先级查询各渠道
    for channel in PRICE_CHANNELS:
        try:
            price_info = query_from_channel(
                channel['name'],
                channel['search_url'],
                component_name,
                spec_clean,
                brand_preference
            )
            
            if price_info and price_info['price'] > 0:
                return price_info
                
        except Exception as e:
            print(f"查询 {channel['name']} 失败: {e}")
            continue
    
    # 所有渠道都失败，返回模拟价格
    return get_mock_price(component_name, spec_clean)


def query_from_channel(channel_name, search_url, component_name, spec, brand):
    """
    从指定渠道查询价格
    
    实际实现时需要:
    1. 构造搜索URL或发送搜索请求
    2. 解析返回的页面或JSON数据
    3. 提取价格信息
    """
    # 这里实现伪代码，实际需要根据各网站的反爬机制进行调整
    
    # 示例：ABB直通车搜索
    if channel_name == "ABB直通车":
        # 构造搜索URL
        # search_url_with_params = f"{search_url}?keyword={spec}"
        # response = requests.get(search_url_with_params, headers=headers)
        # price = extract_price(response.text)
        pass
    
    # 示例：天工直通车
    elif channel_name == "天工直通车":
        # 需要API或网页抓取
        pass
    
    # 示例：工控猫
    elif channel_name == "工控猫商城":
        # 需要API或网页抓取
        pass
    
    # 当前返回None，触发使用模拟价格
    return None


def clean_spec(spec):
    """清理规格型号，移除特殊字符"""
    if not spec:
        return ""
    # 移除空格、特殊符号
    spec = re.sub(r'[\s\-\_]', '', str(spec))
    return spec


def get_mock_price(component_name, spec):
    """
    获取模拟价格（当无法从真实渠道获取时使用）
    
    实际项目中应移除此函数，改为严格使用真实询价
    """
    # 基础价格表（模拟）
    base_prices = {
        "小型断路器": 50,
        "漏电保护断路器": 180,
        "交流接触器": 220,
        "中间继电器": 85,
        "热过载继电器": 150,
        "塑壳断路器": 800,
        "隔离开关": 350,
        "指示灯/按钮": 45
    }
    
    # 根据规格中的数字调整价格
    multiplier = 1.0
    spec_str = str(spec).upper()
    
    # 电流规格
    current_match = re.search(r'C?(\d+)', spec_str)
    if current_match:
        current = int(current_match.group(1))
        if current > 63:
            multiplier = 1.5
        if current > 160:
            multiplier = 3.0
    
    # 极数
    if '4P' in spec_str:
        multiplier *= 1.5
    elif '3P' in spec_str:
        multiplier *= 1.3
    elif '2P' in spec_str:
        multiplier *= 1.1
    
    # 获取基础价格
    base = base_prices.get(component_name, 100)
    final_price = base * multiplier
    
    # 添加随机波动 (±10%)
    final_price *= random.uniform(0.9, 1.1)
    final_price = round(final_price, 2)
    
    return {
        "price": final_price,
        "channel": "参考价格（请以实际询价为准）",
        "url": "https://mall.abb.com.cn",
        "note": "建议在ABB直通车或天工直通车核实价格"
    }


def extract_price_from_abb(response_text):
    """从ABB直通车页面提取价格"""
    # 需要根据实际页面结构实现
    pass


def extract_price_from_tiangong(response_text):
    """从天工直通车页面提取价格"""
    # 需要根据实际页面结构实现
    pass


def extract_price_from_gongkongmao(response_text):
    """从工控猫商城页面提取价格"""
    # 需要根据实际页面结构实现
    pass


# 常用元器件型号参考价格（用于快速查询）
REFERENCE_PRICES = {
    # ABB小型断路器
    "SH201-C10": 35.00,
    "SH201-C16": 42.00,
    "SH201-C20": 48.00,
    "SH201-C25": 52.00,
    "SH201-C32": 58.00,
    "SH201-C40": 65.00,
    "SH201-C50": 75.00,
    "SH201-C63": 88.00,
    
    # ABB漏电保护断路器
    "GSH201 AC-C20/0.03": 180.00,
    "GSH201 AC-C25/0.03": 195.00,
    "GSH201 AC-C32/0.03": 210.00,
    "GSH202 AC-C40/0.03": 280.00,
    "GSH202 AC-C63/0.03": 320.00,
    
    # ABB交流接触器
    "AX09-30-10-80": 180.00,
    "AX12-30-10-80": 210.00,
    "AX18-30-10-80": 245.00,
    "AX25-30-10-80": 290.00,
    "AX32-30-10-80": 340.00,
    
    # ABB中间继电器
    "CR-M024DC2L": 85.00,
    "CR-M024AC2L": 82.00,
    "CR-P024DC2L": 65.00,
    
    # ABB热过载继电器
    "TA25DU-19M": 180.00,
    "TA25DU-25M": 210.00,
    "TA25DU-32M": 240.00,
    "TA45DU-63M": 350.00,
    
    # 施耐德小型断路器
    "iC65N C10": 42.00,
    "iC65N C16": 48.00,
    "iC65N C20": 55.00,
    "iC65N C25": 62.00,
    "iC65N C32": 70.00,
    "iC65N C40": 80.00,
    "iC65N C50": 92.00,
    "iC65N C63": 108.00,
    
    # 施耐德交流接触器
    "LC1D09M7": 165.00,
    "LC1D12M7": 190.00,
    "LC1D18M7": 225.00,
    "LC1D25M7": 265.00,
    "LC1D32M7": 310.00,
}
