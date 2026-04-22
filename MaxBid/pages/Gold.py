import streamlit as st
from AllItems.CalculationGold import calculate_max_bid

st.title("Calculateur Or 🪙")

st.write("Calcule ton enchère max basée sur le prix de l'or au poids.")

gold_price_rate = st.number_input("Prix de l'or (€ / gramme)", value=60.0)
weight = st.number_input("Poids (grammes)", value=10.0)
margin = st.number_input("Marge souhaitée (%)", value=20.0)
bid_fees = st.number_input("Frais enchères (%)", value=20.0)
digital_fees = st.number_input("Frais live (%)", value=1.8)

if st.button("Calculer"):
    max_bid = calculate_max_bid(
        gold_price_rate,
        weight,
        margin,
        bid_fees,
        digital_fees
    )

    resale_value = gold_price_rate * weight

    st.subheader("Résultats")
    st.write(f"Valeur de revente estimée : **{resale_value:.2f} €**")
    st.write(f"Enchère maximale : **{max_bid:.2f} €**")