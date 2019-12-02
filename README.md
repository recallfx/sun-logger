# Sun logger

Raspberry Pi Logger for SUN2000 Huawei string PV inverter

## Setup

1. Install [Raspbian Buster Lite](https://www.raspberrypi.org/downloads/raspbian/) into [SD card](https://www.raspberrypi.org/documentation/installation/installing-images/README.md).
2. Enable SSH by placing a file named `ssh` onto the boot partition of the SD card.
3. Setup WiFi by creating a file on SD card - `wpa_supplicant.conf` with contents:

```
country=US # Your 2-digit country code
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
network={
    ssid="YOUR_NETWORK_NAME"
    psk="YOUR_PASSWORD"
    key_mgmt=WPA-PSK
}
```

[More info](https://howchoo.com/g/ndy1zte2yjn/how-to-set-up-wifi-on-your-raspberry-pi-without-ethernet)

4. Start Raspberry Pi and ssh into it;
5. Disable bluetooth by adding a line in file `boot/config.txt`: `dtoverlay=pi3-disable-bt`;
6. Ensure line `enable_uart=1` (and `core_freq=250`?) is in file `boot/config.txt`;
7. Ensure `console=serial0,115200` is not present in file `/boot/cmdline.txt`;
8. Release GPIOs 14 and 15 by running `sudo systemctl disable hciuart`;
9. Install python dependencies: `sudo apt-get install python-pip python3-numpy`
10. Restart: `sudo reboot`;

[More info on UART](https://www.raspberrypi.org/documentation/configuration/uart.md)

This list is not final as I have not tested on fresh install.

# References

1. [Modbus interface defintions V3.0](https://support.huawei.com/enterprise/en/doc/EDOC1100113918?section=k002)
2. [Signal cable pinout](https://support.huawei.com/enterprise/en/doc/EDOC1100059932/c06b3480/optional-installing-the-signal-cable)