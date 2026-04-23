"""
配电箱自动组价系统 - 主程序
功能：上传配电箱系统图，自动提取元器件，询价并生成Excel报价
"""

import streamlit as st
import pandas as pd
from PIL import Image
import io
import os
import sys
from datetime import datetime

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入模块
from config import PRICE_CHANNELS, BRAND_PREFERENCE
from price_query import query_price
from excel_generator import generate_excel

# 页面配置
st.set_page_config(
    page_title="配电箱自动组价系统",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1e88e5;
        text-align: center;
        padding: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .upload-box {
        border: 2px dashed #1e88e5;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background: #f5f9ff;
    }
    .result-box {
        background: #e8f5e9;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .price-highlight {
        background: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """初始化会话状态"""
    if 'extracted_data' not in st.session_state:
        st.session_state.extracted_data = []
    if 'prices_queried' not in st.session_state:
        st.session_state.prices_queried = False
    if 'final_quote' not in st.session_state:
        st.session_state.final_quote = None


def main():
    # 标题
    st.markdown('<p class="main-header">⚡ 配电箱自动组价系统</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">上传配电箱系统图，自动提取元器件并生成报价单</p>', unsafe_allow_html=True)
    
    init_session_state()
    
    # 主界面 - 左右布局
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📤 上传配电箱系统图")
        
        # 图片上传
        uploaded_files = st.file_uploader(
            "支持 PNG/JPG/BMP 格式，建议每张图包含4-6个配电箱",
            type=['png', 'jpg', 'jpeg', 'bmp'],
            accept_multiple_files=True,
            help="上传配电箱系统图截图，每张图片应包含清晰的配电箱系统图，边界完整无重叠"
        )
        
        if uploaded_files:
            st.success(f"✅ 已上传 {len(uploaded_files)} 张图片")
            
            # 预览图片
            st.subheader("📷 图片预览")
            cols = st.columns(min(len(uploaded_files), 3))
            for idx, file in enumerate(uploaded_files):
                with cols[idx % 3]:
                    st.image(file, caption=f"图片 {idx+1}: {file.name}", use_container_width=True)
        
        # 品牌选择
        st.subheader("🏭 品牌偏好")
        brand_options = ["ABB + 施耐德", "ABB", "施耐德", "优先ABB"]
        selected_brand = st.selectbox("选择元器件品牌", brand_options)
        
        # 询价渠道说明
        st.subheader("🔗 询价渠道")
        st.info("""
        **询价优先级：**
        1. ABB直通车 (mall.abb.com.cn)
        2. 天工直通车 (titanmatrix.com)  
        3. 工控猫商城 (gkmao.com)
        """)
        
        # 开始识别按钮
        st.subheader("🚀 开始处理")
        if st.button("🔍 识别元器件并询价", type="primary", disabled=not uploaded_files):
            if uploaded_files:
                process_images(uploaded_files, selected_brand)
    
    with col2:
        if st.session_state.extracted_data:
            display_results()
        else:
            st.info("👈 请先上传图片并点击识别按钮")


def process_images(files, brand):
    """处理上传的图片"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    all_components = []
    
    for idx, file in enumerate(files):
        status_text.text(f"正在识别第 {idx+1}/{len(files)} 张图片...")
        progress_bar.progress((idx + 0.5) / len(files))
        
        # 读取图片
        image = Image.open(file)
        
        # 模拟元器件提取（实际会调用AI识别）
        # 这里先展示数据结构，实际使用时接入AI识别API
        components = extract_components_from_image(image, file.name)
        all_components.extend(components)
        
        progress_bar.progress((idx + 1) / len(files))
    
    status_text.text("元器件识别完成，正在询价...")
    
    # 询价
    for comp in all_components:
        price_info = query_price(comp['name'], comp['spec'], brand)
        comp['price'] = price_info['price']
        comp['channel'] = price_info['channel']
        comp['url'] = price_info['url']
        comp['total'] = comp['price'] * comp.get('quantity', 1)
    
    st.session_state.extracted_data = all_components
    
    status_text.text("✅ 处理完成！")
    st.success(f"识别到 {len(all_components)} 个元器件，请在右侧查看结果")


def extract_components_from_image(image, filename):
    """
    从图片中提取元器件信息
    实际实现时需要调用AI视觉识别API
    """
    # 模拟数据 - 实际使用时替换为AI识别
    # 这里返回的结构供参考
    mock_components = [
        {
            'box_name': 'CJL-1800',
            'box_size': '1800×600×400mm',
            'component_name': '小型断路器',
            'spec': 'SH201-C16',
            'brand': 'ABB',
            'quantity': 2,
            'unit': '个',
            'image_file': filename
        },
        {
            'box_name': 'CJL-A&L-1',
            'box_size': '800×400×200mm',
            'component_name': '中间继电器',
            'spec': 'CR-M024DC2L',
            'brand': 'ABB',
            'quantity': 4,
            'unit': '个',
            'image_file': filename
        }
    ]
    return mock_components


def display_results():
    """展示识别和询价结果"""
    st.header("📊 识别结果")
    
    data = st.session_state.extracted_data
    
    if not data:
        st.warning("暂无数据")
        return
    
    # 按配电箱分组展示
    boxes = {}
    for item in data:
        box_name = item['box_name']
        if box_name not in boxes:
            boxes[box_name] = {
                'size': item['box_size'],
                'components': []
            }
        boxes[box_name]['components'].append(item)
    
    # 显示每个配电箱的详情
    for box_name, box_info in boxes.items():
        with st.expander(f"📦 {box_name} ({box_info['size']})", expanded=True):
            df = pd.DataFrame(box_info['components'])
            display_cols = ['component_name', 'spec', 'brand', 'quantity', 'unit', 'price', 'total']
            df = df[[col for col in display_cols if col in df.columns]]
            df.columns = ['元器件名称', '规格型号', '品牌', '数量', '单位', '单价(元)', '小计(元)']
            
            # 添加链接列
            st.dataframe(df, hide_index=True, use_container_width=True)
            
            # 计算配电箱总价
            box_total = sum(c['total'] for c in box_info['components'])
            st.metric(f"配电箱总价", f"¥ {box_total:,.2f}")
    
    # 整体汇总
    st.divider()
    st.header("💰 整体报价汇总")
    
    # 计算总价
    total_amount = sum(item['total'] for item in data)
    component_count = len(data)
    box_count = len(boxes)
    
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("配电箱数量", f"{box_count} 个")
    metric_col2.metric("元器件总数", f"{component_count} 个")
    metric_col3.metric("报价总计", f"¥ {total_amount:,.2f}")
    
    # 询价来源统计
    st.subheader("📍 询价来源统计")
    channels = {}
    for item in data:
        ch = item.get('channel', '未知')
        channels[ch] = channels.get(ch, 0) + 1
    
    for ch, count in channels.items():
        st.write(f"- **{ch}**: {count} 个元器件")
    
    # 生成Excel按钮
    st.divider()
    if st.button("📥 下载Excel报价单", type="primary", use_container_width=True):
        with st.spinner("正在生成Excel..."):
            excel_path = generate_excel(data, boxes)
            
            if excel_path and os.path.exists(excel_path):
                with open(excel_path, "rb") as f:
                    st.download_button(
                        label="⬇️ 点击下载 Excel文件",
                        data=f,
                        file_name=os.path.basename(excel_path),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        use_container_width=True
                    )
                st.success("✅ Excel报价单已生成！")
            else:
                st.error("生成Excel时出错，请重试")


if __name__ == "__main__":
    main()
