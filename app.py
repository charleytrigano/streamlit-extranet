import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import plotly.figure_factory as ff
import calendar

st.set_page_config(page_title="Extranet Streamlit", layout="wide")

# -------------------- PARAMÈTRES FREE MOBILE --------------------
FREE_API_1 = "MF7Qjs3C8KxKHz"
FREE_USER_1 = "12026027"

FREE_API_2 = "1Pat6vSRCLiSXl"
FREE_USER_2 = "12026027"

# -------------------- FONCTIONS --------------------
def envoyer_sms_free(user, key, message):
    url = f"https://smsapi.free-mobile.fr/sendmsg?user={user}&pass={key}&msg={requests.utils.quote(message)}"
    response = requests.get(url)
    return response.status_code == 200

def color_platform(plateforme):
    colors = {
        "Airbnb": "rgb(255, 102, 102)",
        "Booking": "rgb(102, 178, 255)",
        "Direct": "rgb(102, 255, 178)"
    }
    return colors.get(plateforme, "rgb(200, 200, 200)")

# -------------------- INTERFACE --------------------
st.title("📅 Portail Extranet Streamlit")

# Tabs
onglet = st.sidebar.radio("Navigation", ["📥 Importer / Visualiser", "📤 Ajouter une réservation", "📆 Calendrier"])

# SESSION
if "sms_log" not in st.session_state:
    st.session_state.sms_log = []

# -------------------- PAGE 1 --------------------
if onglet == "📥 Importer / Visualiser":
    st.subheader("📥 Importer votre fichier .xlsx")
    xlsx_file = st.file_uploader("Téléversez le fichier Excel", type=["xlsx"])

    if xlsx_file:
        try:
            df = pd.read_excel(xlsx_file)

            # Nettoyage et formats
            df.columns = df.columns.str.strip()
            expected_cols = {"nom_client", "date_arrivee", "date_depart", "plateforme", "telephone", "prix_brut", "prix_net", "charges", "%"}
            if not expected_cols.issubset(df.columns):
                st.error(f"❌ Le fichier doit contenir les colonnes : {', '.join(sorted(expected_cols))}")
            else:
                df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
                df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")

                st.success("✅ Fichier bien chargé")
                st.dataframe(df)

                # Envoi SMS pour les clients arrivant demain
                demain = datetime.now().date() + timedelta(days=1)
                df_demain = df[df["date_arrivee"].dt.date == demain]

                for _, row in df_demain.iterrows():
                    nom = row["nom_client"]
                    date_arrivee = row["date_arrivee"].strftime("%d/%m/%Y")
                    message = (
                        f"Bonjour {nom},\n"
                        f"Nous sommes heureux de vous accueillir demain à Nice.\n"
                        f"Un emplacement de parking est à votre disposition.\n"
                        f"Merci d’indiquer votre heure d’arrivée pour que nous puissions nous organiser.\n"
                        f"Bon voyage et à demain !\n"
                        f"Annick & Charley"
                    )
                    tel = row["telephone"]
                    ok1 = envoyer_sms_free(FREE_USER_1, FREE_API_1, message)
                    ok2 = envoyer_sms_free(FREE_USER_2, FREE_API_2, message)
                    log = f"📤 SMS à {nom} ({tel}) → ✅ {'Oui' if ok1 or ok2 else 'Non'}"
                    st.session_state.sms_log.append(log)

                if st.session_state.sms_log:
                    st.subheader("📋 Journal des SMS")
                    for log in st.session_state.sms_log:
                        st.write(log)

        except Exception as e:
            st.error(f"Erreur de lecture : {e}")

# -------------------- PAGE 2 --------------------
elif onglet == "📤 Ajouter une réservation":
    st.subheader("➕ Nouvelle réservation")

    with st.form("formulaire"):
        nom = st.text_input("Nom du client")
        date_arrivee = st.date_input("Date d'arrivée")
        date_depart = st.date_input("Date de départ")
        plateforme = st.selectbox("Plateforme", ["Booking", "Airbnb", "Direct"])
        telephone = st.text_input("Téléphone")
        prix_brut = st.text_input("Prix brut (€)")
        prix_net = st.text_input("Prix net (€)")
        charges = st.text_input("Charges (€)")
        pourcentage = st.text_input("Commission (%)")
        submit = st.form_submit_button("📥 Ajouter")

    if submit:
        try:
            new_row = pd.DataFrame([{
                "nom_client": nom,
                "date_arrivee": pd.to_datetime(date_arrivee),
                "date_depart": pd.to_datetime(date_depart),
                "plateforme": plateforme,
                "telephone": telephone,
                "prix_brut": prix_brut,
                "prix_net": prix_net,
                "charges": charges,
                "%": pourcentage
            }])

            try:
                df_existing = pd.read_excel("reservations.xlsx")
                df = pd.concat([df_existing, new_row], ignore_index=True)
            except:
                df = new_row

            df.to_excel("reservations.xlsx", index=False)
            st.success("✅ Réservation ajoutée")

        except Exception as e:
            st.error(f"Erreur lors de l'ajout : {e}")

# -------------------- PAGE 3 --------------------
elif onglet == "📆 Calendrier":
    st.subheader("🗓️ Calendrier mensuel des réservations")

    try:
        df = pd.read_excel("reservations.xlsx")
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
        df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")

        tasks = []
        for _, row in df.iterrows():
            if pd.isna(row["date_arrivee"]) or pd.isna(row["date_depart"]):
                continue
            tasks.append(dict(
                Task=row["nom_client"],
                Start=row["date_arrivee"],
                Finish=row["date_depart"],
                Resource=row["plateforme"]
            ))

        couleurs = {
            "Booking": "rgb(102, 178, 255)",
            "Airbnb": "rgb(255, 102, 102)",
            "Direct": "rgb(102, 255, 178)"
        }

        fig = ff.create_gantt(tasks, index_col='Resource', colors=couleurs, show_colorbar=True, group_tasks=True)
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Erreur lors de la génération du calendrier : {e}")



