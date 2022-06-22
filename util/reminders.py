from playwright.sync_api import sync_playwright, Page
from util.login import launch, prev_login
from datetime import date, timedelta
from re import split

def prev_date(d: date, *, days: int):
    new_d = (d - timedelta(days=days))
    return new_d.strftime("%m/%d/%Y")


# Get date from user
def get_date() -> tuple[date, str]:
    try:
        month, day, year = split(' |/|-|_', input("What is the expiration date? "))
        
        # Make sure full year
        if len(year) == 2: year = f"20{year}"
        elif len(year) != 4: raise ValueError("invalid year")

        # Turn into date
        d = date(int(year), int(month), int(day))
        if (d - d.today()) < timedelta(days=0): raise ValueError("date is in the past")

        return d, d.strftime("%m/%d/%Y")
    except Exception as e:
        print(f"\nNot a valid date: {e}.\nExamples: 6/21/23 | 6 21 23 | 6-21-2023\n")
        return get_date()


# Show leases and retrieve user input
def show(page: Page):
    page.goto("https://us1.re-leased.com/")

    # Click the "+" button
    page.click("[data-cy=quicklinks-bar] > :nth-child(1) > :nth-child(1) > .material-icons-round")

    # Click "New Reminders"
    page.click("[data-cy=quicklinks-new-reminder]")

    # Print the leases
    page.wait_for_selector("#LeaseId")
    for i, el in enumerate(page.query_selector_all("#LeaseId > *")):
        if el.inner_text() == "< Select >": continue
        print(f"\t{i}. {el.inner_text()}")
    
    # Get the lease
    lease_index = int(input("Which lease? "))

    # Get exp date
    d, exp_date = get_date()

    return lease_index, exp_date, d


# Create reminders from user input
def make(page: Page, exp: str, date: date, *, delta: int, lease_index: int = None, lease_id: str = None):
    page.goto("https://us1.re-leased.com/")

    # Click the "+" button
    page.click("[data-cy=quicklinks-bar] > :nth-child(1) > :nth-child(1) > .material-icons-round")

    # Click "New Reminders"
    page.click("[data-cy=quicklinks-new-reminder]")

    # Assign to R&V
    page.wait_for_selector("#UserId")
    page.click("#select2-UserId-container")
    page.wait_for_selector("#select2-UserId-results")
    for person in page.query_selector_all("#select2-UserId-results > *"):
        if person.inner_text() == "Ron Goldwasser & Victor Martinez": person.click(); break

    # Click the lease
    page.click("#select2-LeaseId-container")

    if lease_id: 
        for el in page.query_selector_all(f"#select2-LeaseId-results > *"):
            id = el.get_attribute("id")
            if id and id.split("-")[-1] == lease_id: lease = el
    elif lease_index: lease = page.query_selector_all(f"#select2-LeaseId-results > *")[lease_index]
    else: raise ValueError("lease_index or lease_id must be specified") 
    lease.click()

    # Fill title and due date
    page.fill("#Title", f"Insurance Exp ({exp})")
    page.fill("#FirstDueDate", prev_date(date, days=delta))

    page.fill("#Description", f"{lease.inner_text()}'s Insurance for {date.year-1}-{date.year} expires in {delta} {'days' if delta > 1 else 'day'}.")

    # Click "Save"
    page.click(".save-reminder-button")


def manual():
    with sync_playwright() as p:
        # Launch browser and login
        _, page = launch(p)

        while True:
            lease_index, exp, date = show(page)

            make(page, exp, date, delta=14, lease_index=lease_index)
            make(page, exp, date, delta=1, lease_index=lease_index)
            print(f"Done Reminders for {lease_index}")


def auto():
    with sync_playwright() as p:
        # Launch browser and login
        browser, page = launch(p)
        page.goto("https://us1.re-leased.com/")

        # Click the "+" button
        page.click("[data-cy=quicklinks-bar] > :nth-child(1) > :nth-child(1) > .material-icons-round")

        # Click "New Reminders"
        page.click("[data-cy=quicklinks-new-reminder]")

        # Add leases to list
        page.wait_for_selector("#LeaseId")
        leases = [el.inner_text() for el in page.query_selector_all("#LeaseId > *")]

        _, page2 = prev_login(browser)
        page2.goto(input("List of data: "))
        page2.wait_for_load_state()
        page2.wait_for_selector("table.striped > tbody > *")

        for tr in page2.query_selector_all("table.striped > tbody > *"):
            if "Insurance" in tr.inner_text():
                tds = tr.query_selector_all("td")
                
                lease = tds[2].inner_text()
                if leases.count(lease) == 1:
                    lease_index = leases.index(lease)
                elif leases.count(lease) > 1:
                    print(f"Multiple leases found for {lease}. Do Manually.")
                    continue
                else: raise ValueError(f"lease {lease} not found")

                
                month, day, year = tds[0].inner_text().split("(")[1].split(")")[0].split("/")
                if len(month) == 2 and month[0] == "0": month = month[1]
                if len(day) == 2 and day[0] == "0": day = day[1]
                d = date(int(year), int(month), int(day))

                make(page, lease_index, d.strftime("%m/%d/%Y"), d, delta=14)
                make(page, lease_index, d.strftime("%m/%d/%Y"), d, delta=1)

                print("Done Reminder for " + lease)


# manual()