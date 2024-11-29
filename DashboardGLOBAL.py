import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import plotly.express as px  # Pour accéder à des palettes de couleurs

# Active le mode large par défaut
st.set_page_config(layout="wide")

# Chargement des données
df2 = pd.read_csv("20241127 Global_streamlit.csv", sep=";")

# Assurer que la colonne 'Date' est bien au format datetime
df2['Date'] = pd.to_datetime(df2['Date'], errors='coerce', dayfirst=True)

# Extraire l'année, le mois et le jour
df2['Année'] = df2['Date'].dt.year
df2['Mois'] = df2['Date'].dt.month
df2['Jour'] = df2['Date'].dt.date
df2['Jour'] = pd.to_datetime(df2['Jour'], errors='coerce', dayfirst=True)
df2['Mois-Abrege'] = df2['Date'].dt.strftime('%b')  # Mois abrégés (ex: Jan, Feb, Mar, etc.)
df2['Mois'] = df2['Année'] * 100 + df2['Mois']
df2['Semaine'] = df2['Année'] * 100 + df2['Date'].dt.isocalendar().week
df2['Semaine_Formate'] = df2['Semaine'].apply(lambda x: f"S{int(str(x)[-2:]):02d} {str(x)[:4]}")
df2['Mois_Formate'] = df2['Mois'].astype(str).str[:4] + '-' + df2['Mois'].astype(str).str[4:]
df2 = df2[df2['Année'].isin([2023, 2024])]

# Charger l'image et afficher en haut à gauche
image = "PT.jpg"  # Remplacez ce chemin par le chemin réel de votre image
st.image(image)

# Filtrage des données dans Streamlit
st.sidebar.title("Filtrage des données")
sites = df2['Site'].unique()
site_selection = st.sidebar.selectbox('Choisissez un site', ['Global'] + list(sites))

# Choisir l'énergie à afficher
energie_choice = st.sidebar.radio("Choisissez l'énergie", ['Gaz (kWh/kg)', 'Electricité (kWh/kg)', 'Gaz (kWh)', 'Electricité (kWh)', 'PE (kg)'])

# Choisir la période de filtrage
period_choice = st.sidebar.radio("Sélectionner la période", ('Année', 'Mois','Semaine','Jour', ))

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
    # Si l'énergie choisie est 'Gaz (kWh/kg)' ou 'Electricité (kWh/kg)', utiliser df_final
    if energie_choice == 'Gaz (kWh/kg)' or energie_choice == 'Electricité (kWh/kg)':
        df_filtered = df_final
    else:
        # Sinon, grouper df2 par période et site, et sommer selon l'énergie choisie
        df_filtered = df2.groupby([period_choice, 'Site'])[energie_choice].sum().reset_index()

elif energie_choice == 'Gaz (kWh/kg)' or energie_choice == 'Electricité (kWh/kg)':
    # Si l'énergie choisie est 'Gaz (kWh/kg)' ou 'Electricité (kWh/kg)', filtrer df_final selon le site sélectionné
    df_filtered = df_final[df_final['Site'] == site_selection]
else:
    # Sinon, filtrer df2 selon le site sélectionné
    df_filtered = df2[df2['Site'] == site_selection]
 
# Filtrage selon la période choisie
if period_choice == 'Année':
    start_year = st.sidebar.selectbox("Année de début", sorted(df2['Année'].unique()))
    end_year = st.sidebar.selectbox("Année de fin", sorted(df2['Année'].unique()))
    df_filtered = df_filtered[(df_filtered['Année'] >= start_year) & (df_filtered['Année'] <= end_year)]
elif period_choice == 'Mois':
    # Choisir l'année et le mois de début et de fin
    start_year_month = st.sidebar.selectbox("Sélectionner le mois de début", sorted(df2['Mois_Formate'].unique()))
    end_year_month = st.sidebar.selectbox("Sélectionner le mois de fin", sorted(df2['Mois_Formate'].unique()))
    # Convertir la valeur sélectionnée en format d'origine (YYYYMM)
    start_year_month_raw = int(start_year_month.replace('-', ''))
    end_year_month_raw = int(end_year_month.replace('-', ''))
    df_filtered = df_filtered[(df_filtered['Mois'] >= start_year_month_raw) & (df_filtered['Mois'] <= end_year_month_raw)]
elif period_choice == 'Semaine':
    start_week = st.sidebar.selectbox("Sélectionner la semaine de début", sorted(df2['Semaine_Formate'].unique(), key=lambda x: (int(x.split()[1]), int(x.split()[0][1:]))))
    end_week = st.sidebar.selectbox("Sélectionner la semaine de fin", sorted(df2['Semaine_Formate'].unique(), key=lambda x: (int(x.split()[1]), int(x.split()[0][1:]))))
    start_week_raw = int(start_week.split()[1]) * 100 + int(start_week.split()[0][1:])
    end_week_raw = int(end_week.split()[1]) * 100 + int(end_week.split()[0][1:])

    df_filtered = df_filtered[(df_filtered['Semaine'] >= start_week_raw) & (df_filtered['Semaine'] <= end_week_raw)]
else:
    start_day = pd.to_datetime(st.sidebar.date_input("Jour de début", pd.to_datetime('2024-01-01')))
    end_day = pd.to_datetime(st.sidebar.date_input("Jour de fin", pd.to_datetime('2024-12-31')))
    df_filtered = df_filtered[(df_filtered['Jour'] >= start_day) & (df_filtered['Jour'] <= end_day)]

# Agrégation des données
if energie_choice == 'Gaz (kWh/kg)' or energie_choice == 'Electricité (kWh/kg)':
    energie_col = df_filtered
    aggregation_method = 'median'
elif energie_choice == 'Gaz (kWh)' or energie_choice == 'Electricité (kWh)':
    energie_col = energie_choice
    aggregation_method = 'sum'
else:
    energie_col = energie_choice
    aggregation_method = 'sum'

if period_choice == 'Année':
    if aggregation_method == 'median':
        df_grouped = df_filtered
    else:
        df_grouped = df_filtered.groupby(['Année', 'Site'])[energie_col].sum().reset_index()
elif period_choice == 'Mois':
    if aggregation_method == 'median':
        df_grouped = df_filtered
    else:
        df_grouped = df_filtered.groupby(['Mois', 'Site'])[energie_col].sum().reset_index()
elif period_choice == 'Semaine':  # Ajout de la condition pour la semaine
    if aggregation_method == 'median':
        df_grouped = df_filtered
    else:
        df_grouped = df_filtered.groupby(['Semaine', 'Site'])[energie_col].sum().reset_index()
else:
    if aggregation_method == 'median':
        df_grouped = df_filtered
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

        # Mise en forme de la semaine pour afficher mois et année (ex : 202301 -> Janvier 2023)

        site_data['Mois'] = site_data['Mois'].apply(
            lambda x: f"{pd.to_datetime(str(x), format='%Y%m').strftime('%B %Y')}" if period_choice == 'Mois' else x
        )

        fig.add_trace(go.Bar(
            x=site_data['Mois'],
            y=site_data[energie_choice],
            name=site,
            marker=dict(color=color)
        ))
    elif period_choice == 'Semaine':
        site_data['Semaine'] = site_data['Semaine'].apply(
            lambda x: f"S{int(str(x)[-2:]):02d} {str(x)[:4]}" if period_choice == 'Semaine' else x
        )
        
        fig.add_trace(go.Bar(
            x=site_data['Semaine'],
            y=site_data[energie_choice],
            name=site,
            marker=dict(color=color)
        ))
    else:
        if energie_choice == 'Gaz (kWh/kg)':
            site_data = site_data[site_data[energie_choice] < 100]

        if energie_choice == 'Electricité (kWh/kg)':
            site_data = site_data[site_data[energie_choice] < 15]

        site_data['Jour'] = site_data['Jour'].apply(
            lambda x: f"{str(x)[:10]}" if period_choice == 'Jour' else x
        )
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
    title_font=dict(size=24),  # Taille du titre
    xaxis_title_font=dict(size=18),  # Taille du titre de l'axe X
    xaxis=dict(
        color='white',  # Change la couleur des axes X en blanc
        type='category',
        categoryorder='category ascending',
        tickfont=dict(size=16),  # Taille des labels des ticks de l'axe X
        linecolor='white'  # Change la couleur de l'axe Y en blanc
        
    ),
    yaxis_title=f'Consommation ({energie_choice})',
    yaxis_title_font=dict(size=18),  # Taille du titre de l'axe Y
    yaxis=dict(
        color='white',  # Change la couleur des axes Y en blanc
        tickfont=dict(size=16),  # Taille des labels des ticks de l'axe Y
        showgrid=True,  # Afficher la grille
        gridcolor='white',  # Change la couleur de la grille en blan
        zerolinecolor='white'  # Change la couleur de la ligne zéro
    ),
    legend_title="Site",
    height=500,  # Hauteur du graphique
    width=2000,  # Largeur du graphique

)

# Affichage du graphique dans Streamlit
if period_choice in df_grouped.columns:
    df_grouped[period_choice] = df_grouped[period_choice].apply(
        lambda x: f"{pd.to_datetime(str(x), format='%Y%m').strftime('%B %Y')}" if period_choice == 'Mois' else
                  f"{x:,.0f}".replace(',', '') if period_choice == 'Année' else
                  f"S{int(str(x)[-2:]):02d} {str(x)[:4]}" if period_choice == 'Semaine' else
                  f"{str(x)[:10]}" if period_choice == 'Jour' else x
                  

)
if energie_choice in df_grouped.columns:
    df_grouped[energie_choice] = df_grouped[energie_choice].apply(
        lambda x: "" if (x <= 0 or pd.isna(x) or x == float('inf') or x == float('-inf'))
                  else f"{x:,.0f}".replace(',', '') if energie_choice in ['Gaz (kWh)', 'Electricité (kWh)', 'PE (kg)'] 
                  else f"{x:,.2f}".replace(',', '')
    )
st.plotly_chart(fig)
st.write(df_grouped)

