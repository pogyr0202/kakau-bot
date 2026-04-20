import os
import requests

def send_line_message(message):
    """LINEにメッセージを送る"""
    url = "https://api.line.me/v2/bot/message/push"
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.environ.get("USER_ID")
    if not token or not user_id: return

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    payload = {"to": user_id, "messages": [{"type": "text", "text": message}]}
    requests.post(url, headers=headers, json=payload)

def get_rakuten_price(keyword):
    """楽天APIで最安値を取得"""
    app_id = os.environ.get("RAKUTEN_APP_ID")
    url = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706"
    params = {
        "applicationId": app_id,
        "keyword": keyword,
        "sort": "+itemPrice", # 安い順
        "hits": 1             # 1番上だけ
    }
    try:
        res = requests.get(url, params=params).json()
        if "Items" in res and res["Items"]:
            item = res["Items"][0]["Item"]
            price = item['itemPrice']
            link = item['itemUrl']
            return f"💰 ¥{price:,}\n🔗 {link}"
    except:
        pass
    return "❌ 楽天で価格が見つかりませんでした"

def main():
    # 🔍 ここに「欲しいもの」を書くだけ！
    items = ["iPhone15 128GB", "AirPods Pro 第2世代"]
    
    for name in items:
        price_info = get_rakuten_price(name)
        msg = f"📦 {name}\n{price_info}"
        print(f"送信中: {name}")
        send_line_message(msg)

if __name__ == "__main__":
    main()