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
df2 = df2[df2['Machine'] != 'F4B,']  # Filtrer les données

# Assurer que la colonne 'Date' est bien au format datetime
df2['Année'] = df2['Année'].astype(int)
df2['Mois'] = df2['Mois'].astype(int)
df2['Mois-Abrege'] = pd.to_datetime(df2['Mois'], format='%m').dt.strftime('%b')
df2['Mois'] = df2['Année'] * 100 + df2['Mois']
df2['Semaine'] = df2['Année'] * 100 + df2['Semaine']
df2['Semaine_Formate'] = df2['Semaine'].apply(lambda x: f"S{int(str(x)[-2:]):02d} {str(x)[:4]}")
df2['Mois_Formate'] = df2['Mois'].astype(str).str[:4] + '-' + df2['Mois'].astype(str).str[4:]
df2 = df2[df2['Année'].isin([2023, 2024])]

# Charger l'image et afficher en haut à gauche
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
energie_choice = st.sidebar.radio("Choisissez l'indicateur", ['Gaz (kWh/kg)', 'PE (kg)', 'Prédiction Gaz (kWh/kg)'])

# Choisir la période de filtrage
period_choice = st.sidebar.radio("Sélectionner la période", ('Année', 'Mois', 'Semaine'))

# Calcul des sommes de Gaz et Electricité selon la période choisie
df_gaz = df2[df2['PE (kg)'] > 0]
df_gaz = df_gaz.groupby([period_choice, 'Machine', 'Site'])['Gaz (kWh)'].sum().reset_index()

df_pe = df2[df2['Gaz (kWh)'] > 0]
df_pe = df_pe.groupby([period_choice, 'Machine', 'Site'])['PE (kg)'].sum().reset_index()

# Fusionner les données gaz et PE
df_merged = pd.merge(df_gaz, df_pe, on=[period_choice, 'Machine', 'Site'], suffixes=('_gaz', '_pe'))
df_merged['Gaz (kWh/kg)'] = df_merged['Gaz (kWh)'] / df_merged['PE (kg)']
df_final = df_merged[[period_choice, 'Site', 'Machine', 'Gaz (kWh/kg)']]

# Prédiction Gaz (kWh/kg) par régression linéaire
def predict_gaz(df_merged):
    model = LinearRegression()
    predictions = []
    for machine in df_merged['Machine'].unique():
        machine_data = df_merged[df_merged['Machine'] == machine]
        X = machine_data[['PE (kg)']].values.reshape(-1, 1)
        y = machine_data['Gaz (kWh/kg)'].values
        model.fit(X, y)
        prediction = model.predict(X)
        predictions.extend(prediction)
    df_merged['Prédiction Gaz (kWh/kg)'] = predictions
    return df_merged

df_merged = predict_gaz(df_merged)

# Filtrage des données en fonction du site et de la machine
if site_selection == 'Global':
    if energie_choice == 'Gaz (kWh/kg)':
        df_filtered = df_final
    elif energie_choice == 'Prédiction Gaz (kWh/kg)':
        df_filtered = df_merged[[period_choice, 'Site', 'Machine', 'Prédiction Gaz (kWh/kg)']]
    else:
        df_filtered = df2.groupby([period_choice, 'Machine'])[energie_choice].sum().reset_index()
else:
    if machine_selection == 'Global':
        if energie_choice == 'Gaz (kWh/kg)':
            df_filtered = df_final[df_final['Site'] == site_selection]
        elif energie_choice == 'Prédiction Gaz (kWh/kg)':
            df_filtered = df_merged[df_merged['Site'] == site_selection][[period_choice, 'Machine', 'Prédiction Gaz (kWh/kg)']]
        else:
            df_filtered = df2[df2['Site'] == site_selection]
    else:
        if energie_choice == 'Gaz (kWh/kg)':
            df_filtered = df_final[(df_final['Site'] == site_selection) & (df_final['Machine'] == machine_selection)]
        elif energie_choice == 'Prédiction Gaz (kWh/kg)':
            df_filtered = df_merged[(df_merged['Site'] == site_selection) & (df_merged['Machine'] == machine_selection)][[period_choice, 'Machine', 'Prédiction Gaz (kWh/kg)']]
        else:
            df_filtered = df2[(df2['Site'] == site_selection) & (df2['Machine'] == machine_selection)]

# Groupement des données et affichage
df_grouped = df_filtered.groupby([period_choice, 'Machine'])[energie_choice].sum().reset_index()

# Création du graphique avec Plotly
fig = go.Figure()

# Ajouter les sous-graphes avec des couleurs différentes pour chaque site
color_palette = px.colors.qualitative.Light24

for idx, machine_selection in enumerate(df_grouped['Machine'].unique()):
    site_data = df_grouped[df_grouped['Machine'] == machine_selection]
    color = color_palette[idx % len(color_palette)]

    if period_choice == 'Année':
        fig.add_trace(go.Bar(
            x=site_data[period_choice],
            y=site_data[energie_choice],
            name=machine_selection,
            marker=dict(color=color)
        ))
    elif period_choice == 'Mois':
        site_data['Mois'] = site_data['Mois'].apply(
            lambda x: f"{pd.to_datetime(str(x), format='%Y%m').strftime('%B %Y')}" if period_choice == 'Mois' else x
        )
        site_data = site_data.sort_values(by='Mois')
        fig.add_trace(go.Bar(
            x=site_data['Mois'],
            y=site_data[energie_choice],
            name=machine_selection,
            marker=dict(color=color)
        ))
    elif period_choice == 'Semaine':
        fig.add_trace(go.Bar(
            x=site_data['Semaine'],
            y=site_data[energie_choice],
            name=machine_selection,
            marker=dict(color=color)
        ))

# Mise à jour des axes et titres
fig.update_layout(
    barmode='group',
    title=f'Consommation d\'énergie pour {site_selection}',
    title_font=dict(size=24),
    xaxis_title_font=dict(size=18),
    xaxis=dict(
        color='white',
        type='category',
        tickfont=dict(size=16),
    ),
    yaxis_title=f'Consommation ({energie_choice})',
    yaxis_title_font=dict(size=18),
    yaxis=dict(
        color='white',
        tickfont=dict(size=16),
        showgrid=True,
        gridcolor='white',
        zerolinecolor='white',
    ),
    legend_title="Site",
    height=500,
    width=2000,
)

# Affichage du graphique dans Streamlit
st.plotly_chart(fig)

# Réinitialiser l'index et ne pas l'afficher
df_grouped_reset = df_grouped.reset_index(drop=True)
st.write(df_grouped_reset)