import streamlit as st
import pandas as pd
import datetime
import calendar
import os
import requests

st.set_page_config(page_title="Portail Extranet", layout="wide")

FICHIER_RESERVATIONS = "reservations.xlsx"

def charger_donnees():
    if os.path.exists(FICHIER_RESERVATIONS):
        df = pd.read_excel(FICHIER_RESERVATIONS)
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"])
        df["date_depart"] = pd.to_datetime(df["date_depart"])
        if "charges" not in df.columns:
            df["charges"] = df["prix_brut"] - df["prix_net"]
        if "%" not in df.columns:
            df["%"] = (df["charges"] / df["prix_brut"]) * 100
        if "nuitees" not in df.columns:
            df["nuitees"] = (df["date_depart"] - df["date_arrivee"]).dt.days
        return df
    return pd.DataFrame(columns=[
        "nom_client", "date_arrivee", "date_depart", "plateforme", "telephone",
        "prix_brut", "prix_net", "charges", "%", "nuitees"
    ])

def enregistrer_donnees(df):
    df.to_excel(FICHIER_RESERVATIONS, index=False)

def envoyer_sms_free(user, api_key, message):
    url = f"https://smsapi.free-mobile.fr/sendmsg?user={user}&pass={api_key}&msg={requests.utils.quote(message)}"
    try:
        response = requests.get(url)
        return response.status_code == 200
    except:
        return False

def formulaire_reservation(df):
    st.subheader("➕ Nouvelle réservation")
    with st.form("ajout_reservation", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            nom_client = st.text_input("Nom du client")
            plateforme = st.selectbox("Plateforme", ["Airbnb", "Booking", "Autre"])
        with col2:
            date_arrivee = st.date_input("Date d'arrivée", value=datetime.date.today())
            prix_brut = st.number_input("Prix brut (€)", min_value=0.0)
        with col3:
            date_depart = st.date_input("Date de départ", value=datetime.date.today() + datetime.timedelta(days=1))
            prix_net = st.number_input("Prix net (€)", min_value=0.0)
        telephone = st.text_input("Téléphone du client (ex: +33612345678)")

        submitted = st.form_submit_button("Enregistrer")
        if submitted and nom_client and telephone:
            charges = prix_brut - prix_net
            pourcentage = (charges / prix_brut * 100) if prix_brut != 0 else 0
            nuitees = (date_depart - date_arrivee).days

            nouvelle_resa = {
                "nom_client": nom_client,
                "date_arrivee": pd.to_datetime(date_arrivee),
                "date_depart": pd.to_datetime(date_depart),
                "plateforme": plateforme,
                "telephone": telephone,
                "prix_brut": prix_brut,
                "prix_net": prix_net,
                "charges": charges,
                "%": pourcentage,
                "nuitees": nuitees
            }
            df = df.append(nouvelle_resa, ignore_index=True)
            enregistrer_donnees(df)
            st.success("Réservation enregistrée avec succès !")
    return df

def afficher_reservations(df):
    st.subheader("📋 Réservations")
    df = df.sort_values("date_arrivee")
    st.dataframe(df, use_container_width=True)

    st.subheader("🛠️ Modifier ou supprimer une réservation")
    if df.empty:
        st.info("Aucune réservation à modifier.")
        return df

    selection = st.selectbox("Choisir une réservation à modifier", df["nom_client"] + " - " + df["date_arrivee"].dt.strftime("%Y-%m-%d"))

    selected_index = df[df["nom_client"] + " - " + df["date_arrivee"].dt.strftime("%Y-%m-%d") == selection].index[0]

    with st.form("form_modif"):
        col1, col2, col3 = st.columns(3)
        with col1:
            nom_client = st.text_input("Nom du client", value=df.loc[selected_index, "nom_client"])
            plateforme = st.selectbox("Plateforme", ["Airbnb", "Booking", "Autre"], index=["Airbnb", "Booking", "Autre"].index(df.loc[selected_index, "plateforme"]))
        with col2:
            date_arrivee = st.date_input("Date d'arrivée", value=df.loc[selected_index, "date_arrivee"].date())
            prix_brut = st.number_input("Prix brut (€)", value=float(df.loc[selected_index, "prix_brut"]))
        with col3:
            date_depart = st.date_input("Date de départ", value=df.loc[selected_index, "date_depart"].date())
            prix_net = st.number_input("Prix net (€)", value=float(df.loc[selected_index, "prix_net"]))
        telephone = st.text_input("Téléphone du client", value=df.loc[selected_index, "telephone"])

        modif = st.form_submit_button("💾 Modifier")
        supprimer = st.form_submit_button("🗑️ Supprimer")

        if modif:
            charges = prix_brut - prix_net
            pourcentage = (charges / prix_brut * 100) if prix_brut != 0 else 0
            nuitees = (date_depart - date_arrivee).days

            df.loc[selected_index] = [
                nom_client, date_arrivee, date_depart, plateforme, telephone,
                prix_brut, prix_net, charges, pourcentage, nuitees
            ]
            enregistrer_donnees(df)
            st.success("Réservation modifiée avec succès")

        if supprimer:
            df = df.drop(selected_index)
            enregistrer_donnees(df)
            st.warning("Réservation supprimée")

    return df

def envoyer_sms_jour(df):
    st.subheader("📩 Envoi de SMS (24h avant arrivée)")
    today = datetime.date.today()
    demain = today + datetime.timedelta(days=1)
    df_sms = df[df["date_arrivee"].dt.date == demain]
    user_free = "12026027"
    api_key = "1Pat6vSRCLiSXl"

    if not df_sms.empty:
        for _, row in df_sms.iterrows():
            message = f"Bonjour {row['nom_client']}, nous sommes heureux de vous accueillir demain à Nice. Parking dispo. Merci de nous indiquer votre heure d’arrivée. Bon voyage ! Annick & Charley"
            success = envoyer_sms_free(user_free, api_key, message)
            if success:
                st.success(f"SMS envoyé à {row['telephone']}")
            else:
                st.error(f"Échec de l’envoi à {row['telephone']}")
    else:
        st.info("Aucun client n’arrive demain.")

def rapport_mensuel(df):
    st.subheader("📊 Rapport mensuel")
    if not {"prix_brut", "prix_net", "charges", "nuitees"}.issubset(df.columns):
        st.warning("Colonnes manquantes dans le fichier.")
        return

    df["annee"] = df["date_arrivee"].dt.year
    df["mois"] = df["date_arrivee"].dt.month

    regroupement = df.groupby(["annee", "mois", "plateforme"]).agg({
        "prix_brut": "sum",
        "prix_net": "sum",
        "charges": "sum",
        "nuitees": "sum"
    }).reset_index()

    regroupement["%"] = (regroupement["charges"] / regroupement["prix_brut"]) * 100
    regroupement["mois"] = regroupement["mois"].apply(lambda x: calendar.month_name[x])

    st.dataframe(regroupement)

def afficher_calendrier(df):
    st.subheader("📅 Calendrier de réservations (type Airbnb/Booking)")

    mois_courant = datetime.date.today().month
    annee_courante = datetime.date.today().year
    nom_mois = calendar.month_name[mois_courant]

    st.markdown(f"### {nom_mois} {annee_courante}")
    mois_dates = pd.date_range(start=datetime.date(annee_courante, mois_courant, 1),
                               end=datetime.date(annee_courante, mois_courant, calendar.monthrange(annee_courante, mois_courant)[1]))
    calendrier = pd.DataFrame(index=mois_dates)

    def afficher_cellule(jour):
        lignes = []
        for _, row in df.iterrows():
            if row["date_arrivee"].date() <= jour.date() < row["date_depart"].date():
                lignes.append(f"{row['nom_client']} ({row['plateforme']})")
        return "\n".join(lignes)

    calendrier["Réservations"] = calendrier.index.to_series().apply(afficher_cellule)
    calendrier.reset_index(inplace=True)
    calendrier.rename(columns={"index": "Date"}, inplace=True)
    st.dataframe(calendrier, height=600, use_container_width=True)

# Interface principale
st.title("🏨 Portail Extranet")

onglet = st.sidebar.radio("Navigation", ["📥 Réservations", "📅 Calendrier", "📈 Rapport"])

df = charger_donnees()

if onglet == "📥 Réservations":
    df = formulaire_reservation(df)
    df = afficher_reservations(df)
    envoyer_sms_jour(df)

elif onglet == "📅 Calendrier":
    afficher_calendrier(df)

elif onglet == "📈 Rapport":
    rapport_mensuel(df)
