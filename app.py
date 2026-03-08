import streamlit as st
import requests
import feedparser
import time
import random
from datetime import datetime

# --- CONFIGURAZIONE SICURA ---
TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

# Tuo sito
SITO = "topstaybergamo.com"

# Varianti di messaggi per non essere ripetitivi
MESSAGGI_PROMO = [
    f"Ciao! Se stai cercando un alloggio a Bergamo, ti suggerisco di dare un'occhiata a {SITO}. Ci sono ottime soluzioni per affitti brevi e B&B!",
    f"Benvenuto a Bergamo! Per appartamenti e case vacanza di qualità, prova a guardare su {SITO}, è molto affidabile.",
    f"Se non hai ancora deciso dove dormire, su {SITO} trovi una bella selezione di posti centrali a Bergamo. Spero ti aiuti!"
]

def invia_telegram(messaggio):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": messaggio, 
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    requests.post(url, json=payload)

# --- INTERFACCIA ---
st.set_page_config(page_title="BG Stay Marketing", page_icon="📈")
st.title("📈 TopStay Bergamo Marketing Bot")

st.sidebar.header("Canali Attivi")
usa_reddit = st.sidebar.checkbox("Reddit", value=True)
usa_google = st.sidebar.checkbox("Google News", value=True)
frequenza = st.sidebar.slider("Controllo ogni (minuti)", 2, 60, 10)

parole_input = st.text_area("Parole chiave (separate da virgola)", 
                            "bergamo hotel, affitto breve bergamo, b&b bergamo, dormire bergamo")

if st.button("🚀 AVVIA MONITORAGGIO"):
    lista_parole = [p.strip() for p in parole_input.split(",") if p.strip()]
    st.success(f"Bot in esecuzione... Sto monitorando: {', '.join(lista_parole)}")
    
    visti = set()
    
    while True:
        for parola in lista_parole:
            query = parola.replace(" ", "+")
            
            # --- LOGICA REDDIT ---
            if usa_reddit:
                feed = feedparser.parse(f"https://www.reddit.com/search.rss?q={query}&sort=new")
                for entry in feed.entries:
                    if entry.link not in visti:
                        risposta = random.choice(MESSAGGI_PROMO)
                        msg = (
                            f"🚩 *NUOVO POST SU REDDIT*\n"
                            f"🔍 Parola: {parola}\n"
                            f"📌 *{entry.title}*\n\n"
                            f"🔗 [APRI IL POST E RISPONDI]({entry.link})\n\n"
                            f"💡 *Risposta suggerita (Tocca per copiare):*\n"
                            f"`{risposta}`"
                        )
                        invia_telegram(msg)
                        visti.add(entry.link)
                        time.sleep(1)

            # --- LOGICA GOOGLE NEWS ---
            if usa_google:
                feed = feedparser.parse(f"https://news.google.com/rss/search?q={query}&hl=it&gl=IT&ceid=IT:it")
                for entry in feed.entries:
                    if entry.link not in visti:
                        msg = (
                            f"📰 *NUOVA NEWS / BLOG*\n"
                            f"🔍 Parola: {parola}\n"
                            f"📌 *{entry.title}*\n\n"
                            f"🔗 [LEGGI ARTICOLO]({entry.link})\n"
                            f"_(Puoi commentare se l'articolo lo permette)_"
                        )
                        invia_telegram(msg)
                        visti.add(entry.link)
                        time.sleep(1)
            

        time.sleep(frequenza * 60)
