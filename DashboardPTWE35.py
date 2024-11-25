import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

# Chargement des données
df1 = pd.read_csv("All2_data.csv", sep=";")

# Sélection des colonnes et conversion
df2 = df1[['Site', 'Date', 'PE(kg)', 'Energie consommée (kWh)', 'KWh/Kg']].copy()
df2['Horodate'] = pd.to_datetime(df2['Date'], format='%d/%m/%Y')

df1['Site'] = df1['Site'].replace({'PTWE42 Andrézieux': 'PTWE42'})

# Création de nouvelles colonnes pour l'année, le mois et le jour
df2['Année'] = df2['Horodate'].dt.year  # Assurer que l'année soit correctement extraite
df2['Mois'] = df2['Horodate'].dt.month
df2['Jour'] = df2['Horodate'].dt.date  # Conversion pour ne garder que la date
df2['Mois-Abrege'] = df2['Horodate'].dt.strftime('%b')  # Mois abrégés (ex: Jan, Feb, Mar, etc.)
df2['Année-Mois'] = df2['Année'].astype(str) + '-' + df2['Mois-Abrege']  # Format Année-Mois (ex: 2024-Jan)

# Filtrage des données
st.sidebar.title("Filtrage des données")
sites = df2['Site'].unique()
site_selection = st.sidebar.selectbox('Choisissez un site', sites)

# Choisir l'énergie à afficher
energie_choice = st.sidebar.selectbox("Choisissez l'énergie", ['Energie consommée (kWh)', 'KWh/Kg'])

# Choisir la période de filtrage
period_choice = st.sidebar.radio("Sélectionner la période", ('Année', 'Mois', 'Jour'))



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
    df_filtered = df2[(df2['Horodate'] >= start_day) & (df2['Horodate'] <= end_day) & (df2['Site'] == site_selection)]

# Agrégation des données par période choisie
if energie_choice == 'Energie consommée (kWh)':
    if period_choice == 'Année':
        df_grouped = df_filtered.groupby(['Année', 'Site'])['Energie consommée (kWh)'].sum().reset_index()
    elif period_choice == 'Mois':
        df_grouped = df_filtered.groupby(['Année-Mois', 'Site'])['Energie consommée (kWh)'].sum().reset_index()
    else:  # Agrégation par jour
        df_grouped = df_filtered.groupby(['Jour', 'Site'])['Energie consommée (kWh)'].sum().reset_index()
else:  # Si une autre énergie est choisie, comme 'KWh/Kg'
    if period_choice == 'Année':
        df_grouped = df_filtered.groupby(['Année', 'Site'])['KWh/Kg'].mean().reset_index()
    elif period_choice == 'Mois':
        df_grouped = df_filtered.groupby(['Année-Mois', 'Site'])['KWh/Kg'].mean().reset_index()
    else:  # Agrégation par jour
        df_grouped = df_filtered.groupby(['Jour', 'Site'])['KWh/Kg'].mean().reset_index()

# Création du graphique avec Matplotlib
fig, ax = plt.subplots(figsize=(10, 6))

# Ajout des sous-graphes selon la période
for site in df_grouped['Site'].unique():
    site_data = df_grouped[df_grouped['Site'] == site]
    if period_choice == 'Année':
        ax.bar(site_data['Année'], site_data[energie_choice], label=site)
    elif period_choice == 'Mois':
        ax.bar(site_data['Année-Mois'], site_data[energie_choice], label=site)
    else:  # Par jour
        ax.bar(site_data['Jour'], site_data[energie_choice], label=site)

# Mise à jour des axes et titres
ax.set_title(f'Consommation d\'énergie pour {site_selection}')
ax.set_xlabel('Période')
ax.set_ylabel(f'Consommation ({energie_choice})')
ax.legend(title="Site")

# Affichage du graphique dans Streamlit
st.pyplot(fig)
