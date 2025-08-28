from enum import Enum


class StringLength(Enum):
    VVERY_SHORT = 7
    VERY_SHORT = 10
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
    OVERDUE = "overdue"

    @classmethod
    def choices(cls):
        return [(key.value, key.name.replace("_", " ").title()) for key in cls]


class PaymentTransactionStatus(Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

    @classmethod
    def choices(cls):
        return [(key.value, key.name.replace("_", " ").title()) for key in cls]


class WebHookCode(Enum):
    SUCCESS = "00"
    INVALID_PARAMS = "01"

    @classmethod
    def choices(cls):
        return [(key.value, key.name.replace("_", " ").title()) for key in cls]


class RoomStatus(Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"
    UNAVAILABLE = "unavailable"  # Thêm dòng này

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


MIN_OCCUPANTS = 1
MAX_OCCUPANTS = 50

PRICE_CHANGES_PER_PAGE_MAX = 5
HISTORY_PER_PAGE_MAX = 5


class UserRole(Enum):
    ADMIN = "ROLE_ADMIN"
    APARTMENT_MANAGER = "ROLE_APARTMENT_MANAGER"
    RESIDENT = "ROLE_RESIDENT"

    @classmethod
    def choices(cls):
        return [(role.value, role.name.replace("_", " ").title()) for role in cls]


class PaginateNumber(Enum):
    P_SHORT = 10
    P_LONG = 20

    @classmethod
    def choices(cls):
        return [(key.value, key.name.replace("_", " ").title()) for key in cls]


DAY_MONTH_YEAR_FORMAT = "%d/%m/%Y"
MONTH_YEAR_FORMAT = "%m/%Y"
DATE_TIME_FORMAT = "%d/%m/%Y %H:%M"
YEAR_MONTH_DAY_FORMAT = "%Y-%m-%d"

STATUS_CHOICES = [
    ("True", "Active"),
    ("False", "Inactive"),
]
DEFAULT_PAGE_SIZE = 10

MIN_RENTAL_PRICE = 0

BILL_SEND_DAYS = [25, 26, 27, 28, 29, 30, 31]
