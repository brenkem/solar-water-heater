import os
import time
import lgpio
import smbus2

################################## Definitionen ####################################
# Pfad zur Leistungsdatei
POWER_FILE = "/mnt/s0hm/power"
LOAD_FILE  = "/run/shm/ww_load"
TEMP_FILES = [
    "/run/shm/ww_temp_oben",
    "/run/shm/ww_temp_mitte",
    "/run/shm/ww_temp_unten"
]

## Temperatur
T_MAX = 80000  # 80 °C, Maximaltemperatur
T_DIFF = 2000  # 2 °C, Toleranzschwelle zwischen Temperatursensoren der selben Ebene

# Leistung
L_TRH = 200    # 300 Watt, Leistungsschwelle zum Heizen
L_STEP = 400   # 400 Watt Rampenschritte

# Gewichtungsfaktoren nach Wassermenge (Summe = 10000)
# 19,55% für oberen und unteren Warmwasserspeicherabschnitt; 60,9 % für Mittelteil
W = [
    19.55,
    60.90,
    19.55
]

# Paar 1: Oben [0], Paar 2: Mitte, Paar 3: Unten
SENS_PAIRS = [
    ("/sys/bus/w1/devices/28-0b239a7284c8/temperature", "/sys/bus/w1/devices/28-0b239a272455/temperature"),
    ("/sys/bus/w1/devices/28-0b239a196fe6/temperature", "/sys/bus/w1/devices/28-00000bfe2de4/temperature"),
    ("/sys/bus/w1/devices/28-0b239a3a204e/temperature", "/sys/bus/w1/devices/28-0b239a7d455a/temperature")
]

# Speichertemperatur oben, mitte und unten
TEMP = [
    0,
    0,
    0
]

# Look-Up-Table basierend auf den Leistungstellerdaten
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

# I2C Bus
I2C_BUS_NUMBER = 1
BUS = None
OFF_VAL = 0x0000

# GPIO
GPIO_CHIP = None
REL_PIN = 18

def read_file(file):
    """
    Liest eine Datei aus und gibt den enthaltenen Integer-Wert zurück.
    """
    try:
        with open(file, 'r') as datei:
            inhalt = datei.read().strip()
            return int(inhalt)

    except FileNotFoundError:
        print(f"Fehler: Die Datei unter '{file}' wurde nicht gefunden.")
    except ValueError:
        print(f"Fehler: Der Inhalt der Datei ist keine gültige Ganzzahl: {inhalt}")
    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")

    return None


def check_level_temp(level):
    """
    Liest beide Temperatursensoren einer Ebene aus und liefert den höheren Wert zurück.
    """
    # Ebene auslesen
    T0 = read_file(SENS_PAIRS[level][0])
    T1 = read_file(SENS_PAIRS[level][1])

    # Kontrolliere Sensorausfall
    if T0 is None or T1 is None:
        # Falls ein Temperatursensor ausfällt, nimm den verbleibenden
        val = T0 if T0 is not None else T1
        if val is None:
            print(f"KRITISCH: Ebene {level} komplett ausgefallen!")
        print(f"WARNUNG: Temperatursensor auf Ebene {level} ausgefallen!")
        return T_MAX

    # Bewerte Messergebnisse hinsichtlich erheblicher Temperaturdifferenz
    if abs(T0 - T1) > T_DIFF:
        print(f"INFO: Differenz Ebene {level} zu hoch ({diff} m°C).")

        # Ebene erneut auslesen
        T0 = read_file(SENS_PAIRS[level][0])
        T1 = read_file(SENS_PAIRS[level][1])

        # Kontrolliere Sensorausfall
        if T0 is None or T1 is None:
            # Falls ein Temperatursensor ausfällt, nimm den verbleibenden
            val = T0 if T0 is not None else T1
            if val is None:
                print(f"KRITISCH: Ebene {level} komplett ausgefallen!")
            print(f"WARNUNG: Temperatursensor auf Ebene {level} ausgefallen!")
            return T_MAX

        if abs(T0 - T1) > T_DIFF:
            print(f"WARNUNG: Temp.differenz immer noch zu hoch ({diff} m°C)!")

    # Rückgabe des höheren Wertes
    return max(T0, T1)


def calc_load():
    """
    Berechnet Speicherladung und schreibt diese in den RAM.
    """
    try:
        # Gewichtete Durchschnittstemperatur in m°C
        T_avg = (TEMP[0] * W[0] + TEMP[1] * W[1] + TEMP[2] * W[2])

        # Berechnung der Ladung relativ zu T_MAX
        load = (T_avg / T_MAX)

        # Schreiben der Speicherladung in RAM
        with open(LOAD_FILE, "w") as file:
            file.write(f"{load:.1f}")

        # Schreiben der Temperaturverteilung in Temperaturdateifeld
        for i in range(3):
            with open(TEMP_FILES[i], "w") as file:
                file.write(f"{TEMP[i]}")

        return load

    except PermissionError:
        print("Fehler: Fehlende Berechtigungen zum Schreiben in Datei.")
    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
    return None


def check_max_t():
    """
    Kontrolliert ob in einer Temperaturebene die Maximaltemperatur überschritten wurde.
    """
    for i in [0, 1, 2]:
        if TEMP[i] >= T_MAX:
            return TEMP[i]
    return 0


def get_dac_value(p_target):
    """
    Interpoliert den DAC-Registerwert basierend auf der gewünschten Leistung in Watt.
    """
    # Untergrenze abfangen
    try:
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
    except Exception as e:
        print(f"Fehler bei DAC Interpolation: {e}")

    return 0


def write_dac_reg(i2c_bus, register_value):
    """
    Schreibt den übergebenen Registerwert in den DAC des übergebenen I2B Busses.
    """
    if i2c_bus is None:
        return

    # DAC Parameter
    device_address = 0x58
    register_address = 0x03

    try:
        # Schreibe Highbyte in [1] und Lowbyte in [0]
        data = [(register_value & 0xFF), ((register_value >> 8) & 0xFF)]

        # Schreibe Datenfeld nach DAC
        i2c_bus.write_i2c_block_data(device_address, register_address, data)
    except Exception as e:
        print(f"I2C Schreibfehler: {e}")
        # Im Fehlerfall versuchen wir nicht weiter zu schreiben, um Bus-Hänger zu vermeiden

def cleanup_files():
    """
    Löscht die erstellten Dateien im Filesystem.
    """
    files_to_remove = [LOAD_FILE] + TEMP_FILES
    for f in files_to_remove:
        try:
            if os.path.exists(f):
                os.remove(f)
        except Exception as e:
            print(f"Fehler beim Löschen von {f}: {e}")


def solar_heater():
    """
    Liest jede zyklisch den Energiebezug …
    """
    print(f"Starte Solarheater...")

    global BUS
    global GPIO_CHIP
    current_heater_power = 0

    # Initialisiere System

    #### TODO: Initialisiere Tageszeit und Sonnenaufgang und Sonnenuntergang

    try:
        ## Initialisiere GPIO Pin
        GPIO_CHIP = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_output(GPIO_CHIP, REL_PIN)
        lgpio.gpio_write(GPIO_CHIP, REL_PIN, 1)

        ## Initialisiere I2C Bus
        BUS = smbus2.SMBus(I2C_BUS_NUMBER)
        BUS.timeout = 0.1 # Set a 100ms timeout
        write_dac_reg(BUS, OFF_VAL)
    except Exception as e:
        print(f"Initialisierungsfehler: {e}")
        if BUS:
            BUS.close()
        return

    ## Starte mit Ebene 0 ^= "oben"
    ebene = 0

    ## Initialisiere Temperaturfeld
    for i in [0, 1, 2]:
        print(f"INIT: Initiere Temperaturebene {i}.")
        TEMP[i] = check_level_temp(i)

    ## Test auf Temperaturüberschreitung
    while (T_exc := check_max_t()):
        print(f"NOTE: Temperaturüberschreitung detektiert: {T_exc}!")
        write_dac_reg(BUS, OFF_VAL)
        ww_load = calc_load()
        time.sleep(10)
        for i in [0, 1, 2]:
            TEMP[i] = check_level_temp(i)
        continue


    # Logikschleife
    while True:
        ## Lese Energiebezug
        try:
            power = read_file(POWER_FILE) # Energiefluss auslesen
            if power is None: # check data
                print("WARNING: Energiebezug gescheitert. RETRY!")
                power = read_file(POWER_FILE) # Zweitversuch
            power = (-power) # Vorzeichen drehen => positiv: Netzeinspeisung
        except Exception:
            print("ERROR: Energiebezug ist ungültig.")
            # Heizung abschalten und kurz warten
            write_dac_reg(BUS, OFF_VAL)
            current_heater_power = 0
            time.sleep(2)
            continue

        ## Berechne Speicherladung und im RAM ablegen
        ww_load = calc_load()

        ## Sicherheitscheck vor Leistungsanforderung
        if (T_exc := check_max_t()):
            print(f"### TEMP to high: T_exc: {T_exc} m°C")
            print(f"LOAD: {ww_load:.1f} %, To: {TEMP[0]} m°C, Tm: {TEMP[1]} m°C,Tu: {TEMP[2]} m°C")
            # Heizung bei T_MAX abschalten!
            write_dac_reg(BUS, OFF_VAL)
            current_heater_power = 0
            ww_load = calc_load()
            time.sleep(10)
            # vor nächster Schleife Temperaturen neu einlesen
            for i in [0, 1, 2]:
                TEMP[i] = check_level_temp(i)
            continue

        ## Asymmetrische Leistungsanpassung mittels "Rampe"
        if power > L_STEP:
            # Fall A: Sonne kommt raus -> Langsam hochregeln
            target_power = L_STEP + current_heater_power
        else:
            # Fall B: Wolken ziehen vor die Sonne oder Eigenverbrauch steigt
            target_power = power + current_heater_power - L_TRH
            #print(f"-> Leistungsregelung: um {power - L_TRH} W") ### DEBUG info

        ## Leistungsregelung für Heizpatrone basierend auf absolutem Überschuss
        if target_power >= L_TRH:
            #print(power) #### DEBUG Info

            # Berechne DAC Registerwert
            reg_val = get_dac_value(target_power)

            try:
                write_dac_reg(BUS, reg_val)

            # Merke neu eingestellte Leistung für den nächsten Loop!
                current_heater_power = target_power
                print(f"DAC({target_power:>4} W) = 0x{hex(reg_val)}; LOAD: {ww_load:.1f} %, To: {TEMP[0]} m°C, Tm: {TEMP[1]} m°C,Tu: {TEMP[2]} m°C")
            except Exception:
                print("Kritischer Fehler beim Setzen der Leistung.")
                current_heater_power = 0
        else:
            write_dac_reg(BUS, OFF_VAL)
            current_heater_power = 0
            print(f"### No POWER: excess={target_power:>5} W; To: {TEMP[0]} m°C, Tm: {TEMP[1]} m°C,Tu: {TEMP[2]} m°C")

        ####################### END WHILE ########################################
        # Wartezeit: etwa 3 Sekunden durch Auslesen von zwei Temperaturebenen zwecks Verzögerung Stromzähler
        try:
            for i in range(2):
                if ebene >= 2:
                    TEMP[ebene] = check_level_temp(ebene)
                    ebene = 0
                else:
                   TEMP[ebene] = check_level_temp(ebene)
                   ebene += 1
        except Exception:
            print(f"Fehler beim zyklischen Lesen der Ebene {ebene}")


if __name__ == "__main__":
    try:
        solar_heater()
    except KeyboardInterrupt:
        print("\n... Solarheater beendet.")
    except Exception as e:
        print(f"\n... Solarheater durch Fehler beendet: {e}")
    finally:
        if BUS:
            try:
                write_dac_reg(BUS, OFF_VAL) # setze Leistungsteller auf 0V
                BUS.close() # Schließe I2B Bus
            except Exception:
                pass
        if GPIO_CHIP:
            try:
                time.sleep(1)
                lgpio.gpio_write(GPIO_CHIP, REL_PIN, 0) # trenne Schütz
                lgpio.gpiochip_close(GPIO_CHIP)
            except Exception:
                pass
        cleanup_files()
