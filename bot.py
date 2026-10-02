import os, re, asyncio, sqlite3
from yt_dlp import YoutubeDL
from telegram import Update, InlineKeyboardButton as B, InlineKeyboardMarkup as M, ReplyKeyboardMarkup
from telegram.constants import ChatMemberStatus
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler,
                          CallbackQueryHandler, ContextTypes, filters)

TOKEN = "8987059390:AAEHMllv2DWnGIzgjqyx92nMurvTc1gf0e8"
ADMINS = [int(x) for x in os.getenv("ADMINS", "123456789").split(",")]
CHANNELS = os.getenv("CHANNELS", "@kanal1,@kanal2").split(",")  # bot kanalda admin bo'lsin
BOT_NAME = "@sizning_botingiz"
URL = re.compile(r"https?://\S+")
os.makedirs("dl", exist_ok=True)

db = sqlite3.connect("bot.db", check_same_thread=False)
db.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT, downloads INTEGER DEFAULT 0)")
db.commit()

MENU = ReplyKeyboardMarkup(
    [["🎬 Video yuklash", "🎵 Musiqa qidirish"], ["📊 Statistika", "ℹ️ Yordam"]],
    resize_keyboard=True)

def add_user(user):
    db.execute("INSERT OR IGNORE INTO users(id,name) VALUES(?,?)", (user.id, user.full_name))
    db.commit()

def stats():
    u = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    d = db.execute("SELECT COALESCE(SUM(downloads),0) FROM users").fetchone()[0]
    return u, d

async def not_joined(bot, uid):
    res = []
    for ch in CHANNELS:
        try:
            m = await bot.get_chat_member(ch, uid)
            if m.status in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED):
                res.append(ch)
        except Exception:
            pass
    return res

def sub_kb(chs):
    rows = [[B(f"➕ {c}", url=f"https://t.me/{c.lstrip('@')}")] for c in chs]
    rows.append([B("✅ Tekshirish", callback_data="check")])
    return M(rows)

async def guard(u: Update, c: ContextTypes.DEFAULT_TYPE):
    """True bo'lsa foydalanuvchi hamma kanalga a'zo."""
    uid = u.effective_user.id
    if uid in ADMINS:
        return True
    chs = await not_joined(c.bot, uid)
    if chs:
        await u.effective_message.reply_text(
            "❗ Botdan foydalanish uchun kanallarga a'zo bo'ling:", reply_markup=sub_kb(chs))
        return False
    return True

def download(url, audio=False, uid=0):
    opts = {"outtmpl": f"dl/{uid}_%(id)s.%(ext)s", "quiet": True,
            "noplaylist": True, "max_filesize": 50 * 1024 * 1024}
    if audio:
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [{"key": "FFmpegExtractAudio",
                                   "preferredcodec": "mp3", "preferredquality": "192"}]
    else:
        opts["format"] = "mp4/best"
    if os.path.exists("cookies.txt"):
        opts["cookiefile"] = "cookies.txt"
    with YoutubeDL(opts) as y:
        info = y.extract_info(url, download=True)
        path = y.prepare_filename(info)
    if audio:
        path = os.path.splitext(path)[0] + ".mp3"
    return path, info

def search(q):
    with YoutubeDL({"quiet": True, "extract_flat": True}) as y:
        return y.extract_info(f"ytsearch5:{q}", download=False)["entries"]

async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    add_user(u.effective_user)
    if not await guard(u, c):
        return
    await u.message.reply_text(
        "👋 Salom! Instagram/TikTok/YouTube havolasini yuboring yoki qo'shiq nomini yozing.",
        reply_markup=MENU)

async def text(u: Update, c: ContextTypes.DEFAULT_TYPE):
    add_user(u.effective_user)
    uid = u.effective_user.id

    # Broadcast rejimi (admin)
    if c.user_data.get("bc") and uid in ADMINS:
        c.user_data["bc"] = False
        ids = [r[0] for r in db.execute("SELECT id FROM users")]
        ok = 0
        for i in ids:
            try:
                await c.bot.copy_message(i, u.effective_chat.id, u.message.message_id)
                ok += 1
                await asyncio.sleep(0.05)
            except Exception:
                pass
        return await u.message.reply_text(f"✅ {ok}/{len(ids)} ta foydalanuvchiga yuborildi.")

    if not await guard(u, c):
        return
    t = u.message.text.strip()
    if t == "📊 Statistika":
        us, d = stats()
        return await u.message.reply_text(f"👥 Foydalanuvchilar: {us}\n📥 Yuklashlar: {d}")
    if t in ("ℹ️ Yordam", "🎬 Video yuklash", "🎵 Musiqa qidirish"):
        return await u.message.reply_text(
            "🎬 Havola yuboring — video yoki MP3 qilib beraman.\n"
            "🎵 Qo'shiq yoki ijrochi nomini yozing — qidirib topaman.")
    m = URL.search(t)
    if m:
        c.user_data["url"] = m.group()
        kb = M([[B("🎬 Video", callback_data="v"), B("🎵 MP3", callback_data="a")]])
        return await u.message.reply_text("Nimani yuklay?", reply_markup=kb)
    msg = await u.message.reply_text("🔎 Qidiryapman...")
    res = await asyncio.to_thread(search, t)
    kb = M([[B(f"🎵 {r['title'][:50]}", callback_data=f"m:{r['id']}")] for r in res])
    await msg.edit_text("Natijalar:", reply_markup=kb)

async def admin(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_user.id not in ADMINS:
        return
    us, d = stats()
    kb = M([[B("📢 Xabar tarqatish", callback_data="bc")],
            [B("📊 Statistika", callback_data="st")]])
    await u.message.reply_text(f"🛠 Admin panel\n\n👥 {us} ta foydalanuvchi\n📥 {d} ta yuklash", reply_markup=kb)

async def button(u: Update, c: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query
    d = q.data
    uid = q.from_user.id

    if d == "check":
        chs = await not_joined(c.bot, uid)
        if chs:
            return await q.answer("❌ Hali hamma kanalga a'zo bo'lmadingiz!", show_alert=True)
        await q.answer()
        return await q.edit_message_text("✅ Rahmat! Endi havola yoki qo'shiq nomini yuboring.")
    if d == "bc" and uid in ADMINS:
        await q.answer()
        c.user_data["bc"] = True
        return await q.edit_message_text("📢 Tarqatiladigan xabarni yuboring (matn, rasm yoki video):")
    if d == "st" and uid in ADMINS:
        us, dl = stats()
        return await q.answer(f"👥 {us} | 📥 {dl}", show_alert=True)

    await q.answer()
    if uid not in ADMINS and await not_joined(c.bot, uid):
        return await q.edit_message_text("❗ Avval kanallarga a'zo bo'ling. /start")

    if d.startswith("m:"):
        url, audio = f"https://youtube.com/watch?v={d[2:]}", True
    else:
        url, audio = c.user_data.get("url"), d == "a"
    if not url:
        return await q.edit_message_text("Havolani qayta yuboring.")
    await q.edit_message_text("⏳ Yuklanmoqda...")
    try:
        path, info = await asyncio.to_thread(download, url, audio, uid)
        with open(path, "rb") as f:
            if audio:
                await q.message.reply_audio(f, title=info.get("title"), caption=f"🎧 {BOT_NAME}")
            else:
                await q.message.reply_video(f, caption=f"🎬 {BOT_NAME}")
        os.remove(path)
        db.execute("UPDATE users SET downloads=downloads+1 WHERE id=?", (uid,))
        db.commit()
        await q.message.delete()
    except Exception:
        await q.edit_message_text("❌ Yuklab bo'lmadi (akkaunt yopiq yoki fayl 50MB dan katta).")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, text))
app.run_polling()
