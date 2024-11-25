import pandas as pd
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
    "GI060319": 'PTWE42',
}
df2['Site'] = df2['N° PCE'].map(mapping)
df2 = df2.drop(columns=['N° PCE'])

# Création de nouvelles colonnes pour l'année, le mois et le jour
df2['Année'] = df2['Horodate'].dt.year
df2['Mois'] = df2['Horodate'].dt.month
df2['Jour'] = df2['Horodate'].dt.day
df2['Mois'] = df2['Horodate'].dt.strftime('%b')  # Mois abrégés
df2['Année-Mois'] = df2['Année'].astype(str) + '-' + df2['Mois']  # Format Année-Mois

# Filtrage des données
st.sidebar.title("Filtrage des données")
sites = df2['Site'].unique()
site_selection = st.sidebar.selectbox('Choisissez un site', sites)

# Choisir la période de filtrage
period_choice = st.sidebar.radio("Sélectionner la période", ('Année', 'Mois', 'Jour'))

months = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]

# Filtrage selon la période choisie
if period_choice == 'Année':
    start_year = st.sidebar.selectbox("Année de début", sorted(df2['Année'].unique()))
    end_year = st.sidebar.selectbox("Année de fin", sorted(df2['Année'].unique()))
    df_filtered = df2[(df2['Année'] >= start_year) & (df2['Année'] <= end_year) & (df2['Site'] == site_selection)]
elif period_choice == 'Mois':
    start_month = st.sidebar.selectbox("Mois de début", months, index=0)
    end_month = st.sidebar.selectbox("Mois de fin", months, index=11)  # Index de "Décembre"
    df_filtered = df2[(df2['Mois'] >= start_month) & (df2['Mois'] <= end_month) & (df2['Site'] == site_selection)]
else:  # Filtrage par jour
    start_day = pd.to_datetime(st.sidebar.date_input("Jour de début", pd.to_datetime('2024-01-01')))
    end_day = pd.to_datetime(st.sidebar.date_input("Jour de fin", pd.to_datetime('2024-12-31')))
    df_filtered = df2[(df2['Horodate'] >= start_day) & (df2['Horodate'] <= end_day) & (df2['Site'] == site_selection)]

# Agrégation des données par période choisie
if period_choice == 'Année':
    df_grouped = df_filtered.groupby(['Année', 'Site'])['Energie consommée (kWh)'].sum().reset_index()
elif period_choice == 'Mois':
    df_grouped = df_filtered.groupby(['Année-Mois', 'Site'])['Energie consommée (kWh)'].sum().reset_index()
else:  # Par jour
    df_grouped = df_filtered.groupby(['Horodate', 'Site'])['Energie consommée (kWh)'].sum().reset_index()

# Création des graphiques distincts
if period_choice == 'Année':
    fig = go.Figure()
    for site in df_grouped['Site'].unique():
        site_data = df_grouped[df_grouped['Site'] == site]
        fig.add_trace(go.Bar(
            x=site_data['Année'],
            y=site_data['Energie consommée (kWh)'],
            name=site,
            marker=dict(color='blue')
        ))
    fig.update_layout(
        barmode='stack',
        title=f'Consommation d\'énergie pour {site_selection} (Année)',
        xaxis_title='Année',
        yaxis_title='Consommation (kWh)',
        legend_title="Site"
    )
    st.plotly_chart(fig)

elif period_choice == 'Mois':
    fig = go.Figure()
    for site in df_grouped['Site'].unique():
        site_data = df_grouped[df_grouped['Site'] == site]
        fig.add_trace(go.Bar(
            x=site_data['Année-Mois'],
            y=site_data['Energie consommée (kWh)'],
            name=site,
            marker=dict(color='lightblue')
        ))
    fig.update_layout(
        barmode='stack',
        title=f'Consommation d\'énergie pour {site_selection} (Mois)',
        xaxis_title='Mois',
        yaxis_title='Consommation (kWh)',
        legend_title="Site"
    )
    st.plotly_chart(fig)

else:  # Par jour
    fig = go.Figure()
    for site in df_grouped['Site'].unique():
        site_data = df_grouped[df_grouped['Site'] == site]
        fig.add_trace(go.Bar(
            x=site_data['Horodate'],
            y=site_data['Energie consommée (kWh)'],
            name=site,
            marker=dict(color='darkblue')
        ))
    fig.update_layout(
        barmode='stack',
        title=f'Consommation d\'énergie pour {site_selection} (Jour)',
        xaxis_title='Jour',
        yaxis_title='Consommation (kWh)',
        legend_title="Site"
    )
    st.plotly_chart(fig)

# Affichage des données filtrées sous-jacentes
st.write(df_filtered)


