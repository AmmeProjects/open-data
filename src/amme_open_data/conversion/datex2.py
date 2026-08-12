from enum import Enum


class DatexParkingType(str, Enum):
    EX_OTHER = "other"
    PARKING_LOT = "openSpace"
    ON_STREET = "onstreet"
    PARKING_GARAGE = "inBuilding"


class DatexCapabilities(str, Enum):
    RFID_READER = "rfid"
    CONTACTLESS_CARD_SUPPORT = "nfc"
    CREDIT_CARD_PAYABLE = "creditCard"
    DEBIT_CARD_PAYABLE = "debitCard"
    REMOTE_START_STOP_CAPABLE = "apps"
    PED_TERMINAL = "pinpad"


class DatexConnectorStandards(str, Enum):
    IEC_62196_T2_COMBO = "iec62196T2COMBO"
    IEC_62196_T2 = "iec62196T2"
    CHADEMO = "chademo"
    DOMESTIC_A = "domesticA"
    DOMESTIC_E = "domesticE"
    DOMESTIC_F = "domesticF"  # schuko
    DOMESTIC_L = "domesticL"
    IEC_62196_T1 = "iec62196T1"
    IEC_62196_T3A = "iec62196T3A"
    IEC_60309_2_single_16 = "iec60309x2single16"
    IEC_60309_2_three_32 = "iec60309x2three32"
    IEC_62196_T1_COMBO = "iec62196T1COMBO"
    IEC_62196_T3C = "iec62196T3C"


class DatexConnectorFormats(str, Enum):
    CABLE = "cableMode3"
    SOCKET = "socket"


class DatexPowerTypes(str, Enum):
    AC_1_PHASE = "mode2AC1p"
    AC_3_PHASE = "mode3AC3p"
    DC = "mode4DC"
