# AutoMediaMover — plugin Deluge 2.x

Detectează automat dacă un torrent terminat este **film** sau **serial** și îl mută:

| Tip | Destinație |
|-----|-----------|
| Serial | `<Folder seriale>/<Nume serial>/Season 01/` (subfolderul de sezon e opțional) |
| Film | `<Folder filme>/` sau `<Folder filme>/<Titlu (An)>/` (opțional) |
| Altceva (fără fișiere video) | nu se atinge |

Funcționează pe **Windows** și **Linux** (căi normalizate, nume de foldere curățate de caractere invalide pe Windows) și se configurează din **clientul GTK** și din **interfața Web** (Preferences → AutoMediaMover).

## Cum detectează un serial

Pe numele torrentului, apoi pe numele fișierelor video:

- `S01E02`, `S01.E02`, `s1e2`, `1x02`
- `Episode 5`, `Ep 05`, `Episodul 5`
- pachete de sezon: `S01`, `S01-S05`, `Season 1`, `Sezonul 2`, `Saison`, `Staffel`, `Temporada`
- `Complete Series`, `Mini-Series`, `Integrala`
- emisiuni zilnice: `Show.2024.03.14`

Dacă nu se potrivește niciun tipar și există fișiere video, e considerat film (titlul se ia până la an / eticheta de calitate, ex. `Inception.2010.1080p.BluRay` → `Inception (2010)`). Fișierele `sample` sunt ignorate.

## Opțiuni

| Opțiune | Implicit | Descriere |
|---------|----------|-----------|
| Automatically move finished torrents | da | activează mutarea la terminarea download-ului |
| Movies folder / TV series folder | gol | căile **de pe mașina unde rulează `deluged`**; gol = nu se mută acel tip |
| Create season sub-folder | da | `Serial/Season 03/` |
| Season folder format | `Season {season:02d}` | format Python, ex. `Sezonul {season}` |
| Remove year from series name | nu | `Doctor Who (2005)` → `Doctor Who` |
| Create "Title (Year)" sub-folder | nu | un folder per film |
| Video extensions | mkv, mp4, avi, … | extensiile considerate video |
| Test a name | — | arată ce ar face pluginul cu un nume dat |
| Process all completed torrents now | — | aplică regulile pe torrentele deja terminate |

> Dacă ai activat și „Move completed to” în Deluge, AutoMediaMover rulează după el și mutarea lui are prioritate.

## Build & instalare

Egg-ul trebuie să aibă aceeași versiune de Python ca Deluge (Deluge 2.2.0 pe Windows = Python 3.9). Pluginul e Python pur, deci scriptul de pe Windows doar redenumește tag-ul.

**Windows**

```powershell
.\build.ps1 -Install          # construiește dist\AutoMediaMover-1.0-py3.9.egg și îl copiază în %APPDATA%\deluge\plugins
```

**Linux**

```bash
./build.sh                    # apoi copiază dist/*.egg în ~/.config/deluge/plugins/
```

Alternativ: Preferences → Plugins → **Install** și alegi fișierul `.egg`. Repornește Deluge, bifează **AutoMediaMover**, setează folderele.

Pentru Web UI, pluginul trebuie activat din Web UI (Preferences → Plugins) sau din clientul GTK — ambele scriu în același daemon.

## Teste

```bash
python tests/test_detector.py
```

## Licență

GPLv3 (ca Deluge).
