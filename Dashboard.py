import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
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
df2['Année-Mois'] = df2['Année'].astype(str) + '-' + df2['Mois'].astype(str).str.zfill(2)

# Filtrage des données
st.sidebar.title("Filtrage des données")
sites = df2['Site'].unique()
site_selection = st.sidebar.selectbox('Choisissez un site', sites)

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

# Agrégation des données par mois et année
df_grouped = df_filtered.groupby(['Année', 'Mois', 'Site'])['Energie consommée (kWh)'].sum().reset_index()

# Création du graphique avec Plotly
fig = go.Figure()

# Ajout des sous-graphes selon la période
for site in df_grouped['Site'].unique():
    site_data = df_grouped[df_grouped['Site'] == site]
    
    # Comparaison des mois entre deux années
    for mois in range(1, 13):  # Pour chaque mois de l'année
        # Données pour chaque année pour ce mois
        month_data = site_data[site_data['Mois'] == mois]
        
        # Ajouter une trace pour chaque mois
        for year in sorted(site_data['Année'].unique()):
            year_data = month_data[month_data['Année'] == year]
            fig.add_trace(go.Bar(
                x=[f"{year}-{mois}"],
                y=year_data['Energie consommée (kWh)'],
                name=f"{site} {year}-{mois}",
                marker=dict(color='green' if year == sorted(site_data['Année'].unique())[0] else 'blue')
            ))

# Mise à jour des axes et titres
fig.update_layout(
    barmode='group',
    title=f'Comparaison de la consommation d\'énergie pour {site_selection} (mois à mois)',
    xaxis_title='Période (Année-Mois)',
    yaxis_title='Consommation (kWh)',
    legend_title="Site - Mois",
    xaxis=dict(type='category')
)

# Affichage du graphique dans Streamlit
st.plotly_chart(fig)

# Affichage des données filtrées sous-jacentes (facultatif)
st.write(df_filtered)
