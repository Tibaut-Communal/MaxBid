import os
import time
import random
import json
from playwright.sync_api import sync_playwright

# --- Configuration ---
EMAIL = "communal.tibaut@gmail.Com"
PASSWORD = "Tib@ut9981C"
STATE_FILE = "state.json"

def human_delay(a=1.5, b=4.0):
    time.sleep(random.uniform(a, b))

def accept_cookies(page):
    try:
        selectors = ['button:has-text("Accepter")', 'button:has-text("Tout accepter")']
        for sel in selectors:
            if page.locator(sel).count() > 0:
                page.locator(sel).first.click()
                break
    except: pass
    
def scrape_lot_data(page, url):
    print(f"[*] Extracting: {url}")
    
    image_urls = set()
    page.on("response", lambda res: image_urls.add(res.url) if "cdn.drouot.com/d/image/lot" in res.url else None)
    
    page.goto(url, wait_until="networkidle")
    human_delay(1.5, 3)

    # 1. Get Metadata + Image Count
    data = page.evaluate("""() => {
        const jsonLd = JSON.parse(document.querySelector('script[type="application/ld+json"]')?.innerText || "{}");
        
        // Find the "1 / 5" text to get the total number of images
        let totalImages = 1;
        const counterEl = document.querySelector('div.text-paragraph-300.text-center.uppercase');
        if (counterEl && counterEl.innerText.includes('/')) {
            const parts = counterEl.innerText.split('/');
            totalImages = parseInt(parts[1].trim());
        }

        let est = "N/A";
        const spans = Array.from(document.querySelectorAll('span'));
        const foundEst = spans.find(s => s.innerText.includes('€') && s.innerText.includes('-'));
        if (foundEst) est = foundEst.innerText.trim();

        // =====================================================================
        // OPTIMISATION SÉCURISÉE DES FRAIS DE VENTE (CORRIGÉE)
        // =====================================================================
        let frais = "N/A";
        const headings = Array.from(document.querySelectorAll('h2'));
        const fraisHeading = headings.find(h => h.innerText && h.innerText.includes('Frais de vente'));
        
        if (fraisHeading) {
            let nextEl = fraisHeading.nextElementSibling;
            
            if (nextEl) {
                const targetFrais = nextEl.querySelector('div.text-paragraph-100.font-medium.leading-tight') || 
                                    (nextEl.classList.contains('text-paragraph-100') ? nextEl : null);
                
                if (targetFrais) {
                    // Utilisation de replaceAll sans Regex pour éviter les conflits d'échappement Python/JS
                    frais = targetFrais.innerText.replaceAll('\\n', ' ').trim();
                } else {
                    frais = nextEl.innerText.replaceAll('\\n', ' ').trim();
                }
            }
        }
        // =====================================================================

        const descEl = document.querySelector('p.whitespace-pre-line');
        const desc = descEl ? descEl.innerText.trim() : "";

        return {
            title: jsonLd.name,
            main_image: jsonLd.image,
            estimation: est,
            frais: frais,
            description: desc,
            total_images: totalImages
        };
    }""")

    # 2. Dynamic Carousel Loop
    num_to_press = data['total_images']
    print(f"    -> Found {num_to_press} images. Scrolling carousel...")
    
    for _ in range(num_to_press):
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(random.randint(400, 700))

    # 3. Filter images
    if data['main_image']:
        base_img_path = data['main_image'].rpartition('/')[0].replace("ftall", "fullHD")
        data['all_images'] = [img for img in image_urls if base_img_path in img]
    else:
        data['all_images'] = []
    
    return data
def run_bot():
    all_results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        
        # 1. Préparation de la session si elle existe
        context_args = {}
        if os.path.exists(STATE_FILE):
            context_args["storage_state"] = STATE_FILE
            print("[*] Tentative de chargement de la session enregistrée...")
        
        context = browser.new_context(
            **context_args,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        
        page = context.new_page()
        
        # 2. Navigation initiale
        page.goto("https://drouot.com")
        accept_cookies(page)
        human_delay(2, 4)
# =====================================================================
        # DÉTECTION DYNAMIQUE DE L'AUTHENTIFICATION (CORRIGÉE STRICTE)
        # =====================================================================
        is_logged_in = False
        try:
            print("[*] Vérification de l'état de la session...")
            page.goto("https://drouot.com/fr/account/favorites", wait_until="networkidle")
            
            # Si l'URL contient "login", Drouot nous a redirigé car les cookies ont expiré
            if "/login" in page.url:
                is_logged_in = False
                print("[!] Redirection vers la page de login détectée. La session a expiré.")
            elif "account/favorites" in page.url:
                is_logged_in = True
                print("[+] Session valide ! Accès direct aux favoris.")
        except Exception as e:
            print(f"[!] Erreur lors de la vérification de session : {e}")
            is_logged_in = False

        # Si nous ne sommes pas connectés (redirection ou session absente)
        if not is_logged_in:
            print("[!] Connexion requise. Lancement de la procédure d'authentification...")
            
            # Si on a été redirigé, les champs de login sont déjà là. 
            # Sinon, on force l'accès à la page de connexion.
            if "/login" not in page.url:
                page.goto("https://drouot.com/fr/login")
                human_delay(2, 3)
            
            # Attente et saisie des identifiants (Email + Password)
            page.wait_for_selector("input[type=email]")
            page.type("input[type=email]", EMAIL, delay=random.randint(50, 100))
            page.type("input[type=password]", PASSWORD, delay=random.randint(50, 100))
            
            # Clic sur le bouton de soumission
            page.locator("button[type=submit]").click()
            
            # # Attente que la connexion se finalise et redirige vers les favoris
            # page.wait_for_url("**/account/favorites", timeout=10000)
            
            # Sauvegarde du nouvel état de session valide
            context.storage_state(path=STATE_FILE)
            print("[+] Connexion réussie et nouvelle session enregistrée.")
            human_delay(3, 5)
        # =====================================================================
        
        
        # Collect all lot URLs
        links = page.locator('[data-cy^="lot-cell-Grid"] a[href*="/l/"]')
        urls = links.evaluate_all("elements => elements.map(e => e.href)")
        
        print(f"[+] Found {len(urls)} items. Starting extraction...")

        # Loop through items with human-like behavior
        for target_url in urls[:17]:
            try:
                lot_info = scrape_lot_data(page, target_url)
                all_results.append(lot_info)
                
                print(f"    -> Extracted: {lot_info['title'][:30]}...")
                print(f"    -> Est: {lot_info['estimation']} | Fees: {lot_info['frais']}")
                
                # Random cooldown between items to mimic human reading time
                human_delay(4, 8) 
            except Exception as e:
                print(f"[-] Error on {target_url}: {e}")

        browser.close()
    
    return all_results

if __name__ == "__main__":
    results = run_bot()
    
    # Save to JSON
    with open("drouot_export.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    
    print(f"\n[DONE] Saved {len(results)} items to drouot_export.json")