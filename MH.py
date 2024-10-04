import numpy as np
import matplotlib.pyplot as plt

# Function to calculate the sinusoidal product for a given prime
def prime_sin_product(x, prime):
    product = 1
    for shift in range(prime - 1):
        product *= np.sin(np.pi * (x - shift) / prime)
    return product

# Function to calculate the finalizing formula for a given range of x and primes
def finalizing_formula(x_values, primes):
    total_sum = np.zeros_like(x_values, dtype=float)
    
    for prime in primes:
        # Summing the products of the sinusoidal functions (no absolute values)
        total_sum += prime_sin_product(x_values, prime)
    
    return total_sum

# Function to plot the result of the finalizing formula in increments of 0.01
def plot_finalizing_formula(max_x, primes):
    x_values = np.arange(1, max_x + 0.01, 0.01)  # Range of x values with increments of 0.01
    y_values = finalizing_formula(x_values, primes)  # Calculate Y values
    
    # Plot the results
    plt.plot(x_values, y_values, label="Y (finalizing formula)")
    plt.title(f"Finalizing Formula Plot for Primes: {primes}")
    plt.xlabel("x")
    plt.ylabel("Y")
    plt.grid(True)
    plt.show()

# Parameters
max_x = 10  # Define the maximum value for x
primes = [2, 3, 5, 7, 11, 13, 17]  # List of prime numbers

# Plot the result for the given range of x and primes
plot_finalizing_formula(max_x, primes)
