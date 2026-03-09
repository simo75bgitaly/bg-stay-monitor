import streamlit as st
import requests
import feedparser
import time
import random

# --- 1. CONFIGURAZIONE SICURA ---
TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]
SITO_PROMO = "https://topstaybergamo.com"

# --- 2. FILTRI E MESSAGGI ---
BLACKLIST_SITI = ["corriere.it", "repubblica.it", "ansa.it", "ecodibergamo.it", "bergamonews.it"]
FILTRI_NEGATIVI = ["atalanta", "serie a", "calcio", "partita", "stadio", "formazione", "risultati", "trasferta", "campionato", "sport"]

MESSAGGI_PROMO = [
    f"Se cerchi un soggiorno di alto livello a Bergamo, ti suggerisco {SITO_PROMO}. Design e comfort superiore.",
    f"Per un'esperienza di lusso, guarda gli appartamenti su {SITO_PROMO}. Molto meglio del classico hotel!",
    f"Se preferisci eleganza e privacy in centro, su {SITO_PROMO} trovi suite stupende."
]

def invia_telegram_semplice(testo):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": testo, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

# --- 3. INTERFACCIA CON FLAG ---
st.set_page_config(page_title="TopStay Global Monitor", page_icon="💎")
st.title("💎 TopStay: Monitor Intelligente")

# Barra laterale con i selettori (Flag)
st.sidebar.header("Cosa monitorare?")
usa_reddit = st.sidebar.checkbox("Reddit (Domande)", value=True)
usa_google = st.sidebar.checkbox("Google News / Blog", value=True)
usa_telegram = st.sidebar.checkbox("Gruppi/Canali Telegram", value=True)

frequenza = st.sidebar.slider("Controllo ogni (minuti)", 5, 60, 15)

parole_default = "consiglio Bergamo b&b, dove dormire bergamo, luxury apartment bergamo, suite bergamo centro"
parole_input = st.text_area("Parole chiave target:", parole_default)

# --- 4. LOGICA DI MONITORAGGIO ---
if st.button("🚀 AVVIA MONITORAGGIO"):
    lista_parole = [p.strip() for p in parole_input.split(",") if p.strip()]
    st.success("Monitoraggio avviato con i filtri selezionati!")
    visti = set()
    primo_avvio = True

    while True:
        for parola in lista_parole:
            query_normale = parola.replace(" ", "+")
            fonti = []
            
            # Aggiunge le fonti solo se il flag è attivo
            if usa_reddit:
                fonti.append(f"https://www.reddit.com/search.rss?q={query_normale}+self:yes&sort=new")
            
            if usa_google:
                fonti.append(f"https://news.google.com/rss/search?q={query_normale}&hl=it&gl=IT&ceid=IT:it")
            
            if usa_telegram:
                # Cerca menzioni di Telegram indicizzate sul web
                query_tg = f"{parola} site:t.me".replace(" ", "+")
                fonti.append(f"https://news.google.com/rss/search?q={query_tg}&hl=it&gl=IT&ceid=IT:it")
            
            for url_fonte in fonti:
                feed = feedparser.parse(url_fonte)
                for entry in feed.entries:
                    titolo = entry.title.lower()
                    link = entry.link.lower()
                    
                    is_blacklisted = any(s in link for s in BLACKLIST_SITI)
                    is_sport = any(s in titolo for s in FILTRI_NEGATIVI)
                    
                    if entry.link not in visti and not is_blacklisted and not is_sport:
                        if not primo_avvio:
                            tipo = "📲 TELEGRAM" if "t.me" in link else "🎯 WEB/REDDIT"
                            msg = (
                                f"{tipo}\n"
                                f"📌 *{entry.title}*\n"
                                f"🔗 Link: {entry.link}\n\n"
                                f"💡 *Copia:* `{random.choice(MESSAGGI_PROMO)}`"
                            )
                            invia_telegram_semplice(msg)
                        visti.add(entry.link)
            time.sleep(2)
        
        primo_avvio = False
        time.sleep(frequenza * 60)
