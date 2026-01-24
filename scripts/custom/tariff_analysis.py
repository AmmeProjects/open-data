#!/usr/bin/env python3
"""
MOBIE Portugal Tariff Analysis Script

This script analyzes the tariff structure of EV charging connectors in Portugal,
identifying the most common pricing component combinations and their characteristics.

Goal: Understand tariff combinations covering at least 90% of connectors
"""

import pandas as pd
import re
from typing import Optional
from dataclasses import dataclass


@dataclass
class TariffStats:
    """Statistics for a specific tariff component type"""

    component_type: str
    count: int
    min_value: float
    max_value: float
    mean_value: float
    median_value: float
    most_common_value: float
    most_common_count: int


def parse_tariff_value(tariff_str: str) -> Optional[float]:
    """Extract numeric value from tariff string (e.g., '€ 0.261 /charge' -> 0.261)"""
    if pd.isna(tariff_str):
        return None
    match = re.search(r"€\s*([\d,\.]+)", str(tariff_str))
    if match:
        return float(match.group(1).replace(",", "."))
    return None


def has_tiered_pricing(tariff_str: str) -> bool:
    """Check if tariff has tiered pricing (different rates before/after threshold)"""
    if pd.isna(tariff_str):
        return False
    return "até" in str(tariff_str) or "após" in str(tariff_str)


def print_header(title: str, char: str = "=", width: int = 80):
    """Print a formatted header"""
    print("\n" + char * width)
    print(title.center(width))
    print(char * width)


def print_section(title: str, width: int = 80):
    """Print a section header"""
    print(f"\n{title}")
    print("-" * width)


def analyze_tariff_data(csv_path: str):
    """Main analysis function"""

    # Load data
    print("Loading tariff data...")
    df = pd.read_csv(csv_path, sep=";")

    # Parse tariff values
    df["tariff_value"] = df["TARIFA"].apply(parse_tariff_value)
    df["is_tiered"] = df["TARIFA"].apply(has_tiered_pricing)

    # Create combination column for each connector
    df["combo"] = df.groupby("UID_TOMADA")["TIPO_TARIFA"].transform(
        lambda x: ",".join(sorted(x.dropna().unique()))
    )

    # Get unique connectors
    unique_df = df.groupby("UID_TOMADA").first().reset_index()
    total_connectors = len(unique_df)

    # ========== OVERVIEW ==========
    print_header("MOBIE PORTUGAL TARIFF ANALYSIS")

    print(f"\nDataset Overview:")
    print(f"  • Total rows: {len(df):,}")
    print(f"  • Unique connectors: {total_connectors:,}")
    print(f"  • Unique operators: {df['OPERADOR'].nunique()}")

    # ========== TARIFF TYPE ANALYSIS ==========
    print_section("Tariff Types (TIPO_TARIFARIO)")

    tipo_counts = df["TIPO_TARIFARIO"].value_counts()
    print(f"\nTariff type distribution:")
    for tipo, count in tipo_counts.items():
        connector_count = df[df["TIPO_TARIFARIO"] == tipo]["UID_TOMADA"].nunique()
        print(
            f"  • {tipo}: {count:,} rows, {connector_count:,} connectors ({connector_count / total_connectors * 100:.2f}%)"
        )

    # Check for overlap
    regular_connectors = set(
        df[df["TIPO_TARIFARIO"] == "REGULAR"]["UID_TOMADA"].unique()
    )
    adhoc_connectors = set(
        df[df["TIPO_TARIFARIO"] == "AD_HOC_PAYMENT"]["UID_TOMADA"].unique()
    )
    overlap = regular_connectors & adhoc_connectors

    print(f"\nTariff type distribution by connector:")
    print(
        f"  • REGULAR only: {len(regular_connectors - adhoc_connectors):,} connectors"
    )
    print(
        f"  • AD_HOC_PAYMENT only: {len(adhoc_connectors - regular_connectors):,} connectors"
    )
    print(f"  • Both types: {len(overlap):,} connectors")

    print(
        f"\n  Note: AD_HOC_PAYMENT typically has higher ENERGY rates (€0.51 avg vs €0.14)"
    )
    print(
        f"        REGULAR tariffs often include FLAT+TIME, AD_HOC is mostly ENERGY-only"
    )

    # ========== COVERAGE ANALYSIS ==========
    print_header("TARIFF COMBINATION COVERAGE", char="-")

    combinations = (
        df.groupby("UID_TOMADA")["TIPO_TARIFA"]
        .apply(lambda x: ",".join(sorted(x.dropna().unique())))
        .value_counts()
    )

    print(f"\nTop tariff combinations (targeting 90% coverage):")
    cumulative = 0
    top_combos = []

    for i, (combo, count) in enumerate(combinations.items(), 1):
        if not combo:  # Skip empty combinations
            continue
        cumulative += count
        percentage = (cumulative / total_connectors) * 100

        print(f'\n  {i}. "{combo}"')
        print(f"     Connectors: {count:,} ({count / total_connectors * 100:.2f}%)")
        print(f"     Cumulative: {cumulative:,} ({percentage:.2f}%)")

        top_combos.append(combo)

        if percentage >= 90 and len(top_combos) >= 4:
            print(
                f"\n  ✓ 90% coverage achieved with top {len(top_combos)} combinations!"
            )
            break

    # ========== COMBINATIONS BY TARIFF TYPE ==========
    print_section("Combinations by Tariff Type (TIPO_TARIFARIO)")

    for tipo in ["REGULAR", "AD_HOC_PAYMENT"]:
        subset = df[df["TIPO_TARIFARIO"] == tipo]
        if len(subset) == 0:
            continue

        tipo_connectors = subset["UID_TOMADA"].nunique()
        print(f"\n{tipo} ({tipo_connectors:,} connectors):")

        combos = (
            subset.groupby("UID_TOMADA")["TIPO_TARIFA"]
            .apply(lambda x: ",".join(sorted(x.dropna().unique())))
            .value_counts()
        )

        for i, (combo, count) in enumerate(combos.head(5).items(), 1):
            if combo:
                print(
                    f'  {i}. "{combo}": {count:,} ({count / tipo_connectors * 100:.2f}%)'
                )

        # Show pricing differences
        print(f"\n  Average component prices:")
        for component in ["ENERGY", "FLAT", "TIME"]:
            comp_data = subset[subset["TIPO_TARIFA"] == component][
                "tariff_value"
            ].dropna()
            if len(comp_data) > 0:
                print(
                    f"    {component}: €{comp_data.mean():.4f} (median: €{comp_data.median():.4f})"
                )

    # ========== COMPONENT STATISTICS ==========
    print_header("TARIFF COMPONENT STATISTICS", char="-")

    for tariff_type in ["ENERGY", "FLAT", "TIME"]:
        type_data = df[df["TIPO_TARIFA"] == tariff_type]["tariff_value"].dropna()

        if len(type_data) > 0:
            top_val = type_data.value_counts().head(1)
            usage_pct = (
                len(df[df["TIPO_TARIFA"] == tariff_type]["UID_TOMADA"].unique())
                / total_connectors
                * 100
            )

            print(f"\n{tariff_type}:")
            print(f"  Usage: {usage_pct:.2f}% of connectors")
            print(f"  Range: €{type_data.min():.4f} - €{type_data.max():.4f}")
            print(f"  Mean: €{type_data.mean():.4f}")
            print(f"  Median: €{type_data.median():.4f}")
            print(
                f"  Most common: €{top_val.index[0]:.4f} ({top_val.values[0]:,} occurrences)"
            )

    # ========== EXAMPLES FOR EACH COMBINATION ==========
    print_header("EXAMPLES BY COMBINATION", char="=")

    for combo in top_combos:
        print_section(f"Combination: {combo}")

        subset = df[df["combo"] == combo]
        connectors_count = subset["UID_TOMADA"].nunique()
        print(
            f"Total connectors: {connectors_count:,} ({connectors_count / total_connectors * 100:.2f}%)"
        )

        # Component statistics for this combination
        print(f"\nComponent values for this combination:")
        for component in combo.split(","):
            comp_data = subset[subset["TIPO_TARIFA"] == component][
                "tariff_value"
            ].dropna()
            if len(comp_data) > 0:
                print(
                    f"  {component}: €{comp_data.mean():.4f} avg (€{comp_data.median():.4f} median)"
                )

        # Show 3 real examples
        print(f"\nReal-world examples:")
        sample_uids = subset["UID_TOMADA"].unique()[:3]

        for j, uid in enumerate(sample_uids, 1):
            conn_data = subset[subset["UID_TOMADA"] == uid]
            first_row = conn_data.iloc[0]

            print(f"\n  Example {j}: {uid}")
            print(f"    Operator: {first_row['OPERADOR']}")
            print(
                f"    Type: {first_row['TIPO_POSTO']} ({first_row['TIPO_TOMADA']}, {first_row['POTENCIA_TOMADA']}kW)"
            )
            print(f"    Location: {first_row['MUNICIPIO']}")
            print(f"    Tariff structure:")

            for _, row in conn_data.iterrows():
                if pd.notna(row["TIPO_TARIFA"]):
                    tiered = "(TIERED) " if row["is_tiered"] else ""
                    tipo_tag = (
                        f"[{row['TIPO_TARIFARIO']}] "
                        if pd.notna(row["TIPO_TARIFARIO"])
                        else ""
                    )
                    print(
                        f"      • {tipo_tag}{row['TIPO_TARIFA']}: {row['TARIFA']} {tiered}"
                    )

    # ========== SPECIAL CASES ==========
    print_header("SPECIAL CASES & ADVANCED FEATURES", char="=")

    # Dual tariff type connectors
    print(f"\nDual Tariff Types (REGULAR + AD_HOC_PAYMENT):")
    print(
        f"  Connectors with both types: {len(overlap):,} ({len(overlap) / total_connectors * 100:.2f}%)"
    )
    print(f"  Purpose: Different pricing for subscribers vs casual users")

    if len(overlap) > 0:
        print(f"\n  Example connector with both tariff types:")
        dual_sample = list(overlap)[0]
        dual_data = df[df["UID_TOMADA"] == dual_sample]
        first = dual_data.iloc[0]
        print(
            f"    Connector: {dual_sample} ({first['OPERADOR']}, {first['TIPO_POSTO']}, {first['POTENCIA_TOMADA']}kW)"
        )

        for tipo in ["REGULAR", "AD_HOC_PAYMENT"]:
            tipo_rows = dual_data[dual_data["TIPO_TARIFARIO"] == tipo]
            if len(tipo_rows) > 0:
                print(f"\n    {tipo}:")
                for _, row in tipo_rows.iterrows():
                    if pd.notna(row["TIPO_TARIFA"]):
                        print(f"      {row['TIPO_TARIFA']}: {row['TARIFA']}")

    # Tiered pricing
    print_section("Tiered Pricing")
    tiered_connectors = df[df["is_tiered"]]["UID_TOMADA"].nunique()
    print(
        f"  Connectors with tiered pricing: {tiered_connectors:,} ({tiered_connectors / total_connectors * 100:.2f}%)"
    )
    print(f"  Purpose: Discourage occupancy after charging completes")

    print(f"\n  Example of tiered pricing:")
    tiered_sample = df[df["is_tiered"]]["UID_TOMADA"].unique()[0]
    tiered_data = df[df["UID_TOMADA"] == tiered_sample]
    first = tiered_data.iloc[0]
    print(
        f"    Connector: {tiered_sample} ({first['OPERADOR']}, {first['TIPO_POSTO']})"
    )
    for _, row in tiered_data.iterrows():
        if pd.notna(row["TIPO_TARIFA"]) and row["is_tiered"]:
            print(f"      {row['TIPO_TARIFA']}: {row['TARIFA']}")

    # Charger type patterns
    print_section("Pricing Patterns by Charger Type")

    charger_patterns = {
        "Lento": "3.7kW slow chargers",
        "Médio": "7-22kW medium chargers",
        "Rápido": "50-120kW fast chargers",
        "Ultrarrápido": "150-300kW ultra-fast chargers",
    }

    for charger_type, description in charger_patterns.items():
        subset = df[df["TIPO_POSTO"] == charger_type]
        if len(subset) == 0:
            continue

        connectors = subset["UID_TOMADA"].nunique()
        top_combo = (
            subset.groupby("UID_TOMADA")["TIPO_TARIFA"]
            .apply(lambda x: ",".join(sorted(x.dropna().unique())))
            .value_counts()
            .head(1)
        )

        print(f"\n  {charger_type} ({description}):")
        print(f"    Connectors: {connectors:,}")
        if len(top_combo) > 0:
            print(
                f"    Most common: {top_combo.index[0]} ({top_combo.values[0]} connectors)"
            )

        # Average costs
        for component in ["ENERGY", "FLAT", "TIME"]:
            comp_data = subset[subset["TIPO_TARIFA"] == component][
                "tariff_value"
            ].dropna()
            if len(comp_data) > 0:
                print(f"    {component} avg: €{comp_data.mean():.4f}")

    # ========== DATA QUALITY ==========
    print_section("Data Quality")

    missing_tariff = unique_df[unique_df["TIPO_TARIFA"].isna()]
    print(
        f"\n  Missing tariff data: {len(missing_tariff):,} connectors ({len(missing_tariff) / total_connectors * 100:.2f}%)"
    )
    print(
        f"  Complete tariff data: {total_connectors - len(missing_tariff):,} connectors ({(total_connectors - len(missing_tariff)) / total_connectors * 100:.2f}%)"
    )

    # ========== SUMMARY ==========
    print_header("IMPLEMENTATION RECOMMENDATIONS", char="=")

    print(f"""
Phase 1 - Simple Tariffs (covers 85.27%):
  • Implement: ENERGY, FLAT, TIME components
  • Each component has single rate
  • No tiered pricing
  • Support REGULAR tariff type only
  
Phase 2 - Complete Coverage (covers 91.87%):
  • Add support for combinations: ENERGY+FLAT (without TIME)
  • Add AD_HOC_PAYMENT tariff type
  • Covers all top 4 combinations
  
Phase 3 - Advanced Features (covers 99%+):
  • Implement tiered TIME pricing
  • Handle PARKING_TIME component
  • Support dual tariff types (REGULAR + AD_HOC on same connector)
  • Support complex pricing structures

Key Implementation Notes:
  • FLAT: Fixed cost per session (simple addition)
  • ENERGY: Cost per kWh (multiply by energy delivered)
  • TIME: Cost per minute (multiply by session duration)
  • TIERED: Different rates based on time thresholds
  • TIPO_TARIFARIO: REGULAR (subscriber) vs AD_HOC_PAYMENT (casual user)
    - REGULAR: Lower rates, complex combinations (FLAT+TIME common)
    - AD_HOC: Higher rates, simpler (mostly ENERGY-only)
    - Some connectors offer both pricing schemes
  
Zero-cost components are valid and should be supported (e.g., €0.00/kWh)
""")

    print("=" * 80)
    print("ANALYSIS COMPLETE".center(80))
    print("=" * 80)


if __name__ == "__main__":
    import sys

    # Default path
    csv_path = "data/naps/portugal/mobie_tariffs_latest.csv"

    # Allow override via command line
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]

    try:
        analyze_tariff_data(csv_path)
    except FileNotFoundError:
        print(f"Error: File not found: {csv_path}")
        print(f"Usage: python {sys.argv[0]} [path/to/tariffs.csv]")
        sys.exit(1)
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
