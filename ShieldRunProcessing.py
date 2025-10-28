import pandas as pd
import numpy as np

def load_TC_data(filepath):
    """
    Loads CSV with a datetime RealTimestamp column and returns:
    - time_s : seconds since start (numpy array)
    - V_Baratron : downstream baratron voltage (numpy array)
    - V_Wasp : wasp voltage (numpy array)
    - df : cleaned DataFrame with Python-safe column names
    """
    # Read CSV
    df = pd.read_csv(filepath)

    # Parse datetimes
    df["RealTimestamp"] = pd.to_datetime(df["RealTimestamp"], errors="coerce")

    # Time since start (0 = first row)
    t0 = df["RealTimestamp"].iloc[0]
    time_s = (df["RealTimestamp"] - t0).dt.total_seconds().to_numpy()

    # Rename columns to be Python-friendly
    df = df.rename(columns=lambda x: x.strip().replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_per_"))

    return time_s, df

def volts_to_temp_constants(mv: float) -> tuple[float, ...]:
    """
    Select the appropriate NIST ITS-90 polynomial coefficients for converting
    Type K thermocouple voltage (in millivolts) to temperature (°C).

    The valid voltage range is -5.891 mV to 54.886 mV.

    args:
        mv: Thermocouple voltage in millivolts.

    returns:
        tuple of float: Polynomial coefficients for the voltage-to-temperature conversion.

    raises:
        ValueError: If the input voltage is out of the valid range.
    """
    # Use a small tolerance for floating-point comparison
    if mv < -5.892 or mv > 54.887:
        raise ValueError("Voltage out of valid Type K range (-5.891 to 54.886 mV).")
    if mv < 0:
        # Range: -5.891 mV to 0 mV
        return (
            0.0e0,
            2.5173462e1,
            -1.1662878e0,
            -1.0833638e0,
            -8.977354e-1,
            -3.7342377e-1,
            -8.6632643e-2,
            -1.0450598e-2,
            -5.1920577e-4,
        )
    elif mv < 20.644:
        # Range: 0 mV to 20.644 mV
        return (
            0.0e0,
            2.508355e1,
            7.860106e-2,
            -2.503131e-1,
            8.31527e-2,
            -1.228034e-2,
            9.804036e-4,
            -4.41303e-5,
            1.057734e-6,
            -1.052755e-8,
        )
    else:
        # Range: 20.644 mV to 54.886 mV
        return (
            -1.318058e2,
            4.830222e1,
            -1.646031e0,
            5.464731e-2,
            -9.650715e-4,
            8.802193e-6,
            -3.11081e-8,
        )

def evaluate_poly(coeffs: list[float] | tuple[float], x: float) -> float:
    """ "
    Evaluate a polynomial at x given the list of coefficients.

    The polynomial is:
        P(x) = a0 + a1*x + a2*x^2 + ... + an*x^n
    where coeffs = [a0, a1, ..., an]

    args:
        coeffs:Polynomial coefficients ordered by ascending power.
        x: The value at which to evaluate the polynomial.

    returns;
        float: The evaluated polynomial result.
    """
    return sum(a * x**i for i, a in enumerate(coeffs))

def mv_to_temp_c(mv):
    """
    Convert Type K thermocouple voltage (mV) to temperature (°C) using
    NIST ITS-90 polynomial approximations.

    args:
        mv: Thermocouple voltage in millivolts.

    returns:
        float: Temperature in degrees Celsius.
    """
    coeffs = volts_to_temp_constants(mv)
    return evaluate_poly(coeffs, mv)

def voltage_to_temp_typeK(voltage_mV):
    return np.array([mv_to_temp_c(mv) for mv in voltage_mV])