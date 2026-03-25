import os

# Konfiguration in m°C (Standardeinheit im Script)
T_MAX = 80000  # 80 °C als Maximaltemperatur

# Sensor-Pfade (Oben, Mitte, Unten)
SENSORS = {
    "t1": "/sys/bus/w1/devices/28-0b239a7284c8/temperature",
    "t2": "/sys/bus/w1/devices/28-0b239a196fe6/temperature",
    "t3": "/sys/bus/w1/devices/28-0b239a3a204e/temperature"
}

# Gewichtungsfaktoren (Summe = 10000)
# Entspricht 19.55%, 60.90%, 19.55%
W1 = 1955
W2 = 6090
W3 = 1955

def read_raw(path):
    """Liest den m°C Wert direkt aus dem Devicefile."""
    try:
        with open(path, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return None

def get_charge():
    # Rohwerte in m°C einlesen
    t1 = read_raw(SENSORS["t1"])
    t2 = read_raw(SENSORS["t2"])
    t3 = read_raw(SENSORS["t3"])

    if None in (t1, t2, t3):
        print("Fehler: Mindestens ein Sensor konnte nicht gelesen werden.")
        return None

    # Gewichtete Durchschnittstemperatur in m°C
    t_avg = (t1 * W1 + t2 * W2 + t3 * W3)

    # Berechnung der Ladung relativ zu T_MAX (Vernachlässigung von T_MIN)
    # Formel: (t_avg / T_MAX) * 100
    # Multiplikation mit 10000 vor Division für 2 Nachkommastellen Präzision
    #charge = (t_avg // T_MAX)
    charge = (t_avg / (T_MAX * 100))
    #charge_pct = charge_scaled / 100.0

    # Begrenzung auf 100% (falls T_MAX überschritten wird)
    #charge_pct = min(100.0, max(0.0, charge_pct))

    return charge, t1, t2, t3

if __name__ == "__main__":
    result = get_charge()

    if result:
        percent, t1, t2, t3 = result
        print(f"Sensordaten (m°C): T1={t1}, T2={t2}, T3={t3}")
        print(f"Berechnete Speicherladung: {percent:.2f} %")
