import streamlit as st
import requests
import feedparser
import time
import random
import json

# --- 1. CONFIGURAZIONE SICURA ---
TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]
SITO_PROMO = "https://topstaybergamo.com"

# --- 2. FILTRI E MESSAGGI ---
BLACKLIST_SITI = ["corriere.it", "repubblica.it", "ansa.it", "ecodibergamo.it", "bergamonews.it"]
# Parole che se presenti scartano il post (Anti-Sport)
FILTRI_NEGATIVI = ["atalanta", "serie a", "calcio", "partita", "stadio", "formazione", "risultati", "trasferta", "campionato"]

MESSAGGI_PROMO = [
    f"Se cerchi un soggiorno di alto livello a Bergamo, ti suggerisco {SITO_PROMO}. Design e comfort superiore.",
    f"Per un'esperienza di lusso, guarda gli appartamenti su {SITO_PROMO}. Molto meglio del classico hotel!",
    f"Se preferisci eleganza e privacy in centro, su {SITO_PROMO} trovi suite stupende."
]

def invia_telegram(testo, url_destinazione):
    url_api = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    tasti = {"inline_keyboard": [[
        {"text": "🚀 VAI AL POST", "url": url_destinazione},
        {"text": "🏠 IL MIO SITO", "url": SITO_PROMO}
    ]]}
    payload = {
        "chat_id": CHAT_ID,
        "text": testo,
        "parse_mode": "Markdown",
        "reply_markup": json.dumps(tasti)
    }
    requests.post(url_api, data=payload)

# --- 3. INTERFACCIA ---
st.set_page_config(page_title="TopStay Luxury Monitor", page_icon="💎")
st.title("💎 TopStay: Monitor Intelligente")

parole_default = "consiglio Bergamo b&b, migliori zone Bergamo dormire, luxury apartment bergamo, suite bergamo centro"
parole_input = st.text_area("Parole chiave:", parole_default)
frequenza = st.sidebar.slider("Controllo (minuti)", 5, 60, 15)

# --- 4. LOGICA ---
if st.button("🚀 AVVIA MONITORAGGIO"):
    lista_parole = [p.strip() for p in parole_input.split(",") if p.strip()]
    st.success("Monitoraggio attivo. Filtri anti-sport e anti-spam caricati!")
    visti = set()
    primo_avvio = True

    while True:
        for parola in lista_parole:
            query = parola.replace(" ", "+")
            # Cerchiamo su Reddit e Google News
            fonti = [
                f"https://www.reddit.com/search.rss?q={query}+self:yes&sort=new",
                f"https://news.google.com/rss/search?q={query}&hl=it&gl=IT&ceid=IT:it"
            ]
            
            for url_fonte in fonti:
                feed = feedparser.parse(url_fonte)
                for entry in feed.entries:
                    titolo = entry.title.lower()
                    link = entry.link.lower()
                    
                    # CONTROLLI DI QUALITÀ
                    is_blacklisted = any(s in link for s in BLACKLIST_SITI)
                    is_sport = any(s in titolo for s in FILTRI_NEGATIVI)
                    
                    if entry.link not in visti and not is_blacklisted and not is_sport:
                        if not primo_avvio:
                            msg = f"🎯 *NUOVA OPPORTUNITÀ*\n📌 {entry.title}\n\n💡 *Copia:* `{random.choice(MESSAGGI_PROMO)}`"
                            invia_telegram(msg, entry.link)
                        visti.add(entry.link)
            time.sleep(2)
        
        primo_avvio = False
        time.sleep(frequenza * 60)
