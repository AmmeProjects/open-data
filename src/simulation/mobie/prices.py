import numpy as np
from src.simulation.mobie.locations import set_connector_class, set_connector_type
from src.simulation.mobie.locations import load_connectors
from src.simulation.mobie.tariffs import load_tariffs_opc
from src.simulation.mobie.tariffs import load_tariffs_ceme
from src.simulation.mobie.tariffs import load_tar


class SimulatePricesMobie:
    
    def __init__(
            self,
            path_connectors: str,
            path_tariffs: str,
            fee_egme_opc: float,
            fee_egme_ceme: float,
            iec: float,
            vat: float,
        ) -> None:
        self.path_connectors = path_connectors
        self.path_tariffs = path_tariffs
        self.vehicle = None
        self.connectors = None
        self.tariffs = None
        self.meta = None
        self.estimate_opc = None
        self.estimate_ceme = None
        self.cemes = None
        self._tar = None
        self._egme_opc = fee_egme_opc
        self._egme_ceme = fee_egme_ceme
        self._iec = iec
        self._vat = vat

    def load_connectors(self):
        connectors = load_connectors(self.path_connectors)
        connectors = (
            connectors[["id", "party_id", "idx_evse", "idx_connector", "mobie_voltage_level", "evse_id", "standard", "max_voltage", "max_amperage", "max_electric_power"]]

            .assign(
                UID_EVSE=lambda _: _.evse_id.str.split("*").str[-3:].str.join("-"),
                TYPE=lambda _: _.apply(set_connector_type, axis=1),
                CLASS=lambda _: _.apply(set_connector_class, axis=1),
            )
        )
        self.connectors = connectors

    def load_opc_tariffs(self):
        tariffs, meta = load_tariffs_opc(self.path_tariffs)
        # clean
        tariffs = tariffs.drop_duplicates(["UID_TOMADA", "TIPO_TARIFA", "TEMPO_APOS"], keep="first")
        self.tariffs = tariffs
        self.meta = meta

    def load_tariffs_ceme(self):
        self._tar = (
            load_tar()
            .loc[lambda _: (_["Calendario"] == _["Calendario"].max())]
            .drop(columns=["Calendario", "PONTA"])
            .melt(["Tarifa", "Tensao"], var_name="Ciclo", value_name="TAR")
            .set_index(["Tarifa", "Tensao", "Ciclo"])
            .loc["2H"]

        )
        self.cemes = load_tariffs_ceme()
    
    def set_vehicle(self, vehicle):
        self.vehicle = vehicle

    def add_vehicle_params(self, dsoc=0.7):
        veh_ac3_amps = self.vehicle["ac3_amps"]
        veh_ac_amps = self.vehicle["ac_amps"]
        veh_cap = self.vehicle["max_cap"] * dsoc
        veh_nom_voltage = self.vehicle["nominal_voltage"]
        veh_avg_pwr = self.vehicle["avg_pwr_10_80"]

        connectors = (
            self
            .connectors
            .copy()
            .assign(
                PWR=lambda _: (_.max_amperage * veh_nom_voltage / 1000).clip(upper=veh_avg_pwr).clip(upper=_.max_electric_power).where(_.TYPE == "DC"),
            )
            .assign(
                PWR=lambda _: (230 * 3 * _.max_amperage.clip(upper=veh_ac3_amps) / 1000).where(_.TYPE == "AC3", _.PWR),
            )
            .assign(
                PWR=lambda _: (230 * _.max_amperage.clip(upper=veh_ac_amps) / 1000).where(_.TYPE == "AC", _.PWR),
                ENERGY=lambda _: veh_cap,
                TIME=lambda _: (_.ENERGY / _.PWR * 60).pipe(np.ceil),
            )
        )
        self.connectors = connectors

    def estimate_opc_cost(self, time_factor=1.0):
        connectors = self.connectors
        tariffs = self.tariffs
        merged = (
            connectors
            .merge(tariffs, on=["id", "idx_evse", "idx_connector"])
            .assign(
                COST_OPC_TIME=lambda _: (_.TIME - _.TEMPO_APOS).clip(lower=0).where(_.TIPO_TARIFA == "TIME").fillna(0) * _.TARIFA_VALOR * time_factor,
                COST_OPC_ENERGY=lambda _: (_.ENERGY * _.TARIFA_VALOR).where(_.TIPO_TARIFA == "ENERGY").fillna(0),
                COST_OPC_FLAT=lambda _: _.TARIFA_VALOR.where(_.TIPO_TARIFA == "FLAT").fillna(0),
            )
        )


        merged = (
            merged
            .groupby(["id", "idx_evse", "idx_connector"]).agg(
                COST_OPC_TIME=("COST_OPC_TIME", "sum"),
                COST_OPC_ENERGY=("COST_OPC_ENERGY", "sum"),
                COST_OPC_FLAT=("COST_OPC_FLAT", "sum"),
            )
            .assign(
                COST_OPC_FLAT=lambda _: _.COST_OPC_FLAT - self._egme_opc,
                COST_OPC_EGME=self._egme_opc,
            )
        )
        
        self.estimate_opc = self.connectors.merge(merged, on=["id", "idx_evse", "idx_connector"])

    def estimate_ceme_cost(self, w_vazio=.0):
        _tar = self._tar
        
        costs = (
            self.cemes
            .assign(
                COST_CEME_FLAT=lambda _: _["Ativacao"],
                COST_TAX_IEC_ENERGY_UNIT=self._iec,
                
                COST_CEME_EGME=lambda _: (1 - _["Inclui EGME"]) * self._egme_ceme,
                COST_CEME_ENERGY_UNIT_BT=lambda _: 
                w_vazio * (_.VAZIO + (1-_["Inclui TAR"]) * _tar.loc[("BT", "VAZIO")].iat[0]) +
                (1-w_vazio) * (_.FORA_VAZIO + (1-_["Inclui TAR"]) * _tar.loc[("BT", "FORA_VAZIO")].iat[0]),

                COST_CEME_ENERGY_UNIT_MT=lambda _: 
                w_vazio * (_.VAZIO + (1-_["Inclui TAR"]) * _tar.loc[("MT", "VAZIO")].iat[0]) +
                (1-w_vazio) * (_.FORA_VAZIO + (1-_["Inclui TAR"]) * _tar.loc[("MT", "FORA_VAZIO")].iat[0]),
            )
            .loc[:, lambda _: ["CEME | CONTRATO", "Condicionantes"] + [c for c in _.columns if c.startswith("COST_")]]
        )
        self.estimate_ceme = costs

