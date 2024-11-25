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

# Création de la colonne "Mois-Jour" (au lieu de "Mois-Année")
df2['Mois-Jour'] = df2['Mois'].astype(str) + '-' + df2['Jour'].astype(str).str.zfill(2)

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
    start_day = st.sidebar.date_input("Jour de début", pd.to_datetime('2024-01-01'))
    end_day = st.sidebar.date_input("Jour de fin", pd.to_datetime('2024-12-31'))
    df_filtered = df2[(df2['Horodate'] >= start_day) & (df2['Horodate'] <= end_day) & (df2['Site'] == site_selection)]

# Regroupement des données par "Année-Mois" et somme de la consommation
df_grouped = df_filtered.groupby(['Année-Mois', 'Site'])['Energie consommée (kWh)'].sum().reset_index()

# Ajouter la colonne 'Année' à df_grouped pour pouvoir l'utiliser comme 'color' dans Plotly
df_grouped['Année'] = df_grouped['Année-Mois'].str[:4].astype(int)

# Création du graphique avec Plotly
fig = px.bar(df_grouped,
              x='Année-Mois',
              y='Energie consommée (kWh)',
              color='Année',  # Utilisation de la colonne Année
              labels={'Année-Mois': 'Période', 'Energie consommée (kWh)': 'Consommation (kWh)'},
              title=f'Consommation d\'énergie pour {site_selection}')
fig.update_xaxes(type='category', categoryorder='category ascending')

# Regroupement des données par "Mois-Jour" et somme de la consommation
df_grouped2 = df_filtered.groupby(['Mois-Jour', 'Site'])['Energie consommée (kWh)'].sum().reset_index()

# Ajouter la colonne 'Mois' à df_grouped2 pour pouvoir l'utiliser comme 'color' dans Plotly
df_grouped2['Mois'] = df_grouped2['Mois-Jour'].str[:2].astype(int)

# Création du graphique avec Plotly pour "Mois-Jour"
fig2 = px.bar(df_grouped2,
              x='Mois-Jour',
              y='Energie consommée (kWh)',
              color='Mois',  # Utilisation de la colonne Mois
              labels={'Mois-Jour': 'Période', 'Energie consommée (kWh)': 'Consommation (kWh)'},
              title=f'Consommation d\'énergie pour {site_selection}')
fig2.update_xaxes(type='category', categoryorder='category ascending')

# Afficher le graphique dans Streamlit
st.plotly_chart(fig)
st.plotly_chart(fig2)

# Affichage des données filtrées sous-jacentes (facultatif)
st.write(df_filtered)