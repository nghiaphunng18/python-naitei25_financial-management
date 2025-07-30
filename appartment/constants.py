from enum import Enum


class StringLength(Enum):
    SHORT = 20
    MEDIUM = 30
    LONG = 50
    EXTRA_LONG = 100
    DESCRIPTION = 255
    ADDRESS = 55


class DecimalConfig:
    MONEY = {"max_digits": 10, "decimal_places": 2}


class ServiceType(Enum):
    PER_ROOM = "per_room"
    PER_PERSON = "per_person"

    @classmethod
    def choices(cls):
        return [(key.value, key.name.replace("_", " ").title()) for key in cls]


class BillStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"

    @classmethod
    def choices(cls):
        return [(key.value, key.name.replace("_", " ").title()) for key in cls]


class PaymentStatus(Enum):
    UNPAID = "unpaid"
    PAID = "paid"

    @classmethod
    def choices(cls):
        return [(key.value, key.name.replace("_", " ").title()) for key in cls]


class RoomStatus(Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"

    @classmethod
    def choices(cls):
        return [(key.value, key.name.replace("_", " ").title()) for key in cls]


class NotificationStatus(Enum):
    UNREAD = "unread"
    READ = "read"

    @classmethod
    def choices(cls):
        return [(key.value, key.name.replace("_", " ").title()) for key in cls]


class PaymentMethod(Enum):
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CARD = "card"

    @classmethod
    def choices(cls):
        return [(key.value, key.name.replace("_", " ").title()) for key in cls]


class ElectricWaterStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"

    @classmethod
    def choices(cls):
        return [(key.value, key.name.replace("_", " ").title()) for key in cls]
