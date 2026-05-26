from typing import Literal

from pydantic import BaseModel, model_validator


class TariffTier(BaseModel):
    min: float | None = None
    max: float | None = None
    price: float
    unit: Literal["energy", "time", "flat", "parking"] = "energy"


class Tariff(BaseModel):
    type: Literal["AC", "DC"] | None = None
    price: float | None = None
    unit: Literal["energy", "time", "flat", "parking"] = "energy"
    min: float | None = None
    max: float | None = None
    tiers: list[TariffTier] | None = None

    @model_validator(mode="after")
    def check_price_or_tiers(self) -> "Tariff":
        if self.price is None and self.tiers is None:
            raise ValueError('Either "price" or "tiers" must be provided in a tariff')
        return self


class Network(BaseModel):
    name: str
    included_cpos: list[str] | None = None
    excluded_cpos: list[str] | None = None
    tariffs: list[Tariff]


class Plan(BaseModel):
    name: str
    country_code: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    cost: float | None = None
    months: int | None = None
    period: str | None = None
    payment_methods: (
        list[
            Literal[
                "DEBIT_CARD",
                "CREDIT_CARD",
                "REMOTE",
                "APP",
                "AD_HOC_PAYMENT",
                "RFID_CARD",
            ]
        ]
        | None
    ) = None
    networks: list[Network]


class Provider(BaseModel):
    name: str
    plans: list[Plan]


class TariffDocument(BaseModel):
    providers: list[Provider]
