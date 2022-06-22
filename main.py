from playwright.sync_api import sync_playwright, Page, Browser
from util.login import launch, new_login
from tkinter import filedialog, Tk
import util.reminders as reminder


Tk().withdraw()

def upload_file(page: Page, lease: tuple[str, str, str], filename: str):
    (prop, lease_name, lease_id) = lease
    page.goto(f"https://us1.re-leased.com/Lease/Edit/{lease_id}?SortBy=0&leaseFilterTab=Current&applyTenancyFunds=False&returnToFolder=False&leaseTab=7")
    page.wait_for_selector("[data-cy=documents]")
    
    page.on("filechooser", lambda file_chooser: (file_chooser.set_files(filename)))  #, print("File added!")))

    folder_exists = False
    for folder in page.query_selector_all("[data-folderid].droppable.ui-droppable > a > span"):
        # print("Folder", folder.inner_text())
        if folder.inner_text() == "Insurance":
            folder_exists = True
            folder.click()
            break

    if not folder_exists:
        # print("Folder does not exist")
        page.query_selector("[data-cy=create-new-folder]").click()
        page.fill("#Name", "Insurance")
        page.click("#saveFolderButton")
        # print("Made new insurance folder")
        page.wait_for_selector(".folder-list")

    # Wait for load state to click button # page.wait_for_timeout(3000)
    page.wait_for_function('document.querySelector("ul > li[data-folderid].selected > a > span").innerText == "Insurance"')
    page.query_selector("#documentUpload").click()
    # print("Upload button clicked!")
    
    page.wait_for_selector(".attachment-upload-button")
    page.click(".attachment-upload-button")
    # print("Real attachment button clicked!")

    page.set_input_files("#fileupload", filename) 
    # print("Hidden input set_input_files")

    d, expir = reminder.get_date()

    page.fill("#DocumentList_0__Title", f"Insurance Exp ({expir})")

    page.click("#save-attachments")

    try:
        page.wait_for_selector(".open > tbody > [data-id]")
        print("\nSaved file!")
        reminder.make(page, expir, d, delta=14, lease_id=lease_id)
        reminder.make(page, expir, d, delta=1, lease_id=lease_id)
        print("Created Reminders!\n")
    except Exception as e:
        print("Error:", e)
        print("Could not save file!")

    


def select_a_lease(properties: dict[str, dict[str, str]], browser: Browser, page: Page):
    prop = None
    lease = None
    lease_id = None
    
    # User selects a property
    while True:
        print("Properties:")
        for i, prop in enumerate(properties):
            print(f"\t{i+1}. {prop}")
        print(f"\t{len(properties)+1}. Go back")

        inp = input("Which property? ")

        if inp.isdigit() == False: continue
        if int(inp) <= 0 or int(inp) > len(properties)+1: continue
        if int(inp) == len(properties)+1: return menu(browser, page)

        prop = list(properties.keys())[int(inp)-1]
        break

    # User selects a lease with the option to go back to the property selection
    while True:
        print(f"Leases:")
        for i, lease in enumerate(properties[prop]):
            print(f"\t{i+1}. {lease}")
        print(f"\t{len(properties[prop])+1}. Go back")
        inp = input("Which lease? ")

        if inp.isdigit() == False: continue
        if int(inp) <= 0 or int(inp) > len(properties[prop])+1: continue
        if int(inp) == len(properties[prop])+1: return select_a_lease(properties, browser, page)

        lease = list(properties[prop].keys())[int(inp)-1]
        lease_id = properties[prop][lease]
        break

    return (prop, lease, lease_id)


def get_leases(page: Page, properties: dict[str, dict[str, str]]):
    page.wait_for_load_state()

    # Check if pagination
    next_button = page.query_selector("[page_number].next")
    
    # Get Leases and put in properties
    for el in page.query_selector_all("#main > div > table.striped.large > tbody > tr"):
        prop = el.query_selector("td:nth-child(3) > table > tbody > tr:nth-child(1) > td:nth-child(2)").inner_text()
        lease_name = el.query_selector("td:nth-child(2) > a").inner_text()

        if properties.get(prop) == None: properties[prop] = {}

        # lease_id = "NOT FOUND"
        for tr in el.query_selector_all(f"td:nth-child(3) > table > tbody > tr"):
            if tr.query_selector("td").inner_text() == "Code/Reference": 
                lease_name += " - " + tr.query_selector(f"td:nth-child(2)").inner_text()
            if tr.query_selector("td").inner_text() == "System ID":
                lease_id = tr.query_selector(f"td:nth-child(2)").inner_text()
        properties[prop][lease_name] = lease_id

    return (properties, next_button)


def upload_insurance(page: Page, browser: Browser):
    # Go to Leases Page
    page.goto("https://us1.re-leased.com/Lease")
    
    # Show all leases
    page.click("#select2-LeaseContextOptions_company-container")
    page.query_selector("#select2-LeaseContextOptions_company-results").query_selector("xpath=child::*").click()

    print("Loading leases...")

    # Compile 'Current' tab leases to dict
    (properties, next_button) = get_leases(page, {})
    
    # Check if pagination
    while next_button:
        next_button.click()
        (properties, next_button) = get_leases(page, properties)

    # Do the same for 'Holding Over' tab
    page.click(".tabMenu > li:nth-child(2) > a")
    (properties, next_button) = get_leases(page, properties)

    # Check if pagination
    while next_button:
        next_button.click()
        (properties, next_button) = get_leases(page, properties)

    while True:
        # Print Leases # print(json.dumps(properties, indent=4, sort_keys=True))
        lease = select_a_lease(properties, browser, page)
        print("Lease Chosen:", lease[1])

        while True:
            print("Select the file to upload: ", end="", flush=True)
            filename = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
            if not filename: print("No file selected!\n"); continue
            print(filename); break

        upload_file(page, lease, filename)
        

def menu(browser: Browser, page: Page):
    while True:
        inp = input("""
What would you like to do?
\t1. Upload Insurance Documents
\t2. Change Login Email & Password
\t3. Quit
Pick one: """)
        print()

        if inp == "1": upload_insurance(page, browser)
        if inp == "2": browser, page = new_login(browser, resign=True)
        if inp == "3": browser.close(); print("Application closed."); exit()


def main():
    with sync_playwright() as p:
        # Launch browser and login
        browser, page = launch(p)

        # Main Menu
        menu(browser, page)


main()