# chat gpt result for limit trnache with specific avg price

def generate_limit_orders(total_amount, upper_limit, lower_limit, desired_avg_price, number_of_orders):
    # Calculate the spacing between prices using the cubic formula
    a = 4 * (desired_avg_price - lower_limit) / ((number_of_orders - 1) ** 3)
    b = -6 * (desired_avg_price - lower_limit) / ((number_of_orders - 1) ** 2)
    c = 4 * (desired_avg_price - lower_limit) / (number_of_orders - 1)

    price_spacing = lambda i: a * (i ** 3) + b * (i ** 2) + c * i + lower_limit

    # Generate limit orders
    orders = []
    total_amount_left = total_amount
    avg_price = 0.0

    for i in range(number_of_orders):
        price = price_spacing(i)
        amount = total_amount / number_of_orders

        if price > upper_limit:
            price = upper_limit

        order = (price, amount)
        orders.append(order)

        avg_price = ((avg_price * (total_amount - amount)) + (price * amount)) / total_amount
        total_amount_left -= amount

    # Adjust the last order to reach the desired average price
    last_order = orders[-1]
    last_price, last_amount = last_order
    price_diff = desired_avg_price - avg_price
    last_order = (last_price + price_diff, last_amount)
    orders[-1] = last_order

    return orders

# Input parameters
total_amount = 1000
upper_limit = 50
lower_limit = 10
desired_avg_price = 25
number_of_orders = 10  # You can specify the desired number of orders

# Generate limit orders
limit_orders = generate_limit_orders(total_amount, upper_limit, lower_limit, desired_avg_price, number_of_orders)

# Display the generated orders
for i, (price, amount) in enumerate(limit_orders):
    print(f"Order {i + 1}: Price = {price:.2f}, Amount = {amount:.2f}")

# Calculate the actual average price of the orders
actual_avg_price = sum(price * amount for price, amount in limit_orders) / total_amount
print(f"Actual Average Price: {actual_avg_price:.2f}")









