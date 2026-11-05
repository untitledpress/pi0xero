# pi0xero

A Raspberry Pi Zero with a small Waveshare e-Paper screen on top that shows four numbers from Xero and updates them every 30 minutes:

```
+-----------------------------------------------+
| Demo Company (UK)              upd 5 Nov 10:07 |
+-----------------------+-----------------------+
| Revenue Oct           | Revenue TTM           |
| £48.2k                | £512k                 |
+-----------------------+-----------------------+
| Op profit Oct     21% | Op profit TTM     18% |
| £10.1k                | £92.4k                |
+-----------------------+-----------------------+
```

This guide assumes you've never set up a Raspberry Pi before. It goes from the parts on your desk to the screen updating by itself. Allow about an hour and a half, most of it waiting for things to download or install.

You'll be typing commands into two different computers: your Mac, and (over the network) the Pi. Every command block below says which one it's for. Copy commands exactly, one block at a time, and wait for each to finish before typing the next.

## Contents

1. [Check you have everything](#1-check-you-have-everything)
2. [Put the operating system on the memory card](#2-put-the-operating-system-on-the-memory-card)
3. [Fit the screen and start the Pi](#3-fit-the-screen-and-start-the-pi)
4. [Connect to the Pi from your Mac](#4-connect-to-the-pi-from-your-mac)
5. [Bring the Pi up to date](#5-bring-the-pi-up-to-date)
6. [Copy pi0xero onto the Pi](#6-copy-pi0xero-onto-the-pi)
7. [Run the installer](#7-run-the-installer)
8. [Test the screen](#8-test-the-screen)
9. [Create a Xero app](#9-create-a-xero-app)
10. [Log the Pi in to Xero](#10-log-the-pi-in-to-xero)
11. [First real update, then switch on the timer](#11-first-real-update-then-switch-on-the-timer)
12. [Living with it](#12-living-with-it)
13. [Troubleshooting](#13-troubleshooting)
14. [What the numbers mean](#14-what-the-numbers-mean)

---

## 1. Check you have everything

You need:

- A Raspberry Pi Zero W, Zero WH or Zero 2 W. The "W" matters because it means it has Wi-Fi. A plain Pi Zero without the W can't reach Xero.
- Header pins on the Pi: the two rows of 40 little metal pins along one edge. A "WH" has them already. If your board just has 40 empty holes, you'll need to solder on a 2×20 male header (or use a solder-free "hammer header" kit) before going any further.
- A Waveshare 2.13inch e-Paper HAT, the black and white one (250×122 pixels). Turn it over and find the version on the sticker or printed on the board: V2, V3 or V4. Write it down, you'll need it later.
- A microSD card, 8 GB or bigger.
- A way to plug the microSD card into your Mac: an SD adapter for the Mac's card slot, or a cheap USB card reader.
- A micro-USB power supply, 5 V and at least 1.2 A (2.5 A if it's a Zero 2 W). An official Raspberry Pi supply is the safe choice. Old phone chargers often work but sometimes don't give enough power.
- Your Wi-Fi network name and password. The Pi Zero only works on 2.4 GHz Wi-Fi. Most home routers broadcast both 2.4 GHz and 5 GHz under the same name, which is fine. If your router has a separate network with "5G" in its name, use the other one.
- A Xero login that can see the organisation you want on the screen.

You don't need a keyboard, mouse or monitor for the Pi. Everything is done from your Mac.

## 2. Put the operating system on the memory card

The Pi doesn't come with any software. You'll put Raspberry Pi OS (a version of Linux) onto the microSD card using a free Mac app called Raspberry Pi Imager.

1. On your Mac, go to https://www.raspberrypi.com/software/ and download **Raspberry Pi Imager for macOS**. Open the downloaded file and drag Raspberry Pi Imager into Applications.
2. Put the microSD card into your Mac. If macOS pops up a message saying it can't read the disk, click Ignore.
3. Open Raspberry Pi Imager from Applications. The first time, macOS may ask if you're sure you want to open an app downloaded from the internet: click Open. It may also ask for your Mac password, because it needs permission to write to the card.

Imager walks you through a few choices. The wording differs a little between versions, but you're always picking the same things.

4. **Device:** choose **Raspberry Pi Zero** if you have a Zero W or WH, or **Raspberry Pi Zero 2 W** if you have a Zero 2 W. (It's printed on the board.)
5. **Operating system:** click **Raspberry Pi OS (other)**, then **Raspberry Pi OS Lite (32-bit)**. "Lite" means no desktop, which is what you want: the Pi will never have a monitor and the desktop would just slow it down. On a Zero 2 W, the 64-bit Lite is fine too, but 32-bit works on every Zero so the rest of this guide assumes it.
6. **Storage:** choose your microSD card. Check the size matches your card, so you don't wipe the wrong drive.

Next comes the customisation. This is the important bit, because it's how the Pi learns your Wi-Fi and lets you log in to it later. In newer versions of Imager these are separate screens after Storage. In older versions, click Next, then **Edit settings** when it asks "Would you like to apply OS customisation settings?".

7. **Hostname:** `pi0xero`. This is the Pi's name on your network.
8. **Username and password:** username `pi`, and a password you'll remember. Write it down. This guide uses `pi` everywhere, so if you pick a different username, swap it in wherever you see `pi@`.
9. **Wi-Fi:** your network name (SSID) and password, exactly as they are, capitals included. Set the Wi-Fi country to where you are (GB for the UK). If the country is wrong, the Wi-Fi may not turn on at all.
10. **Locale / time zone:** your time zone (for example Europe/London) and keyboard layout. The time zone is what the "upd" time on the screen uses.
11. **SSH** (sometimes under a "Services" or "Remote access" heading): turn it on, and choose **Use password authentication**. SSH is how your Mac will talk to the Pi.
12. If there's an option for **Raspberry Pi Connect**, leave it off.
13. Save, then click **Write** (or **Yes** to apply the settings, then **Yes** to confirm wiping the card).

Writing and checking the card takes 5 to 15 minutes. When Imager says it's finished, take the card out. If macOS complains that the disk wasn't ejected properly, ignore it: Imager has already ejected it.

## 3. Fit the screen and start the Pi

Do this with the Pi unplugged.

1. Push the microSD card into the slot on the end of the Pi, with the card's metal contacts facing the board. It goes in a few millimetres and stops. It doesn't click.
2. Line the screen's black 40-hole socket up over the Pi's 40 pins, so the two boards sit on top of each other with their edges lined up and the screen facing up, away from the Pi. Press down evenly and firmly until the socket is all the way onto the pins. Check from the side that no pins are left showing at one end, which would mean it's one pin out.
3. If the screen board has a small switch on it, leave it where it was set in the factory.
4. Look at the two micro-USB sockets on the Pi. One is labelled **PWR IN** (the one nearest the corner) and the other **USB**. Plug the power supply into **PWR IN**. The other socket won't power it properly.

A green light on the Pi will flicker. The screen won't do anything yet, that comes later.

The first start-up takes a while on a Pi Zero, often 5 minutes or more, because it sets itself up, restarts once and joins your Wi-Fi. Make a cup of tea before moving on.

## 4. Connect to the Pi from your Mac

You'll use the Mac's **Terminal** app to type commands into the Pi over Wi-Fi.

Open Terminal: press Cmd+Space, type `Terminal`, press Enter. A window with a text prompt appears. You can paste into it with Cmd+V as normal.

**On the Mac**, type this and press Enter:

```
ssh pi@pi0xero.local
```

The first time, you'll see something like:

```
The authenticity of host 'pi0xero.local' can't be established.
ED25519 key fingerprint is SHA256:...
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

Type `yes` and press Enter. This is normal for any new machine.

Then it asks for the password you set in Imager. **Nothing appears on screen while you type the password, not even dots.** That's deliberate. Type it and press Enter.

If it worked, the prompt changes to something like:

```
pi@pi0xero:~ $
```

That means you're now typing on the Pi, not the Mac. Everything you type in this window goes to the Pi until you type `exit` or close the window.

If you get `Could not resolve hostname pi0xero.local`, the Pi either hasn't finished starting or hasn't joined the Wi-Fi. Wait another five minutes and try again. If it still fails, see [The Pi can't be found](#the-pi-cant-be-found) in Troubleshooting.

## 5. Bring the Pi up to date

**On the Pi** (the window showing `pi@pi0xero:~ $`):

```
sudo apt update && sudo apt full-upgrade -y
```

`sudo` means "do this as administrator". It may ask for your password again (again, nothing shows as you type).

On a Pi Zero this can take anything from 10 minutes to an hour, depending on how much has changed since the image was made. Lines of text will scroll past. It's finished when you get the `pi@pi0xero:~ $` prompt back. Then restart the Pi:

```
sudo reboot
```

This disconnects you. Wait two minutes, then connect again **on the Mac** with:

```
ssh pi@pi0xero.local
```

## 6. Copy pi0xero onto the Pi

The project lives on your Mac in `~/Documents/Cursor/pi0xero`. You'll copy it across the network.

Open a **second** Terminal window on the Mac (Cmd+N inside Terminal). This one stays on the Mac. Paste this into it:

```
rsync -av --exclude data --exclude config.ini --exclude __pycache__ ~/Documents/Cursor/pi0xero/ pi@pi0xero.local:~/pi0xero/
```

It asks for the Pi's password, then lists the files it copied. You can close this second window afterwards.

Back in the Pi window, check the files arrived:

```
ls ~/pi0xero
```

You should see `README.md  config.example.ini  install.sh  pi0xero  systemd  tests`.

## 7. Run the installer

**On the Pi:**

```
cd ~/pi0xero
./install.sh
```

`cd` moves you into the project folder. The installer then does the setup in one go:

- installs the Python libraries pi0xero needs, plus git and a font, using the Pi's own package manager (which is much quicker on a Zero than building them yourself)
- turns on SPI, the connection the Pi uses to talk to the screen, and gives your user permission to use it
- downloads Waveshare's screen driver into `~/e-Paper`
- creates `config.ini`, the settings file
- sets up a timer that will run the update every 30 minutes (switched on in step 11)

It takes 5 to 15 minutes and finishes with "Done." If you'd rather the screen updated every hour instead, run it as `INTERVAL=1h ./install.sh`. You can change this later too.

Now restart so SPI switches on:

```
sudo reboot
```

Wait two minutes and reconnect **on the Mac**: `ssh pi@pi0xero.local`.

## 8. Test the screen

First tell pi0xero which version of the screen you have (the V2, V3 or V4 you wrote down in step 1). **On the Pi**, open the settings file in a simple text editor called nano:

```
nano ~/pi0xero/config.ini
```

Use the arrow keys to move around (the mouse doesn't work in nano). Find the line:

```
model = epd2in13_V4
```

If your screen is a V4, leave it. For a V3 change it to `epd2in13_V3`, for a V2 to `epd2in13_V2`. Then save and exit: press Ctrl+O, then Enter to save, then Ctrl+X to exit. (That's the Control key, not Cmd.)

Now draw some made-up numbers:

```
cd ~/pi0xero
python3 -m pi0xero demo
```

The screen flashes black and white a few times, which is how e-Paper clears itself, then shows "Demo Company (UK)" and four numbers. It takes 10 to 20 seconds.

If the picture is upside down for how you want to stand it, open `config.ini` again, change `rotate = 0` to `rotate = 180`, save, and run the demo again.

If nothing happens on the screen, or you get an error, see [The screen doesn't change](#the-screen-doesnt-change).

## 9. Create a Xero app

Xero needs to know about pi0xero before it'll let it read your data. You do this once, on the Mac, in a web browser.

1. Go to https://developer.xero.com/app/manage and log in with your normal Xero email and password.
2. Click **New app**.
3. Fill in the form:

   | Field | What to enter |
   |---|---|
   | App name | `pi0xero` (Xero shows this when you approve access) |
   | Integration type | **Mobile or desktop app** |
   | Company or application URL | `https://localhost` |
   | Redirect URI | `http://localhost:5055/callback` |

   Type the redirect URI exactly as shown, with no space or slash at the end.

4. Tick the box agreeing to the terms and click **Create app**.
5. You're taken to the app's page. Click **Configuration** if it's not already showing. Copy the long string labelled **Client id** (there's usually a copy button next to it).

Now put the client id in the Pi's settings. **On the Pi:**

```
nano ~/pi0xero/config.ini
```

Find the line `client_id =` near the top and paste the client id after it, so it looks like this (yours will be different):

```
client_id = 3F2A9C...E71B
```

To paste into nano from your Mac, use Cmd+V as normal. Save with Ctrl+O, Enter, and exit with Ctrl+X.

## 10. Log the Pi in to Xero

The Pi has no web browser, so you'll do the Xero login in the browser on your Mac and pass the answer back to the Pi. The neatest way is to reconnect to the Pi with a small extra option that links the two.

In the Pi window, type `exit` to disconnect. Then **on the Mac**:

```
ssh -L 5055:127.0.0.1:5055 pi@pi0xero.local
```

(The extra `-L 5055:127.0.0.1:5055` means "when my browser visits localhost:5055, send it to the Pi".)

Now **on the Pi**:

```
cd ~/pi0xero
python3 -m pi0xero login
```

It prints a very long web address beginning `https://login.xero.com/identity/connect/authorize?...`. Select the whole thing in Terminal (it may wrap over several lines; drag from the `h` of https to the very last character), copy it with Cmd+C, and paste it into the address bar of Safari or Chrome on your Mac.

Xero asks you to log in (if you aren't already), then shows a page asking you to let pi0xero access your organisation. Pick the organisation, and click **Allow access**.

The browser should end on a plain page saying **Connected to Xero. You can close this tab.** Back in Terminal you'll see:

```
Logged in.
  1. Your Organisation Ltd
Using Your Organisation Ltd.
Run `python3 -m pi0xero update` to draw the screen.
```

If you allowed more than one organisation, it lists them and asks which one to show. Type the number and press Enter.

### If the browser shows "can't connect" instead

That happens when the link between Mac and Pi isn't there, for example if you connected with plain `ssh pi@pi0xero.local`. It's easy to get round. Leave the Terminal as it is (the login command is still waiting). In the browser, click in the address bar and copy the whole address. It starts with `http://localhost:5055/callback?code=`. Paste it into the Terminal window and press Enter. You have about 5 minutes to do this.

The login is saved in `~/pi0xero/data/tokens.json`. Anyone with that file can read your Xero reports, so don't copy it anywhere or share it.

## 11. First real update, then switch on the timer

**On the Pi:**

```
python3 -m pi0xero update
```

It takes 20 to 40 seconds on a Zero: it asks Xero for twelve monthly Profit and Loss reports, adds them up, then redraws the screen. The last line of text shows the exact figures, for example:

```
2026-11-05 10:24:07 INFO Revenue Oct 41000.00, TTM 487800.00; op profit 11000.00, TTM 127800.00
```

It's worth checking these against Xero once: in Xero, run a Profit and Loss report for last month, and one for the last 12 months, and compare. See [What the numbers mean](#14-what-the-numbers-mean) if they don't match.

When you're happy, switch on the timer so it updates by itself:

```
sudo systemctl start pi0xero.timer
```

The timer also starts itself every time the Pi is switched on, so you only do this once.

That's the setup finished. Type `exit` to disconnect. From now on the Pi just needs power and Wi-Fi.

## 12. Living with it

All of these are typed **on the Pi**, after connecting with `ssh pi@pi0xero.local`.

To update the screen right now instead of waiting:

```
sudo systemctl start pi0xero.service
```

To see when it last ran and when it'll run next:

```
systemctl list-timers pi0xero.timer
```

To read what happened on recent runs, including any errors (press `q` to get out):

```
journalctl -u pi0xero.service -n 50
```

To change how often it updates:

```
sudo systemctl edit --full pi0xero.timer
```

Change `OnUnitActiveSec=30min` to what you want (`15min`, `1h`, `6h` and so on), save with Ctrl+O, Enter, Ctrl+X, then:

```
sudo systemctl restart pi0xero.timer
```

I wouldn't go below 15 minutes. The screen shouldn't be redrawn more often than every 3 minutes, and month-end numbers don't change that fast anyway.

To show a different organisation: `cd ~/pi0xero && python3 -m pi0xero orgs`. If the one you want isn't listed, do step 10 again and tick it on the Xero page.

To change the name in the top bar: set `title = ` in `config.ini` to whatever you like. Blank means the organisation's name from Xero.

To switch the Pi off, don't just pull the plug, as that can corrupt the memory card. Run `sudo poweroff`, wait until the green light has stayed off for 10 seconds, then unplug it. The screen keeps showing the last numbers with no power at all. If you're putting it away for months, run `cd ~/pi0xero && python3 -m pi0xero clear` first to blank the screen, which is better for the e-Paper.

### Staying logged in to Xero

Each update quietly renews the Xero login. As long as the Pi runs at least once every 60 days, you'll never need to log in again. If it's been unplugged for longer than that, or someone removes pi0xero from Xero's list of connected apps, the top bar shows `! login needed` and you repeat step 10.

### What the top bar tells you

`upd 5 Nov 10:07` means the last update worked at that time.

`! offline (5 Nov 09:30)` means it couldn't reach Xero (Wi-Fi down, or Xero down). The numbers are from the time in brackets. It'll try again at the next update.

`! Xero error (...)` means Xero answered but something went wrong. Check the log with `journalctl` as above.

`! login needed (...)` means see Staying logged in, above.

## 13. Troubleshooting

### The Pi can't be found

You get `Could not resolve hostname pi0xero.local` or `Operation timed out`.

- Wait 10 minutes after first power-on. A Pi Zero is slow to start the first time.
- Check the power is in the **PWR IN** socket and the green light flickered.
- Log in to your router's admin page (often printed on a sticker on the router) and look at its list of connected devices for `pi0xero`. If it's there, use its address instead, for example `ssh pi@192.168.1.42`, and in every other command in this guide.
- If it's not on the router's list, the Wi-Fi settings were probably wrong: name or password mistyped, a 5 GHz-only network, or the wrong Wi-Fi country. Put the card back in the Mac and go through step 2 again carefully. Re-writing the card wipes it, which is fine at this stage.

### ssh says "REMOTE HOST IDENTIFICATION HAS CHANGED"

This happens if you re-wrote the card: the Pi is "new" but has the same name. On the Mac, run `ssh-keygen -R pi0xero.local`, then connect again and answer `yes`.

### "Permission denied" when logging in with ssh

Wrong username or password. The username is the one you set in Imager (this guide assumes `pi`). If you've forgotten the password, re-write the card (step 2).

### `./install.sh: Permission denied`

Run `chmod +x install.sh` and try again.

### The screen doesn't change

- If you see `Can't load the Waveshare driver`, check `~/e-Paper/RaspberryPi_JetsonNano/python/lib/waveshare_epd/` exists with `ls ~/e-Paper/RaspberryPi_JetsonNano/python/lib/waveshare_epd/`. If it doesn't, run `rm -rf ~/e-Paper` and then `./install.sh` again.
- If the command sits there forever printing `e-Paper busy`, press Ctrl+C. It's usually the wrong `model` in `config.ini`, or the screen isn't pushed fully onto the pins. Run `sudo poweroff`, unplug, reseat the screen, and try again. If it still hangs, try the other versions (V2, V3, V4) in turn.
- `No such file or directory: '/dev/spidev0.0'` means SPI isn't on. Run `sudo raspi-config nonint do_spi 0`, then `sudo reboot`.
- A "permission denied" error mentioning spidev or gpio means the reboot after the installer hasn't happened yet. Run `sudo reboot`.

### Faint ghosts of old numbers on the screen

Normal for e-Paper over time. Run `python3 -m pi0xero clear` and then `python3 -m pi0xero update`.

### Login problems

`invalid_scope`: the Xero app wasn't created as "Mobile or desktop app". Create a new one (step 9) and put its client id in `config.ini`.

`unauthorized_client`, or Xero complaining about the redirect URI: the redirect URI in the Xero app must be exactly `http://localhost:5055/callback`. You can fix it on the app's Configuration page in the Xero developer site.

`Set client_id in config.ini`: you haven't done the nano part of step 9 yet, or it didn't save.

Xero doesn't let you tick your organisation: your Xero user may not have permission to connect apps. Ask whoever runs the organisation's Xero account.

### Wrong time in the top bar

Run `sudo raspi-config`, choose Localisation Options, then Timezone. Use the arrow keys and Enter, and Tab to get to Finish.

## 14. What the numbers mean

"Oct" (or whichever month) is the last complete calendar month. On 5 November that's October.

TTM, trailing twelve months, is the twelve complete months ending with that month. On 5 November it's November last year to October this year.

Revenue is the total income line from Xero's Profit and Loss report. Depending on your region and accounts it's called Total Income, Total Trading Income or Total Turnover.

Operating profit is gross profit less total operating expenses. Other income (interest received, grants and so on) and anything Xero lists below operating expenses are left out, so it won't match the Net Profit line in Xero.

The percentages next to operating profit are the operating margin: operating profit as a share of revenue for the same period.

pi0xero always asks Xero for the standard layout of the Profit and Loss report. If you normally look at a custom layout in Xero, tick "standard layout" when comparing, or the lines may be grouped differently.

Each update makes 13 requests to Xero (twelve monthly reports and one for the organisation's name and currency). Xero allows 5,000 a day, so even a 15-minute timer uses about a quarter of that.

---

## For tinkering

You can preview the screen on your Mac without the Pi, if Python's Pillow and requests libraries are installed there:

```
cd ~/Documents/Cursor/pi0xero
python3 -m pi0xero demo --preview demo.png
```

Tests: `python3 -m pytest tests`.

```
pi0xero/
├── README.md              this guide
├── install.sh             one-off setup on the Pi
├── config.example.ini     copied to config.ini by install.sh
├── systemd/               timer and service templates used by install.sh
├── pi0xero/
│   ├── __main__.py        commands: login, update, demo, orgs, clear
│   ├── config.py          config.ini and data file paths
│   ├── xero.py            Xero login, token renewal, API calls
│   ├── metrics.py         reads the P&L, adds up last month and TTM
│   └── display.py         draws the 250×122 picture and drives the screen
├── tests/test_metrics.py
└── data/                  tokens.json and state.json, created on the Pi (keep private)
```
