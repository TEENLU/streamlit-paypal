# Streamlit PayPal Integration - 專案總覽

## 📦 專案資訊

**專案名稱：** streamlit-oauth (with PayPal support)
**版本：** 0.1.14
**狀態：** ✅ 可用於開發測試
**最後更新：** 2025-10-01

## 🎯 專案目標

將 `streamlit-oauth` 架構改造為支援 PayPal 付款的 Streamlit 組件，保留其優雅的 popup + 回調機制，同時維持與原 OAuth2Component 的兼容性。

## 📂 專案結構

```
streamlit-oauth/
├── streamlit_oauth/              # 主套件
│   ├── __init__.py              # OAuth2Component + PayPalComponent
│   └── frontend/                # 前端組件
│       ├── main.js              # 核心邏輯（支援 OAuth 和 PayPal）
│       ├── style.css            # 按鈕樣式
│       └── dist/                # 打包後的前端（release 模式）
│
├── examples/                     # 範例應用
│   ├── paypal_basic.py          # PayPal 基本範例
│   ├── google.py                # OAuth 範例（原有）
│   └── ...                      # 其他 OAuth 範例
│
├── tests/                        # 測試檔案
│   ├── test_oauth_component.py  # OAuth 測試
│   └── test_internal.py         # 內部測試
│
├── docs/                         # 文檔
│   ├── PAYPAL_DESIGN.md         # 設計文檔
│   ├── IMPLEMENTATION_SUMMARY.md # 實作總結
│   ├── README_PAYPAL.md         # PayPal 使用文檔
│   └── TESTING_GUIDE.md         # 測試指南
│
├── test_paypal_component.py     # PayPal 單元測試
├── quick_test.sh                # 快速測試腳本
│
├── setup.py                     # 套件設定
├── requirements.txt             # 生產依賴
├── requirements-dev.txt         # 開發依賴
├── .env.example                 # 環境變數範本
└── .gitignore                   # Git 忽略規則
```

## 🚀 快速開始

### 1. 安裝

```bash
# 從原始碼安裝（開發模式）
pip install -e .

# 或從 PyPI 安裝（未來發布後）
# pip install streamlit-paypal
```

### 2. 設定環境變數

```bash
cp .env.example .env
# 編輯 .env 填入 PayPal Sandbox 憑證
```

### 3. 執行測試

```bash
# 一鍵測試
./quick_test.sh

# 或手動測試
python test_paypal_component.py
streamlit run examples/paypal_basic.py
```

## ⚙️ 核心功能

### PayPalComponent

```python
from streamlit_oauth import PayPalComponent

paypal = PayPalComponent(
    client_id='your_client_id',
    client_secret='your_client_secret',
    mode='sandbox'  # or 'production'
)

result = paypal.payment_button(
    name="支付 $10 USD",
    amount=10.00,
    currency='USD',
    description='購買商品'
)
```

**主要方法：**
- `payment_button()` - 渲染付款按鈕並處理完整流程
- `_create_order()` - 後端創建訂單（私有）
- `_capture_order()` - 後端捕獲付款（私有）
- `_get_access_token()` - OAuth 2.0 認證（私有）

### OAuth2Component（原功能保留）

```python
from streamlit_oauth import OAuth2Component

oauth2 = OAuth2Component(
    client_id='your_client_id',
    client_secret='your_client_secret',
    authorize_endpoint='https://...',
    token_endpoint='https://...'
)

result = oauth2.authorize_button(
    name="Login with Google",
    redirect_uri='https://...',
    scope='openid email'
)
```

## 🔒 安全特性

| 特性 | 實作方式 | 狀態 |
|------|---------|------|
| **Client Secret 保護** | 只在後端使用，前端只傳遞 Order ID | ✅ |
| **CSRF 防護** | Order ID 驗證 + Session state 追蹤 | ✅ |
| **時效性控制** | 訂單 5 分鐘過期 | ✅ |
| **跨域保護** | Popup 同源策略 | ✅ |
| **重放攻擊防護** | Order 單次捕獲 | ✅ |

## 📊 技術決策

### 為什麼保留 OAuth 架構？

1. **Popup 機制優雅**：避免 URL 參數傳遞複雜性
2. **狀態管理簡單**：直接回傳 Python dict
3. **用戶體驗好**：獨立彈窗更專業
4. **架構可擴展**：未來可支援其他支付方式

### 為什麼不改回調 URL 名稱？

- `component/streamlit_oauth.authorize_button` 語義上合理（authorize payment）
- 這只是內部技術路徑，用戶不需要理解
- PayPal 不需要在 Dashboard 預先設定（動態指定）
- 保持簡單，避免破壞性變更

## 🧪 測試覆蓋

### 單元測試
- ✅ Component 初始化（sandbox/production）
- ✅ Access token 取得
- ✅ 訂單創建與 session 追蹤
- ✅ CSRF 防護（unknown order 拒絕）
- ✅ 過期檢查（>5 分鐘）
- ✅ 訂單捕獲與清理
- ✅ 錯誤處理

**執行：** `python test_paypal_component.py`

### 整合測試
- ✅ 完整付款流程（需要真實 Sandbox 憑證）
- ✅ Popup 開啟與關閉
- ✅ 付款結果回傳

**執行：** `streamlit run examples/paypal_basic.py`

## 📝 依賴管理

### 生產依賴（requirements.txt）
```
streamlit>=1.28.1       # 核心框架
httpx-oauth==0.15.1     # OAuth2Component
requests>=2.31.0        # PayPalComponent
python-dotenv==1.0.1    # 環境變數
```

### 開發依賴（requirements-dev.txt）
```
build>=1.0.0            # 打包工具
twine>=4.0.0            # PyPI 上傳
pytest>=7.0.0           # 測試框架
black>=23.0.0           # 代碼格式化
flake8>=6.0.0           # 代碼檢查
mypy>=1.0.0             # 類型檢查
sphinx>=7.0.0           # 文檔生成
```

## 📈 版本歷史

### v0.1.14 (2025-10-01)
- ✅ 新增 PayPalComponent 類別
- ✅ 支援 sandbox/production 模式切換
- ✅ 實作完整的付款流程（創建、授權、捕獲）
- ✅ CSRF 防護與時效性檢查
- ✅ 前端支援 OAuth 和 PayPal 雙模式
- ✅ 完整文檔與測試覆蓋
- ✅ 保留 OAuth2Component 兼容性

## 🗺️ 未來規劃

### v0.2.0（短期）
- [ ] 前端打包優化（減少檔案大小）
- [ ] 更多幣別支援測試
- [ ] 錯誤訊息本地化（中文）
- [ ] 更多範例應用

### v0.3.0（中期）
- [ ] 支援多種付款方式（信用卡、Venmo）
- [ ] 訂閱付款功能
- [ ] 退款 API
- [ ] Webhook 整合

### v1.0.0（長期）
- [ ] 完整的文檔網站
- [ ] CI/CD 整合
- [ ] 效能優化
- [ ] 發布到 PyPI

## 🤝 貢獻指南

### 開發流程

1. **設定開發環境**
   ```bash
   git clone <repo-url>
   cd streamlit-oauth
   pip install -e .
   pip install -r requirements-dev.txt
   ```

2. **執行測試**
   ```bash
   python test_paypal_component.py
   ```

3. **代碼格式化**
   ```bash
   black streamlit_oauth/
   flake8 streamlit_oauth/
   ```

4. **提交變更**
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

### 提交訊息規範

遵循 [Conventional Commits](https://www.conventionalcommits.org/)：

- `feat:` 新功能
- `fix:` 錯誤修復
- `docs:` 文檔變更
- `test:` 測試相關
- `chore:` 建構或輔助工具變更

## 📚 相關資源

### 文檔
- [PAYPAL_DESIGN.md](./PAYPAL_DESIGN.md) - 設計決策
- [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - 實作總結
- [README_PAYPAL.md](./README_PAYPAL.md) - 使用文檔
- [TESTING_GUIDE.md](./TESTING_GUIDE.md) - 測試指南

### 外部資源
- [PayPal Orders API](https://developer.paypal.com/docs/api/orders/v2/)
- [PayPal Developer Dashboard](https://developer.paypal.com/dashboard/)
- [Streamlit Components](https://docs.streamlit.io/develop/concepts/custom-components)
- [原 streamlit-oauth](https://github.com/dnplus/streamlit-oauth)

## 📧 聯絡資訊

- **Issue Tracker:** [GitHub Issues](<your-repo-url>/issues)
- **Discussions:** [GitHub Discussions](<your-repo-url>/discussions)

## 📄 授權

與原 streamlit-oauth 專案相同的授權條款。

---

**最後更新：** 2025-10-01
**維護者：** [Your Name]
**狀態：** 🟢 Active Development
