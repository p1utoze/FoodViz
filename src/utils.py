import streamlit as st
from abc import ABC, abstractmethod
from json import load
from pathlib import Path
from collections import OrderedDict
from pydantic import BaseModel, Field

GROUPS = Path(__file__).parent.parent / "data" / "food_groups.json"

def load_json(file_path: str = GROUPS) -> dict:
    with open(file_path, "r") as f:
        return OrderedDict(load(f))

class Page(ABC):
    @abstractmethod
    def write(self):
        pass


def add_custom_css():
    st.markdown(
        """
        <style>
        </style>
        """,
        unsafe_allow_html=True
    )