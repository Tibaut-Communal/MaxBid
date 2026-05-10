
import os
import time
import random
import json
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# --- Configuration ---
EMAIL = "communal.tibaut@gmail.Com"
PASSWORD = "Tib@ut9981C"
STATE_FILE = "state.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# --- Utility Functions ---

def human_delay(a=0.8, b=2.5):
    time.sleep(random.uniform(a, b))

def accept_cookies(page):
    try:
        page.wait_for_timeout(1000)
        selectors = ['button:has-text("Accepter")', 'button:has-text("Tout accepter")', 'button:has-text("Accept all")']
        for sel in selectors:
            if page.locator(sel).count() > 0:
                page.locator(sel).first.click()
                print("[+] Cookies accepted")
                break
    except Exception:
        print("[-] No cookie popup found")

# --- Main Logic Functions ---

def get_favorite_urls():
    """Logs in if necessary and retrieves URLs from the favorites page."""
    urls = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=random.randint(50, 100))
        
        # Session Management
        context = browser.new_context(storage_state=STATE_FILE) if os.path.exists(STATE_FILE) else browser.new_context()
        page = context.new_page()
        
        page.goto("https://drouot.com", timeout=60000)
        human_delay()
        accept_cookies(page)

        if not os.path.exists(STATE_FILE):
            print("[!] Logging in...")
            page.locator('[data-cy="header-button-profile"]').click()
            page.wait_for_selector("input[type=email]")
            
            for char in EMAIL: page.type("input[type=email]", char, delay=random.randint(50, 120))
            for char in PASSWORD: page.type("input[type=password]", char, delay=random.randint(50, 120))
            
            page.locator("button[type=submit]").click()
            human_delay(4, 6)
            context.storage_state(path=STATE_FILE)

        # Navigate to favorites
        page.goto("https://drouot.com/fr/account/favorites")
        page.wait_for_selector('[data-cy^="lot-cell-Grid"]')
        
        # Infinite Scroll simulation
        for _ in range(random.randint(2, 4)):
            page.mouse.wheel(0, random.randint(800, 1200))
            human_delay(1, 2)

        links = page.locator('[data-cy^="lot-cell-Grid"] a[href*="/l/"]')
        urls = links.evaluate_all("elements => elements.map(e => e.href)")
        
        browser.close()
    return urls

def extract_lot_details(url):
    """Uses BeautifulSoup to extract text data and the main image base URL."""
    print(f"[*] Extracting details for: {url}")
    response = requests.get(url, headers=HEADERS)
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")

    # JSON-LD Data
    data_json = soup.find("script", type="application/ld+json")
    json_data = json.loads(data_json.string) if data_json else {}

    # Extraction logic
    details = {
        "title": json_data.get("name"),
        "main_image": json_data.get("image"),
        "estimation": next((span.text.strip() for span in soup.find_all("span") if "€" in span.text and "-" in span.text), "N/A"),
        "fees": soup.find("div", class_="text-paragraph-100 font-medium leading-tight").get_text(strip=True) if soup.find("div", class_="text-paragraph-100 font-medium leading-tight") else "N/A",
        "description": "\n".join(line.strip() for line in soup.find("p", class_="whitespace-pre-line").get_text().splitlines() if line.strip()) if soup.find("p", class_="whitespace-pre-line") else ""
    }
    return details

def scrape_all_images(url, main_image_url):
    """Launches Playwright to capture all high-res images from the carousel."""
    image_urls = set()
    base_img_path, _, _ = main_image_url.rpartition('/')
    search_pattern = base_img_path.replace("ftall", "fullHD")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Intercept network responses to find image URLs
        page.on("response", lambda res: image_urls.add(res.url) if "cdn.drouot.com/d/image/lot" in res.url else None)
        
        page.goto(url, wait_until="networkidle")
        
        # Click through carousel
        for _ in range(10):
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(800)
            
        browser.close()

    return [img for img in image_urls if search_pattern in img]

# --- Execution ---

if __name__ == "__main__":
    # 1. Get List of Lots
    favorite_urls = get_favorite_urls()
    print(f"[+] Found {len(favorite_urls)} items.")

    if favorite_urls:
        # 2. Process an example URL (e.g., the first one)
        target_url = favorite_urls[0]
        
        # 3. Get Text Metadata
        data = extract_lot_details(target_url)
        print(data)
        
        # 4. Get High-Res Images
        if data['main_image']:
            all_images = scrape_all_images(target_url, data['main_image'])
            print(f"Found {len(all_images)} high-res images.")
            for img in all_images:
                print(f"  - {img}")
