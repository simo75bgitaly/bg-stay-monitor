import streamlit as st
import requests
import feedparser
import time
import random

# --- CONFIGURAZIONE ---
TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]
SITO_PROMO = "https://topstaybergamo.com"

# Filtri per eliminare lo sport e le città sbagliate
FILTRI_NEGATIVI = ["atalanta", "serie a", "serie b", "calcio", "coppa", "vince", "partita", "monza", "milano", "inter", "juve"]

# --- INTERFACCIA ---
st.set_page_config(page_title="TopStay Monitor", layout="wide")
st.title("💎 TopStay: Monitor di Precisione")

# Sidebar
st.sidebar.header("Parametri")
frequenza = st.sidebar.slider("Aggiornamento (minuti)", 5, 60, 15)

# Inserisci le parole chiave separate da virgola
parole_input = st.text_area("Parole chiave (es: b&b bergamo, hotel bergamo):", "casa vacanze bergamo, hotel bergamo")

# Creazione Tab
tab_tg, tab_reddit, tab_web = st.tabs(["📲 Telegram", "🧡 Reddit", "🌐 Web & News"])

def invia_telegram(testo):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": testo, "parse_mode": "Markdown"})

# --- LOGICA ---
if st.button("🚀 AVVIA MONITORAGGIO"):
    # Puliamo le parole chiave e le rendiamo una lista
    lista_parole = [p.strip().lower() for p in parole_input.split(",") if p.strip()]
    st.success(f"Monitoraggio attivo su {len(lista_parole)} chiavi esatte.")
    
    visti = set()
    primo_avvio = True

    while True:
        results_tg, results_reddit, results_web = [], [], []

        for parola in lista_parole:
            # Forziamo la ricerca con virgolette per Google
            query_google = f'"{parola}"'.replace(" ", "+")
            
            fonti = {
                "reddit": f"https://www.reddit.com/search.rss?q={query_google}&sort=new",
                "web": f"https://news.google.com/rss/search?q={query_google}&hl=it&gl=IT&ceid=IT:it",
                "telegram": f"https://news.google.com/rss/search?q={query_google}+site:t.me&hl=it&gl=IT&ceid=IT:it"
            }

            for tipo, url in fonti.items():
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    titolo = entry.title.lower()
                    
                    # --- IL SUPER FILTRO ---
                    # 1. Controlla che la frase esatta sia presente
                    check_esatto = parola in titolo
                    # 2. Controlla che non ci siano parole sportive
                    check_sport = any(s in titolo for s in FILTRI_NEGATIVI)

                    if entry.link not in visti and check_esatto and not check_sport:
                        if not primo_avvio:
                            msg = f"📍 FONTE: {tipo.upper()}\n🔍 Trovato: {parola}\n📌 {entry.title}\n🔗 {entry.link}"
                            invia_telegram(msg)
                        
                        visti.add(entry.link)
                        
                        # Organizzazione nelle Tab
                        item = f"✅ **{entry.title}**\n[Link]({entry.link})"
                        if tipo == "telegram": results_tg.append(item)
                        elif tipo == "reddit": results_reddit.append(item)
                        else: results_web.append(item)

        # Aggiornamento UI
        tab_tg.write("\n\n".join(results_tg) if results_tg else "In attesa di nuovi post Telegram...")
        tab_reddit.write("\n\n".join(results_reddit) if results_reddit else "In attesa di nuovi post Reddit...")
        tab_web.write("\n\n".join(results_web) if results_web else "In attesa di nuove News...")
        
        primo_avvio = False
        time.sleep(frequenza * 60)
