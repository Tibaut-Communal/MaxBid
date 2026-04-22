def compute_max_bid(PR, site_fee_rate, house_fee_rate, L, margin_rate = 0.2, live_fee_rate = 0.018):
    """
    Calcule l'enchère maximale E.
    PR : prix de revente espéré (TTC), en euros.
    site_fee_rate : frais plateforme de revente (ex. 0.10 pour 10%).
    house_fee_rate : frais maison de vente (ex. 0.20 pour 20%).
    live_fee_rate : frais live (ex. 0.018 pour 1.8%).
    margin_rate : marge cible en % du prix d'achat total (ex. 0.20 pour 20%).
    L : frais fixes de livraison/emballage (euros).
    """
    # Net de revente après frais de plateforme et livraison

    net_revenue = PR * (1 - site_fee_rate) - L

    # Dénominateur = (1 + F_vente + F_live) * (1 + marge)

    denominator = (1 + house_fee_rate + live_fee_rate) * (1 + margin_rate)

 

    E = net_revenue / denominator

    return E

 


print("Enchère maximale calculée :", compute_max_bid(300, 0, 0.3, 20))