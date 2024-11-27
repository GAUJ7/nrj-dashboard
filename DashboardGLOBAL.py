import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import plotly.express as px

# Chargement des données
df2 = pd.read_csv("Global_streamlit.csv", sep=";")
df2['Site'] = df2['Site'].replace({'PTWE42 Andrézieux': 'PTWE42'})

# Assurer que la colonne 'Date' est bien au format datetime
df2['Date'] = pd.to_datetime(df2['Date'], errors='coerce')

# Extraire l'année, le mois et l'année-mois
df2['Année'] = df2['Date'].dt.year
df2['Mois'] = df2['Date'].dt.month
df2['Année-Mois'] = df2['Année'] * 100 + df2['Mois']

# Filtrage des données dans Streamlit
st.sidebar.title("Filtrage des données")
sites = df2['Site'].unique()
site_selection = st.sidebar.selectbox('Choisissez un site', list(sites) + ['Global'])

# Choisir l'énergie à afficher
energie_choice = st.sidebar.radio("Choisissez l'énergie", ['Gaz (kWh/kg)', 'Electricité (kWh/kg)', 'Gaz (kWh)', 'Electricité (kWh)', 'PE (kg)'])

# Choisir deux mois à comparer
start_year_month = st.sidebar.selectbox("Sélectionner le mois de début", sorted(df2['Année-Mois'].unique()))
end_year_month = st.sidebar.selectbox("Sélectionner le mois de fin", sorted(df2['Année-Mois'].unique()))

# Filtrer les données pour les deux mois sélectionnés
df_filtered = df2[(df2['Année-Mois'] >= start_year_month) & (df2['Année-Mois'] <= end_year_month)]

# Filtrage selon le site sélectionné
if site_selection != 'Global':
    df_filtered = df_filtered[df_filtered['Site'] == site_selection]

# Agrégation des données selon l'énergie choisie
if energie_choice == 'Gaz (kWh/kg)' or energie_choice == 'Electricité (kWh/kg)':
    df_filtered['Gaz (kWh/kg)'] = df_filtered['Gaz (kWh)'] / df_filtered['PE (kg)']
    df_filtered['Electricité (kWh/kg)'] = df_filtered['Electricité (kWh)'] / df_filtered['PE (kg)']

# Groupement par période (Année-Mois)
df_grouped = df_filtered.groupby(['Année-Mois', 'Site'])[energie_choice].sum().reset_index()

# Création du graphique avec Plotly
color_palette = px.colors.qualitative.Safe  # Palette de couleurs pré-définie
fig = go.Figure()

# Ajouter les sous-graphes avec des couleurs différentes pour chaque site
for idx, site in enumerate(df_grouped['Site'].unique()):
    site_data = df_grouped[df_grouped['Site'] == site]
    color = color_palette[idx % len(color_palette)]  # Assurer une couleur unique pour chaque site
    fig.add_trace(go.Bar(
        x=site_data['Année-Mois'],
        y=site_data[energie_choice],
        name=site,
        marker=dict(color=color)
    ))

# Mise à jour des axes et titres
fig.update_layout(
    barmode='group',
    title=f'Comparaison de la consommation d\'énergie pour {site_selection}',
    xaxis_title='Année-Mois',
    yaxis_title=f'Consommation ({energie_choice})',
    legend_title="Site",
    xaxis=dict(type='category', categoryorder='category ascending')
)

# Affichage du graphique dans Streamlit
st.plotly_chart(fig)

# Affichage des données agrégées
st.write(df_grouped)