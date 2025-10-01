# PayPal Payment Cancellation Handling Design

**日期：** 2025-10-01
**版本：** v1.0
**狀態：** 設計階段（待決定是否實作）

---

## 📋 問題說明

### 當前行為

**用戶取消付款時：**
1. PayPal 返回 cancel URL：`?token=XXX`（沒有 `PayerID` 參數）
2. 前端偵測邏輯：`urlParams.has('token') && urlParams.has('PayerID')` → `false`
3. Popup 不會自動關閉，interval 繼續等待
4. 用戶手動關閉 popup 後，component 返回 `null`
5. Streamlit 端：`result = None`，不觸發任何邏輯

**這是正常行為：**
- ✅ 沒有成功付款 = 沒有返回值 = 頁面保持原狀
- ✅ 不會有意外的狀態變化
- ❌ 但 UX 不夠明確，用戶不知道取消是否成功

---

## 🎯 方案對比

### 方案 1：維持現狀

**實作內容：** 不做任何修改

**優點：**
- ✅ 零開發成本
- ✅ 簡單、符合直覺（沒付款就什麼都不發生）
- ✅ 不引入新的複雜性

**缺點：**
- ❌ Popup 需要用戶手動關閉（UX 不佳）
- ❌ 無法區分「取消」、「超時」、「錯誤」
- ❌ 無法追蹤取消行為分析
- ❌ Session 狀態污染（pending order 留存 5 分鐘）

**適用情境：**
- 簡單的 MVP 專案
- 不需要分析付款行為
- 資源有限，無法投入開發

---

### 方案 2：自動偵測關閉

**實作內容：** 檢測 `popup.closed`，自動返回 `null`

**前端修改：**
```javascript
const interval = setInterval(() => {
  // 檢測 popup 手動關閉
  if (popup.closed) {
    clearInterval(interval)
    return resolve(null)
  }

  // ... 原有邏輯
}, 1000)
```

**優點：**
- ✅ 開發成本低（約 5 行程式碼）
- ✅ 自動清理 interval（節省資源）
- ✅ Popup 關閉後立即返回控制權

**缺點：**
- ❌ 無法區分「取消」和「手動關閉」
- ❌ 仍然返回 `null`，無法提供反饋
- ❌ 無法清理 pending order（依然依賴 5 分鐘過期）

**適用情境：**
- 快速改進 UX
- 不需要詳細的取消原因

---

### 方案 3：完整取消處理 ⭐

**實作內容：** 完整檢測取消狀態，返回詳細資訊

#### 前端修改 (`main.js`)

**新增功能：**
1. 檢測三種取消情境：用戶取消、手動關閉、超時
2. 返回 `{cancelled: true, reason: '...', token: '...'}` 物件
3. 添加 5 分鐘超時機制

**程式碼：**
```javascript
button.onclick = async () => {
  const popup = window.open(authorization_url, "oauthWidget", ...)

  let qs = await new Promise((resolve, reject) => {
    let timeoutId = null

    // 設置 5 分鐘超時（與後端一致）
    if (!redirect_uri) {  // PayPal flow only
      timeoutId = setTimeout(() => {
        if (!popup.closed) popup.close()
        clearInterval(interval)
        resolve({cancelled: true, reason: 'timeout'})
      }, 300000)
    }

    const interval = setInterval(() => {
      try {
        // 檢測 popup 手動關閉
        if (popup.closed) {
          clearInterval(interval)
          if (timeoutId) clearTimeout(timeoutId)
          return resolve({cancelled: true, reason: 'user_closed'})
        }

        let redirect_uri = new URLSearchParams(authorization_url).get("redirect_uri")
        let popup_url = (new URL(popup.location.href)).toString()
        let urlParams = new URLSearchParams(popup.location.search)

        let shouldCapture = false
        let isCancelled = false

        if (redirect_uri) {
          // OAuth flow (不變)
          shouldCapture = popup_url.startsWith(redirect_uri)
        } else {
          // PayPal flow
          if (urlParams.has('token') && urlParams.has('PayerID')) {
            // 成功完成付款
            shouldCapture = true
          } else if (urlParams.has('token') && !urlParams.has('PayerID')) {
            // 用戶在 PayPal 頁面點擊取消
            isCancelled = true
          }
        }

        // 處理取消
        if (isCancelled) {
          popup.close()
          clearInterval(interval)
          if (timeoutId) clearTimeout(timeoutId)
          return resolve({
            cancelled: true,
            reason: 'user_cancelled',
            token: urlParams.get('token')  // 包含 order ID 用於清理
          })
        }

        if (!shouldCapture) return

        // 成功捕獲
        popup.close()
        clearInterval(interval)
        if (timeoutId) clearTimeout(timeoutId)

        let result = {}
        for(let pairs of urlParams.entries()) {
          result[pairs[0]] = pairs[1]
        }
        return resolve(result)

      } catch (e) {
        if (e.name === "SecurityError") return
        return reject(e)
      }
    }, 1000)
  })

  Streamlit.setComponentValue(qs)
}
```

#### 後端修改 (`__init__.py`)

**新增功能：**
1. 檢測 `result.get('cancelled')`
2. 清理 pending order（立即清理，不等 5 分鐘）
3. 返回取消資訊給應用層

**程式碼：**
```python
def payment_button(
    self,
    name: str,
    amount: float,
    currency: str = 'USD',
    redirect_uri: str = None,
    description: str = '',
    key: Optional[str] = None,
    icon: Optional[str] = None,
    use_container_width: bool = False,
    popup_height: int = 800,
    popup_width: int = 600
) -> Optional[Dict[str, Any]]:
    """
    Render PayPal payment button with popup checkout flow.

    Returns:
      - Payment result dict if successful
      - Cancellation dict if cancelled: {'cancelled': True, 'reason': '...', 'order_id': '...'}
      - None if pending
    """
    # Create order on backend (secure)
    order = self._create_order(
        amount=amount,
        currency=currency,
        description=description,
        return_url=redirect_uri,
        cancel_url=redirect_uri
    )

    # Get approval URL from order links
    approval_url = None
    for link in order.get('links', []):
        if link.get('rel') in ['approve', 'payer-action']:
            approval_url = link.get('href')
            break

    if not approval_url:
        raise PayPalError(f"No approval URL in order response. Links: {order.get('links')}")

    # Call frontend component
    result = _authorize_button(
        authorization_url=approval_url,
        name=name,
        popup_height=popup_height,
        popup_width=popup_width,
        key=key,
        icon=icon,
        use_container_width=use_container_width,
        auto_click=False
    )

    # Process result from popup
    if result:
        try:
            # ============ 新增：檢查取消狀態 ============
            if result.get('cancelled'):
                # 清理被取消的訂單
                order_id = result.get('token')
                if order_id and order_id in st.session_state.paypal_pending_orders:
                    del st.session_state.paypal_pending_orders[order_id]

                # 返回取消資訊
                return {
                    'cancelled': True,
                    'reason': result.get('reason', 'unknown'),
                    'order_id': order_id
                }
            # ========================================

            # 檢查錯誤
            if 'error' in result:
                raise PayPalError(result)

            # 處理成功付款 (原有邏輯)
            if 'token' in result and 'PayerID' in result:
                order_id = result['token']
                captured = self._capture_order(order_id)

                return {
                    'order_id': order_id,
                    'status': captured.get('status'),
                    'payer': captured.get('payer'),
                    'purchase_units': captured.get('purchase_units'),
                    'captured': captured
                }

        except PayPalError:
            raise
        except Exception as e:
            raise PayPalError(f"Unexpected error: {str(e)}")

    return None
```

#### 應用層使用 (`examples/paypal_basic.py`)

**新增功能：** 顯示取消訊息，記錄取消行為

```python
if 'payment' not in st.session_state:
    st.info("👇 點擊按鈕開始付款")

    try:
        result = paypal.payment_button(
            name=f"Pay ${amount} {currency}",
            amount=amount,
            currency=currency,
            redirect_uri=PAYPAL_REDIRECT_URI,
            description=description,
            key='payment_btn',
            use_container_width=True
        )

        if result:
            # ============ 新增：檢查取消狀態 ============
            if result.get('cancelled'):
                # 顯示取消訊息
                reason_map = {
                    'user_cancelled': '您已在 PayPal 頁面取消付款',
                    'user_closed': '付款視窗已關閉',
                    'timeout': '付款超時（超過 5 分鐘）'
                }
                reason = reason_map.get(result['reason'], '付款未完成')
                st.warning(f"⚠️ {reason}")

                # 可選：記錄取消行為（用於分析）
                if 'cancelled_payments' not in st.session_state:
                    st.session_state.cancelled_payments = []
                st.session_state.cancelled_payments.append({
                    'order_id': result.get('order_id'),
                    'reason': result['reason'],
                    'timestamp': time.time(),
                    'amount': amount,
                    'currency': currency
                })

                # 顯示重試按鈕
                if st.button("🔄 重試付款"):
                    st.rerun()
            # ========================================
            else:
                # 成功付款 (原有邏輯)
                st.session_state.payment = result
                st.rerun()

    except PayPalError as e:
        st.error(f"❌ 付款失敗：{str(e)}")
    except Exception as e:
        st.error(f"❌ 未預期的錯誤：{str(e)}")

else:
    # 顯示付款成功資訊 (原有邏輯)
    payment = st.session_state.payment
    st.success("🎉 付款成功！")
    # ...
```

### 方案 3 優點

**UX 改進：**
- ✅ 明確的狀態反饋（三種取消原因）
- ✅ 自動關閉 popup（無需用戶手動操作）
- ✅ 超時保護（5 分鐘自動關閉）
- ✅ 提供重試按鈕（引導用戶繼續）

**工程改進：**
- ✅ 立即清理 session 狀態（不等 5 分鐘）
- ✅ 可記錄取消行為（用於分析和優化）
- ✅ 完整的狀態管理（成功/取消/錯誤）

**分析價值：**
- ✅ 追蹤取消率（user_cancelled / total_attempts）
- ✅ 識別問題（timeout 多 = 流程太慢）
- ✅ 優化轉換率（分析取消原因）

### 方案 3 缺點

**開發成本：**
- 🔧 前端修改：約 40 行程式碼
- 🔧 後端修改：約 15 行程式碼
- 🔧 範例更新：約 20 行程式碼
- 🔧 測試：需測試三種取消情境
- ⏱ 估計工時：1-2 小時

**複雜性增加：**
- 🔧 新增返回狀態（`cancelled`）需文件說明
- 🔧 應用層需處理取消邏輯

---

## 📊 改進效果對比

| 項目 | 方案 1 (現狀) | 方案 2 (自動關閉) | 方案 3 (完整處理) ⭐ |
|------|-------------|-----------------|-------------------|
| **取消檢測** | ❌ 無法識別 | ✅ 檢測關閉 | ✅ 三種原因 |
| **Session 清理** | 🟡 5分鐘後 | 🟡 5分鐘後 | ✅ 立即清理 |
| **UX 反饋** | ❌ 無提示 | ❌ 無提示 | ✅ 明確訊息 |
| **超時處理** | ❌ 無限等待 | ❌ 無限等待 | ✅ 5分鐘自動關閉 |
| **分析追蹤** | ❌ 無記錄 | ❌ 無記錄 | ✅ 可記錄取消行為 |
| **開發成本** | ✅ 0 | ✅ 5 行 | 🟡 75 行 |
| **複雜度** | ✅ 最低 | ✅ 低 | 🟡 中 |

---

## 🎯 建議決策

### 推薦方案：方案 3（完整取消處理）⭐

**理由：**

1. **UX 顯著改善：** 用戶體驗從「不知道發生什麼」變成「明確的狀態反饋」
2. **工程價值：** 解決實際的狀態管理問題（session 清理）
3. **分析價值：** 可追蹤取消行為，優化轉換率
4. **開發成本可接受：** 約 1-2 小時，一次性投入

**適用情境：**
- ✅ 重視 UX 的產品
- ✅ 需要分析付款行為
- ✅ 有時間投入開發（1-2 小時）

### 替代方案：方案 1（維持現狀）

**適用情境：**
- ✅ MVP 階段，快速驗證商業模式
- ✅ 資源有限，無法投入開發
- ✅ 付款流程不是核心功能

---

## 📝 實作檢查清單

**如果決定實作方案 3，需完成以下項目：**

### 前端 (`main.js`)
- [ ] 添加 popup 關閉檢測
- [ ] 添加超時機制（5 分鐘）
- [ ] 檢測取消參數（token 但無 PayerID）
- [ ] 返回 `{cancelled: true, reason, token}` 物件
- [ ] 測試三種取消情境

### 後端 (`__init__.py`)
- [ ] 檢測 `result.get('cancelled')`
- [ ] 清理 pending order
- [ ] 返回取消資訊
- [ ] 更新 docstring（說明返回值）
- [ ] 添加單元測試

### 範例 (`paypal_basic.py`)
- [ ] 顯示取消訊息
- [ ] 添加重試按鈕
- [ ] 可選：記錄取消行為
- [ ] 更新註解

### 文件
- [ ] 更新 `README_PAYPAL.md`（說明取消處理）
- [ ] 更新 `TESTING_GUIDE.md`（添加取消測試）
- [ ] 更新 `PAYPAL_DESIGN.md`（更新測試計劃）

### 測試
- [ ] 用戶在 PayPal 頁面點擊取消
- [ ] 用戶手動關閉 popup
- [ ] 付款超時（等待 5 分鐘）
- [ ] 驗證 pending order 被清理
- [ ] 驗證取消訊息正確顯示

---

## 🔗 相關文件

- `SECURITY_AUDIT.md` - 安全審查報告
- `PAYPAL_DESIGN.md` - PayPal 整合設計
- `README_PAYPAL.md` - 使用指南
- `TESTING_GUIDE.md` - 測試指南

---

**文件版本：** v1.0
**最後更新：** 2025-10-01
**決策狀態：** 待用戶決定
**預計工時：** 1-2 小時（如選擇方案 3）
