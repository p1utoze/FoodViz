import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from src.utils.helpers import load_bubble_data
from src.utils.config import PROJECT_ROOT

custom_chart = Path(__file__).parent / "frontend" / "bubble.html"
chart_data = PROJECT_ROOT / "data" / "food-types.csv"

def run():
    empty = st.empty()
    with empty.container():
        col1, col2 = st.columns([1, 1])
        col1.markdown(
            """
            <h1 style="font-size: 4.5em; font-weight: bold; color: #e63946;">FoodViz</h1>
            <h3 style="font-size: 2.5em; color: #a8dadc;">Interactive Food Composition Explorer</h3>
            """,
            unsafe_allow_html=True,
        )
        with open(custom_chart.absolute(), "r") as f:
            canvas = f.read()

        with col2:
            components.html(canvas, height=400, width=600)
        # col2.image(
        #     "https://img.freepik.com/premium-photo/different-types-meats-vegetables-fruits-lay-"
        #     "supermarkets-generative-ai_572887-4418.jpg",
        #     use_column_width=True,
        # )

    st.divider()

    with st.container():
        cphrase = "Are you a Gym freak or a Health enthusiast?"
        cphrase_sub = (
            "Either way, you are at the right place! Explore the food composition of your favourite indian meals."
        )
        st.markdown(
            f"""
            <h2 style="font-size: 2.5em; font-weight: bold; text-align: center; color: #457b9d">{cphrase}</h2>
            <h5 style="font-size: 1.5em; text-align: center;">{cphrase_sub}</h5>
            """,
            unsafe_allow_html=True,
        )
        st.divider()
        st.markdown(
            """
            I have created this web app to help you find all the food related sources.
            The explorer is based on the Indian Food Composition Table (IFCT) database which is a comprehensive database
            consisting of **:blue[542 food items]**
            My goal is to provide you with a simple and interactive way to discover and compare the nutritional contents
            and values of different food items.

            **:orange[The Indian Food Composition Table]** (IFCT) is a comprehensive database consisting of 542 food
            items. The database provides information on the proximate principles and dietary fibre content of Indian
            foods. The database is useful for nutritionists, dieticians, and health professionals for planning and
            assessing diets.
            """
        )
        st.divider()
        st.subheader("How to use the explorer?")
        st.markdown(
            """
            The explorer is divided into two main sections:
            #### 👁‍🗨️ Viewer Page:
            - :blue[**Overview**]: This tab provides a brief overview of the food item categorized by food groups.
            - :blue[**Details**]: This tab provides detailed nutritional information about the selected food item's
            various food compositions.
            #### 📊 Comparison Page
            """
        )
