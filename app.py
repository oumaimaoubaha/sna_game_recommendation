import streamlit as st
import pandas as pd
import networkx as nx
from collections import Counter
import pickle
import requests
import io

# ===========================================================
# 🔥 1. Fonction spéciale pour télécharger les gros fichiers Drive
# ===========================================================

def load_from_drive(url):
    session = requests.Session()
    response = session.get(url, stream=True)

    # Si Google Drive bloque le téléchargement → HTML renvoyé
    if "text/html" in response.headers.get("Content-Type", ""):
        for key, value in response.cookies.items():
            if key.startswith("download_warning"):
                confirm_url = url + "&confirm=" + value
                response = session.get(confirm_url, stream=True)
                break

    return response.content


# ===========================================================
# 🔥 2. Liens Drive (toujours ce format : uc?export=download&id=xxxx)
# ===========================================================

URL_DF = "https://drive.google.com/uc?export=download&id=1BBVNK0RgL3S4PryNmYNse70C4L8SGhsk"
URL_GRAPHS = "https://drive.google.com/uc?export=download&id=1bcFb6RNp1SDEetOhAhSBwSKNnXs2DDjQ"
URL_PARTS  = "https://drive.google.com/uc?export=download&id=1jnmc_2HDaAzyifwXROl8A-1qdf7Vzbck"


# ===========================================================
# 🔥 3. Chargement des données
# ===========================================================

st.write("⏳ Chargement des données... (peut prendre 10–20 secondes)")

# Dataset CSV
df_bytes = load_from_drive(URL_DF)
df = pd.read_csv(io.BytesIO(df_bytes), encoding="utf-8", engine="python")

# Graphes
graphs_bytes = load_from_drive(URL_GRAPHS)
all_graphs = pickle.load(io.BytesIO(graphs_bytes))

# Partitions Louvain
parts_bytes = load_from_drive(URL_PARTS)
all_partitions = pickle.load(io.BytesIO(parts_bytes))

st.success("✔️ Données chargées avec succès !")


# ===========================================================
# 🎨 4. CSS / STYLE
# ===========================================================

st.markdown("""
<style>
html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
h1 { color: #1F2937; font-weight: 800; }
h2 { color: #4F46E5; font-weight: 700; margin-top: 30px; }
</style>
""", unsafe_allow_html=True)


# ===========================================================
# 🏷️ 5. TITRE
# ===========================================================

st.title("🎮 Système de Recommandation de Jeux Vidéo — SNA")
st.write("Basé sur les graphes, les communautés Louvain et l’analyse du réseau d’utilisateurs.")


# ===========================================================
# 🔵 1️⃣ Recommandation PAR JEU
# ===========================================================

st.header("🔵 Recommandation par Jeu")

asin = st.text_input("Entrer un ASIN")
year = st.number_input("Année", min_value=1999, max_value=2018, step=1)

if st.button("Recommander pour ce jeu"):
    if year in all_graphs and asin in all_partitions[year]:

        G = all_graphs[year]
        part = all_partitions[year]

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
# 🟢 2️⃣ Recommandation PAR UTILISATEUR
# ===========================================================

st.header("🟢 Recommandation par Utilisateur")

user = st.text_input("Entrer un reviewerID")

if st.button("Recommander pour cet utilisateur"):
    user_games = df[df["reviewerID"] == user]

    if user_games.empty:
        st.error("Utilisateur introuvable.")
    else:
        community_list = [
            all_partitions[row["year"]].get(row["asin"])
            for _, row in user_games.iterrows()
            if row["asin"] in all_partitions[row["year"]]
        ]

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
# 🔴 3️⃣ Recherche de Communauté
# ===========================================================

st.header("🔴 Explorer une Communauté")

year_c = st.number_input("Année de la communauté", min_value=1999, max_value=2018, step=1)
comm_c = st.number_input("ID de communauté", min_value=0, step=1)

if st.button("Afficher la communauté"):
    part = all_partitions.get(year_c, {})

    comm_games = [g for g, c in part.items() if c == comm_c]

    if not comm_games:
        st.error("Communauté vide ou inexistante.")
    else:
        G = all_graphs[year_c]
        top = sorted(comm_games, key=lambda g: G.degree(g), reverse=True)[:15]
        st.success(f"Top jeux de la communauté {comm_c}")
        st.write(top)
