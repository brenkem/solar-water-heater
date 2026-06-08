import smbus2

# power delta ~ 150 Watt

# Parameter Definition
bus_number = 1
device_address = 0x58
register_address = 0x03
data = [0xEF, 0x03] # 8630 W  |  10 V
data = [0xBC, 0x03] # 8590 W  |  9,5 V
data = [0x8A, 0x03] # 8320 W  |  9 V
data = [0x57, 0x03] # 7750 W  |  8,5 V
data = [0x25, 0x03] # 6780 W  |  8 V
data = [0xF2, 0x02] # 5650 W  |  7,5 V
data = [0xC0, 0x02] # 4540 W  |  7 V
data = [0x8D, 0x02] # 3420 W  |  6,5 V
data = [0x5B, 0x02] # 2450 W  |  6 V
data = [0x28, 0x02] # 1670 W  |  5,5 V
data = [0xF6, 0x01] # 1110 W  |  5 V
data = [0xC2, 0x01] #  690 W  |  4,5 V
data = [0x8F, 0x01] #  410 W  |  4 V
data = [0x5D, 0x01] #  220 W  |  3,5 V
data = [0x30, 0x01] #  130 W  |  3 V
data = [0xF9, 0x00] #   60 W  |  2,5 V
data = [0xC7, 0x00] #   30 W  |  2 V
data = [0x95, 0x00] #   20 W  |  1,5 V
data = [0x63, 0x00] #   10 W  |  1 V
data = [0x31, 0x00] #    5 W  |  0,5 V
data = [0x00, 0x00] #    0 W  |  0 V

# Ausführung
with smbus2.SMBus(bus_number) as bus:
    # 'i' im Bash-Kommando steht für I2C Block Data
    bus.write_i2c_block_data(device_address, register_address, data)
