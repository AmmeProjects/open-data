"""
Parser for Mobie Portugal tariff data.

Handles complex tariff structures including:
- Multiple tariff components (FLAT, ENERGY, TIME, PARKING_TIME)
- Tariff types (REGULAR vs AD_HOC_PAYMENT)
- Tiered pricing (different rates based on time thresholds)
"""

import re
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from sim.models.tariff import Tariff


@dataclass
class TieredRate:
    """
    Represents a tiered pricing rate.

    For example:
    - €0.12/min up to 45 minutes
    - €0.15/min after 45 minutes
    """

    rate: float
    threshold_minutes: Optional[float] = (
        None  # None means no threshold (applies to all)
    )
    is_before_threshold: bool = True  # True: "até", False: "após"

    def applies_at_time(self, minutes: float) -> bool:
        """Check if this rate applies at a given time."""
        if self.threshold_minutes is None:
            return True

        if self.is_before_threshold:
            return minutes <= self.threshold_minutes
        else:
            return minutes > self.threshold_minutes

    @classmethod
    def from_string(cls, tariff_str: str) -> "TieredRate":
        """
        Parse tiered rate from string.

        Examples:
        - "€ 0.12 /min até 45 min" -> TieredRate(0.12, 45, True)
        - "€ 0.15 /min após 45 min" -> TieredRate(0.15, 45, False)
        - "€ 0.03 /min" -> TieredRate(0.03, None, True)
        """
        # Extract rate
        rate_match = re.search(r"€\s*([\d,\.]+)", tariff_str)
        if not rate_match:
            return cls(0.0)

        rate = float(rate_match.group(1).replace(",", "."))

        # Check for threshold
        threshold = None
        is_before = True

        if "até" in tariff_str:
            is_before = True
            threshold_match = re.search(r"até\s+([\d,\.]+)\s*min", tariff_str)
            if threshold_match:
                threshold = float(threshold_match.group(1).replace(",", "."))
        elif "após" in tariff_str:
            is_before = False
            threshold_match = re.search(r"após\s+([\d,\.]+)\s*min", tariff_str)
            if threshold_match:
                threshold = float(threshold_match.group(1).replace(",", "."))

        return cls(rate, threshold, is_before)


@dataclass
class ParsedTariff:
    """
    Complete parsed tariff information for a connector.

    May contain multiple tariff types (REGULAR and AD_HOC_PAYMENT).
    """

    uid: str
    operator: str
    charger_type: str  # Lento, Médio, Rápido, Ultrarrápido
    connector_type: str  # MENNEKES, CCS, CHADEMO, etc.
    power_kw: float
    location: str

    # REGULAR tariff (for subscribers/members)
    regular_flat: float = 0.0
    regular_energy: float = 0.0
    regular_time: List[TieredRate] = None
    regular_parking_time: float = 0.0

    # AD_HOC_PAYMENT tariff (for casual users)
    adhoc_flat: float = 0.0
    adhoc_energy: float = 0.0
    adhoc_time: List[TieredRate] = None
    adhoc_parking_time: float = 0.0

    def __post_init__(self):
        """Initialize tiered rate lists if None."""
        if self.regular_time is None:
            self.regular_time = []
        if self.adhoc_time is None:
            self.adhoc_time = []

    def to_tariff(self, tariff_type: str = "REGULAR") -> Tariff:
        """
        Convert to simple Tariff model.

        Args:
            tariff_type: Either 'REGULAR' or 'AD_HOC_PAYMENT'

        Returns:
            Tariff instance (note: tiered pricing is simplified to single rate)
        """
        if tariff_type == "REGULAR":
            # For tiered rates, use the first tier rate
            time_rate = self.regular_time[0].rate if self.regular_time else 0.0

            return Tariff(
                id=f"{self.uid}|REGULAR",
                operator=self.operator,
                flat_fee=self.regular_flat,
                energy_rate=self.regular_energy,
                time_rate=time_rate,
                parking_rate=self.regular_parking_time,
                currency="EUR",
            )
        else:  # AD_HOC_PAYMENT
            time_rate = self.adhoc_time[0].rate if self.adhoc_time else 0.0

            return Tariff(
                id=f"{self.uid}|AD_HOC",
                operator=self.operator,
                flat_fee=self.adhoc_flat,
                energy_rate=self.adhoc_energy,
                time_rate=time_rate,
                parking_rate=self.adhoc_parking_time,
                currency="EUR",
            )

    def has_tiered_pricing(self) -> bool:
        """Check if this tariff has any tiered pricing."""
        return len(self.regular_time) > 1 or len(self.adhoc_time) > 1

    def calculate_time_cost(
        self, minutes: float, tariff_type: str = "REGULAR"
    ) -> float:
        """
        Calculate time-based cost handling tiered pricing.

        Args:
            minutes: Total charging time in minutes
            tariff_type: Either 'REGULAR' or 'AD_HOC_PAYMENT'

        Returns:
            Total time-based cost
        """
        rates = self.regular_time if tariff_type == "REGULAR" else self.adhoc_time

        if not rates:
            return 0.0

        # If only one rate (no tiers), simple multiplication
        if len(rates) == 1:
            return rates[0].rate * minutes

        # Handle tiered pricing
        # Sort rates by threshold
        sorted_rates = sorted(
            rates,
            key=lambda r: (
                r.threshold_minutes or float("inf"),
                not r.is_before_threshold,
            ),
        )

        total_cost = 0.0
        remaining_minutes = minutes

        # Find threshold rates (before) and after rates
        before_rates = [
            r
            for r in sorted_rates
            if r.is_before_threshold and r.threshold_minutes is not None
        ]
        after_rates = [
            r
            for r in sorted_rates
            if not r.is_before_threshold and r.threshold_minutes is not None
        ]

        if before_rates:
            # There's a threshold, apply before rate up to threshold
            threshold = before_rates[0].threshold_minutes
            before_rate = before_rates[0].rate

            if minutes <= threshold:
                # Entire session is within threshold
                total_cost = before_rate * minutes
            else:
                # Session exceeds threshold
                total_cost = before_rate * threshold
                remaining_minutes = minutes - threshold

                # Apply after rate to remaining time
                if after_rates:
                    after_rate = after_rates[0].rate
                    total_cost += after_rate * remaining_minutes
                else:
                    # No explicit after rate, use before rate
                    total_cost += before_rate * remaining_minutes
        else:
            # No threshold, use first rate
            total_cost = sorted_rates[0].rate * minutes

        return total_cost


class MobieTariffParser:
    """Parser for Mobie Portugal tariff CSV data."""

    @staticmethod
    def parse_rate(tariff_str: str) -> float:
        """
        Extract numeric rate from tariff string.

        Args:
            tariff_str: String like "€ 0.261 /charge" or "€ 0.1 /kWh"

        Returns:
            Parsed rate as float, 0.0 if parsing fails
        """
        if pd.isna(tariff_str):
            return 0.0

        match = re.search(r"€\s*([\d,\.]+)", str(tariff_str))
        if match:
            return float(match.group(1).replace(",", "."))
        return 0.0

    @staticmethod
    def is_tiered(tariff_str: str) -> bool:
        """Check if tariff string indicates tiered pricing."""
        if pd.isna(tariff_str):
            return False
        return "até" in str(tariff_str) or "após" in str(tariff_str)

    @staticmethod
    def parse_connector_tariffs(df: pd.DataFrame, uid: str) -> Optional[ParsedTariff]:
        """
        Parse all tariff information for a specific connector.

        Args:
            df: DataFrame with Mobie tariff data
            uid: Connector UID (UID_TOMADA)

        Returns:
            ParsedTariff instance or None if connector not found
        """
        # Get all rows for this connector
        conn_data = df[df["UID_TOMADA"] == uid]

        if len(conn_data) == 0:
            return None

        # Get basic connector info from first row
        first_row = conn_data.iloc[0]

        # Parse power (handle comma as decimal separator)
        power_str = str(first_row.get("POTENCIA_TOMADA", "0"))
        try:
            power_kw = (
                float(power_str.replace(",", "."))
                if power_str and power_str != "nan"
                else 0.0
            )
        except (ValueError, AttributeError):
            power_kw = 0.0

        parsed = ParsedTariff(
            uid=uid,
            operator=first_row.get("OPERADOR", ""),
            charger_type=first_row.get("TIPO_POSTO", ""),
            connector_type=first_row.get("TIPO_TOMADA", ""),
            power_kw=power_kw,
            location=first_row.get("MUNICIPIO", ""),
        )

        # Parse each tariff component
        for _, row in conn_data.iterrows():
            tipo_tarifario = row.get("TIPO_TARIFARIO")
            tipo_tarifa = row.get("TIPO_TARIFA")
            tarifa = row.get("TARIFA")

            if pd.isna(tipo_tarifa):
                continue

            # Determine which tariff type we're dealing with
            # If TIPO_TARIFARIO is NaN/missing, treat as REGULAR
            is_regular = pd.isna(tipo_tarifario) or tipo_tarifario == "REGULAR"
            is_adhoc = tipo_tarifario == "AD_HOC_PAYMENT"

            # Parse based on component type
            if tipo_tarifa == "FLAT":
                rate = MobieTariffParser.parse_rate(tarifa)
                if is_regular:
                    parsed.regular_flat = rate
                elif is_adhoc:
                    parsed.adhoc_flat = rate

            elif tipo_tarifa == "ENERGY":
                rate = MobieTariffParser.parse_rate(tarifa)
                if is_regular:
                    parsed.regular_energy = rate
                elif is_adhoc:
                    parsed.adhoc_energy = rate

            elif tipo_tarifa == "TIME":
                # Handle tiered pricing
                tiered_rate = TieredRate.from_string(tarifa)
                if is_regular:
                    parsed.regular_time.append(tiered_rate)
                elif is_adhoc:
                    parsed.adhoc_time.append(tiered_rate)

            elif tipo_tarifa == "PARKING_TIME":
                rate = MobieTariffParser.parse_rate(tarifa)
                if is_regular:
                    parsed.regular_parking_time = rate
                elif is_adhoc:
                    parsed.adhoc_parking_time = rate

        return parsed

    @staticmethod
    def load_all_tariffs(csv_path: str) -> Dict[str, ParsedTariff]:
        """
        Load and parse all tariffs from Mobie CSV file.

        Args:
            csv_path: Path to mobie_tariffs_latest.csv

        Returns:
            Dictionary mapping UID_TOMADA to ParsedTariff
        """
        df = pd.read_csv(csv_path, sep=";")

        # Get unique connector UIDs
        unique_uids = df["UID_TOMADA"].unique()

        tariffs = {}
        for uid in unique_uids:
            parsed = MobieTariffParser.parse_connector_tariffs(df, uid)
            if parsed:
                tariffs[uid] = parsed

        return tariffs
