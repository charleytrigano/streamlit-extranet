import streamlit as st
import pandas as pd
import datetime
import requests

st.set_page_config(page_title="📅 Réservations + SMS", layout="centered")

st.title("📩 Envoi automatique de SMS aux clients")

xlsx_file = st.file_uploader("Importer un fichier Excel (.xlsx)", type=["xlsx"])

# ---------------- CONFIGURATION SMS FREE ---------------- #
# Numéros administrateurs Free Mobile
FREE_USER_1 = "12026027"
FREE_API_KEY_1 = "MF7Qjs3C8KxKHz"
FREE_USER_2 = "12026027"
FREE_API_KEY_2 = "1Pat6vSRCLiSXl"
ADMIN_NUMEROS = ["+33617722379", "+33611772793"]

# -------------------------------------------------------- #

if xlsx_file is not None:
    try:
        df = pd.read_excel(xlsx_file)
        df.columns = df.columns.str.strip().str.lower()

        required_cols = {"nom_client", "date_arrivee", "date_depart", "plateforme", "telephone",
                         "prix_brut", "prix_net", "charges", "%"}
        if not required_cols.issubset(df.columns):
            st.error("❌ Le fichier doit contenir les colonnes : " + ", ".join(required_cols))
        else:
            st.success("✅ Données chargées avec succès")
            st.dataframe(df)

            # Nettoyage des dates
            df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce")
            df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce")

            # Sélection des clients arrivant demain
            demain = datetime.date.today() + datetime.timedelta(days=1)
            df_demain = df[df["date_arrivee"].dt.date == demain]

            if not df_demain.empty:
                st.info(f"📨 {len(df_demain)} client(s) arrivent demain ({demain})")

                for _, row in df_demain.iterrows():
                    nom = row["nom_client"]
                    tel = str(row["telephone"])
                    plateforme = row["plateforme"]
                    date_arrivee = row["date_arrivee"].strftime("%d/%m/%Y")
                    date_depart = row["date_depart"].strftime("%d/%m/%Y")

                    message_client = (
                        f"Bonjour {nom},\n"
                        f"Nous sommes heureux de vous accueillir demain à Nice.\n"
                        f"Un emplacement de parking est à votre disposition.\n"
                        f"Merci de nous indiquer votre heure approximative d'arrivée.\n"
                        f"Bon voyage et à demain !\n\n"
                        f"Annick et Charley"
                    )

                    # Envoi au client (si valide)
                    if tel.startswith("33") or tel.startswith("+33") or tel.startswith("06") or tel.startswith("07"):
                        try:
                            url = f"https://smsapi.free-mobile.fr/sendmsg?user={FREE_USER_1}&pass={FREE_API_KEY_1}&msg={requests.utils.quote(message_client)}"
                            requests.get(url, timeout=10)
                            st.success(f"✅ SMS envoyé à {nom} ({tel})")
                        except Exception as e:
                            st.error(f"❌ Échec d’envoi à {tel} : {e}")
                    else:
                        st.warning(f"⚠️ Numéro invalide pour {nom} : {tel}")

                # Confirmation pour les admins
                try:
                    message_admin = f"📢 {len(df_demain)} SMS ont été envoyés pour les arrivées du {demain}."
                    url1 = f"https://smsapi.free-mobile.fr/sendmsg?user={FREE_USER_1}&pass={FREE_API_KEY_1}&msg={requests.utils.quote(message_admin)}"
                    url2 = f"https://smsapi.free-mobile.fr/sendmsg?user={FREE_USER_2}&pass={FREE_API_KEY_2}&msg={requests.utils.quote(message_admin)}"
                    requests.get(url1, timeout=10)
                    requests.get(url2, timeout=10)
                except:
                    st.warning("⚠️ Impossible d’envoyer la confirmation aux administrateurs.")

            else:
                st.info("📭 Aucun client prévu pour demain.")

    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier : {e}")

