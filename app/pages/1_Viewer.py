import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


from src import (
    SupabaseConnection,
    prepare_indian_geojson,
    prepare_indian_languages,
    prepare_unit_data
)
from src.utils import load_json
from src.config import (
    DB_TABLE_NAME,
    DB_FOOD_NAME_HEADER,
    DB_FOOD_CODE_HEADER,
    DB_SCI_NAME_HEADER,
    PROJECT_ROOT,
    DB_FOOD_TAGS_HEADER
)

st.markdown(
    """
    <style>
.appview-container .main .block-container{{
        padding-top: {padding_top}rem;    }}
</style>
""".format(padding_top=0.5),
    unsafe_allow_html=True,
)

_sess_state = st.session_state

if "is_fil_row" in _sess_state:
    del st.session_state["is_fil_row"]

if "_conn" not in _sess_state:
    _sess_state["_conn"] = st.connection("supabase", type=SupabaseConnection)

if 'gjson' not in _sess_state:
    _sess_state['gjson'] = prepare_indian_geojson()

if 'indian_states' not in _sess_state:
    _sess_state['indian_states'] = prepare_indian_languages()

if "units" not in _sess_state:
    path = PROJECT_ROOT / "data" / "units_with_e.csv"
    _sess_state["units"] = prepare_unit_data(path)

if "fg" not in _sess_state:
    _sess_state["fg"] = load_json()

if "selected_code" not in _sess_state:
    _sess_state["selected_code"] = None

if "visibility" not in st.session_state:
    _sess_state.disabled = True

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


st.header("IFCT Food Database Overview 🚚")


tab1, tab2 = st.tabs(["Overview", "Details"])
with tab1:
    with st.container(height=100):
        return_cols = f"{DB_FOOD_CODE_HEADER}, {DB_FOOD_NAME_HEADER}, {DB_SCI_NAME_HEADER}, {DB_FOOD_TAGS_HEADER}"
        col1, col2 = st.columns(2, gap="large")
        grp_name = col1.selectbox("Choose a food group: ", _sess_state["fg"].keys(), index=None,
                                  placeholder="Select a food group")
        if grp_name:
            fil_row = query_with_filter_like(
                return_columns=return_cols,
                table=DB_TABLE_NAME,
                column=DB_FOOD_CODE_HEADER,
                value=_sess_state["fg"][grp_name]
            )
            fil_row = pd.DataFrame(fil_row.data)
            sel = col2.selectbox("Choose a food item: ", ["ALL"] + fil_row[DB_FOOD_NAME_HEADER].tolist(), index=None,
                                 placeholder="Select a food item")
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
                _sess_state["disabled"] = False
                _sess_state["is_fil_row"] = True
                sel = fil_row.loc[fil_row[DB_FOOD_NAME_HEADER] == sel, DB_FOOD_CODE_HEADER].values[0]
                _sess_state["selected_code"] = sel

        else:
            _sess_state["selected_code"] = None

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
        with view.container(height=600):
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
                    labels={"properties.ST_NM": "State"},
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
                # fig.data[1]['colorbar']['x'] = 0.05
                fig.data[1]['colorbar']['len'] = 0.6
                fig.data[1]['colorbar']['y'] = 0.5
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
                geo=dict(bgcolor='rgba(14, 17, 20, 0.1)'),
                margin=dict(l=0, r=0, t=0, b=0),
                height=350,
                title=dict(text=f"Regional language distribution of {sel_name}", xanchor="center", x=0.5, xref='paper', yanchor="bottom", y=0.1, font_size=12, font_color="grey"),
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, font_size=15),
                modebar=dict(orientation='h', bgcolor=st._config.get_option('theme.backgroundColor'), color=st._config.get_option('theme.primaryColor')),
            )

            fig.update_mapboxes(domain=dict(x=[0, 0.5], y=[0, 1]))
            col1.plotly_chart(fig, use_container_width=True)


with tab2:
    with tab2.container(height=100):
        base_cols = [DB_FOOD_CODE_HEADER, DB_FOOD_NAME_HEADER, DB_SCI_NAME_HEADER, DB_FOOD_TAGS_HEADER]
        comp_name = st.selectbox(
            "Choose a food composition category: ",
            _sess_state["units"]["table_name"].dropna().unique(),
            index=None,
            placeholder="Select a food composition category",
            disabled=_sess_state.disabled
        )

    print(_sess_state["selected_code"])
    if _sess_state["selected_code"]:
        if comp_name:
            with st.container(height=450):
                cts = [st.container(height=175) for _ in range(2)]
                for c in cts:
                    with c:
                        st.write("This is a container")
                        cols = st.columns(7)
                        for i, col in enumerate(cols):
                            with col:
                                st.metric(label=f"Metric {i}", value=i, delta=i/10, delta_color="off")

    else:
        st.warning("Please select a food item from the Overview tab to view its composition details.")