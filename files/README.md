# 🚀 Čedok URL Konvertor - Webová Aplikace

Webová aplikace pro automatickou konverzi Čedok URL na affiliate linky s Bitly zkrácením a generováním šablon.

## 📋 Co aplikace dělá

1. ✅ Stáhne data z Čedok stránky (hotel, cena, hvězdičky, strava, termín)
2. ✅ Vytvoří affiliate URL
3. ✅ Zkrátí ji přes Bitly
4. ✅ Vygeneruje šablony pro kanál i web
5. ✅ Umožní kopírování jedním klikem

## 🌐 Nasazení na Render.com (ZDARMA)

### Krok 1: Připravte GitHub repozitář

1. Vytvořte nový repozitář na GitHub.com
2. Nahrajte tam tyto soubory:
   - `app.py`
   - `requirements.txt`
   - `templates/index.html`

### Krok 2: Nasaďte na Render

1. Jděte na https://render.com a přihlaste se
2. Klikněte na **"New +"** → **"Web Service"**
3. Připojte váš GitHub repozitář
4. Nastavte:
   - **Name**: cedok-converter (nebo jiný název)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free

5. Klikněte **"Create Web Service"**

### Krok 3: Použití

Po nasazení dostanete URL jako: `https://cedok-converter.onrender.com`

Tu můžete sdílet s kolegou a oba můžete používat!

## 💻 Lokální spuštění (pro testování)

```bash
# Nainstalujte závislosti
pip install -r requirements.txt

# Spusťte aplikaci
python app.py

# Otevřete v prohlížeči
http://localhost:5000
```

## 🔧 Alternativní hostingy (také zdarma)

### Railway.app
1. Jděte na railway.app
2. "New Project" → "Deploy from GitHub"
3. Vyberte repozitář
4. Automaticky detekuje Python a nasadí

### Vercel
1. Jděte na vercel.com
2. "New Project" → Import z GitHubu
3. Framework: Other
4. Nasadí automaticky

### PythonAnywhere (bez GitHubu)
1. Zaregistrujte se na pythonanywhere.com
2. Upload soubory přes "Files"
3. Nastavte web app v Dashboard

## 📝 Poznámky

- **API token a affiliate prefix** jsou zabudované v `app.py`
- Aplikace běží na **Free tieru** Renderu (může usínat po nečinnosti, první load pak trvá ~30s)
- Pro **produkční** použití doporučuji paid tier nebo Railway

## 🎯 Funkce

- ✅ Responsive design (funguje na mobilu i PC)
- ✅ Kopírování jedním klikem
- ✅ Real-time zpracování
- ✅ Krásné moderní UI
- ✅ Žádná registrace potřebná pro uživatele
