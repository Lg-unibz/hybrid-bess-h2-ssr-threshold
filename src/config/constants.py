"""
Constants — Physical and economic constants for the energy-system model.
========================================================================

Every constant has units documented in its docstring so that
downstream code can be read like a physics textbook.

Naming convention
-----------------
``<QUANTITY>_<UNIT>``  e.g. ``H2_LHV_KWH_KG`` means
"Hydrogen Lower Heating Value expressed in kWh per kg".

Sources
-------
* H₂ heating values — ISO 6976:2016, NIST WebBook.
* Faraday constant  — 2018 CODATA.
* Water density     — at 25 °C, 1 atm.
* Molar masses      — IUPAC 2021.

All values are rounded for engineering accuracy (4–5 significant digits).
"""

# ===================================================================== #
#  HYDROGEN THERMOCHEMISTRY                                             #
# ===================================================================== #

H2_LHV_KWH_KG: float = 33.33
"""Lower Heating Value of H₂ [kWh/kg].

Physics
-------
The LHV (net calorific value) excludes the latent heat of
water-vapour condensation.  It is the reference for PEM fuel-cell
and electrolyzer efficiency definitions in most European standards.

Source: ISO 6976:2016 → 119.96 MJ/kg → 33.32 kWh/kg (≈ 33.33).
"""

H2_HHV_KWH_KG: float = 39.41
"""Higher Heating Value of H₂ [kWh/kg].

Physics
-------
The HHV (gross calorific value) accounts for the enthalpy
released when product water condenses back to liquid at 25 °C.

.. math::
    HHV = LHV + n_{H_2O} \\cdot h_{fg}

For H₂:  HHV = 141.88 MJ/kg → 39.41 kWh/kg.

Source: NIST WebBook; ISO 6976:2016.
"""

H2_LHV_MJ_KG: float = 119.96
"""Lower Heating Value of H₂ [MJ/kg].  Convenience alias."""

H2_HHV_MJ_KG: float = 141.88
"""Higher Heating Value of H₂ [MJ/kg].  Convenience alias."""

H2_DENSITY_KG_M3_STP: float = 0.08988
"""Density of H₂ gas at STP (0 °C, 1 atm) [kg/m³].

Source: NIST Standard Reference Database 69.
"""

H2_MOLAR_MASS_KG_MOL: float = 2.016e-3
"""Molar mass of H₂ [kg/mol].

Source: IUPAC 2021 — M(H₂) = 2.016 g/mol.
"""


# ===================================================================== #
#  WATER                                                                #
# ===================================================================== #

WATER_DENSITY_KG_M3: float = 997.0
"""Density of liquid water at 25 °C, 1 atm [kg/m³].

Used to size water supply for electrolysis (≈ 9 kg H₂O per kg H₂).

Source: CRC Handbook of Chemistry and Physics, 97th Edition.
"""

WATER_CONSUMPTION_KG_PER_KG_H2: float = 8.94
"""Stoichiometric water consumption for electrolysis [kg_H₂O / kg_H₂].

Physics
-------
From the balanced reaction:

.. math::
    2 H_2O \\rightarrow 2 H_2 + O_2

Mass ratio: M(2·H₂O) / M(2·H₂) = 36.03 / 4.032 ≈ 8.94.
Real systems consume ≈ 9–10 kg/kg including purification losses.
"""


# ===================================================================== #
#  ELECTROCHEMISTRY                                                     #
# ===================================================================== #

FARADAY_CONSTANT_C_MOL: float = 96_485.332
"""Faraday constant [C/mol].

Number of Coulombs per mole of electrons transferred.

Source: 2018 CODATA — F = 96 485.33212 C/mol.
"""

UNIVERSAL_GAS_CONSTANT_J_MOL_K: float = 8.31446
"""Universal gas constant R [J/(mol·K)].

Source: 2018 CODATA — R = 8.314 462 618 J·mol⁻¹·K⁻¹.
"""

STANDARD_TEMPERATURE_K: float = 298.15
"""Standard reference temperature [K]  (25 °C)."""


# ===================================================================== #
#  SOLAR / PV                                                           #
# ===================================================================== #

STC_IRRADIANCE_W_M2: float = 1000.0
"""Standard Test Conditions irradiance [W/m²].

PV module ratings (kWp) are specified at this irradiance
and a cell temperature of 25 °C.
"""

STC_TEMPERATURE_C: float = 25.0
"""Standard Test Conditions cell temperature [°C]."""

NOCT_IRRADIANCE_W_M2: float = 800.0
"""Irradiance used in the NOCT definition [W/m²].

Physics
-------
The Nominal Operating Cell Temperature (NOCT) is measured
at G = 800 W/m², T_amb = 20 °C, wind = 1 m/s.

.. math::
    T_{cell} = T_{amb} + \\frac{NOCT - 20}{800} \\cdot G
"""

NOCT_AMBIENT_TEMPERATURE_C: float = 20.0
"""Ambient temperature in the NOCT definition [°C]."""





# ===================================================================== #
#  UNIT CONVERSIONS                                                     #
# ===================================================================== #

KWH_TO_MJ: float = 3.6
"""Conversion factor: 1 kWh = 3.6 MJ."""

MJ_TO_KWH: float = 1.0 / 3.6
"""Conversion factor: 1 MJ ≈ 0.2778 kWh."""

BAR_TO_PA: float = 1.0e5
"""Conversion factor: 1 bar = 100 000 Pa."""

HOURS_PER_YEAR: float = 8760.0
"""Hours in a non-leap year."""
