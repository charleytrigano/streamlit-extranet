import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar

st.set_page_config(layout="wide")

# Onglets
page = st.sidebar.radio("Navigation", ["📁 Importer les réservations", "📆 Calendrier mensuel"])

# Fonction pour générer un calendrier mensuel
def draw_calendar(df, mois, annee):
    jours = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    mois_nom = calendar.month_name[mois]
    nb_jours = calendar.monthrange(annee, mois)[1]

    # Créer une grille vide
    cal = [[] for _ in range(6)]  # 6 lignes max
    start_day = calendar.monthrange(annee, mois)[0]  # 0 = Monday

    ligne = 0
    for i in range(start_day):
        cal[ligne].append("")  # Jours vides avant le 1er

    for day in range(1, nb_jours + 1):
        cal[ligne].append(day)
        if len(cal[ligne]) == 7:
            ligne += 1

    # Mapping couleur par plateforme
    couleurs = {
        "Airbnb": "#87CEFA",  # bleu clair
        "Booking": "#FFB6C1",  # rose
        "Autre": "#90EE90"     # vert clair
    }

    fig = go.Figure()

    # Créer chaque case du calendrier
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

            fig.add_shape(type="rect",
                          x0=x, y0=-y, x1=x+1, y1=-(y+1),
                          line=dict(color="gray"),
                          fillcolor=couleur_fond)

            texte = f"<b>{jour}</b><br>{noms}" if noms else f"<b>{jour}</b>"
            fig.add_trace(go.Scatter(x=[x + 0.5],
                                     y=[-(y + 0.5)],
                                     text=[texte],
                                     mode="text",
                                     hoverinfo="text",
                                     textposition="middle center"))

    fig.update_layout(
        title=f"{mois_nom} {annee}",
        xaxis=dict(showgrid=False, zeroline=False, tickvals=list(range(7)), ticktext=jours),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        margin=dict(l=20, r=20, t=60, b=20),
        height=600,
        plot_bgcolor="white"
    )

    st.plotly_chart(fig, use_container_width=True)

# Onglet 2 : 📆 Calendrier
if page == "📆 Calendrier mensuel":
    st.title("📆 Calendrier des réservations")

    uploaded_file = st.file_uploader("Importer votre fichier .xlsx", type="xlsx")

    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)

            # Nettoyage
            df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")

            mois = st.number_input("Mois", min_value=1, max_value=12, value=datetime.now().month)
            annee = st.number_input("Année", min_value=2023, max_value=2100, value=datetime.now().year)

            draw_calendar(df, mois, annee)

        except Exception as e:
            st.error(f"Erreur lors du chargement du fichier : {e}")
    else:
        st.info("Importez un fichier pour afficher le calendrier.")






