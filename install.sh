#!/usr/bin/env bash
# Sets up pi0xero on a Raspberry Pi. Run from the pi0xero folder:
#   ./install.sh            (refresh every 30 minutes)
#   INTERVAL=1h ./install.sh
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
INTERVAL="${INTERVAL:-30min}"
WAVESHARE="$HOME/e-Paper"

echo "== Packages"
sudo apt-get update
sudo apt-get install -y git python3-pil python3-requests python3-spidev python3-gpiozero \
    fonts-dejavu-core
# GPIO backend for gpiozero; already present on most images, so carry on if apt can't find it.
sudo apt-get install -y python3-lgpio || echo "(python3-lgpio not available, carrying on)"

echo "== SPI"
sudo raspi-config nonint do_spi 0
sudo usermod -aG spi,gpio "$USER"

echo "== Waveshare driver (python lib only)"
if [ ! -d "$WAVESHARE" ]; then
    git clone --depth 1 --filter=blob:none --sparse https://github.com/waveshare/e-Paper.git "$WAVESHARE"
    git -C "$WAVESHARE" sparse-checkout set RaspberryPi_JetsonNano/python/lib
else
    echo "$WAVESHARE already there, leaving it alone"
fi

echo "== Config"
if [ ! -f "$DIR/config.ini" ]; then
    cp "$DIR/config.example.ini" "$DIR/config.ini"
    echo "Created config.ini. Put your Xero client_id in it."
fi
mkdir -p "$DIR/data"

echo "== systemd timer (every $INTERVAL)"
sed -e "s|__USER__|$USER|" -e "s|__DIR__|$DIR|" "$DIR/systemd/pi0xero.service" \
    | sudo tee /etc/systemd/system/pi0xero.service >/dev/null
sed -e "s|__INTERVAL__|$INTERVAL|" "$DIR/systemd/pi0xero.timer" \
    | sudo tee /etc/systemd/system/pi0xero.timer >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable pi0xero.timer

echo
echo "Done. Next: edit config.ini, reboot once (for SPI), then run"
echo "  python3 -m pi0xero demo     to test the screen"
echo "  python3 -m pi0xero login    to connect Xero (see README)"
echo "  sudo systemctl start pi0xero.timer"
