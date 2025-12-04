from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from datetime import datetime

app = Flask(__name__)

# 環境変数から取得
line_bot_api = LineBotApi(os.environ.get('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('CHANNEL_SECRET'))

# テスト用のゴミ出しスケジュール
GARBAGE_SCHEDULE = {
    '橘通': {
        '燃えるゴミ': ['月', '木'],
        '資源ゴミ': ['水'],
        'ペットボトル': ['金']
    },
    '大橋': {
        '燃えるゴミ': ['火', '金'],
        '資源ゴミ': ['木'],
        'ペットボトル': ['水']
    }
}

def get_weekday_name():
    """今日の曜日を取得"""
    weekdays = ['月', '火', '水', '木', '金', '土', '日']
    return weekdays[datetime.now().weekday()]

def get_today_garbage(district):
    """今日のゴミを取得"""
    if district not in GARBAGE_SCHEDULE:
        return None
    
    today = get_weekday_name()
    schedule = GARBAGE_SCHEDULE[district]
    garbage_list = []
    
    for garbage_type, days in schedule.items():
        if today in days:
            garbage_list.append(garbage_type)
    
    if garbage_list:
        return f"今日({today}曜日)は\n{'、'.join(garbage_list)}\nの日です🗑️"
    else:
        return f"今日({today}曜日)はゴミ出しの日ではありません"

@app.route("/")
def hello():
    return "ゴミ出しBotが動いています!"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    
    # 地区名チェック
    if '橘通' in text or '大橋' in text:
        district = '橘通' if '橘通' in text else '大橋'
        
        if '今日' in text or 'きょう' in text:
            reply = get_today_garbage(district)
            if reply is None:
                reply = "その地区は登録されていません"
        else:
            # スケジュール表示
            schedule = GARBAGE_SCHEDULE[district]
            reply = f"{district}地区のゴミ出しスケジュール:\n"
            for g_type, days in schedule.items():
                reply += f"・{g_type}: {', '.join(days)}曜日\n"
    else:
        reply = "地区名を教えてください\n例: 橘通の今日のゴミは?"
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
