# atomic units
def eV2au(energy): #eV -> j.a
    """
    Convert energy from electron volts (eV) to atomic units (a.u.).
    
    This function converts energy measurements from electron volts to atomic units,
    where 1 eV = 0.03674932587122423 a.u.
    
    Args:
        energy (float): Energy value in electron volts (eV).
    
    Returns:
        float: Energy value converted to atomic units (a.u.).
    
    Example:
        >>> eV2au(1.0)
        0.03674932587122423
    """
    return energy*0.03674932587122423
def nm2au(length): #nm -> j.a
    """
    Convert length from nanometers to atomic units.

    Args:
        length: Length value in nanometers (nm).

    Returns:
        float: Length value converted to atomic units (a.u.).
        
    Notes:
        1 nm = 18.89726133921252 a.u.
        This conversion factor is commonly used in quantum chemistry
        and atomic physics calculations.
    """
    return length*18.89726133921252
def T2au(length):  #Tesla -> j.a
    """
    Convert magnetic field strength from Tesla to atomic units.
    
    Parameters
    ----------
    length : float
        Magnetic field strength in Tesla (T).
    
    Returns
    -------
    float
        Magnetic field strength in atomic units (a.u.).
    
    Notes
    -----
    The conversion factor is approximately 4.254382E-6.
    1 Tesla = 4.254382E-6 atomic units of magnetic field.
    """
    return length*4.254382E-6