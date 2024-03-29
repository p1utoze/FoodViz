from pathlib import Path
from enum import Enum
DB_TABLE_NAME = 'food_ifct'
DB_FOOD_NAME_HEADER = 'name'
DB_FOOD_CODE_HEADER = 'code'
DB_SCI_NAME_HEADER = 'scie'
DB_FOOD_TAGS_HEADER = 'tags'

# Path: config.py
PROJECT_ROOT = Path(__file__).parent.parent


class PPADF(Enum):
    """
    Proximate Principles and Dietary Fibre
    """
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

