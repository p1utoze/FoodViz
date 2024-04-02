import pandas as pd
import streamlit as st
from src import prepare_unit_data
from src.config import PROJECT_ROOT


def run():
    _sess_state = st.session_state

    if "units_data" not in _sess_state:
        path = PROJECT_ROOT / "data" / "units_with_e.csv"
        _sess_state["units_df"] = prepare_unit_data(path, "")
    if "tooltips" not in _sess_state:
        _sess_state["tooltips"] = {
            "mg": "Milligrams",
            "g": "Grams",
            "kg": "Kilograms",
            "ug": "Micrograms",
        }

    def get_food_code() -> list:
        ss = _sess_state["units_df"].loc[(_sess_state["units_df"]["name"].isin(_sess_state["nutrient"])), "code"]
        return ss[~ss.str.endswith("_e")].tolist()

    @st.cache_data(ttl=600)
    def get_nutrient_column(table: str, return_columns: str = "*", as_df: bool = True):
        return_columns = f"name, {return_columns}"
        response = _sess_state["_conn"].table(table).select(return_columns).execute()
        if as_df:
            return pd.DataFrame(response.data)
        return response.data

    st.header("📊 Nutrient Comparison Table Chart")

    st.multiselect(
        "Select Nutrient",
        _sess_state["units_df"].loc[_sess_state["units_df"]["type"].isin(["mass", "energy"]), "name"].unique(),
        key="nutrient",
        max_selections=10,
    )

    st.empty()
    if "nutrient" in _sess_state and _sess_state["nutrient"]:
        cols = get_food_code()
        response = get_nutrient_column("food_ifct", return_columns=",".join(cols))
        response.set_index("name", inplace=True)
        config = {}
        units = _sess_state["units_df"].loc[_sess_state["units_df"]["code"].isin(cols), "unit"].tolist()
        factors = _sess_state["units_df"].loc[_sess_state["units_df"]["code"].isin(cols), "factor"].tolist()

        for i in range(len(cols)):
            response[cols[i]] = response[cols[i]] * factors[i]
            config[cols[i]] = st.column_config.ProgressColumn(
                f"{_sess_state['nutrient'][i].upper()}",
                format=f"%.2f {units[i]}",
                help=f"Values in {_sess_state['tooltips'][units[i]]}",
                min_value=float(response[cols[i]].min()),
                max_value=float(response[cols[i]].max()),
            )

        st.dataframe(response, column_config=config, use_container_width=True, height=500)
