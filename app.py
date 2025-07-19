import streamlit as st
import pandas as pd
import datetime
from datetime import datetime as dt, timedelta
import requests

st.set_page_config(page_title="Extranet", layout="wide")

EXCEL_FILE = "reservations.xlsx"

# ---------------------- Fonctions utilitaires ----------------------

def charger_donnees():
    try:
        df = pd.read_excel(EXCEL_FILE)
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
        df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame()

def enregistrer_donnees(df):
    df.to_excel(EXCEL_FILE, index=False)

def envoyer_sms_free(api_key, user, message):
    url = f"https://smsapi.free-mobile.fr/sendmsg?user={user}&pass={api_key}&msg={requests.utils.quote(message)}"
    try:
        response = requests.get(url)
        return response.status_code == 200
    except Exception:
        return False

# ---------------------- Interface principale ----------------------

onglet = st.sidebar.radio("Navigation", ["📋 Réservations", "📅 Calendrier", "✉️ SMS", "📊 RAPPORT"])

df = charger_donnees()

# ---------------------- Onglet Réservations ----------------------

if onglet == "📋 Réservations":
    st.title("📋 Tableau des Réservations")
    st.dataframe(df)

# ---------------------- Onglet Calendrier ----------------------

elif onglet == "📅 Calendrier":
    st.title("📅 Calendrier des réservations")

    mois_selectionne = st.selectbox("Mois", list(range(1, 13)), index=dt.now().month - 1)
    annee_selectionnee = st.selectbox("Année", list(range(2023, 2031)), index=2)

    if not df.empty:
        df_mois = df[
            (df["date_arrivee"].dt.month == mois_selectionne) &
            (df["date_arrivee"].dt.year == annee_selectionnee)
        ]

        import calendar
        from calendar import monthrange

        nb_jours = monthrange(annee_selectionnee, mois_selectionne)[1]
        jours_mois = [dt(annee_selectionnee, mois_selectionne, j).date() for j in range(1, nb_jours + 1)]

        plateforme_couleurs = {
            "Booking": "#AED6F1",
            "Airbnb": "#F9E79F",
            "Autre": "#D5F5E3"
        }

        def case(jour, nom_client, color):
            return f"<div style='background-color:{color}; padding:3px; border-radius:3px'>{nom_client}</div>"

        calendrier = {jour: [] for jour in jours_mois}

        for _, row in df.iterrows():
            arrivee = row["date_arrivee"].date()
            depart = row["date_depart"].date()
            nom = row["nom_client"]
            plate = row["plateforme"]
            couleur = plateforme_couleurs.get(plate, "#E8DAEF")

            for jour in jours_mois:
                if arrivee <= jour < depart:
                    calendrier[jour].append(case(jour, nom, couleur))

        tableau = pd.DataFrame(
            [[", ".join(calendrier[jour]) if calendrier[jour] else "" for jour in jours_mois]],
            columns=[jour.strftime("%d") for jour in jours_mois]
        )
        st.write(f"**Mois de {calendar.month_name[mois_selectionne]} {annee_selectionnee}**")
        st.markdown(tableau.to_html(escape=False, index=False), unsafe_allow_html=True)

# ---------------------- Onglet SMS ----------------------

elif onglet == "✉️ SMS":
    st.title("✉️ Envoi de SMS aux clients arrivant demain")

    if df.empty:
        st.warning("Aucune donnée chargée.")
    else:
        aujourd_hui = dt.today().date()
        demain = aujourd_hui + timedelta(days=1)

        df_demain = df[df["date_arrivee"].dt.date == demain]

        if df_demain.empty:
            st.info("Aucune réservation prévue pour demain.")
        else:
            st.write("Clients arrivant demain :")
            st.dataframe(df_demain[["nom_client", "date_arrivee", "telephone", "plateforme"]])

            for _, row in df_demain.iterrows():
                message = (
                    f"Bonjour {row['nom_client']},\n"
                    f"Nous sommes heureux de vous accueillir demain à Nice.\n"
                    f"Un emplacement de parking est à votre disposition.\n"
                    f"Merci de nous indiquer votre heure d'arrivée.\n"
                    f"Bon voyage et à demain !\n"
                    f"Annick & Charley"
                )
                ok = envoyer_sms_free("1Pat6vSRCLiSXl", "12026027", message)
                if ok:
                    st.success(f"SMS envoyé à {row['telephone']}")
                else:
                    st.error(f"Échec de l'envoi à {row['telephone']}")

# ---------------------- Onglet RAPPORT ----------------------

elif onglet == "📊 RAPPORT":
    st.title("📊 Rapport mensuel")

    if df.empty:
        st.warning("Aucune donnée disponible.")
    else:
        df["annee"] = df["date_arrivee"].dt.year
        df["mois"] = df["date_arrivee"].dt.month

        regroupement = df.groupby(["annee", "mois", "plateforme"]).agg({
            "prix_brut": "sum",
            "prix_net": "sum",
            "charges": "sum"
        }).reset_index()

        regroupement["%"] = (regroupement["charges"] / regroupement["prix_brut"]) * 100
        regroupement["mois"] = regroupement["mois"].apply(lambda x: calendar.month_name[x])

        regroupement = regroupement.rename(columns={
            "annee": "Année",
            "mois": "Mois",
            "plateforme": "Plateforme",
            "prix_brut": "Total Brut",
            "prix_net": "Total Net",
            "charges": "Charges",
            "%": "% Charges"
        })

        st.dataframe(regroupement.style.format({
            "Total Brut": "€{:.2f}",
            "Total Net": "€{:.2f}",
            "Charges": "€{:.2f}",
            "% Charges": "{:.1f} %"
        }))

