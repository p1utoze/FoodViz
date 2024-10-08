import streamlit as st
import streamlit_antd_components as sac
from dotenv import load_dotenv
# from src.pages.comparer import run as comparer_run
from src.pages import home_run, comparer_run, search_run, viewer_run
# from src.pages.viewer import run as viewer_run
# from src.pages.search import run as search_run
from src.utils import SupabaseConnection

# Loads the environment variables
load_dotenv()

pages = {
    "Home": [home_run, 0, "house"],
    "View": [viewer_run, 1, "eye"],
    "Compare": [comparer_run, 2, "bar-chart-steps"],
    "Search": [search_run, 3, "search"],
}


def menu_callback():
    st.session_state.page_index = pages[st.session_state.tab_item][1]


if __name__ == "__main__":
    st.set_page_config(
        page_title="IFCT Food Database",
        page_icon="🍔",
        layout="wide",
    )
    
    # Set the page index to Home.
    if "page_index" not in st.session_state:
        st.session_state.page_index = 0

    # Initialize connection.
    if "_conn" not in st.session_state:
        st.session_state["_conn"] = st.connection("supabase", type=SupabaseConnection)

    st.markdown(
        """
        <style>
    .appview-container .main .block-container{{
            padding-top: {padding_top}rem;    }}
    </style>
    """.format(
            padding_top=1.5
        ),
        unsafe_allow_html=True,
    )
    sac.tabs(
        [sac.TabsItem(label=i, icon=pages[i][2]) for i in pages.keys()],
        variant="outline",
        index=st.session_state.page_index,
        use_container_width=True,
        on_change=menu_callback,
        key="tab_item",
    )
    try:
        pages[st.session_state.tab_item][0]()
    except Exception as e:
        st.error(f"Page '{st.session_state.tab_item}' not found.")
        st.error(f"Error: {e}")
