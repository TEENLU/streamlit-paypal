# 測試指南

## 🧪 測試流程

### 方法一：本地開發模式測試（推薦用於開發）

#### 1. 安裝開發依賴

```bash
# 在專案根目錄
pip install -e .
```

這會以「可編輯模式」安裝套件，任何代碼修改都會立即生效。

#### 2. 設定環境變數

```bash
# 複製範例檔案
cp .env.example .env

# 編輯 .env 填入你的 PayPal Sandbox 憑證
# PAYPAL_CLIENT_ID=你的_sandbox_client_id
# PAYPAL_CLIENT_SECRET=你的_sandbox_client_secret
```

**取得 PayPal Sandbox 憑證：**
1. 前往 https://developer.paypal.com/dashboard/applications
2. 登入你的 PayPal 開發者帳號
3. 點擊 "Create App" 或選擇現有應用
4. 複製 "Sandbox" 標籤下的 Client ID 和 Secret

#### 3. 執行單元測試

```bash
# 測試核心功能（不需要真實憑證）
python test_paypal_component.py
```

**預期輸出：**
```
🚀 PayPalComponent Test Suite
============================================================
🧪 Test 1: Component Initialization
  ✅ Sandbox mode initialized correctly
  ✅ Production mode initialized correctly
  ✅ Invalid mode rejected correctly
✅ Test 1 passed
...
🎉 All tests passed!
```

#### 4. 執行範例應用

```bash
# 啟動 Streamlit 應用
streamlit run examples/paypal_basic.py
```

#### 5. 測試付款流程

1. 瀏覽器會自動開啟 `http://localhost:8501`
2. 輸入金額和幣別
3. 點擊「Pay」按鈕
4. 會彈出 PayPal Sandbox 付款頁面
5. 使用 PayPal Sandbox 測試帳號登入並完成付款
6. 完成後應該會看到付款成功訊息

**取得 PayPal Sandbox 測試帳號：**
- 前往 https://developer.paypal.com/dashboard/accounts
- 使用「Sandbox」標籤下的測試買家帳號（Personal Account）

---

### 方法二：前端開發模式（修改 JavaScript 時使用）

如果你需要修改前端代碼（`streamlit_oauth/frontend/main.js`）：

#### 1. 設定開發模式

編輯 `streamlit_oauth/__init__.py`：

```python
_RELEASE = False  # 改為 False
```

#### 2. 啟動前端開發伺服器

```bash
cd streamlit_oauth/frontend
npm install
npm run dev
```

這會啟動 Vite 開發伺服器在 `http://localhost:3000`

#### 3. 在另一個終端執行 Streamlit

```bash
# 在專案根目錄
streamlit run examples/paypal_basic.py --server.enableCORS=false
```

#### 4. 前端修改會即時生效

修改 `main.js` 後，Streamlit 會自動重新載入。

---

### 方法三：打包測試（測試發布前）

#### 1. 建立 distribution

```bash
# 安裝打包工具
pip install build twine

# 建立 distribution
python -m build
```

#### 2. 本地安裝測試

```bash
# 從本地安裝
pip install dist/streamlit_oauth-*.whl

# 測試
python -c "from streamlit_paypal import PayPalComponent; print('✅ Import successful')"
```

#### 3. 測試應用

```bash
streamlit run examples/paypal_basic.py
```

---

## 📋 測試檢查清單

### 功能測試

- [ ] **單元測試通過**
  ```bash
  python test_paypal_component.py
  ```

- [ ] **組件初始化**
  - [ ] Sandbox 模式正確設定
  - [ ] Production 模式正確設定
  - [ ] 無效模式被拒絕

- [ ] **付款流程**
  - [ ] 按鈕正確顯示
  - [ ] 點擊後彈出 PayPal 視窗
  - [ ] PayPal Sandbox 頁面正確載入
  - [ ] 完成付款後視窗關閉
  - [ ] 付款結果正確回傳
  - [ ] Session state 正確更新

- [ ] **錯誤處理**
  - [ ] 無效憑證顯示錯誤訊息
  - [ ] 取消付款正確處理
  - [ ] 網路錯誤正確處理

- [ ] **安全性**
  - [ ] Client Secret 不出現在前端
  - [ ] CSRF 保護有效（unknown order 被拒絕）
  - [ ] 過期訂單被拒絕（>5分鐘）

### UI/UX 測試

- [ ] **按鈕樣式**
  - [ ] 自訂圖示顯示正確
  - [ ] `use_container_width` 參數有效
  - [ ] 按鈕文字正確顯示

- [ ] **多幣別支援**
  - [ ] USD 正常運作
  - [ ] EUR 正常運作
  - [ ] TWD 正常運作
  - [ ] 其他幣別正常運作

- [ ] **付款結果顯示**
  - [ ] Order ID 正確顯示
  - [ ] Payer 資訊正確顯示
  - [ ] 金額正確顯示

### 效能測試

- [ ] **載入時間**
  - [ ] 組件初始化 < 1 秒
  - [ ] 訂單創建 < 2 秒
  - [ ] 訂單捕獲 < 2 秒

- [ ] **並發測試**
  - [ ] 多個用戶同時付款
  - [ ] Session state 正確隔離

---

## 🐛 常見問題排查

### 問題 1：`ImportError: No module named 'streamlit_oauth'`

**解決方案：**
```bash
pip install -e .
```

### 問題 2：`PayPalError: Failed to get access token: 401 Unauthorized`

**原因：** Client ID 或 Secret 錯誤

**解決方案：**
1. 檢查 `.env` 檔案中的憑證
2. 確認使用的是 Sandbox 憑證（非 Production）
3. 重新從 PayPal Dashboard 複製憑證

### 問題 3：Popup 視窗不關閉

**原因：** 可能是 redirect URI 問題或前端檢測邏輯問題

**解決方案：**
1. 檢查瀏覽器控制台（F12）是否有錯誤
2. 確認 PayPal 回調 URL 包含 `token` 和 `PayerID` 參數
3. 檢查 `main.js` 的檢測邏輯

### 問題 4：`PayPalError: Unknown order ID - possible CSRF attack`

**原因：** Session state 被清除或訂單過期

**解決方案：**
1. 確認在 5 分鐘內完成付款
2. 不要在付款過程中重新整理頁面
3. 檢查 Streamlit session state 是否正常運作

### 問題 5：前端修改不生效

**解決方案：**
```bash
# 如果使用開發模式
cd streamlit_oauth/frontend
npm run build

# 如果使用 release 模式，需要重新打包
cd ../..
pip install -e .
```

---

## 📊 測試報告範例

測試完成後，可以記錄以下資訊：

```markdown
## 測試報告

**測試日期：** 2025-10-01
**測試環境：**
- OS: macOS 14.2
- Python: 3.9.18
- Streamlit: 1.28.1
- 瀏覽器: Chrome 120.0

**測試結果：**
- ✅ 單元測試：5/5 通過
- ✅ 付款流程：正常
- ✅ 錯誤處理：正常
- ✅ 安全性：CSRF 和過期檢查有效
- ✅ UI/UX：按鈕和結果顯示正常

**效能指標：**
- 組件初始化：0.5 秒
- 訂單創建：1.2 秒
- 訂單捕獲：1.5 秒

**已知問題：** 無

**建議：** 可以發布測試版本
```

---

## 🚀 下一步

測試通過後，你可以：

1. **發布到 PyPI**
   ```bash
   python -m build
   twine upload dist/*
   ```

2. **建立 GitHub Repository**
   ```bash
   git remote add origin https://github.com/your-username/streamlit-paypal.git
   git push -u origin main
   ```

3. **撰寫使用文檔**
   - 更新 README.md
   - 新增更多範例
   - 建立 GitHub Pages

4. **收集使用者回饋**
   - 在 Streamlit 社群分享
   - 收集 issues 和 feature requests
