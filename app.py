import streamlit as st
import pandas as pd
import calendar
import datetime
import requests
from io import BytesIO

# ----------------------------
# 📩 Fonction : Envoi SMS via Free Mobile
# ----------------------------
def envoyer_sms(message):
    destinataires = [
        {"user": "12026027", "key": "MF7Qjs3C8KxKHz"},
        {"user": "12026027", "key": "1Pat6vSRCLiSXl"},
    ]
    for dest in destinataires:
        try:
            url = f"https://smsapi.free-mobile.fr/sendmsg?user={dest['user']}&pass={dest['key']}&msg={message}"
            requests.get(url)
        except Exception as e:
            st.error(f"Erreur envoi SMS : {e}")

# ----------------------------
# 🗓️ Affichage Calendrier
# ----------------------------
def afficher_calendrier(df):
    st.subheader("📆 Calendrier mensuel")

    mois_selectionne = st.selectbox("Choisissez un mois :", list(calendar.month_name)[1:])
    annee_selectionnee = st.selectbox("Année :", list(range(datetime.datetime.now().year, datetime.datetime.now().year + 2)))

    mois_index = list(calendar.month_name).index(mois_selectionne)

    # Couleurs par plateforme
    couleurs_plateformes = {
        "Booking": "#FFB6C1",  # Rose
        "Airbnb": "#ADD8E6",   # Bleu clair
        "Autre": "#90EE90"     # Vert clair
    }

    filtered_df = df[
        (df["date_arrivee"].dt.month == mois_index) &
        (df["date_arrivee"].dt.year == annee_selectionnee)
    ]

    jours_mois = calendar.monthrange(annee_selectionnee, mois_index)[1]
    jours = [datetime.date(annee_selectionnee, mois_index, jour) for jour in range(1, jours_mois + 1)]

    calendrier = {jour: "" for jour in jours}

    for _, row in filtered_df.iterrows():
        arrivee = row["date_arrivee"].date()
        depart = row["date_depart"].date()
        nom = row["nom_client"]
        plateforme = row["plateforme"]

        couleur = couleurs_plateformes.get(plateforme, "#D3D3D3")
        jours_sejour = pd.date_range(arrivee, depart - datetime.timedelta(days=0)).date

        for jour in jours_sejour:
            if jour in calendrier:
                calendrier[jour] += f"🧑 {nom} ({plateforme})\n"

    # Affichage
    cols = st.columns(7)
    for i, day in enumerate(calendar.day_abbr):
        cols[i].markdown(f"**{day}**")

    row = 0
    for jour in jours:
        col_idx = (jour.weekday() + 1) % 7
        if col_idx == 0 and jour.day != 1:
            row += 1
            cols = st.columns(7)
        contenu = calendrier[jour]
        couleur = "#f0f0f0" if contenu == "" else "#d0f0c0"
        cols[col_idx].markdown(f"<div style='background-color:{couleur}; padding:5px'>{jour.day}<br>{contenu}</div>", unsafe_allow_html=True)

# ----------------------------
# 📈 Rapport mensuel
# ----------------------------
def rapport_mensuel(df):
    st.subheader("📊 Rapport mensuel par plateforme")
    df["mois"] = df["date_arrivee"].dt.to_period("M")
    rapport = df.groupby(["mois", "plateforme"])["prix_net"].sum().reset_index()
    rapport["mois"] = rapport["mois"].astype(str)
    st.dataframe(rapport)

# ----------------------------
# 📋 Tableau des réservations
# ----------------------------
def afficher_tableau(df):
    st.subheader("📋 Réservations")
    st.dataframe(df.sort_values("date_arrivee"))

# ----------------------------
# 🆕 Nouvelle réservation
# ----------------------------
def ajouter_reservation(df):
    with st.form("Ajouter réservation"):
        nom = st.text_input("Nom client")
        plateforme = st.selectbox("Plateforme", ["Booking", "Airbnb", "Autre"])
        date_arrivee = st.date_input("Date d'arrivée")
        date_depart = st.date_input("Date de départ")
        telephone = st.text_input("Téléphone")
        prix_brut = st.number_input("Prix brut", step=1.0)
        prix_net = st.number_input("Prix net", step=1.0)
        charges = st.number_input("Charges", step=1.0)
        pourcentage = st.number_input("Pourcentage", step=1.0)

        submit = st.form_submit_button("Valider")
        if submit:
            new_row = pd.DataFrame({
                "nom_client": [nom],
                "plateforme": [plateforme],
                "date_arrivee": [pd.to_datetime(date_arrivee)],
                "date_depart": [pd.to_datetime(date_depart)],
                "telephone": [telephone],
                "prix_brut": [prix_brut],
                "prix_net": [prix_net],
                "charges": [charges],
                "%": [pourcentage],
            })
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_excel("reservations.xlsx", index=False)
            st.success("Réservation ajoutée avec succès ✅")

            # SMS si dans 24h
            if date_arrivee == datetime.date.today() + datetime.timedelta(days=1):
                message = f"Bonjour {nom}, nous sommes heureux de vous accueillir demain à Nice. Un parking est disponible. Merci d’indiquer votre heure d’arrivée. Bon voyage ! - Annick & Charley"
                envoyer_sms(message)

# ----------------------------
# ▶️ Exécution principale
# ----------------------------
def main():
    st.set_page_config(layout="wide")
    st.title("🏨 Extranet - Gestion des Réservations")

    onglet = st.sidebar.radio("Navigation", ["Tableau", "Calendrier", "Ajouter", "Rapport"])

    try:
        df = pd.read_excel("reservations.xlsx", engine="openpyxl")
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
        df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")
    except Exception as e:
        st.error(f"Erreur de chargement : {e}")
        return

    if onglet == "Tableau":
        afficher_tableau(df)

    elif onglet == "Calendrier":
        afficher_calendrier(df)

    elif onglet == "Ajouter":
        ajouter_reservation(df)

    elif onglet == "Rapport":
        rapport_mensuel(df)

if __name__ == "__main__":
    main()
