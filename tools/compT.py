import os

# Konfiguration
T_MAX = 80000  # 80 °C
# Gewichtungsfaktoren (Summe = 10000)
W = [1955, 6090, 1955] # 19,55% für oberen und unteren Warmwasserspeicherabschnitt; 60,9 % für Mittelteil
MAX_DIFF = 2000  # 2 °C Toleranzschwelle

# Definition der Sensorpaare (m°C)
# Paar 1: Oben, Paar 2: Mitte, Paar 3: Unten
SENS_PAIRS = [
    ("/sys/bus/w1/devices/28-0b239a7284c8/temperature", "/sys/bus/w1/devices/28-0b239a272455/temperature"),
    ("/sys/bus/w1/devices/28-0b239a196fe6/temperature", "/sys/bus/w1/devices/28-00000bfe2de4/temperature"),
    ("/sys/bus/w1/devices/28-0b239a3a204e/temperature", "/sys/bus/w1/devices/28-0b239a7d455a/temperature")
]

def read_raw(path):
    try:
        with open(path, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return None

def get_best_value(p1, p2, ebene_name):
    v1 = read_raw(p1)
    v2 = read_raw(p2)

    if v1 is None or v2 is None:
        # Falls einer ausfällt, nimm den verbleibenden
        val = v1 if v1 is not None else v2
        if val is None:
            print(f"KRITISCH: Ebene {ebene_name} komplett ausgefallen!")
        return val

    diff = abs(v1 - v2)
    if diff > MAX_DIFF:
        print(f"WARNUNG: Differenz Ebene {ebene_name} zu hoch ({diff} m°C)!")

    # Rückgabe des höheren Wertes
    return max(v1, v2)

def calculate_redundant_charge():
    ebenen_namen = ["Oben", "Mitte", "Unten"]
    valid_temps = []

    for i, paar in enumerate(SENS_PAIRS):
        val = get_best_value(paar[0], paar[1], ebenen_namen[i])
        if val is None:
            return None
        valid_temps.append(val)

    # Gewichtete Durchschnittstemperatur
    t_avg = (valid_temps[0] * W[0] + valid_temps[1] * W[1] + valid_temps[2] * W[2])

    # Ladung relativ zu T_MAX (auf 2 Nachkommastellen genau)
    charge = (t_avg / (T_MAX * 100))

    return charge, valid_temps

if __name__ == "__main__":
    result = calculate_redundant_charge()

    if result:
        percent, temps = result
        print(f"--- Redundante Auswertung ---")
        print(f"Effektive Werte: Oben={temps[0]}, Mitte={temps[1]}, Unten={temps[2]}")
        print(f"Speicherladung: {percent:.2f} %")
