# 💳 Streamlit OAuth + PayPal Integration

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**安全、優雅的 Streamlit 付款與認證組件**

這個專案是從 [streamlit-oauth](https://github.com/dnplus/streamlit-oauth) fork 並擴展，新增了完整的 PayPal 付款支援，同時保留原有的 OAuth2 認證功能。

## ✨ 特色

### 💳 PayPal 付款支援（新功能）
- 🔒 **安全優先**：Client Secret 只在後端使用
- 🪟 **Popup 結帳**：專業的彈窗付款體驗
- ✅ **自動捕獲**：付款完成後自動捕獲訂單
- 🛡️ **CSRF 防護**：內建安全機制
- 🌍 **多幣別**：支援 USD、EUR、GBP、TWD 等
- 🧪 **Sandbox 就緒**：輕鬆使用 PayPal 測試環境

### 🔐 OAuth2 認證（原功能保留）
- 支援多種 OAuth 提供商（Google、GitHub、Discord 等）
- PKCE 支援
- Token 刷新與撤銷

## 🚀 快速開始

### 安裝

```bash
pip install -e .
```

### PayPal 付款範例

```python
import streamlit as st
from streamlit_oauth import PayPalComponent
import os

# 初始化 PayPal 組件
paypal = PayPalComponent(
    client_id=os.getenv('PAYPAL_CLIENT_ID'),
    client_secret=os.getenv('PAYPAL_CLIENT_SECRET'),
    mode='sandbox'  # 測試環境
)

# 創建付款按鈕
if 'payment' not in st.session_state:
    result = paypal.payment_button(
        name="支付 $10 USD",
        amount=10.00,
        currency='USD',
        description='購買商品'
    )

    if result:
        st.session_state.payment = result
        st.rerun()
else:
    st.success(f"付款成功！訂單 ID: {st.session_state.payment['order_id']}")
```

### OAuth2 認證範例

```python
import streamlit as st
from streamlit_oauth import OAuth2Component

# 初始化 OAuth2 組件
oauth2 = OAuth2Component(
    client_id='your_client_id',
    client_secret='your_client_secret',
    authorize_endpoint='https://accounts.google.com/o/oauth2/auth',
    token_endpoint='https://oauth2.googleapis.com/token'
)

# 創建登入按鈕
result = oauth2.authorize_button(
    name="Login with Google",
    redirect_uri='https://your-app/component/streamlit_oauth.authorize_button',
    scope='openid email'
)
```

## 📚 文檔

**完整文檔索引請見 [docs/README.md](docs/README.md)**

### 快速導航

**新手入門：**
- 📖 [用戶指南](docs/guides/user-guide.md) - 完整的 PayPal 整合使用指南
- 🧪 [測試指南](docs/guides/testing-guide.md) - 如何測試 PayPal 功能

**開發者：**
- 📐 [PayPal 整合設計](docs/design/paypal-integration.md) - 技術決策與架構
- 🔒 [安全審查](docs/design/security-audit.md) - 安全性分析報告（9.5/10）
- 🎯 [取消處理設計](docs/design/cancellation-handling.md) - 付款取消功能設計

**專案報告：**
- ✅ [實作總結](docs/reports/implementation.md) - v1.1 功能實作詳情
- 📊 [測試報告](docs/reports/test-report.md) - 完整測試結果（4/4 通過）
- 📈 [專案狀態](docs/reports/project-status.md) - 開發進度與統計

## 🧪 測試

### 快速測試（一鍵完成）

```bash
./quick_test.sh
```

### 手動測試

```bash
# 1. 單元測試
python test_paypal_component.py

# 2. 啟動範例應用
streamlit run examples/paypal_basic.py
```

## 📦 專案結構

```
streamlit-oauth/
├── streamlit_oauth/       # 主套件
│   ├── __init__.py       # OAuth2Component + PayPalComponent
│   └── frontend/         # 前端組件（React + TypeScript）
├── examples/             # 範例應用
│   ├── paypal_basic.py   # PayPal 基本範例
│   └── google.py         # OAuth 範例
├── tests/                # 測試檔案
├── docs/                 # 文檔
└── requirements.txt      # 依賴管理
```

## 🔒 安全特性

| 特性 | PayPal | OAuth2 |
|------|--------|--------|
| Client Secret 保護 | ✅ | ✅ |
| CSRF 防護 | ✅ | ✅ |
| 時效性控制 | ✅ (5分鐘) | ✅ |
| 跨域保護 | ✅ | ✅ |
| 重放攻擊防護 | ✅ | ✅ |

## 🛠️ 開發

### 設定開發環境

```bash
# 安裝開發依賴
pip install -r requirements-dev.txt

# 以開發模式安裝
pip install -e .

# 執行測試
python test_paypal_component.py

# 代碼格式化
black streamlit_oauth/
```

### 前端開發

```bash
cd streamlit_oauth/frontend
npm install
npm run dev  # 啟動 Vite 開發伺服器
```

## 📊 技術決策

### 為什麼使用 Popup 模式？

1. **避免 URL 參數複雜性**：直接回傳 Python dict
2. **更好的用戶體驗**：獨立視窗更專業
3. **狀態管理簡單**：自動整合 Streamlit session state

### 為什麼保留 OAuth 架構？

- Popup 機制適用於多種場景（認證、付款等）
- 可擴展支援其他服務
- 代碼重用性高

## 🗺️ 未來規劃

- [ ] 支援更多付款方式（Stripe、LINE Pay）
- [ ] 訂閱付款功能
- [ ] 退款 API
- [ ] Webhook 整合
- [ ] 發布到 PyPI

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

### 貢獻指南

1. Fork 本專案
2. 創建 feature 分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

## 📝 授權

與原 [streamlit-oauth](https://github.com/dnplus/streamlit-oauth) 專案相同的授權條款。

## 🙏 致謝

- 原 **streamlit-oauth** 專案由 [Dylan Lu](https://github.com/dnplus) 創建
- PayPal 整合功能擴展與實作

## 📧 聯絡

- **Issues**: [GitHub Issues](../../issues)
- **Discussions**: [GitHub Discussions](../../discussions)

---

**狀態：** 🟢 Active Development
**最後更新：** 2025-10-01
**版本：** 0.1.14
