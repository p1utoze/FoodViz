import pandas as pd
import streamlit as st
from plotly import express as px, graph_objects as go
from src.utils import (
    prepare_indian_geojson,
    prepare_indian_languages,
    prepare_unit_data,
)
from src.utils.config import (
    DB_FOOD_CODE_HEADER,
    DB_FOOD_NAME_HEADER,
    DB_FOOD_TAGS_HEADER,
    DB_SCI_NAME_HEADER,
    DB_TABLE_NAME,
    PROJECT_ROOT,
)
from src.utils.config import load_json


def run():
    css = """
    <style>
        [data-testid="stMetricDelta"] svg {
            display: none;
        }
        [data-testid="stMetricDelta"] > div::before {
            content:"±";
            font-weight: bold;
            font-size: 1.3rem;
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

    _sess_state = st.session_state

    if "is_fil_row" in _sess_state:
        del st.session_state["is_fil_row"]

    if "gjson" not in _sess_state:
        _sess_state["gjson"] = prepare_indian_geojson()

    if "indian_states" not in _sess_state:
        _sess_state["indian_states"] = prepare_indian_languages()

    if "units_df" not in _sess_state:
        path = PROJECT_ROOT / "data" / "units_with_e.csv"
        _sess_state["units_df"] = prepare_unit_data(path)

    if "fg" not in _sess_state:
        _sess_state["fg"] = load_json()

    if "selected_code" not in _sess_state:
        _sess_state["selected_code"] = None

    if "disable" not in st.session_state:
        _sess_state["disabled"] = True

    if "comp_name" not in _sess_state:
        _sess_state["comp_name"] = None

    @st.cache_data()
    def fetch_image(file_name: str):
        # _, _, image = _sess_state['_conn'].download(
        #     bucket_id="indian_food",
        #     source_path=file_name
        # )
        url = _sess_state["_conn"].get_public_url("indian_food", f"{file_name}.jpg")
        # res = image.read()
        return url

    @st.cache_data(ttl=600)
    def query_with_filter_like(table: str, column: str, value: str, return_columns: str = "*", as_df: bool = True):
        response = _sess_state["_conn"].table(table).select(return_columns).like(column, f"{value}%25").execute()
        if as_df:
            return pd.DataFrame(response.data)
        return response.data

    @st.cache_data(ttl=600)
    def query_with_filter_eq(table: str, column: str, value: str, return_columns: str = "*", as_df: bool = True):
        response = _sess_state["_conn"].table(table).select(return_columns).eq(column, value).execute()
        if as_df:
            return pd.DataFrame(response.data)
        return response.data

    def tab1_box1_callback():
        _sess_state["comp_name"] = None

    st.header("🚚 IFCT Food Database Overview")
    st.markdown("Choose the food group and food item from the dropdown to view the basic info of the food item. 👇")

    tab1, tab2 = st.tabs(["🍽 Overview", "🔢 Nutritional Details"])
    with tab1:
        with st.container(height=100):
            return_cols = f"{DB_FOOD_CODE_HEADER}, {DB_FOOD_NAME_HEADER}, {DB_SCI_NAME_HEADER}, {DB_FOOD_TAGS_HEADER}"
            col1, col2 = st.columns(2, gap="large")
            grp_name = col1.selectbox(
                "Choose a food group: ",
                _sess_state["fg"].keys(),
                index=None,
                placeholder="Select a food group",
                on_change=tab1_box1_callback,
            )
            if grp_name:
                fil_row = query_with_filter_like(
                    return_columns=return_cols,
                    table=DB_TABLE_NAME,
                    column=DB_FOOD_CODE_HEADER,
                    value=_sess_state["fg"][grp_name],
                )
                # fil_row = pd.DataFrame(fil_row.data)
                sel = col2.selectbox(
                    "Choose a food item: ",
                    ["ALL"] + fil_row[DB_FOOD_NAME_HEADER].tolist(),
                    index=None,
                    placeholder="Select a food item",
                )
                if sel == "ALL":
                    _sess_state["is_fil_row"] = False
                    fil_row[DB_FOOD_TAGS_HEADER] = fil_row[DB_FOOD_TAGS_HEADER].str.split(" ")
                    img_urls = [
                        _sess_state["_conn"].get_public_url("indian_food", f"{code}.jpg")
                        for code in fil_row[DB_FOOD_CODE_HEADER]
                    ]
                    fil_row["images"] = img_urls
                elif sel:
                    sel_name = sel
                    _sess_state["disabled"] = False

                    _sess_state["is_fil_row"] = True
                    sel = fil_row.loc[fil_row[DB_FOOD_NAME_HEADER] == sel, DB_FOOD_CODE_HEADER].values[0]
                    _sess_state["selected_code"] = sel
            else:
                _sess_state["selected_code"] = None

        view = st.empty()
        if "is_fil_row" in _sess_state and not _sess_state["is_fil_row"]:
            st.data_editor(
                fil_row,
                column_config={
                    "images": st.column_config.ImageColumn("Preview Image", help="Streamlit app preview screenshots"),
                    "tags": st.column_config.ListColumn(
                        "Diet Preferences", help="Dietary preferences for the food item"
                    ),
                },
                hide_index=True,
                use_container_width=True,
            )

        if "is_fil_row" in _sess_state and _sess_state["is_fil_row"]:
            with view.container(height=600):
                img = fetch_image(f"{sel}")
                col1, col2 = view.columns(2, gap="large")
                col2.image(img, use_column_width=True, caption=f"Image of {sel_name.upper()}")
                sel_lang = query_with_filter_eq(
                    return_columns="lang", table=DB_TABLE_NAME, column=DB_FOOD_CODE_HEADER, value=sel, as_df=False
                )
                sel_lang: list[str] = sel_lang[0]["lang"].split(";")
                try:
                    _ = sel_lang[0]
                    sel_lang_code = pd.DataFrame(
                        [lang.strip().split(" ", maxsplit=1) for lang in sel_lang], columns=["abbr", "name"]
                    )
                    df = pd.merge(sel_lang_code, _sess_state["indian_states"], left_on="abbr", right_on="abbr")
                    all_states = pd.json_normalize(_sess_state["gjson"]["features"])["properties.ST_NM"]
                    fig = px.choropleth(
                        all_states,
                        geojson=_sess_state["gjson"],
                        locations="properties.ST_NM",
                        featureidkey="properties.ST_NM",
                        color_discrete_sequence=["lightgrey"],
                        labels={"properties.ST_NM": "State"},
                    )
                    fig.add_trace(
                        go.Choropleth(
                            z=df["id"],
                            name=sel,
                            autocolorscale=False,
                            geojson=_sess_state["gjson"],
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
                                customdata=pd.DataFrame(
                                    {
                                        "state": ["Nepal"],
                                        "lang": "Nepali",
                                        "name": sel_lang_code.loc[is_nepal, "name"].values[0],
                                    }
                                )[["state", "lang", "name"]],
                                autocolorscale=False,
                                reversescale=True,
                                showscale=False,
                                locationmode="ISO-3",
                                locations=["NPL"],
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
                    fig.data[0]["name"] = "Toggle States"
                    fig.data[1]["colorbar"]["len"] = 0.6
                    fig.data[1]["colorbar"]["y"] = 0.5
                    fig.data[1]["hoverlabel"]["bgcolor"] = "rgba(0, 0, 0, 0.9)"
                    fig.data[1]["hoverlabel"]["bordercolor"] = "white"

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

                fig.update_layout(
                    geo=dict(bgcolor="rgba(14, 17, 20, 0.1)"),
                    margin=dict(l=0, r=0, t=0, b=0),
                    height=350,
                    title=dict(
                        text=f"Regional language distribution of {sel_name}",
                        xanchor="center",
                        x=0.5,
                        xref="paper",
                        yanchor="bottom",
                        y=0.1,
                        font_size=12,
                        font_color="grey",
                    ),
                    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, font_size=15),
                    modebar=dict(
                        orientation="h",
                        bgcolor=st._config.get_option("theme.backgroundColor"),
                        color=st._config.get_option("theme.primaryColor"),
                    ),
                )

                fig.update_mapboxes(domain=dict(x=[0, 0.5], y=[0, 1]))
                col1.plotly_chart(fig, use_container_width=True)

    with tab2:
        with tab2.container(height=100):
            st.selectbox(
                "Choose a food composition category: ",
                _sess_state["units_df"]["table_name"].dropna().unique(),
                index=None,
                key="comp_name",
                placeholder="Select a food composition category",
                disabled=_sess_state.disabled,
            )

        if _sess_state["disabled"]:
            st.warning("Please select a food item from the Overview tab to view its composition details.")

        if _sess_state["selected_code"]:
            food_item_df = query_with_filter_eq(
                return_columns="*", table=DB_TABLE_NAME, column=DB_FOOD_CODE_HEADER, value=_sess_state["selected_code"]
            )
            food_item_df = food_item_df.T.reset_index()
            food_item_df.columns = ["code", "value"]
            if _sess_state["comp_name"]:
                cards = pd.merge(
                    _sess_state["units_df"].loc[_sess_state["units_df"]["table_name"] == _sess_state["comp_name"]],
                    food_item_df,
                    left_on="code",
                    right_on="code",
                    how="inner",
                )
                cards["value"] = cards["value"].astype(float)
                cards = cards.loc[cards["value"] != 0, :]
                card_elements = cards.shape[0]
                if not card_elements:
                    st.info("No data available for the selected food composition. :red[Please Select different one.]")
                    st.stop()

                condition = cards["code"].str.endswith("_e")
                item_indexes = cards.loc[~condition, :].index.tolist()
                item_index_c, row_size = 0, 4
                metric_containers = [st.container(height=175) for _ in range((len(item_indexes) - 1) // row_size + 1)]
                for container in metric_containers:
                    with container:
                        columns = st.columns(row_size)
                        for col in columns:
                            try:
                                current_index = item_indexes[item_index_c]
                                measurement_unit = cards.at[current_index, "unit"]
                                factor = cards.at[current_index, "factor"]
                            except IndexError:
                                break

                            if _sess_state["selected_code"].startswith("T"):
                                measurement_unit = "%"
                                factor = 1

                            with col:
                                try:
                                    delta_val = cards.at[current_index + 1, "value"] * factor
                                    delta = f"{delta_val:.5f} {measurement_unit}"
                                    delta_color = "normal"
                                except KeyError:
                                    delta = f"Nil {measurement_unit}"
                                    delta_color = "off"

                                st.metric(
                                    label=cards.at[current_index, "name"],
                                    value=f"{cards.at[current_index, 'value'] * factor:.5f} {measurement_unit}",
                                    delta=delta,
                                    delta_color=delta_color,
                                )
                                item_index_c += 1
