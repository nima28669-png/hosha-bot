from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
import sqlite3, time, asyncio, logging, os, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
logging.basicConfig(level=logging.INFO)
print("BOT STARTED ON SERVER...")

TOKEN = "8974692488:AAFFr7XHkDcibKYuaRcsMEIqd33WlvaQSms"
BOT_USERNAME = "HoshaStationBot"
WEBAPP_URL = "https://phenomenal-frangollo-3a9343.netlify.app/"
CHANNEL = "@HoshaChannel"
ADMIN_ID = 7902082956
TOKEN_NAME = "HOSHA"
FARM_TIME = 8 * 3600
FARM_REWARD = 250
REF_REWARD = 600
DAILY_REWARD = 100

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b"HOSHA BOT OK")
    def log_message(self, *a): pass

def web():
    port = int(os.environ.get("PORT", "10000"))
    HTTPServer(("0.0.0.0", port), H).serve_forever()
threading.Thread(target=web, daemon=True).start()

bot = Bot(token=TOKEN)
dp = Dispatcher()
db = sqlite3.connect("hosha.db", check_same_thread=False)
cur = db.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0,
farm_start INTEGER DEFAULT 0, refs INTEGER DEFAULT 0,
ref_by INTEGER, last_daily INTEGER DEFAULT 0)""")
db.commit()

def get_user(uid):
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    return cur.fetchone()

@dp.message(CommandStart())
async def start(m: types.Message):
    args = m.text.split()
    ref = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    if ref == m.from_user.id:
        ref = None
    if not get_user(m.from_user.id):
        cur.execute("INSERT INTO users(user_id, ref_by) VALUES(?,?)", (m.from_user.id, ref))
        if ref and get_user(ref):
            cur.execute("UPDATE users SET balance=balance+?, refs=refs+1 WHERE user_id=?", (REF_REWARD, ref))
        db.commit()
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 باز کردن HOSHA STATION", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="🚜 شروع فارم 8 ساعته", callback_data="farm")],
        [InlineKeyboardButton(text="💰 Claim", callback_data="claim")],
        [InlineKeyboardButton(text="👥 دعوت +600", callback_data="ref"), InlineKeyboardButton(text="🏆 تاپ", callback_data="top")],
        [InlineKeyboardButton(text="🎁 پاداش روزانه", callback_data="daily")]
    ])
    u = get_user(m.from_user.id)
    await m.answer(f"به HOSHA STATION خوش اومدی {m.from_user.first_name} 💎\n\nموجودی: {u[1]} $HOSHA\nرفرال‌ها: {u[3]} نفر\n\nهر 8 ساعت {FARM_REWARD} توکن فارم کن!", reply_markup=kb)

@dp.message(Command("stats"))
async def stats(m: types.Message):
    if m.from_user.id != ADMIN_ID:
        return
    cur.execute("SELECT COUNT(*), SUM(balance) FROM users")
    c, s = cur.fetchone()
    await m.answer(f"کاربران: {c}\nمجموع توکن: {s}")

@dp.callback_query()
async def cb(c: types.CallbackQuery):
    u = get_user(c.from_user.id)
    now = int(time.time())
    if c.data == "farm":
        if u[2] == 0:
            cur.execute("UPDATE users SET farm_start=? WHERE user_id=?", (now, c.from_user.id))
            db.commit()
            await c.message.answer("🚜 فارم 8 ساعته شروع شد! بعدش دکمه Claim رو بزن.")
        else:
            left = FARM_TIME - (now - u[2])
            if left <= 0:
                await c.message.answer("✅ فارمت آماده‌ست! دکمه Claim رو بزن.")
            else:
                h = left // 3600
                mi = (left % 3600) // 60
                await c.message.answer(f"⏳ {h} ساعت و {mi} دقیقه مونده.")
    elif c.data == "claim":
        if u[2] != 0 and now - u[2] >= FARM_TIME:
            cur.execute("UPDATE users SET balance=balance+?, farm_start=0 WHERE user_id=?", (FARM_REWARD, c.from_user.id))
            if u[4] and get_user(u[4]):
                bonus = int(FARM_REWARD * 0.10)
                cur.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (bonus, u[4]))
            db.commit()
            await c.message.answer(f"✅ {FARM_REWARD} $HOSHA گرفتی!")
        else:
            await c.message.answer("هنوز فارمت کامل نشده.")
    elif c.data == "ref":
        await c.message.answer(f"لینک دعوتت:\n`https://t.me/{BOT_USERNAME}?start={c.from_user.id}`\n\nبه ازای هر نفر {REF_REWARD} توکن + 10 درصد از هر فارمش!", parse_mode="Markdown")
    elif c.data == "top":
        cur.execute("SELECT user_id,balance FROM users ORDER BY balance DESC LIMIT 10")
        rows = cur.fetchall()
        txt = "🏆 تاپ 10 هولدر $HOSHA:\n\n"
        for i,(uid,bal) in enumerate(rows,1):
            txt += f"{i}. {uid} - {bal}\n"
        await c.message.answer(txt)
    elif c.data == "daily":
        if now - u[5] >= 86400:
            cur.execute("UPDATE users SET balance=balance+?, last_daily=? WHERE user_id=?", (DAILY_REWARD, now, c.from_user.id))
            db.commit()
            await c.message.answer("🎁 100 توکن روزانه گرفتی!")
        else:
            await c.message.answer("فردا دوباره بیا برای پاداش روزانه.")
    await c.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())