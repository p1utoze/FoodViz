import os

import geopandas as gpd
import pandas as pd
import streamlit as st
from llama_index.core import load_index_from_storage, StorageContext
from llama_index.core.retrievers import BaseRetriever
from llama_index.embeddings.voyageai import VoyageEmbedding
from llama_index.vector_stores.faiss import FaissVectorStore

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
def prepare_unit_data(path: str, drop_col: str = "type") -> pd.DataFrame:
    df = pd.read_csv(path)
    if drop_col:
        df.drop("type", axis=1, inplace=True)
    return df

def generate_color_range(start_rgb, end_rgb, steps):
    """
    Generate a color range between two RGB colors.

    :param start_rgb: Tuple representing the starting RGB color.
    :param end_rgb: Tuple representing the ending RGB color.
    :param steps: Number of steps in the color range.
    :return: List of interpolated RGB colors.
    """
    color_range = []
    for t in range(steps + 1):  # +1 to ensure the end color is included
        r = int(start_rgb[0] * (1 - t/steps) + end_rgb[0] * (t/steps))
        g = int(start_rgb[1] * (1 - t/steps) + end_rgb[1] * (t/steps))
        b = int(start_rgb[2] * (1 - t/steps) + end_rgb[2] * (t/steps))
        color_range.append(f"rgb({r} {g} {b})")
    return color_range

@st.cache_resource
def load_retriever(persist_dir: str, top_k: int = 5) -> BaseRetriever:
    embed_model = VoyageEmbedding(model_name="voyage-large-2", voyage_api_key=os.environ["VOYAGE_API_KEY"])
    storage_context = StorageContext.from_defaults(
        vector_store=FaissVectorStore.from_persist_dir(persist_dir),
        persist_dir=persist_dir,
    )
    loaded_index = load_index_from_storage(storage_context, embed_model=embed_model, show_progress=True)
    return loaded_index.as_retriever(similarity_top_k=top_k, vector_store_query_mode="semantic_hybrid", vector_store_kwargs={"alpha": 0.1})

@st.cache_data
def load_bubble_data(df_path: str ):
    df = pd.read_csv(df_path)
    query = lambda x: st.session_state["_conn"].storage.from_('indian_food').get_public_url(f'food-classes/{x.capitalize()}.jpg')
    df["url"] = df["grup"].apply(query)
    return df
    
