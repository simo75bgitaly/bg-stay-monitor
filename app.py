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
# Escludiamo i siti di news inutili e lo sport
BLACKLIST_SITI = ["corriere.it", "repubblica.it", "ansa.it", "ecodibergamo.it", "bergamonews.it"]
FILTRI_NEGATIVI = ["atalanta", "serie a", "calcio", "partita", "stadio", "formazione", "risultati", "trasferta", "campionato"]

MESSAGGI_PROMO = [
    f"Se cerchi un soggiorno di alto livello a Bergamo, ti suggerisco {SITO_PROMO}. Design e comfort superiore.",
    f"Per un'esperienza di lusso, guarda gli appartamenti su {SITO_PROMO}. Molto meglio del classico hotel!",
    f"Se preferisci eleganza e privacy in centro, su {SITO_PROMO} trovi suite stupende."
]

def invia_telegram_semplice(testo):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": testo,
        "parse_mode": "Markdown"
    }
    requests.post(url, data=payload)

# --- 3. INTERFACCIA ---
st.set_page_config(page_title="TopStay Global Monitor", page_icon="💎")
st.title("💎 TopStay: Monitor Web & Telegram")

parole_default = "consiglio Bergamo b&b, dove dormire bergamo, luxury apartment bergamo, suite bergamo centro"
parole_input = st.text_area("Parole chiave:", parole_default)
frequenza = st.sidebar.slider("Controllo (minuti)", 5, 60, 15)

# --- 4. LOGICA DI MONITORAGGIO ---
if st.button("🚀 AVVIA MONITORAGGIO"):
    lista_parole = [p.strip() for p in parole_input.split(",") if p.strip()]
    st.success("Monitoraggio attivo. Cercherò anche menzioni su canali Telegram pubblici.")
    visti = set()
    primo_avvio = True

    while True:
        for parola in lista_parole:
            # Ricerca mirata: cerchiamo la parola chiave + riferimenti a Telegram
            query_con_telegram = f"{parola} site:t.me"
            query_normale = parola.replace(" ", "+")
            
            fonti = [
                f"https://www.reddit.com/search.rss?q={query_normale}+self:yes&sort=new",
                f"https://news.google.com/rss/search?q={query_normale}&hl=it&gl=IT&ceid=IT:it",
                f"https://news.google.com/rss/search?q={query_con_telegram.replace(' ', '+')}&hl=it&gl=IT&ceid=IT:it"
            ]
            
            for url_fonte in fonti:
                feed = feedparser.parse(url_fonte)
                for entry in feed.entries:
                    titolo = entry.title.lower()
                    link = entry.link.lower()
                    
                    # Filtri di qualità
                    is_blacklisted = any(s in link for s in BLACKLIST_SITI)
                    is_sport = any(s in titolo for s in FILTRI_NEGATIVI)
                    
                    if entry.link not in visti and not is_blacklisted and not is_sport:
                        if not primo_avvio:
                            # Se il link contiene t.me, è una menzione da Telegram
                            tipo = "📲 TELEGRAM / SOCIAL" if "t.me" in link else "🎯 OPPORTUNITÀ"
                            
                            msg = (
                                f"{tipo}\n"
                                f"📌 *{entry.title}*\n"
                                f"🔗 Link: {entry.link}\n\n"
                                f"💡 *Suggerimento:* `{random.choice(MESSAGGI_PROMO)}`"
                            )
                            invia_telegram_semplice(msg)
                        visti.add(entry.link)
            time.sleep(2)
        
        primo_avvio = False
        time.sleep(frequenza * 60)
