import streamlit as st
import toml

# Fonction pour charger les identifiants depuis le fichier config.toml
def load_config():
    config = toml.load(".streamlit/config.toml")
    return config["auth"]["username"], config["auth"]["password"]

# Fonction de vérification du mot de passe
def check_password(correct_username, correct_password):
    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")
    
    if username == correct_username and password == correct_password:
        return True
    elif username or password:
        st.error("Nom d'utilisateur ou mot de passe incorrect.")
    return False

# Fonction principale de l'application
def main():
    correct_username, correct_password = load_config()

    # Vérifier les identifiants
    if not check_password(correct_username, correct_password):
        st.stop()  # Arrêter l'application si l'utilisateur n'est pas authentifié

    # Afficher la page sécurisée après authentification
    st.write("Bienvenue sur la page sécurisée!")