1. Install [arduino-cli](https://github.com/arduino/arduino-cli/).

2. Install arduino core for the board:
```sh
arduino-cli core install arduino:avr
```

3. Build avrdude from sources with the support of libgpiod, install avrdude.

```sh
sudo apt-get install build-essential git cmake \
     flex bison pkg-config \
     libelf-dev libusb-dev libhidapi-dev libftdi1-dev libreadline-dev libserialport-dev libgpiod-dev

git clone https://github.com/avrdudes/avrdude.git
cd avrdude
./build.sh

sudo cmake --build build_linux --target install
```

4. Create symbolic links to `/usr/local/bin/avrdude` and `/usr/local/etc/avrdude.conf` in the following folder: `~/.arduino15/packages/arduino/tools/avrdude/6.3.0-arduino17/`.

5. Modify `/usr/local/etc/avrdude.conf`:

```conf
programmer
     id                   = "linuxgpio";
     desc                 = "Linux sysfs/libgpiod to bitbang GPIO lines";
     type                 = "linuxgpio";
     prog_modes           = PM_ISP;
     connection_type      = linuxgpio;
     reset                = 8;
     sck                  = 11;
     sdo                  = 10;
     sdi                  = 9;
;
```

4. Add new AVR programmer in `~/.arduino15/packages/arduino/hardware/avr/1.8.6/programmers.txt`:

```conf
gpio.name=Linux GPIO
gpio.protocol=linuxgpio
gpio.program.tool=avrdude
gpio.program.extra_params=
```

5. Add new RasPiO Duino board in `~/.arduino15/packages/arduino/hardware/avr/1.8.6/boards.txt`:

```conf
##############################################################

gert328.name=RasPiO Duino with ATmega328 (GPIO)

gert328.program.tool=avrdude
gert328.program.tool.default=avrdude

gert328.upload.tool=avrdude
gert328.upload.tool.default=avrdude
gert328.upload.using=gpio
gert328.upload.protocol=gpio
gert328.upload.maximum_size=32768
gert328.upload.speed=57600
gert328.upload.disable_flushing=true

gert328.bootloader.tool=avrdude
gert328.bootloader.tool.default=avrdude
gert328.bootloader.low_fuses=0xE7
gert328.bootloader.high_fuses=0xDA
gert328.bootloader.extended_fuses=0xFF
gert328.bootloader.file=atmega/ATmegaBOOT_168_gert328.hex
gert328.bootloader.unlock_bits=0x3F
gert328.bootloader.lock_bits=0x0F

gert328.build.mcu=atmega328p
gert328.build.f_cpu=12000000L
gert328.build.core=arduino
gert328.build.variant=standard
```

6. Add new build target in `~/.arduino15/packages/arduino/hardware/avr/1.8.6/bootloaders/atmega/Makefile`:

```make
gert328: TARGET = atmega328
gert328: MCU_TARGET = atmega328p
gert328: CFLAGS += '-DMAX_TIME_COUNT=F_CPU>>4' '-DNUM_LED_FLASHES=1' -DBAUD_RATE=57600
gert328: AVR_FREQ = 12000000L
gert328: LDSECTION  = --section-start=.text=0x7800
gert328: $(PROGRAM)_gert328.hex
```

7. Build bootloader:

```sh
export PATH="$HOME/.arduino15/packages/arduino/tools/avr-gcc/7.3.0-atmel3.6.1-arduino7/bin:$PATH"
make gert328
```

8. Burn bootloader:

```sh
arduino-cli burn-bootloader -P gpio -b arduino:avr:gert328 -v
```
