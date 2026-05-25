import json
import requests
from google import genai
from google.genai import types

# 1. Initialisation du client Gemini API
client = genai.Client()

# 2. Définition du Prompt Système
system_instruction = """
Tu es un expert senior en analyse de marché secondaire pour les produits de luxe (Horlogerie, Maroquinerie, Joaillerie). Ton objectif est d'évaluer la valeur réelle de revente, la liquidité et de préparer la "due diligence" pour un achat en enchères.

Tu dois impérativement respecter le schéma de sortie JSON suivant :
{
  "item": {
    "brand": "Nom de la marque",
    "model": "Modèle exact",
    "ref": "Référence si trouvable",
    "full_name": "Nom complet qualifié",
    "period": "Année ou époque"
  },
  "condition": {
    "visual_grade": "A/B/C/D",
    "notes": "Remarques sur l'état décrit ou visible"
  },
  "market": {
    "low_estimate_eur": 0,
    "high_estimate_eur": 0,
    "recommended_bid_max": 0,
    "resale_liquidity_score": 0/100,
    "liquidity_trend": "Stable/Bullish/Bearish"
  },
  "due_diligence": {
    "critical_questions": ["Question 1", "Question 2"],
    "red_flags": ["Alerte 1"]
  }
}
"""

# =====================================================================
# NOUVEAU : Fonction de sécurisation de la longueur du texte
# =====================================================================
def clean_and_truncate_text(text, max_chars=5000):
    """Nettoie le texte et le limite pour éviter l'erreur HTTP 500"""
    if not text:
        return "N/A"
    # Convertit en string si ce n'est pas déjà le cas
    text_str = str(text).strip()
    
    if len(text_str) > max_chars:
        print(f"  [Info] Texte trop long détecté ({len(text_str)} caractères). Tronqué à {max_chars}.")
        return text_str[:max_chars] + "... [Texte tronqué pour des raisons techniques]"
    return text_str
# =====================================================================

# 3. Chargement des données depuis votre fichier JSON
chemin_fichier_json = r"C:\Users\commu\Documents\AppEnchere\drouot_export.json" 

with open(chemin_fichier_json, "r", encoding="utf-8") as f:
    lots_a_analyser = json.load(f)
print(f"Structure JSON chargée avec succès ({len(lots_a_analyser)} lots trouvés).\n")

# 4. Boucle de traitement des lots
for lot in lots_a_analyser:
    # Nettoyage et sécurisation des inputs textuels
    titre_propre = clean_and_truncate_text(lot.get('title'), max_chars=200)
    estimation_propre = clean_and_truncate_text(lot.get('estimation'), max_chars=100)
    frais_propre = clean_and_truncate_text(lot.get('frais'), max_chars=50)
    
    # Limitation stricte de la description pour éviter l'erreur 500
    description_propre = clean_and_truncate_text(lot.get('description'), max_chars=4000)

    print(f"Analyse en cours pour : {titre_propre}...")
    
    # Récupération sécurisée de l'image principale
    main_image_url = lot.get("main_image")
    image_data = None
    image_mime = 'image/jpeg'
    
    if main_image_url:
        try:
            img_response = requests.get(main_image_url, timeout=10)
            if img_response.status_code == 200:
                image_data = img_response.content
                image_mime = img_response.headers.get('Content-Type', 'image/jpeg')
        except Exception as e:
            print(f"  [Attention] Impossible de récupérer l'image : {e}")

    # Préparation du prompt textuel sécurisé
    prompt_content = f"""
    Analyse ce lot provenant d'un catalogue d'enchères :
    Titre: {titre_propre}
    Estimation Catalogue: {estimation_propre}
    Frais de vente: {frais_propre}
    Description textuelle: {description_propre}
    """
    
    contents = [prompt_content]
    if image_data:
        contents.append(
            types.Part.from_bytes(
                data=image_data,
                mime_type=image_mime
            )
        )

    # Appel à l'API Gemini avec gestion d'erreur HTTP robuste
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.2
            ),
        )
        
        resultat_analyse = json.loads(response.text)
        print(json.dumps(resultat_analyse, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"  [Erreur 500 ou API] Échec de l'analyse pour ce lot : {e}")
        
    print("-" * 50)