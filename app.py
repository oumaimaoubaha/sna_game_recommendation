import streamlit as st
import pandas as pd
import networkx as nx
from collections import Counter
import pickle
import requests
import io

# ===========================================================
# 📌 1. Fonction fiable pour télécharger un fichier Drive
# ===========================================================
def load_from_drive(file_id):
    """Télécharge un fichier Google Drive via son ID."""
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    response = requests.get(url)
    return response.content


# ===========================================================
# 📌 2. IDs Drive (PAS LES URLs ENTIÈRES)
# ===========================================================
ID_DF = "1BBVNK0RgL3S4PryNmYNse70C4L8SGhsk"
ID_GRAPHS = "1bcFb6RNp1SDEetOhAhSBwSKNnXs2DDjQ"
ID_PARTS = "1jnmc_2HDaAzyifwXROl8A-1qdf7Vzbck"


# ===========================================================
# 📌 3. Chargement des fichiers
# ===========================================================
st.write("⏳ Chargement des données...")

# CSV
df = pd.read_csv(
    io.BytesIO(load_from_drive(ID_DF)),
    encoding="utf-8",
    on_bad_lines="skip"
)

# Pickle graphes
all_graphs = pickle.load(io.BytesIO(load_from_drive(ID_GRAPHS)))

# Pickle partitions
all_partitions = pickle.load(io.BytesIO(load_from_drive(ID_PARTS)))

st.success("✔️ Données chargées avec succès !")


# ===========================================================
# 🎨 4. Thème CSS
# ===========================================================
st.markdown("""
<style>
html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
h1 { color: #1F2937; font-weight: 800; }
h2 { color: #4F46E5; font-weight: 700; margin-top: 30px; }
</style>
""", unsafe_allow_html=True)


# ===========================================================
# 🏷️ 5. Titre
# ===========================================================
st.title("🎮 Recommandation de Jeux – Analyse SNA")
st.write("Recommandations basées sur les graphes et les communautés Louvain.")


# ===========================================================
# 🔵 6. Recommandation PAR JEU
# ===========================================================
st.header("🔵 Recommandation par Jeu")

asin = st.text_input("Entrer un ASIN")
year = st.number_input("Année", min_value=1999, max_value=2018, step=1)

if st.button("Recommander pour ce jeu"):
    if year in all_graphs and asin in all_partitions[year]:

        part = all_partitions[year]
        G = all_graphs[year]

        comm = part.get(asin)

        if comm is None:
            st.error("Ce jeu n'existe pas dans cette année.")
        else:
            st.info(f"Communauté du jeu : **{comm}**")
            comm_games = [g for g, c in part.items() if c == comm and g != asin]
            top = sorted(comm_games, key=lambda g: G.degree(g), reverse=True)[:10]

            st.success("Top recommandations :")
            st.write(top)
    else:
        st.error("ASIN non trouvé.")


# ===========================================================
# 🟢 7. Recommandation PAR UTILISATEUR
# ===========================================================
st.header("🟢 Recommandation par Utilisateur")

user = st.text_input("Entrer un reviewerID")

if st.button("Recommander pour cet utilisateur"):
    user_games = df[df["reviewerID"] == user]

    if user_games.empty:
        st.error("Utilisateur introuvable.")
    else:
        community_list = []
        for _, row in user_games.iterrows():
            y = row["year"]
            g = row["asin"]
            if g in all_partitions[y]:
                community_list.append(all_partitions[y][g])

        dominant_comm = Counter(community_list).most_common(1)[0][0]
        st.info(f"Communauté dominante : **{dominant_comm}**")

        sample_year = int(user_games["year"].mode()[0])
        G = all_graphs[sample_year]
        part = all_partitions[sample_year]

        comm_games = [g for g, c in part.items() if c == dominant_comm]
        played = user_games["asin"].tolist()

        recos = [g for g in comm_games if g not in played]
        top = sorted(recos, key=lambda g: G.degree(g), reverse=True)[:10]

        st.success("Recommandations personnalisées :")
        st.write(top)


# ===========================================================
# 🔴 8. Explorer une communauté
# ===========================================================
st.header("🔴 Explorer une Communauté")

year_c = st.number_input("Année de la communauté", min_value=1999, max_value=2018, step=1)
comm_c = st.number_input("ID de communauté", min_value=0, step=1)

if st.button("Afficher la communauté"):
    if year_c in all_graphs:
        G = all_graphs[year_c]
        part = all_partitions[year_c]

        comm_games = [g for g, c in part.items() if c == comm_c]

        if len(comm_games) == 0:
            st.error("Communauté vide ou inexistante.")
        else:
            top = sorted(comm_games, key=lambda g: G.degree(g), reverse=True)[:15]
            st.success(f"Top jeux de la communauté {comm_c}")
            st.write(top)
