import streamlit as st
import requests
import feedparser
import time
import random

# --- 1. CONFIGURAZIONE E FILTRI ---
TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]
SITO_PROMO = "https://topstaybergamo.com"

BLACKLIST_SITI = ["corriere.it", "repubblica.it", "ansa.it", "ecodibergamo.it", "bergamonews.it"]
FILTRI_NEGATIVI = ["atalanta", "serie a", "calcio", "partita", "stadio", "risultati", "campionato", "monza"]

# --- 2. INTERFACCIA ---
st.set_page_config(page_title="TopStay Pro Monitor", layout="wide")
st.title("💎 TopStay: Monitor Diviso per Fonti")

# Sidebar per impostazioni
st.sidebar.header("Impostazioni")
frequenza = st.sidebar.slider("Aggiornamento (minuti)", 5, 60, 15)
parole_input = st.text_area("Parole chiave (esatte tra virgolette):", '"dormire a Bergamo", "hotel Bergamo centro"')

# Creazione delle Schede (Tabs)
tab_tg, tab_reddit, tab_web = st.tabs(["📲 Telegram", "🧡 Reddit", "🌐 Google News/Blog"])

# --- 3. LOGICA DI MONITORAGGIO ---
if st.button("🚀 AVVIA MONITORAGGIO"):
    lista_parole = [p.strip() for p in parole_input.split(",") if p.strip()]
    visti = set()
    primo_avvio = True
    
    # Placeholder per visualizzare i risultati nelle schede corrette
    area_tg = tab_tg.empty()
    area_reddit = tab_reddit.empty()
    area_web = tab_web.empty()

    while True:
        # Liste temporanee per visualizzare gli ultimi risultati nelle Tab
        results_tg, results_reddit, results_web = [], [], []

        for parola in lista_parole:
            # Ricerca forzata: usiamo le virgolette se l'utente non le ha messe
            query_pulita = parola if '"' in parola else f'"{parola}"'
            q_url = query_pulita.replace(" ", "+")

            fonti = {
                "reddit": f"https://www.reddit.com/search.rss?q={q_url}+self:yes&sort=new",
                "web": f"https://news.google.com/rss/search?q={q_url}&hl=it&gl=IT&ceid=IT:it",
                "telegram": f"https://news.google.com/rss/search?q={q_url}+site:t.me&hl=it&gl=IT&ceid=IT:it"
            }

            for tipo, url in fonti.items():
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    titolo = entry.title.lower()
                    # Verifica che TUTTE le parole della chiave siano presenti (Super Filtro)
                    parole_chiave = parola.replace('"', '').lower().split()
                    match_reale = all(p in titolo for p in parole_chiave)

                    if entry.link not in visti and match_reale and not any(f in titolo for f in FILTRI_NEGATIVI):
                        if not primo_avvio:
                            # Invia a Telegram per notifica immediata
                            msg = f"📍 FONTE: {tipo.upper()}\n📌 {entry.title}\n🔗 {entry.link}"
                            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                                          data={"chat_id": CHAT_ID, "text": msg})
                        
                        visti.add(entry.link)
                        
                        # Organizza per le Tab di Streamlit
                        res_item = f"- **{entry.title}** \n[Apri Link]({entry.link})"
                        if tipo == "telegram": results_tg.append(res_item)
                        elif tipo == "reddit": results_reddit.append(res_item)
                        else: results_web.append(res_item)

        # Aggiorna l'interfaccia Streamlit
        area_tg.markdown("\n".join(results_tg) if results_tg else "Nessun nuovo post Telegram")
        area_reddit.markdown("\n".join(results_reddit) if results_reddit else "Nessun nuovo post Reddit")
        area_web.markdown("\n".join(results_web) if results_web else "Nessun nuovo post Web")
        
        primo_avvio = False
        time.sleep(frequenza * 60)
