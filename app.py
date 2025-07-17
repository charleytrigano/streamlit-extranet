import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import calendar
from datetime import datetime, timedelta
import requests

# Configuration initiale
st.set_page_config(layout="wide")
st.title("🏨 Gestion des Réservations Extranet")

# --- Paramètres SMS Free Mobile ---
FREE_API_KEYS = {
    "charley": {"user": "12026027", "key": "1Pat6vSRCLiSXl", "tel": "+33617722379"},
    "annick": {"user": "12026027", "key": "MF7Qjs3C8KxKHz", "tel": "+33611772793"}
}

# --- Téléversement du fichier ---
uploaded_file = st.file_uploader("📂 Importer votre fichier .xlsx", type="xlsx")

# --- Fonction d'envoi de SMS ---
def send_free_sms(user_id, api_key, message):
    url = f"https://smsapi.free-mobile.fr/sendmsg?user={user_id}&pass={api_key}&msg={message}"
    response = requests.get(url)
    return response.status_code == 200

# --- Fonction calendrier interactif ---
def draw_calendar(df, mois, annee):
    jours = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    nb_jours = calendar.monthrange(annee, mois)[1]
    cal = [[] for _ in range(6)]
    start_day = (calendar.monthrange(annee, mois)[0] + 1) % 7

    ligne = 0
    for i in range(start_day):
        cal[ligne].append("")
    for day in range(1, nb_jours + 1):
        cal[ligne].append(day)
        if len(cal[ligne]) == 7:
            ligne += 1

    couleurs = {"Airbnb": "#87CEFA", "Booking": "#FFB6C1", "Autre": "#90EE90"}
    fig = go.Figure()

    for y, semaine in enumerate(cal):
        for x, jour in enumerate(semaine):
            if jour == "":
                continue
            date_str = f"{annee}-{mois:02d}-{jour:02d}"
            clients = df[df["date_arrivee"] == pd.to_datetime(date_str)]
            noms = ""
            couleurs_cases = []
            for _, row in clients.iterrows():
                noms += f"{row['nom_client']} ({row['plateforme']})<br>"
                couleurs_cases.append(couleurs.get(row["plateforme"], "#D3D3D3"))
            couleur_fond = couleurs_cases[0] if couleurs_cases else "#F5F5F5"
            fig.add_shape(type="rect", x0=x, y0=-y, x1=x+1, y1=-(y+1),
                          line=dict(color="gray"), fillcolor=couleur_fond)
            texte = f"<b>{jour}</b><br>{noms}" if noms else f"<b>{jour}</b>"
            fig.add_trace(go.Scatter(x=[x + 0.5], y=[-(y + 0.5)],
                                     text=[texte], mode="text",
                                     hoverinfo="text", textposition="middle center"))

    fig.update_layout(
        title=f"{calendar.month_name[mois]} {annee}",
        xaxis=dict(showgrid=False, zeroline=False, tickvals=list(range(7)), ticktext=jours),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        margin=dict(l=20, r=20, t=60, b=20),
        height=600,
        plot_bgcolor="white"
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Traitement du fichier ---
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # Vérification des colonnes
        required_cols = {"nom_client", "date_arrivee", "date_depart", "plateforme", "telephone",
                         "prix_brut", "prix_net", "charges", "%"}
        if not required_cols.issubset(df.columns):
            st.error(f"❌ Le fichier doit contenir les colonnes : {', '.join(required_cols)}")
        else:
            df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
            df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")

            # 📋 Affichage du tableau
            st.subheader("📋 Tableau des Réservations")
            st.dataframe(df)

            # 📩 Envoi de SMS aux clients arrivant demain
            st.subheader("📩 Envoi de SMS")
            demain = datetime.now() + timedelta(days=1)
            df_demain = df[df["date_arrivee"] == demain.date()]

            if not df_demain.empty:
                for _, row in df_demain.iterrows():
                    msg = f"Bonjour {row['nom_client']}, Nous sommes heureux de vous accueillir demain à Nice. " \
                          f"Un emplacement de parking est à votre disposition. Merci de nous indiquer votre heure d’arrivée. " \
                          f"Bon voyage ! Annick & Charley"
                    sent_1 = send_free_sms(FREE_API_KEYS["charley"]["user"], FREE_API_KEYS["charley"]["key"], msg)
                    sent_2 = send_free_sms(FREE_API_KEYS["annick"]["user"], FREE_API_KEYS["annick"]["key"], msg)

                    st.write(f"📨 SMS envoyé à **{row['nom_client']}** : "
                             f"{'✅' if sent_1 and sent_2 else '❌'}")

            else:
                st.info("Aucune arrivée prévue demain.")

            # 📅 Calendrier visuel
            st.subheader("📆 Calendrier Mensuel")
            col1, col2 = st.columns(2)
            with col1:
                mois = st.selectbox("Mois", list(range(1, 13)), index=datetime.now().month - 1)
            with col2:
                annee = st.selectbox("Année", list(range(2023, 2031)), index=1)

            draw_calendar(df, mois, annee)

    except Exception as e:
        st.error(f"Erreur lors du traitement du fichier : {e}")
