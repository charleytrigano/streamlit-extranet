import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import calendar
from datetime import datetime

st.set_page_config(layout="wide")
st.title("📆 Calendrier des réservations")

# ⬆️ Téléversement du fichier Excel
uploaded_file = st.file_uploader("Importer votre fichier .xlsx", type="xlsx")

# ⬇️ Fonction pour dessiner le calendrier mensuel
def draw_calendar(df, mois, annee):
    jours = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    nb_jours = calendar.monthrange(annee, mois)[1]
    cal = [[] for _ in range(6)]
    start_day = (calendar.monthrange(annee, mois)[0] + 1) % 7  # Pour que lundi commence à 0

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

# 🔄 Navigation par mois et année
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        required_cols = {"nom_client", "date_arrivee", "date_depart", "plateforme", "telephone"}
        if not required_cols.issubset(df.columns):
            st.error(f"❌ Le fichier doit contenir les colonnes : {', '.join(required_cols)}")
        else:
            df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
            df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")

            # Sélection du mois et de l’année
            col1, col2 = st.columns(2)
            with col1:
                mois = st.selectbox("Mois", list(range(1, 13)), index=datetime.now().month - 1)
            with col2:
                annee = st.selectbox("Année", list(range(2023, 2031)), index=1)

            # Afficher le calendrier
            draw_calendar(df, mois, annee)

    except Exception as e:
        st.error(f"Erreur lors du traitement du fichier : {e}")






