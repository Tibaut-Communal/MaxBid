from playwright.sync_api import sync_playwright

EMAIL = "communal.tibaut@gmail.Com"
PASSWORD = "Tib@ut9981C"

with sync_playwright() as p:

    browser = p.chromium.launch(headless=False)

    context = browser.new_context()

    page = context.new_page()

    page.goto("https://drouot.com")

    # ouvrir le panneau login
    page.locator('[data-cy="header-button-profile"]').click()

    # attendre que le formulaire apparaisse
    page.wait_for_selector("input[type=email]")

    # remplir
    page.fill("input[type=email]", EMAIL)
    page.fill("input[type=password]", PASSWORD)

    # bouton login
    page.click("button[type=submit]")

    page.wait_for_timeout(5000)

    print("Login done")

