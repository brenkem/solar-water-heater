import time
import os

# Pfad zur Leistungsdatei
POWER_FILE = "/mnt/s0hm/power"

def monitor_power():
    """
    Liest jede Sekunde den Wert aus POWER_FILE und gibt ihn aus,
    sofern er negativ ist.
    """
    print(f"Starte Überwachung von {POWER_FILE}...")

    while True:
        try:
            if os.path.exists(POWER_FILE):
                with open(POWER_FILE, "r") as f:
                    content = f.read().strip()

                    if content:
                        # Umwandlung in Integer
                        power_val = int(content)

                        # Logik: Nur negative Werte ausgeben
                        if power_val < 0:
                            print(power_val)
                        else:
                            print(f"no excess power {power_val}")
            else:
                print(f"Datei {POWER_FILE} nicht gefunden.")

        except ValueError:
            print("Fehler: Dateiinhalt ist kein gültiger Integer.")
        except Exception as e:
            print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")

        # Wartezeit von einer Sekunde
        time.sleep(1)

if __name__ == "__main__":
    try:
        monitor_power()
    except KeyboardInterrupt:
        print("\nÜberwachung durch Benutzer beendet.")
