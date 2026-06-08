# Look-Up-Table basierend auf den neuen Daten
# Format: (Ausgangsleistung in Watt : DAC Registerwert hex/int)
LUT_POWER_TO_DAC = [
    (0, 0x00),
    (5, 0x31),
    (10, 0x63),
    (20, 0x95),
    (30, 0xC7),
    (60, 0xF9),
    (130, 0x0130),
    (220, 0x015D),
    (410, 0x018F),
    (690, 0x01C2),
    (1110, 0x01F6),
    (1670, 0x0228),
    (2450, 0x025B),
    (3420, 0x028D),
    (4540, 0x02C0),
    (5650, 0x02F2),
    (6780, 0x0325),
    (7750, 0x0357),
    (8320, 0x038A),
    (8590, 0x03BC),
    (8630, 0x0400)
]

def get_dac_value(p_target):
    """
    Interpoliert den DAC-Registerwert basierend auf der gewünschten Leistung in Watt.
    """
    # Untergrenze abfangen
    if p_target <= LUT_POWER_TO_DAC[0][0]:
        return LUT_POWER_TO_DAC[0][1]

    # Obergrenze abfangen
    if p_target >= LUT_POWER_TO_DAC[-1][0]:
        return LUT_POWER_TO_DAC[-1][1]

    # Suche das passende Segment in der LUT zur Linearinterpolation
    for i in range(len(LUT_POWER_TO_DAC) - 1):
        p_low, r_low = LUT_POWER_TO_DAC[i]
        p_high, r_high = LUT_POWER_TO_DAC[i+1]

        if p_low <= p_target <= p_high:
            # Berechnung des Zwischenwerts (Linearinterpolation)
            # Formel: Register = R_unten + (P_ziel - P_unten) * (R_oben - R_unten) / (P_oben - P_unten)
            fraction = (p_target - p_low) / (p_high - p_low)
            r_target = r_low + (fraction * (r_high - r_low))
            return int(round(r_target))

    return 0

# --- Beispielhafte Abfrage ---
if __name__ == "__main__":
    try:
        eingabe = input("Gewünschte Leistung in Watt eingeben: ").replace(',', '.')
        p_watt = float(eingabe)

        reg_val = get_dac_value(p_watt)

        print(f"Eingestellte Leistung: {str(p_watt).replace('.', ',')} W")
        print(f"DAC Registerwert (Hex): {hex(reg_val)}")

    except ValueError:
        print("Bitte eine gültige Zahl für die Leistung eingeben.")
