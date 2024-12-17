import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import plotly.express as px  # Pour accéder à des palettes de couleurs
import toml
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="Tableau", layout="wide")

# Fonction pour charger les informations d'authentification
# Fonction pour charger les informations d'authentification
def load_config():
    config = toml.load('.streamlit/config.toml')
    return config['auth']['password']

# Fonction de vérification du mot de passe
def check_password(correct_password):
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True  # L'utilisateur est déjà authentifié, ne rien demander

    password = st.text_input("Mot de passe", type="password")
    
    if password == correct_password:
        st.session_state.authenticated = True
        return True  # Authentification réussie
    elif password:
        st.error("Mot de passe incorrect.")
    
    return False

# Fonction principale
def main():
    # N'afficher le titre que si l'utilisateur n'est pas encore authentifié
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.title("Application Sécurisée")
    
    correct_password = load_config()

    # Vérification de l'authentification
    if not check_password(correct_password):
        st.stop()  # Arrêter l'exécution si l'authentification échoue


if __name__ == "__main__":
    main()

# Chargement des données
df2 = pd.read_csv("20241209 Machine_streamlit.csv", sep=";")
df2 = df2[df2['Machine'] != 'F4B,']
# Assurer que la colonne 'Date' est bien au format datetime
#df2['Date'] = pd.to_datetime(df2['Date'], errors='coerce', dayfirst=True)

# Extraire l'année, le mois et le jour
#df2['Année'] = df2['Année'].dt.year
#df2['Mois'] = df2['Mois'].dt.month
#df2['Semaine'] = df2['Semaine'].dt.isocalendar().week
#df2['Jour'] = df2['Date'].dt.date
#df2['Jour'] = pd.to_datetime(df2['Jour'], errors='coerce', dayfirst=True)
df2['Année'] = df2['Année'].astype(int)
df2['Mois'] = df2['Mois'].astype(int)
df2['Mois-Abrege'] = pd.to_datetime(df2['Mois'], format='%m').dt.strftime('%b')
df2['Mois'] = df2['Année'] * 100 + df2['Mois']
df2['Semaine'] = df2['Année'] * 100 + df2['Semaine']
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

# Filtrage des machines selon le site sélectionné
if site_selection != "Global":
    machines_site = df2[df2['Site'] == site_selection]['Machine'].unique()
    machine_selection = st.sidebar.selectbox('Choisissez une Machine', ['Global'] + list(machines_site))
else:
    machine_selection = "Global"  # Ou aucune sélection de machine si le site est global

# Choisir l'indicateur à afficher
energie_choice = st.sidebar.radio("Choisissez l'indicateur", ['Gaz (kWh/kg)','PE (kg)', 'Prédiction Gaz (kwh/kg)'])

# Choisir la période de filtrage
period_choice = st.sidebar.radio("Sélectionner la période", ('Année', 'Mois', 'Semaine'))

# Calcul des sommes de Gaz et Electricité selon la période choisie
df_gaz = df2[df2['PE (kg)'] > 0]
df_gaz = df_gaz.groupby([period_choice,'Machine', 'Site'])['Gaz (kWh)'].sum().reset_index()
#df_electricite = df2.groupby([period_choice, 'Site'])['Electricité (kWh)'].sum().reset_index()


# Filtrer les lignes où la valeur de 'Gaz (kWh)' est supérieure à 0
df_pe = df2[df2['Gaz (kWh)'] > 0]
# Calcul de la somme de PE (kg) par période et site
df_pe = df_pe.groupby([period_choice,'Machine', 'Site'])['PE (kg)'].sum().reset_index()

# Fusionner df_gaz et df_electricite
#df_merged_gaz_elec = pd.merge(df_gaz, df_electricite, on=[period_choice, 'Site'], suffixes=('_gaz', '_elec'))

# Fusionner le résultat avec df_pe
if energie_choice == 'Gaz (kWh/kg)':
    df_merged = pd.merge(df_gaz, df_pe, on=[period_choice,'Machine', 'Site'], suffixes=('_gaz_elec', '_pe'))
    df_merged = df_merged[(df_merged['Machine'] == 'M2') | (df_merged['Machine'] == 'R2') | (df_merged['Machine'] == 'F4B') | (df_merged['Machine'] == 'Rock6')]
    df_merged['Gaz (kWh/kg)'] = df_merged['Gaz (kWh)'] / df_merged['PE (kg)']
    df_final = df_merged[[period_choice, 'Site','Machine', 'Gaz (kWh/kg)']]

elif energie_choice == 'Prédiction Gaz (kwh/kg)':
    df_merged = pd.merge(df_gaz, df_pe, on=[period_choice,'Machine', 'Site'], suffixes=('_gaz_elec', '_pe'))
    df_merged = df_merged[(df_merged['Machine'] == 'Rock6')]
    df_merged['Gaz (kWh/kg)'] = df_merged['Gaz (kWh)'] / df_merged['PE (kg)']
    df_final = df_merged[[period_choice, 'Site','Machine', 'Gaz (kWh/kg)','PE (kg)']]

# Filtrage des données par site
if site_selection == 'Global':
    if energie_choice == 'Gaz (kWh/kg)':
        df_filtered = df_final
    elif energie_choice == 'Prédiction Gaz (kwh/kg)':
        df_filtered = df_final
    else:
        # Si le site est 'Global', on groupe df2 par période et machine et on somme selon l'énergie choisie
        df_filtered = df2.groupby([period_choice, 'Machine'])[energie_choice].sum().reset_index()
else:
    # Sinon, on filtre les données selon le site sélectionné
    if machine_selection == 'Global':
        if energie_choice == 'Gaz (kWh/kg)':
            df_filtered = df_final[df_final['Site'] == site_selection]
        elif energie_choice == 'Prédiction Gaz (kwh/kg)':
            df_filtered = df_final[df_final['Site'] == site_selection]
        else:
            df_filtered = df2[df2['Site'] == site_selection]
            df_filtered = df_filtered.groupby([period_choice, 'Machine'])[energie_choice].sum().reset_index()
            # Si l'option 'Global' est choisie pour la machine, on groupe par période, site, et machine
    else:
        if energie_choice == 'Gaz (kWh/kg)':
            df_filtered = df_final[(df_final['Site'] == site_selection) & (df_final['Machine'] == machine_selection)]
        elif energie_choice == 'Prédiction Gaz (kwh/kg)':
            df_filtered = df_final[(df_final['Site'] == site_selection) & (df_final['Machine'] == machine_selection)]
        else:
            # Si une machine spécifique est choisie, on filtre les données pour cette machine
            df_filtered = df2[(df2['Site'] == site_selection) & (df2['Machine'] == machine_selection)]
 
# Filtrage selon la période choisie
if period_choice == 'Année':
    start_year = st.sidebar.selectbox("Année de début", sorted(df2['Année'].unique()),index=1)
    end_year = st.sidebar.selectbox("Année de fin", sorted(df2['Année'].unique()),index=1)
    df_filtered = df_filtered[(df_filtered['Année'] >= start_year) & (df_filtered['Année'] <= end_year)]
elif period_choice == 'Mois':
    # Choisir l'année et le mois de début et de fin
    start_year_month = st.sidebar.selectbox("Sélectionner le mois de début", sorted(df2['Mois_Formate'].unique()),index=12)
    end_year_month = st.sidebar.selectbox("Sélectionner le mois de fin", sorted(df2['Mois_Formate'].unique()),index=20)
    # Convertir la valeur sélectionnée en format d'origine (YYYYMM)
    start_year_month_raw = int(start_year_month.replace('-', ''))
    end_year_month_raw = int(end_year_month.replace('-', ''))
    df_filtered = df_filtered[(df_filtered['Mois'] >= start_year_month_raw) & (df_filtered['Mois'] <= end_year_month_raw)]
elif period_choice == 'Semaine':
    start_week = st.sidebar.selectbox("Sélectionner la semaine de début", sorted(df2['Semaine_Formate'].unique(), key=lambda x: (int(x.split()[1]), int(x.split()[0][1:]))),index=52)
    end_week = st.sidebar.selectbox("Sélectionner la semaine de fin", sorted(df2['Semaine_Formate'].unique(), key=lambda x: (int(x.split()[1]), int(x.split()[0][1:]))), index=87)
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
elif energie_choice == 'Prédiction Gaz (kwh/kg)':
    model = LinearRegression()
    model.fit(df_filtered[['PE (kg)']], df_filtered['Gaz (kWh/kg)'])
    
    # Prédictions
    df_filtered['Predicted Gaz (kWh/kg)'] = model.predict(df_filtered[['PE (kg)']])
    
    # Calcul de l'équation de la droite de régression
    slope = model.coef_[0]
    intercept = model.intercept_
    equation = f"y = {slope:.2f}x + {intercept:.2f}"

    # Graphique nuage de points avec droite de régression
    fig = go.Figure()

    # Nuage de points pour les données réelles
    fig.add_trace(go.Scatter(x=df_filtered['PE (kg)'], y=df_filtered['Gaz (kWh/kg)'], mode='markers', name='Données réelles', marker=dict(color='blue')))
    
    # Droite de régression
    fig.add_trace(go.Scatter(x=df_filtered['PE (kg)'], y=df_filtered['Predicted Gaz (kWh/kg)'], mode='lines', name='Droite de régression', line=dict(color='red')))

    # Affichage de l'équation
    fig.add_annotation(x=0.05, y=0.95, text=equation, showarrow=False, font=dict(size=14, color="black"), xref="paper", yref="paper")

    # Mise à jour des axes et titres
    fig.update_layout(
        title="Prédiction Gaz (kWh/kg) en fonction de PE (kg)",
        title_font=dict(size=24),
        xaxis_title="PE (kg)",
        yaxis_title="Gaz (kWh/kg)",
        height=500,
        width=800
    )
    st.plotly_chart(fig)
else:
    energie_col = energie_choice
    aggregation_method = 'sum'

if period_choice == 'Année':
    if aggregation_method == 'median':
        df_grouped = df_filtered
    elif aggregation_method == 'sum':
        df_grouped = df_filtered.groupby(['Année', 'Machine'])[energie_col].sum().reset_index()
elif period_choice == 'Mois':
    if aggregation_method == 'median':
        df_grouped = df_filtered
    else:
        df_grouped = df_filtered.groupby(['Mois', 'Machine'])[energie_col].sum().reset_index()
elif period_choice == 'Semaine':  # Ajout de la condition pour la semaine
    if aggregation_method == 'median':
        df_grouped = df_filtered
    else:
        df_grouped = df_filtered.groupby(['Semaine', 'Machine'])[energie_col].sum().reset_index()
else:
    if aggregation_method == 'median':
        df_grouped = df_filtered
    else:
        df_grouped = df_filtered.groupby(['Jour', 'Machine'])[energie_col].sum().reset_index()

# Créer une palette de couleurs distinctes
color_palette = px.colors.qualitative.Light24  # Palette de couleurs pré-définie

# Création du graphique avec Plotly
fig = go.Figure()

# Ajouter les sous-graphes avec des couleurs différentes pour chaque site
for idx, machine_selection in enumerate(df_grouped['Machine'].unique()):
    site_data = df_grouped[df_grouped['Machine'] == machine_selection]
    color = color_palette[idx % len(color_palette)]  # Assurer une couleur unique pour chaque site
        # Si un seul site est sélectionné, appliquer la couleur bleue
    if site_selection != 'Global' and len(df_grouped['Machine'].unique()) == 1:
        color = 'Lightblue'
    else:
        color = color_palette[idx % len(color_palette)]  # Assurer une couleur unique pour chaque site

    if period_choice == 'Année':
        fig.add_trace(go.Bar(
            x=site_data['Année'],
            y=site_data[energie_choice],
            name=machine_selection,
            marker=dict(color=color)
        ))
    elif period_choice == 'Mois':

        # Mise en forme de la semaine pour afficher mois et année (ex : 202301 -> Janvier 2023)

        site_data['Mois'] = site_data['Mois'].apply(
            lambda x: f"{pd.to_datetime(str(x), format='%Y%m').strftime('%B %Y')}" if period_choice == 'Mois' else x
        )

        # Trier les données par mois (dans l'ordre croissant des dates)
        site_data['Mois'] = pd.to_datetime(site_data['Mois'], format='%B %Y')
        site_data = site_data.sort_values(by='Mois')

        # Ajout des traces pour le graphique
        fig.add_trace(go.Bar(
        x=site_data['Mois'].dt.strftime('%B %Y'),  # Reformater le mois pour l'affichage
        y=site_data[energie_choice],
        name=machine_selection,
        marker=dict(color=color)
        ))
    elif period_choice == 'Semaine':
        site_data['Semaine'] = site_data['Semaine'].apply(
            lambda x: f"S{int(str(x)[-2:]):02d} {str(x)[:4]}" if period_choice == 'Semaine' else x
        )
        
        fig.add_trace(go.Bar(
            x=site_data['Semaine'],
            y=site_data[energie_choice],
            name=machine_selection,
            marker=dict(color=color)
        ))
    else:
        if energie_choice == 'Gaz (kWh/kg)':
            site_data = site_data[site_data[energie_choice] < 15]

        if energie_choice == 'Electricité (kWh/kg)':
            site_data = site_data[site_data[energie_choice] < 7]

        site_data['Jour'] = site_data['Jour'].apply(
            lambda x: f"{str(x)[:10]}" if period_choice == 'Jour' else x
        )
        fig.add_trace(go.Bar(
            x=site_data['Jour'],
            y=site_data[energie_choice],
            name=machine_selection,
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
        tickfont=dict(size=16),  # Taille des labels des ticks de l'axe X            
    ),
    yaxis_title=f'Consommation ({energie_choice})',
    yaxis_title_font=dict(size=18),  # Taille du titre de l'axe Y
    yaxis=dict(
        color='white',  # Change la couleur des axes Y en blanc
        tickfont=dict(size=16),  # Taille des labels des ticks de l'axe Y
        showgrid=True,  # Afficher la grille
        gridcolor='white',  # Change la couleur de la grille en blan
        zerolinecolor='white',  # Change la couleur de la ligne zéro
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

# Réinitialiser l'index et ne pas l'afficher
df_grouped_reset = df_grouped.reset_index(drop=True)

# Afficher sans l'index
st.write(df_grouped_reset)