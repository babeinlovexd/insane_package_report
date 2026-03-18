from datetime import timedelta

DOMAIN = "insane_updater"
CONF_GITHUB_TOKEN = "github_token"

UPDATE_INTERVAL = timedelta(hours=24)
EVENT_INSANE_PACKAGE_REPORT = "esphome.insane_package_report"

SIGNAL_NEW_PACKAGE = f"{DOMAIN}_new_package"
STORAGE_KEY = f"{DOMAIN}_storage"
STORAGE_VERSION = 1
