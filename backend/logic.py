"""预测与补货建议的核心逻辑（规则版）。"""

from datetime import datetime, timedelta

from backend import db


def avg_purchase_cycle(product_id: int) -> float | None:
    """计算平均购买周期（天）。至少需要 2 条记录。"""
    purchases = db.get_purchases(product_id)
    if len(purchases) < 2:
        return None
    dates = sorted(datetime.strptime(p["purchased_at"], "%Y-%m-%d") for p in purchases)
    gaps = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
    return sum(gaps) / len(gaps)


def avg_purchase_quantity(product_id: int) -> float:
    """计算平均每次购买数量。"""
    purchases = db.get_purchases(product_id)
    if not purchases:
        return 0
    return sum(p["quantity"] for p in purchases) / len(purchases)


def predict_days_remaining(product_id: int) -> dict:
    """
    预测库存还能撑多少天。

    逻辑：日均消耗 = 平均购买数量 / 平均购买周期
          剩余天数 = 当前库存 / 日均消耗
    """
    products = {p["id"]: p for p in db.list_products()}
    product = products.get(product_id)
    if product is None:
        return {"error": "商品不存在"}

    cycle = avg_purchase_cycle(product_id)
    avg_qty = avg_purchase_quantity(product_id)

    if cycle is None or cycle == 0 or avg_qty == 0:
        return {
            "product": product["name"],
            "stock": product["stock"],
            "days_remaining": None,
            "message": "历史数据不足，无法预测",
        }

    daily_consumption = avg_qty / cycle
    days = product["stock"] / daily_consumption

    return {
        "product": product["name"],
        "stock": product["stock"],
        "avg_cycle_days": round(cycle, 1),
        "daily_consumption": round(daily_consumption, 2),
        "days_remaining": round(days, 1),
    }


def recommend(product_id: int) -> dict:
    """
    基于规则的补货建议。

    规则：
      - 剩余天数 < 3 天  → 🔴 立即购买
      - 剩余天数 < 7 天  → 🟡 建议近期购买
      - 剩余天数 >= 7 天 → 🟢 库存充足
      - 价格低于历史均价  → 额外提示"当前价格较低，适合囤货"
    """
    pred = predict_days_remaining(product_id)
    if "error" in pred:
        return pred

    days = pred.get("days_remaining")
    product = [p for p in db.list_products() if p["id"] == product_id][0]
    price = product["price"]

    result = {**pred, "price": price}

    if days is None:
        result["advice"] = "⚪ 数据不足，请多记录几次购买"
        result["level"] = "unknown"
        return result

    if days < 3:
        result["advice"] = "🔴 立即购买！库存即将耗尽"
        result["level"] = "urgent"
    elif days < 7:
        result["advice"] = "🟡 建议近期购买，库存偏低"
        result["level"] = "warning"
    else:
        result["advice"] = "🟢 库存充足，暂不需要补货"
        result["level"] = "ok"

    return result
