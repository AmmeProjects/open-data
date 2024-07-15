import os
import json
import requests
import pandas as pd
import geopandas as gpd

FILE_MUNICIPIOS = "data/raw/municipios.json"
FILE_DISTRITOS = "data/raw/distritos.json"


def load_municipios(path=FILE_MUNICIPIOS):

    if os.path.exists(path):
        print("reading from cache")
        with open(path, "r") as f:
            return json.load(f)
    else:
        print("reading from geoapi")
        response = requests.get("https://json.geoapi.pt/distritos/municipios")
        with open(path, "w") as f:
            json.dump(response.json(), f)
        return response.json()


def load_distritos(path=FILE_DISTRITOS):

    if os.path.exists(path):
        print("reading from cache")
        with open(path, "r") as f:
            return json.load(f)
    else:
        print("reading from geoapi")
        response = requests.get("https://json.geoapi.pt/distritos")
        with open(path, "w") as f:
            json.dump(response.json(), f)
        return response.json()
    

def dataframe_municipios():
    js_minicipios = load_municipios()
    
    return (
        pd
        .DataFrame(js_minicipios)[["distrito", "municipios"]]
        .explode("municipios")
        .assign(
            municipio=lambda _: _.municipios.str["nome"],
        )
        .drop(columns=["municipios"])
        .reset_index(drop=True)
        .rename(columns={"distrito": "DISTRITO", "municipio": "MUNICIPIO"})
    )

def geoframe_distritos():
    distritos_geo = load_distritos()

    df_distritos = (
        pd
        .DataFrame(distritos_geo)[["distrito", "geojson"]]
        .rename(columns={"distrito": "DISTRITO"})
    )

    geojson = {"type": "FeatureCollection", "features": df_distritos["geojson"].tolist()}
    for i, feature in enumerate(geojson["features"]):
        if "Distrito" in feature["properties"]:
            feature["id"] = feature["properties"]["Distrito"]
            
    return (        
        gpd
        .GeoDataFrame
        .from_features(geojson)
        .rename(columns={"Distrito": "DISTRITO"})
        [["DISTRITO", "geometry", "centros"]]
    )
