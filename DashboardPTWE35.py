import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st

# Chargement des données
df1 = pd.read_csv("All2_data.csv", sep=";")
df1['Site'] = df1['Site'].replace({'PTWE42 Andrézieux': 'PTWE42'})
df2 = df1[['Site', 'Année', 'Mois', 'Date', 'PE(kg)', 'Energie consommée (kWh)', 'KWh/Kg']].copy()

# Filtrage des données
st.sidebar.title("Filtrage des données")
sites = df2['Site'].unique()
site_selection = st.sidebar.selectbox('Choisissez un site', sites)

# Choisir l'énergie à afficher
energie_choice = st.sidebar.radio("Choisissez l'énergie", ['Energie consommée (kWh)', 'KWh/Kg'])

# Choisir la période de filtrage
period_choice = st.sidebar.radio("Sélectionner la période", ('Année', 'Mois', 'Jour'))

# Filtrage des données par site
df_filtered = df2[df2['Site'] == site_selection]

# Filtrage selon la période choisie
if period_choice == 'Année':
    start_year = st.sidebar.selectbox("Année de début", sorted(df2['Année'].unique()))
    end_year = st.sidebar.selectbox("Année de fin", sorted(df2['Année'].unique()))
    df_filtered = df2[(df2['Année'] >= start_year) & (df2['Année'] <= end_year) & (df2['Site'] == site_selection)]
elif period_choice == 'Mois':
    start_month = st.sidebar.selectbox("Mois de début", range(1, 13))
    end_month = st.sidebar.selectbox("Mois de fin", range(1, 13))
    df_filtered = df2[(df2['Mois'] >= start_month) & (df2['Mois'] <= end_month) & (df2['Site'] == site_selection)]
else:  # Filtrage par jour
    start_day = pd.to_datetime(st.sidebar.date_input("Jour de début", pd.to_datetime('2024-01-01')))
    end_day = pd.to_datetime(st.sidebar.date_input("Jour de fin", pd.to_datetime('2024-12-31')))
    df_filtered = df2[(df2['Date'] >= start_day) & (df2['Date'] <= end_day) & (df2['Site'] == site_selection)]

# Agrégation des données par période choisie
if energie_choice == 'Energie consommée (kWh)':  # Vérification de l'énergie choisie
    if period_choice == 'Année':  # Agrégation par année
        df_grouped = df_filtered.groupby(['Année', 'Site'])['Energie consommée (kWh)'].sum().reset_index()
    elif period_choice == 'Mois':  # Agrégation par mois
        df_grouped = df_filtered.groupby(['Année-Mois', 'Site'])['Energie consommée (kWh)'].sum().reset_index()
    else:  # Agrégation par jour
        df_grouped = df_filtered.groupby(['Jour', 'Site'])['Energie consommée (kWh)'].sum().reset_index()
else:  # Si une autre énergie est choisie, comme 'KWh/Kg'
    if period_choice == 'Année':  # Agrégation par année
        df_grouped = df_filtered.groupby(['Année', 'Site'])['KWh/Kg'].mean().reset_index()
    elif period_choice == 'Mois':  # Agrégation par mois
        df_grouped = df_filtered.groupby(['Année-Mois', 'Site'])['KWh/Kg'].mean().reset_index()
    else:  # Agrégation par jour
        df_grouped = df_filtered.groupby(['Jour', 'Site'])['KWh/Kg'].mean().reset_index()

# Création du graphique avec Plotly
fig = go.Figure()

# Ajout des sous-graphes selon la période
for site in df_grouped['Site'].unique():
    site_data = df_grouped[df_grouped['Site'] == site]
    if period_choice == 'Année':
        fig.add_trace(go.Bar(
            x=site_data['Année'],
            y=site_data[energie_choice],
            name=site,
            marker=dict(color='blue')
        ))
    elif period_choice == 'Mois':
        fig.add_trace(go.Bar(
            x=site_data['Année-Mois'],
            y=site_data[energie_choice],
            name=site,
            marker=dict(color='lightblue')
        ))
    else:  # Par jour
        fig.add_trace(go.Bar(
            x=site_data['Jour'],  # Utilisation de la date sans l'heure
            y=site_data[energie_choice],
            name=site,
            marker=dict(color='darkblue')
        ))

# Mise à jour des axes et titres
fig.update_layout(
    barmode='group',  # Utilisation de 'group' pour séparer les barres
    title=f'Consommation d\'énergie pour {site_selection}',
    xaxis_title='Période',
    yaxis_title=f'Consommation ({energie_choice})',
    legend_title="Site",
    xaxis=dict(type='category', categoryorder='category ascending')  # Trier l'axe X
)

# Affichage du graphique dans Streamlit
st.plotly_chart(fig)
