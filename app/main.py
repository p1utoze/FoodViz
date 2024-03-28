import streamlit as st
from src import SupabaseConnection
from src.utils import add_custom_css
# from src.state import provide_state

st.set_page_config(
    page_title="IFCT Food Database",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize connection.
if "_conn" not in st.session_state:
    st.session_state._conn = st.connection("supabase", type=SupabaseConnection)




st.write("Hello, world!")