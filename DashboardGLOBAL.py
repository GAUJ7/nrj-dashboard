import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import plotly.express as px  # Pour accéder à des palettes de couleurs

# Chargement des données
df2 = pd.read_csv("Global_streamlit.csv", sep=";")
df2['Site'] = df2['Site'].replace({'PTWE42 Andrézieux': 'PTWE42'})

# Assurer que la colonne 'Date' est bien au format datetime
df2['Date'] = pd.to_datetime(df2['Date'], errors='coerce')

# Extraire l'année, le mois et le jour
df2['Année'] = df2['Date'].dt.year
df2['Mois'] = df2['Date'].dt.month
df2['Jour'] = df2['Date'].dt.date
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

# Calcul des sommes de Gaz et Electricité selon la période choisie
df_gaz = df2.groupby([period_choice, 'Site'])['Gaz (kWh)'].sum().reset_index()
df_electricite = df2.groupby([period_choice, 'Site'])['Electricité (kWh)'].sum().reset_index()

# Calcul de la somme de PE (kg) par période et site
df_pe = df2.groupby([period_choice, 'Site'])['PE (kg)'].sum().reset_index()

# Fusionner df_gaz et df_electricite
df_merged_gaz_elec = pd.merge(df_gaz, df_electricite, on=[period_choice, 'Site'], suffixes=('_gaz', '_elec'))

# Fusionner le résultat avec df_pe
df_merged = pd.merge(df_merged_gaz_elec, df_pe, on=[period_choice, 'Site'], suffixes=('_gaz_elec', '_pe'))

# Appliquer la condition selon le choix d'énergie
if energie_choice == "Gaz (kWh/kg)":
    df_merged['Gaz (kWh/kg)'] = df_merged['Gaz (kWh)'] / df_merged['PE (kg)']
    df_final = df_merged[[period_choice, 'Site', 'Gaz (kWh/kg)']]
elif energie_choice == "Electricité (kWh/kg)":
    df_merged['Electricité (kWh/kg)'] = df_merged['Electricité (kWh)'] / df_merged['PE (kg)']
    df_final = df_merged[[period_choice, 'Site', 'Electricité (kWh/kg)']]

# Filtrage des données par site
if site_selection == 'Global':
    if energie_choice == 'Gaz (kWh/kg)' or energie_choice == 'Electricité (kWh/kg)':
        df_filtered = df_final
    else:
        df_filtered = df2.groupby([period_choice, 'Site'])[energie_choice].sum().reset_index()
else:
    df_filtered = df2[df2['Site'] == site_selection]
    df_filtered2 = df_final[df_final['Site'] == site_selection]
 
# Filtrage selon la période choisie
if period_choice == 'Année':
    start_year = st.sidebar.selectbox("Année de début", sorted(df2['Année'].unique()))
    end_year = st.sidebar.selectbox("Année de fin", sorted(df2['Année'].unique()))
    df_filtered = df_filtered[(df_filtered['Année'] >= start_year) & (df_filtered['Année'] <= end_year)]
    df_filtered2 = df_filtered2[(df_filtered2['Année'] >= start_year) & (df_filtered2['Année'] <= end_year)]
elif period_choice == 'Mois':
    start_month = st.sidebar.selectbox("Mois de début", range(1, 13))
    end_month = st.sidebar.selectbox("Mois de fin", range(1, 13))
    df_filtered = df_filtered[(df_filtered['Mois'] >= start_month) & (df_filtered['Mois'] <= end_month)]
    df_filtered2 = df_filtered2[(df_filtered2['Mois'] >= start_month) & (df_filtered2['Mois'] <= end_month)]
else:
    start_day = pd.to_datetime(st.sidebar.date_input("Jour de début", pd.to_datetime('2024-01-01')))
    end_day = pd.to_datetime(st.sidebar.date_input("Jour de fin", pd.to_datetime('2024-12-31')))
    df_filtered = df_filtered[(df_filtered['Date'] >= start_day) & (df_filtered['Date'] <= end_day)]
    df_filtered2 = df_filtered2[(df_filtered2['Date'] >= start_day) & (df_filtered2['Date'] <= end_day)]

# Agrégation des données
if energie_choice == 'Gaz (kWh/kg)' or energie_choice == 'Electricité (kWh/kg)':
    energie_col = df_filtered2
    aggregation_method = 'median'
elif energie_choice == 'Gaz (kWh)' or energie_choice == 'Electricité (kWh)':
    energie_col = energie_choice
    aggregation_method = 'sum'
else:
    energie_col = energie_choice
    aggregation_method = 'sum'

if period_choice == 'Année':
    if aggregation_method == 'median':
        df_grouped = df_filtered2
    else:
        df_grouped = df_filtered.groupby(['Année', 'Site'])[energie_col].sum().reset_index()
elif period_choice == 'Mois':
    if aggregation_method == 'median':
        df_grouped = df_filtered2
    else:
        df_grouped = df_filtered.groupby(['Année-Mois', 'Site'])[energie_col].sum().reset_index()
else:
    if aggregation_method == 'median':
        df_grouped = df_final
    else:
        df_grouped = df_filtered.groupby(['Jour', 'Site'])[energie_col].sum().reset_index()

# Créer une palette de couleurs distinctes
color_palette = px.colors.qualitative.Safe  # Palette de couleurs pré-définie

# Création du graphique avec Plotly
fig = go.Figure()

# Ajouter les sous-graphes avec des couleurs différentes pour chaque site
for idx, site in enumerate(df_grouped['Site'].unique()):
    site_data = df_grouped[df_grouped['Site'] == site]
    color = color_palette[idx % len(color_palette)]  # Assurer une couleur unique pour chaque site
    if period_choice == 'Année':
        fig.add_trace(go.Bar(
            x=site_data['Année'],
            y=site_data[energie_choice],
            name=site,
            marker=dict(color=color)
        ))
    elif period_choice == 'Mois':
        fig.add_trace(go.Bar(
            x=site_data['Année-Mois'],
            y=site_data[energie_choice],
            name=site,
            marker=dict(color=color)
        ))
    else:
        fig.add_trace(go.Bar(
            x=site_data['Jour'],
            y=site_data[energie_choice],
            name=site,
            marker=dict(color=color)
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