import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import plotly.express as px  # Pour accéder à des palettes de couleurs
import toml
import streamlit_authenticator as stauth

st.set_page_config(page_title="Tableau", layout="wide")

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
df2 = pd.read_csv("20250601 Global_streamlit.csv", sep=";")

# Assurer que la colonne 'Date' est bien au format datetime
df2['Date'] = pd.to_datetime(df2['Date'], errors='coerce', dayfirst=False)

# Extraire l'année, le mois et le journb
#df2['Année'] = df2['Date'].dt.year
#df2['Mois'] = df2['Date'].dt.month
#df2['Jour'] = df2['Date'].dt.date

df2['Jour'] = pd.to_datetime(df2['Jour'], errors='coerce', dayfirst=False)
df2['Mois-Abrege'] = df2['Date'].dt.strftime('%b')  # Mois abrégés (ex: Jan, Feb, Mar, etc.)
df2['Trimestre'] = df2['Année'] * 10 + ((df2['Mois'] - 1) // 3 + 1)
df2['Mois'] = df2['Année'] * 100 + df2['Mois']
df2['Semaine'] = df2['Année'] * 100 + df2['Semaine']
df2['Semaine_Formate'] = df2['Semaine'].apply(lambda x: f"S{int(str(x)[-2:]):02d} {str(x)[:4]}")
df2['Trimestre_Formate'] = df2['Trimestre'].astype(str).str[:4] + '-Q' + df2['Trimestre'].astype(str).str[4:]
df2['Mois_Formate'] = df2['Mois'].astype(str).str[:4] + '-' + df2['Mois'].astype(str).str[4:]
df2 = df2[df2['Année'].isin([2023,2024, 2025])]
df2['Empreinte carbone (tCO2)'] = ((df2['Gaz (kWh)'].fillna(0)) / 1000 * 0.181) + ((df2['Electricité (kWh)'].fillna(0)) / 1000 * 0.0338)
# Charger l'image et afficher en haut à gauche
image = "PT.jpg"  # Remplacez ce chemin par le chemin réel de votre image
st.image(image)

# Filtrage des données dans Streamlit
st.sidebar.title("Filtrage des données")
sites = df2['Site'].unique()
site_selection = st.sidebar.selectbox('Choisissez un site', ['Global'] + list(sites) + ['Total'])

# Choisir l'énergie à afficher
energie_choice = st.sidebar.radio("Choisissez l'indicateur", ['Gaz (kWh/kg)', 'Electricité (kWh/kg)','Empreinte carbone (tCO2)', 'Gaz (kWh)', 'Electricité (kWh)', 'PE (kg)'])

# Choisir la période de filtrage
period_choice = st.sidebar.radio("Sélectionner la période", ('Année','Trimestre', 'Mois','Semaine')) #j'ai enlevé le filtre journalier

if site_selection == 'Total' :
    df2['Site'] = 'Total'

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
        
elif site_selection == 'Total' :

    if energie_choice == 'Gaz (kWh/kg)' or energie_choice == 'Electricité (kWh/kg)':
        # Si l'énergie choisie est 'Gaz (kWh/kg)' ou 'Electricité (kWh/kg)', filtrer df_final selon le site sélectionné
        df_filtered = df_final
    else:
        # Sinon, filtrer df2 selon le site sélectionné
        df2['Site'] = 'Total'
        df_filtered = df2.groupby([period_choice, 'Site'])[energie_choice].sum().reset_index()

elif energie_choice == 'Gaz (kWh/kg)' or energie_choice == 'Electricité (kWh/kg)':
    # Si l'énergie choisie est 'Gaz (kWh/kg)' ou 'Electricité (kWh/kg)', filtrer df_final selon le site sélectionné
    df_filtered = df_final[df_final['Site'] == site_selection]

else:
    # Sinon, filtrer df2 selon le site sélectionné
    df_filtered = df2[df2['Site'] == site_selection]
 
# Filtrage selon la période choisie
if period_choice == 'Année':
    start_year = st.sidebar.selectbox("Année de début", sorted(df2['Année'].unique()),index=0)
    end_year = st.sidebar.selectbox("Année de fin", sorted(df2['Année'].unique()),index=1)
    df_filtered = df_filtered[(df_filtered['Année'] >= start_year) & (df_filtered['Année'] <= end_year)]
elif period_choice == 'Trimestre' :
    start_year_quarter = st.sidebar.selectbox(
    "Sélectionner le trimestre de début",
    sorted(df2['Trimestre_Formate'].unique(), key=lambda x: (int(x[:4]), int(x[-1]))), 
    index=4
    )
    end_year_quater = st.sidebar.selectbox(
    "Sélectionner le trimestre de début",
    sorted(df2['Trimestre_Formate'].unique(), key=lambda x: (int(x[:4]), int(x[-1]))), 
    index=7
    )
    # Convertir la valeur sélectionnée en format d'origine (YYYYMM)
    start_year_month_raw = int(start_year_quarter.replace('-Q', ''))
    end_year_month_raw = int(end_year_quater.replace('-Q', ''))
    df_filtered = df_filtered[(df_filtered['Trimestre'] >= start_year_month_raw) & (df_filtered['Trimestre'] <= end_year_month_raw)]
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
    end_week = st.sidebar.selectbox("Sélectionner la semaine de fin", sorted(df2['Semaine_Formate'].unique(), key=lambda x: (int(x.split()[1]), int(x.split()[0][1:]))), index=90)
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
elif energie_choice == 'Gaz (kWh)' or energie_choice == 'Electricité (kWh)' or energie_choice == 'Empreinte carbone (tCO2)' :
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

elif period_choice == 'Trimestre' :
    if aggregation_method == 'median':
        df_grouped = df_filtered
    else:
        df_grouped = df_filtered.groupby(['Trimestre', 'Site'])[energie_col].sum().reset_index()

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
color_palette = px.colors.qualitative.Light24  # Palette de couleurs pré-définie

# Création du graphique avec Plotly
fig = go.Figure()

# Ajouter les sous-graphes avec des couleurs différentes pour chaque site
for idx, site in enumerate(df_grouped['Site'].unique()):
    site_data = df_grouped[df_grouped['Site'] == site]
    
    # Si un seul site est sélectionné, appliquer la couleur bleue
    if site_selection != 'Global' and 'Total'  and len(df_grouped['Site'].unique()) == 1:
        color = 'Lightblue'
    else:
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
        # Trier les données par mois (dans l'ordre croissant des dates)
        site_data['Mois'] = pd.to_datetime(site_data['Mois'], format='%B %Y')
        site_data = site_data.sort_values(by='Mois')
        # Ajout des traces pour le graphique
        fig.add_trace(go.Bar(
            x=site_data['Mois'].dt.strftime('%B %Y'),  # Reformater le mois pour l'affichage
            y=site_data[energie_choice],
            name=site,
            marker=dict(color=color)
        ))

    elif period_choice == 'Trimestre':
        # Création du format Q1 2024, Q2 2024, ...
        site_data['Trimestre_Formate'] = site_data['Trimestre'].apply(
            lambda x: f"Q{(int(str(x)[-1]))} {str(x)[:4]}"
        )

        # Associer chaque trimestre à une date de référence pour le tri (ex: Q1 -> 15 février de l'année)
        site_data['Trimestre_Sort'] = pd.to_datetime(
            site_data['Trimestre'].apply(lambda x: f"{str(x)[:4]}-{(int(str(x)[-1]) - 1) * 3 + 2}-15"),
            format='%Y-%m-%d'
        )

        # Trier les données par trimestre (ordre chronologique)
        site_data = site_data.sort_values(by='Trimestre_Sort')

        # Ajout des traces pour le graphique
        fig.add_trace(go.Bar(
            x=site_data['Trimestre_Formate'],  # Affichage sous "Q1 2024"
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
            site_data = site_data[site_data[energie_choice] < 15]
        if energie_choice == 'Electricité (kWh/kg)':
            site_data = site_data[site_data[energie_choice] < 7]
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
        tickfont=dict(size=16),  # Taille des labels des ticks de l'axe X
    ),
    yaxis_title=f'Consommation ({energie_choice})',
    yaxis_title_font=dict(size=18),  # Taille du titre de l'axe Y
    yaxis=dict(
        color='white',  # Change la couleur des axes Y en blanc
        tickfont=dict(size=16),  # Taille des labels des ticks de l'axe Y
        showgrid=True,  # Afficher la grille
        gridcolor='white',  # Change la couleur de la grille en blanc
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
                  f"{str(x)[:10]}" if period_choice == 'Jour' else
                  f"Q{str(x)[-1]} {str(x)[:4]}" if period_choice == 'Trimestre' else x
                

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

