import json
import pandas as pd

FILE_OPCS = "data/naps/portugal/simulation/opcs.csv"


def set_connector_type(row):
    if "COMBO" in row.standard or "CHADEMO" in row.standard:
        return "DC"
    elif row.max_voltage >= 400:
        return "AC3"
    else:
        return "AC"


def set_connector_class(row):
    if row.TYPE.startswith("AC"):
        if row.max_electric_power < 7.4:
            return "AC Lento (P <7.4kW)"
        elif 7.4 <= row.max_electric_power <= 22:
            return "AC Médio (7.4 <= P <= 22kW)"
        else:
            return "AC Rápido (P > 22kW)"
    else:
        if row.max_electric_power < 50:
            return "DC Lento (P < 50kW)"
        elif 50 <= row.max_electric_power < 150:
            return "DC Rápido (50 <= P < 150kW)"
        elif 150 <= row.max_electric_power < 350:
            return "DC Ultra Rápido I (150 <= P < 350kW)"
        else:
            return "DC Ultra Rápido II (P >= 350kW)"


def load_connectors(file_locations):

    with open(file_locations, "r") as fp:
        locations = json.load(fp).get("data")
    
    opcs = pd.read_csv(FILE_OPCS, sep=";")[["party_id", "party_name"]]

    df = (
        pd
        .json_normalize(locations)
        .assign(network="MOBIE", mobie_voltage_level=lambda _: _.mobie_voltage_level.str[:2])
        .merge(opcs, how="left", on="party_id")
        .explode("evses")
        .assign(
            evse_id=lambda _: _.evses.str["evse_id"],
            connector=lambda _: _.evses.str["connectors"],
        )
        .explode("connector")
        .assign(
            standard=lambda _: _.connector.str["standard"],
            max_voltage=lambda _: _.connector.str["max_voltage"],
            max_amperage=lambda _: _.connector.str["max_amperage"],
            max_electric_power=lambda _: _.connector.str["max_electric_power"] / 1000,
        )

        .assign(
            idx_evse=lambda _: _.evse_id.str[-2:].str.split("*").str[-1].astype(int),
            idx_connector=lambda _: _.groupby("evse_id")["evse_id"].cumcount()+1,
        )

        .assign(
            TYPE=lambda _: _.apply(set_connector_type, axis=1),
            CLASS=lambda _: _.apply(set_connector_class, axis=1),
        )

    )
    return df



