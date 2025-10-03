#!/bin/bash

echo "🚀 PayPal Component 快速測試"
echo "================================"
echo ""

# 檢查 .env 檔案
if [ ! -f .env ]; then
    echo "⚠️  未找到 .env 檔案"
    echo "📝 正在建立 .env 範本..."
    cp .env.example .env
    echo ""
    echo "⚠️  請編輯 .env 檔案並填入你的 PayPal Sandbox 憑證："
    echo "   PAYPAL_CLIENT_ID=你的_client_id"
    echo "   PAYPAL_CLIENT_SECRET=你的_client_secret"
    echo ""
    echo "📖 取得憑證："
    echo "   1. 前往 https://developer.paypal.com/dashboard/applications"
    echo "   2. 登入並創建或選擇應用"
    echo "   3. 複製 Sandbox 標籤下的 Client ID 和 Secret"
    echo ""
    exit 1
fi

# 檢查憑證是否已填寫
if grep -q "your_sandbox_client_id_here" .env; then
    echo "⚠️  .env 檔案中的憑證尚未填寫"
    echo "📝 請編輯 .env 檔案並填入真實的 PayPal Sandbox 憑證"
    echo ""
    exit 1
fi

echo "✅ 找到 .env 檔案"
echo ""

# 步驟 1: 單元測試
echo "📋 步驟 1/3: 執行單元測試..."
echo "--------------------------------"
python test_paypal_component.py 2>&1 | grep -E "(🧪|✅|❌|🎉)" || {
    echo "❌ 單元測試失敗"
    exit 1
}
echo ""

# 步驟 2: 驗證導入
echo "📋 步驟 2/3: 驗證套件導入..."
echo "--------------------------------"
python -c "from streamlit_paypal import PayPalComponent; print('✅ PayPalComponent 導入成功')" 2>&1 | grep "✅" || {
    echo "❌ 導入失敗"
    exit 1
}
echo ""

# 步驟 3: 啟動測試應用
echo "📋 步驟 3/3: 啟動 Streamlit 測試應用..."
echo "--------------------------------"
echo ""
echo "🌐 瀏覽器即將開啟 http://localhost:8501"
echo ""
echo "📝 測試步驟："
echo "   1. 輸入金額（例如：10）"
echo "   2. 選擇幣別（例如：USD）"
echo "   3. 點擊付款按鈕"
echo "   4. 在彈出視窗登入 PayPal Sandbox 測試帳號"
echo "   5. 完成付款"
echo "   6. 驗證付款結果顯示"
echo ""
echo "🔑 PayPal Sandbox 測試帳號："
echo "   前往 https://developer.paypal.com/dashboard/accounts"
echo "   使用 Personal (買家) 帳號登入"
echo ""
echo "按 Ctrl+C 停止應用"
echo ""
echo "================================"
echo ""

streamlit run examples/paypal_basic.py
