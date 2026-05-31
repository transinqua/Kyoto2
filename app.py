import os
import requests
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

app = Flask(__name__)

# === 🧩 請填入你的 LINE 憑證 ===
LINE_CHANNEL_ACCESS_TOKEN = 'LA56IiJpDkPywOMt7pWFbreOrETZFcEVFDGKLfgD9pPycdmJcUHH0kXN6nHExnmbeh05KyUzydjPfyjklkV5fdSLUmECuyzT110fDCdr3oJXGXxbwdxZK2tPBNhGwLN2Lub2xQdC+UcOXyRpdW6v8QdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = '58452e90d64df9eeb6dfa91e0d94a74d'
# ==================================

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def search_kyoto_travel(user_query):
    """ 旅遊資訊搜尋邏輯（與之前相同） """
    query = user_query.lower()
    if "景點" in query or "去哪" in query:
        return "🌸 京都必去景點推薦：\n1. 清水寺\n2. 伏見稻荷大社\n3. 金閣寺\n4. 嵐山"
    elif "美食" in query or "吃" in query:
        return "🍵 京都美食推薦：\n1. 錦市場\n2. 祇園 鰻魚飯\n3. 宇治抹茶\n4. 順正 豆腐料理"
    elif "交通" in query:
        return "🚌 京都交通指南：\n推薦購買「地下鐵・巴士一日券」，觀光最划算！"
    else:
        return f"針對您的問題「{user_query}」，建議可以先從清水寺或嵐山開始規劃喔！"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 當收到文字訊息時的處理邏輯
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text.strip() # 去除前後空白
    
    # 檢查是否在群組中被 @Tag 標籤
    is_mentioned = False
    if event.message.mention and event.message.mention.mentions:
        # 如果有 mentions 列表，代表有人被標籤
        is_mentioned = True

    # 💡 核心判斷邏輯：
    # 狀況 A：在 1 對 1 私訊中，一律回答。
    # 狀況 B：在群組中，必須符合「開頭是 !京都」或「被 @Tag 標籤」才回答。
    is_group = event.source.type in ['group', 'room']
    
    if is_group:
        if user_message.startswith("!京都"):
            # 移除開頭的 "!京都" 字樣，只留下後面的關鍵字（例如：將 "!京都 美食" 變成 " 美食"）
            clean_query = user_message[3:].strip() 
        elif is_mentioned:
            # 如果是被標籤，直接把整段話拿去查（LINE 的 tag 本身也會變成文字的一部分，AI 或關鍵字能辨識即可）
            clean_query = user_message
        else:
            # 如果在群組內，但既沒輸入關鍵字也沒被 Tag，就直接「已讀不回」，不浪費 Token
            return
    else:
        # 1 對 1 私訊，直接當作查詢字串
        clean_query = user_message

    # 如果使用者只打了 "!京都" 卻沒輸入內容，給予防呆提示
    if not clean_query:
        reply_content = "請在 `!京都` 後面加上你想查詢的內容喔！例如：`!京都 美食`"
    else:
        # 呼叫搜尋函數
        reply_content = search_kyoto_travel(clean_query)

    # 回傳訊息
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_content)]
            )
        )

if __name__ == "__main__":
    app.run(port=5000)
