import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta, datetime
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
import unicodedata
import requests

FICHIER = "reservations.xlsx"

# Infos API Free
FREE_SMS_API_URL = "https://smsapi.free-mobile.fr/sendmsg"
USER = "12026027"
API_KEY = "MF7Qjs3C8KxKHz"

# ➤ Nettoyage texte
def nettoyer_texte(s):
    if isinstance(s, str):
        return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    return str(s)

# ➤ Envoi SMS via Free
def envoyer_sms_free(message):
    params = {"user": USER, "pass": API_KEY, "msg": message}
    return requests.get(FREE_SMS_API_URL, params=params)

# ➤ Multiligne PDF sécurisé
def ecrire_pdf_multiligne_safe(pdf, texte, largeur_max=270):
    try:
        mots = texte.split()
        ligne = ""
        for mot in mots:
            if pdf.get_string_width(ligne + " " + mot) > largeur_max:
                pdf.multi_cell(0, 8, ligne)
                ligne = mot
            else:
                ligne += " " + mot if ligne else mot
        if ligne:
            pdf.multi_cell(0, 8, ligne)
    except:
        pdf.multi_cell(0, 8, "<ligne non imprimable>")

# ➤ Chargement des données
def charger_donnees():
    df = pd.read_excel(FICHIER)
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce").dt.date
    df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce").dt.date
    df = df[df["date_arrivee"].notna() & df["date_depart"].notna()]
    df["prix_brut"] = pd.to_numeric(df["prix_brut"], errors="coerce").round(2)
    df["prix_net"] = pd.to_numeric(df["prix_net"], errors="coerce").round(2)
    df["charges"] = (df["prix_brut"] - df["prix_net"]).round(2)
    df["%"] = ((df["charges"] / df["prix_brut"]) * 100).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
    df["nuitees"] = (pd.to_datetime(df["date_depart"]) - pd.to_datetime(df["date_arrivee"])).dt.days
    df["annee"] = pd.to_datetime(df["date_arrivee"]).dt.year
    df["mois"] = pd.to_datetime(df["date_arrivee"]).dt.month
    return df

# ➤ Liste clients
def liste_clients(df):
    st.subheader("📄 Liste des clients")
    annee = st.selectbox("Année", sorted(df["annee"].unique()))
    mois = st.selectbox("Mois", ["Tous"] + list(range(1, 13)))
    data = df[df["annee"] == annee]
    if mois != "Tous":
        data = data[data["mois"] == mois]
    if not data.empty:
        data["prix_brut_nuit"] = (data["prix_brut"] / data["nuitees"]).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
        data["prix_net_nuit"] = (data["prix_net"] / data["nuitees"]).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
        colonnes = ["nom_client", "plateforme", "date_arrivee", "date_depart", "nuitees",
                    "prix_brut", "prix_net", "charges", "%", "prix_brut_nuit", "prix_net_nuit"]
        st.dataframe(data[colonnes])

        totaux = data[["nuitees", "prix_brut", "prix_net", "charges"]].sum()
        totaux["%"] = ((totaux["charges"] / totaux["prix_brut"]) * 100).round(2) if totaux["prix_brut"] else 0
        st.markdown("#### Total")
        st.write(totaux)

        # Export Excel
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            data[colonnes].to_excel(writer, index=False)
        buffer.seek(0)
        st.download_button("📥 Télécharger la liste Excel", data=buffer, file_name=f"clients_{annee}_{mois}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("Aucune donnée disponible.")

# ➤ Envoi de SMS 24h avant arrivée
def notifier_arrivees_prochaines(df):
    aujourd_hui = datetime.now().date()
    demain = aujourd_hui + timedelta(days=1)
    df_notif = df[df["date_arrivee"] == demain]
    for _, row in df_notif.iterrows():
        nom = row["nom_client"]
        plateforme = row["plateforme"]
        arrivee = row["date_arrivee"].strftime("%Y-%m-%d")
        depart = row["date_depart"].strftime("%Y-%m-%d")
        message = f"{plateforme} - {nom} - {arrivee} - {depart}"
        response = envoyer_sms_free(message)
        if response.status_code == 200:
            st.info(f"📩 SMS envoyé pour {nom}")
        else:
            st.warning(f"❌ Erreur SMS pour {nom} ({response.status_code})")

# ➤ Rapport PDF (paysage)
def exporter_pdf(data, annee):
    pdf = FPDF(orientation="L", format="A4")
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 10, txt=f"Rapport Réservations - {annee}", ln=True, align="C")
    pdf.ln(5)
    for _, row in data.iterrows():
        texte = (
            f"{row['annee']} {row['mois']} | Plateforme: {row['plateforme']} | Nuitées: {int(row['nuitees'])} | "
            f"Brut: {row['prix_brut']:.2f}€ | Net: {row['prix_net']:.2f}€ | Charges: {row['charges']:.2f}€ | "
            f"Moy. brut/nuit: {row['prix_moyen_brut']:.2f}€ | Moy. net/nuit: {row['prix_moyen_net']:.2f}€"
        )
        ecrire_pdf_multiligne_safe(pdf, nettoyer_texte(texte))
    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

# ➤ Rapport mensuel
def rapport_mensuel(df):
    st.subheader("📊 Rapport mensuel")
    annee = st.selectbox("Année", sorted(df["annee"].unique()))
    mois = st.selectbox("Mois", ["Tous"] + list(range(1, 13)))
    data = df[df["annee"] == annee]
    if mois != "Tous":
        data = data[data["mois"] == mois]
    if not data.empty:
        reg = data.groupby(["annee", "mois", "plateforme"]).agg({
            "prix_brut": "sum", "prix_net": "sum", "charges": "sum", "%": "mean", "nuitees": "sum"
        }).reset_index()
        reg["prix_moyen_brut"] = (reg["prix_brut"] / reg["nuitees"]).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
        reg["prix_moyen_net"] = (reg["prix_net"] / reg["nuitees"]).replace([float("inf"), float("-inf")], 0).fillna(0).round(2)
        st.dataframe(reg)

        st.markdown("### 📈 Nuitées par mois")
        pivot_nuits = data.pivot_table(index="mois", columns="plateforme", values="nuitees", aggfunc="sum").fillna(0)
        pivot_nuits.plot(kind="bar", stacked=True)
        st.pyplot(plt.gcf())
        plt.clf()

        st.markdown("### 📈 Total Net par mois")
        pivot_net = data.pivot_table(index="mois", columns="plateforme", values="prix_net", aggfunc="sum").fillna(0)
        pivot_net.plot(kind="bar", stacked=True)
        st.pyplot(plt.gcf())
        plt.clf()

        # Excel export
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            reg.to_excel(writer, index=False)
        buffer.seek(0)
        st.download_button("📥 Télécharger Excel", data=buffer, file_name=f"rapport_{annee}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # PDF export
        pdf_buffer = exporter_pdf(reg, annee)
        st.download_button("📄 Télécharger PDF", data=pdf_buffer, file_name=f"rapport_{annee}.pdf", mime="application/pdf")
    else:
        st.info("Aucune donnée disponible.")

# ➤ Main
def main():
    df = charger_donnees()
    onglet = st.sidebar.radio("Menu", ["📋 Réservations", "➕ Ajouter", "✏️ Modifier / Supprimer", "📅 Calendrier", "📊 Rapport", "📄 Liste clients"])
    if onglet == "📋 Réservations":
        st.title("📋 Réservations")
        st.dataframe(df)
    elif onglet == "📊 Rapport":
        rapport_mensuel(df)
    elif onglet == "📄 Liste clients":
        liste_clients(df)
    # Optionnel : appeler notifier_arrivees_prochaines(df) ici si souhaité automatiquement

if __name__ == "__main__":
    main()