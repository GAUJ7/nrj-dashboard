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

# Calcul de la consommation par période
df2['Année'] = df2['Horodate'].dt.year
df2['Mois'] = df2['Horodate'].dt.month
df2['Jour'] = df2['Horodate'].dt.day

# Mappage des mois en texte
month_map = {
    1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril', 5: 'Mai', 6: 'Juin',
    7: 'Juillet', 8: 'Août', 9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
}
df2['Mois_texte'] = df2['Mois'].map(month_map)

# Sélection de la période manuellement (choisir une date de début et une date de fin)
start_date = st.date_input("Date de début", df2['Horodate'].min())
end_date = st.date_input("Date de fin", df2['Horodate'].max())

# Filtrer les données en fonction de la plage de dates
df_filtered = df2[(df2['Horodate'] >= pd.to_datetime(start_date)) & (df2['Horodate'] <= pd.to_datetime(end_date))]

# Sélecteur de période d'affichage (Jour, Mois, Année)
periode_selection = st.selectbox('Sélectionnez la période d\'affichage', ['Jour', 'Mois', 'Année'])

# Agrégation en fonction de la période sélectionnée
if periode_selection == 'Jour':
    df_agg = df_filtered.groupby(['Année', 'Mois_texte', 'Jour', 'Site'])['Energie consommée (kWh)'].sum().reset_index()
    x_axis = 'Jour'
    title = f'Consommation quotidienne par site'
elif periode_selection == 'Mois':
    df_agg = df_filtered.groupby(['Année', 'Mois_texte', 'Site'])['Energie consommée (kWh)'].sum().reset_index()
    x_axis = 'Mois_texte'
    title = f'Consommation mensuelle par site'
else:  # Année
    df_agg = df_filtered.groupby(['Année', 'Site'])['Energie consommée (kWh)'].sum().reset_index()
    x_axis = 'Année'
    title = f'Consommation annuelle par site'

# Choisir un site à afficher
sites = df_agg['Site'].unique()
site_selection = st.selectbox('Choisissez un site', sites)

# Filtrer les données en fonction du site sélectionné
df_filtered_site = df_agg[df_agg['Site'] == site_selection]

# Créer un graphique avec Plotly
fig = px.bar(df_filtered_site, x=x_axis, y='Energie consommée (kWh)',
             color='Année', barmode='group',
             labels={x_axis: x_axis, 'Energie consommée (kWh)': 'Consommation (kWh)'},
             title=title)

# Afficher le graphique interactif dans Streamlit
st.plotly_chart(fig)

# Afficher les données sous-jacentes (facultatif)
st.write(df_filtered_site)