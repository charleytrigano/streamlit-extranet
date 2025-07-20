import streamlit as st
import pandas as pd
import calendar
import datetime
import requests

st.set_page_config(layout="wide")
st.title("📅 Extranet Réservations - Nice")

# ---------- CONFIGURATION NUMÉROS & API FREE ----------
NUMEROS_FREE = {
    "charley": {"id": "12026027", "key": "MF7Qjs3C8KxKHz"},
    "autre": {"id": "12026027", "key": "1Pat6vSRCLiSXl", "telephone": "+33611772793"}
}

# ---------- FONCTIONS ----------
def envoyer_sms(nom_client, date_arrivee):
    message = (
        f"Bonjour {nom_client},\n"
        f"Nous sommes heureux de vous accueillir demain à Nice.\n"
        f"Un emplacement de parking est à votre disposition sur place.\n"
        f"Merci de nous indiquer votre heure approximative d’arrivée.\n"
        f"Bon voyage et à demain !\n"
        f"Annick & Charley"
    )
    for user in NUMEROS_FREE.values():
        url = f"https://smsapi.free-mobile.fr/sendmsg?user={user['id']}&pass={user['key']}&msg={requests.utils.quote(message)}"
        requests.get(url)

def charger_donnees():
    df = pd.read_excel("reservations.xlsx")

    # Gestion des dates avec suppression des lignes invalides
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
    df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")
    df = df.dropna(subset=["date_arrivee", "date_depart"])

    # Ajout des colonnes calculées
    df["charges"] = df["prix_brut"] - df["prix_net"]
    df["%"] = round((df["charges"] / df["prix_brut"]) * 100, 2)
    df["nuitees"] = (df["date_depart"] - df["date_arrivee"]).dt.days

    return df

def sauvegarder_donnees(df):
    df.to_excel("reservations.xlsx", index=False)

def afficher_calendrier(df):
    st.subheader("📆 Calendrier mensuel")
    now = datetime.datetime.now()
    mois = st.selectbox("Mois", list(calendar.month_name)[1:], index=now.month - 1)
    annee = st.selectbox("Année", list(range(now.year - 1, now.year + 2)), index=1)

    mois_index = list(calendar.month_name).index(mois)

    df_mois = df[
        (df["date_arrivee"].dt.month == mois_index) &
        (df["date_arrivee"].dt.year == annee)
    ]

    cal = calendar.monthcalendar(annee, mois_index)
    plateforme_couleurs = {"Booking": "#AED6F1", "Airbnb": "#F9E79F", "Autre": "#D5F5E3"}

    st.markdown("<style>table, th, td {border: 1px solid gray; padding: 5px;} th {background-color: #f2f2f2;}</style>", unsafe_allow_html=True)
    cal_html = "<table><tr>" + "".join([f"<th>{day}</th>" for day in ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]]) + "</tr>"

    for week in cal:
        cal_html += "<tr>"
        for day in week:
            cell = ""
            if day != 0:
                date_jour = datetime.date(annee, mois_index, day)
                clients_du_jour = df[
                    (df["date_arrivee"].dt.date <= date_jour) & (df["date_depart"].dt.date > date_jour)
                ]
                for _, row in clients_du_jour.iterrows():
                    couleur = plateforme_couleurs.get(row["plateforme"], "#FFFFFF")
                    cell += f"<div style='background-color:{couleur}; padding:2px; margin:1px;'>{row['nom_client']}</div>"
                cal_html += f"<td><strong>{day}</strong><br>{cell}</td>"
            else:
                cal_html += "<td></td>"
        cal_html += "</tr>"
    cal_html += "</table>"

    st.markdown(cal_html, unsafe_allow_html=True)

def afficher_tableau(df):
    st.subheader("📋 Réservations")
    st.dataframe(df.sort_values("date_arrivee"))

def ajouter_reservation(df):
    st.subheader("➕ Ajouter une réservation")

    with st.form("form_ajout"):
        nom_client = st.text_input("Nom du client")
        date_arrivee = st.date_input("Date d'arrivée")
        date_depart = st.date_input("Date de départ")
        plateforme = st.selectbox("Plateforme", ["Booking", "Airbnb", "Autre"])
        telephone = st.text_input("Téléphone")
        prix_brut = st.number_input("Prix brut", min_value=0.0)
        prix_net = st.number_input("Prix net", min_value=0.0)

        valider = st.form_submit_button("Enregistrer")

    if valider:
        new_row = {
            "nom_client": nom_client,
            "date_arrivee": pd.to_datetime(date_arrivee),
            "date_depart": pd.to_datetime(date_depart),
            "plateforme": plateforme,
            "telephone": telephone,
            "prix_brut": prix_brut,
            "prix_net": prix_net,
        }
        new_row["charges"] = prix_brut - prix_net
        new_row["%"] = round((new_row["charges"] / prix_brut) * 100, 2) if prix_brut else 0
        new_row["nuitees"] = (pd.to_datetime(date_depart) - pd.to_datetime(date_arrivee)).days

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        sauvegarder_donnees(df)
        st.success("Réservation ajoutée avec succès ✅")

def envoyer_sms_jour(df):
    aujourd_hui = datetime.date.today()
    demain = aujourd_hui + datetime.timedelta(days=1)

    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
    df_sms = df[df["date_arrivee"].dt.date == demain]

    if not df_sms.empty:
        for _, row in df_sms.iterrows():
            envoyer_sms(row["nom_client"], row["date_arrivee"])
        st.success(f"📩 {len(df_sms)} SMS envoyés aux clients arrivant demain.")
    else:
        st.info("Aucun client n'arrive demain.")

# ---------- APP ----------
df = charger_donnees()
onglet = st.sidebar.radio("Navigation", ["Tableau", "Calendrier", "Nouvelle réservation"])

if onglet == "Tableau":
    afficher_tableau(df)
    envoyer_sms_jour(df)

elif onglet == "Calendrier":
    afficher_calendrier(df)

elif onglet == "Nouvelle réservation":
    ajouter_reservation(df)
