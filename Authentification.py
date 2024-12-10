import streamlit as st
import streamlit_authenticator as stauth

# Utiliser un dictionnaire avec les utilisateurs
usernames = ['admin']
passwords = ['password123']

# Crée un objet authentificateur
authenticator = stauth.Authenticate(usernames, passwords)

# Afficher le formulaire de connexion
name, authentication_status = authenticator.login('Connexion', 'main')

if authentication_status:
    st.write(f"Bienvenue {name}!")
else:
    st.warning("Nom d'utilisateur ou mot de passe incorrect.")
    st.stop()  # Arrêter l'exécution si l'authentification échoue