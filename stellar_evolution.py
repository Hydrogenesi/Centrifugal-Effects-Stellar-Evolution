import numpy as np
from scipy.integrate import odeint
import matplotlib.pyplot as plt

# Constants
G = 6.67408e-11  # Gravitational constant (m^3 kg^-1 s^-2)
c = 299792458  # Speed of light (m/s)
a = 7.5657e-16  # Radiation constant (J/m^3K^4)

# Stellar Structure Equations
def hydrostatic_equilibrium(rho: float, M: float, r: float) -> float:
    """Compute hydrostatic equilibrium."""
    if r == 0:
        return 0.0
    return -rho * G * M / r**2

def energy_generation(rho: float, epsilon: float, dM: float) -> float:
    """Compute energy generation."""
    return epsilon * rho * dM

def radiative_transfer(kappa: float, rho: float, L: float, r: float, T: float) -> float:
    """Compute radiative transfer."""
    return -3 * kappa * rho * L / (16 * np.pi * a * c * T**3)

# Nuclear Reaction Rates
def proton_proton_chain(T: float, rho: float) -> float:
    """Compute proton-proton chain reaction rate."""
    return T**4 * rho**2

def CNO_cycle(T: float, rho: float) -> float:
    """Compute CNO cycle reaction rate."""
    return T**19 * rho

# Opacity
def kappa(rho: float, T: float) -> float:
    """Compute opacity."""
    return 1e-2 * rho**0.5 * T**-3

# Stellar Evolution Timescales
def main_sequence_lifetime(M: float, L: float) -> float:
    """Compute main sequence lifetime."""
    return M / L

# Differential Equations
def stellar_evolution(state: list, t: float, M: float) -> list:
    """
    Compute stellar evolution differential equations.

    NOTE: This is a simplified model. The time variable 't' is used as the
    radius 'r' in some calculations, which is a significant simplification
    and can lead to physical inaccuracies.
    """
    rho, L, T = state

    # In the original model, time 't' is used for radius 'r'. This is
    # problematic as t starts from 0. We use 't' but handle the t=0 case
    # in hydrostatic_equilibrium. A more robust model would separate time
    # and radius.
    r = t

    pressure_gradient_term = hydrostatic_equilibrium(rho, M, r)

    # Using a constant epsilon as in the original context.
    epsilon = 1e-6
    # The original code passed a pressure gradient term as a proxy for dM.
    dLdt = energy_generation(rho, epsilon, pressure_gradient_term)

    dTdt = radiative_transfer(kappa(rho, T), rho, L, r, T)

    if r == 0:
        drhodt = 0.0
    else:
        drhodt = -pressure_gradient_term / (4 * np.pi * r**2)

    return [drhodt, dLdt, dTdt]

# Initial Conditions
def initial_conditions(M: float) -> list:
    """Compute initial conditions."""
    return [1e3, 1e26, 1e7]

def main():
    """Main function to run the simulation and plot results."""
    # We start time from a small positive number to avoid division by zero
    # in the original model's use of t as r.
    t = np.linspace(1e5, 1e10, 1000)

    M_values = [1e30, 5e30, 1e31]

    for M in M_values:
        state0 = initial_conditions(M)
        solution = odeint(stellar_evolution, state0, t, args=(M,))

        plt.figure(figsize=(10, 6))
        plt.plot(t, solution[:, 0], label='Density')
        plt.plot(t, solution[:, 1], label='Luminosity')
        plt.plot(t, solution[:, 2], label='Temperature')
        plt.xlabel('Time (s) / Radius (m)')
        plt.ylabel('Value')
        plt.title(f'Stellar Evolution (M={M:.1e} kg)')
        plt.legend()
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    main()
