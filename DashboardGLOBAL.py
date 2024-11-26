import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import plotly.express as px

# Chargement des données
df2 = pd.read_csv("Global_streamlit.csv", sep=";")
df2['Site'] = df2['Site'].replace({'PTWE42 Andrézieux': 'PTWE42'})

# Assurer que la colonne 'Date' est bien au format datetime
df2['Date'] = pd.to_datetime(df2['Date'], errors='coerce')

# Extraire l'année, le mois et le jour
df2['Année'] = df2['Date'].dt.year
df2['Mois'] = df2['Date'].dt.month
df2['Jour'] = df2['Date'].dt.day
df2['Mois-Abrege'] = df2['Date'].dt.strftime('%b')  # Mois abrégés (ex: Jan, Feb, Mar, etc.)
df2['Année-Mois'] = df2['Année'].astype(str) + '-' + df2['Mois-Abrege']  # Format Année-Mois (ex: 2024-Jan)

# Filtrage des données dans Streamlit
st.sidebar.title("Filtrage des données")
sites = df2['Site'].unique()
site_selection = st.sidebar.selectbox('Choisissez un site', list(sites) + ['Global'])

# Choisir l'énergie à afficher
energie_choice = st.sidebar.radio("Choisissez l'énergie", ['Gaz (kWh/kg)', 'Electricité (kWh/kg)', 'Gaz (kWh)', 'Electricité (kWh)', 'PE (kg)'])

# Choisir la période de filtrage
period_choice = st.sidebar.radio("Sélectionner la période", ('Année', 'Mois', 'Jour'))

# Filtrage des données par site
if site_selection == 'Global':  
    # Si "Global" est sélectionné, utiliser la médiane pour les énergies kWh/kg, sinon utiliser la somme
    if energie_choice == 'Gaz (kWh/kg)' or energie_choice == 'Electricité (kWh/kg)':  
        df_filtered = df2.groupby([period_choice, 'Site'])[energie_choice].median().reset_index()  
    else:
        df_filtered = df2.groupby([period_choice, 'Site'])[energie_choice].sum().reset_index()  
else:
    df_filtered = df2[df2['Site'] == site_selection]

# Filtrage selon la période choisie
if period_choice == 'Année':
    start_year = st.sidebar.selectbox("Année de début", sorted(df2['Année'].unique()))
    end_year = st.sidebar.selectbox("Année de fin", sorted(df2['Année'].unique()))
    df_filtered = df_filtered[(df_filtered['Année'] >= start_year) & (df_filtered['Année'] <= end_year)]
elif period_choice == 'Mois':
    start_month = st.sidebar.selectbox("Mois de début", range(1, 13))
    end_month = st.sidebar.selectbox("Mois de fin", range(1, 13))
    df_filtered = df_filtered[(df_filtered['Mois'] >= start_month) & (df_filtered['Mois'] <= end_month)]
else:  # Filtrage par jour
    start_day = pd.to_datetime(st.sidebar.date_input("Jour de début", pd.to_datetime('2024-01-01')))
    end_day = pd.to_datetime(st.sidebar.date_input("Jour de fin", pd.to_datetime('2024-12-31')))
    df_filtered = df_filtered[(df_filtered['Date'] >= start_day) & (df_filtered['Date'] <= end_day)]

# Agrégation des données par energie
if energie_choice == 'Gaz (kWh/kg)' or energie_choice == 'Electricité (kWh/kg)':     
    energie_col = energie_choice  
    aggregation_method = 'median'  # Utilisation de la médiane pour ces énergies
elif energie_choice == 'Gaz (kWh)' or energie_choice == 'Electricité (kWh)':   
    energie_col = energie_choice  
    aggregation_method = 'sum'  
else:   
    energie_col = energie_choice  
    aggregation_method = 'sum'  

# Agrégation des données par période choisie
if period_choice == 'Année':
    if aggregation_method == 'median':
        df_grouped = df_filtered.groupby(['Année', 'Site'])[energie_col].median().reset_index()
    else:
        df_grouped = df_filtered.groupby(['Année', 'Site'])[energie_col].sum().reset_index()
elif period_choice == 'Mois':
    if aggregation_method == 'median':
        df_grouped = df_filtered.groupby(['Année-Mois', 'Site'])[energie_col].median().reset_index()
    else:
        df_grouped = df_filtered.groupby(['Année-Mois', 'Site'])[energie_col].sum().reset_index()
else:  # Agrégation par jour
    if aggregation_method == 'median':
        df_grouped = df_filtered.groupby(['Jour', 'Site'])[energie_col].median().reset_index()
    else:
        df_grouped = df_filtered.groupby(['Jour', 'Site'])[energie_col].sum().reset_index()

# Création du graphique avec Plotly
fig = go.Figure()

# Générer une palette de couleurs pour les sites
if site_selection == 'Global':
    colors = px.colors.qualitative.Set1  # Palette de couleurs distinctes
    color_map = {site: colors[i % len(colors)] for i, site in enumerate(df_grouped['Site'].unique())}
else:
    color_map = {'blue': 'blue'}  # Si un seul site est sélectionné

# Ajout des sous-graphes selon la période
for site in df_grouped['Site'].unique():
    site_data = df_grouped[df_grouped['Site'] == site]
    fig.add_trace(go.Bar(
        x=site_data[period_choice],
        y=site_data[energie_choice],
        name=site,
        marker=dict(color=color_map[site])  # Applique la couleur spécifique
    ))

# Mise à jour des axes et titres
fig.update_layout(
    barmode='group',  
    title=f'Consommation d\'énergie pour {site_selection}',
    xaxis_title='Période',
    yaxis_title=f'Consommation ({energie_choice})',
    legend_title="Site",
    xaxis=dict(type='category', categoryorder='category ascending')
)

# Affichage du graphique dans Streamlit
st.plotly_chart(fig)
st.write(df_grouped)