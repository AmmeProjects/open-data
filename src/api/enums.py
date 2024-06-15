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
    IEC_62196_T2_COMBO = auto()
    IEC_62196_T2 = auto()
    CHADEMO = auto()
    DOMESTIC_F = auto()
    IEC_62196_T1 = auto()
    IEC_62196_T3A = auto()
    IEC_60309_2_three_32 = auto()
    IEC_62196_T1_COMBO = auto()
    IEC_62196_T3C = auto()


class ConnectorFormats(Enum):
    CABLE = auto()
    SOCKET = auto()


class PowerTypes(Enum):
    AC_1_PHASE = auto()
    AC_3_PHASE = auto()
    DC = auto()
