import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import calendar
import io

FICHIER_RESERVATIONS = "reservations.xlsx"

FREE_SMS_KEYS = [
    {"user": "12026027", "key": "1Pat6vSRCLiSXl"},
    {"user": "12026027", "key": "1Pat6vSRCLiSXl"}
]

def envoyer_sms_free(message):
    for sms_config in FREE_SMS_KEYS:
        url = f"https://smsapi.free-mobile.fr/sendmsg?user={sms_config['user']}&pass={sms_config['key']}&msg={message}"
        requests.get(url)

def charger_donnees():
    try:
        df = pd.read_excel(FICHIER_RESERVATIONS)
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
        df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier : {e}")
        return pd.DataFrame(columns=["nom_client", "date_arrivee", "date_depart", "plateforme", "telephone", "prix_brut", "prix_net", "charges", "%"])

def sauvegarder_donnees(df):
    df.to_excel(FICHIER_RESERVATIONS, index=False)

def formulaire_nouvelle_reservation(df):
    st.subheader("➕ Nouvelle réservation")
    with st.form("formulaire"):
        nom_client = st.text_input("Nom du client")
        date_arrivee = st.date_input("Date d'arrivée")
        date_depart = st.date_input("Date de départ")
        plateforme = st.selectbox("Plateforme", ["Airbnb", "Booking", "Autre"])
        telephone = st.text_input("Téléphone")
        prix_brut = st.text_input("Prix brut")
        prix_net = st.text_input("Prix net")
        charges = st.text_input("Charges")
        pourcentage = st.text_input("%")

        submit = st.form_submit_button("✅ Enregistrer")
        if submit:
            nouvelle_ligne = {
                "nom_client": nom_client,
                "date_arrivee": pd.to_datetime(date_arrivee),
                "date_depart": pd.to_datetime(date_depart),
                "plateforme": plateforme,
                "telephone": telephone,
                "prix_brut": prix_brut,
                "prix_net": prix_net,
                "charges": charges,
                "%": pourcentage
            }
            df = pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True)
            sauvegarder_donnees(df)
            st.success("Réservation enregistrée ✅")

def envoyer_sms_jour_avant(df):
    demain = datetime.now().date() + timedelta(days=1)
    df_demain = df[df["date_arrivee"].dt.date == demain]
    for _, row in df_demain.iterrows():
        message = (
            f"Bonjour {row['nom_client']},\n"
            f"Nous sommes heureux de vous accueillir demain à Nice.\n"
            f"Parking sur place disponible.\n"
            f"Merci d’indiquer votre heure d’arrivée.\n"
            f"Bon voyage et à demain !\n"
            f"Annick & Charley"
        )
        try:
            envoyer_sms_free(message)
        except Exception:
            pass

def afficher_calendrier(df):
    st.subheader("📅 Calendrier mensuel")
    mois = st.selectbox("Mois", list(calendar.month_name)[1:], index=datetime.now().month - 1)
    annee = st.selectbox("Année", list(range(datetime.now().year, datetime.now().year + 2)), index=0)
    plateforme_filtre = st.selectbox("Plateforme", ["Toutes"] + df["plateforme"].dropna().unique().tolist())

    mois_index = list(calendar.month_name).index(mois)
    df_filtre = df.copy()
    if plateforme_filtre != "Toutes":
        df_filtre = df_filtre[df_filtre["plateforme"] == plateforme_filtre]
    df_filtre = df_filtre[
        (df_filtre["date_arrivee"].dt.month == mois_index) &
        (df_filtre["date_arrivee"].dt.year == annee)
    ]

    grille = [["" for _ in range(7)] for _ in range(6)]
    premier_jour = datetime(annee, mois_index, 1)
    decalage = premier_jour.weekday()
    jours_dans_mois = calendar.monthrange(annee, mois_index)[1]

    jour = 1
    for ligne in range(6):
        for col in range(7):
            if ligne == 0 and col < decalage:
                continue
            if jour > jours_dans_mois:
                break
            date_jour = datetime(annee, mois_index, jour).date()
            cell_content = ""
            for _, row in df_filtre.iterrows():
                if pd.isna(row["date_arrivee"]) or pd.isna(row["date_depart"]):
                    continue
                debut = row["date_arrivee"].date()
                fin = row["date_depart"].date()
                if debut <= date_jour < fin:
                    emoji = {
                        "Airbnb": "🔴",
                        "Booking": "🔵",
                        "Autre": "🟢"
                    }.get(row["plateforme"], "⚪")
                    cell_content += f"{emoji} {row['nom_client']}\n"
            grille[ligne][col] = cell_content.strip()
            jour += 1

    jours_semaine = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    st.markdown("| " + " | ".join(jours_semaine) + " |")
    st.markdown("|" + "|".join(["---"] * 7) + "|")
    for semaine in grille:
        st.markdown("| " + " | ".join(cell if cell else " " for cell in semaine) + " |")

def afficher_tableau(df):
    st.subheader("📋 Tableau des réservations")
    st.dataframe(df.sort_values(by="date_arrivee"))

    st.download_button(
        label="📥 Télécharger le fichier complet",
        data=convert_to_excel(df),
        file_name="reservations.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def convert_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output

def main():
    st.title("🏨 Extranet Annick & Charley")
    onglet = st.sidebar.radio("Menu", ["📥 Importer / Ajouter", "📅 Calendrier", "📊 Réservations"])

    df = charger_donnees()

    if onglet == "📥 Importer / Ajouter":
        formulaire_nouvelle_reservation(df)
        envoyer_sms_jour_avant(df)

    elif onglet == "📅 Calendrier":
        afficher_calendrier(df)

    elif onglet == "📊 Réservations":
        afficher_tableau(df)

if __name__ == "__main__":
    main()
