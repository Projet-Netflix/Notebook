# Streamlit app converted from Netflix_notebook.ipynb
# Auteur: automated conversion
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Exploration Netflix", layout="wide")

@st.cache_data
def load_data(path='netflix_titles.csv'):
    df = pd.read_csv(path)
    # Parse dates
    df['date_added'] = pd.to_datetime(df['date_added'], errors='coerce')
    df['year_added'] = df['date_added'].dt.year
    df['month_added'] = df['date_added'].dt.month
    # Fill missing
    df['country'] = df['country'].fillna('Non spécifié')
    df['director'] = df['director'].fillna('Non spécifié')
    df['cast'] = df['cast'].fillna('Non spécifié')
    df['rating'] = df['rating'].fillna('Non classifié')
    # Duration parsing: extract minutes for Movies, seasons for TV Shows
    def parse_minutes(x):
        if pd.isna(x):
            return np.nan
        if isinstance(x, str) and 'min' in x:
            try:
                return int(x.split(' ')[0])
            except:
                return np.nan
        return np.nan
    def parse_seasons(x):
        if pd.isna(x):
            return np.nan
        if isinstance(x, str) and 'Season' in x:
            try:
                return int(x.split(' ')[0])
            except:
                return np.nan
        return np.nan
    df['duration_min'] = df['duration'].apply(parse_minutes)
    df['duration_seasons'] = df['duration'].apply(parse_seasons)
    # Delay between release and added
    df['delay_years'] = df['year_added'] - df['release_year']
    df.loc[df['delay_years'] < 0, 'delay_years'] = np.nan
    return df

# Load
with st.spinner('Chargement des données...'):
    df = load_data()

# Sidebar filters
st.sidebar.header('Filtres')
min_year = int(df['release_year'].min())
max_year = int(df['release_year'].max())
year_range = st.sidebar.slider('Année de sortie', min_year, max_year, (2000, max_year))

types = st.sidebar.multiselect('Type', options=df['type'].unique().tolist(), default=df['type'].unique().tolist())

# Top countries list
top_countries = df['country'].value_counts().nlargest(20).index.tolist()
selected_countries = st.sidebar.multiselect('Pays (top 20)', options=top_countries, default=top_countries[:5])

# Apply filters
df_filtered = df[
    (df['release_year'] >= year_range[0]) &
    (df['release_year'] <= year_range[1]) &
    (df['type'].isin(types)) &
    (df['country'].isin(selected_countries))
]

# Main layout
st.title('Analyse Exploratoire du Catalogue Netflix')
st.markdown('Dataset: Netflix Movies & TV Shows (extrait)')

# Key metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric('Titres (filtrés)', len(df_filtered))
col2.metric('Films', int((df_filtered['type']=='Movie').sum()))
col3.metric('Séries', int((df_filtered['type']=='TV Show').sum()))
col4.metric('Années couvertes', f"{df_filtered['release_year'].min()} - {df_filtered['release_year'].max()}")

# Distribution type
st.header('Répartition Films vs Séries')
type_counts = df_filtered['type'].value_counts()
fig_type = px.pie(names=type_counts.index, values=type_counts.values, title='Proportion Films vs Séries', hole=0.3)
st.plotly_chart(fig_type, use_container_width=True)

# Missing values
st.header('Valeurs manquantes par colonne (global)')
missing = df.isnull().sum()
missing = missing[missing > 0].sort_values(ascending=False)
fig_missing = px.bar(x=missing.values, y=missing.index, orientation='h', labels={'x':'Nombre de valeurs manquantes','y':'Colonne'})
st.plotly_chart(fig_missing, use_container_width=True)

# Delay between release and addition
st.header("Délai entre sortie et ajout sur Netflix")
valid_delay = df_filtered.dropna(subset=['delay_years'])
if len(valid_delay)>0:
    fig_delay = px.box(valid_delay, x='type', y='delay_years', color='type', title='Délai (années) par type')
    st.plotly_chart(fig_delay, use_container_width=True)
    avg_movie = valid_delay[valid_delay['type']=='Movie']['delay_years'].mean()
    avg_tv = valid_delay[valid_delay['type']=='TV Show']['delay_years'].mean()
    st.write(f"Délai moyen Films: {avg_movie:.1f} ans" if not np.isnan(avg_movie) else "Délai moyen Films: N/A")
    st.write(f"Délai moyen Séries: {avg_tv:.1f} ans" if not np.isnan(avg_tv) else "Délai moyen Séries: N/A")
else:
    st.info('Aucune donnée de délai disponible pour les filtres sélectionnés.')

# Duration distribution for movies
st.header('Distribution des durées (films)')
movies = df_filtered[df_filtered['type']=='Movie']
if len(movies)>0 and movies['duration_min'].notna().sum()>0:
    fig_dur = px.histogram(movies, x='duration_min', nbins=50, title='Distribution des durées (minutes)')
    fig_dur.update_xaxes(title_text='Durée (minutes)')
    st.plotly_chart(fig_dur, use_container_width=True)
else:
    st.info('Pas assez de données de durée pour les films (après filtres).')

# Top countries
st.header('Top pays par nombre de titres')
country_counts = df_filtered['country'].value_counts().nlargest(10)
fig_country = px.bar(x=country_counts.values, y=country_counts.index, orientation='h', labels={'x':'Nombre','y':'Pays'}, title='Top 10 pays')
st.plotly_chart(fig_country, use_container_width=True)

# Afficher données
st.header('Aperçu des données')
st.dataframe(df_filtered.sample(min(100, len(df_filtered))))

# Téléchargement du dataset nettoyé
@st.cache_data
def convert_df_to_csv(dff):
    return dff.to_csv(index=False).encode('utf-8')

csv = convert_df_to_csv(df_filtered)
st.download_button('Télécharger le dataset filtré (CSV)', data=csv, file_name='netflix_filtered.csv', mime='text/csv')

# Footer
st.markdown('---')
st.caption('Application générée automatiquement à partir de Netflix_notebook.ipynb')
