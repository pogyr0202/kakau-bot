import asyncio
from playwright.async_api import async_playwright
import requests
import re

# --- 設定 ---
LINE_TOKEN = "h0rzXa015a+BtQAb3ilk1QU7y5S/caxq/LEJChcXK8eAWjhUxH4obxSPMioxAyyN71OAy7jpwyPFa+RWJ13ttYh7aUrnpe02rsA15YMGXx4Qdim85Qgd3/FO2MSHPIzPrUMeXaV9GIAguwlVuGBrpwdB04t89/1O/w1cDnyilFU="
USER_ID = "Uc078e7e043d026f4147503f4d8376cd4"

async def get_price_amazon(page, url):
    print("Amazonをチェック中...")
    try:
        await page.goto(url, wait_until="load", timeout=60000)
        await asyncio.sleep(5)
        price_element = await page.query_selector(".a-price-whole")
        if price_element:
            text = await price_element.inner_text()
            price = int("".join(filter(str.isdigit, text)))
            print(f"✅ Amazon成功: {price:,}円")
            return price
        return None
    except Exception as e:
        print(f"❌ Amazonエラー: {e}")
        return None

async def get_price_rakuten(page, url):
    print("楽天をチェック中...")
    try:
        await page.goto(url, wait_until="load", timeout=90000)
        await asyncio.sleep(8)
        await page.mouse.wheel(0, 700)
        await asyncio.sleep(3)
        content = await page.inner_text("body")
        price_matches = re.findall(r'(\d{1,3}(?:,\d{3})+)\s*円', content)
        if price_matches:
            prices = [int(p.replace(',', '')) for p in price_matches]
            valid_prices = [p for p in prices if p > 50000]
            price = valid_prices[0] if valid_prices else prices[0]
            print(f"✅ 楽天成功: {price:,}円")
            return price
        return None
    except Exception as e:
        print(f"❌ 楽天エラー: {e}")
        return None

def send_line(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Authorization": f"Bearer {LINE_TOKEN}", "Content-Type": "application/json"}
    data = {"to": USER_ID, "messages": [{"type": "text", "text": message}]}
    res = requests.post(url, headers=headers, json=data)
    if res.status_code == 200:
        print("📱 LINEに通知を送信しました！")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
        page = await context.new_page()
        
        # 1. Amazonチェック
        a_price = await get_price_amazon(page, "https://amzn.asia/d/0e9KiDic")
        
        # 2. 楽天チェック（修正箇所：引数を2つにしました）
        r_price = await get_price_rakuten(page, "https://item.rakuten.co.jp/dji-shop/setdji0000210/")
        
        msg = "🚀 価格パトロール報告\n\n"
        msg += f"🛒 楽天: {f'{r_price:,}円' if r_price else '取得失敗'}\n"
        msg += f"📦 Amazon: {f'{a_price:,}円' if a_price else '取得失敗'}\n\n"
        
        if r_price and a_price:
            if r_price == a_price:
                msg += "💡 両サイト同じ価格です。"
            else:
                cheaper = "楽天" if r_price < a_price else "Amazon"
                diff = abs(r_price - a_price)
                msg += f"🔥 {cheaper}の方が {diff:,}円 安いです！"
        
        send_line(msg)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())