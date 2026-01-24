"""
Tariff registry for querying charging tariff information.

Provides access to parsed Mobie tariff data with lookup and filtering capabilities.
"""

from typing import Dict, List, Optional
from pathlib import Path

from sim.data.tariff_parser import MobieTariffParser, ParsedTariff
from sim.models.tariff import Tariff


class TariffRegistry:
    """
    Registry for querying tariff information from Mobie data.

    Loads and indexes tariff data by connector UID, operator, charger type, etc.
    Handles both REGULAR and AD_HOC_PAYMENT tariff types.

    Example:
        >>> registry = TariffRegistry('data/naps/portugal/mobie_tariffs_latest.csv')
        >>> tariff = registry.get_tariff('PT-EDP-EABF-00008-1-1')
        >>> print(f"Flat fee: €{tariff.regular_flat}")
        >>> regular = tariff.to_tariff('REGULAR')
        >>> cost = regular.calculate_cost(energy_kwh=30, time_minutes=45)
    """

    def __init__(self, csv_path: Optional[str] = None):
        """
        Initialize the tariff registry.

        Args:
            csv_path: Path to mobie_tariffs_latest.csv file.
                     If None, loads from default location.
        """
        if csv_path is None:
            # Default path relative to project root
            default_path = (
                Path(__file__).parents[2]
                / "data"
                / "naps"
                / "portugal"
                / "mobie_tariffs_latest.csv"
            )
            csv_path = str(default_path)

        self.csv_path = csv_path
        self.tariffs: Dict[str, ParsedTariff] = {}
        self._operator_index: Dict[str, List[str]] = {}
        self._charger_type_index: Dict[str, List[str]] = {}

        self._load_tariffs()

    def _load_tariffs(self):
        """Load and index all tariffs from CSV file."""
        print(f"Loading tariffs from {self.csv_path}...")
        self.tariffs = MobieTariffParser.load_all_tariffs(self.csv_path)

        # Build indexes
        for uid, tariff in self.tariffs.items():
            # Index by operator
            operator = tariff.operator
            if operator not in self._operator_index:
                self._operator_index[operator] = []
            self._operator_index[operator].append(uid)

            # Index by charger type
            charger_type = tariff.charger_type
            if charger_type not in self._charger_type_index:
                self._charger_type_index[charger_type] = []
            self._charger_type_index[charger_type].append(uid)

        print(f"Loaded {len(self.tariffs)} connector tariffs")
        print(f"  Operators: {len(self._operator_index)}")
        print(f"  Charger types: {list(self._charger_type_index.keys())}")

    def get_tariff(self, uid: str) -> Optional[ParsedTariff]:
        """
        Get tariff information for a specific connector.

        Args:
            uid: Connector UID (UID_TOMADA)

        Returns:
            ParsedTariff instance or None if not found
        """
        return self.tariffs.get(uid)

    def get_regular_tariff(self, uid: str) -> Optional[Tariff]:
        """
        Get REGULAR tariff as simple Tariff model.

        Args:
            uid: Connector UID

        Returns:
            Tariff instance for REGULAR pricing or None if not found
        """
        parsed = self.get_tariff(uid)
        if parsed:
            return parsed.to_tariff("REGULAR")
        return None

    def get_adhoc_tariff(self, uid: str) -> Optional[Tariff]:
        """
        Get AD_HOC_PAYMENT tariff as simple Tariff model.

        Args:
            uid: Connector UID

        Returns:
            Tariff instance for AD_HOC pricing or None if not found
        """
        parsed = self.get_tariff(uid)
        if parsed:
            return parsed.to_tariff("AD_HOC_PAYMENT")
        return None

    def find_by_operator(self, operator: str) -> List[ParsedTariff]:
        """
        Find all tariffs for a specific operator.

        Args:
            operator: Operator name (e.g., 'EDP', 'GLP', 'HRZ')

        Returns:
            List of ParsedTariff instances
        """
        uids = self._operator_index.get(operator, [])
        return [self.tariffs[uid] for uid in uids]

    def find_by_charger_type(self, charger_type: str) -> List[ParsedTariff]:
        """
        Find all tariffs for a specific charger type.

        Args:
            charger_type: One of 'Lento', 'Médio', 'Rápido', 'Ultrarrápido'

        Returns:
            List of ParsedTariff instances
        """
        uids = self._charger_type_index.get(charger_type, [])
        return [self.tariffs[uid] for uid in uids]

    def find_with_dual_pricing(self) -> List[ParsedTariff]:
        """
        Find connectors that offer both REGULAR and AD_HOC_PAYMENT tariffs.

        Returns:
            List of ParsedTariff instances with both pricing types
        """
        dual_tariffs = []
        for tariff in self.tariffs.values():
            # Check if both have non-zero components
            has_regular = (
                tariff.regular_flat > 0
                or tariff.regular_energy > 0
                or len(tariff.regular_time) > 0
            )
            has_adhoc = (
                tariff.adhoc_flat > 0
                or tariff.adhoc_energy > 0
                or len(tariff.adhoc_time) > 0
            )

            if has_regular and has_adhoc:
                dual_tariffs.append(tariff)

        return dual_tariffs

    def find_with_tiered_pricing(self) -> List[ParsedTariff]:
        """
        Find connectors with tiered pricing (different rates at time thresholds).

        Returns:
            List of ParsedTariff instances with tiered pricing
        """
        return [t for t in self.tariffs.values() if t.has_tiered_pricing()]

    def get_statistics(self) -> Dict:
        """
        Get statistics about the tariff data.

        Returns:
            Dictionary with various statistics
        """
        total = len(self.tariffs)

        # Count by combination type
        combinations = {
            "ENERGY,FLAT,TIME": 0,
            "FLAT,TIME": 0,
            "TIME": 0,
            "ENERGY,FLAT": 0,
            "ENERGY": 0,
            "Other": 0,
        }

        tiered_count = 0
        dual_count = 0

        for tariff in self.tariffs.values():
            # Determine combination (simplified)
            has_flat = tariff.regular_flat > 0
            has_energy = tariff.regular_energy > 0
            has_time = len(tariff.regular_time) > 0

            if has_energy and has_flat and has_time:
                combinations["ENERGY,FLAT,TIME"] += 1
            elif has_flat and has_time:
                combinations["FLAT,TIME"] += 1
            elif has_time:
                combinations["TIME"] += 1
            elif has_energy and has_flat:
                combinations["ENERGY,FLAT"] += 1
            elif has_energy:
                combinations["ENERGY"] += 1
            else:
                combinations["Other"] += 1

            if tariff.has_tiered_pricing():
                tiered_count += 1

            # Check for dual pricing
            has_regular = (
                tariff.regular_flat > 0
                or tariff.regular_energy > 0
                or len(tariff.regular_time) > 0
            )
            has_adhoc = (
                tariff.adhoc_flat > 0
                or tariff.adhoc_energy > 0
                or len(tariff.adhoc_time) > 0
            )
            if has_regular and has_adhoc:
                dual_count += 1

        return {
            "total_connectors": total,
            "operators": len(self._operator_index),
            "charger_types": list(self._charger_type_index.keys()),
            "combinations": combinations,
            "tiered_pricing_count": tiered_count,
            "dual_pricing_count": dual_count,
        }

    def calculate_session_cost(
        self,
        uid: str,
        energy_kwh: float,
        time_minutes: float,
        tariff_type: str = "REGULAR",
    ) -> Optional[float]:
        """
        Calculate cost for a charging session.

        Handles tiered pricing correctly.

        Args:
            uid: Connector UID
            energy_kwh: Energy consumed in kWh
            time_minutes: Total charging time in minutes
            tariff_type: Either 'REGULAR' or 'AD_HOC_PAYMENT'

        Returns:
            Total cost in EUR or None if connector not found
        """
        tariff = self.get_tariff(uid)
        if not tariff:
            return None

        # Get base costs
        if tariff_type == "REGULAR":
            flat = tariff.regular_flat
            energy_cost = tariff.regular_energy * energy_kwh
        else:
            flat = tariff.adhoc_flat
            energy_cost = tariff.adhoc_energy * energy_kwh

        # Calculate time cost (handles tiered pricing)
        time_cost = tariff.calculate_time_cost(time_minutes, tariff_type)

        return flat + energy_cost + time_cost

    def __len__(self) -> int:
        """Return number of connectors with tariff information."""
        return len(self.tariffs)

    def __repr__(self) -> str:
        return f"TariffRegistry({len(self.tariffs)} connectors)"
