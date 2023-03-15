# PICCTV

*Bezpečná* bezpečnostní kamera pro Raspberry PI

## O projektu

Projekt je rozdělen na tři části: kamera, server a prohlížečová aplikace pro živý přenos.

## Použití

### Vygenerování klíčů

Nejprve je třeba vygenerovat šifrovací klíče. To lze udělat jednodušše za použí scriptu, takto:
`python utils/generate_keys.py`. Klíče jsou čtyři, dva (privátní a veřejný) pro kameru a dva pro příjemce obrazu z
kamery.
Uloží se do souborů `camera_private.key`, `camera_public.key`, `receiver_private.key` a `receiver_public.key`.
Aby šifrování bylo smysluplné, privátní klíče musí být uchovávány na bezpečném místě.

### Nastavení serveru

Kód pro server se nachází v adresáři [server](server). Před spuštěním je nejprve potřeba vytvořit konfigurační
soubor `server_config.json`.
V něm musí být definovány tyto hodnoty:

* `max_recording_file_size`: Maximální velikost jednoho souboru se záznamem z kamery v bytech
* `max_recording_files`: Maximální počet souborů se záznamem, které budou najednou uloženy na disku
* `records_directory`: Adresář, do kterého se budou průběžně ukládat soubory se záznamem
* `server_port`: Port, na kterém bude server poslouchat

Konfigurační soubor může vypadat například takto:

```json
{
  "max_recording_file_size": 20000000,
  "max_recording_files": 5,
  "records_directory": "records",
  "server_port": 8765
}
```

S takovýmto konfiguračním souborem tedy bude server poslouchat na portu 8765 a záznam z kamery ukládat do adresáře
records. Jeden soubor bude mít maximálně 20 Mb a zároveň bude uloženo maximálně 5 souborů. Velikost adresáře records
tedy nikdy nepřesáhne 5 * 20 Mb = 100 Mb.

Server lze spustit takto: `python receiver_server.py`.

### Nastavení kamery

Kód pro kameru se nachází v adresáři [camera](camera). Před spuštěním je nejprve potřeba vytvořit konfigurační
soubor `camera_config.json`. V něm musí být definovány tyto hodnoty:

* `receiver_public_key_hex`: Veřejný klíč přijemce obrazu z kamery (zkopírováno z `receiver_public.key`)
* `camera_private_key_hex`: Privátní klíč kamery (zkopírováno z `camera_private.key`)
* `video_height`: Výška přenášeného obrazu v pixelech
* `video_width`: Šířka přenášeného obrazu v pixelech. Kombinace výšky a šířky musí být podporována hardwarem připojeného
  kamerového modulu
* `video_quality`: Číslo od 0 do 4, čím vyšší, tím nižší úroveň komprese
* `server_address`: Adresa serveru

Konfigurační soubor může vypadat například takto:

```json
{
  "receiver_public_key_hex": "abc123",
  "camera_private_key_hex": "cba321",
  "video_height": 972,
  "video_width": 1296,
  "video_quality": 4,
  "server_address": "ws://192.168.0.88:8765"
}
```

S takovýmto konfiguračním souborem tedy bude kamera posílat obraz nejvyšší kvality o rozlišení 972x1296 na server na
adrese `ws://192.168.0.88:8765`. Obraz bude šifrován zadanými klíči.

Odesílání obrazu lze spustit takto: `python camera_client.py`

### Sledování živého přenosu

Kód prohlížečové aplikace pro živé sledování se nachází v adresáři [viewer-live](viewer-live). Lze ji spustit příkazem `npm run dev`.
Aplikace po spuštění vyžaduje zadání tří hodnot:

* Camera public key (hex): Veřejný klíč kamery (zkopírováno z `camera_public.key`)
* Viewer private key (hex): Privátní klíč příjemce obrazu z kamery (zkopírováno z `receiver_private.key`)
* Server address: Adresa serveru, na který kamera posílá obraz

Po zadání hodnot a kliknutí na tlačítko `Start stream` začne živý přenos.

### Dešifrování a přehrání uložených nahrávek

Nahrávky uložené v `records_directory` (viz konfigurace serveru) jsou šifrované. Pro jejich přehrání je třeba je dešifrovat.
To lze udělat za pomocí scriptu, takto: `python utils/decryptor.py nahravka.h264.enc`. Script načte soubory `camera_public.key`
a `receiver_private.key` a dešifruje nahrávku `nahravka.h264.enc`. Výsledek uloží do souboru `nahravka.h264` (odstraní příponu `.enc`).

Dešifrovaná nahrávka je stream H.264 framů. Lze ji přehrát například pomocí programu ffplay: `ffplay nahravka.h264`.

Pro přehrání v běžných přehrávačích (VLC, apod.) je třeba stream zabalit do nějakého kontejneru. To lze udělat například pomocí programu ffmpeg:
`ffmpeg -i nahravka.h264 -c copy nahravka.mp4`

Před zabalením do kontejneru je také možné několik nahrávek spojit do jedné: `cat nahravka1.h264 nahravka2.h264 nahravka3.h264 > spojena.h264`
