import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import plotly.express as px  # Pour accéder à des palettes de couleurs
import toml
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="Tableau", layout="wide")

# Fonction pour charger les informations d'authentification
# Fonction pour charger les informations d'authentification
def load_config():
    config = toml.load('.streamlit/config.toml')
    return config['auth']['password']

# Fonction de vérification du mot de passe
def check_password(correct_password):
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True  # L'utilisateur est déjà authentifié, ne rien demander

    password = st.text_input("Mot de passe", type="password")
    
    if password == correct_password:
        st.session_state.authenticated = True
        return True  # Authentification réussie
    elif password:
        st.error("Mot de passe incorrect.")
    
    return False

# Fonction principale
def main():
    # N'afficher le titre que si l'utilisateur n'est pas encore authentifié
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.title("Application Sécurisée")
    
    correct_password = load_config()

    # Vérification de l'authentification
    if not check_password(correct_password):
        st.stop()  # Arrêter l'exécution si l'authentification échoue


if __name__ == "__main__":
    main()

# Chargement des données
df2 = pd.read_csv("20241209 Machine_streamlit.csv", sep=";")
df2 = df2[df2['Machine'] != 'F4B,']

# Traitement des colonnes de dates et de périodes
df2['Année'] = df2['Année'].astype(int)
df2['Mois'] = df2['Mois'].astype(int)
df2['Mois-Abrege'] = pd.to_datetime(df2['Mois'], format='%m').dt.strftime('%b')
df2['Mois'] = df2['Année'] * 100 + df2['Mois']
df2['Semaine'] = df2['Année'] * 100 + df2['Semaine']
df2['Semaine_Formate'] = df2['Semaine'].apply(lambda x: f"S{int(str(x)[-2:]):02d} {str(x)[:4]}")
df2['Mois_Formate'] = df2['Mois'].astype(str).str[:4] + '-' + df2['Mois'].astype(str).str[4:]
df2 = df2[df2['Année'].isin([2023, 2024])]

# Filtrage des données dans Streamlit
st.sidebar.title("Filtrage des données")
sites = df2['Site'].unique()
site_selection = st.sidebar.selectbox('Choisissez un site', ['Global'] + list(sites))

if site_selection != "Global":
    machines_site = df2[df2['Site'] == site_selection]['Machine'].unique()
    machine_selection = st.sidebar.selectbox('Choisissez une Machine', ['Global'] + list(machines_site))
else:
    machine_selection = "Global"

energie_choice = st.sidebar.radio("Choisissez l'indicateur", ['Gaz (kWh/kg)', 'PE (kg)', 'Prédiction Gaz (kWh/kg)'])
period_choice = st.sidebar.radio("Sélectionner la période", ('Année', 'Mois', 'Semaine'))

# Calcul des sommes de Gaz et Electricité selon la période choisie
df_gaz = df2[df2['PE (kg)'] > 0]
df_gaz = df_gaz.groupby([period_choice, 'Machine', 'Site'])['Gaz (kWh)'].sum().reset_index()

df_pe = df2[df2['Gaz (kWh)'] > 0]
df_pe = df_pe.groupby([period_choice, 'Machine', 'Site'])['PE (kg)'].sum().reset_index()

# Fusionner les données
df_merged = pd.merge(df_gaz, df_pe, on=[period_choice, 'Machine', 'Site'], suffixes=('_gaz', '_pe'))
df_merged['Gaz (kWh/kg)'] = df_merged['Gaz (kWh)'] / df_merged['PE (kg)']
df_final = df_merged[[period_choice, 'Site', 'Machine', 'Gaz (kWh/kg)']]

# Filtrer les données selon le site et la machine
if site_selection == 'Global':
    if energie_choice == 'Gaz (kWh/kg)':
        df_filtered = df_final
    else:
        df_filtered = df2.groupby([period_choice, 'Machine'])[energie_choice].sum().reset_index()
else:
    if machine_selection == 'Global':
        if energie_choice == 'Gaz (kWh/kg)':
            df_filtered = df_final[df_final['Site'] == site_selection]
        else:
            df_filtered = df2[df2['Site'] == site_selection]
            df_filtered = df_filtered.groupby([period_choice, 'Machine'])[energie_choice].sum().reset_index()
    else:
        if energie_choice == 'Gaz (kWh/kg)':
            df_filtered = df_final[(df_final['Site'] == site_selection) & (df_final['Machine'] == machine_selection)]
        else:
            df_filtered = df2[(df2['Site'] == site_selection) & (df2['Machine'] == machine_selection)]

# Ajouter la régression linéaire pour la prédiction de "Gaz (kWh/kg)"
if energie_choice == 'Prédiction Gaz (kWh/kg)':
    # Appliquer la régression linéaire sur les données filtrées
    X = df_filtered[['PE (kg)']]  # Variable indépendante (PE en kg)
    y = df_filtered['Gaz (kWh/kg)']  # Variable dépendante (Gaz en kWh/kg)

    reg = LinearRegression()
    reg.fit(X, y)
    df_filtered['Prédiction Gaz (kWh/kg)'] = reg.predict(X)

    # Calcul de l'équation de la droite de régression
    coef = reg.coef_[0]
    intercept = reg.intercept_
    equation = f"y = {coef:.2f}x + {intercept:.2f}"

# Créer un graphique avec un nuage de points et la droite de régression
fig = go.Figure()

# Nuage de points (scatter)
fig.add_trace(go.Scatter(
    x=df_filtered['PE (kg)'],
    y=df_filtered['Gaz (kWh/kg)'],
    mode='markers',
    name='Données observées',
    marker=dict(color='blue', size=8)
))

# Droite de régression
if energie_choice == 'Prédiction Gaz (kWh/kg)':
    fig.add_trace(go.Scatter(
        x=df_filtered['PE (kg)'],
        y=df_filtered['Prédiction Gaz (kWh/kg)'],
        mode='lines',
        name='Droite de régression',
        line=dict(color='red', width=2)
    ))

# Mise à jour du graphique
fig.update_layout(
    title=f'Prédiction Gaz (kWh/kg) pour {site_selection}',
    title_font=dict(size=24),
    xaxis_title="PE (kg)",
    yaxis_title="Gaz (kWh/kg)",
    xaxis=dict(color='white'),
    yaxis=dict(color='white'),
    showlegend=True
)

# Affichage du graphique avec la droite de régression
st.plotly_chart(fig)

# Afficher l'équation de la régression
if energie_choice == 'Prédiction Gaz (kWh/kg)':
    st.write(f"Équation de la droite de régression : {equation}")

# Réinitialiser l'index et afficher les données
df_filtered_reset = df_filtered.reset_index(drop=True)
st.write(df_filtered_reset)