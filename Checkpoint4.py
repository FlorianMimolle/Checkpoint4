import pandas as pd
import streamlit as st
import re
import folium
import json
import requests
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from streamlit_folium import folium_static
import numpy as np
import string 
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO

#FONCTION : 
def textualisation(df):
        result = []
        for comment in df["description_clean"]:
            for mot in re.findall("\S+",str(comment)):
                result.append(mot)
        result = " ".join(result)
        return result
def couleur(*args, **kwargs):
        import random
        return "rgb({}, 0, 0)".format(random.randint(100, 255))

#Définit le mode "large" du site : afin que l'ensemble de la page soit utilisée pour afficher les graphiques:
st.set_page_config(layout="wide")
st.sidebar.image("https://github.com/FlorianMimolle/Checkpoint4/blob/main/te%CC%81le%CC%81chargement.png?raw=true")

link = "https://github.com/murpi/wilddata/raw/master/wine.zip"
df = pd.read_csv(link,low_memory=False)

#Correspond à la colonne description nettoyée 
link2= "https://raw.githubusercontent.com/FlorianMimolle/Checkpoint4/main/df_checkpoint4"
df_clean = pd.read_csv(link2,low_memory=False)

df = pd.concat([df,df_clean],axis = 1).drop(columns = ["Unnamed: 0"])
df_all = df.copy() #On garde une copie du df non filtré (notamment pour le wordcloud)

Graphique = st.sidebar.radio("Séléctionner le graphique souhaité :",
                                     ("Introduction",
                                      "Nombre de vins produits par pays",
                                      "Pays qui ont les meilleures notes",
                                      "Moyennes de notes par cépage",
                                      "Distribution par quantile",
                                      "Wordcloud de Description",
                                      "Influence sur le prix",
                                      "Prix Conseillés"))

#On ajoute les différents cépages dans une liste : 
if (Graphique != "Introduction") & (Graphique != "Prix Conseillés"):
    
    Cépages = ["All"] #On met all pour permettre à l'utilisateur de voir l'ensemble des cépages
    for cépage in sorted(df["variety"].unique().astype(str)):
        Cépages.append(cépage)
    #On  propose à l'utilisateur de sélectionner le cépage désiré:
    filtre_cepage = st.sidebar.selectbox('Sur quel cépage souhaitez-vous filtrer ?',
                                        Cépages) #Choix présélectionné à l'ouverture du fichier
    if filtre_cepage != "All":
        df = df[df["variety"]==filtre_cepage]
        
        
    #On ajoute les différentes province dans une liste : 
    Province = ["All"] #On met all pour permettre à l'utilisateur de voir l'ensemble des cépages
    for province in sorted(df["province"].unique().astype(str)): 
        Province.append(province)  
    #On  propose à l'utilisateur de sélectionner le cépage désiré:
    filtre_province = st.sidebar.selectbox('Sur quel province souhaitez-vous filtrer ?',
                                        Province) #Choix présélectionné à l'ouverture du fichier
    if filtre_province != "All":
        df = df[df["province"]==filtre_province]
    
    table = st.sidebar.checkbox("Afficher le Tableau de données ")    
    if table:
        df

####################PREPROCESSING#####################Debut : 

#On récupère les années (nombre composé de 4 chiffres) commencant par 18,19 ou 20 (après vérification, les années antérieurs sont accompagnées d'une autre année plus récente. Nous prenons ensuite l'année la plus récente (souvent l'autre année correspond à l'année de l'espèce de vigne))
df["year"] = df["title"].apply(lambda x: (",".join(sorted(re.findall("18\d{2}|19\d{2}|20\d{2}",x),reverse = True))).split(",")[0])
annee_med = int(df[df["year"]!=""]["year"].median())
df["year"] = df["year"].apply(lambda x : 2015 if x == "2067" else 
                                         int(x) if x !="" else 
                                         annee_med)
#On rempli les colonnes vides de l'origine et designation par "Inconnu":
for colonne in ["country","designation","province","region_1","region_2"]:
  df[colonne] = df[colonne].fillna("Unknown")
#On suppose que les colonnes taster sont vides lorsque le vin n'a pas été goûté:
for colonne in ["taster_name","taster_twitter_handle"]:
  df[colonne] = df[colonne].fillna("Not tasted")
#On supprime les lignes vides dans price car c'est notre colonne target. Si le prix n'est pas renseigné, alors nous ne pouvons pas exploîter ces lignes.
df = df.dropna(subset=['price'])
#La seule ligne vide pour variety (id = 86900) a pour titre : Carmen 2003 (Maipo Valley). En cherchant sur internet, nous trouvons facilement qu'il s'agit d'un sauvignon
df["variety"] = df["variety"].fillna("Sauvignon")

####################PREPROCESSING#####################FIN

####################GRAPHIQUES#####################Debut :

#la répartition du nombre de vins par pays: 
if Graphique == "Introduction":
    st.title("Introdction")
    st.write("le Domaine des Croix cherche à définir le prix de ses bouteilles de vin pour le marché américain à l'aide d'une base de données de 130 000 bouteilles de vins et leur prix sur le marché Américain.")
    st.write("Il faudra :\n- Faire une étude du marché\n- Expliquer la démarche réaliser pour déterminer le prix\n- Proposer au client un prix à ses bouteilles  ")
    st.image("https://github.com/FlorianMimolle/Checkpoint4/blob/main/Capture%20d%E2%80%99e%CC%81cran%202022-02-03%20a%CC%80%2009.56.37.png?raw=true")
    st.write("source : CNIV")


if Graphique == "Nombre de vins produits par pays":
    st.title("Nombre de vins produits par pays")
    #On créé un df avec les valeurs que nous souhaitons dans notre graphique : 
    df_1 = df[["country","title"]].groupby("country").count().reset_index().sort_values(by="title",ascending = False)
    #On modifie les valeurs pour que cela corresponde aux noms du fichier json:
    df_1.loc[df_1.country=="US",'country']='United States of America' 
    df_1.loc[df_1.country=="England",'country']='United Kingdom'
    
    col1,col2 = st.columns(2)
    with col1:
        m = folium.Map(location = [46.00996, 3.993163],zoom_start=1,tiles='cartodb positron')
        country_geo = json.loads(requests.get('https://raw.githubusercontent.com/python-visualization/folium/master/examples/data/world-countries.json').text)
        for pays_geo in range(0,len(country_geo["features"])): #Pour tout les pays du fichier json on créé la donnée vide nb_wines
            country_geo["features"][pays_geo]['properties']["nb_wines"]= 0
        for pays_geo in range(0,len(country_geo["features"])): #Pour tout les pays du fichier json:
            for pays_df1 in range(0,len(df_1)): #Pour tout les départements du df_1 :
                if country_geo["features"][pays_geo]['properties']['name']==df_1.iloc[pays_df1,0]: #Si les deux pays_geo et pays_df1 concorde : alors on modifie le fichier Json pour ajouter le nb_wines au pays
                    country_geo["features"][pays_geo]['properties']["nb_wines"]= int(df_1.iloc[pays_df1,1]) 

        choropleth = folium.Choropleth(
            geo_data=country_geo,
            name='choropleth',
            data=df_1,
            columns=['country',"title"],
            key_on='properties.name',
            fill_color='Reds',
            fill_opacity=0.7,
            line_opacity=0.2,
            threshold_scale = df_1["title"].quantile((0,0.2,0.4,0.6,0.8,1)).tolist(), #On utilise les quantiles pour répartir les pays équitablement dans les couleurs
            nan_fill_color='white',
            legend_name="Nombre de Vins produits"
        ).add_to(m)
        folium.LayerControl().add_to(m)
        style_function = "font-size: 10px"

        choropleth.geojson.add_child(folium.features.GeoJsonTooltip
                                                (aliases=["Pays","nb_Vins"], #Modifie les aliases (partie gauche de la bulle d'info)
                                                fields=["name","nb_wines"], #On modifie les valeurs (partie droite de la bulle d'info)
                                                labels=True)) #Pour afficher l'aliases
        folium_static(m)
        
    with col2:
        fig = px.bar(df_1.head(15), 
                    x='country', 
                    y='title',
                    title="Top 15 des pays producteurs de vin",
                    labels={"title":'Nombre de vins',
                            "country": "Pays"},
                    text_auto='.2s')
        fig.update_xaxes(tickangle=90)
        fig.update_layout(height = 600, #Hauteur du graphique (afin que les trois graphiques en bar de la page soient homogènes)
                          width =700,
                          font = dict(size = 16))
        fig.update_traces(marker_color='indianred')
        st.plotly_chart(fig)
        
#les pays qui ont les meilleures notes: 
if Graphique == "Pays qui ont les meilleures notes":
    st.title("Moyenne des notes des vins produits par pays")
    #On créé un df avec les valeurs que nous souhaitons dans notre graphique : 
    df_2 = df[["country","points"]].groupby("country").mean().reset_index().sort_values(by="points",ascending = False)
    df_2["points"] = round(df_2["points"],2)
    #On modifie les valeurs pour que cela corresponde aux noms du fichier json:
    df_2.loc[df_2.country=="US",'country']='United States of America' 
    df_2.loc[df_2.country=="England",'country']='United Kingdom'
    
    col1,col2 = st.columns(2)
    with col1:
        m = folium.Map(location = [46.00996, 3.993163],zoom_start=1,tiles='cartodb positron')
        country_geo = json.loads(requests.get('https://raw.githubusercontent.com/python-visualization/folium/master/examples/data/world-countries.json').text)
        for pays_geo in range(0,len(country_geo["features"])): #Pour tout les pays du fichier json on créé la donnée vide nb_wines
            country_geo["features"][pays_geo]['properties']["note"]= 0
        for pays_geo in range(0,len(country_geo["features"])): #Pour tout les pays du fichier json:
            for pays_df2 in range(0,len(df_2)): #Pour tout les départements du df_2 :
                if country_geo["features"][pays_geo]['properties']['name']==df_2.iloc[pays_df2,0]: #Si les deux pays_geo et pays_df2 concorde : alors on modifie le fichier Json pour ajouter le nb_wines au pays
                    country_geo["features"][pays_geo]['properties']["note"]= df_2.iloc[pays_df2,1]

        choropleth = folium.Choropleth(
            geo_data=country_geo,
            name='choropleth',
            data=df_2,
            columns=['country',"points"],
            key_on='properties.name',
            fill_color='Reds',
            fill_opacity=0.7,
            line_opacity=0.2,
            threshold_scale = df_2["points"].quantile((0,0.2,0.4,0.6,0.8,1)).tolist(), #On utilise les quantiles pour répartir les pays équitablement dans les couleurs
            nan_fill_color='white',
            legend_name="Moyenne des notes"
        ).add_to(m)
        folium.LayerControl().add_to(m)
        style_function = "font-size: 10px"

        choropleth.geojson.add_child(folium.features.GeoJsonTooltip
                                                (aliases=["Pays","note"], #Modifie les aliases (partie gauche de la bulle d'info)
                                                fields=["name","note"], #On modifie les valeurs (partie droite de la bulle d'info)
                                                labels=True)) #Pour afficher l'aliases
        folium_static(m)
    with col2:
        fig = px.bar(df_2, 
                    x='country', 
                    y='points',
                    title="Classement des pays en fonction de leur note moyenne",
                    labels={"title":'Moyenne des notes',
                            "country": "Pays"},
                    text_auto=True,
                    range_y = [80,100])
        fig.update_xaxes(tickangle=90)
        fig.update_layout(height = 600, #Hauteur du graphique (afin que les trois graphiques en bar de la page soient homogènes)
                          width =700,
                          font = dict(size = 16))
        fig.update_traces(marker_color='indianred')
        st.plotly_chart(fig)
        
if Graphique == "Moyennes de notes par cépage":
    st.title("Moyennes de notes par cépage")
    #On créé un df avec les valeurs que nous souhaitons dans notre graphique : 
    df_3 = df[["variety","points"]].groupby("variety").mean().reset_index().sort_values(by="points",ascending = False)
    df_3["points"] = round(df_3["points"],2)
    fig = make_subplots(rows=2, 
                        cols=1,
                        subplot_titles=["Top 20 des meilleurs cépages",
                                        "Flop 20 des cépages les moins biens notés"],
                        vertical_spacing = 0.35,
                        y_title = "Moyenne des notes")

    fig.add_trace(go.Bar(x=df_3.iloc[0:20,:]["variety"], 
                        y=df_3.iloc[0:20,:]["points"],
                        text = df_3.iloc[0:20,:]["points"]),
                row = 1, 
                col = 1)

    fig.add_trace(go.Bar(x=df_3.iloc[-20:,:]["variety"], 
                        y=df_3.iloc[-20:,:]["points"],
                        text = df_3.iloc[-20:,:]["points"]),
                row = 2, 
                col = 1)
    fig.update_xaxes(tickangle=90)
    fig.update_layout(coloraxis=dict(colorscale='Bluered_r'), 
                    showlegend=False,
                    yaxis1 = dict(range=[80,100]),
                    yaxis2 = dict(range=[80,100]),
                    height = 800, #Hauteur du graphique (afin que les trois graphiques en bar de la page soient homogènes)
                    width =1300,
                    font = dict(size = 16))
    fig.update_traces(marker_color='indianred')

    st.plotly_chart(fig)
    
if Graphique =="Distribution par quantile":
    st.title("Distribution des données numériques")
    fig = make_subplots(rows=1, 
                        cols=3,
                        subplot_titles=["Prix",
                                        "Note",
                                        "Année de production"])
    position = 1
    for colonne in ["price","points","year"]:
        fig.add_trace(go.Box(y=df[colonne]),
                    row = 1, 
                    col = position)
        position += 1
    fig.update_layout(showlegend=False,
                    height = 800, #Hauteur du graphique (afin que les trois graphiques en bar de la page soient homogènes)
                    width =1300,
                    font = dict(size = 16))
    fig.update_traces(marker_color='indianred')
    fig['layout']['yaxis1']['title']='€'
    fig['layout']['yaxis2']['title']='Note moyenne'
    fig['layout']['yaxis3']['title']='Année'
    st.plotly_chart(fig)

if Graphique =="Wordcloud de Description":
    st.title("Wordcloud des 20 mots les plus fréquents dans la colonne 'Description'")
    texte_all = textualisation(df_all)
    texte = textualisation(df)
    url = requests.get("https://github.com/FlorianMimolle/Checkpoint4/blob/main/Ardoise%20bouteille%20de%20vin%20Securit%20%5Bgg112%5D(1).jpg?raw=true")
    img = Image.open(BytesIO(url.content))
    mask = np.array(img)
    mask[mask == 1] = 255

    wordcloud = WordCloud(width=480, 
						height=480, 
						random_state=1,
						max_font_size=200, 
						min_font_size=10,
						collocations=False,
						background_color = None,
      					max_words=20,
                        mask = mask,
                        mode = "RGBA")
    fig, ax = plt.subplots( 
						nrows = 1,
						ncols = 2)
    #fig.patch.set_facecolor('xkcd:black')
    wordcloud.generate_from_text(texte_all)
    ax[0].imshow(wordcloud.recolor(color_func = couleur))
    ax[0].set_title("Sur l'ensemble de la base de données",fontsize=8)
    ax[0].axis("off")
    ax[0].margins(x=0, y=0)
    
    wordcloud.generate_from_text(texte)
    ax[1].imshow(wordcloud.recolor(color_func = couleur))
    ax[1].set_title(f"filtré sur le cépage : {filtre_cepage}\net la province : {filtre_province}",fontsize=8)
    ax[1].axis("off")
    ax[1].margins(x=0, y=0)
    plt.subplots_adjust(wspace = 0)
    st.pyplot(fig.figure)
if Graphique == "Influence sur le prix":
    st.title("Observation de l'influence des variables sur le prix")
    df_perso=df.drop(columns=["description","designation","province","region_1","region_2","taster_name","taster_twitter_handle","title","winery","description_clean"])
    measures = df_perso.columns
    col1,col2,col3,col4,col5 = st.columns(5)
    with col1:
        scatter_y_1 = st.selectbox("Y axis:", measures, index = 2)
    with col2:
        scatter_x_1 = st.selectbox("X axis:", measures,index = 1)
    with col4:
        scatter_y_2 = st.selectbox("Y axis :", measures, index = 2)
    with col5:
        scatter_x_2= st.selectbox("X axis :", measures, index = 4)
    col1,col2 = st.columns(2)
    with col1:
        fig = px.scatter(df_perso,
                         x=scatter_x_1,
                         y=scatter_y_1,
                         title="Corrélation",
                         color_discrete_sequence= ["deepskyblue"])
        st.plotly_chart(fig)
    with col2:
        fig = px.scatter(df_perso,
                         x=scatter_x_2,
                         y=scatter_y_2,
                         title="Corrélation",
                         color_discrete_sequence= ["deepskyblue"])
        st.plotly_chart(fig)

if Graphique == "Prix Conseillés":
    df_prix = pd.read_csv("https://raw.githubusercontent.com/FlorianMimolle/Checkpoint4/main/df_prix",low_memory=False)
    df_prix = df_prix.drop(columns = ["Unnamed: 0"])
    df_prix
    st.write("- low : moins de 20€\n- medium : entre 20 et 40€\n- cher : entre 40 et 80€\n- très cher : entre 80 et 200€\n- luxe : supérieur à 200€")
    st.write("Arbre de décision ayant eu le meilleur score (celui utiliser pour déterminer la tranche de prix conseillées)")
    st.image("https://github.com/FlorianMimolle/Checkpoint4/blob/main/Unknown.png?raw=true")
