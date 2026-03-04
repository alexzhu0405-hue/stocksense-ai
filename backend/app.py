"""FastAPI 后端入口。"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend import db, logic


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="StockSense AI", version="0.1.0", lifespan=lifespan)


# ── Schemas ───────────────────────────────────────────────

class ProductIn(BaseModel):
    name: str
    unit: str = "件"
    stock: int = 0
    price: float = 0


class StockUpdate(BaseModel):
    stock: int


class PriceUpdate(BaseModel):
    price: float


class PurchaseIn(BaseModel):
    quantity: int = 1
    purchased_at: str | None = None


# ── Products ──────────────────────────────────────────────

@app.get("/products")
def list_products():
    return db.list_products()


@app.post("/products", status_code=201)
def create_product(body: ProductIn):
    try:
        pid = db.add_product(body.name, body.unit, body.stock, body.price)
    except Exception:
        raise HTTPException(400, "商品名已存在")
    return {"id": pid}


@app.patch("/products/{pid}/stock")
def update_stock(pid: int, body: StockUpdate):
    db.update_stock(pid, body.stock)
    return {"ok": True}


@app.patch("/products/{pid}/price")
def update_price(pid: int, body: PriceUpdate):
    db.update_price(pid, body.price)
    return {"ok": True}


# ── Purchases ─────────────────────────────────────────────

@app.post("/products/{pid}/purchases", status_code=201)
def add_purchase(pid: int, body: PurchaseIn):
    db.add_purchase(pid, body.quantity, body.purchased_at)
    return {"ok": True}


@app.get("/products/{pid}/purchases")
def get_purchases(pid: int):
    return db.get_purchases(pid)


# ── Predictions & Recommendations ─────────────────────────

@app.get("/products/{pid}/predict")
def predict(pid: int):
    return logic.predict_days_remaining(pid)


@app.get("/products/{pid}/recommend")
def recommend(pid: int):
    return logic.recommend(pid)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)
