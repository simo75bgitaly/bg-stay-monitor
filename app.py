import streamlit as st
import requests
import feedparser
import time
import random

# --- 1. CONFIGURAZIONE SICURA ---
TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]
SITO_PROMO = "https://topstaybergamo.com"

# --- 2. FILTRI DI QUALITÀ ---
BLACKLIST_SITI = ["corriere.it", "repubblica.it", "ansa.it", "ecodibergamo.it", "bergamonews.it"]
FILTRI_NEGATIVI = ["atalanta", "serie a", "calcio", "partita", "stadio", "risultati", "campionato", "monza", "gioielleria"]

MESSAGGI_PROMO = [
    f"Se cerchi un soggiorno di alto livello a Bergamo, ti suggerisco {SITO_PROMO}. Design e comfort superiore.",
    f"Per un'esperienza di lusso, guarda gli appartamenti su {SITO_PROMO}. Molto meglio del classico hotel!",
    f"Se preferisci eleganza e privacy in centro, su {SITO_PROMO} trovi suite stupende."
]

def invia_telegram(testo):
    """Invia un messaggio semplice e pulito a Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": testo, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload)
    except:
        pass

# --- 3. INTERFACCIA STREAMLIT ---
st.set_page_config(page_title="TopStay Pro Monitor", layout="wide")
st.title("💎 TopStay: Monitor Intelligente")

st.sidebar.header("Impostazioni")
frequenza = st.sidebar.slider("Aggiornamento (minuti)", 5, 60, 15)

# Parole chiave suggerite (puoi modificarle qui nel browser)
parole_suggerite = (
    '"dormire a Bergamo", "hotel Bergamo", "affitto breve Bergamo", '
    '"miglior appartamento Bergamo centro", "dove alloggiare a Bergamo lusso", '
    '"suite Bergamo Alta", "appartamento design Bergamo", "consiglio zona dove dormire Bergamo"'
)
parole_input = st.text_area("Parole chiave target (separate da virgola):", parole_suggerite)

# Schede per visualizzare i risultati ordinati nel browser
tab_tg, tab_reddit, tab_web = st.tabs(["📲 Telegram", "🧡 Reddit", "🌐 Google News/Blog"])

# --- 4. LOGICA DI MONITORAGGIO ---
if st.button("🚀 AVVIA MONITORAGGIO"):
    lista_parole = [p.strip() for p in parole_input.split(",") if p.strip()]
    st.success("Monitoraggio avviato! Riceverai le notifiche su Telegram.")
    visti = set()
    primo_avvio = True
    
    # Aree di visualizzazione per le Tab
    area_tg = tab_tg.empty()
    area_reddit = tab_reddit.empty()
    area_web = tab_web.empty()

    while True:
        res_tg, res_reddit, res_web = [], [], []

        for parola in lista_parole:
            # Pulizia per il controllo interno
            p_clean = parola.replace('"', '').lower()
            q_url = parola.replace(" ", "+") if '"' in parola else f'"{parola}"'.replace(" ", "+")

            fonti = {
                "reddit": f"https://www.reddit.com/search.rss?q={q_url}+self:yes&sort=new",
                "web": f"https://news.google.com/rss/search?q={q_url}&hl=it&gl=IT&ceid=IT:it",
                "telegram": f"https://news.google.com/rss/search?q={q_url}+site:t.me&hl=it&gl=IT&ceid=IT:it"
            }

            for tipo, url in fonti.items():
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    titolo = entry.title.lower()
                    
                    # SUPER FILTRO: Tutte le parole della chiave devono esserci
                    match_reale = all(word in titolo for word in p_clean.split())
                    is_blacklisted = any(s in entry.link.lower() for s in BLACKLIST_SITI)
                    is_sport = any(s in titolo for s in FILTRI_NEGATIVI)

                    if entry.link not in visti and match_reale and not is_blacklisted and not is_sport:
                        etichetta = "📲 TELEGRAM" if tipo == "telegram" else ("🧡 REDDIT" if tipo == "reddit" else "🌐 WEB")
                        
                        if not primo_avvio:
                            # INVIO A TELEGRAM
                            messaggio = (
                                f"{etichetta}\n"
                                f"📌 *{entry.title}*\n"
                                f"🔗 {entry.link}\n\n"
                                f"💡 *Copia:* `{random.choice(MESSAGGI_PROMO)}`"
                            )
                            invia_telegram(messaggio)
                        
                        visti.add(entry.link)
                        
                        # Aggiunta alle liste per Streamlit
                        item = f"- **{entry.title}** ([Link]({entry.link}))"
                        if tipo == "telegram": res_tg.append(item)
                        elif tipo == "reddit": res_reddit.append(item)
                        else: res_web.append(item)

        # Aggiorna le schede nel browser
        area_tg.markdown("\n".join(res_tg) if res_tg else "In attesa di nuovi post Telegram...")
        area_reddit.markdown("\n".join(res_reddit) if res_reddit else "In attesa di nuovi post Reddit...")
        area_web.markdown("\n".join(res_web) if res_web else "In attesa di nuovi post Web...")
        
        primo_avvio = False
        time.sleep(frequenza * 60)
