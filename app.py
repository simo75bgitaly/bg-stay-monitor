import streamlit as st
import requests
import feedparser
import time
import random

# --- 1. CONFIGURAZIONE ---
TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]
SITO_PROMO = "https://topstaybergamo.com"

# Filtri anti-sport (fondamentali)
FILTRI_NEGATIVI = [
    "atalanta", "serie a", "serie b", "calcio", "basket", "hockey", 
    "vince", "coppa", "campionato", "punteggio", "monza", "milano", 
    "inter", "juve", "fiorentina", "parma", "sport", "risultati"
]

# --- 2. INTERFACCIA ---
st.set_page_config(page_title="TopStay Pro Monitor", layout="centered", page_icon="💎")

# CSS per abbellire l'interfaccia
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #007bff; color: white; }
    .stExpander { border: 1px solid #007bff; border-radius: 10px; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("💎 TopStay Monitor Pro")
st.caption("Ricerca intelligente di opportunità immobiliari e turistiche a Bergamo")

# Inizializzazione memoria sessione e contatori
for key in ['res_tg', 'res_reddit', 'res_web', 'count_tg', 'count_reddit', 'count_web']:
    if key not in st.session_state: 
        st.session_state[key] = [] if 'res' in key else 0

# Sidebar con controlli puliti
with st.sidebar:
    st.header("⚙️ Pannello Controllo")
    if st.button("🗑️ PULISCI SCHERMO"):
        for key in ['res_tg', 'res_reddit', 'res_web', 'count_tg', 'count_reddit', 'count_web']:
            st.session_state[key] = [] if 'res' in key else 0
        st.success("Reset effettuato!")
    
    frequenza = st.sidebar.slider("Intervallo controllo (min)", 5, 60, 15)
    st.divider()
    st.write("📊 **Statistiche Sessione**")
    st.write(f"📲 Telegram: {st.session_state.count_tg}")
    st.write(f"🌐 Web/News: {st.session_state.count_web}")

# Box input semplificato (ora basta mettere i concetti, il bot li incrocia con Bergamo)
parole_alloggio_default = "dormire, hotel, affitto breve, soggiornare, casa vacanze, alloggio, appartamento, suite"
st.subheader("🎯 Cosa stiamo cercando?")
parole_input = st.text_area("Parole chiave (il bot cercherà queste + 'Bergamo'):", parole_alloggio_default)

# Contenitori per i risultati
container_tg = st.expander(f"📲 SOCIAL & TELEGRAM ({st.session_state.count_tg})", expanded=True)
container_reddit = st.expander(f"🧡 DOMANDE REDDIT ({st.session_state.count_reddit})", expanded=False)
container_web = st.expander(f"🌐 NEWS & BLOG ({st.session_state.count_web})", expanded=False)

def invia_telegram(tipo, titolo, link):
    emoji = "📲" if tipo == "telegram" else ("🧡" if tipo == "reddit" else "🌐")
    testo = (
        f"————————————————\n"
        f"{emoji} *NUOVO MATCH: {tipo.upper()}*\n"
        f"————————————————\n"
        f"📌 {titolo}\n\n"
        f"🔗 [APRI LINK]({link})\n"
        f"————————————————"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": testo, "parse_mode": "Markdown"})

# --- 3. LOGICA DI RICERCA FLESSIBILE ---
if st.button("🚀 AVVIA MONITORAGGIO"):
    termini = [p.strip().lower() for p in parole_input.split(",") if p.strip()]
    st.info("Monitoraggio intelligente attivo...")
    progress_bar = st.progress(0)
    
    visti = set()
    primo_avvio = True

    while True:
        # Loop di ricerca
        for i, termine in enumerate(termini):
            progress_bar.progress((i + 1) / len(termini))
            
            # Cerchiamo "Bergamo" + il termine specifico
            query_url = f'Bergamo+{termine.replace(" ", "+")}'
            
            fonti = {
                "reddit": f"https://www.reddit.com/search.rss?q={query_url}&sort=new",
                "web": f"https://news.google.com/rss/search?q={query_url}&hl=it&gl=IT&ceid=IT:it",
                "telegram": f"https://news.google.com/rss/search?q={query_url}+site:t.me&hl=it&gl=IT&ceid=IT:it"
            }

            for tipo, url in fonti.items():
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    titolo_low = entry.title.lower()
                    
                    # LOGICA FLESSIBILE: Deve esserci Bergamo E il termine
                    match = "bergamo" in titolo_low and termine in titolo_low
                    no_calcio = not any(s in titolo_low for s in FILTRI_NEGATIVI)
                    no_bb = all(x not in titolo_low for x in ["b&b", "serie b", " b "])

                    if entry.link not in visti and match and no_calcio and no_bb:
                        if not primo_avvio:
                            invia_telegram(tipo, entry.title, entry.link)
                        
                        visti.add(entry.link)
                        item = f"🔔 **{termine.upper()}**\n{entry.title}\n[Link]({entry.link})\n---"
                        
                        # Aggiornamento liste e contatori
                        if tipo == "telegram": 
                            st.session_state.res_tg.insert(0, item)
                            st.session_state.count_tg += 1
                        elif tipo == "reddit": 
                            st.session_state.res_reddit.insert(0, item)
                            st.session_state.count_reddit += 1
                        else: 
                            st.session_state.res_web.insert(0, item)
                            st.session_state.count_web += 1

        # Aggiornamento interfaccia
        container_tg.markdown("\n".join(st.session_state.res_tg) if st.session_state.res_tg else "Nessun nuovo post")
        container_reddit.markdown("\n".join(st.session_state.res_reddit) if st.session_state.res_reddit else "Nessun post Reddit")
        container_web.markdown("\n".join(st.session_state.res_web) if st.session_state.res_web else "Nessuna News")
        
        primo_avvio = False
        time.sleep(frequenza * 60)
