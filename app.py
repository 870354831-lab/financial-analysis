"""
Streamlit 财务分析交互式网页应用 (AkShare 免费版)
"""

import streamlit as st
import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from datetime import datetime
import io
import warnings

warnings.filterwarnings('ignore')

# 设置matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def get_color_scale_row(value, row_min, row_max):
    """红黄绿色阶"""
    if pd.isna(value):
        return '#FFFFFF'
    
    if row_max == row_min:
        return '#FFFF00'
    
    normalized = (value - row_min) / (row_max - row_min)
    normalized = max(0, min(1, normalized))
    
    if normalized < 0.5:
        ratio = normalized * 2
        r = int(99 + (255 - 99) * ratio)
        g = int(190 + (235 - 190) * ratio)
        b = int(123 + (132 - 123) * ratio)
    else:
        ratio = (normalized - 0.5) * 2
        r = int(255 + (248 - 255) * ratio)
        g = int(235 + (105 - 235) * ratio)
        b = int(132 + (107 - 132) * ratio)
    
    return f'#{r:02x}{g:02x}{b:02x}'


def create_heatmap_table_buf(df, title):
    """创建核心财务指标表格图"""
    if df.empty:
        return None
    
    fig_height = max(10, len(df) * 0.7)
    fig_width = max(16, len(df.columns) * 2.2)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    is_yoy_row = lambda name: '同比' in str(name)
    is_margin_row = lambda name: any(x in str(name) for x in ['毛利率', '净利率'])
    
    cell_text = []
    
    for idx, row in df.iterrows():
        row_text = [str(idx)]
        for val in row.values:
            if pd.isna(val):
                row_text.append('-')
            else:
                if is_yoy_row(idx):
                    if val > 0:
                        row_text.append(f"+{val:.1f}%")
                    else:
                        row_text.append(f"{val:.1f}%")
                elif abs(val) >= 10000:
                    row_text.append(f"{val/10000:.2f}万")
                elif abs(val) >= 100:
                    row_text.append(f"{val:.1f}")
                elif abs(val) >= 1:
                    row_text.append(f"{val:.2f}")
                else:
                    row_text.append(f"{val:.4f}")
        cell_text.append(row_text)
    
    col_labels = ['指标'] + list(df.columns)
    n_rows = len(cell_text)
    n_cols = len(col_labels)
    cell_width = 0.95 / n_cols
    cell_height = 0.92 / (n_rows + 1)
    
    # 表头
    for j, label in enumerate(col_labels):
        x = 0.025 + j * cell_width + cell_width / 2
        y = 0.96 - cell_height / 2
        
        rect = patches.FancyBboxPatch(
            (0.025 + j * cell_width, 0.96 - cell_height),
            cell_width * 0.98, cell_height * 0.95,
            boxstyle="square,pad=0",
            facecolor='#4472C4', edgecolor='black', linewidth=0.8,
            transform=ax.transAxes
        )
        ax.add_patch(rect)
        
        ax.text(x, y, label, ha='center', va='center',
                fontsize=14, fontweight='bold', color='white',
                transform=ax.transAxes)
    
    # 数据单元格
    for i, row_text in enumerate(cell_text):
        row_name = df.index[i]
        is_yoy = is_yoy_row(row_name)
        is_margin = is_margin_row(row_name)
        
        row_values = df.iloc[i].values
        row_min = np.nanmin(row_values) if len(row_values) > 0 else 0
        row_max = np.nanmax(row_values) if len(row_values) > 0 else 1
        row_abs_max = np.nanmax(np.abs(row_values)) if len(row_values) > 0 else 1
        
        for j, text in enumerate(row_text):
            x = 0.025 + j * cell_width + cell_width / 2
            y = 0.96 - (i + 1.5) * cell_height
            
            if j == 0:
                bg_color = '#D9E1F2'
                font_weight = 'bold'
                font_size = 12
                text_color = 'black'
            else:
                actual_value = df.iloc[i, j-1]
                font_weight = 'normal'
                font_size = 11
                
                if is_yoy:
                    bg_color = '#FFFFFF'
                    text_color = 'black'
                elif is_margin:
                    bg_color = get_color_scale_row(actual_value, row_min, row_max)
                    normalized = (actual_value - row_min) / (row_max - row_min) if row_max != row_min else 0.5
                    text_color = 'white' if normalized > 0.7 else 'black'
                else:
                    bg_color = '#FFFFFF'
                    text_color = 'black'
            
            rect = patches.FancyBboxPatch(
                (0.025 + j * cell_width, 0.96 - (i + 2) * cell_height),
                cell_width * 0.98, cell_height * 0.95,
                boxstyle="square,pad=0",
                facecolor=bg_color, edgecolor='black', linewidth=0.5,
                transform=ax.transAxes
            )
            ax.add_patch(rect)
            
            # 同比行绘制数据条
            if is_yoy and j > 0 and not pd.isna(df.iloc[i, j-1]):
                bar_max_width = cell_width * 0.8
                value = df.iloc[i, j-1]
                bar_ratio = min(abs(value) / (row_abs_max * 1.1), 1.0) if row_abs_max > 0 else 0
                bar_width = bar_max_width * bar_ratio
                
                bar_color = '#5B9BD5' if value >= 0 else '#FF6B6B'
                
                if bar_width > 0.001:
                    bar_rect = patches.FancyBboxPatch(
                        (0.025 + j * cell_width + 0.015, 0.96 - (i + 1.85) * cell_height),
                        bar_width, cell_height * 0.55,
                        boxstyle="square,pad=0",
                        facecolor=bar_color, edgecolor='none', alpha=0.7,
                        transform=ax.transAxes
                    )
                    ax.add_patch(bar_rect)
            
            ax.text(x, y, text, ha='center', va='center',
                   fontsize=font_size, fontweight=font_weight, color=text_color,
                   transform=ax.transAxes)
    
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20, y=0.99)
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close()
    
    return buf


def safe_float(value):
    """安全转换为float"""
    if pd.isna(value) or value is None:
        return 0
    try:
        return float(value)
    except:
        return 0


def normalize_stock_code(code):
    """标准化股票代码，添加交易所前缀"""
    code = str(code).strip()
    # 移除可能的后缀
    if '.' in code:
        code = code.split('.')[0]
    
    # 根据代码规则判断交易所
    if code.startswith('6'):
        return f"sh{code}"  # 上海证券交易所
    elif code.startswith(('0', '3', '2')):
        return f"sz{code}"  # 深圳证券交易所
    elif code.startswith('8') or code.startswith('4'):
        return f"bj{code}"  # 北京证券交易所
    else:
        return f"sh{code}"  # 默认上海


def get_financial_indicators(ticker, start_year=2016, end_year=2024):
    """使用AkShare获取核心财务指标"""
    code = ticker.split('.')[0] if '.' in ticker else ticker
    code_with_prefix = normalize_stock_code(code)
    
    result_data = {}
    
    # 尝试多个数据源
    # 方法1: 使用业绩报表接口
    try:
        for year in range(end_year, start_year - 1, -1):
            try:
                df_yjbb = ak.stock_yjbb_em(date=f"{year}1231")
                
                # 打印列名用于调试（仅在出错时显示）
                if st.session_state.get('debug_mode', False):
                    st.write(f"{year}年列名:", df_yjbb.columns.tolist())
                
                df_stock = df_yjbb[df_yjbb['股票代码'] == code]
                
                if df_stock.empty:
                    continue
                
                row = df_stock.iloc[0]
                year_str = f"{year}年报"
                
                # 尝试不同的列名格式
                revenue = row.get('营业收入', row.get('营业总收入', row.get('营业总收入-营业总收入', 0)))
                profit = row.get('净利润', row.get('归属净利润', row.get('净利润-净利润', 0)))
                roe = row.get('净资产收益率', row.get('ROE', row.get('加权平均净资产收益率', 0)))
                margin = row.get('毛利率', row.get('销售毛利率', 0))
                revenue_yoy = row.get('营业收入同比增长', row.get('营业总收入同比增长', row.get('营业总收入-同比增长', 0)))
                profit_yoy = row.get('净利润同比增长', row.get('归属净利润同比增长', row.get('净利润-同比增长', 0)))
                
                year_data = {
                    '营业总收入(亿元)': safe_float(revenue) / 1e8,
                    '营业总收入同比(%)': safe_float(revenue_yoy),
                    '归属母公司所有者净利润(亿元)': safe_float(profit) / 1e8,
                    '归属母公司所有者净利润同比(%)': safe_float(profit_yoy),
                    '净资产收益率ROE(%)': safe_float(roe),
                    '销售毛利率(%)': safe_float(margin),
                    '销售净利率(%)': None,
                    '总资产周转率(次)': None,
                    '销售费用/营业总收入(%)': None,
                    '管理费用/营业总收入(%)': None,
                    '财务费用/营业总收入(%)': None,
                    '研发费用(亿元)': None,
                }
                
                # 获取详细财务报表数据
                try:
                    df_profit = ak.stock_financial_report_sina(stock=code_with_prefix, symbol="利润表")
                    if not df_profit.empty and '报告日' in df_profit.columns:
                        df_profit['报告日'] = pd.to_datetime(df_profit['报告日'])
                        year_profit = df_profit[df_profit['报告日'].dt.year == year]
                        
                        if not year_profit.empty:
                            p_row = year_profit.iloc[0]
                            
                            revenue_val = safe_float(revenue)
                            if revenue_val > 0:
                                profit_val = safe_float(profit)
                                year_data['销售净利率(%)'] = (profit_val / revenue_val) * 100
                            
                            sales_exp = safe_float(p_row.get('销售费用', p_row.get('营业费用', 0)))
                            admin_exp = safe_float(p_row.get('管理费用', 0))
                            fina_exp = safe_float(p_row.get('财务费用', 0))
                            rd_exp = safe_float(p_row.get('研发费用', p_row.get('研究开发费', 0)))
                            
                            if revenue_val > 0:
                                year_data['销售费用/营业总收入(%)'] = (sales_exp / revenue_val) * 100
                                year_data['管理费用/营业总收入(%)'] = (admin_exp / revenue_val) * 100
                                year_data['财务费用/营业总收入(%)'] = (fina_exp / revenue_val) * 100
                            
                            if rd_exp > 0:
                                year_data['研发费用(亿元)'] = rd_exp / 1e8
                except Exception as e:
                    if st.session_state.get('debug_mode', False):
                        st.warning(f"利润表获取失败: {e}")
                
                # 获取资产负债表数据
                try:
                    df_balance = ak.stock_financial_report_sina(stock=code_with_prefix, symbol="资产负债表")
                    if not df_balance.empty and '报告日' in df_balance.columns:
                        df_balance['报告日'] = pd.to_datetime(df_balance['报告日'])
                        year_balance = df_balance[df_balance['报告日'].dt.year == year]
                        
                        if not year_balance.empty:
                            b_row = year_balance.iloc[0]
                            
                            total_assets = safe_float(b_row.get('资产总计', b_row.get('总资产', 0)))
                            revenue_val = safe_float(revenue)
                            if total_assets > 0 and revenue_val > 0:
                                year_data['总资产周转率(次)'] = revenue_val / total_assets
                except Exception as e:
                    if st.session_state.get('debug_mode', False):
                        st.warning(f"资产负债表获取失败: {e}")
                
                result_data[year_str] = year_data
                
            except Exception as e:
                if st.session_state.get('debug_mode', False):
                    st.warning(f"{year}年数据获取失败: {e}")
                continue
        
        if result_data:
            result_df = pd.DataFrame(result_data)
            return result_df
            
    except Exception as e:
        st.error(f"数据获取出错: {e}")
    
    return pd.DataFrame()


# ==================== Streamlit 页面 ====================

def main():
    # 初始化session state
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False
    
    st.set_page_config(
        page_title="股票财务分析系统",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 股票财务分析系统")
    st.markdown("基于 AkShare 的免费财务数据可视化工具")
    
    # 侧边栏
    with st.sidebar:
        st.header("🔍 参数设置")
        
        ticker = st.text_input(
            "股票代码",
            value="600519",
            help="请输入A股股票代码，如：600519（贵州茅台）、689009（九号公司）、300750（宁德时代）"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            start_year = st.number_input("起始年份", min_value=2010, max_value=2024, value=2016)
        with col2:
            end_year = st.number_input("结束年份", min_value=2010, max_value=2024, value=2024)
        
        st.markdown("---")
        
        generate_btn = st.button(
            "🚀 开始生成",
            type="primary",
            use_container_width=True
        )
        
        st.markdown("---")
        
        # 调试模式开关
        with st.expander("🔧 高级选项"):
            st.session_state.debug_mode = st.checkbox("开启调试模式", value=False, 
                                                       help="开启后会显示详细错误信息")
        
        st.markdown("### 📌 使用说明")
        st.markdown("""
        1. 输入A股股票代码（无需后缀）
        2. 选择分析年份范围
        3. 点击按钮生成分析
        4. 查看财务分析图表
        
        **示例股票代码：**
        - 600519 - 贵州茅台
        - 689009 - 九号公司
        - 300750 - 宁德时代
        """)
    
    # 主页面内容
    if generate_btn:
        if not ticker:
            st.error("⚠️ 请输入股票代码！")
            return
        
        # 显示进度
        progress_placeholder = st.empty()
        with progress_placeholder.container():
            st.info("🔄 正在获取数据并生成分析图表，请稍候...")
            progress_bar = st.progress(0)
        
        try:
            # 清理股票代码
            code = ticker.split('.')[0] if '.' in ticker else ticker
            
            # 获取财务数据
            progress_bar.progress(30)
            df_indicators = get_financial_indicators(code, start_year, end_year)
            
            if df_indicators.empty:
                progress_placeholder.empty()
                st.error(f"❌ 未找到股票 {code} 的财务数据")
                
                st.info("""
                **可能的原因和解决方案：**
                
                1. **股票代码错误** - 请确认输入的是正确的A股代码（如：600519、000001）
                
                2. **网络问题** - AkShare需要访问国内财经网站，如果部署在海外服务器可能被限制
                
                3. **数据源问题** - 某些股票可能没有完整的财务数据
                
                **建议：**
                - 尝试在本地运行此应用
                - 或者使用其他数据源（如Tushare、AKShare的替代接口）
                """)
                
                # 调试模式下显示更多技术信息
                if st.session_state.get('debug_mode', False):
                    st.warning("调试模式：尝试显示可用的股票列名...")
                    try:
                        test_df = ak.stock_yjbb_em(date="20231231")
                        st.write("数据源列名:", test_df.columns.tolist()[:10])
                        st.write("示例数据行:", test_df.head(1).to_dict())
                    except Exception as debug_e:
                        st.error(f"调试信息获取失败: {debug_e}")
                
                return
            
            progress_bar.progress(80)
            
            # 生成财务指标图
            st.subheader("📋 核心财务指标")
            indicator_buf = create_heatmap_table_buf(
                df_indicators, 
                f"{code} 核心财务指标 ({start_year}-{end_year})"
            )
            if indicator_buf:
                st.image(indicator_buf, use_container_width=True)
            else:
                st.warning("无法生成财务指标图")
            
            progress_bar.progress(100)
            progress_placeholder.empty()
            
            # 显示数据表格（可展开）
            with st.expander("📈 查看原始数据"):
                st.dataframe(df_indicators.T, use_container_width=True)
            
            st.success(f"✅ {code} 财务分析图表生成完成！")
            
        except Exception as e:
            progress_placeholder.empty()
            st.error(f"❌ 生成图表时出错：{str(e)}")
    else:
        # 初始状态显示提示
        st.info("👈 请在左侧输入股票代码并点击生成按钮")
        
        # 显示示例说明
        st.markdown("### 📋 功能说明")
        st.markdown("""
        本应用使用 **AkShare** 开源财经数据接口，生成专业财务分析图表：
        
        **核心财务指标包括：**
        - 营业总收入及同比变化
        - 归属母公司净利润及同比变化
        - ROE（净资产收益率）
        - 销售毛利率、销售净利率
        - 各项费用率分析
        - 研发费用
        
        **无需 Wind 终端，完全免费！**
        """)


if __name__ == "__main__":
    main()
