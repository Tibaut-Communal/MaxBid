import streamlit as st
from AllItems.CalculationItem import compute_max_bid

def main():
    st.title("Calculateur d'enchère maximale")

    st.write("Calcule ton enchère maximale à partir d'un prix de revente cible, "
             "des frais et d'une marge exprimée en % du prix d'achat total.")

    st.header("Paramètres de revente")

    PR = st.number_input("Prix de revente espéré (PR) en €", min_value=0, value=500, step=10)

    site_fee_percent = st.number_input("Frais de plateforme de revente (%)", min_value=0.0, max_value=100.0, value=10.0, step=0.5)
    house_fee_percent = st.number_input("Frais maison de vente (%)", min_value=0.0, max_value=100.0, value=30.0, step=0.5)
    live_fee_percent = st.number_input("Frais live (%)", min_value=0.0, max_value=100.0, value=1.8, step=0.1)

    L = st.number_input("Frais fixes de livraison / emballage (L) en €", min_value=0.0, value=20.0, step=1.0)

    margin_percent = st.number_input("Marge nette souhaitée (% du prix d'achat total)", min_value=0.0, max_value=500.0, value=20.0, step=1.0)

    if st.button("Calculer l'enchère maximale"):
        # Conversion des pourcentages en taux décimaux
        site_fee_rate = site_fee_percent / 100.0
        house_fee_rate = house_fee_percent / 100.0
        live_fee_rate = live_fee_percent / 100.0
        margin_rate = margin_percent / 100.0

        E = compute_max_bid(PR, site_fee_rate, house_fee_rate, L, live_fee_rate, margin_rate)

        # Calculs complémentaires pour afficher un résumé
        net_revenue = PR * (1 - site_fee_rate) 
        purchase_cost = E * (1 + house_fee_rate + live_fee_rate) + L
        profit = net_revenue - purchase_cost
        actual_margin_rate = profit / purchase_cost if purchase_cost > 0 else 0

        st.subheader("Résultats")
        st.write(f"Enchère maximale (E) : **{E:.2f} €**")
        st.write(f"Prix d'achat total (enchère + frais vente + frais live) : **{purchase_cost:.2f} €**")
        st.write(f"Net à la revente après plateforme et livraison : **{net_revenue:.2f} €**")
        st.write(f"Marge nette (en €) : **{profit:.2f} €**")
        st.write(f"Marge nette réelle : **{actual_margin_rate*100:.2f} %**")

        st.info("La marge nette réelle affichée doit être proche de la marge souhaitée si les paramètres sont cohérents.")


if __name__ == "__main__":
    main()
