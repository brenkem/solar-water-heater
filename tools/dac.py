import smbus2

# power delta ~ 150 Watt

# Parameter Definition
bus_number = 1
device_address = 0x58
register_address = 0x00
data = [0x00, 0x04] # 8630 W  |  10,13 V
#data = [0xF1, 0x03] # 8630 W  |  10 V
#data = [0xBF, 0x03] # 8590 W  |  9,5 V
#data = [0x8C, 0x03] # 8320 W  |  9 V
#data = [0x5A, 0x03] # 7750 W  |  8,5 V
#data = [0x27, 0x03] # 6780 W  |  8 V
#data = [0xF5, 0x02] # 5650 W  |  7,5 V
#data = [0xC3, 0x02] # 4540 W  |  7 V
#data = [0x8F, 0x02] # 3420 W  |  6,5 V
#data = [0x5E, 0x02] # 2450 W  |  6 V
#data = [0x2C, 0x02] # 1670 W  |  5,5 V
#data = [0xF9, 0x01] # 1110 W  |  5 V
#data = [0xC6, 0x01] #  690 W  |  4,5 V
#data = [0x93, 0x01] #  410 W  |  4 V
#data = [0x61, 0x01] #  220 W  |  3,5 V
#data = [0x2E, 0x01] #  130 W  |  3 V
#data = [0xFC, 0x00] #   60 W  |  2,5 V
#data = [0xCA, 0x00] #   30 W  |  2 V
#data = [0x97, 0x00] #   20 W  |  1,5 V
#data = [0x66, 0x00] #   10 W  |  1 V
#data = [0x34, 0x00] #    5 W  |  0,5 V
#data = [0x00, 0x00] #    0 W  |  0 V

# Ausführung
with smbus2.SMBus(bus_number) as bus:
    # 'i' im Bash-Kommando steht für I2C Block Data
    bus.write_i2c_block_data(device_address, register_address, data)
