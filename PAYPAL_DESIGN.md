# Streamlit-PayPal 設計文件

## 專案目標

將 `streamlit-oauth` 架構改造為支援 PayPal 付款的 Streamlit 組件，保留其優雅的 popup + 回調機制，避免傳統方案中 URL 參數傳遞的複雜性。

## 技術決策

### 為什麼選擇改造 streamlit-oauth？

| 特性 | components.html (純 SDK) | streamlit-oauth 架構 |
|------|-------------------------|---------------------|
| **參數傳遞** | ❌ 需要透過 URL 或 postMessage | ✅ 直接回傳 Python dict |
| **彈窗控制** | ❌ 需要自己處理 | ✅ 內建 popup 邏輯 |
| **狀態管理** | ❌ 需手動同步 | ✅ 自動回傳到 session_state |
| **使用體驗** | 📄 嵌入式按鈕 | 🪟 獨立彈窗（更專業） |

### OAuth vs PayPal 流程對比

#### OAuth 流程
```
1. 開啟授權 URL (popup)
2. 用戶授權
3. 回調帶 code
4. 用 code 換 token ✅ (一次性完成)
```

#### PayPal 付款流程
```
1. 創建訂單 (需調用 PayPal API)
2. 開啟 PayPal 付款頁面
3. 用戶完成付款
4. 回調後需再次調用 API 捕獲付款 ✅ (兩階段交易)
```

## 環境配置

### Sandbox vs Production

PayPal 使用**完全獨立的兩組 credentials**，而非同一組 API Key 切換環境：

```
應用程式名稱：MyApp
├─ Sandbox Credentials
│  ├─ Client ID: AXxxxx-sandbox-xxxx
│  ├─ Secret: EJxxxx-sandbox-xxxx
│  ├─ API Base: https://api-m.sandbox.paypal.com
│  └─ Checkout Base: https://www.sandbox.paypal.com
│
└─ Live Credentials (需驗證商業帳戶)
   ├─ Client ID: AYxxxx-live-xxxx
   ├─ Secret: EKxxxx-live-xxxx
   ├─ API Base: https://api-m.paypal.com
   └─ Checkout Base: https://www.paypal.com
```

**實作方式：**
```python
class PayPalComponent:
    def __init__(self, client_id, client_secret, mode='sandbox'):
        if mode == 'sandbox':
            self.api_base = 'https://api-m.sandbox.paypal.com'
            self.checkout_base = 'https://www.sandbox.paypal.com'
        elif mode == 'production':
            self.api_base = 'https://api-m.paypal.com'
            self.checkout_base = 'https://www.paypal.com'
```

## 安全性設計

### 風險評估

| 風險項目 | 嚴重度 | 防護措施 |
|---------|--------|---------|
| **Client Secret 暴露** | 🔴 高 | Client Secret 只在後端使用，前端僅傳遞 Order ID |
| **CSRF 攻擊** | 🟡 中 | 後端驗證 Order ID + 時效性檢查 |
| **中間人攻擊** | 🟢 低 | PayPal HTTPS + popup 跨域保護 |

### 安全架構

```
┌─────────────────────────────────────────────────┐
│ Streamlit App (Python Backend)                  │
│                                                  │
│  1. 用戶點擊「付款」                               │
│  2. Python 用 client_secret 創建訂單              │
│  3. 傳遞 order_id 到前端（無敏感資訊）              │
│     ↓                                            │
│  ┌────────────────────────────────┐             │
│  │ JavaScript Component (Frontend) │             │
│  │                                 │             │
│  │  4. 開啟 PayPal popup            │             │
│  │  5. 用戶完成付款                  │             │
│  │  6. 回傳 order_id 到 Python      │             │
│  └────────────────────────────────┘             │
│     ↓                                            │
│  7. Python 驗證 order_id 匹配                     │
│  8. Python 用 client_secret 捕獲付款              │
│  9. 返回付款結果給用戶                             │
└─────────────────────────────────────────────────┘
```

### 安全檢查清單

- [x] Client Secret 只在 Python 後端使用
- [x] 前端只傳遞 Order ID（非敏感資訊）
- [x] 後端驗證 Order ID 來源
- [x] Production 模式強制 HTTPS
- [x] 訂單有時效性限制（防重放攻擊，預設 5 分鐘）
- [x] 使用環境變數管理 credentials

## 實作計劃

### 修改範圍評估

| 項目 | 難度 | 工作量 | 說明 |
|------|------|--------|------|
| Python API 整合 | 🟡 中 | 2-3 小時 | 實作 PayPal Orders API 的 create/capture |
| JavaScript 修改 | 🟢 低 | 1 小時 | 修改回調參數解析（從 `code` 改為 `token` + `PayerID`） |
| 安全加固 | 🟡 中 | 1-2 小時 | Order ID 驗證、時效性檢查、HTTPS 強制 |
| 測試與除錯 | 🟡 中 | 2-3 小時 | PayPal Sandbox 環境測試 |

### 需要修改的文件

#### 1. `streamlit_oauth/__init__.py` - 核心邏輯改造

**主要變更：**
- 移除 `httpx_oauth` 依賴
- 新增 `PayPalComponent` 類別
- 實作 `_create_order_backend()` - 創建訂單
- 實作 `_capture_order_backend()` - 捕獲付款
- 實作 `_get_access_token()` - OAuth 2.0 認證
- 新增 Order ID 驗證機制
- 新增時效性檢查

#### 2. `streamlit_oauth/frontend/main.js` - 輕度修改

**主要變更：**
- 保留 popup 邏輯（完全不動）
- 修改回調 URL 參數解析：
  - OAuth: `?code=xxx&state=yyy`
  - PayPal: `?token=xxx&PayerID=yyy`

#### 3. 新增文件

- `requirements.txt` - 移除 `httpx-oauth`，確保有 `requests`
- `examples/paypal_basic.py` - 基本使用範例
- `examples/paypal_advanced.py` - 進階功能範例
- `README_PAYPAL.md` - PayPal 專用文檔

## API 設計

### 基本使用

```python
import streamlit as st
from streamlit_paypal import PayPalComponent
import os

# 初始化組件
paypal = PayPalComponent(
    client_id=os.getenv('PAYPAL_CLIENT_ID'),
    client_secret=os.getenv('PAYPAL_CLIENT_SECRET'),
    mode='sandbox'  # 或 'production'
)

# 使用付款按鈕
if 'payment' not in st.session_state:
    result = paypal.payment_button(
        name="支付 $10 USD",
        amount=10.00,
        currency='USD',
        redirect_uri='https://your-app.streamlit.app/component/streamlit_paypal.payment_button',
        description='購買商品',
        key='payment_btn'
    )

    if result:
        st.session_state.payment = result
        st.rerun()
else:
    payment = st.session_state.payment
    st.success(f"付款成功！訂單 ID: {payment['id']}")
    st.json(payment)
```

### 進階功能

```python
# 自訂按鈕樣式
result = paypal.payment_button(
    name="立即購買",
    amount=29.99,
    currency='TWD',
    redirect_uri='...',
    icon='💳',
    use_container_width=True,
    popup_height=800,
    popup_width=600
)

# 錯誤處理
try:
    result = paypal.payment_button(...)
except PayPalError as e:
    st.error(f"付款失敗：{e}")
```

## 與 OAuth 的安全性對比

| 安全特性 | streamlit-oauth (OAuth) | streamlit-paypal (改造版) |
|---------|------------------------|--------------------------|
| **敏感資訊處理** | Client Secret 在後端 ✅ | Client Secret 在後端 ✅ |
| **CSRF 防護** | State 參數驗證 ✅ | Order ID 驗證 ✅ |
| **跨域保護** | Popup 同源策略 ✅ | Popup 同源策略 ✅ |
| **資料篡改風險** | 低（只傳 code） | 低（只傳 orderID） |
| **重放攻擊防護** | Code 單次使用 ✅ | Order 單次捕獲 ✅ |

**結論：安全性相當，只要遵守「Client Secret 不上前端」原則。**

## 測試計劃

### Sandbox 測試

1. **基本流程測試**
   - [ ] 創建訂單成功
   - [ ] Popup 正常開啟
   - [ ] 用戶完成付款
   - [ ] 訂單捕獲成功
   - [ ] 結果正確回傳

2. **錯誤處理測試**
   - [ ] 用戶取消付款
   - [ ] 訂單過期（>5 分鐘）
   - [ ] 無效的 Order ID
   - [ ] API 認證失敗

3. **安全性測試**
   - [ ] Client Secret 不出現在前端
   - [ ] Order ID 驗證有效
   - [ ] CSRF 防護有效

### Production 檢查

- [ ] HTTPS 強制啟用
- [ ] 使用 Live Credentials
- [ ] 環境變數正確設定
- [ ] 錯誤日誌記錄

## 未來擴展

### 可能的功能

1. **多種支付方式**
   - 信用卡直接付款
   - PayPal Credit
   - Venmo

2. **訂閱付款**
   - 週期性扣款
   - 訂閱管理

3. **退款功能**
   - 全額退款
   - 部分退款

4. **Webhook 整合**
   - 付款狀態變更通知
   - 爭議處理

## 參考資料

- [PayPal REST API 文檔](https://developer.paypal.com/api/rest/)
- [PayPal Orders API](https://developer.paypal.com/docs/api/orders/v2/)
- [PayPal Sandbox 指南](https://developer.paypal.com/tools/sandbox/)
- [streamlit-oauth 原始專案](https://github.com/dnplus/streamlit-oauth)

---

**文件版本：** v1.0
**最後更新：** 2025-10-01
**狀態：** 設計階段
