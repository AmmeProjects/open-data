from enum import Enum, auto


class ParkingType(Enum):
    PARKING_LOT = auto()
    ON_STREET = auto()
    PARKING_GARAGE = auto()
    EX_OTHER = auto()  # extended


class Capabilities(Enum):
    RFID_READER = auto()
    CONTACTLESS_CARD_SUPPORT = auto()
    CREDIT_CARD_PAYABLE = auto()
    DEBIT_CARD_PAYABLE = auto()
    REMOTE_START_STOP_CAPABLE = auto()
    PED_TERMINAL = auto()


class ConnectorStandards(Enum):
    IEC_62196_T2_COMBO = auto()  # Combo Type 2 based, DC
    IEC_62196_T2 = auto()  # IEC 62196 Type 2 "Mennekes"
    CHADEMO = auto()  # The connector type is CHAdeMO, DC
    CHAOJI = auto()  # The ChaoJi connector. The new generation charging connector, harmonized between CHAdeMO and GB/T. DC.
    DOMESTIC_A = auto()  # Standard/Domestic household, type "A", NEMA 1-15, 2 pins
    DOMESTIC_B = auto()  # Standard/Domestic household, type "B", NEMA 5-15, 3 pins
    DOMESTIC_C = auto()  # Standard/Domestic household, type "C", CEE 7/17, 2 pins
    DOMESTIC_D = auto()  # Standard/Domestic household, type "D", 3 pin
    DOMESTIC_E = auto()  # Standard/Domestic household, type "E", CEE 7/5 3 pins
    DOMESTIC_F = auto()  # Standard/Domestic household, type "F", CEE 7/4, Schuko, 3 pins
    DOMESTIC_G = auto()  # Standard/Domestic household, type "G", BS 1363, Commonwealth, 3 pins
    IEC_62196_T1 = auto()  # IEC 62196 Type 1 "SAE J1772"
    IEC_62196_T3A = auto()
    IEC_60309_2_three_32 = auto()  # IEC 60309-2 Industrial Connector three phases 32 amperes (usually red)
    IEC_62196_T1_COMBO = auto()  # Combo Type 1 based, DC
    IEC_62196_T3C = auto()  # IEC 62196 Type 3C "Scame"
    DOMESTIC_H = auto()  # Standard/Domestic household, type "H", SI-32, 3 pins
    DOMESTIC_I = auto()  # Standard/Domestic household, type "I", AS 3112, 3 pins
    DOMESTIC_J = auto()  # Standard/Domestic household, type "J", SEV 1011, 3 pins
    DOMESTIC_K = auto()  # Standard/Domestic household, type "K", DS 60884-2-D1, 3 pins
    DOMESTIC_L = auto()  # Standard/Domestic household, type "L", CEI 23-16-VII, 3 pins
    DOMESTIC_M = auto()  # Standard/Domestic household, type "M", BS 546, 3 pins
    DOMESTIC_N = auto()  # Standard/Domestic household, type "N", NBR 14136, 3 pins
    DOMESTIC_O = auto()  # Standard/Domestic household, type "O", TIS 166-2549, 3 pins
    GBT_AC = auto()  # Guobiao GB/T 20234.2 AC socket/connector
    GBT_DC = auto()  # Guobiao GB/T 20234.3 DC connector
    IEC_60309_2_single_16 = auto()  # IEC 60309-2 Industrial Connector single phase 16 amperes (usually blue)
    IEC_60309_2_three_16 = auto()  # IEC 60309-2 Industrial Connector three phases 16 amperes (usually red)
    IEC_60309_2_three_64 = auto()  # IEC 60309-2 Industrial Connector three phases 64 amperes (usually red)
    NEMA_5_20 = auto()  # NEMA 5-20, 3 pins
    NEMA_6_30 = auto()  # NEMA 6-30, 3 pins
    NEMA_6_50 = auto()  # NEMA 6-50, 3 pins
    NEMA_10_30 = auto()  # NEMA 10-30, 3 pins
    NEMA_10_50 = auto()  # NEMA 10-50, 3 pins
    NEMA_14_30 = auto()  # NEMA 14-30, 3 pins, rating of 30 A
    NEMA_14_50 = auto()  # NEMA 14-50, 3 pins, rating of 50 A
    PANTOGRAPH_BOTTOM_UP = auto()  # On-board Bottom-up-Pantograph typically for bus charging
    PANTOGRAPH_TOP_DOWN = auto()  # Off-board Top-down-Pantograph typically for bus charging
    TESLA_R = auto()  # Tesla Connector "Roadster"-type (round, 4 pin)
    TESLA_S = auto()  # Tesla Connector "Model S/X"-type (oval, 5 pin)


class ConnectorFormats(Enum):
    CABLE = auto()
    SOCKET = auto()


class PowerTypes(Enum):
    AC_1_PHASE = auto()
    AC_3_PHASE = auto()
    DC = auto()
