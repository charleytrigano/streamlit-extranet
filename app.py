import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta, datetime
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
import unicodedata
import requests
import os

FICHIER = "reservations.xlsx"
SMS_LOG = "sms_log.csv"
USER = "12026027"
API_KEY = "MF7Qjs3C8KxKHz"
FREE_SMS_ENDPOINT = "https://smsapi.free-mobile.fr/sendmsg"

def nettoyer_texte(s):
    if isinstance(s, str):
        return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    return str(s)

def charger_donnees():
    df = pd.read_excel(FICHIER)
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"]).dt.date
    df["date_depart"] = pd.to_datetime(df["date_depart"]).dt.date
    df["prix_brut"] = pd.to_numeric(df["prix_brut"], errors="coerce").round(2)
    df["prix_net"] = pd.to_numeric(df["prix_net"], errors="coerce").round(2)
    df["charges"] = (df["prix_brut"] - df["prix_net"]).round(2)
    df["%"] = ((df["charges"] / df["prix_brut"]) * 100).replace([float("inf"), -float("inf")], 0).fillna(0).round(2)
    df["nuitees"] = (pd.to_datetime(df["date_depart"]) - pd.to_datetime(df["date_arrivee"])).dt.days
    df["annee"] = pd.to_datetime(df["date_arrivee"]).dt.year
    df["mois"] = pd.to_datetime(df["date_arrivee"]).dt.month
    return df

def liste_clients(df):
    st.subheader("📜 Liste des clients")
    annee = st.selectbox("Année", sorted(df["annee"].dropna().unique()))
    mois = st.selectbox("Mois", ["Tous"] + sorted(df[df["annee"] == annee]["mois"].dropna().unique()))

    data = df[df["annee"] == annee]
    if mois != "Tous":
        data = data[data["mois"] == mois]

    if data.empty:
        st.warning("Aucune donnée disponible.")
        return

    data["prix_brut/nuit"] = (data["prix_brut"] / data["nuitees"]).replace([float("inf"), -float("inf")], 0).fillna(0).round(2)
    data["prix_net/nuit"] = (data["prix_net"] / data["nuitees"]).replace([float("inf"), -float("inf")], 0).fillna(0).round(2)

    colonnes = [
        "plateforme", "nom_client", "date_arrivee", "date_depart", "nuitees",
        "prix_brut", "prix_net", "charges", "%", "prix_brut/nuit", "prix_net/nuit"
    ]

    df_affiche = data[colonnes].copy()
    st.dataframe(df_affiche)

    total_row = pd.DataFrame(df_affiche.select_dtypes(include=['number']).sum()).T
    total_row.index = ['Total']
    st.dataframe(total_row)

    # Export Excel
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_affiche.to_excel(writer, index=False, sheet_name="Clients")
        total_row.to_excel(writer, index=True, sheet_name="Total")
    buffer.seek(0)
    st.download_button("📥 Télécharger Excel", data=buffer, file_name=f"liste_clients_{annee}_{mois}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def notifier_arrivees_prochaines(df):
    aujourd_hui = date.today()
    demain = aujourd_hui + timedelta(days=1)
    df = df.copy()
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"]).dt.date
    df_notif = df[df["date_arrivee"] == demain]

    if df_notif.empty:
        return

    # Charger historique
    if os.path.exists(SMS_LOG):
        log = pd.read_csv(SMS_LOG)
    else:
        log = pd.DataFrame(columns=["nom_client", "telephone", "date_arrivee", "date_envoi", "message"])

    for _, row in df_notif.iterrows():
        tel = row.get("telephone")
        nom = row["nom_client"]
        plateforme = row["plateforme"]
        arrivee = row["date_arrivee"]
        depart = row["date_depart"]
        msg = f"{plateforme} - {nom} - {arrivee} - {depart}"

        deja_envoye = ((log["nom_client"] == nom) &
                       (log["telephone"] == tel) &
                       (log["date_arrivee"] == str(arrivee))).any()

        if not deja_envoye:
            params = {"user": USER, "pass": API_KEY, "msg": msg}
            try:
                requests.get(FREE_SMS_ENDPOINT, params=params, timeout=10)
                log.loc[len(log)] = [nom, tel, arrivee, aujourd_hui, msg]
            except Exception as e:
                st.error(f"Erreur d'envoi SMS à {nom} : {e}")

    log.to_csv(SMS_LOG, index=False)

def main():
    df = charger_donnees()
    notifier_arrivees_prochaines(df)

    onglet = st.sidebar.radio("Menu", [
        "📋 Réservations", "➕ Ajouter", "✏️ Modifier / Supprimer",
        "📅 Calendrier", "📊 Rapport", "📜 Liste des clients"
    ])

    if onglet == "📜 Liste des clients":
        liste_clients(df)

    # ... les autres fonctions (ajouter/modifier/calendrier/rapport) sont à insérer ici comme avant

if __name__ == "__main__":
    main()