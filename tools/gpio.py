import lgpio
import time

h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(h, 18)
lgpio.gpio_write(h, 18, 1)
time.sleep(3)
lgpio.gpio_write(h, 18, 0)
time.sleep(3)
