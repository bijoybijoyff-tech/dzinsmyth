## 🤖 টেলিগ্রাম স্টক ইনফো বট — সেটআপ গাইড

### ধাপ ১: Bot Token নিন
1. টেলিগ্রামে @BotFather এ যান
2. `/newbot` পাঠান
3. বটের নাম দিন (যেমন: My Stock Bot)
4. Username দিন (যেমন: mystockinfo_bot)
5. যে Token পাবেন সেটা কপি করুন

### ধাপ ২: Admin ID নিন
1. টেলিগ্রামে @userinfobot এ গিয়ে /start পাঠান
2. আপনার User ID পাবেন (সংখ্যা)

### ধাপ ৩: bot.py এডিট করুন
```python
BOT_TOKEN = "1234567890:AAF..."   # আপনার token
ADMIN_IDS = [987654321]            # আপনার user ID
EXCEL_FILE = "data.xlsx"           # ফাইলের নাম (একই ফোল্ডারে রাখুন)
```

### ধাপ ৪: ইনস্টল ও রান করুন
```bash
pip install -r requirements.txt
python bot.py
```

---

### 📊 এক্সেল ফাইলের ফরম্যাট
| আইটেম নেইম | পরিমান   | রেট (টাকা) | মন্তব্য |
|------------|----------|------------|---------|
| চাল        | 500 কেজি | 65         | পাইকারি |
| ডাল        | 200 কেজি | 120        |         |

- **প্রথম কলাম** → আইটেম নেইম (এটি দিয়ে সার্চ হবে)
- বাকি কলামগুলো যেকোনো কিছু হতে পারে

---

### 🔧 বট কমান্ড
| কমান্ড | কাজ |
|--------|-----|
| /start | বট শুরু করুন |
| /list  | সব আইটেম বাটন হিসেবে দেখুন |
| /reload | এক্সেল রিলোড করুন (Admin) |
| /upload | নতুন এক্সেল আপলোড করুন (Admin) |

---

### 🔄 এক্সেল আপডেট করার ২টি উপায়

**উপায় ১ — সরাসরি ফাইল রিপ্লেস করুন:**
- পুরনো `data.xlsx` মুছে নতুনটি রাখুন
- `/reload` কমান্ড পাঠান

**উপায় ২ — টেলিগ্রামে আপলোড করুন:**
- বটকে `/upload` পাঠান
- নতুন `.xlsx` ফাইল attach করে পাঠান
- বট স্বয়ংক্রিয়ভাবে আপডেট হয়ে যাবে

---

### ☁️ সার্বক্ষণিক চালু রাখতে (VPS/Server)
```bash
# Screen ব্যবহার করে background এ চালান
screen -S stockbot
python bot.py
# Ctrl+A তারপর D চাপুন (detach)
```

অথবা systemd service বানান:
```ini
# /etc/systemd/system/stockbot.service
[Unit]
Description=Stock Info Telegram Bot
After=network.target

[Service]
WorkingDirectory=/path/to/telegram_bot
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl enable stockbot
sudo systemctl start stockbot
```
