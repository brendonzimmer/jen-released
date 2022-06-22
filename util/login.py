# Different login depeing on if cache exists
from playwright.sync_api import Playwright, Browser, Page
from util.cache import state, save_context, new_context
from util.env import create_env, env

# Load context go to home page
def prev_login(browser: Browser) -> tuple[Browser, Page]:
    context = new_context(browser)
    page = context.new_page()
    
    page.goto("https://us1.re-leased.com/")
    page.wait_for_load_state()

    # If login timeout, login again
    if page.url == "https://signin.re-leased.com/?returnUrl=%2F": return new_login(browser)
    return browser, page


# Save context and go to home page
def new_login(browser: Browser, resign: bool = False) -> tuple[Browser, Page]:
    page = browser.new_page()
    page.goto("https://signin.re-leased.com/")
    
    # Sign In
    if resign: create_env()
    E, P = env()
    page.fill("#Email", E)
    page.fill("#Password", P)

    # Click 'Remember Me'
    page.click(".checkbox")
    
    # Click 'Sign In'
    page.click("body > div > section.login > form > div:nth-child(2) > div > input")

    # Handle wrong login
    page.wait_for_load_state()
    if page.query_selector(".field-validation-error"): 
        print("The e-mail address or password provided is incorrect.\nPlease check your credentials and try again.\n")
        return new_login(browser)

    # Save context to cache folder
    page.wait_for_load_state()
    save_context(page)
    return browser, page


# Launch chrome and run login
def launch(p: Playwright) -> tuple[Browser, Page]:
    # Launch Chrome
    browser = p.chromium.launch(headless=False, slow_mo=0)
    
    # Check if state exists
    if state(): return prev_login(browser)
    return new_login(browser)
    
