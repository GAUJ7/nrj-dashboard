import toml
import streamlit as st

# Fonction pour charger les données du fichier .toml
def load_config():
    config = toml.load(".streamlit/config.toml")
    return config["auth"]["username"], config["auth"]["password"]

# Fonction de vérification du mot de passe
def check_password(correct_username, correct_password):
    username = st.text_input("Nom d'utilisateur", key="username")
    password = st.text_input("Mot de passe", type="password", key="password")
    
    if username == correct_username and password == correct_password:
        return True
    elif username or password:
        st.error("Nom d'utilisateur ou mot de passe incorrect.")
    return False

# Fonction principale de l'application
def main():
    st.title("Application sécurisée")
    
    correct_username, correct_password = load_config()
    
    # Créer une page d'authentification
    if not check_password(correct_username, correct_password):
        st.stop()  # Arrêter l'application si l'utilisateur n'est pas authentifié
    
    # Si l'authentification est réussie, l'application continue
    st.write("Bienvenue dans l'application sécurisée!")

# Si l'utilisateur n'est pas authentifié, le code ne continue pas et la page d'authentification reste affichée
if __name__ == "__main__":
    main()