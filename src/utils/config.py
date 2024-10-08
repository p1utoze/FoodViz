from enum import Enum
from pathlib import Path

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


DB_TABLE_NAME = "food_ifct"
DB_FOOD_NAME_HEADER = "name"
DB_FOOD_CODE_HEADER = "code"
DB_SCI_NAME_HEADER = "scie"
DB_FOOD_TAGS_HEADER = "tags"

# Path: config.py
PROJECT_ROOT = Path(__file__).parent.parent

COLOR_MAP = {
    "CEREALS AND MILLETS": "#440154",
    "GRAIN LEGUMES": "#471466",
    "GREEN LEAFY VEGETABLES": "#472575",
    "OTHER VEGETABLES": "#453681",
    "FRUITS": "#3f4587",
    "ROOTS AND TUBERS": "#39558b",
    "CONDIMENTS AND SPICES": "#32628d",
    "NUTS AND OIL SEEDS": "#2c708e",
    "SUGARS": "#277c8e",
    "MUSHROOMS": "#22898d",
    "MISCELLANEOUS FOODS": "#1f968b",
    "MILK AND MILK PRODUCTS": "#1fa386",
    "EGG AND EGG PRODUCTS": "#29af7f",
    "POULTRY": "#3dbb74",
    "ANIMAL MEAT": "#55c666",
    "MARINE FISH": "#74d054",
    "MARINE SHELLFISH": "#95d73f",
    "MARINE MOLLUSKS": "#bade27",
    "FRESH WATER FISH AND SHELLFISH": "#dce218",
    "EDIBLE OILS AND FATS": "#fde724",
}


class PPADF(Enum):
    """Proximate Principles and Dietary Fibre."""

    WATER = "Water"
    ENERGY = "Energy"
    PROTEIN = "Protein"
    FAT = "Fat"
    CARBOHYDRATES = "Carbohydrates"
    FIBRE = "Fibre"
    ASH = "Ash"
    TOTAL = "Total"

    @classmethod
    def get_all(cls):
        return [i.value for i in cls]
