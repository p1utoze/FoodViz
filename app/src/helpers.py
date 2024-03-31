import streamlit as st
import geopandas as gpd
import pandas as pd
import numpy as np
from .config import PROJECT_ROOT


@st.cache_data(show_spinner=":blue[Loading the database..] Please wait...", persist=True)
def prepare_indian_geojson():
    url = "https://raw.githubusercontent.com/Subhash9325/GeoJson-Data-of-Indian-States/master/Indian_States"
    # url = PROJECT_ROOT / "data" / "INDIA_STATES.geojson"
    gdf = gpd.read_file(url)
    gdf["geometry"] = gdf.to_crs(gdf.estimate_utm_crs()).simplify(1000).to_crs(gdf.crs)
    india_states = gdf.rename(columns={"NAME_1": "ST_NM"}).__geo_interface__
    return india_states


@st.cache_data()
def prepare_indian_languages():
    path = PROJECT_ROOT / "data" / "languages.csv"
    df = pd.read_csv(path)
    return df

@st.cache_data()
def prepare_unit_data(path: str):
    df = pd.read_csv(path)
    df.drop("type", axis=1, inplace=True)
    return df
