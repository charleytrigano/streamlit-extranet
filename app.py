import streamlit as st
import pandas as pd
import datetime
import calendar
import os
import requests

# ---------- CONFIGURATION ----------
FICHIER_EXCEL = "reservations.xlsx"

FREE_API_ENDPOINT = "https://smsapi.free-mobile.fr/sendmsg"
FREE_API_CREDENTIALS = [
    {"user": "12026027", "key": "1Pat6vSRCLiSXl", "telephone": "+33611772793"},
    {"user": "12026027", "key": "MF7Qjs3C8KxKHz", "telephone": "+33617722379"}
]

# ---------- FONCTIONS DE BASE ----------

def charger_donnees():
    df = pd.read_excel(FICHIER_EXCEL)
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"])
    df["date_depart"] = pd.to_datetime(df["date_depart"])
    df["nuitees"] = (df["date_depart"] - df["date_arrivee"]).dt.days
    df["charges"] = df["prix_brut"] - df["prix_net"]
    df["%"] = (df["charges"] / df["prix_brut"] * 100).round(2)
    return df

def sauvegarder_donnees(df):
    df.to_excel(FICHIER_EXCEL, index=False)

# ---------- FONCTION SMS ----------

def envoyer_sms(nom_client, date_arrivee):
    message = (
        f"Bonjour {nom_client},\n"
        f"Nous sommes heureux de vous accueillir demain à Nice.\n"
        f"Un emplacement de parking est à votre disposition.\n"
        f"Merci de nous indiquer votre heure d’arrivée.\n"
        f"Bon voyage et à demain !\n"
        f"Annick & Charley"
    )
    for contact in FREE_API_CREDENTIALS:
        payload = {
            "user": contact["user"],
            "pass": contact["key"],
            "msg": message
        }
        try:
            requests.get(FREE_API_ENDPOINT, params=payload, timeout=5)
        except:
            pass

def envoyer_sms_jour(df):
    demain = datetime.date.today() + datetime.timedelta(days=1)
    df_sms = df[df["date_arrivee"].dt.date == demain]
    for _, row in df_sms.iterrows():
        envoyer_sms(row["nom_client"], row["date_arrivee"])

# ---------- INTERFACE STREAMLIT ----------

st.set_page_config(page_title="Extranet", layout="wide")
st.title("📅 Extranet de Réservations")

onglet = st.sidebar.selectbox("Navigation", ["Tableau des réservations", "Ajouter une réservation", "Modifier / Supprimer", "Rapport mensuel"])

df = charger_donnees()

# ---------- ONGLET TABLEAU ----------
if onglet == "Tableau des réservations":
    st.subheader("📋 Tableau des Réservations")
    st.dataframe(df.sort_values("date_arrivee"), use_container_width=True)

# ---------- ONGLET AJOUT ----------
elif onglet == "Ajouter une réservation":
    st.subheader("➕ Ajouter une nouvelle réservation")

    with st.form("ajout_resa"):
        col1, col2 = st.columns(2)
        nom = col1.text_input("Nom du client")
        plateforme = col2.selectbox("Plateforme", sorted(df["plateforme"].unique()))
        date_arrivee = col1.date_input("Date d'arrivée")
        date_depart = col2.date_input("Date de départ")
        telephone = col1.text_input("Téléphone")
        brut = col1.number_input("Prix brut (€)", min_value=0.0)
        net = col2.number_input("Prix net (€)", min_value=0.0)
        envoyer_sms_checkbox = st.checkbox("Envoyer un SMS au client 24h avant l'arrivée", value=True)
        submit = st.form_submit_button("Enregistrer")

        if submit:
            new_row = {
                "nom_client": nom,
                "plateforme": plateforme,
                "date_arrivee": pd.to_datetime(date_arrivee),
                "date_depart": pd.to_datetime(date_depart),
                "telephone": telephone,
                "prix_brut": brut,
                "prix_net": net,
                "charges": brut - net,
                "%": round(((brut - net) / brut * 100), 2) if brut else 0,
                "nuitees": (date_depart - date_arrivee).days
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            sauvegarder_donnees(df)
            st.success("✅ Réservation ajoutée avec succès.")

# ---------- ONGLET MODIFICATION ----------
elif onglet == "Modifier / Supprimer":
    st.subheader("✏️ Modifier ou Supprimer une Réservation")
    selection = st.selectbox("Choisissez un client", df["nom_client"] + " | " + df["date_arrivee"].dt.strftime('%Y-%m-%d'))

    index = df.index[df["nom_client"] + " | " + df["date_arrivee"].dt.strftime('%Y-%m-%d') == selection][0]
    reservation = df.loc[index]

    with st.form("modif_resa"):
        col1, col2 = st.columns(2)
        nom = col1.text_input("Nom du client", reservation["nom_client"])
        plateforme = col2.selectbox("Plateforme", sorted(df["plateforme"].unique()), index=sorted(df["plateforme"].unique()).index(reservation["plateforme"]))
        date_arrivee = col1.date_input("Date d'arrivée", reservation["date_arrivee"].date())
        date_depart = col2.date_input("Date de départ", reservation["date_depart"].date())
        telephone = col1.text_input("Téléphone", reservation["telephone"])
        brut = col1.number_input("Prix brut (€)", value=float(reservation["prix_brut"]))
        net = col2.number_input("Prix net (€)", value=float(reservation["prix_net"]))
        submit_modif = st.form_submit_button("Enregistrer les modifications")
        submit_suppr = st.form_submit_button("🗑️ Supprimer")

        if submit_modif:
            df.at[index, "nom_client"] = nom
            df.at[index, "plateforme"] = plateforme
            df.at[index, "date_arrivee"] = pd.to_datetime(date_arrivee)
            df.at[index, "date_depart"] = pd.to_datetime(date_depart)
            df.at[index, "telephone"] = telephone
            df.at[index, "prix_brut"] = brut
            df.at[index, "prix_net"] = net
            df.at[index, "charges"] = brut - net
            df.at[index, "%"] = round(((brut - net) / brut * 100), 2) if brut else 0
            df.at[index, "nuitees"] = (date_depart - date_arrivee).days
            sauvegarder_donnees(df)
            st.success("✅ Réservation modifiée.")

        if submit_suppr:
            df = df.drop(index).reset_index(drop=True)
            sauvegarder_donnees(df)
            st.success("🗑️ Réservation supprimée.")

# ---------- ONGLET RAPPORT MENSUEL ----------
elif onglet == "Rapport mensuel":
    st.subheader("📊 Rapport mensuel par plateforme")

    df["annee"] = df["date_arrivee"].dt.year
    df["mois"] = df["date_arrivee"].dt.month

    annee = st.selectbox("Filtrer par année", sorted(df["annee"].unique()))
    mois = st.selectbox("Filtrer par mois", range(1, 13))

    df_filtre = df[(df["annee"] == annee) & (df["mois"] == mois)]

    regroupement = df_filtre.groupby("plateforme").agg({
        "prix_brut": "sum",
        "prix_net": "sum",
        "charges": "sum",
        "%": "mean",
        "nuitees": "sum"
    }).round(2).reset_index()

    st.dataframe(regroupement, use_container_width=True)

    st.markdown("**Total général :**")
    st.write({
        "Prix brut": df_filtre["prix_brut"].sum(),
        "Prix net": df_filtre["prix_net"].sum(),
        "Charges": df_filtre["charges"].sum(),
        "Nuitées": df_filtre["nuitees"].sum()
    })

# ---------- ENVOI DES SMS ----------
envoyer_sms_jour(df)

