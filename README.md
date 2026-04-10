# PH-Überschuss-Heizer
Ein SBC steuert einen 9 kW Heizstab im Brauchwasserspeicher eines 
Mehrfamilienhauses an, um ausschlieszlich den Energieüberschuss einer
installierten PH-Anlage auf dem Haus umzuwandeln. Die Steuerung sorgt
somit für eine Reduzierung des Energieüberschusses der PV-Anlage, welche
nicht als Eigenverbrauch vor Ort genutzt wird.

# Warmwasserspeicher
Verbaut wurde aus platzgründen ein 300 Liter Warmwasserspeicher der Marke ThermoFlux vom Typ
THBWS-R 300 horizontal mit einem Wärmespeicher.

# Temperaturmessung:
Warmwasserspeicher verfügt über drei Ebenen von DS1820 Temperatursensoren,
welche in einer Tauchhülse über die Bauhöhe des Speichers verteilt sind.
Jede Ebene ist mit zwei nebeneinander sitzenden Temperatursensoren
ausgestattet zur Redundanz und Sicherheit. Es sind somit sechs Temperatur-
sensoren für drei Temperaturmessungen verbaut. Die drei Temperaturmessebenen
teilen einen liegenden 300 Liter Brauchwasserspeicher wie folgt auf:

Oberste Ebene: 19,55%
 28-0b239a7284c8
 28-0b239a272455

Mittlere Ebene: 60,9%
 28-0b239a196fe6
 28-00000bfe2de4

Unterste Ebene: 19,55%
 28-0b239a3a204e
 28-0b239a7d455a

Weiterhin listet die Übersicht die 1-wire IDs der beiden
Temperatursensoren jeder Ebene.

Die Speicherladung berechnet sich durch folgende Formel:

L[%]=(19,55 * T1​ + 60,9 * T2​ + 19,55 * T3​​) / Tmax​ | T in m°C

# DAC
Zur Ansteuerung des verwendeten Leistungstellers wurde die Spannungssteuerungs-
option 0-10 Volt gewählt und mittels eines I2C Analog Output Moduls mit 4 Kanal
á 10 Bit umgesetzt.

# Leistungssteller
Ohne ein passendes Angebot für einen Leistungssteller mit Schwingungspaketsteuerung wurde
zeitweise auf ein günstiges Modell mit Phasenanschnittssteuerung vom Typ TSR-120WA-H
zurückgegriffen. Zwecks der Netzrückwirkungen dieser Leistungssteuerungsvariante wird
jedoch empfohlen auf eine netzverträglichere Ansteuerung umzusteigen.


# Sourcen:

## Warmwasserspeicher
https://www.klimaworld.com/products/horizontaler-brauchwasserspeicher-300-liter-thermoflux

## Temperatursensoren
https://cbrell.de/blog/raspilab-wetterstation-dritte-mission-temperatur-messen-mit-dem-bs18b20/

## DAC
https://www.horter-shop.de/de/home/93-343-bausatz-i2c-analog-output-modul-4-kanal-10-bit-4260404260752.html

## Leistungssteller
https://www.ebay.de/itm/146901272886
