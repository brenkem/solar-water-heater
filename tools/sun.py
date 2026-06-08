from datetime import datetime, timedelta
from astral import LocationInfo
from astral.sun import sun
import pytz
import time

def get_sun_data(lat, lon):
    """Berechnet die Sonnenereignisse für den aktuellen Tag."""
    city = LocationInfo("ANEWAND", "Germany", "UTC", lat, lon)
    now = datetime.now(pytz.utc)
    return sun(city.observer, date=now, tzinfo=pytz.utc)

def main():
    # Koordinaten (50°54'36.0"N 13°23'24.0"E)
    LAT, LON = 50.91, 13.39

    print("Initialisiere System...")
    current_sun = get_sun_data(LAT, LON)
    last_update_day = datetime.now(pytz.utc).date()

    now = datetime.now(pytz.utc)

    # 1. Tägliches Update der Sonnen-Daten (um Mitternacht)
    if now.date() > last_update_day:
        print("Neuer Tag erkannt. Aktualisiere Sonnenstandsdaten...")
        current_sun = get_sun_data(LAT, LON)
        last_update_day = now.date()

    # 2. Prüfen, ob Tag oder Nacht ist
    is_daylight = current_sun["sunrise"] < now < current_sun["sunset"]

    if is_daylight:
        # --- AKTIVER MODUS (Tag) ---
        print(f"[{now.strftime('%H:%M:%S')}] TAG-MODUS: Verarbeite Aufgaben bis {current_sun["sunset"].strftime('%H:%M:%S')}")

        # Hier kommt dein eigentlicher Programmcode hin
        # execute_main_logic()
    else:
        # --- STANDBY MODUS (Nacht) ---
        print(f"[{now.strftime('%H:%M:%S')}] NACHT-MODUS: Warte auf Sonnenaufgang bis {current_sun["sunrise"].strftime('%H:%M:%S')}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgramm beendet.")
