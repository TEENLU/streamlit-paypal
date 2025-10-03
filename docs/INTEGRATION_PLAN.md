# Streamlit-PayPal 主專案整合計劃

**計劃版本：** v1.0
**建立日期：** 2025-10-03
**目標專案：** 3droid_template_en (MicroSaaS Template)

---

## 📋 整合概述

將 streamlit-paypal 套件整合至主專案 (3droid_template_en)，作為第三個支付渠道，與現有的 Patreon（訂閱制）和 Buy Me a Coffee（一次性購買）並存。

### 整合定位

```
主專案支付架構
├── Patreon (會員訂閱)
│   └── 月費制，提供會員點數（membership credits）
├── Buy Me a Coffee (咖啡打賞)
│   └── 一次性購買，提供購買點數（purchased credits）
└── PayPal (通用支付) ← 新增
    └── 一次性購買，提供購買點數（purchased credits）
```

---

## 🎯 整合策略

### 核心原則

1. **最小侵入性**：不修改 template 核心，只在 `features/` 新增模組
2. **架構一致性**：完全參照現有 BMC 整合模式
3. **可選功能**：環境變數未設定時自動隱藏
4. **多元支付**：提供更多元的一次性購買選項

### 設計目標

- ✅ 整合進現有 Dual Credit System
- ✅ 與 BMC 平行存在，不相互影響
- ✅ 遵循 CLAUDE.md 開發規範
- ✅ 使用 `features/` 目錄進行功能擴展
- ✅ 使用 `st.session_state` 做為主要資料儲存

---

## 📁 整合架構設計

### 主專案現狀分析

```
3droid_template_en/
├── pages/
│   └── app.py                    # 主應用頁面（修改 main() 函數）
├── utils/                         # Template 核心模組（唯讀）
│   ├── db.py                     # FirestoreDB（參考模式）
│   ├── dual_credit_system.py    # 雙點數系統
│   ├── bmc_integration.py       # BMC API 整合（參考）
│   └── bmc_ui_components.py     # BMC UI 元件（參考）
├── features/                      # 自訂功能區（可修改）
│   └── (空的，準備新增 PayPal)
├── requirements.txt              # 依賴清單
└── .env                          # 環境變數
```

### 整合後架構

```
3droid_template_en/
├── pages/
│   └── app.py                         # 修改：新增 PayPal UI 區塊
├── utils/                              # 不修改
│   ├── bmc_integration.py            # 參考模式
│   └── bmc_ui_components.py          # 參考模式
├── features/                           # 新增模組
│   ├── paypal_integration.py         # 新增：PayPal API 整合
│   └── paypal_ui_components.py       # 新增：PayPal UI 元件
├── requirements.txt                   # 修改：新增 streamlit-paypal
└── .env                               # 修改：新增 PayPal 環境變數
```

---

## 🔄 資料流設計

### 付款流程

```
用戶點擊 PayPal 按鈕
    ↓
features/paypal_ui_components.py
    ↓
streamlit_paypal.create_order()  # 使用套件 API
    ↓
PayPal 彈窗完成付款
    ↓
features/paypal_integration.py 處理回調
    ↓
account_processor.add_credits(
    user_id=user_id,
    credits=credits,
    credit_type='purchased',
    source='paypal',
    transaction_id=order_id
)
    ↓
utils/dual_credit_system.py 更新點數
    ↓
st.session_state 更新
    ↓
UI 顯示成功訊息
```

### 與現有系統整合點

| 整合點 | 現有方法 | PayPal 調用方式 |
|-------|---------|----------------|
| **點數新增** | `account_processor.add_credits()` | 相同，`source='paypal'` |
| **點數查詢** | `account_processor.get_dual_credit_balance()` | 相同 |
| **UI 顯示** | `render_bmc_integration_section()` | 新增 `render_paypal_integration_section()` |
| **儲存層** | `st.session_state` + Firebase | 相同 |

---

## 🛠️ 實作計劃

### Phase 1: 依賴安裝 (5 分鐘)

**檔案：** `requirements.txt`

```diff
  streamlit==1.40.0
  firebase-admin==6.6.0
  python-dotenv==1.0.1
  streamlit-oauth
+ streamlit-paypal  # 本地套件路徑或 PyPI
  patreon
  setuptools
  streamlit-bridge
  streamlit-cookies-controller
  streamlit-image-select
  pytest>=7.0.0
  requests
  pyyaml
```

**安裝方式：**
```bash
# 本地開發（使用本地套件）
pip install -e ../streamlit-paypal

# 或未來發布後（使用 PyPI）
pip install streamlit-paypal
```

---

### Phase 2: 環境變數配置 (5 分鐘)

**檔案：** `.env`

```bash
# PayPal Configuration (Optional - for one-time purchases)
PAYPAL_CLIENT_ID=your-paypal-client-id
PAYPAL_CLIENT_SECRET=your-paypal-client-secret
PAYPAL_MODE=sandbox  # or 'live' for production
```

**說明：**
- 未設定時，PayPal 功能自動隱藏
- Sandbox 模式用於開發測試
- Production 模式需通過 PayPal 商業帳戶驗證

---

### Phase 3: PayPal 整合模組 (30 分鐘)

**檔案：** `features/paypal_integration.py`

**設計原則：**
- 完全參照 `utils/bmc_integration.py` 架構
- 使用 `streamlit_paypal` 套件處理訂單
- 整合進 `DualCreditSystem.add_credits()`
- 提供錯誤處理與日誌記錄

**核心功能：**
```python
class PayPalIntegration:
    """PayPal 整合模組，處理付款邏輯"""

    def __init__(self, account_processor):
        self.account_processor = account_processor
        self.paypal = PayPalComponent(
            client_id=os.getenv('PAYPAL_CLIENT_ID'),
            client_secret=os.getenv('PAYPAL_CLIENT_SECRET'),
            mode=os.getenv('PAYPAL_MODE', 'sandbox')
        )

    def process_payment(self, user_id, amount, currency, credits):
        """處理付款並新增點數"""
        # 使用 streamlit_paypal 創建訂單
        # 處理付款結果
        # 調用 account_processor.add_credits()
        pass

    def handle_payment_result(self, result, user_id, credits):
        """處理付款結果（成功/取消/錯誤）"""
        pass
```

**參考架構：**
- `utils/bmc_integration.py` 的錯誤處理模式
- `utils/dual_credit_system.py` 的點數新增方法
- `streamlit_paypal` 的付款流程

---

### Phase 4: PayPal UI 元件 (30 分鐘)

**檔案：** `features/paypal_ui_components.py`

**設計原則：**
- 完全參照 `utils/bmc_ui_components.py` 的 UI 模式
- 提供與 BMC 一致的視覺風格
- 支援多種方案配置
- 完善的錯誤提示與成功反饋

**核心功能：**
```python
def render_paypal_integration_section(account_processor, user_id):
    """渲染 PayPal 整合區塊"""

    st.markdown("### 💰 PayPal 購買點數")

    # 檢查環境變數
    if not all([os.getenv('PAYPAL_CLIENT_ID'),
                os.getenv('PAYPAL_CLIENT_SECRET')]):
        st.info("💡 PayPal 功能未啟用")
        return

    # 顯示購買方案
    plans = [
        {"amount": 2.99, "currency": "USD", "credits": 30},
        {"amount": 4.99, "currency": "USD", "credits": 50},
        {"amount": 9.99, "currency": "USD", "credits": 100},
    ]

    # 渲染方案按鈕
    for plan in plans:
        render_payment_button(plan, user_id, account_processor)
```

**UI 風格參考：**
- BMC 的方案卡片設計
- 統一的按鈕樣式
- 一致的成功/錯誤訊息格式

---

### Phase 5: 主頁面整合 (15 分鐘)

**檔案：** `pages/app.py`

**修改位置：** `main(account_processor)` 函數

```python
def main(account_processor: AccountProcessor):
    """Main function page - Dual Credit System Demo"""
    st.subheader("🎯 Dual Credit System Demo")

    user_id = st.session_state.get('user', {}).get('id')

    # 1. 顯示點數餘額（現有）
    try:
        balance = account_processor.get_dual_credit_balance(user_id)
        # ... 現有顯示邏輯 ...
    except Exception as e:
        st.error(f"Error displaying credits: {e}")

    # 2. BMC 整合區塊（現有）
    from utils.bmc_ui_components import render_bmc_integration_section
    render_bmc_integration_section(
        account_processor=account_processor,
        user_id=user_id
    )

    # 3. PayPal 整合區塊（新增）
    from features.paypal_ui_components import render_paypal_integration_section
    render_paypal_integration_section(
        account_processor=account_processor,
        user_id=user_id
    )

    st.divider()

    # ... 其餘現有邏輯 ...
```

**修改原則：**
- ✅ 只修改 `main()` 函數
- ✅ 新增自訂函數到檔案末端
- ❌ 不修改 `init_page()`, 登入/登出流程, `if __name__ == "__main__"` 區塊

---

## 🎨 UI 設計方案

### 方案 A: 平行展示（推薦）

**優點：** 直觀、易於比較、無需切換
**缺點：** 佔用較多垂直空間

```
┌─────────────────────────────────────────┐
│  💳 購買點數                             │
├─────────────────────────────────────────┤
│                                         │
│  ☕ Buy Me a Coffee                      │
│  ┌──────────┐ ┌──────────┐             │
│  │ 3 coffees│ │ 5 coffees│             │
│  │   $3     │ │   $5     │             │
│  │  30 點   │ │  50 點   │             │
│  └──────────┘ └──────────┘             │
│                                         │
│  💰 PayPal                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐│
│  │ 入門方案 │ │ 進階方案 │ │ 專業方案 ││
│  │  $2.99   │ │  $4.99   │ │  $9.99   ││
│  │  30 點   │ │  50 點   │ │  100 點  ││
│  └──────────┘ └──────────┘ └──────────┘│
└─────────────────────────────────────────┘
```

**實作：**
```python
st.markdown("### 💳 購買點數")

# BMC 區塊
render_bmc_integration_section(...)

# PayPal 區塊
render_paypal_integration_section(...)
```

---

### 方案 B: Tab 切換

**優點：** 節省空間、整潔
**缺點：** 需要切換、可能降低可見性

```
┌─────────────────────────────────────────┐
│  💳 購買點數                             │
├─────────────────────────────────────────┤
│  [☕ Buy Me a Coffee] [💰 PayPal]       │
├─────────────────────────────────────────┤
│                                         │
│  當前選擇的支付方式內容...               │
│                                         │
└─────────────────────────────────────────┘
```

**實作：**
```python
st.markdown("### 💳 購買點數")

tab1, tab2 = st.tabs(["☕ Buy Me a Coffee", "💰 PayPal"])

with tab1:
    render_bmc_integration_section(...)

with tab2:
    render_paypal_integration_section(...)
```

---

### 推薦方案：A（平行展示）

**理由：**
1. 與現有 BMC 展示方式一致
2. 用戶可直接比較價格與方案
3. 無需額外互動即可看到所有選項
4. 符合 template 的 UI 風格

---

## 🧪 測試計劃

### 單元測試

**檔案：** `tests/unit/test_paypal_integration.py`

```python
def test_paypal_integration_init():
    """測試 PayPal 整合初始化"""
    pass

def test_payment_processing():
    """測試付款處理流程"""
    pass

def test_credit_addition():
    """測試點數新增"""
    pass

def test_error_handling():
    """測試錯誤處理"""
    pass
```

### 整合測試

**檔案：** `tests/integration/test_paypal_flow.py`

```python
def test_complete_payment_flow():
    """測試完整付款流程"""
    # 1. 創建訂單
    # 2. 模擬付款完成
    # 3. 驗證點數新增
    # 4. 驗證 Firebase 記錄
    pass

def test_cancelled_payment():
    """測試付款取消處理"""
    pass

def test_dual_credit_integration():
    """測試與雙點數系統整合"""
    pass
```

### 手動測試檢查清單

- [ ] **環境設定**
  - [ ] `.env` 配置正確
  - [ ] Sandbox credentials 有效

- [ ] **UI 顯示**
  - [ ] PayPal 區塊正確顯示
  - [ ] 方案價格與點數正確
  - [ ] 未設定環境變數時隱藏

- [ ] **付款流程**
  - [ ] 訂單創建成功
  - [ ] Popup 正常開啟
  - [ ] 付款完成後視窗關閉
  - [ ] 點數正確新增

- [ ] **取消處理**
  - [ ] PayPal 頁面取消 → 顯示訊息
  - [ ] 關閉 Popup → 顯示訊息
  - [ ] 超時 → 自動關閉

- [ ] **錯誤處理**
  - [ ] 網路錯誤 → 友好提示
  - [ ] API 錯誤 → 友好提示
  - [ ] 點數新增失敗 → 回滾處理

- [ ] **Dual Credit System**
  - [ ] 點數加入 `purchased` 類別
  - [ ] Firebase 記錄正確
  - [ ] 餘額顯示更新

---

## 📝 文檔更新計劃

### 更新檔案

1. **`README.md`**
   - 新增 PayPal 配置章節
   - 更新支付方式說明
   - 新增 PayPal 使用範例

2. **`docs/dual_credit_system.md`** (如存在)
   - 更新支付渠道清單
   - 新增 PayPal 整合說明

3. **新增 `docs/paypal_integration_guide.md`**
   - PayPal 設定步驟
   - Sandbox/Production 切換
   - 常見問題排解

### 範例更新

**`README.md` 新增章節：**

```markdown
### 2.4 PayPal 配置（可選）

如果您想提供 PayPal 支付選項：

1. 前往 [PayPal Developer Dashboard](https://developer.paypal.com/dashboard/applications)
2. 創建應用並取得 Client ID 和 Secret
3. 配置 `.env` 檔案：
   ```bash
   PAYPAL_CLIENT_ID=your-client-id
   PAYPAL_CLIENT_SECRET=your-client-secret
   PAYPAL_MODE=sandbox  # 測試環境，正式上線改為 'live'
   ```

> 💡 未設定時，PayPal 功能自動隱藏，不影響其他功能
```

---

## ⚙️ 環境配置範本

### `.env.example` 更新

```bash
# Firebase (Required for database and authentication)
FIREBASE_PRIVATE_KEY="your-firebase-private-key"

# Patreon OAuth (Required for user authentication)
PATREON_CLIENT_ID="your-client-id"
PATREON_CLIENT_SECRET="your-client-secret"
PATREON_REDIRECT_URI="http://localhost:8501/component/streamlit_oauth.authorize_button"
PATREON_AUTHORIZE_URL="https://www.patreon.com/oauth2/authorize"
PATREON_TOKEN_URL="https://www.patreon.com/api/oauth2/token"
PATREON_REFRESH_TOKEN_URL="https://www.patreon.com/api/oauth2/token"
PATREON_REVOKE_TOKEN_URL="https://www.patreon.com/api/oauth2/revoke"
PATREON_SCOPE="identity identity[email] identity.memberships"

# Buy Me a Coffee (Optional - for one-time purchases)
BMC_API_TOKEN="your-bmc-api-token-here"

# PayPal (Optional - for one-time purchases)
PAYPAL_CLIENT_ID="your-paypal-client-id"
PAYPAL_CLIENT_SECRET="your-paypal-client-secret"
PAYPAL_MODE="sandbox"  # or 'live' for production

# Google Analytics (Optional - for tracking user behavior)
GA_MEASUREMENT_ID="your-ga-measurement-id-here"
GA_API_SECRET="your-ga-api-secret-here"
```

---

## 🔐 安全性考量

### 整合安全檢查清單

- [x] **Client Secret 保護**
  - PayPal Client Secret 僅在後端使用（由 streamlit-paypal 套件保證）
  - 環境變數管理，不進版本控制

- [x] **CSRF 防護**
  - Order ID 驗證機制（由 streamlit-paypal 套件提供）
  - Session state 追蹤

- [x] **資料驗證**
  - 付款金額驗證
  - 點數計算驗證
  - Firebase 寫入驗證

- [x] **錯誤處理**
  - 所有 API 呼叫都有 try-except
  - 用戶友好的錯誤訊息
  - 錯誤日誌記錄

- [x] **Production 準備**
  - HTTPS 強制（由 Streamlit Cloud 提供）
  - 環境變數檢查
  - Mode 切換機制

---

## 📊 實作檢查清單

### Phase 1: 準備工作 ✅
- [ ] 確認 streamlit-paypal 套件可用
- [ ] 準備 PayPal Sandbox credentials
- [ ] 閱讀主專案 CLAUDE.md 規範

### Phase 2: 依賴安裝
- [ ] 更新 `requirements.txt`
- [ ] 測試本地安裝 `pip install -e ../streamlit-paypal`
- [ ] 驗證套件可正常導入

### Phase 3: 環境配置
- [ ] 更新 `.env` 新增 PayPal 配置
- [ ] 更新 `.env.example` 範本
- [ ] 測試環境變數載入

### Phase 4: 模組開發
- [ ] 創建 `features/paypal_integration.py`
- [ ] 實作 `PayPalIntegration` 類別
- [ ] 參考 `utils/bmc_integration.py` 架構
- [ ] 整合 `account_processor.add_credits()`

### Phase 5: UI 開發
- [ ] 創建 `features/paypal_ui_components.py`
- [ ] 實作 `render_paypal_integration_section()`
- [ ] 參考 `utils/bmc_ui_components.py` 風格
- [ ] 設計購買方案

### Phase 6: 主頁面整合
- [ ] 修改 `pages/app.py` 的 `main()` 函數
- [ ] 新增 PayPal UI 區塊
- [ ] 測試與現有功能共存

### Phase 7: 測試
- [ ] 單元測試
- [ ] 整合測試
- [ ] 手動測試（完整流程）
- [ ] Sandbox 環境驗證

### Phase 8: 文檔
- [ ] 更新 `README.md`
- [ ] 新增 PayPal 設定說明
- [ ] 創建使用範例

### Phase 9: Code Review
- [ ] 檢查符合 CLAUDE.md 規範
- [ ] 確認沒有修改 template 核心
- [ ] 驗證錯誤處理完整
- [ ] 檢查安全性措施

### Phase 10: 部署準備
- [ ] Production credentials 準備
- [ ] 環境變數設定
- [ ] HTTPS 配置確認

---

## 🚀 部署步驟

### 本地開發環境

```bash
# 1. 安裝套件
cd /Users/lvdeen/3droid_template_en
pip install -e streamlit-paypal

# 2. 配置環境變數
# 編輯 .env 新增 PayPal 配置

# 3. 啟動應用
streamlit run Home.py

# 4. 測試付款流程
# 訪問 app.py 頁面，測試 PayPal 購買
```

### Production 部署

```bash
# 1. 更新 requirements.txt
# 改為 PyPI 版本（未來發布後）
streamlit-paypal>=0.1.14

# 2. 設定 Streamlit Cloud 環境變數
# PAYPAL_CLIENT_ID=<production-client-id>
# PAYPAL_CLIENT_SECRET=<production-client-secret>
# PAYPAL_MODE=live

# 3. 部署更新
git push origin main
```

---

## 💡 最佳實踐

### 開發建議

1. **參考現有模式**
   - 完全參照 `utils/bmc_integration.py` 和 `utils/bmc_ui_components.py`
   - 保持命名、結構、風格一致

2. **漸進式開發**
   - 先實作最基本功能（單一方案）
   - 測試通過後再擴展（多方案、進階功能）

3. **完善錯誤處理**
   - 所有外部 API 呼叫都要有 try-except
   - 提供用戶友好的錯誤訊息
   - 記錄詳細的錯誤日誌

4. **測試優先**
   - 每個功能完成後立即測試
   - 使用 Sandbox 環境充分測試
   - 模擬各種錯誤情境

### 整合建議

1. **環境變數管理**
   - 使用 `os.getenv()` 並提供預設值
   - 未設定時優雅降級（隱藏功能）
   - 不要硬編碼任何 credentials

2. **UI 一致性**
   - 與 BMC 區塊保持一致的視覺風格
   - 使用相同的 emoji、顏色、排版
   - 按鈕樣式統一

3. **點數系統整合**
   - 所有點數操作都透過 `account_processor`
   - 使用 `credit_type='purchased'`
   - 提供完整的 transaction metadata

---

## 📈 預期成果

### 功能成果
- ✅ PayPal 作為第三個支付渠道
- ✅ 完整的訂單創建、付款、捕獲流程
- ✅ 三種取消情境處理
- ✅ 與 Dual Credit System 無縫整合

### 技術成果
- ✅ 遵循 template 開發規範
- ✅ 最小侵入性修改
- ✅ 模組化、可維護的程式碼
- ✅ 完整的測試覆蓋

### 使用者成果
- ✅ 更多元的支付選擇
- ✅ 統一的購買體驗
- ✅ 清楚的錯誤提示與反饋
- ✅ 無縫的點數新增流程

---

## 🎯 成功指標

### 技術指標
- [ ] 所有測試通過（單元 + 整合）
- [ ] 無修改 template 核心檔案
- [ ] 遵循 CLAUDE.md 所有規範
- [ ] 安全評分 ≥ 9/10

### 功能指標
- [ ] Sandbox 環境測試通過
- [ ] 三種取消情境正確處理
- [ ] 點數正確新增到 Firebase
- [ ] UI 顯示與 BMC 一致

### 使用者指標
- [ ] 付款流程順暢（≤ 3 步）
- [ ] 錯誤訊息清晰易懂
- [ ] 取消後可重試
- [ ] 無需離開當前頁面

---

## 📞 支援與參考

### 相關文檔
- **主專案規範**：`/Users/lvdeen/3droid_template_en/CLAUDE.md`
- **Dual Credit System**：`/Users/lvdeen/3droid_template_en/docs/dual_credit_system.md`
- **BMC 整合參考**：`/Users/lvdeen/3droid_template_en/docs/bmc_integration_design.md`
- **PayPal 套件文檔**：`./docs/guides/user-guide.md`

### 參考實作
- **BMC 整合**：`/Users/lvdeen/3droid_template_en/utils/bmc_integration.py`
- **BMC UI**：`/Users/lvdeen/3droid_template_en/utils/bmc_ui_components.py`
- **主頁面**：`/Users/lvdeen/3droid_template_en/pages/app.py`

### 技術支援
- PayPal API：https://developer.paypal.com/api/rest/
- Streamlit Docs：https://docs.streamlit.io/
- Firebase Docs：https://firebase.google.com/docs

---

## 🎉 總結

本整合計劃提供了一個完整、可執行的路線圖，將 streamlit-paypal 套件整合至主專案。整合遵循最小侵入性原則，完全參照現有 BMC 整合模式，確保架構一致性和可維護性。

### 核心優勢
✅ **零侵入性**：不修改 template 核心，只在 `features/` 新增模組
✅ **架構一致**：完全參照現有 BMC 整合模式
✅ **可選功能**：環境變數未設定時自動隱藏
✅ **多元支付**：Patreon (訂閱) + BMC (咖啡) + PayPal (通用)

### 下一步行動
1. 審查此計劃，確認整合方向
2. 選擇 UI 展示方案（推薦方案 A）
3. 準備 PayPal Sandbox credentials
4. 開始實作（預計 2-3 小時完成）

---

**計劃版本：** v1.0
**建立日期：** 2025-10-03
**狀態：** 待審查
**預計工時：** 2-3 小時（含測試）
