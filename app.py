import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import calendar
from io import BytesIO
from openpyxl import Workbook

st.set_page_config(page_title="Portail Extranet", layout="wide")

st.title("🏨 Portail Extranet")

# ✅ Onglets
tab1, tab2, tab3 = st.tabs(["📋 Réservations", "🗓️ Calendrier", "➕ Nouvelle Réservation"])

@st.cache_data
def load_data(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file)
        df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
        df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")
        return df
    except Exception as e:
        st.error(f"Erreur de chargement du fichier : {e}")
        return None

def envoyer_sms_free(identifiant, cle_api, message, destinataires):
    for numero in destinataires:
        try:
            url = f"https://smsapi.free-mobile.fr/sendmsg?user={identifiant}&pass={cle_api}&msg={message}"
            response = requests.get(url)
            if response.status_code == 200:
                st.success(f"✅ SMS envoyé à {numero}")
            else:
                st.error(f"❌ Échec SMS pour {numero} – Code {response.status_code}")
        except Exception as e:
            st.error(f"❌ Erreur envoi SMS à {numero} : {e}")

with tab1:
    st.subheader("📁 Importer le fichier des réservations")
    uploaded_file = st.file_uploader("Importer un fichier .xlsx", type=["xlsx"])
    
    if uploaded_file:
        df = load_data(uploaded_file)

        required_cols = ["nom_client", "date_arrivee", "date_depart", "plateforme", "telephone",
                         "prix_brut", "prix_net", "charges", "%"]

        if df is not None and all(col in df.columns for col in required_cols):
            st.success("✅ Données chargées avec succès")
            st.dataframe(df)

            # SMS 24h avant
            aujourd_hui = datetime.now().date()
            demain = aujourd_hui + timedelta(days=1)
            df_demain = df[df["date_arrivee"].dt.date == demain]

            if not df_demain.empty:
                for _, row in df_demain.iterrows():
                    nom = row["nom_client"]
                    message = (
                        f"Bonjour {nom},\n"
                        "Nous sommes heureux de vous accueillir demain à Nice.\n"
                        "Un emplacement de parking est à votre disposition.\n"
                        "Merci d’indiquer votre heure d’arrivée.\n"
                        "Bon voyage et à demain !\n"
                        "Annick & Charley"
                    )
                    envoyer_sms_free(
                        identifiant="12026027",
                        cle_api="1Pat6vSRCLiSXl",
                        message=message,
                        destinataires=[row["telephone"], "+33611772793"]
                    )

            # Téléchargement du fichier
            def convert_to_excel(dataframe):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    dataframe.to_excel(writer, index=False)
                return output.getvalue()

            st.download_button(
                label="📥 Télécharger le fichier modifié",
                data=convert_to_excel(df),
                file_name="reservations_modifiees.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("❌ Le fichier doit contenir les colonnes : " + ", ".join(required_cols))

with tab2:
    st.subheader("🗓️ Calendrier des réservations")

    if uploaded_file:
        df = load_data(uploaded_file)
        if df is not None and all(col in df.columns for col in required_cols):
            try:
                mois = st.selectbox("📅 Mois", list(calendar.month_name)[1:], index=datetime.now().month - 1)
                annee = st.number_input("Année", value=datetime.now().year, step=1)

                mois_num = list(calendar.month_name).index(mois)
                dates_mois = pd.date_range(start=f"{annee}-{mois_num}-01", end=f"{annee}-{mois_num}-28") + pd.offsets.MonthEnd(0)
                nb_jours = calendar.monthrange(annee, mois_num)[1]

                cal = calendar.Calendar()
                semaines = cal.monthdatescalendar(annee, mois_num)

                couleurs = {
                    "Booking": "#FFB347",
                    "Airbnb": "#87CEFA",
                    "Autre": "#90EE90"
                }

                st.markdown("<style>.calendar-cell { width: 120px; height: 80px; padding: 5px; border: 1px solid #ccc; vertical-align: top; font-size: 12px; }</style>", unsafe_allow_html=True)

                def afficher_jour(date, df):
                    contenu = f"<div><strong>{date.day}</strong><br>"
                    for _, row in df.iterrows():
                        if row["date_arrivee"] <= date < row["date_depart"]:
                            couleur = couleurs.get(row["plateforme"], "#E6E6FA")
                            contenu += f"<div style='background-color:{couleur}; margin:2px; padding:2px; border-radius:4px'>{row['nom_client']}</div>"
                    contenu += "</div>"
                    return contenu

                html = "<table style='border-collapse: collapse;'><tr>"
                jours = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
                for j in jours:
                    html += f"<th class='calendar-cell'><strong>{j}</strong></th>"
                html += "</tr>"

                for semaine in semaines:
                    html += "<tr>"
                    for jour in semaine:
                        if jour.month == mois_num:
                            html += f"<td class='calendar-cell'>{afficher_jour(jour, df)}</td>"
                        else:
                            html += "<td class='calendar-cell' style='background-color:#f0f0f0;'></td>"
                    html += "</tr>"
                html += "</table>"
                st.markdown(html, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Erreur calendrier : {e}")
        else:
            st.warning("Veuillez importer un fichier valide dans l'onglet Réservations.")

with tab3:
    st.subheader("➕ Ajouter une nouvelle réservation")

    with st.form("ajout_reservation"):
        nom_client = st.text_input("Nom du client")
        date_arrivee = st.date_input("Date d'arrivée")
        date_depart = st.date_input("Date de départ")
        plateforme = st.selectbox("Plateforme", ["Airbnb", "Booking", "Autre"])
        telephone = st.text_input("Téléphone (format international)")
        prix_brut = st.text_input("Prix brut")
        prix_net = st.text_input("Prix net")
        charges = st.text_input("Charges")
        pourcentage = st.text_input("%")

        submitted = st.form_submit_button("Valider")

    if submitted and uploaded_file:
        new_row = {
            "nom_client": nom_client,
            "date_arrivee": pd.to_datetime(date_arrivee),
            "date_depart": pd.to_datetime(date_depart),
            "plateforme": plateforme,
            "telephone": telephone,
            "prix_brut": prix_brut,
            "prix_net": prix_net,
            "charges": charges,
            "%": pourcentage
        }

        df = load_data(uploaded_file)
        if df is not None:
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            st.success("✅ Réservation ajoutée avec succès (temporairement)")
        else:
            st.error("Erreur lors du chargement du fichier.")



        except Exception as e:
            st.error(f"Erreur lors de la génération du calendrier : {e}")
    else:
        st.warning("📂 Veuillez importer un fichier Excel pour afficher le calendrier.")
