# PH-Überschuss-Heizer
Ein SBC steuert einen 9 kW Heizstab im Brauchwasserspeicher eines 
Mehrfamilienhauses an, um ausschlieszlich den Energieüberschuss einer
installierten PH-Anlage auf dem Haus umzuwandeln. Die Steuerung sorgt
somit für eine Reduzierung des Energieüberschusses der PV-Anlage welche
nicht als Eigenverbrauch vor Ort genutzt wird.


# Temperaturmessung:
Warmwasserspeicher verfügt über drei Ebenen von DS1820 Temperatursensoren.
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

L[%]=(19,55*T1​+60,9*T2​+19,55*T3​​)/Tmax​ | T in m°C
