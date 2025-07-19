import streamlit as st
import pandas as pd
import calendar
import datetime
import requests
from io import BytesIO

# Configuration Free Mobile (à adapter selon ton compte)
FREE_API_1 = {
    "user": "12026027",
    "key": "1Pat6vSRCLiSXl",
    "number": "+33611772793"
}
FREE_API_2 = {
    "user": "12026027",
    "key": "MF7Qjs3C8KxKHz",
    "number": "+33617722379"
}

FICHIER = "reservations.xlsx"

# Charger les données
@st.cache_data
def charger_reservations():
    try:
        df = pd.read_excel(FICHIER)
        df['date_arrivee'] = pd.to_datetime(df['date_arrivee'])
        df['date_depart'] = pd.to_datetime(df['date_depart'])
        return df
    except Exception as e:
        st.error(f"Erreur de chargement : {e}")
        return pd.DataFrame(columns=[
            "nom_client", "date_arrivee", "date_depart", "plateforme",
            "telephone", "prix_brut", "prix_net", "charges", "%"
        ])

def sauvegarder_reservations(df):
    df.to_excel(FICHIER, index=False)

def envoyer_sms(message):
    for api in [FREE_API_1, FREE_API_2]:
        try:
            url = f"https://smsapi.free-mobile.fr/sendmsg?user={api['user']}&pass={api['key']}&msg={requests.utils.quote(message)}"
            r = requests.get(url)
            if r.status_code != 200:
                st.warning(f"❌ Échec SMS à {api['number']}")
        except Exception as e:
            st.warning(f"Erreur SMS : {e}")

# Affichage calendrier type Airbnb
def afficher_calendrier(df):
    st.subheader("📅 Calendrier mensuel")
    today = datetime.date.today()
    mois = st.slider("Mois", 1, 12, today.month)
    annee = st.slider("Année", today.year, today.year + 1, today.year)

    cal = calendar.Calendar()
    mois_data = [date for date in cal.itermonthdates(annee, mois)]

    data_grid = []
    for semaine in range(0, len(mois_data), 7):
        ligne = []
        for jour in mois_data[semaine:semaine+7]:
            cell = ""
            for _, row in df.iterrows():
                debut = row['date_arrivee'].date()
                fin = row['date_depart'].date()
                if pd.notna(debut) and pd.notna(fin):
                    if debut <= jour < fin:
                        nom = row["nom_client"]
                        plateforme = row["plateforme"]
                        couleur = "🔵" if "Booking" in plateforme else "🟢"
                        cell += f"{couleur} {nom}\n"
            ligne.append(cell.strip())
        data_grid.append(ligne)

    days = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    st.markdown("### Réservations")
    st.table(pd.DataFrame(data_grid, columns=days))

# Interface principale
st.set_page_config(page_title="Portail Extranet", layout="wide")
st.title("🏨 Portail Extranet - Gestion des réservations")

onglet = st.sidebar.radio("Navigation", ["📋 Réservations", "➕ Nouvelle réservation", "📅 Calendrier"])

df = charger_reservations()

# Onglet Réservations
if onglet == "📋 Réservations":
    st.subheader("📋 Réservations enregistrées")
    st.dataframe(df)

    index = st.number_input("🔍 Modifier ou supprimer la ligne N° :", min_value=0, max_value=len(df)-1, step=1)

    with st.expander("✏️ Modifier cette réservation"):
        for col in df.columns:
            new_val = st.text_input(f"{col}", value=str(df.at[index, col]))
            df.at[index, col] = new_val

        if st.button("💾 Enregistrer les modifications"):
            sauvegarder_reservations(df)
            st.success("Réservation mise à jour.")

    if st.button("🗑️ Supprimer cette réservation"):
        df = df.drop(index).reset_index(drop=True)
        sauvegarder_reservations(df)
        st.success("Réservation supprimée.")

# Onglet Nouvelle réservation
elif onglet == "➕ Nouvelle réservation":
    st.subheader("➕ Ajouter une nouvelle réservation")
    with st.form("formulaire"):
        nom = st.text_input("Nom du client")
        arrivee = st.date_input("Date d'arrivée")
        depart = st.date_input("Date de départ")
        plateforme = st.selectbox("Plateforme", ["Booking", "Airbnb"])
        tel = st.text_input("Téléphone")
        brut = st.text_input("Prix brut (€)")
        net = st.text_input("Prix net (€)")
        chg = st.text_input("Charges (€)")
        pct = st.text_input("Pourcentage (%)")

        submit = st.form_submit_button("✅ Valider")

    if submit:
        nouvelle = {
            "nom_client": nom,
            "date_arrivee": arrivee,
            "date_depart": depart,
            "plateforme": plateforme,
            "telephone": tel,
            "prix_brut": brut,
            "prix_net": net,
            "charges": chg,
            "%": pct,
        }
        df = df.append(nouvelle, ignore_index=True)
        sauvegarder_reservations(df)

        message = (
            f"Bonjour {nom},\n"
            f"Nous sommes heureux de vous accueillir demain à Nice.\n"
            f"Un emplacement de parking est à votre disposition.\n"
            f"Merci de nous indiquer votre heure d'arrivée.\n"
            f"Bon voyage !\nAnnick & Charley"
        )
        envoyer_sms(message)
        st.success("✅ Réservation enregistrée & SMS envoyé.")

# Onglet Calendrier
elif onglet == "📅 Calendrier":
    afficher_calendrier(df)

