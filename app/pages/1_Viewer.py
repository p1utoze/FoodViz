from numpy import array as np_array
import streamlit as st
import pandas as pd

from postgrest import APIResponse
from src import SupabaseConnection
from src.utils import load_json
from src.config import DB_TABLE_NAME, DB_FOOD_NAME_HEADER, DB_FOOD_CODE_HEADER, DB_SCI_NAME_HEADER, PROJECT_ROOT
from PIL import Image

_sess_state = st.session_state

if "is_fil_row" in _sess_state:
    del st.session_state["is_fil_row"]

if "_conn" not in _sess_state:
    _sess_state["_conn"] = st.connection("supabase", type=SupabaseConnection)


@st.cache_data(show_spinner=False)
def fetch_image(file_name: str):
    _, _, image = _sess_state['_conn'].download(
        bucket_id="indian_food",
        source_path=file_name
    )
    res = image.read()
    return res


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

st.title("IFCT Food Database Overview 🚚")

with st.container(height=100):
    return_cols = f"{DB_FOOD_CODE_HEADER}, {DB_FOOD_NAME_HEADER}, {DB_SCI_NAME_HEADER}, tags"
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
        sel = col2.selectbox("Choose a food item: ", ["ALL"] + fil_row["food_code"].tolist(), index=None,  placeholder="Select a food item")
        if sel == 'ALL':
            _sess_state["is_fil_row"] = False
            fil_row['tags'] = fil_row['tags'].str.split(' ')
            img_urls = [
                _sess_state["_conn"].get_public_url('indian_food', f"{code}.jpeg")
                for code in fil_row["food_code"]
            ]
            fil_row["images"] = img_urls
        elif sel:
            _sess_state["is_fil_row"] = True
            food_id = query_with_filter_eq(
                return_columns="*",
                table=DB_TABLE_NAME,
                column=DB_FOOD_CODE_HEADER,
                value=sel
            )
            food_id = pd.Series(food_id.data[0], index=food_id.data[0].keys())



if "is_fil_row" in _sess_state and not _sess_state["is_fil_row"]:
    with st.container():
        # fil_row['tags'] = fil_row['tags'].str.split(' ')
        st.data_editor(
            fil_row,
            column_config={
                "images": st.column_config.ImageColumn(
                    "Preview Image", help="Streamlit app preview screenshots"
                )
            },
            hide_index=True,
            use_container_width=True
        )

if "is_fil_row" in _sess_state and _sess_state["is_fil_row"]:
    with st.container():
        img = fetch_image(f"{sel}.jpeg")
        print(type(img))
        st.image(img, width=300, caption='IFCT Food Database')
        col1, col2 = st.columns(2)
        col1.dataframe(food_id)
        # path = PROJECT_ROOT / "data" / "figures" / "fileoutpart1.png"
        # path = PROJECT_ROOT / "data" / "A001.jpeg"
        # img = Image.open(path)
        # col2.image(np_array(img), width=img.width, caption='IFCT Food Database')
