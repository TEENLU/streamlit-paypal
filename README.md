# 💳 Streamlit PayPal

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**安全、優雅的 Streamlit PayPal 付款組件**

輕鬆整合 PayPal 付款到你的 Streamlit 應用。

> 本專案 fork 自 [streamlit-oauth](https://github.com/dnplus/streamlit-oauth)，專注於 PayPal 付款整合。

## ✨ 特色

- 🔒 **安全優先**：Client Secret 只在後端使用，前端零洩漏風險
- 🪟 **Popup 結帳**：專業的彈窗付款體驗，不中斷應用流程
- ✅ **自動捕獲**：付款完成後自動捕獲訂單
- 🛡️ **CSRF 防護**：內建訂單驗證與超時機制
- 🌍 **多幣別支援**：USD、EUR、GBP、TWD、JPY 等
- 🧪 **Sandbox 就緒**：輕鬆使用 PayPal 測試環境
- 🎯 **取消處理**：完整的付款取消與錯誤處理

## 🚀 快速開始

### 1. 安裝套件

```bash
pip install -e .
```

### 2. 設定環境變數

建立 `.env` 檔案：

```bash
PAYPAL_CLIENT_ID=你的_Client_ID
PAYPAL_CLIENT_SECRET=你的_Client_Secret
```

### 3. 執行範例

```bash
# 基礎範例
streamlit run examples/paypal_basic.py
```

### 4. 程式碼範例

```python
import streamlit as st
from streamlit_paypal import PayPalComponent
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
        description='購買商品',
        return_url='https://yourapp.streamlit.app'  # Required!
    )

    if result:
        st.session_state.payment = result
        st.rerun()
else:
    st.success(f"付款成功！訂單 ID: {st.session_state.payment['order_id']}")
```

> **⚠️ 生產環境注意**：此組件基於 Streamlit session state，適合即時互動場景。
> 若需可靠的訂單處理（避免網路中斷、瀏覽器關閉等問題），請額外設定 **PayPal Webhooks**
> 在後端接收付款通知並持久化訂單狀態。

## 📚 API 文檔

### PayPalComponent

```python
paypal = PayPalComponent(
    client_id: str,           # PayPal Client ID
    client_secret: str,       # PayPal Client Secret
    mode: str = 'sandbox'     # 'sandbox' 或 'live'
)

result = paypal.payment_button(
    name: str,                # 按鈕文字
    amount: float,            # 金額
    currency: str,            # 幣別 (USD, TWD, EUR...)
    description: str,         # 訂單描述
    return_url: str           # 付款後返回 URL (必填)
)
```

### 回傳值

付款成功時回傳 dict：

```python
{
    'order_id': 'xxx',        # PayPal 訂單 ID
    'status': 'COMPLETED',    # 訂單狀態
    'payer_email': 'xxx',     # 付款者 email
    'amount': '10.00',        # 金額
    'currency': 'USD'         # 幣別
}
```

## 🧪 測試

```bash
# 單元測試
python test_paypal_component.py

# 啟動範例測試
streamlit run examples/basic_payment.py
```

## 📦 專案結構

```
streamlit-paypal/
├── streamlit_paypal/      # 主套件
│   ├── __init__.py       # PayPalComponent
│   └── frontend/         # 前端組件（React + TypeScript）
├── examples/             # 範例應用
│   ├── basic_payment.py  # 基礎付款範例
│   └── complete_example.py  # 完整範例
├── tests/                # 測試檔案
├── docs/                 # 文檔
└── requirements.txt      # 依賴管理
```

## 🔒 安全特性

| 特性 | 說明 |
|------|------|
| Client Secret 保護 | ✅ Secret 只在後端使用，前端零洩漏 |
| CSRF 防護 | ✅ 訂單 ID 驗證機制 |
| 時效性控制 | ✅ 5分鐘超時自動取消 |
| 訂單驗證 | ✅ 只能 capture 自己創建的訂單 |
| 重放攻擊防護 | ✅ 訂單狀態追蹤 |

## 🛠️ 開發

```bash
# 安裝開發依賴
pip install -e .

# 執行測試
python test_paypal_component.py

# 前端開發
cd streamlit_paypal/frontend
npm install
npm run dev
```

## 📊 技術決策

### 為什麼使用 Popup 模式？

1. **避免 URL 參數複雜性**：直接回傳 Python dict，無需處理 callback URL
2. **更好的用戶體驗**：獨立視窗更專業，不中斷主應用流程
3. **狀態管理簡單**：自動整合 Streamlit session state
4. **安全性更高**：減少 URL 參數洩漏風險

## 🙏 致謝

本專案 fork 自 [dnplus/streamlit-oauth](https://github.com/dnplus/streamlit-oauth)，感謝原作者提供的優秀 Popup 機制架構。

## 🗺️ 未來規劃

- [ ] 支援更多付款方式（Stripe、LINE Pay）
- [ ] 訂閱付款功能
- [ ] 退款 API
- [ ] Webhook 整合範例（生產環境必備）
- [ ] 發布到 PyPI

### 關於 Webhook

本套件提供 **前端互動層**，適合即時付款體驗。
**生產環境建議架構**：

```
Streamlit App (此套件)     →  即時 UI、付款按鈕、用戶體驗
      ↓
PayPal Orders API          →  創建訂單、Popup 付款
      ↓
你的後端 + Webhook         →  接收 PAYMENT.CAPTURE.COMPLETED
                              持久化訂單、發貨、授權等
```

**為何需要 Webhook？**
- ✅ 可靠性：即使用戶關閉瀏覽器也能處理
- ✅ 安全性：Server-to-Server 驗證
- ✅ 完整性：接收所有付款事件（成功、失敗、退款等）

參考：[PayPal Webhooks 文檔](https://developer.paypal.com/docs/api-basics/notifications/webhooks/)

## 🙏 致謝

本專案 fork 自 [dnplus/streamlit-oauth](https://github.com/dnplus/streamlit-oauth)，感謝原作者提供的優秀 Popup 機制架構。

## 📝 授權

MIT License

---

**版本：** 0.1.14
**狀態：** 🟢 Active Development
