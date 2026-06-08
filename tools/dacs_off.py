import smbus2

# power delta ~ 150 Watt

# Parameter Definition
bus_number = 1
device_address = 0x58
register_address = 0x00
data = [0x00, 0x00] #    0 W  |  0 V

# Ausführung
with smbus2.SMBus(bus_number) as bus:
    # 'i' im Bash-Kommando steht für I2C Block Data
    for register_address in [0, 1, 2, 3]:
        print(f"test: {register_address}")
        bus.write_i2c_block_data(device_address, register_address, data)

