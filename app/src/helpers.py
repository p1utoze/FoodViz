import streamlit as st
import geopandas as gpd
import pandas as pd
import numpy as np
from .config import PROJECT_ROOT
@st.cache_data(show_spinner=":blue[Loading the database..] Please wait...")
def prepare_indian_geojson():
    url = "https://raw.githubusercontent.com/Subhash9325/GeoJson-Data-of-Indian-States/master/Indian_States"
    # url = PROJECT_ROOT / "data" / "INDIA_STATES.geojson"
    gdf = gpd.read_file(url)
    gdf["geometry"] = gdf.to_crs(gdf.estimate_utm_crs()).simplify(1000).to_crs(gdf.crs)
    india_states = gdf.rename(columns={"NAME_1": "ST_NM"}).__geo_interface__
    return india_states


@st.cache_data()
def prepare_indian_languages():
    # simulate data frame
    # state = ['Arunachal Pradesh', 'Assam', 'Chandigarh', 'Chhattisgarh', 'Delhi', 'Goa', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Punjab', 'Rajasthan', 'Sikkim', 'Tripura', 'Uttarakhand', 'Telangana', 'Andaman & Nicobar', 'Bihar', 'Gujarat', 'Kerala', 'Lakshadweep', 'Madhya Pradesh', 'Odisha', 'Tamil Nadu', 'Uttar Pradesh', 'West Bengal', 'Andhra Pradesh', 'Puducherry', 'Maharashtra', 'Daman & Diu', 'Dadra & Nagar Haveli', 'Ladakh', 'Jammu & Kashmir']
    # dff = pd.DataFrame(
    #     {
    #         # "state": ['Andaman and Nicobar', 'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chandigarh',
    #         #           'Chhattisgarh', 'Dadra and Nagar Haveli', 'Daman and Diu', 'Delhi', 'Goa', 'Gujarat', 'Haryana',
    #         #           'Himachal Pradesh', 'Jammu and Kashmir', 'Jharkhand', 'Karnataka', 'Kerala', 'Lakshadweep',
    #         #           'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Orissa',
    #         #           'Puducherry', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Tripura', 'Uttar Pradesh',
    #         #           'Uttaranchal', 'West Bengal'],  # fmt: skip
    #         "state": state,
    #         "content_view": np.random.randint(1, 5, 37),
    #     }
    # )
    path = PROJECT_ROOT / "data" / "languages.csv"
    df = pd.read_csv(path)
    return df

