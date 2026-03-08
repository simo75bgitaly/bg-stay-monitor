import streamlit as st
import requests
import feedparser
import time
import random
from datetime import datetime

# --- 1. CONFIGURAZIONE SICURA (DA SECRETS) ---
# Assicurati di aver inserito questi nomi in Streamlit Settings -> Secrets
TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

# --- 2. CONFIGURAZIONE FILTRI ASTUTI ---
SITO_PROMO = "topstaybergamo.com"

# Siti news da ignorare perché non hanno commenti o sono troppo grandi
BLACKLIST_SITI = [
    "corriere.it", "repubblica.it", "ansa.it", "ilgiorno.it", 
    "ecodibergamo.it", "bergamonews.it", "lastampa.it", "ilfattoquotidiano.it"
]

MESSAGGI_PROMO = [
    f"Ciao! Se cerchi un alloggio a Bergamo, ti suggerisco di guardare {SITO_PROMO}. Ci sono ottime soluzioni per affitti brevi!",
    f"Benvenuto a Bergamo! Per trovare i migliori appartamenti e B&B, prova {SITO_PROMO}, è molto comodo.",
    f"Se hai bisogno di info su dove dormire, su {SITO_PROMO} trovi una bella selezione di posti centrali a Bergamo."
]

def invia_telegram(messaggio):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": messaggio, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

# --- 3. INTERFACCIA ---
st.set_page_config(page_title="BG Stay Smart Monitor", page_icon="🕵️‍♂️")
st.title("🕵️‍♂️ BG Stay: Monitor Astuto")

st.sidebar.header("Filtri Attivi")
usa_reddit = st.sidebar.checkbox("Reddit (Solo Domande)", value=True)
usa_google = st.sidebar.checkbox("Google News (Filtrato)", value=True)
frequenza = st.sidebar.slider("Controllo ogni (minuti)", 2, 60, 10)

parole_input = st.text_area("Parole chiave (separate da virgola)", 
                            "consiglio hotel bergamo, dove dormire bergamo, b&b bergamo reddit")

# --- 4. LOGICA DI MONITORAGGIO ---
if st.button("🚀 AVVIA MONITORAGGIO"):
    lista_parole = [p.strip() for p in parole_input.split(",") if p.strip()]
    st.success(f"Monitoraggio avviato su: {', '.join(lista_parole)}")
    visti = set()
    
    while True:
        for parola in lista_parole:
            query = parola.replace(" ", "+")
            
            # --- REDDIT: SOLO DOMANDE (Self-posts) ---
            if usa_reddit:
                # 'self:yes' dice a Reddit di cercare solo post di testo (domande)
                url_reddit = f"https://www.reddit.com/search.rss?q={query}+self:yes&sort=new"
                feed = feedparser.parse(url_reddit)
                for entry in feed.entries:
                    if entry.link not in visti:
                        risposta = random.choice(MESSAGGI_PROMO)
                        msg = (
                            f"❓ *DOMANDA SU REDDIT*\n"
                            f"🔍 Parola: {parola}\n"
                            f"📌 *{entry.title}*\n\n"
                            f"🔗 [RISPONDI ORA]({entry.link})\n\n"
                            f"💡 *Copia e incolla:*\n`{risposta}`"
                        )
                        invia_telegram(msg)
                        visti.add(entry.link)

            # --- GOOGLE NEWS: FILTRO BLACKLIST ---
            if usa_google:
                url_google = f"https://news.google.com/rss/search?q={query}&hl=it&gl=IT&ceid=IT:it"
                feed = feedparser.parse(url_google)
                for entry in feed.entries:
                    # Controlla se il link è già visto o se appartiene alla blacklist
                    is_blacklisted = any(sito in entry.link.lower() for sito in BLACKLIST_SITI)
                    
                    if entry.link not in visti and not is_blacklisted:
                        msg = (
                            f"📰 *NEWS/BLOG COMMENTABILE*\n"
                            f"🔍 Parola: {parola}\n"
                            f"📌 *{entry.title}*\n\n"
                            f"🔗 [APRI SITO]({entry.link})"
                        )
                        invia_telegram(msg)
                        visti.add(entry.link)
            
            time.sleep(2) # Piccola pausa per non sovraccaricare
            
        time.sleep(frequenza * 60)
