import streamlit as st
import pandas as pd
import plotly.express as px
import calendar
from datetime import datetime, timedelta
import requests
import os

st.set_page_config(page_title="Extranet", layout="wide")
st.title("🏨 Portail Extranet Streamlit")

# ---------- CONFIG ----------
FREE_API_1 = "MF7Qjs3C8KxKHz"
FREE_USER_1 = "12026027"

FREE_API_2 = "1Pat6vSRCLiSXl"
FREE_USER_2 = "12026027"  # Remplace si nécessaire

XLSX_FILE = "reservations.xlsx"
SMS_LOG = []

# ---------- CHARGEMENT ----------
st.sidebar.header("📁 Fichier Réservations")
uploaded_file = st.sidebar.file_uploader("Importer un fichier .xlsx", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.to_excel(XLSX_FILE, index=False)
    st.success("✅ Données chargées depuis le fichier importé.")
elif os.path.exists(XLSX_FILE):
    df = pd.read_excel(XLSX_FILE)
    st.info("📄 Données chargées depuis le fichier local.")
else:
    st.warning("📂 Aucun fichier chargé.")
    df = pd.DataFrame()

# ---------- VÉRIF STRUCTURE ----------
required_cols = {
    "nom_client", "date_arrivee", "date_depart", "plateforme",
    "telephone", "prix_brut", "prix_net", "charges", "%"
}
if not required_cols.issubset(set(df.columns)):
    st.error(f"❌ Le fichier doit contenir les colonnes : {', '.join(required_cols)}")
    st.stop()

# ---------- CLEANUP DATES ----------
df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")

# ---------- SMS 24h AVANT ----------
aujourd_hui = datetime.now().date()
demain = aujourd_hui + timedelta(days=1)
df_demain = df[df["date_arrivee"].dt.date == demain]

st.sidebar.header("📩 SMS Automatique")

def envoyer_sms(user, key, message):
    url = f"https://smsapi.free-mobile.fr/sendmsg?user={user}&pass={key}&msg={message}"
    try:
        r = requests.get(url)
        return r.status_code == 200
    except Exception:
        return False

for _, row in df_demain.iterrows():
    msg = (
        f"Bonjour {row['nom_client']}, nous sommes heureux de vous accueillir demain à Nice.\n"
        f"Un emplacement de parking est à votre disposition.\n"
        f"Merci de nous indiquer votre heure d’arrivée.\n"
        f"Bon voyage et à demain !\nAnnick & Charley"
    )
    to_log = {"nom": row['nom_client'], "téléphone": row['telephone'], "message": msg}
    success_1 = envoyer_sms(FREE_USER_1, FREE_API_1, msg)
    success_2 = envoyer_sms(FREE_USER_2, FREE_API_2, msg)
    to_log["status"] = "✅" if success_1 or success_2 else "❌"
    SMS_LOG.append(to_log)

if SMS_LOG:
    st.sidebar.subheader("📜 Journal des SMS")
    for entry in SMS_LOG:
        st.sidebar.markdown(f"{entry['status']} {entry['nom']} → {entry['téléphone']}")

# ---------- AJOUT MANUEL ----------
st.sidebar.header("➕ Nouvelle Réservation")
with st.sidebar.form("add_resa"):
    nom = st.text_input("Nom du client")
    tel = st.text_input("Téléphone")
    plateforme = st.selectbox("Plateforme", ["Airbnb", "Booking", "Autre"])
    arrivee = st.date_input("Date d’arrivée")
    depart = st.date_input("Date de départ", value=arrivee + timedelta(days=2))
    prix_brut = st.text_input("Prix brut")
    prix_net = st.text_input("Prix net")
    charges = st.text_input("Charges")
    pourcentage = st.text_input("%")

    submit = st.form_submit_button("Ajouter")

    if submit:
        nouvelle_resa = {
            "nom_client": nom,
            "telephone": tel,
            "plateforme": plateforme,
            "date_arrivee": pd.to_datetime(arrivee),
            "date_depart": pd.to_datetime(depart),
            "prix_brut": prix_brut,
            "prix_net": prix_net,
            "charges": charges,
            "%": pourcentage
        }
        df = pd.concat([df, pd.DataFrame([nouvelle_resa])], ignore_index=True)
        df.to_excel(XLSX_FILE, index=False)
        st.success(f"✅ Réservation ajoutée pour {nom}")

# ---------- CALENDRIER ----------
st.subheader("📅 Calendrier des Réservations (Mensuel)")

try:
    calendar_data = []
    couleurs = {
        "Airbnb": "lightgreen",
        "Booking": "lightblue",
        "Autre": "lightgray"
    }

    for _, row in df.iterrows():
        jours = pd.date_range(row["date_arrivee"], row["date_depart"] - timedelta(days=1))
        for jour in jours:
            calendar_data.append({
                "Date": jour,
                "Client": row["nom_client"],
                "Plateforme": row["plateforme"],
                "Color": couleurs.get(row["plateforme"], "gray")
            })

    cal_df = pd.DataFrame(calendar_data)
    fig = px.timeline(
        cal_df,
        x_start="Date",
        x_end="Date",
        y="Client",
        color="Plateforme",
        color_discrete_map=couleurs
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(height=600, title="Réservations")
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Erreur lors de la génération du calendrier : {e}")

# ---------- TABLEAU ----------
st.subheader("📊 Tableau des Réservations")
st.dataframe(df)



