import streamlit as st
import pandas as pd
import networkx as nx
from collections import Counter
import pickle
import requests
import zipfile
import io

# ===========================================================
# 🔧 1. Téléchargement Google Drive (gros fichiers)
# ===========================================================
def load_from_drive_big(file_id):
    """Télécharge un fichier depuis Google Drive, même lourd, même protégé."""
    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()

    response = session.get(URL, params={'id': file_id}, stream=True)

    # Vérifier TOKEN Google Drive
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            response = session.get(
                URL,
                params={'id': file_id, 'confirm': value},
                stream=True
            )
            break

    return response.content


# ===========================================================
# 🔗 2. IDs Google Drive des fichiers
# ===========================================================
ID_ZIP = "1nizxGHWa216MurrblfuxtzV6dvmB09lc"       # dataset_clean.csv (dans ZIP)
ID_GRAPHS = "1bcFb6RNp1SDEetOhAhSBwSKNnXs2DDjQ"    # all_graphs.pkl
ID_PARTS = "1jnmc_2HDaAzyifwXROl8A-1qdf7Vzbck"      # all_partitions.pkl


# ===========================================================
# 📥 3. Chargement du dataset depuis le ZIP
# ===========================================================
@st.cache_data(show_spinner=True)
def load_dataset():
    zip_bytes = load_from_drive_big(ID_ZIP)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        with z.open("dataset_clean.csv") as f:
            df = pd.read_csv(f, encoding="utf-8", on_bad_lines="skip")
    return df

df = load_dataset()


# ===========================================================
# 📥 4. Chargement graphes + partitions
# ===========================================================
@st.cache_resource(show_spinner=True)
def load_graphs():
    graphs_bytes = load_from_drive_big(ID_GRAPHS)
    return pickle.load(io.BytesIO(graphs_bytes))

@st.cache_resource(show_spinner=True)
def load_partitions():
    parts_bytes = load_from_drive_big(ID_PARTS)
    return pickle.load(io.BytesIO(parts_bytes))

all_graphs = load_graphs()
all_partitions = load_partitions()


# ===========================================================
# 🎨 5. Thème graphique
# ===========================================================
st.markdown("""
<style>
html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
h1 { color: #1F2937; font-weight: 800; }
h2 { color: #4F46E5; font-weight: 700; margin-top: 30px; }
</style>
""", unsafe_allow_html=True)


# ===========================================================
# 🏷️ 6. Titre principal
# ===========================================================
st.title("🎮 Système de Recommandation de Jeux – Analyse de Réseaux (SNA)")
st.write("""
Cette application utilise :

- 🧩 Les graphes bipartites joueurs–jeux  
- 🧭 L’algorithme de **Louvain** pour détecter les communautés  
- 🤖 Trois stratégies de recommandation

Toutes les données sont chargées dynamiquement depuis Google Drive.
""")


# ===========================================================
# 🔵 7. Recommandation par jeu
# ===========================================================
st.header("🔵 Recommandation par Jeu")

asin = st.text_input("Entrer un ASIN")
year = st.number_input("Année", min_value=1999, max_value=2018, step=1)

if st.button("Recommander pour ce jeu"):
    if year not in all_graphs:
        st.error("Année non trouvée.")
    elif asin not in all_partitions[year]:
        st.error("ASIN introuvable dans cette année.")
    else:
        G = all_graphs[year]
        part = all_partitions[year]

        comm = part.get(asin)
        st.info(f"Communauté du jeu : **{comm}**")

        comm_games = [g for g, c in part.items() if c == comm and g != asin]
        top = sorted(comm_games, key=lambda g: G.degree(g), reverse=True)[:10]

        st.success("Top recommandations :")
        st.write(top)


# ===========================================================
# 🟢 8. Recommandation par utilisateur
# ===========================================================
st.header("🟢 Recommandation par Utilisateur")

user = st.text_input("Entrer un reviewerID")

if st.button("Recommander pour cet utilisateur"):
    user_games = df[df["reviewerID"] == user]

    if user_games.empty:
        st.error("Utilisateur introuvable.")
    else:
        # Liste des communautés fréquentes chez l'utilisateur
        community_list = []

        for _, row in user_games.iterrows():
            y = row["year"]
            g = row["asin"]
            if y in all_partitions and g in all_partitions[y]:
                community_list.append(all_partitions[y][g])

        if len(community_list) == 0:
            st.error("Impossible d'identifier une communauté dominante.")
        else:
            dominant_comm = Counter(community_list).most_common(1)[0][0]
            st.info(f"Communauté dominante : **{dominant_comm}**")

            sample_year = int(user_games["year"].mode()[0])
            G = all_graphs[sample_year]
            part = all_partitions[sample_year]

            comm_games = [g for g, c in part.items() if c == dominant_comm]
            played = set(user_games["asin"])

            recos = [g for g in comm_games if g not in played]
            top = sorted(recos, key=lambda g: G.degree(g), reverse=True)[:10]

            st.success("Recommandations personnalisées :")
            st.write(top)


# ===========================================================
# 🔴 9. Exploration d’une communauté
# ===========================================================
st.header("🔴 Explorer une Communauté")

year_c = st.number_input("Année", min_value=1999, max_value=2018, step=1)
comm_c = st.number_input("ID de communauté", min_value=0, step=1)

if st.button("Afficher la communauté"):
    if year_c not in all_graphs:
        st.error("Année non trouvée.")
    else:
        G = all_graphs[year_c]
        part = all_partitions[year_c]

        comm_games = [g for g, c in part.items() if c == comm_c]

        if len(comm_games) == 0:
            st.error("Communauté vide.")
        else:
            top = sorted(comm_games, key=lambda g: G.degree(g), reverse=True)[:15]
            st.success(f"Top jeux de la communauté {comm_c}")
            st.write(top)
