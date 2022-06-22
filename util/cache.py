# Manage caching folder for playwright context
from playwright.sync_api import Browser, Page
from os import path, mkdir

# Contants for caching
CACHE_PATH = f"{path.dirname(__file__)}/cache"
STATE_PATH = CACHE_PATH + "/state.json"

# Create and return a new browser context
def new_context(browser: Browser):
    return browser.new_context(storage_state=STATE_PATH)


# Saves browser context to state path
def save_context(page: Page):
    page.context.storage_state(path=STATE_PATH)


# Checks if folder and file exist
def state():
    cache()
    return path.exists(STATE_PATH)


# Checks if folder exists
def cache():
    exists = path.exists(CACHE_PATH)
    if not exists: mkdir(CACHE_PATH)
    return exists