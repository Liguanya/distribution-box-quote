"""
配置文件
包含询价渠道、品牌偏好等配置
"""

# 询价渠道（按优先级排序）
PRICE_CHANNELS = [
    {
        "name": "ABB直通车",
        "url": "https://mall.abb.com.cn",
        "search_url": "https://mall.abb.com.cn/search",
        "priority": 1,
        "description": "ABB官方商城，原厂直供"
    },
    {
        "name": "天工直通车",
        "url": "https://www.titanmatrix.com",
        "search_url": "https://www.titanmatrix.com/search",
        "priority": 2,
        "description": "专业电气选型询价平台"
    },
    {
        "name": "工控猫商城",
        "url": "https://www.gkmao.com",
        "search_url": "https://www.gkmao.com/product/search",
        "priority": 3,
        "description": "施耐德官方授权合作伙伴"
    }
]

# 品牌偏好
BRAND_PREFERENCE = {
    "ABB + 施耐德": ["ABB", "Schneider"],
    "ABB": ["ABB"],
    "施耐德": ["Schneider"],
    "优先ABB": ["ABB", "Schneider"]
}

# 常见的ABB和施耐德元器件类型映射
COMPONENT_TYPE_MAPPING = {
    # 小型断路器
    "小型断路器": {
        "ABB": ["SH200", "GSH200", "S200"],
        "Schneider": ["iC65", "iDPN", "EA9"]
    },
    # 漏电保护断路器
    "漏电保护断路器": {
        "ABB": ["SH200L", "GSH201", "GSH202"],
        "Schneider": ["iC65N", "Vigi", "EA9R"]
    },
    # 交流接触器
    "交流接触器": {
        "ABB": ["AX", "AF", "A"],
        "Schneider": ["LC1D", "TeSys D", "TeSys K"]
    },
    # 中间继电器
    "中间继电器": {
        "ABB": ["CR-M", "CR-P", "DNX"],
        "Schneider": ["RXM", "LC2", "CAD"]
    },
    # 热过载继电器
    "热过载继电器": {
        "ABB": ["TA", "TF", "E90"],
        "Schneider": ["LRD", "LR3", "TeSys"]
    },
    # 塑壳断路器
    "塑壳断路器": {
        "ABB": ["XT", "Formula", "Tmax"],
        "Schneider": ["NSX", "EZD", "MVS"]
    },
    # 隔离开关
    "隔离开关": {
        "ABB": ["OT", "E90", "S800"],
        "Schneider": ["K", "INT", "INS"]
    },
    # 指示灯/按钮
    "指示灯/按钮": {
        "ABB": ["LD", "CP", "KA"],
        "Schneider": ["XB7", "XB5", "Harmony"]
    }
}

# 元器件默认数量（用于模拟询价）
DEFAULT_QUANTITIES = {
    "小型断路器": 2,
    "漏电保护断路器": 1,
    "交流接触器": 1,
    "中间继电器": 4,
    "热过载继电器": 1,
    "塑壳断路器": 1,
    "隔离开关": 1,
    "指示灯/按钮": 3
}

# Excel导出配置
EXCEL_CONFIG = {
    "sheet_name": "配电箱报价单",
    "date_format": "%Y-%m-%d",
    "currency": "¥"
}
