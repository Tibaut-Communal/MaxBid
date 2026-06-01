import json
import os
import requests
import traceback
from google import genai
from google.genai import types

# 1. Initialisation du client Gemini API
client = genai.Client()

# 2. Définition du Prompt Système (Mis à jour pour dissocier l'estimation catalogue du marché de l'occasion)
system_instruction = """
Tu es un expert senior en analyse de marché secondaire pour les produits de luxe (Horlogerie, Maroquinerie, Joaillerie). Ton objectif est d'évaluer la valeur réelle de revente sur le marché de l'occasion, la liquidité et de préparer la "due diligence" pour un achat en enchères.

CRUCIAL POUR LES PRIX : 
Ne recopie JAMAIS l'estimation du catalogue d'enchères fournie en entrée. L'estimation du catalogue est souvent volontairement basse pour attirer les acheteurs. 
Tu dois estimer la VRAIE valeur de transaction finale sur le marché secondaire (ex: prix constatés sur Chrono24, Vestiaire Collective, eBay, ou plateformes spécialisées) selon l'état de l'objet.
Si il n'y a pas de fees ou que la valeur est étrange, part du principe que c'est 30%.

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
    "resale_low_estimate_market_eur": 0,
    "resale_high_estimate_market_eur": 0,
    "recommended_bid_max": 0,
    "resale_liquidity_score": 0,
    "liquidity_trend": "Stable/Bullish/Bearish"
  },
  "due_diligence": {
    "critical_questions": ["Question 1", "Question 2"],
    "red_flags": ["Alerte 1"]
  }
}
"""
def clean_and_truncate_text(text, max_chars=5000):
    """Nettoie le texte et le limite pour éviter l'erreur HTTP 500"""
    if not text:
        return "N/A"
    text_str = str(text).strip()
    if len(text_str) > max_chars:
        print(f"  [Info] Texte trop long détecté ({len(text_str)} caractères). Tronqué à {max_chars}.")
        return text_str[:max_chars] + "... [Texte tronqué]"
    return text_str

# 3. Chemins des fichiers
chemin_fichier_json = r"C:\Users\commu\Documents\AppEnchere\drouot_export.json" 
chemin_sortie_json = r"C:\Users\commu\Documents\AppEnchere\drouot_analyses.json"
chemin_erreurs_json = r"C:\Users\commu\Documents\AppEnchere\drouot_erreurs.json"

with open(chemin_fichier_json, "r", encoding="utf-8") as f:
    lots_a_analyser = json.load(f)
print(f"Structure JSON chargée avec succès ({len(lots_a_analyser)} lots trouvés).\n")

# =====================================================================
# Chargement des historiques (Analyses + Erreurs existantes)
# =====================================================================
analyses_sauvegardees = []
if os.path.exists(chemin_sortie_json):
    try:
        with open(chemin_sortie_json, "r", encoding="utf-8") as f:
            analyses_sauvegardees = json.load(f)
        print(f"[Backup] {len(analyses_sauvegardees)} analyses existantes chargées.")
    except Exception:
        pass

erreurs_sauvegardees = []
if os.path.exists(chemin_erreurs_json):
    try:
        with open(chemin_erreurs_json, "r", encoding="utf-8") as f:
            erreurs_sauvegardees = json.load(f)
        print(f"[Backup] {len(erreurs_sauvegardees)} historiques d'erreurs chargés.")
    except Exception:
        pass
# =====================================================================

# 4. Boucle de traitement des lots
for i, lot in enumerate(lots_a_analyser):
    titre_propre = clean_and_truncate_text(lot.get('title'), max_chars=200)
    
    # Évite de ré-analyser un lot déjà validé OU déjà répertorié en erreur
    deja_analyse = any(a.get("source_title") == titre_propre for a in analyses_sauvegardees)
    deja_en_erreur = any(e.get("source_title") == titre_propre for e in erreurs_sauvegardees)
    
    if deja_analyse:
        print(f"[{i+1}/{len(lots_a_analyser)}] Déjà analysé (Sauté) : {titre_propre}")
        continue
    if deja_en_erreur:
        print(f"[{i+1}/{len(lots_a_analyser)}] Déjà connu comme en erreur (Sauté) : {titre_propre}")
        continue

    estimation_propre = clean_and_truncate_text(lot.get('estimation'), max_chars=100)
    frais_propre = clean_and_truncate_text(lot.get('frais'), max_chars=50)
    description_propre = clean_and_truncate_text(lot.get('description'), max_chars=4000)

    print(f"[{i+1}/{len(lots_a_analyser)}] Analyse en cours pour : {titre_propre}...")
    
    main_image_url = lot.get("main_image")
    image_data = None
    image_mime = 'image/jpeg'
    statut_image = "Aucune image fournie"
    
    if main_image_url:
        try:
            img_response = requests.get(main_image_url, timeout=10)
            if img_response.status_code == 200:
                image_data = img_response.content
                image_mime = img_response.headers.get('Content-Type', 'image/jpeg')
                statut_image = "Téléchargée avec succès"
            else:
                statut_image = f"Échec HTTP {img_response.status_code}"
        except Exception as img_err:
            statut_image = f"Erreur de connexion : {str(img_err)}"
            print(f"  [Attention] Impossible de récupérer l'image : {img_err}")

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
        resultat_analyse["source_title"] = titre_propre
        resultat_analyse["source_url"] = lot.get("url", "N/A")
        
        # Sauvegarde Succès
        analyses_sauvegardees.append(resultat_analyse)
        with open(chemin_sortie_json, "w", encoding="utf-8") as f_out:
            json.dump(analyses_sauvegardees, f_out, indent=2, ensure_ascii=False)
        
        print(f"  [Succès] Ajouté aux analyses.")
        
    except Exception as e:
        print(f"  [Erreur] Échec de l'analyse. Enregistrement dans le fichier des erreurs...")
        
        # =====================================================================
        # NOUVEAU : Structure complète du log d'erreur
        # =====================================================================
        rapport_erreur = {
            "source_title": titre_propre,
            "source_url": lot.get("url", "N/A"),
            "statut_image": statut_image,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc(), # Donne la ligne exacte du code qui a planté
            "input_lengths": {
                "title_chars": len(titre_propre),
                "description_chars": len(description_propre),
                "has_image_binary": image_data is not None
            }
        }
        
        erreurs_sauvegardees.append(rapport_erreur)
        with open(chemin_erreurs_json, "w", encoding="utf-8") as f_err:
            json.dump(erreurs_sauvegardees, f_err, indent=2, ensure_ascii=False)
        # =====================================================================
        
    print("-" * 50)

print(f"\n[+] Script terminé.")
print(f" -> Analyses réussies : {chemin_sortie_json}")
print(f" -> Logs des erreurs : {chemin_erreurs_json}")