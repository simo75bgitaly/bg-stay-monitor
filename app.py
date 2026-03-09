import streamlit as st
import requests
import feedparser
import time
import random

# --- 1. CONFIGURAZIONE ---
TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]
SITO_PROMO = "https://topstaybergamo.com"

FILTRI_NEGATIVI = ["atalanta", "serie a", "serie b", "calcio", "basket", "hockey", "vince", "coppa", "campionato", "monza"]

MESSAGGI_PROMO = [
    f"Se cerchi eleganza in centro, su {SITO_PROMO} trovi suite stupende.",
    f"Per un soggiorno di lusso a Bergamo, guarda {SITO_PROMO}. Design e comfort superiore."
]

# --- 2. INTERFACCIA SMARTPHONE-FRIENDLY ---
st.set_page_config(page_title="TopStay Monitor", layout="centered")
st.title("💎 Monitor TopStay")

# Inizializzazione liste risultati se non esistono
if 'res_tg' not in st.session_state: st.session_state.res_tg = []
if 'res_reddit' not in st.session_state: st.session_state.res_reddit = []
if 'res_web' not in st.session_state: st.session_state.res_web = []

# Sidebar
st.sidebar.header("Comandi")
if st.sidebar.button("🗑️ PULISCI SCHERMO"):
    st.session_state.res_tg = []
    st.session_state.res_reddit = []
    st.session_state.res_web = []
    st.sidebar.success("Schermo pulito!")

frequenza = st.sidebar.slider("Aggiorna ogni (min)", 5, 60, 15)
parole_predefinite = '"dormire a Bergamo", "hotel Bergamo", "affitto breve bergamo", "soggiornare a Bergamo", "casa vacanze Bergamo"'
parole_input = st.text_area("Target:", parole_predefinite)

# Spazio per i risultati divisi per categoria
st.subheader("Risultati per Fonte")
container_tg = st.expander("📲 SOCIAL & TELEGRAM", expanded=True)
container_reddit = st.expander("🧡 DOMANDE REDDIT", expanded=False)
container_web = st.expander("🌐 NEWS & BLOG", expanded=False)

def invia_telegram(testo):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": testo, "parse_mode": "Markdown"})

# --- 3. LOGICA DI FILTRO E RICERCA ---
if st.button("🚀 AVVIA MONITORAGGIO"):
    lista_parole = [p.strip().replace('"', '') for p in parole_input.split(",") if p.strip()]
    st.info("Monitoraggio in corso... I nuovi risultati appariranno qui sotto.")
    
    visti = set()
    primo_avvio = True

    while True:
        for parola in lista_parole:
            q_url = f'"{parola}"'.replace(" ", "+")
            
            fonti = {
                "reddit": f"https://www.reddit.com/search.rss?q={q_url}&sort=new",
                "web": f"https://news.google.com/rss/search?q={q_url}&hl=it&gl=IT&ceid=IT:it",
                "telegram": f"https://news.google.com/rss/search?q={q_url}+site:t.me&hl=it&gl=IT&ceid=IT:it"
            }

            for tipo, url in fonti.items():
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    titolo_low = entry.title.lower()
                    
                    # Filtro di precisione
                    match = parola.lower() in titolo_low
                    no_sport = not any(s in titolo_low for s in FILTRI_NEGATIVI)

                    if entry.link not in visti and match and no_sport:
                        if not primo_avvio:
                            tag = "📲 TG" if tipo == "telegram" else "🌐 WEB"
                            invia_telegram(f"📍 {tag}\n🔍 {parola}\n📌 {entry.title}\n🔗 {entry.link}")
                        
                        visti.add(entry.link)
                        
                        item = f"📍 **{parola}**\n\n{entry.title}\n\n[Apri Link]({entry.link})\n---"
                        if tipo == "telegram": st.session_state.res_tg.insert(0, item)
                        elif tipo == "reddit": st.session_state.res_reddit.insert(0, item)
                        else: st.session_state.res_web.insert(0, item)

        # Scrittura nei contenitori (aggiornati in tempo reale)
        container_tg.markdown("\n".join(st.session_state.res_tg) if st.session_state.res_tg else "In attesa di Telegram...")
        container_reddit.markdown("\n".join(st.session_state.res_reddit) if st.session_state.res_reddit else "In attesa di Reddit...")
        container_web.markdown("\n".join(st.session_state.res_web) if st.session_state.res_web else "In attesa di Web...")
        
        primo_avvio = False
        time.sleep(frequenza * 60)
