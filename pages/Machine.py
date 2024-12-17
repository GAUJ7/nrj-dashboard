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

# Traitement de la colonne 'Date' pour extraire les informations
df2['Année'] = df2['Année'].astype(int)
df2['Mois'] = df2['Mois'].astype(int)
df2['Mois-Abrege'] = pd.to_datetime(df2['Mois'], format='%m').dt.strftime('%b')
df2['Mois'] = df2['Année'] * 100 + df2['Mois']
df2['Semaine'] = df2['Année'] * 100 + df2['Semaine']
df2['Semaine_Formate'] = df2['Semaine'].apply(lambda x: f"S{int(str(x)[-2:]):02d} {str(x)[:4]}")
df2['Mois_Formate'] = df2['Mois'].astype(str).str[:4] + '-' + df2['Mois'].astype(str).str[4:]
df2 = df2[df2['Année'].isin([2023, 2024])]

# Chargement de l'image
image = "PT.jpg"  # Remplacez ce chemin par le chemin réel de votre image
st.image(image)

# Filtrage des données dans Streamlit
st.sidebar.title("Filtrage des données")
sites = df2['Site'].unique()
site_selection = st.sidebar.selectbox('Choisissez un site', ['Global'] + list(sites))

# Filtrer les machines selon le site sélectionné
if site_selection != "Global":
    machines_site = df2[df2['Site'] == site_selection]['Machine'].unique()
    machine_selection = st.sidebar.selectbox('Choisissez une Machine', ['Global'] + list(machines_site))
else:
    machine_selection = "Global"  # Ou aucune sélection de machine si le site est global

# Choisir l'indicateur à afficher
energie_choice = st.sidebar.radio("Choisissez l'indicateur", ['Gaz (kWh/kg)', 'PE (kg)', 'Prédiction Gaz (kwh/kg)'])

# Choisir la période de filtrage
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

# Filtrage des données
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

# Filtrage par période
if period_choice == 'Année':
    start_year = st.sidebar.selectbox("Année de début", sorted(df2['Année'].unique()), index=1)
    end_year = st.sidebar.selectbox("Année de fin", sorted(df2['Année'].unique()), index=1)
    df_filtered = df_filtered[(df_filtered['Année'] >= start_year) & (df_filtered['Année'] <= end_year)]
elif period_choice == 'Mois':
    start_year_month = st.sidebar.selectbox("Sélectionner le mois de début", sorted(df2['Mois_Formate'].unique()), index=12)
    end_year_month = st.sidebar.selectbox("Sélectionner le mois de fin", sorted(df2['Mois_Formate'].unique()), index=20)
    start_year_month_raw = int(start_year_month.replace('-', ''))
    end_year_month_raw = int(end_year_month.replace('-', ''))
    df_filtered = df_filtered[(df_filtered['Mois'] >= start_year_month_raw) & (df_filtered['Mois'] <= end_year_month_raw)]
elif period_choice == 'Semaine':
    start_week = st.sidebar.selectbox("Sélectionner la semaine de début", sorted(df2['Semaine_Formate'].unique(), key=lambda x: (int(x.split()[1]), int(x.split()[0][1:]))), index=52)
    end_week = st.sidebar.selectbox("Sélectionner la semaine de fin", sorted(df2['Semaine_Formate'].unique(), key=lambda x: (int(x.split()[1]), int(x.split()[0][1:]))), index=87)
    start_week_raw = int(start_week.split()[1]) * 100 + int(start_week.split()[0][1:])
    end_week_raw = int(end_week.split()[1]) * 100 + int(end_week.split()[0][1:])
    df_filtered = df_filtered[(df_filtered['Semaine'] >= start_week_raw) & (df_filtered['Semaine'] <= end_week_raw)]

# Régression linéaire pour la prédiction Gaz (kWh/kg) basé sur PE (kg)
if energie_choice == 'Prédiction Gaz (kwh/kg)':
    # Appliquer la régression linéaire sur les données
    reg_model = LinearRegression()
    X = df_filtered['PE (kg)'].values.reshape(-1, 1)  # Variable indépendante (PE)
    y = df_filtered['Gaz (kWh/kg)'].values  # Variable dépendante (Gaz)

    # Entraîner le modèle
    reg_model.fit(X, y)

    # Calculer la droite de régression
    y_pred = reg_model.predict(X)

    # Créer un graphique avec la droite de régression et les points
    fig = go.Figure()

    # Ajouter les points
    fig.add_trace(go.Scatter(x=df_filtered['PE (kg)'], y=df_filtered['Gaz (kWh/kg)'], mode='markers', name='Données', marker=dict(color='blue')))

    # Ajouter la droite de régression
    fig.add_trace(go.Scatter(x=df_filtered['PE (kg)'], y=y_pred, mode='lines', name='Régression Linéaire', line=dict(color='red')))

    # Ajouter l'équation de la droite de régression
    equation = f"y = {reg_model.coef_[0]:.4f}x + {reg_model.intercept_:.4f}"
    fig.add_annotation(x=0.05, y=0.95, text=f"Équation : {equation}", showarrow=False, font=dict(size=14, color="black"), align="left", xref="paper", yref="paper")

    # Mise en forme du graphique
    fig.update_layout(title='Prédiction Gaz (kWh/kg) basé sur PE (kg)', xaxis_title='PE (kg)', yaxis_title='Gaz (kWh/kg)', height=500)

    # Affichage du graphique dans Streamlit
    st.plotly_chart(fig)
else:
    # Autres graphiques pour les autres indicateurs (Histogrammes)
    # ... code pour afficher les autres histogrammes
    pass

# Affichage des données filtrées sans l'index
df_filtered_reset = df_filtered.reset_index(drop=True)
st.write(df_filtered_reset)