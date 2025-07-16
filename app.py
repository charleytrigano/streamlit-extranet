import streamlit as st
import pandas as pd
import datetime
import requests
import plotly.express as px

st.set_page_config(page_title="📆 Extranet Streamlit", layout="wide")
st.title("📆 Portail Extranet - Calendrier et SMS")

st.markdown("Importez un fichier `.xlsx` avec les réservations. Il doit contenir les colonnes suivantes :")
st.code("nom_client, date_arrivee, date_depart, plateforme, telephone, prix_brut, prix_net, charges, %")

# ⏳ Upload du fichier Excel
excel_file = st.file_uploader("📁 Importer un fichier Excel", type=["xlsx"])

# 📅 Date d'aujourd'hui et demain
aujourd_hui = datetime.date.today()
demain = aujourd_hui + datetime.timedelta(days=1)
demain_str = demain.strftime("%Y-%m-%d")

# 📩 Paramètres pour API Free Mobile (modifie avec tes infos)
FREE_SMS_USERS = [
    {"user": "12026027", "api_key": "1Pat6vSRCLiSXl", "tel": "+33617722379"},
    {"user": "12026027", "api_key": "1Pat6vSRCLiSXl", "tel": "+33611772793"},
]

# 📦 Traitement du fichier
if excel_file:
    try:
        df = pd.read_excel(excel_file, engine="openpyxl")

        # 🧼 Vérif des colonnes requises
        required_cols = {"nom_client", "date_arrivee", "date_depart", "plateforme", "telephone", "prix_brut", "prix_net", "charges", "%"}
        if not required_cols.issubset(set(df.columns)):
            st.error(f"❌ Le fichier doit contenir les colonnes : {', '.join(sorted(required_cols))}")
        else:
            # ✅ Conversion des dates
            df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce").dt.date
            df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce").dt.date

            st.success("✅ Données correctement importées !")
            st.dataframe(df)

            # 📅 Affichage calendrier Plotly
            st.subheader("📊 Calendrier des réservations")
            calendar_df = df.copy()
            calendar_df["Durée"] = calendar_df["date_depart"] - calendar_df["date_arrivee"]
            calendar_df["nom_affiche"] = calendar_df["nom_client"] + " (" + calendar_df["plateforme"] + ")"

            fig = px.timeline(
                calendar_df,
                x_start="date_arrivee",
                x_end="date_depart",
                y="nom_affiche",
                color="plateforme",
                title="Calendrier des séjours"
            )
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)

            # 📩 Envoi automatique de SMS pour les arrivées demain
            st.subheader("📩 Envoi automatique de SMS aux clients arrivant demain")
            df_demain = df[df["date_arrivee"] == demain]

            if not df_demain.empty:
                for _, row in df_demain.iterrows():
                    msg = (
                        f"Bonjour {row['nom_client']},\n"
                        "Nous sommes heureux de vous accueillir demain à Nice.\n"
                        "Un emplacement de parking est à votre disposition sur place.\n"
                        "Merci de nous indiquer votre heure approximative d'arrivée.\n"
                        "Bon voyage et à demain !\nAnnick & Charley"
                    )
                    for user in FREE_SMS_USERS:
                        url = f"https://smsapi.free-mobile.fr/sendmsg?user={user['user']}&pass={user['api_key']}&msg={requests.utils.quote(msg)}"
                        response = requests.get(url)
                        if response.status_code == 200:
                            st.success(f"✅ SMS envoyé à {row['nom_client']} pour {user['tel']}")
                        else:
                            st.error(f"❌ Échec de l'envoi à {user['tel']} - Code : {response.status_code}")
            else:
                st.info("📭 Aucune arrivée prévue demain.")
    except Exception as e:
        st.error(f"❌ Erreur lors du traitement du fichier : {e}")




