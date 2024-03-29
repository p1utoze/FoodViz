import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np


from postgrest import APIResponse
from src import SupabaseConnection, prepare_indian_geojson, prepare_indian_languages
from src.utils import load_json
from src.config import (
    DB_TABLE_NAME,
    DB_FOOD_NAME_HEADER,
    DB_FOOD_CODE_HEADER,
    DB_SCI_NAME_HEADER,
    PROJECT_ROOT,
    DB_FOOD_TAGS_HEADER
)

_sess_state = st.session_state

if "is_fil_row" in _sess_state:
    del st.session_state["is_fil_row"]

if "_conn" not in _sess_state:
    _sess_state["_conn"] = st.connection("supabase", type=SupabaseConnection)

if 'gjson' not in _sess_state:
    _sess_state['gjson'] = prepare_indian_geojson()
    # path = PROJECT_ROOT / "data" / "Indian_States.json"
    # with open(path, 'r') as f:
    #     _sess_state['gjson'] = json.load(f)

if 'indian_states' not in _sess_state:
    _sess_state['indian_states'] = prepare_indian_languages()


@st.cache_data()
def fetch_image(file_name: str):
    # _, _, image = _sess_state['_conn'].download(
    #     bucket_id="indian_food",
    #     source_path=file_name
    # )
    url = _sess_state["_conn"].get_public_url('indian_food', f"{file_name}.jpg")
    # res = image.read()
    return url


@st.cache_resource(ttl=600)
def query_with_filter_like(table: str, column: str, value: str, return_columns: str = "*"):
    return _sess_state["_conn"].table(table).select(return_columns).like(column, f"{value}%25").execute()


@st.cache_resource(ttl=600)
def query_with_filter_eq(table: str, column: str, value: str, return_columns: str = "*"):
    return _sess_state["_conn"].table(table).select(return_columns).eq(column, value).execute()

if "fg" not in _sess_state:
    _sess_state["fg"] = load_json()
# Perform query.
# rows: APIResponse = _sess_state["_conn"].query("*", table="food_ifct", ttl="10m").execute()
# conn.table("mytable").insert({"name": "John Doe"}).execute()


st.header("IFCT Food Database Overview 🚚")

with st.container(height=100):
    return_cols = f"{DB_FOOD_CODE_HEADER}, {DB_FOOD_NAME_HEADER}, {DB_SCI_NAME_HEADER}, {DB_FOOD_TAGS_HEADER}"
    col1, col2 = st.columns(2, gap="large")
    grp_name = col1.selectbox("Choose a food group: ", _sess_state["fg"].keys(), index=None, placeholder="Select a food group")
    if grp_name:
        fil_row = query_with_filter_like(
            return_columns=return_cols,
            table=DB_TABLE_NAME,
            column=DB_FOOD_CODE_HEADER,
            value=_sess_state["fg"][grp_name]
        )
        fil_row = pd.DataFrame(fil_row.data)
        sel = col2.selectbox("Choose a food item: ", ["ALL"] + fil_row[DB_FOOD_NAME_HEADER].tolist(), index=None,  placeholder="Select a food item")
        if sel == 'ALL':
            _sess_state["is_fil_row"] = False
            fil_row[DB_FOOD_TAGS_HEADER] = fil_row[DB_FOOD_TAGS_HEADER].str.split(' ')
            img_urls = [
                _sess_state["_conn"].get_public_url('indian_food', f"{code}.jpg")
                for code in fil_row[DB_FOOD_CODE_HEADER]
            ]
            fil_row["images"] = img_urls
        elif sel:
            sel_name = sel
            _sess_state["is_fil_row"] = True
            sel = fil_row.loc[fil_row[DB_FOOD_NAME_HEADER] == sel, DB_FOOD_CODE_HEADER].values[0]
            # food_id = query_with_filter_eq(
            #     return_columns="*",
            #     table=DB_TABLE_NAME,
            #     column=DB_FOOD_CODE_HEADER,
            #     value=sel
            # )
            # food_id = pd.Series(food_id.data[0], index=food_id.data[0].keys())

with st.container():
    tab1, tab2 = st.tabs(["Overview", "Details"])
    with tab1:
        view = st.empty()
        if "is_fil_row" in _sess_state and not _sess_state["is_fil_row"]:
            with view.container(height=450):
                # fil_row['tags'] = fil_row['tags'].str.split(' ')
                st.data_editor(
                    fil_row,
                    column_config={
                        "images": st.column_config.ImageColumn(
                            "Preview Image", help="Streamlit app preview screenshots"
                        ),
                        "tags": st.column_config.ListColumn(
                            "Diet Preferences", help="Dietary preferences for the food item"
                        )
                    },
                    hide_index=True,
                    use_container_width=True
                )

        if "is_fil_row" in _sess_state and _sess_state["is_fil_row"]:
            with view.container():
                img = fetch_image(f"{sel}")
                col1, col2 = view.columns(2, gap="large")
                col2.image(img, use_column_width=True, caption=f"Image of {sel_name.upper()}")
                # print(_sess_state['gjson'].keys(), _sess_state['gjson']["features"][0].keys())
                # print(_sess_state['gjson']["features"][0]["properties"]["NAME_0"].tolist())
                # print(pd.json_normalize(_sess_state['gjson']["features"]).columns)
                sel_lang = query_with_filter_eq(
                    return_columns="lang",
                    table=DB_TABLE_NAME,
                    column=DB_FOOD_CODE_HEADER,
                    value=sel
                )
                sel_lang: list[str] = sel_lang.data[0]["lang"].split(";")
                try:
                    assert sel_lang[0]
                    sel_lang_code = pd.DataFrame([lang.strip().split(' ', maxsplit=1) for lang in sel_lang], columns=["abbr", "name"])
                    df = pd.merge(sel_lang_code, _sess_state['indian_states'], left_on="abbr", right_on="abbr")
                    all_states = pd.json_normalize(_sess_state['gjson']["features"])["properties.ST_NM"]
                    fig = px.choropleth(
                        all_states,
                        geojson=_sess_state['gjson'],
                        locations="properties.ST_NM",
                        featureidkey="properties.ST_NM",
                        color_discrete_sequence=["lightgrey"],
                        labels={"properties.ST_NM": "State"}
                    )
                    fig.add_trace(go.Choropleth(
                            z=df["id"],
                            name=sel,
                            autocolorscale=False,
                            geojson=_sess_state['gjson'],
                            featureidkey="properties.ST_NM",
                            locations=df["state"],
                            locationmode="geojson-id",
                            customdata=df[["state", "lang", "name"]],
                            colorscale=px.colors.sequential.Inferno_r,
                            uid=f"{sel}",
                            hovertemplate="<br>".join(
                                [
                                    "<b>%{customdata[0]}</b><br>",
                                    "Language: %{customdata[1]}",
                                    "Known as: %{customdata[2]}",
                                ]
                            ),
                        )
                    )
                    is_nepal = sel_lang_code["abbr"].str.contains("N.")
                    if is_nepal.any():
                        fig.add_trace(
                            go.Choropleth(
                                z=[1],
                                customdata=pd.DataFrame({
                                    "state": ["Nepal"],
                                    "lang": "Nepali",
                                    "name": sel_lang_code.loc[is_nepal, "name"].values[0]
                                })[["state", "lang", "name"]],
                                autocolorscale=False,
                                reversescale=True,
                                showscale=False,
                                locationmode='ISO-3',
                                locations=['NPL'],
                                colorscale="greens",
                                hovertemplate="<br>".join(
                                    [
                                        "<b>%{customdata[0]}</b><br>",
                                        "Language: %{customdata[1]}",
                                        "Known as: %{customdata[2]}",
                                    ]
                                ),
                            )
                        )
                    fig.data[0]['name'] = "Toggle States"
                    # fig.data[0]['legendgrouptitle'] = dict(text="Toggle states")
                    fig.data[1]['colorbar']['x'] = 0.05
                    fig.data[1]['colorbar']['len'] = 0.9
                    fig.data[1]['colorbar']['y'] = 0.5
                    fig.data[1]["hoverlabel"]["bgcolor"] = "rgba(0, 0, 0, 0.9)"
                    fig.data[1]["hoverlabel"]["bordercolor"] = "white"
                    # )

                except AssertionError:
                    fig = px.choropleth(
                        locations=["IND"],
                        locationmode="ISO-3",
                        color=[1],
                        scope="asia",
                        fitbounds="locations",
                    )
                    fig.data[0]["name"] = sel
                    fig.data[0]["hovertemplate"] = f"<b>India</b><br>Language: English/Hindi<br>Known as: {sel_name}"
                fig.update_geos(fitbounds="locations", visible=False)
                fig.update_layout(geo=dict(bgcolor='rgba(14, 17, 20, 0.6)'))
                col1.plotly_chart(fig, use_container_width=True)
