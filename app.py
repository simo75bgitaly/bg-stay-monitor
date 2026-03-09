import streamlit as st
import requests
import feedparser
import time
import random

# --- 1. CONFIGURAZIONE ---
TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]
SITO_PROMO = "https://topstaybergamo.com"

# Filtri anti-sport potenziati (per eliminare i messaggi errati degli screenshot)
FILTRI_NEGATIVI = [
    "atalanta", "serie a", "serie b", "calcio", "basket", "hockey", 
    "vince", "coppa", "campionato", "punteggio", "monza", "milano", 
    "inter", "juve", "fiorentina", "parma", "sport", "risultati", "pumas"
]

# --- 2. INTERFACCIA ---
st.set_page_config(page_title="TopStay Monitor", layout="centered")
st.title("💎 Monitor TopStay")

if 'res_tg' not in st.session_state: st.session_state.res_tg = []
if 'res_reddit' not in st.session_state: st.session_state.res_reddit = []
if 'res_web' not in st.session_state: st.session_state.res_web = []

st.sidebar.header("Comandi")
if st.sidebar.button("🗑️ PULISCI SCHERMO"):
    st.session_state.res_tg = []
    st.session_state.res_reddit = []
    st.session_state.res_web = []
    st.sidebar.success("Schermo pulito!")

frequenza = st.sidebar.slider("Aggiorna ogni (min)", 5, 60, 15)

# CHIAVI ESATTE (B&B RIMOSSO)
parole_predefinite = '"dormire a Bergamo", "hotel Bergamo", "affitto breve bergamo", "soggiornare a Bergamo", "casa vacanze Bergamo"'
parole_input = st.text_area("Target Attivo:", parole_predefinite)

container_tg = st.expander("📲 SOCIAL & TELEGRAM", expanded=True)
container_reddit = st.expander("🧡 DOMANDE REDDIT", expanded=False)
container_web = st.expander("🌐 NEWS & BLOG", expanded=False)

def invia_telegram_diviso(tipo, parola, titolo, link):
    """Invia un messaggio con formattazione specifica per dividere le fonti visivamente"""
    emoji = "📲" if tipo == "telegram" else ("🧡" if tipo == "reddit" else "🌐")
    nome_fonte = tipo.upper()
    
    testo = (
        f"————————————————\n"
        f"{emoji} *FONTE: {nome_fonte}*\n"
        f"————————————————\n"
        f"🎯 *Target:* {parola}\n"
        f"📌 *Titolo:* {titolo}\n\n"
        f"🔗 [APRI IL POST]({link})\n"
        f"————————————————"
    )
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": testo, "parse_mode": "Markdown", "disable_web_page_preview": False})

# --- 3. LOGICA DI RICERCA ---
if st.button("🚀 AVVIA MONITORAGGIO"):
    lista_parole = [p.strip().replace('"', '') for p in parole_input.split(",") if p.strip()]
    st.info("Monitoraggio avviato. Le notifiche Telegram saranno ora divise visivamente.")
    
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
                    
                    # Filtro di precisione: la frase deve essere intera
                    match = parola.lower() in titolo_low
                    no_calcio = not any(s in titolo_low for s in FILTRI_NEGATIVI)
                    # Blocco definitivo per qualsiasi riferimento a "B" singola o B&B
                    no_bb = all(x not in titolo_low for x in ["b&b", " b ", "serie b"])

                    if entry.link not in visti and match and no_calcio and no_bb:
                        if not primo_avvio:
                            # INVIO DIVISO SU TELEGRAM
                            invia_telegram_diviso(tipo, parola, entry.title, entry.link)
                        
                        visti.add(entry.link)
                        
                        item = f"📍 **{parola}**\n\n{entry.title}\n\n[Apri Link]({entry.link})\n---"
                        if tipo == "telegram": st.session_state.res_tg.insert(0, item)
                        elif tipo == "reddit": st.session_state.res_reddit.insert(0, item)
                        else: st.session_state.res_web.insert(0, item)

        # Update UI
        container_tg.markdown("\n".join(st.session_state.res_tg) if st.session_state.res_tg else "Nessun nuovo post Telegram")
        container_reddit.markdown("\n".join(st.session_state.res_reddit) if st.session_state.res_reddit else "Nessun nuovo post Reddit")
        container_web.markdown("\n".join(st.session_state.res_web) if st.session_state.res_web else "Nessuna nuova News")
        
        primo_avvio = False
        time.sleep(frequenza * 60)
