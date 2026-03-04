# StockSense AI — 智能补货助手

基于 FastAPI + Streamlit + SQLite 的最小可运行 AI 补货决策 Demo。

## 功能

1. **记录购买日期** — 维护商品购买历史
2. **预测库存剩余天数** — 基于平均购买周期计算日均消耗
3. **补货建议** — 根据库存天数给出红/黄/绿建议

## 安装

```bash
pip install fastapi uvicorn streamlit requests
```

## 运行

需要同时启动后端和前端（两个终端）：

```bash
# 终端 1：启动 FastAPI 后端
python -m backend.app

# 终端 2：启动 Streamlit 前端
streamlit run frontend/ui.py
```

后端运行在 http://localhost:8000（API 文档：http://localhost:8000/docs）
前端运行在 http://localhost:8501

## 项目结构

```
StockSense-AI/
├── backend/
│   ├── app.py      # FastAPI 路由
│   ├── db.py       # SQLite 数据库操作
│   └── logic.py    # 预测与建议逻辑
├── frontend/
│   └── ui.py       # Streamlit 界面
├── .gitignore
└── README.md
```
