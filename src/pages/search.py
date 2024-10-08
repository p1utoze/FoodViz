import streamlit as st
from streamlit_card import card
from src.utils import load_retriever, generate_color_range
from src.utils.config import PROJECT_ROOT

start_green = (0, 255, 0)
end_red = (255, 0, 0)


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
        .row-gradient {
            background: linear-gradient(to right, #ff7f50, #ffa500);
            padding: 10px;
            margin-bottom: 5px;
            color: white;
        }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)
    _sess_state = st.session_state

    if "_conn" not in _sess_state:
        st.error("Please connect to the database first.")
        return

    if "retriever" not in _sess_state:
        data_store_path = PROJECT_ROOT / "data" / "context_storage"
        _sess_state.retriever = load_retriever(data_store_path)

    if "color_range" not in _sess_state:
        _sess_state.color_range = generate_color_range(start_green, end_red, 5)

    # Load and preprocess the data

    # Define the search function
    @st.cache_data(ttl=600)
    def retrieve_top_matches_callback(query: str):
        return _sess_state.retriever.retrieve(query)

    # Streamlit app
    st.title("Optimized Local Language Food Search")

    # Use a container for dynamic updates
    search_container = st.empty()

    # Create a text input for search
    search_query = search_container.text_input(
        "Enter a food name in your local language",
    )
    if "idx" not in _sess_state:
        _sess_state.idx = -1

    # Perform search as user types
    st.write("Top matches for the search query:")
    if search_query:
        nodes = retrieve_top_matches_callback(search_query)
        node_len = len(nodes)
        container = st.empty()
        for i in range(node_len):
            idx = node_len - i - 1
            card(
                title=f"{nodes[idx].text}",
                text=f"Name: {nodes[idx].metadata['name']}  |   Scientific Name: {nodes[idx].metadata['scientific_name']}   |   Local Language: {nodes[idx].metadata['lang']} | Score: {nodes[idx].score}",
                key=f"card_{idx}",
                on_click=lambda: _sess_state.update({"idx": idx}),
                styles={
                    "card": {
                        "width": "100%",
                        "background-color": f"{_sess_state.color_range[i]}",
                        "height": "100px",
                        "border-radius": "15px",
                        "box-shadow": "0 0 10px rgba(0,0,0,0.5)",
                        "padding": "0px",
                        "margin": "0px"
                    }
                },

            )

        # TODO: Create a sidebar that displays some information about the selected node
        # st.write(f"Selected index: {_sess_state.idx}, Selected node: {nodes[_sess_state.idx].text}")
    # Add some information about the search engine
    st.sidebar.title("About")
    st.sidebar.info(
        "This optimized search engine allows you to find food items by their local language names. "
        "It searches through various Indian languages and returns the top matches "
        "for the common name and scientific name of the food item. "
        "The search updates as you type for a more interactive experience."
    )

    # # Display some statistics
    # st.sidebar.title("Statistics")
    # st.sidebar.write(f"Total number of unique local names: {len(name_dict)}")
