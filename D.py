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

# Filtrage par période
if period_choice == 'Année':
    start_year = st.sidebar.selectbox("Année de début", sorted(df_filtered['Année'].unique()))
    end_year = st.sidebar.selectbox("Année de fin", sorted(df_filtered['Année'].unique()))
    df_filtered = df_filtered[(df_filtered['Année'] >= start_year) & (df_filtered['Année'] <= end_year)]
elif period_choice == 'Mois':
    start_month = st.sidebar.selectbox("Mois de début", range(1, 13))
    end_month = st.sidebar.selectbox("Mois de fin", range(1, 13))
    df_filtered = df_filtered[(df_filtered['Mois'] >= start_month) & (df_filtered['Mois'] <= end_month)]
else:  # Filtrage par jour
    start_day = pd.to_datetime(st.sidebar.date_input("Jour de début", pd.to_datetime('2024-01-01')))
    end_day = pd.to_datetime(st.sidebar.date_input("Jour de fin", pd.to_datetime('2024-12-31')))
    df_filtered = df_filtered[(df_filtered['Date'] >= start_day) & (df_filtered['Date'] <= end_day)]

# Graphique
fig = go.Figure()

# Ajout des données au graphique
fig.add_trace(go.Bar(
    x=df_filtered['Date'] if period_choice == 'Jour' else df_filtered['Mois'] if period_choice == 'Mois' else df_filtered['Année'],
    y=df_filtered[energie_choice],
    name='Consommation d\'énergie',
    marker=dict(color='blue')
))

# Mise en forme du graphique
fig.update_layout(
    title=f'Consommation d\'énergie pour {site_selection}',
    xaxis_title='Période',
    yaxis_title=f'{energie_choice}',
    barmode='stack',
    xaxis=dict(type='category')
)

# Affichage du graphique
st.plotly_chart(fig)

# Affichage des données filtrées
st.write(df_filtered)