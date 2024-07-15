import io
import os
import urllib.request
from dataclasses import dataclass
import numpy as np
import pandas as pd

FILE_TAR = "data/naps/portugal/simulation/tar.csv"
FILE_CEMES = "data/naps/portugal/simulation/cemes.csv"


def load_tar(file=FILE_TAR, reload=False):
    url_csv = "https://docs.google.com/spreadsheets/d/1c1itP5vir1xZ9BkfJGehJyoEro6UhncgRw-fLw5m6MQ/export?format=tsv&id=1c1itP5vir1xZ9BkfJGehJyoEro6UhncgRw-fLw5m6MQ&gid=463183857"
    
    if not os.path.exists(file) or reload:

        with urllib.request.urlopen(url_csv) as f:
            data = f.read().decode('utf-8')
        df = pd.read_csv(io.StringIO(data), sep="\t", skiprows=3, decimal=",").iloc[:,:7]
        df.to_csv(file, index=False)
    
    df = (
        pd
        .read_csv(file)
        .drop(columns="Id")
        .rename(columns={
            "Calendário": "Calendario",
            "Tensão": "Tensao",
            "Ponta": "PONTA",
            "Cheias/Não Vazio": "FORA_VAZIO",
            "Vazio": "VAZIO",
        })
        .loc[lambda _: _.Tarifa != "1H"]
    )
    return df

def load_tariffs_ceme(file=FILE_CEMES, reload=False):
    url_csv = "https://docs.google.com/spreadsheets/d/1c1itP5vir1xZ9BkfJGehJyoEro6UhncgRw-fLw5m6MQ/export?format=tsv&id=1c1itP5vir1xZ9BkfJGehJyoEro6UhncgRw-fLw5m6MQ&gid=1552482801"
    
    if not os.path.exists(file) or reload:

        with urllib.request.urlopen(url_csv) as f:
            data = f.read().decode('utf-8')
        df = (
            pd
            .read_csv(io.StringIO(data), sep="\t", skiprows=3, decimal=",")
            .iloc[:, :18]
        )
        df.to_csv(file, index=False)
    
    df = (
        pd
        .read_csv(file)
        .assign(
            PONTA=lambda _: _[["Ponta (cTAR)", "Ponta (sTAR)"]].sum(axis=1),
            FORA_VAZIO=lambda _: _[["Cheias / Fora de Vazio (cTAR)", "Cheias / Fora de Vazio (sTAR)"]].sum(axis=1),
            VAZIO=lambda _: _[["Vazio (cTAR)", "Vazio (sTAR)"]].sum(axis=1),
        )
        .drop(columns=[
            'Ponta (cTAR)', 'Cheias / Fora de Vazio (cTAR)', 'Vazio (cTAR)', 'Ponta (sTAR)',
            'Cheias / Fora de Vazio (sTAR)', 'Vazio (sTAR)'
        ])
    )
    return df


def load_tariffs_opc(file):
    tariffs = (
        pd
        .read_csv(file, sep=";")
        .assign(
            # ID=lambda _: _.UID_TOMADA.str[:-2],
            idx_evse=lambda _: _.UID_TOMADA.str.split("-").str[-2].astype(int),
            idx_connector=lambda _: _.UID_TOMADA.str.split("-").str[-1].astype(int),
            # UID_EVSE=lambda _: _.UID_TOMADA.str.split("-").str[:-1].str.join("-"),
            TARIFA_VALOR=lambda _: _.TARIFA.str.extract(r'([-+]?\d*\.\d+|\d+)', False).astype(float),
            TEMPO_APOS=lambda _: _.TARIFA.str.split("após").str[1].str.extract(r'([-+]?\d*\.\d+|\d+)', False).astype(float).fillna(0),
            TEMPO_ATE=lambda _: _.TARIFA.str.split("até").str[1].str.extract(r'([-+]?\d*\.\d+|\d+)', False).astype(float).fillna(np.inf),

            MUNICIPIO=lambda _: _.MUNICIPIO.str.split(",").str[0],

        )
        .rename(columns={"ID": "id"})
        # .loc[lambda _: _.UID_TOMADA.str.split("-").str[3].astype(int) == 1]
    )
    meta = tariffs[["TIPO_POSTO", "MUNICIPIO", "MORADA", "OPERADOR", "MOBICHARGER", "NIVELTENSAO", "TIPO_TOMADA", "FORMATO_TOMADA", "POTENCIA_TOMADA"]]
    tariffs = tariffs.drop(columns=meta.columns)
    meta[["id", "idx_evse", "idx_connector"]] = tariffs[["id", "idx_evse", "idx_connector"]]
    meta = meta.drop_duplicates(subset=["id", "idx_evse", "idx_connector"])
    return tariffs, meta
