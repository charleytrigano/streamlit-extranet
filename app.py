import streamlit as st
import pandas as pd
import datetime
import calendar
import requests
from io import BytesIO

FICHIER_EXCEL = "reservations.xlsx"

FREE_API_URL = "https://smsapi.free-mobile.fr/sendmsg"
FREE_USER_1 = "12026027"
FREE_KEY_1 = "MF7Qjs3C8KxKHz"
FREE_USER_2 = "12026027"
FREE_KEY_2 = "1Pat6vSRCLiSXl"

@st.cache_data
def charger_donnees():
    df = pd.read_excel(FICHIER_EXCEL)
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
    df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")
    df["nuitees"] = (df["date_depart"] - df["date_arrivee"]).dt.days
    return df

def sauvegarder_donnees(df):
    df.to_excel(FICHIER_EXCEL, index=False)

def envoyer_sms(client, telephone, date_arrivee):
    message = (
        f"Bonjour {client},\n"
        f"Nous sommes heureux de vous accueillir demain à Nice.\n"
        f"Un emplacement de parking est à votre disposition.\n"
        f"Merci de nous indiquer votre heure approximative d’arrivée.\n"
        f"Bon voyage et à demain !\n"
        f"Annick & Charley"
    )
    for user, key in [(FREE_USER_1, FREE_KEY_1), (FREE_USER_2, FREE_KEY_2)]:
        try:
            requests.post(FREE_API_URL, params={
                "user": user,
                "pass": key,
                "msg": message
            })
        except Exception:
            pass

def envoyer_sms_jour(df):
    demain = datetime.date.today() + datetime.timedelta(days=1)
    df_sms = df[df["date_arrivee"].dt.date == demain]
    for _, row in df_sms.iterrows():
        envoyer_sms(row["nom_client"], row["telephone"], row["date_arrivee"])

def afficher_calendrier(df):
    mois = st.selectbox("Mois", list(calendar.month_name)[1:], index=datetime.date.today().month - 1)
    annee = st.selectbox("Année", list(range(2023, 2031)), index=2)

    mois_index = list(calendar.month_name).index(mois)
    premier_jour = datetime.date(annee, mois_index, 1)
    _, nb_jours = calendar.monthrange(annee, mois_index)

    plateforme_couleurs = {
        "Booking": "#FF9999",
        "Airbnb": "#99CCFF",
        "Abritel": "#99FF99",
        "Expedia": "#FFD700"
    }

    data = [[""] * 7 for _ in range(6)]
    jours = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    for jour in range(1, nb_jours + 1):
        date_actuelle = datetime.date(annee, mois_index, jour)
        semaine = (jour + premier_jour.weekday() - 1) // 7
        colonne = (date_actuelle.weekday()) % 7

        occupants = []
        for _, row in df.iterrows():
            debut = row["date_arrivee"].date()
            fin = row["date_depart"].date()
            if debut <= date_actuelle < fin:
                occupants.append((row["nom_client"], row["plateforme"]))

        if occupants:
            texte = ""
            for nom, plat in occupants:
                couleur = plateforme_couleurs.get(plat, "#DDDDDD")
                texte += f":rainbow[{nom}]  \n"
            data[semaine][colonne] = texte
        else:
            data[semaine][colonne] = ""

    st.markdown("### Calendrier des Réservations")
    st.table(pd.DataFrame(data, columns=jours))

def ajouter_reservation(df):
    st.subheader("Ajouter une Réservation")
    with st.form("ajout_resa"):
        nom = st.text_input("Nom du client")
        arrivee = st.date_input("Date d’arrivée")
        depart = st.date_input("Date de départ", min_value=arrivee)
        plateforme = st.selectbox("Plateforme", ["Booking", "Airbnb", "Abritel", "Expedia"])
        telephone = st.text_input("Téléphone")
        prix_brut = st.number_input("Prix brut", min_value=0.0)
        prix_net = st.number_input("Prix net", min_value=0.0)
        submit = st.form_submit_button("Enregistrer")

        if submit:
            charges = prix_brut - prix_net
            pourcent = round((charges / prix_brut) * 100, 2) if prix_brut else 0
            new_row = {
                "nom_client": nom,
                "date_arrivee": pd.to_datetime(arrivee),
                "date_depart": pd.to_datetime(depart),
                "plateforme": plateforme,
                "telephone": telephone,
                "prix_brut": prix_brut,
                "prix_net": prix_net,
                "charges": charges,
                "%": pourcent,
                "nuitees": (depart - arrivee).days
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            sauvegarder_donnees(df)
            st.success("Réservation ajoutée !")
            st.rerun()

def modifier_reservation(df):
    st.subheader("Modifier ou Supprimer une Réservation")
    options = df["nom_client"] + " | " + df["date_arrivee"].dt.strftime("%Y-%m-%d")
    selection = st.selectbox("Choisissez un client", options)
    index = options[options == selection].index[0]
    selected = df.loc[index]

    with st.form("modif_resa"):
        nom = st.text_input("Nom du client", selected["nom_client"])
        arrivee = st.date_input("Date d’arrivée", selected["date_arrivee"])
        depart = st.date_input("Date de départ", selected["date_depart"])
        plateforme = st.selectbox("Plateforme", ["Booking", "Airbnb", "Abritel", "Expedia"], index=["Booking", "Airbnb", "Abritel", "Expedia"].index(selected["plateforme"]))
        telephone = st.text_input("Téléphone", selected["telephone"])
        prix_brut = st.number_input("Prix brut", value=selected["prix_brut"])
        prix_net = st.number_input("Prix net", value=selected["prix_net"])
        modifier = st.form_submit_button("Modifier")
        supprimer = st.form_submit_button("Supprimer")

        if modifier:
            charges = prix_brut - prix_net
            pourcent = round((charges / prix_brut) * 100, 2) if prix_brut else 0
            df.loc[index] = [nom, arrivee, depart, plateforme, telephone, prix_brut, prix_net, charges, pourcent, (depart - arrivee).days]
            sauvegarder_donnees(df)
            st.success("Réservation modifiée.")
            st.rerun()

        if supprimer:
            df = df.drop(index).reset_index(drop=True)
            sauvegarder_donnees(df)
            st.success("Réservation supprimée.")
            st.rerun()

def rapport_mensuel(df):
    st.subheader("Rapport mensuel")
    df["annee"] = df["date_arrivee"].dt.year
    df["mois"] = df["date_arrivee"].dt.month

    annee_filtre = st.selectbox("Filtrer par année", sorted(df["annee"].unique()))
    mois_filtre = st.selectbox("Filtrer par mois", list(calendar.month_name)[1:], index=datetime.date.today().month - 1)
    mois_index = list(calendar.month_name).index(mois_filtre)

    df_filtre = df[(df["annee"] == annee_filtre) & (df["mois"] == mois_index)]
    regroupement = df_filtre.groupby("plateforme")[["prix_brut", "prix_net", "charges", "%", "nuitees"]].sum().reset_index()

    total_row = pd.DataFrame({
        "plateforme": ["TOTAL"],
        "prix_brut": [regroupement["prix_brut"].sum()],
        "prix_net": [regroupement["prix_net"].sum()],
        "charges": [regroupement["charges"].sum()],
        "%": [round((regroupement["charges"].sum() / regroupement["prix_brut"].sum()) * 100, 2) if regroupement["prix_brut"].sum() else 0],
        "nuitees": [regroupement["nuitees"].sum()]
    })

    rapport = pd.concat([regroupement, total_row], ignore_index=True)
    st.dataframe(rapport)

def afficher_tableau(df):
    st.subheader("Tableau des réservations")
    st.dataframe(df)

# Interface principale
st.set_page_config(page_title="Gestion Réservations", layout="wide")

st.title("📅 Extranet Réservations")

onglet = st.sidebar.radio("Navigation", ["Tableau", "Calendrier", "Ajouter", "Modifier", "Rapport"])

df = charger_donnees()

envoyer_sms_jour(df)

if onglet == "Tableau":
    afficher_tableau(df)

elif onglet == "Calendrier":
    afficher_calendrier(df)

elif onglet == "Ajouter":
    ajouter_reservation(df)

elif onglet == "Modifier":
    modifier_reservation(df)

elif onglet == "Rapport":
    rapport_mensuel(df)
