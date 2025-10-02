# Manual Testing Guide - Cancellation Handling

**測試日期：** 2025-10-01
**測試版本：** v1.1 (含取消處理)

---

## 📋 測試檢查清單

### 情境 1：用戶在 PayPal 頁面點擊取消 ✅

**測試步驟：**
1. 開啟 `http://localhost:8502`
2. 設定金額 $10.00 USD
3. 點擊「Pay $10.00 USD」按鈕
4. PayPal popup 開啟後，點擊「Cancel and return to...」連結
5. 觀察結果

**預期行為：**
- ✅ Popup 自動關閉
- ✅ 顯示訊息：「⚠️ You cancelled the payment on PayPal」
- ✅ 顯示「🔄 Retry Payment」按鈕
- ✅ Backend 清理 `st.session_state.paypal_pending_orders`
- ✅ 記錄到 `st.session_state.cancelled_payments`（reason: `user_cancelled`）

**實際結果：**
[x] 通過

**備註：**
- 2025-10-02: 用戶測試通過 ✅
- PayPal 頁面取消按鈕正常運作
- 訊息正確顯示


---

### 情境 2：用戶手動關閉 Popup ✅

**測試步驟：**
1. 開啟 `http://localhost:8502`
2. 設定金額 $10.00 USD
3. 點擊「Pay $10.00 USD」按鈕
4. PayPal popup 開啟後，直接關閉視窗（點 X 或按 ESC）
5. 觀察結果

**預期行為：**
- ✅ Streamlit 檢測到 popup 關閉
- ✅ 顯示訊息：「⚠️ Payment window was closed」
- ✅ 顯示「🔄 Retry Payment」按鈕
- ✅ Backend 清理 pending order
- ✅ 記錄到 cancelled_payments（reason: `user_closed`）

**實際結果：**
[x] 通過

**備註：**
- 2025-10-02: 用戶測試通過 ✅
- Popup 關閉檢測正常
- 訊息正確顯示
- **Bug 修復：** Retry 按鈕現在會清除取消狀態


---

### 情境 3：付款超時（5 分鐘） ⏱

**測試步驟：**
1. 開啟 `http://localhost:8502`
2. 設定金額 $10.00 USD
3. 點擊「Pay $10.00 USD」按鈕
4. PayPal popup 開啟後，**不做任何操作**
5. 等待 5 分鐘
6. 觀察結果

**預期行為：**
- ✅ 5 分鐘後 popup 自動關閉
- ✅ 顯示訊息：「⚠️ Payment timed out (exceeded 5 minutes)」
- ✅ 顯示「🔄 Retry Payment」按鈕
- ✅ Backend 清理 pending order
- ✅ 記錄到 cancelled_payments（reason: `timeout`）

**實際結果：**
[x] 通過

**備註：**
- 2025-10-02: 用戶測試通過 ✅
- 5 分鐘超時機制正常運作
- Popup 自動關閉
- 訊息正確顯示


---

### 情境 4：成功付款（驗證未受影響） ✅

**測試步驟：**
1. 開啟 `http://localhost:8502`
2. 設定金額 $10.00 USD
3. 點擊「Pay $10.00 USD」按鈕
4. 在 PayPal 頁面完成付款
5. 觀察結果

**預期行為：**
- ✅ 付款成功
- ✅ 顯示「🎉 Payment Successful!」
- ✅ 顯示訂單資訊（Order ID, Status, Payer, Amount）
- ✅ **不顯示取消訊息**
- ✅ Backend 正常捕獲訂單並清理 pending order

**實際結果：**
[x] 通過

**備註：**
- 2025-10-02: 用戶測試通過 ✅
- 訂單 ID: 69Y8080736191525L
- 狀態: COMPLETED
- 金額: $10.00 USD
- 手續費: $0.84
- 實收: $9.16
- 取消處理功能不影響正常付款流程


---

## 🔍 檢查項目

### Backend 狀態檢查

**檢查 `st.session_state.paypal_pending_orders`：**
```python
# 在 Streamlit app 中添加臨時 debug
with st.expander("🔍 Debug: Pending Orders"):
    st.json(st.session_state.get('paypal_pending_orders', {}))
```

**預期：**
- 取消後應為空 `{}`
- 付款成功後應為空 `{}`

---

### Frontend 控制台檢查

**開啟瀏覽器開發者工具（F12）**

**檢查項目：**
1. 點擊付款按鈕時，console 應顯示：
   ```
   authorization_url: https://www.sandbox.paypal.com/checkoutnow?token=XXX
   ```

2. 取消時，component 應返回：
   ```javascript
   {cancelled: true, reason: "user_cancelled", token: "XXX"}
   ```

3. 成功付款時，component 應返回：
   ```javascript
   {token: "XXX", PayerID: "YYY"}
   ```

---

## 📊 測試結果統計

| 情境 | 狀態 | 原因檢測 | UI 反饋 | State 清理 | Retry 功能 |
|------|------|---------|---------|-----------|-----------|
| 1. PayPal 取消 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 2. 手動關閉 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 3. 超時 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 4. 成功付款 | ✅ | N/A | ✅ | ✅ | N/A |

---

## 🐛 已知問題

### 問題 1: Retry 按鈕未清除取消狀態 ❌ → ✅ 已修復

**發現日期：** 2025-10-02
**狀態：** ✅ 已修復

**問題描述：**
- 點擊 Retry Payment 按鈕後，取消訊息仍然顯示
- 原因：component 的 result 被快取，未正確清除狀態

**修復方式：**
- 將取消結果存入 `st.session_state.last_cancellation`
- Retry 按鈕點擊時刪除 `last_cancellation` 並 rerun
- 只在無 pending cancellation 時顯示付款按鈕

**提交：** commit 待提交

---

## ✅ 測試簽核

**測試人員：** 用戶（lvdeen）
**測試日期：** 2025-10-02
**測試結果：** [x] 全部通過
**備註：**
- 所有 4 個情境測試通過
- 發現並修復 Retry 按鈕 bug
- 功能完整且穩定
