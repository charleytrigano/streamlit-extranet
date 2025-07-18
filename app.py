import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar

# --------------- CONFIG --------------- #
st.set_page_config(page_title="Extranet", layout="wide")

# --------------- VARIABLES --------------- #
MOIS_EN_COURS = datetime.now().month
ANNEE_EN_COURS = datetime.now().year

# --------------- FONCTION UTILITAIRE POUR CALENDRIER --------------- #
def generer_calendrier(df, mois, annee):
    jours = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    mois_nom = calendar.month_name[mois]
    nb_jours = calendar.monthrange(annee, mois)[1]
    premier_jour_semaine = calendar.monthrange(annee, mois)[0]  # 0 = lundi

    # Création de la matrice calendrier
    grille = [["" for _ in range(7)] for _ in range(6)]
    jour = 1
    ligne = 0
    col = premier_jour_semaine
    while jour <= nb_jours:
        grille[ligne][col] = str(jour)
        jour += 1
        col += 1
        if col == 7:
            col = 0
            ligne += 1

    # Titre
    st.markdown(f"### 📅 {mois_nom} {annee}")
    st.write("")  # espace

    # Légende couleurs plateformes
    plateformes = df['plateforme'].dropna().unique()
    couleurs = {
        nom: color
        for nom, color in zip(plateformes, ['#a6cee3', '#b2df8a', '#fdbf6f', '#fb9a99', '#cab2d6'])
    }

    st.markdown("**🔹 Légende plateformes :**")
    for p in couleurs:
        st.markdown(f"<span style='background-color:{couleurs[p]};padding:5px;'>{p}</span>", unsafe_allow_html=True)

    # Table calendrier avec réservations
    st.markdown("---")
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    colonnes = [col1, col2, col3, col4, col5, col6, col7]

    for i, j in enumerate(jours):
        colonnes[i].markdown(f"**{j}**")

    for semaine in grille:
        colonnes = st.columns(7)
        for i, jour_str in enumerate(semaine):
            if jour_str == "":
                colonnes[i].markdown(" ")
                continue

            date_jour = datetime(annee, mois, int(jour_str)).date()

            # Rechercher les clients présents ce jour-là
            cell_resas = ""
            for _, row in df.iterrows():
                if pd.isna(row['date_arrivee']) or pd.isna(row['date_depart']):
                    continue
                if row['date_arrivee'] <= date_jour <= row['date_depart']:
                    couleur = couleurs.get(row['plateforme'], "#e0e0e0")
                    cell_resas += f"<div style='background-color:{couleur};padding:2px;margin:1px;font-size:12px;border-radius:4px;'>{row['nom_client']}</div>"

            if cell_resas == "":
                colonnes[i].markdown(jour_str)
            else:
                colonnes[i].markdown(f"**{jour_str}**<br>{cell_resas}", unsafe_allow_html=True)

# --------------- CHARGER FICHIER EXCEL --------------- #
st.sidebar.title("📁 Fichier Réservations")
fichier = st.sidebar.file_uploader("Importer un fichier Excel (.xlsx)", type=["xlsx"])

if fichier:
    df = pd.read_excel(fichier)
    df.columns = df.columns.str.strip()

    try:
        # Nettoyage des dates
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
        df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")

        required_cols = {"nom_client", "date_arrivee", "date_depart", "plateforme", "telephone"}
        if not required_cols.issubset(df.columns):
            st.error(f"❌ Le fichier doit contenir les colonnes : {', '.join(required_cols)}")
        else:
            onglet = st.sidebar.radio("Navigation", ["📋 Tableau", "📆 Calendrier"])

            if onglet == "📋 Tableau":
                st.title("📋 Tableau des Réservations")
                st.dataframe(df)

            elif onglet == "📆 Calendrier":
                mois = st.sidebar.number_input("Mois", min_value=1, max_value=12, value=MOIS_EN_COURS)
                annee = st.sidebar.number_input("Année", min_value=2024, max_value=2100, value=ANNEE_EN_COURS)
                generer_calendrier(df, mois, annee)

    except Exception as e:
        st.error("❌ Erreur lors du traitement du fichier. Détails :")
        st.error(str(e))
else:
    st.warning("Veuillez importer un fichier Excel .xlsx contenant les réservations.")


