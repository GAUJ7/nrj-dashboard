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

# Prétraitement des données
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

# Filtrage des machines selon le site sélectionné
if site_selection != "Global":
    machines_site = df2[df2['Site'] == site_selection]['Machine'].unique()
    machine_selection = st.sidebar.selectbox('Choisissez une Machine', ['Global'] + list(machines_site))
else:
    machine_selection = "Global"  # Ou aucune sélection de machine si le site est global

# Choisir l'indicateur à afficher
energie_choice = st.sidebar.radio("Choisissez l'indicateur", ['Gaz (kWh/kg)', 'PE (kg)', 'Prédiction Gaz (kWh/kg)'])

# Choisir la période de filtrage
period_choice = st.sidebar.radio("Sélectionner la période", ('Année', 'Mois', 'Semaine'))

# Préparer les données pour la régression linéaire de la prédiction Gaz (kWh/kg)
df_gaz = df2[df2['PE (kg)'] > 0]
df_gaz = df_gaz.groupby([period_choice, 'Machine', 'Site'])['Gaz (kWh)'].sum().reset_index()

df_pe = df2[df2['Gaz (kWh)'] > 0]
df_pe = df_pe.groupby([period_choice, 'Machine', 'Site'])['PE (kg)'].sum().reset_index()

df_merged = pd.merge(df_gaz, df_pe, on=[period_choice, 'Machine', 'Site'], suffixes=('_gaz', '_pe'))
df_merged['Gaz (kWh/kg)'] = df_merged['Gaz (kWh)'] / df_merged['PE (kg)']

# Filtrage selon site et machine
df_filtered = df_merged if site_selection == 'Global' else df_merged[df_merged['Site'] == site_selection]
df_filtered = df_filtered if machine_selection == 'Global' else df_filtered[df_filtered['Machine'] == machine_selection]

# Régression linéaire pour prédire Gaz (kWh/kg) en fonction de PE (kg)
if energie_choice == 'Prédiction Gaz (kWh/kg)':
    # Régression linéaire
    model = LinearRegression()
    
    # Prédictions
    df_filtered['Predicted Gaz (kWh/kg)'] = model.fit(df_filtered[['PE (kg)']], df_filtered['Gaz (kWh/kg)'])
    
    # Calcul de l'équation de la droite de régression
    slope = model.coef_[0]
    intercept = model.intercept_
    equation = f"y = {slope:.2f}x + {intercept:.2f}"

    # Graphique nuage de points avec droite de régression
    fig = go.Figure()

    # Nuage de points pour les données réelles
    fig.add_trace(go.Scatter(x=df_filtered['PE (kg)'], y=df_filtered['Gaz (kWh/kg)'], mode='markers', name='Données réelles', marker=dict(color='blue')))
    
    # Droite de régression
    fig.add_trace(go.Scatter(x=df_filtered['PE (kg)'], y=df_filtered['Predicted Gaz (kWh/kg)'], mode='lines', name='Droite de régression', line=dict(color='red')))

    # Affichage de l'équation
    fig.add_annotation(x=0.05, y=0.95, text=equation, showarrow=False, font=dict(size=14, color="black"), xref="paper", yref="paper")

    # Mise à jour des axes et titres
    fig.update_layout(
        title="Prédiction Gaz (kWh/kg) en fonction de PE (kg)",
        title_font=dict(size=24),
        xaxis_title="PE (kg)",
        yaxis_title="Gaz (kWh/kg)",
        height=500,
        width=800
    )
    st.plotly_chart(fig)

# Créer l'histogramme pour les autres indicateurs
else:
    # Préparation du graphique pour les autres indicateurs
    fig = go.Figure()

    for idx, machine_selection in enumerate(df_filtered['Machine'].unique()):
        machine_data = df_filtered[df_filtered['Machine'] == machine_selection]
        color = px.colors.qualitative.Light24[idx % len(px.colors.qualitative.Light24)]

        if period_choice == 'Année':
            fig.add_trace(go.Bar(x=machine_data['Année'], y=machine_data[energie_choice], name=machine_selection, marker=dict(color=color)))
        elif period_choice == 'Mois':
            machine_data['Mois'] = pd.to_datetime(machine_data['Mois'], format='%Y%m').dt.strftime('%B %Y')
            fig.add_trace(go.Bar(x=machine_data['Mois'], y=machine_data[energie_choice], name=machine_selection, marker=dict(color=color)))
        elif period_choice == 'Semaine':
            machine_data['Semaine'] = machine_data['Semaine'].apply(lambda x: f"S{int(str(x)[-2:]):02d} {str(x)[:4]}")
            fig.add_trace(go.Bar(x=machine_data['Semaine'], y=machine_data[energie_choice], name=machine_selection, marker=dict(color=color)))

    # Mise à jour des axes et titres
    fig.update_layout(
        barmode='group',
        title=f'Consommation d\'énergie pour {site_selection}',
        title_font=dict(size=24),
        xaxis_title_font=dict(size=18),
        xaxis=dict(color='white', type='category', tickfont=dict(size=16)),
        yaxis_title=f'Consommation ({energie_choice})',
        yaxis_title_font=dict(size=18),
        yaxis=dict(color='white', tickfont=dict(size=16), showgrid=True, gridcolor='white', zerolinecolor='white'),
        legend_title="Site",
        height=500,
        width=2000
    )
    st.plotly_chart(fig)

# Réinitialiser l'index et ne pas l'afficher
df_grouped_reset = df_filtered.reset_index(drop=True)
st.write(df_grouped_reset)
