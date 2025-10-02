# OAuth2 Removal Plan - Streamlit PayPal Component

**日期：** 2025-10-02
**狀態：** ✅ 已確認執行
**目標：** 移除 OAuth2 功能並重新命名為 `streamlit-paypal` 獨立套件

---

## 📌 專案定位

**重要說明：**
- 本專案是 fork 自 [streamlit-oauth](https://github.com/dnplus/streamlit-oauth)
- 目的是建立**獨立的** PayPal 付款套件，而非 streamlit-oauth v2
- 因此可以**完全移除** OAuth2 功能，不需考慮向後兼容

## 🎯 移除理由

### 1. 功能定位不同
- **OAuth2：** 用戶認證（登入）
- **PayPal：** 付款處理

兩者是完全不同的使用場景，應該是兩個獨立的套件。

### 2. 程式碼複雜度
- 目前需要維護 OAuth 和 PayPal 的兼容邏輯
- 前端需要判斷 `redirect_uri` 來區分流程
- 後端有許多 OAuth 專用的輔助函數

### 3. 依賴管理
- `httpx-oauth` 只用於 OAuth2Component
- 移除後可減少依賴

### 4. 命名混淆
- 套件名稱 `streamlit-oauth` 但主要功能是 PayPal
- 應該重新命名為 `streamlit-paypal`

---

## 📊 影響分析

### 後端 (`streamlit_oauth/__init__.py`)

**總行數：** 472 行

**需要移除的部分：**

| 區塊 | 行數範圍 | 說明 | 行數 |
|------|---------|------|------|
| OAuth2 imports | 13-20 | `httpx_oauth` 相關 | 8 |
| OAuth2 輔助函數 | 48-70 | `_generate_state`, `_generate_pkce_pair` | 23 |
| OAuth2Component 類別 | 72-172 | 完整的 OAuth2 實作 | 101 |
| OAuth2 開發測試代碼 | 442-472 | `if not _RELEASE` 區塊 | 31 |
| **總計** | | | **163 行** |

**保留的部分：**

| 區塊 | 行數範圍 | 說明 | 行數 |
|------|---------|------|------|
| 基本 imports | 1-11 | Python 標準庫 + requests | 11 |
| Component 定義 | 22-35 | Streamlit component 設定 | 14 |
| PayPalError | 43-46 | PayPal 異常類別 | 4 |
| PayPalComponent | 178-440 | 完整的 PayPal 實作 | 263 |
| **總計** | | | **292 行** |

**移除比例：** 35% (163/472)

---

### 前端 (`streamlit_oauth/frontend/main.js`)

**需要修改的部分：**

```javascript
// 移除前：需要判斷 OAuth vs PayPal
let redirect_uri = new URLSearchParams(authorization_url).get("redirect_uri")

if (redirect_uri) {
  // OAuth flow: check if redirected to redirect_uri
  shouldCapture = popup_url.startsWith(redirect_uri)
} else {
  // PayPal flow
  if (urlParams.has('token') && urlParams.has('PayerID')) {
    shouldCapture = true
  } else if (urlParams.has('token') && !urlParams.has('PayerID')) {
    isCancelled = true
  }
}

// 移除後：只保留 PayPal 邏輯
if (urlParams.has('token') && urlParams.has('PayerID')) {
  // Payment completed successfully
  shouldCapture = true
} else if (urlParams.has('token') && !urlParams.has('PayerID')) {
  // User cancelled on PayPal page
  isCancelled = true
}
```

**簡化效果：**
- 移除 `redirect_uri` 檢測
- 移除條件分支邏輯
- 程式碼更直觀

---

### 範例文件 (`examples/`)

**需要移除：**
- `bitbucket.py`
- `discord.py`
- `github.py`
- `google.py`
- `jira.py`
- `kinde.py`
- `notion.py`
- `yandex.py`

**保留：**
- `paypal_basic.py`

**移除比例：** 89% (8/9)

---

### 依賴 (`requirements.txt`)

**移除前：**
```txt
streamlit>=1.28.1
httpx-oauth==0.15.1  # 👈 移除
requests>=2.31.0
python-dotenv==1.0.1
```

**移除後：**
```txt
streamlit>=1.28.1
requests>=2.31.0
python-dotenv==1.0.1
```

---

### 測試文件

**需要移除：**
- `tests/test_oauth_component.py` - OAuth2 測試

**保留：**
- `test_paypal_component.py` - PayPal 測試
- `tests/test_internal.py` - 內部函數測試（如果有用到）

---

## 📝 執行步驟

### Phase 1: 準備工作

1. **建立備份分支**
   ```bash
   git checkout -b backup/with-oauth
   git push origin backup/with-oauth
   ```

2. **更新文檔**
   - 更新 README.md 移除 OAuth 說明
   - 更新所有文檔中的 OAuth 參考

### Phase 2: 移除 OAuth 程式碼

#### 2.1 後端清理

**streamlit_oauth/__init__.py**

```python
# 移除區塊 1: OAuth2 imports (行 13-20)
# 移除 httpx_oauth 相關 import

# 移除區塊 2: OAuth2 輔助函數 (行 48-70)
# 移除 _generate_state, _generate_pkce_pair

# 移除區塊 3: OAuth2Component 類別 (行 72-172)
# 完整移除 OAuth2Component

# 移除區塊 4: StreamlitOauthError (行 38-41)
# 只保留 PayPalError

# 移除區塊 5: 開發測試代碼 (行 442-472)
# 移除 OAuth2 測試代碼
```

**清理後的結構：**
```python
# Imports (精簡)
import os
import streamlit.components.v1 as components
import streamlit as st
import time
import requests
from typing import Optional, Dict, Any

# Component 定義
_RELEASE = True
if not _RELEASE:
    _payment_button = components.declare_component(...)
else:
    _payment_button = components.declare_component(...)

# Exception
class PayPalError(Exception):
    """Exception raised from PayPal operations."""

# Main Component
class PayPalComponent:
    # ... PayPal 實作
```

#### 2.2 前端簡化

**streamlit_oauth/frontend/main.js**

```javascript
// 移除 redirect_uri 檢測邏輯
// 簡化為純 PayPal 流程

button.onclick = async () => {
  const popup = window.open(authorization_url, "paypalWidget", ...)

  let qs = await new Promise((resolve, reject) => {
    // Set 5-minute timeout for PayPal
    let timeoutId = setTimeout(() => {
      if (!popup.closed) popup.close()
      clearInterval(interval)
      resolve({cancelled: true, reason: 'timeout'})
    }, 300000)

    const interval = setInterval(() => {
      try {
        // Detect popup closed
        if (popup.closed) {
          clearInterval(interval)
          clearTimeout(timeoutId)
          return resolve({cancelled: true, reason: 'user_closed'})
        }

        let urlParams = new URLSearchParams(popup.location.search)

        // PayPal success
        if (urlParams.has('token') && urlParams.has('PayerID')) {
          popup.close()
          clearInterval(interval)
          clearTimeout(timeoutId)
          let result = {}
          for(let pairs of urlParams.entries()) {
            result[pairs[0]] = pairs[1]
          }
          return resolve(result)
        }

        // PayPal cancelled
        if (urlParams.has('token') && !urlParams.has('PayerID')) {
          popup.close()
          clearInterval(interval)
          clearTimeout(timeoutId)
          return resolve({
            cancelled: true,
            reason: 'user_cancelled',
            token: urlParams.get('token')
          })
        }
      } catch (e) {
        if (e.name === "SecurityError") return
        return reject(e)
      }
    }, 1000)
  })

  Streamlit.setComponentValue(qs)
}
```

#### 2.3 移除範例文件

```bash
rm examples/bitbucket.py
rm examples/discord.py
rm examples/github.py
rm examples/google.py
rm examples/jira.py
rm examples/kinde.py
rm examples/notion.py
rm examples/yandex.py
```

#### 2.4 更新依賴

**requirements.txt**
```bash
# 移除 httpx-oauth==0.15.1
```

**setup.py**
```python
install_requires=[
    "streamlit>=1.28.1",
    "requests>=2.31.0",
    "python-dotenv==1.0.1"
]
```

### Phase 3: 重新命名（可選）

考慮重新命名套件為 `streamlit-paypal`：

1. **套件名稱**
   - `streamlit_oauth` → `streamlit_paypal`

2. **Component 名稱**
   - `authorize_button` → `payment_button`

3. **目錄結構**
   ```
   streamlit_oauth/     →  streamlit_paypal/
   ├── __init__.py          ├── __init__.py
   └── frontend/            └── frontend/
   ```

### Phase 4: 測試

1. **單元測試**
   ```bash
   python test_paypal_component.py
   ```

2. **範例應用**
   ```bash
   streamlit run examples/paypal_basic.py
   ```

3. **完整測試**
   - 付款成功
   - 付款取消
   - 超時
   - 錯誤處理

### Phase 5: 文檔更新

1. **README.md**
   - 移除 OAuth2 說明
   - 更新範例代碼
   - 更新安裝指引

2. **docs/**
   - 更新所有文檔移除 OAuth 參考
   - 更新 API 文檔

3. **setup.py**
   - 更新描述
   - 更新關鍵字

---

## 📊 移除效果預估

### 程式碼減少

| 檔案 | 移除前 | 移除後 | 減少 |
|------|-------|-------|------|
| `__init__.py` | 472 行 | ~309 行 | -163 行 (35%) |
| `main.js` | ~100 行 | ~80 行 | -20 行 (20%) |
| **總計** | **~572 行** | **~389 行** | **-183 行 (32%)** |

### 依賴減少

| 依賴 | 移除前 | 移除後 |
|------|-------|-------|
| Python 套件 | 4 個 | 3 個 |
| `httpx-oauth` | ✅ | ❌ |

### 範例文件

| 項目 | 移除前 | 移除後 |
|------|-------|-------|
| 範例數量 | 9 個 | 1 個 |
| 維護負擔 | 高 | 低 |

### 維護性

| 面向 | 移除前 | 移除後 |
|------|-------|-------|
| **程式碼複雜度** | 中等 | 低 |
| **兼容邏輯** | 需要 | 不需要 |
| **測試範圍** | OAuth + PayPal | 只有 PayPal |
| **文檔維護** | 雙重 | 單一 |

---

## ⚠️ 風險與注意事項

### 1. 破壞性變更

**風險：** 如果有用戶在使用 OAuth2Component

**緩解：**
- 先建立備份分支
- 發布為新的 major version (2.0.0)
- 在 README 中明確說明

### 2. 套件重新命名

**風險：** PyPI 套件名稱變更

**緩解：**
- 可以先不重新命名，只移除功能
- 或發布為全新套件 `streamlit-paypal`
- 在舊套件說明中指向新套件

### 3. 現有用戶

**風險：** 使用 OAuth 功能的用戶無法升級

**緩解：**
- v1.x 保留 OAuth 功能（停止更新）
- v2.x 只有 PayPal 功能（新功能）
- 明確的遷移指南

---

## 🗺️ 執行方式

### ✅ 選擇的方案：A + C 組合

**激進移除 + 新套件命名**

因為這是一個獨立專案（fork），所以可以：
1. ✅ 完全移除所有 OAuth2 代碼（無需兼容）
2. ✅ 重新命名為 `streamlit-paypal`
3. ✅ 作為全新套件發布（v1.0.0）

**優點：**
- ✅ 程式碼最乾淨
- ✅ 命名準確（streamlit-paypal）
- ✅ 無向後兼容包袱
- ✅ 定位明確（純 PayPal 付款）

**無缺點：**
- ❌ 不存在破壞性變更問題（因為是新套件）
- ❌ 不需要遷移指南（因為沒有舊用戶）

---

## ✅ 執行檢查清單

### Phase 1: 移除 OAuth2 代碼 ✅ (完成於 commit 5ef783e)
- [x] 移除 OAuth2 imports (`httpx_oauth`)
- [x] 移除 OAuth2 輔助函數 (`_generate_state`, `_generate_pkce_pair`)
- [x] 移除 OAuth2Component 類別（完整）
- [x] 移除 StreamlitOauthError（保留 PayPalError）
- [x] 移除開發測試代碼（OAuth2 部分）
- [x] 簡化前端邏輯（移除 `redirect_uri` 檢測）
- [x] **移除 `redirect_uri` 參數**（從 `PayPalComponent.payment_button()` 方法）
- [x] **移除 `return_url` / `cancel_url` 設定**（從 `_create_order()` 方法）
- [x] 移除 OAuth 範例文件（8 個）
- [x] 移除 `httpx-oauth` 依賴

**成果：** 移除 692 行程式碼，所有測試通過 ✅

### Phase 2: 套件重新命名
- [ ] 重新命名目錄：`streamlit_oauth/` → `streamlit_paypal/`
- [ ] 更新 `setup.py` 套件名稱
- [ ] 更新 component 名稱：`authorize_button` → `payment_button`
- [ ] 更新所有 import 路徑
- [ ] 更新根目錄名稱（可選）

### Phase 3: 文檔更新
- [ ] 更新 README.md（移除 OAuth，更新套件名）
- [ ] 更新所有 docs/ 文檔
- [ ] 更新 setup.py 描述和關鍵字
- [ ] 添加致謝說明（fork 自 streamlit-oauth）

### Phase 4: 測試與發布
- [ ] 重新編譯前端 (`npm run build`)
- [ ] 執行單元測試
- [ ] 執行範例應用測試
- [ ] 更新版本號為 1.0.0（新套件起點）
- [ ] 提交並標記 tag v1.0.0
- [ ] 準備 PyPI 發布（可選）

---

## 📌 決策確認

**已確認：**

1. ✅ 移除 OAuth2 功能
2. ✅ 重新命名套件為 `streamlit-paypal`
3. ✅ 執行方式：A + C 組合
4. ✅ 版本號：1.0.0（新套件）
5. ✅ **移除 `redirect_uri` 參數**（PayPal popup 模式不需要）

**重要發現：**

- PayPal Orders API 的 `return_url` / `cancel_url` 在現代整合方式（popup/in-context）中是**可選的**
- 即使提供也會被忽略，因為 popup 流程不需要重導向
- PayPal 開發者儀表板也沒有設定 redirect URI 的地方
- 這簡化了我們的實作，使用者不需要設定 `PAYPAL_REDIRECT_URI` 環境變數

---

**文件版本：** v1.3
**最後更新：** 2025-10-02
**狀態：** 🚧 Phase 1 完成，進行中
