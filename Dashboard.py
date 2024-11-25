import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

# Chargement des données
df = pd.read_excel("GRDF 20241118.xlsx")

# Sélection et modification des colonnes nécessaires
df2 = df[['N° PCE', 'Date de relevé', 'Energie consommée (kWh)']].copy()
df2['Horodate'] = pd.to_datetime(df2['Date de relevé'], format='%d/%m/%Y')

# Remplacement des identifiants par des noms de sites
mapping = {
    "GI153881": 'PTWE89',
    "GI087131": 'PTWE35',
    "GI060319": 'PTWE42 Andrézieux',
}
df2['Site'] = df2['N° PCE'].map(mapping)
df2 = df2.drop(columns=['N° PCE'])

# Création de nouvelles colonnes pour l'année, le mois et le jour
df2['Année'] = df2['Horodate'].dt.year
df2['Mois'] = df2['Horodate'].dt.month
df2['Jour'] = df2['Horodate'].dt.day

# Création des colonnes "Année-Mois" et "Mois-Jour"
df2['Année-Mois'] = df2['Année'].astype(str) + '-' + df2['Mois'].astype(str).str.zfill(2)
df2['Mois-Jour'] = df2['Mois'].astype(str).str.zfill(2) + '-' + df2['Jour'].astype(str).str.zfill(2)

# Filtrage des données
st.sidebar.title("Filtrage des données")
sites = df2['Site'].unique()
site_selection = st.sidebar.selectbox('Choisissez un site', sites)

# Choisir la période de filtrage
period_choice = st.sidebar.radio("Sélectionner la période", ('Année', 'Mois', 'Jour', 'Mois-Jour'))

if period_choice == 'Année':
    start_year = st.sidebar.selectbox("Année de début", sorted(df2['Année'].unique()))
    end_year = st.sidebar.selectbox("Année de fin", sorted(df2['Année'].unique()))
    df_filtered = df2[(df2['Année'] >= start_year) & (df2['Année'] <= end_year) & (df2['Site'] == site_selection)]
elif period_choice == 'Mois':
    start_month = st.sidebar.selectbox("Mois de début", range(1, 13))
    end_month = st.sidebar.selectbox("Mois de fin", range(1, 13))
    df_filtered = df2[(df2['Mois'] >= start_month) & (df2['Mois'] <= end_month) & (df2['Site'] == site_selection)]
elif period_choice == 'Mois-Jour':  # Filtrage par Mois-Jour
    start_month_day = st.sidebar.selectbox("Date de début (Mois-Jour)", df2['Mois-Jour'].unique())
    end_month_day = st.sidebar.selectbox("Date de fin (Mois-Jour)", df2['Mois-Jour'].unique())
    df_filtered = df2[(df2['Mois-Jour'] >= start_month_day) & (df2['Mois-Jour'] <= end_month_day) & (df2['Site'] == site_selection)]
else:  # Filtrage par jour
    start_day = st.sidebar.date_input("Jour de début", pd.to_datetime('2024-01-01'))
    end_day = st.sidebar.date_input("Jour de fin", pd.to_datetime('2024-12-31'))
    df_filtered = df2[(df2['Horodate'] >= start_day) & (df2['Horodate'] <= end_day) & (df2['Site'] == site_selection)]

# Groupement des données par la période choisie
if period_choice == 'Mois-Jour':
    df_grouped = df_filtered.groupby(['Mois-Jour', 'Site'])['Energie consommée (kWh)'].sum().reset_index()
else:
    df_grouped = df_filtered.groupby(['Année-Mois', 'Site'])['Energie consommée (kWh)'].sum().reset_index()

# Ajouter la colonne 'Année' pour la couleur dans Plotly
df_grouped['Année'] = df_grouped['Année-Mois'].str[:4].astype(int) if period_choice != 'Mois-Jour' else df_grouped['Mois-Jour']

# Création du graphique avec Plotly
fig = px.bar(df_grouped,
              x='Année-Mois' if period_choice != 'Mois-Jour' else 'Mois-Jour',
              y='Energie consommée (kWh)',
              color='Année',  # Utilisation de la colonne Année
              labels={'Année-Mois': 'Période', 'Energie consommée (kWh)': 'Consommation (kWh)'},
              title=f'Consommation d\'énergie pour {site_selection}')
fig.update_xaxes(type='category', categoryorder='category ascending')

# Affichage du graphique dans Streamlit
st.plotly_chart(fig)

# Affichage des données filtrées sous-jacentes (facultatif)
st.write(df_filtered)