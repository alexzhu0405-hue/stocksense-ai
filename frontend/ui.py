"""Streamlit 前端界面。"""

import streamlit as st
import requests
from datetime import date

API = "http://localhost:8000"

st.set_page_config(page_title="StockSense AI", page_icon="📦", layout="wide")
st.title("📦 StockSense AI — 智能补货助手")


def api(method: str, path: str, **kwargs):
    resp = getattr(requests, method)(f"{API}{path}", **kwargs)
    resp.raise_for_status()
    return resp.json()


# ── 侧边栏：添加商品 ──────────────────────────────────────

with st.sidebar:
    st.header("➕ 添加商品")
    with st.form("add_product"):
        name = st.text_input("商品名称")
        unit = st.text_input("单位", value="件")
        stock = st.number_input("初始库存", min_value=0, value=0)
        price = st.number_input("当前价格", min_value=0.0, value=0.0, step=0.1)
        if st.form_submit_button("添加"):
            if name.strip():
                try:
                    api("post", "/products", json={
                        "name": name, "unit": unit, "stock": stock, "price": price,
                    })
                    st.success(f"已添加「{name}」")
                    st.rerun()
                except Exception as e:
                    st.error(f"添加失败：{e}")

# ── 主区域 ────────────────────────────────────────────────

products = api("get", "/products")

if not products:
    st.info("暂无商品，请在左侧添加。")
    st.stop()

# 商品选择
selected = st.selectbox(
    "选择商品",
    products,
    format_func=lambda p: f"{p['name']}（库存 {p['stock']} {p['unit']}，¥{p['price']}）",
)
pid = selected["id"]

tab1, tab2, tab3 = st.tabs(["📝 记录购买", "📊 库存预测", "💡 补货建议"])

# ── Tab 1: 记录购买 ────────────────────────────────────────

with tab1:
    st.subheader("记录一次购买")
    col1, col2 = st.columns(2)
    with col1:
        qty = st.number_input("购买数量", min_value=1, value=1, key="qty")
    with col2:
        pdate = st.date_input("购买日期", value=date.today(), key="pdate")

    if st.button("记录购买"):
        api("post", f"/products/{pid}/purchases", json={
            "quantity": qty, "purchased_at": str(pdate),
        })
        st.success(f"已记录购买 {qty} {selected['unit']}")
        st.rerun()

    st.divider()
    st.subheader("购买历史")
    history = api("get", f"/products/{pid}/purchases")
    if history:
        st.table([
            {"日期": h["purchased_at"], "数量": h["quantity"]}
            for h in reversed(history)
        ])
    else:
        st.caption("暂无购买记录")

    st.divider()
    st.subheader("更新信息")
    c1, c2 = st.columns(2)
    with c1:
        new_stock = st.number_input("修正库存", min_value=0, value=selected["stock"], key="ns")
        if st.button("更新库存"):
            api("patch", f"/products/{pid}/stock", json={"stock": new_stock})
            st.rerun()
    with c2:
        new_price = st.number_input("更新价格", min_value=0.0, value=selected["price"], step=0.1, key="np")
        if st.button("更新价格"):
            api("patch", f"/products/{pid}/price", json={"price": new_price})
            st.rerun()

# ── Tab 2: 库存预测 ────────────────────────────────────────

with tab2:
    st.subheader("库存剩余天数预测")
    pred = api("get", f"/products/{pid}/predict")

    if pred.get("days_remaining") is not None:
        col1, col2, col3 = st.columns(3)
        col1.metric("当前库存", f"{pred['stock']} {selected['unit']}")
        col2.metric("日均消耗", f"{pred['daily_consumption']} {selected['unit']}")
        col3.metric("预计可用天数", f"{pred['days_remaining']} 天")
        st.caption(f"平均购买周期：{pred['avg_cycle_days']} 天")
    else:
        st.warning(pred.get("message", "无法预测"))

# ── Tab 3: 补货建议 ────────────────────────────────────────

with tab3:
    st.subheader("智能补货建议")
    rec = api("get", f"/products/{pid}/recommend")

    level_colors = {
        "urgent": "🔴", "warning": "🟡", "ok": "🟢", "unknown": "⚪",
    }
    level = rec.get("level", "unknown")

    st.markdown(f"### {rec.get('advice', '暂无建议')}")

    if rec.get("days_remaining") is not None:
        col1, col2 = st.columns(2)
        col1.metric("剩余天数", f"{rec['days_remaining']} 天")
        col2.metric("当前价格", f"¥{rec['price']}")
