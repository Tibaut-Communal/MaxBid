# old code

from playwright.sync_api import sync_playwright
import time
import random
import os
import requests
from bs4 import BeautifulSoup
import json




EMAIL = "communal.tibaut@gmail.Com"
PASSWORD = "Tib@ut9981C"
STATE_FILE = "state.json"

def human_delay(a=0.8, b=2.5):
    time.sleep(random.uniform(a, b))

def accept_cookies(page):
    try:
        page.wait_for_timeout(1000)

        # essayer plusieurs variantes possibles
        selectors = [
            'button:has-text("Accepter")',
            'button:has-text("Tout accepter")',
            'button:has-text("Accept all")'
        ]

        for sel in selectors:
            if page.locator(sel).count() > 0:
                page.locator(sel).first.click()
                print("Cookies accepted")
                break

    except:
        print("No cookie popup")


with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=False,
        slow_mo=random.randint(50, 120)
    )

    # 👉 Charger session si elle existe
    if os.path.exists(STATE_FILE):
        context = browser.new_context(storage_state=STATE_FILE)
        print("Session loaded")
    else:
        context = browser.new_context()
        print("No session found, logging in...")

    page = context.new_page()

    page.goto("https://drouot.com", timeout=60000)
    human_delay()
    accept_cookies(page)
    
    # Si pas de session → login
    if not os.path.exists(STATE_FILE):

        page.mouse.wheel(0, random.randint(200, 800))
        human_delay()

        page.locator('[data-cy="header-button-profile"]').click()
        page.wait_for_selector("input[type=email]")

        # typing humain
        for char in EMAIL:
            page.type("input[type=email]", char, delay=random.randint(50, 150))
        human_delay()

        for char in PASSWORD:
            page.type("input[type=password]", char, delay=random.randint(50, 150))
        human_delay()

        btn = page.locator("button[type=submit]")
        btn.hover()
        human_delay(0.3, 1)

        btn.click()
        human_delay(4, 7)

        # 👉 Sauvegarde session
        context.storage_state(path=STATE_FILE)
        print("Session saved")

    # Aller aux favoris
    page.goto("https://drouot.com/fr/account/favorites")
    human_delay(2, 4)

    print("On favorites page")

    page.wait_for_selector('[data-cy^="lot-cell-Grid"]')

    # Scroll pour charger contenu
    for _ in range(random.randint(2, 5)):
        page.mouse.wheel(0, random.randint(800, 1500))
        human_delay(1, 2)

    # Récupérer les liens
    links = page.locator('[data-cy^="lot-cell-Grid"] a[href*="/l/"]')
    urls = links.evaluate_all("elements => elements.map(e => e.href)")

    print(f"{len(urls)} lots trouvés")
    print(urls)

    input("press enter to close...")

urls[1]
# for url in urls[1] :

url = urls[1]
url = "https://drouot.com/fr/l/33535913-louis-vuitton-neverfull-mm-sac-cabas-en-cuir-epis-bleu"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)
# UTF-8 IMPORTANT
response.encoding = "utf-8"

soup = BeautifulSoup(response.text, "html.parser")

# ---------------------------
# 1. JSON LD (titre, image…)
# ---------------------------
data_json = soup.find("script", type="application/ld+json")

data = {}
if data_json:
    data = json.loads(data_json.string)

titre = data.get("name")
# description_json = data.get("description")
Mainimage = data.get("image")

# ---------------------------
# 2. Estimation
# ---------------------------
estimation = None
for span in soup.find_all("span"):
    if "€" in span.text and "-" in span.text:
        estimation = span.text.strip()
        break

# ---------------------------
# 3. Frais
# ---------------------------
frais = None


frais = soup.find(
    "div",
    class_="text-paragraph-100 font-medium leading-tight"
).get_text("\n", strip=True)

# ---------------------------
# 4. Description complète
# ---------------------------

description = soup.find(
    "p",
    class_="whitespace-pre-line"
).get_text("\n", strip=True)

description = "\n".join(
    line.strip()
    for line in description.splitlines()
    if line.strip()
)
# ---------------------------
# OUTPUT
# ---------------------------


print("Titre:", titre)
print("Estimation:", estimation)
print("Frais:", frais)
print("Description:", description)

print("Images:", Mainimage)


base_url, separator, tail = Mainimage.rpartition('/')

base_url = base_url.replace("ftall","fullHD")
base_url

with sync_playwright() as p:

    browser = p.chromium.launch(headless=False)

    page = browser.new_page()

    image_urls = set()

    def handle_response(response):

        url = response.url

        if "cdn.drouot.com/d/image/lot" in url:
            image_urls.add(url)

    page.on("response", handle_response)

    page.goto(url, wait_until="networkidle")

    # faire défiler carousel
    for _ in range(10):

        try:
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(1000)

        except:
            pass

    allimgs_urls = [item for item in image_urls if base_url in item]

    print(list(allimgs_urls))

    browser.close()

