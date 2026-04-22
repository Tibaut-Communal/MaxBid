def calculate_max_bid(gold_price_rate, weight, margin, bid_fees, digital_fees):

    """

    Returns the maximum bid to keep the desired margin (%) when gold_price_rate is the expected resale value.

    All percentages should be provided as whole numbers (e.g., 10 for 10%).

    """

    resale_value = gold_price_rate * weight

    desired_margin_percent = margin / 100

    total_fees_percent = (bid_fees + digital_fees) / 100

 

    # Calculate maximum bid

    max_bid = resale_value / (1 + desired_margin_percent) / (1 + total_fees_percent)

    return round(max_bid, 2)

 

gold_price_rate = 85    # €/g

weight = 5.38              # grams

margin = 5             # desired margin in percent

bid_fees = 30           # percent

digital_fees = 1.8      # percent

 

max_bid = calculate_max_bid(gold_price_rate, weight, margin, bid_fees, digital_fees)

print("Maximum allowable bid to maintain your margin: €", max_bid)