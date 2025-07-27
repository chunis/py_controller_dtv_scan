# About

This demo shows how to do spectrual scan, and switches frequency bands accordingly.
It bases on Chirpstack NS v3, sx1302_hal v2.1.0 and Python3.


## Info for Gateway

First, needs to apply the patches under folder "sx1302_hal_patches/".

Then, the gateway config needs to add or modify below lines:

- in section "gateway_conf":
        "ext_server_address": "192.168.1.202",
        "ext_serv_port_up": 1612,
        "ext_serv_port_down": 1612,

- in section "SX130x_conf/sx1261_conf":
	"enable": true,
	"freq_start": 867100000,
	"nb_chan": 16,
	"nb_scan": 2000,
	"pace_s": 2


## Info for Chirpstack NS/AS

This demo uses the Chirpstack OS v3.6 full version based on Raspberry Pi 3B, downloaded from:
	https://artifacts.chirpstack.io/downloads/chirpstack-gateway-os/raspberrypi/raspberrypi3/3.6.0/
It only supports EU868 and US915.


## Info for the demo python script

To run it, follow these steps:

```
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
./pyserver.py
```

