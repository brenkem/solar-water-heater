import os
import time
import lgpio
import smbus2

################################## defines ####################################
# Pfad zur Leistungsdatei
POWER_FILE = "/mnt/s0hm/power"
LOAD_FILE = "/run/shm/ww_load"

############ TODO 70 °C to debug ########################
T_MAX = 70000  # 80 °C, Maximaltemperatur
T_DIFF = 2000  # 2 °C, Toleranzschwelle zwischen Temperatursensoren der selben Ebene

L_TRH = 150    # 150 Watt, Leistungsschwelle zum Heizen
# Gewichtungsfaktoren nach Wassermenge (Summe = 10000)
# 19,55% für oberen und unteren Warmwasserspeicherabschnitt; 60,9 % für Mittelteil
W = [
    1955,
    6090,
    1955
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
OFF = 0x0000

# GPIO
GPIO_CHIP = None
REL_PIN = 18

def read_file(file):
    """
    Liest eine Datei aus und gibt den enthaltenen Integer-Wert zurück.
    """
    try:
        with open(file, 'r', encoding='utf-8') as datei:
            # Inhalt lesen und Leerzeichen/Zeilenumbrüche entfernen
            inhalt = datei.read().strip()

            datei.close()
            # Umwandlung in Integer
            return int(inhalt)

    except FileNotFoundError:
        print(f"Fehler: Die Datei unter '{file}' wurde nicht gefunden.")
    except ValueError:
        print(f"Fehler: Der Inhalt der Datei ist keine gültige Ganzzahl.")
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
        return val

    diff = abs(T0 - T1)
    if diff > T_DIFF:
        print(f"WARNUNG: Differenz Ebene {level} zu hoch ({diff} m°C)!")

    # Rückgabe des höheren Wertes
    return max(T0, T1)


def calc_load():
    """
    Berechnet Speicherladung und schreibt diese in den RAM.
    """
    # Gewichtete Durchschnittstemperatur in m°C
    T_avg = (TEMP[0] * W[0] + TEMP[1] * W[1] + TEMP[2] * W[2])

    # Berechnung der Ladung relativ zu T_MAX
    # Formel: (T_avg / T_MAX) * 100
    load = (T_avg / (T_MAX * 100))

    # Schreibe Speicherladung nach RAM
    try:
        # Datei im Schreibmodus öffnen ('w')
        with open(LOAD_FILE, "w") as file:
            file.write(f"{load:.1f}")

    except PermissionError:
        print("Fehler: Fehlende Berechtigungen zum Schreiben in diese Datei.")
    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")

    return load


def check_max_t():
    """
    Kontrolliert ob in einer Temperaturebene die Maximaltemperatur überschritten wurde.
    """
    for i in [0, 1, 2]:
        if TEMP[i] > T_MAX:
            return TEMP[i]
    return 0


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


def write_dac_reg(i2c_bus, register_value):
    # DAC Parameter
    device_address = 0x58
    register_address = 0x03

    # Schreibe Highbyte in [1] und Lowbyte in [0]
    data = [(register_value & 0xFF), ((register_value >> 8) & 0xFF)]

    i2c_bus.write_i2c_block_data(device_address, register_address, data)
    #print(f"--- DEBUG: data [0]={hex(data[0])} [1]={hex(data[1])}!")
    #try:
        #i2c_bus.write_i2c_block_data(device_address, register_address, data)
    #print(f"--- DEBUG: data [0]={hex(data[0])} [1]={hex(data[1])}!")
    #except Exception as e:
        #print(f"Ein unerwarteter Fehler beim Schreiben des I2C Busses ist aufgetreten: {e}")
    #except:
        #print("Failed to write I2C bus.")


def solar_heater():
    """
    Liest jede zyklisch den Energiebezug …
    """
    print(f"Starte Solarheater...")

    global BUS
    global GPIO_CHIP
    current_heater_power = 0

    # Initialiesiere System

    ## Initialisiere GPIO Pin
    GPIO_CHIP = lgpio.gpiochip_open(0)
    lgpio.gpio_claim_output(GPIO_CHIP, REL_PIN)
    lgpio.gpio_write(GPIO_CHIP, REL_PIN, 1)

    ## Initialisiere I2C Bus
    BUS = smbus2.SMBus(I2C_BUS_NUMBER)
    try:
        BUS.timeout = 0.5 # Set a 500ms timeout
        write_dac_reg(BUS, OFF)
    except:
        BUS.close() # Always close manually if not using 'with'

    ## Starte mit Ebene 0 ^= "oben"
    ebene = 0

    ## Initialisiere Temperaturfeld
    for i in [0, 1, 2]:
        print(f"INIT: Initiere Temperaturebene {i}.")
        TEMP[i] = check_level_temp(i)

    ## Test auf Temperaturüberschreitung
    while (T_exc := check_max_t()):
        print(f"NOTE: Temperaturüberschreitung detektiert: {T_exc}!")
        time.sleep(10)
        for i in [0, 1, 2]:
            TEMP[i] = check_level_temp(i)
        continue


    # Logikschleife
    while True:
        # Lese Energiebezug
        try:
            power = read_file(POWER_FILE) # Energiefluss auslesen
            power = (-power) # Vorzeichen drehen:: positiv: Netzeinspeisung
        except:
            print("ERROR: Energiebezug ist ungültig.")
            # Heizung abschalten und kurz warten
            current_heater_power = 0
            write_dac_reg(BUS, OFF)
            time.sleep(1)
            continue

        # Berechne Speicherladung und schreibe Speicherladung diese in den RAM
        calc_load()


        # Wahren PV-Überschuss berechnen
        # (Was wir ins Netz speisen + was wir gerade schon verheizen)
        absolute_excess = power + current_heater_power


        # 2. Sicherheitscheck VOR der Leistungsanforderung
        if (T_exc := check_max_t()):
            print(f"### TEMP to high: T_exc: {T_exc} m°C")
            # Heizung bei T_MAX abschalten!
            write_dac_reg(BUS, OFF)
            current_heater_power = 0
            time.sleep(10)
            # Neue Temperaturen einlesen bevor es im Loop weitergeht
            for i in [0, 1, 2]:
                TEMP[i] = check_level_temp(i)
            continue




        # Leistungsregelung für Heizpatrone basierend auf absolutem Überschuss
        if absolute_excess > L_TRH:
            print(power) #### TODO DEBUG
            print(absolute_excess) #### TODO DEBUG

            # Ziehe Puffer ab, um Netzbezug zu vermeiden
            target_power = absolute_excess - L_TRH

            # Berechne DAC Registerwert
            reg_val = get_dac_value(target_power)
            write_dac_reg(BUS, reg_val)

            # Merke neu eingestellte Leistung für den nächsten Loop!
            # TODO: Ideal wäre es, hier den realen Leistungswert aus der LUT
            # zurückzulesen, aber target_power reicht als gute Näherung.
            current_heater_power = target_power

            print(f"DAC({target_power} W) = 0x{hex(reg_val)}; To: {TEMP[0]} m°C, Tm: {TEMP[1]} m°C,Tu: {TEMP[2]} m°C")
        else:
            write_dac_reg(BUS, OFF)
            current_heater_power = 0
            print(f"### No POWER: excess={absolute_excess} W; To: {TEMP[0]} m°C, Tm: {TEMP[1]} m°C,Tu: {TEMP[2]} m°C")

        ####################### END WHILE ########################################
        # Wartezeit von etwa 1,6 Sekunden durch Auslesen einer Temperaturebene
        TEMP[ebene] = check_level_temp(ebene)
        ebene += 1
        if ebene >= 3:
            ebene = 0 # setze Ebene zurück auf oben



if __name__ == "__main__":
    try:
        solar_heater()
    except KeyboardInterrupt:
        print("\n... Solarheater beendet.")
        write_dac_reg(BUS, OFF)
        BUS.close() # Always close manually if not using 'with'
        lgpio.gpio_write(GPIO_CHIP, REL_PIN, 0)
