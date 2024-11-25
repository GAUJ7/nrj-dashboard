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

# Création de la colonne "Année-Mois"
df2['Année-Mois'] = df2['Année'].astype(str) + '-' + df2['Mois'].astype(str).str.zfill(2)

# Filtrage des données
st.sidebar.title("Filtrage des données")
sites = df2['Site'].unique()
site_selection = st.sidebar.selectbox('Choisissez un site', sites)

# Choisir la période de filtrage
period_choice = st.sidebar.radio("Sélectionner la période", ('Année', 'Mois', 'Jour'))
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
    df_filtered = df2[(df2['Horodate'] >= start_day) & (df2['Horodate'] <= end_day) & (df2['Site'] == site_selection)]

# Agrégation des données par jour
df_grouped = df_filtered.groupby(['Année', 'Mois', 'Jour', 'Site'])['Energie consommée (kWh)'].sum().reset_index()

# Création de la colonne 'Mois-Nom' pour afficher le mois
df_grouped['Mois-Nom'] = df_grouped['Mois'].apply(lambda x: pd.to_datetime(f"2024-{x:02d}-01").strftime('%B'))

# Créer une colonne combinée "Jour-Mois" pour l'axe x
df_grouped['Jour-Mois'] = df_grouped['Jour'].astype(str) + '-' + df_grouped['Mois-Nom']

# Création du graphique avec Plotly
fig = px.bar(df_grouped,
             x='Jour-Mois',  # Utiliser la colonne combinée "Jour-Mois"
             y='Energie consommée (kWh)',
             color='Année',
             labels={'Jour-Mois': 'Jour-Mois', 'Energie consommée (kWh)': 'Consommation (kWh)', 'Mois-Nom': 'Mois'},
             title=f'Consommation d\'énergie pour {site_selection}')

# Mise à jour de l'axe des x pour qu'il soit catégorisé
fig.update_xaxes(type='category', categoryorder='category ascending')

# Afficher le graphique dans Streamlit
st.plotly_chart(fig)

# Affichage des données filtrées sous-jacentes (facultatif)
st.write(df_filtered)