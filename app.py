import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import calendar
from datetime import datetime

st.set_page_config(layout="wide")

# Fichier .xlsx
uploaded_file = st.file_uploader("Importer votre fichier .xlsx", type="xlsx")

def draw_calendar(df, mois, annee):
    jours = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    nb_jours = calendar.monthrange(annee, mois)[1]
    cal = [[] for _ in range(6)]
    start_day = calendar.monthrange(annee, mois)[0]

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

    fig.update_layout(title=f"{calendar.month_name[mois]} {annee}",
                      xaxis=dict(showgrid=False, zeroline=False, tickvals=list(range(7)), ticktext=jours),
                      yaxis=dict(showgrid=False, zeroline=False, visible=False),
                      margin=dict(l=20, r=20, t=60, b=20),
                      height=600,
                      plot_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")

    mois = st.number_input("Mois", 1, 12, value=datetime.now().month)
    annee = st.number_input("Année", 2023, 2100, value=datetime.now().year)
    draw_calendar(df, mois, annee)






