import streamlit as st
import pandas as pd
import datetime
import calendar
import requests
from io import BytesIO

st.set_page_config(page_title="Extranet Réservations", layout="wide")

# ---------------------- Config
FREE_SMS_KEYS = [
    {"user": "12026027", "key": "1Pat6vSRCLiSXl", "phone": "+33611772793"},
    {"user": "12026027", "key": "MF7Qjs3C8KxKHz", "phone": "+33617722379"}
]

# ---------------------- Fonctions utiles

def envoyer_sms_free(message):
    for dest in FREE_SMS_KEYS:
        payload = {
            "user": dest["user"],
            "pass": dest["key"],
            "msg": message
        }
        try:
            requests.get("https://smsapi.free-mobile.fr/sendmsg", params=payload)
        except Exception as e:
            st.warning(f"Erreur SMS vers {dest['phone']} : {e}")

def afficher_tableau(df):
    st.subheader("📋 Tableau des réservations")
    st.dataframe(df)

def convertir_xlsx(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def dessiner_calendrier(df):
    st.subheader("📆 Calendrier des réservations")
    aujourdhui = datetime.date.today()
    mois = st.selectbox("Choisir un mois :", range(1, 13), index=aujourdhui.month - 1)
    annee = st.selectbox("Choisir une année :", range(aujourdhui.year - 1, aujourdhui.year + 2), index=1)

    cal = calendar.monthcalendar(annee, mois)
    jours = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]

    platform_colors = {
        "Airbnb": "#f55",
        "Booking": "#55f",
        "Autre": "#5f5"
    }

    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
    df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")
    df = df.dropna(subset=["date_arrivee", "date_depart"])

    data = {}
    for _, row in df.iterrows():
        debut = row["date_arrivee"].date()
        fin = row["date_depart"].date()
        nom = row["nom_client"]
        plateforme = row.get("plateforme", "Autre")

        jours_sejour = pd.date_range(debut, fin - pd.Timedelta(days=1)).date
        for jour in jours_sejour:
            if jour.month == mois and jour.year == annee:
                data.setdefault(jour.day, []).append((nom, plateforme))

    # Affichage du calendrier
    st.markdown("### 📅 Vue mensuelle")
    cal_html = "<table style='width:100%; border-collapse:collapse;'>"
    cal_html += "<tr>" + "".join([f"<th>{j}</th>" for j in jours]) + "</tr>"
    for semaine in cal:
        cal_html += "<tr>"
        for jour in semaine:
            if jour == 0:
                cal_html += "<td style='padding:10px; border:1px solid #ccc;'></td>"
            else:
                contenu = ""
                if jour in data:
                    for nom, plateforme in data[jour]:
                        couleur = platform_colors.get(plateforme, "#ddd")
                        contenu += f"<div style='background:{couleur}; padding:2px; margin:1px; font-size:12px;'>{nom}</div>"
                cal_html += f"<td style='padding:5px; border:1px solid #ccc; vertical-align:top; min-height:60px;'><b>{jour}</b><br>{contenu}</td>"
        cal_html += "</tr>"
    cal_html += "</table>"
    st.markdown(cal_html, unsafe_allow_html=True)

# ---------------------- Interface

st.title("🏨 Portail Extranet Streamlit")

fichier_xlsx = st.file_uploader("📁 Importer le fichier de réservations (.xlsx)", type="xlsx")

if fichier_xlsx:
    try:
        df = pd.read_excel(fichier_xlsx)

        # Nettoyage des dates
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
        df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")
        df = df.dropna(subset=["date_arrivee", "date_depart"])

        required_columns = {"nom_client", "date_arrivee", "date_depart", "plateforme", "telephone", "prix_brut", "prix_net", "charges", "%"}
        if not required_columns.issubset(df.columns):
            st.error(f"❌ Le fichier doit contenir les colonnes : {', '.join(required_columns)}")
        else:
            onglet = st.radio("Navigation", ["📋 Réservations", "📆 Calendrier", "➕ Nouvelle réservation"])

            if onglet == "📋 Réservations":
                afficher_tableau(df)

                excel_data = convertir_xlsx(df)
                st.download_button("💾 Télécharger le fichier", data=excel_data, file_name="reservations_export.xlsx")

            elif onglet == "📆 Calendrier":
                dessiner_calendrier(df)

            elif onglet == "➕ Nouvelle réservation":
                with st.form("formulaire_resa"):
                    nom_client = st.text_input("Nom du client")
                    plateforme = st.selectbox("Plateforme", ["Airbnb", "Booking", "Autre"])
                    telephone = st.text_input("Téléphone (ex: +33612345678)")
                    date_arrivee = st.date_input("Date d'arrivée")
                    date_depart = st.date_input("Date de départ")
                    prix_brut = st.text_input("Prix brut")
                    prix_net = st.text_input("Prix net")
                    charges = st.text_input("Charges")
                    pourcentage = st.text_input("%")

                    submit = st.form_submit_button("Enregistrer")

                if submit:
                    nouvelle = pd.DataFrame([{
                        "nom_client": nom_client,
                        "date_arrivee": pd.to_datetime(date_arrivee),
                        "date_depart": pd.to_datetime(date_depart),
                        "plateforme": plateforme,
                        "telephone": telephone,
                        "prix_brut": prix_brut,
                        "prix_net": prix_net,
                        "charges": charges,
                        "%": pourcentage
                    }])
                    df = pd.concat([df, nouvelle], ignore_index=True)
                    df.to_excel("reservations.xlsx", index=False)

                    message = (
                        f"Reservation : {plateforme}\n"
                        f"Client : {nom_client}\n"
                        f"Arrive le : {date_arrivee}\n"
                        f"Depart le : {date_depart}\n"
                        f"Bon voyage et à demain !\n"
                        f"Annick & Charley"
                    )
                    envoyer_sms_free(message)
                    st.success("Réservation enregistrée et SMS envoyé.")
    except Exception as e:
        st.error(f"Erreur lors du traitement du fichier. Détails :\n\n{e}")
