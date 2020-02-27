from enum import Enum


class SourceDApp(Enum):
    PUBLISHER_DAPP = "PUBLISHER_DAPP"
    MARKETPLACE_DAPP = "MARKETPLACE_DAPP"
    RFAI_DAPP = "RFAI_DAPP"


class CommunicationType(Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"


class PreferenceType(Enum):
    FEATURE_RELEASE = "FEATURE_RELEASE"
    WEEKLY_SUMMARY = "WEEKLY_SUMMARY"
    COMMENTS_AND_MESSAGES = "COMMENTS_AND_MESSAGES"


class Status(Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
