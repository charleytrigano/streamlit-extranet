import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
import unicodedata

FICHIER = "reservations.xlsx"

# 🔤 Nettoyer accents & caractères spéciaux
def nettoyer_texte(s):
    if isinstance(s, str):
        return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    return str(s)

# 🧾 Multi-ligne PDF sécurisé
def ecrire_pdf_multiligne_safe(pdf, texte, largeur_max=270):
    mots = texte.split()
    ligne = ""
    for mot in mots:
        if pdf.get_string_width(ligne + " " + mot) < largeur_max:
            ligne += " " + mot
        else:
            try:
                pdf.multi_cell(0, 8, ligne.strip())
            except:
                pdf.multi_cell(0, 8, "<ligne non imprimable>")
            ligne = mot
    if ligne:
        try:
            pdf.multi_cell(0, 8, ligne.strip())
        except:
            pdf.multi_cell(0, 8, "<ligne non imprimable>")

# 📥 Charger données
def charger_donnees():
    df = pd.read_excel(FICHIER)
    df["date_arrivee"] = pd.to_datetime(df["date_arrivee"], errors="coerce").dt.date
    df["date_depart"] = pd.to_datetime(df["date_depart"], errors="coerce").dt.date
    df = df[df["date_arrivee"].notna() & df["date_depart"].notna()]
    df["prix_brut"] = pd.to_numeric(df["prix_brut"], errors="coerce").round(2)
    df["prix_net"] = pd.to_numeric(df["prix_net"], errors="coerce").round(2)
    df["charges"] = (df["prix_brut"] - df["prix_net"]).round(2)
    df["%"] = ((df["charges"] / df["prix_brut"]) * 100).round(2)
    df["nuitees"] = (pd.to_datetime(df["date_depart"]) - pd.to_datetime(df["date_arrivee"])).dt.days
    df["annee"] = pd.to_datetime(df["date_arrivee"]).dt.year
    df["mois"] = pd.to_datetime(df["date_arrivee"]).dt.month
    return df