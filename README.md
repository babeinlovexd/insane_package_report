# Insane Updater

*[Read this in English](#insane-updater-english)*

**Insane Updater** ist ein zweiteiliges Projekt, das dir in Home Assistant mitteilt, wenn es Updates für die in deinen ESPHome-Geräten verwendeten `packages` und `external_components` gibt. Das System greift während der Kompilierung eines ESPs die verwendeten GitHub-Repositories ab und übermittelt diese asynchron an Home Assistant. Dort wird eine dynamische Update-Entität für jedes Repository und Gerät erstellt.

---

## 🏗 Architektur

Das Projekt besteht aus zwei Hauptkomponenten:

1. **ESPHome Custom Component (`insane_package_report`)**
   Diese Komponente liest die rohe ESPHome-Konfiguration (`CORE.raw_config`) deines Geräts während der Kompilierung. Sie sucht nach `packages` und `external_components`, extrahiert deren GitHub-URLs und Refs (Tags/Branches) und brennt diese Informationen mit in die Firmware ein. Sobald der ESP mit Home Assistant verbunden ist (via Native API), feuert er die Liste seiner Repositories in Form von Home Assistant Custom Events (`esphome.insane_package_report`). Dabei wird ein asynchrones Delay zwischen jedem Event eingefügt, um zu verhindern, dass das 255-Zeichen-Limit für Events überschritten wird.

2. **Home Assistant Integration (`insane_updater`)**
   Die HA-Integration lauscht auf diese Custom Events. Wenn ein Event eintrifft, erkennt die Integration das meldende ESP-Gerät anhand seiner Device-ID in der Home Assistant Device Registry. Anschließend wird dynamisch (ohne Neustart!) eine Update-Entität (`UpdateEntity`) dem ESP-Gerät hinzugefügt. Ein `DataUpdateCoordinator` prüft im eingestellten Intervall (1h, 3h, 6h, 12h oder 24h) per GitHub API auf neue Versionen:
   - Ist ein `ref` (z.B. Tag) konfiguriert, wird die `/tags` API geprüft, um neuere Tags zu finden.
   - Ist kein `ref` konfiguriert, wird der Commit-Hash des `default_branch` überprüft.
   Die installierten Versionen werden über den HA Storage Helper persistiert, sodass die Update-Entitäten auch nach einem Neustart von Home Assistant sofort wieder ihre korrekten Stati anzeigen.

---

## 📥 Installation

Die Installation ist in zwei Schritte unterteilt: Du musst die Home Assistant Integration installieren, damit Updates angezeigt werden, und du musst deinen ESPHome-Code anpassen, damit dieser die verbauten Komponenten meldet.

### 1. Home Assistant Integration (`insane_updater`)

**Empfohlen: Installation via HACS (Home Assistant Community Store)**

Dies ist der einfachste und sicherste Weg für die meisten Nutzer.

1. Öffne **HACS** in deinem Home Assistant.
2. Klicke auf **Integrationen**.
3. Klicke auf das **Drei-Punkte-Menü** oben rechts und wähle **Benutzerdefinierte Repositories**.
4. Füge die URL dieses Repositories ein (z.B. `https://github.com/babeinlovexd/insane_package_report`) und wähle als Kategorie **Integration**.
5. Klicke auf **Hinzufügen**.
6. Suche nun in HACS nach "Insane Updater" und klicke auf **Herunterladen**.
7. **Starte Home Assistant neu**.
8. Gehe in Home Assistant zu **Einstellungen -> Geräte & Dienste -> Integration hinzufügen**.
9. Suche nach **Insane Updater** und füge die Integration hinzu.
10. Konfiguriere die Integration nach deinen Wünschen:
    - **Update-Intervall:** Wähle, wie oft nach Updates gesucht werden soll (1h, 3h, 6h, 12h oder 24h).
    - *(Optional aber dringend empfohlen)*: Trage einen **GitHub Personal Access Token** ein. Ein Classic Token mit den Rechten `public_repo` reicht vollkommen aus. Ohne diesen Token stößt du bei vielen Anfragen schnell an das Rate-Limit von GitHub und Updates können nicht geprüft werden.

**Alternative: Manuelle Installation (Für Experten)**

1. Lade dir dieses Repository als ZIP-Datei herunter.
2. Kopiere den gesamten Ordner `custom_components/insane_updater` in das Verzeichnis `config/custom_components/` deiner Home Assistant Installation.
3. Fahre ab Schritt 7 der HACS-Anleitung fort.

### 2. ESPHome Component (`insane_package_report`)

Du musst keine Dateien manuell auf deinen Rechner herunterladen! Du kannst die Komponente direkt von GitHub über deine ESPHome YAML-Datei einbinden.

Füge diesen Block zu den `external_components` deines ESPs hinzu:

```yaml
external_components:
  - source:
      type: git
      url: https://github.com/babeinlovexd/insane_package_report
    components: [ insane_package_report ]
    refresh: 1d # Prüft einmal am Tag auf neue Versionen der Komponente
```

*Falls du die Komponente trotzdem manuell installieren möchtest, kannst du den Ordner `components/insane_package_report` in das `custom_components` Verzeichnis deines ESPHome-Ordners kopieren.*

---

## ⚙️ Konfiguration (ESPHome)

Damit dein ESPHome-Gerät seine genutzten Packages melden kann, musst du die Komponente in der YAML des jeweiligen Geräts aktivieren.

**Achtung:** Dies ist ein Dummy-Eintrag. Du musst einfach nur `insane_package_report:` ins Root-Level deiner YAML schreiben.

```yaml
# Aktiviert den Insane Package Report (Zwingend erforderlich!)
insane_package_report:
```

### 💡 Detaillierte Beispiele

Hier siehst du, wie `packages` und `external_components` üblicherweise eingebunden werden, damit Insane Updater sie erkennt:

#### Beispiel 1: Einfaches Package von GitHub mit Versions-Tag
```yaml
insane_package_report:

packages:
  mein_smart_device:
    # URL im Format benutzer/repo
    github: jesserockz/esphome-smart-device
    # Eine explizite Version (Tag oder Branch) ist für Updates sehr empfehlenswert!
    ref: v1.0.0
    # Optional: Pfad zur YAML-Datei innerhalb des Repos
    files:
      - smart_device.yaml
```

#### Beispiel 2: External Component von GitHub
```yaml
insane_package_report:

external_components:
  - source:
      type: git
      # Komplette GitHub-URL
      url: https://github.com/pr#1234
      # Auf welchen Commit oder Branch soll geprüft werden?
      ref: fix-irgendwas
    # Welche Komponenten sollen aus dem Repo geladen werden?
    components: [ sensor, binary_sensor ]
```

#### Beispiel 3: Kombination von beidem
```yaml
insane_package_report:

packages:
  wifi_config:
    github: mein_user/meine_esphome_configs
    ref: main
    files: [ wifi.yaml ]

external_components:
  # Einbinden von Insane Package Report selbst!
  - source:
      type: git
      url: https://github.com/babeinlovexd/insane_package_report
      components: [ insane_package_report ]
    refresh: 1d
```

**Was passiert nun?**
1. Beim Klicken auf "Install" / "Compile" parst die `insane_package_report`-Komponente die obige Konfiguration.
2. Sie merkt sich die Repositories (z.B. `jesserockz/esphome-smart-device` mit Tag `v1.0.0`) und das Pull-Request-Repo (`fix-irgendwas`).
3. Nach dem Start des ESP-Geräts meldet es sich per API bei Home Assistant.
4. Nach einem kurzen Delay feuert das Gerät Events an Home Assistant ab.
5. Home Assistant fängt diese Events ab und erstellt unter dem ESP-Gerät neue Update-Entitäten ("esphome-smart-device Update" und "pr#1234 Update").
6. Zeigt das Repo auf GitHub einen neueren Release oder Tag, meldet die Update-Entität in Home Assistant ein verfügbares Update! Du kannst dann einfach deine ESPHome YAML anpassen und neu flashen.

---

## 🛠 Fehlerbehebung

- **Es tauchen keine Entitäten in HA auf?**
  Prüfe, ob du die ESPHome-Komponente per `insane_package_report:` auf Root-Ebene wirklich aktiviert hast und die Firmware erfolgreich auf den ESP geflasht wurde.
- **GitHub Rate Limit Error?**
  Dies passiert, wenn HA zu oft die GitHub API ohne Token abfragt (was bei vielen Repos schnell passiert). Füge der HA-Integration einen Token hinzu, indem du die Integration über die UI konfigurierst oder löschst und neu hinzufügst.
- **Wann werden die Sensoren erstellt?**
  Die Sensoren werden beim Start des ESPs an HA übertragen. Wird der ESP frisch gebootet (z.B. vom Strom getrennt und wieder eingesteckt), sendet er wenige Sekunden nach der Verbindung die Report-Events an Home Assistant.


---


# Insane Updater (English)

**Insane Updater** is a two-part project that notifies you in Home Assistant whenever updates are available for the `packages` and `external_components` used in your ESPHome devices. During the compilation of an ESP, the system intercepts the GitHub repositories being used and asynchronously transmits them to Home Assistant. A dynamic update entity is then created for each repository and device.

---

## 🏗 Architecture

The project consists of two main components:

1. **ESPHome Custom Component (`insane_package_report`)**
   This component reads the raw ESPHome configuration (`CORE.raw_config`) of your device during compilation. It searches for `packages` and `external_components`, extracts their GitHub URLs and refs (tags/branches), and bakes this information directly into the firmware. Once the ESP is connected to Home Assistant (via Native API), it fires off its list of repositories as Home Assistant Custom Events (`esphome.insane_package_report`). An asynchronous delay is inserted between each event to prevent exceeding the 255-character limit for events.

2. **Home Assistant Integration (`insane_updater`)**
   The HA integration listens for these custom events. When an event arrives, the integration identifies the reporting ESP device using its Device ID from the Home Assistant Device Registry. Subsequently, an update entity (`UpdateEntity`) is dynamically added to the ESP device (without requiring a restart!). A `DataUpdateCoordinator` checks the GitHub API for new versions at a configured interval (1h, 3h, 6h, 12h, or 24h):
   - If a `ref` (e.g., tag) is configured, the `/tags` API is checked to find newer tags.
   - If no `ref` is configured, the commit hash of the `default_branch` is checked.
   The installed versions are persisted via the HA Storage Helper, ensuring that update entities display their correct states immediately after a Home Assistant restart.

---

## 📥 Installation

The installation is divided into two steps: You must install the Home Assistant integration to display updates, and you must adjust your ESPHome code so that it reports the utilized components.

### 1. Home Assistant Integration (`insane_updater`)

**Recommended: Installation via HACS (Home Assistant Community Store)**

This is the easiest and safest method for most users.

1. Open **HACS** in your Home Assistant.
2. Click on **Integrations**.
3. Click on the **three-dot menu** in the top right corner and select **Custom repositories**.
4. Paste the URL of this repository (e.g., `https://github.com/babeinlovexd/insane_package_report`) and select **Integration** as the category.
5. Click **Add**.
6. Now search HACS for "Insane Updater" and click **Download**.
7. **Restart Home Assistant**.
8. In Home Assistant, navigate to **Settings -> Devices & Services -> Add Integration**.
9. Search for **Insane Updater** and add the integration.
10. Configure the integration to your liking:
    - **Update Interval:** Choose how often to check for updates (1h, 3h, 6h, 12h, or 24h).
    - *(Optional but highly recommended)*: Provide a **GitHub Personal Access Token**. A Classic Token with `public_repo` permissions is perfectly sufficient. Without this token, you will quickly hit the GitHub Rate Limit if you have many requests, preventing update checks.

**Alternative: Manual Installation (For Experts)**

1. Download this repository as a ZIP file.
2. Copy the entire `custom_components/insane_updater` folder into the `config/custom_components/` directory of your Home Assistant installation.
3. Continue from step 7 of the HACS instructions.

### 2. ESPHome Component (`insane_package_report`)

You do not need to download any files manually to your computer! You can include the component directly from GitHub via your ESPHome YAML file.

Add this block to the `external_components` of your ESP:

```yaml
external_components:
  - source:
      type: git
      url: https://github.com/babeinlovexd/insane_package_report
    components: [ insane_package_report ]
    refresh: 1d # Checks for new versions of the component once a day
```

*If you prefer to install the component manually anyway, you can copy the `components/insane_package_report` folder into the `custom_components` directory of your ESPHome folder.*

---

## ⚙️ Configuration (ESPHome)

For your ESPHome device to report its used packages, you must activate the component in the YAML of the respective device. Additionally, the component needs permission to fire Home Assistant events. For this, `homeassistant_services: true` must be enabled in your `api:` configuration.

**Attention:** This is a dummy entry. You simply need to write `insane_package_report:` at the root level of your YAML.

```yaml
api:
  # Required so ESPHome can send events to Home Assistant!
  homeassistant_services: true

# Activates the Insane Package Report (Mandatory!)
insane_package_report:
```

### 📌 Tags vs. Branches (Smart Updates!)

The integration is extremely smart and detects updates entirely automatically, regardless of whether you use fixed versions or rolling branches:

- **Tracking Tags (Release Updates):**
  If you specify a fixed version like `ref: v1.0.0`, the integration will check GitHub to see if a newer release tag exists (e.g., `v1.0.1`). If so, a "Update available" notification will appear in Home Assistant.
- **Tracking Branches (Commit Updates):**
  If you specify *no* `ref` or use a branch name like `ref: main`, the integration remembers exactly which commit you downloaded from GitHub when flashing your ESP (e.g., `main (a1b2c3d)`). As soon as the repository author pushes a new code commit, "Update available" is immediately displayed in Home Assistant!
  Once you click "Install" (or "Clean Build") in ESPHome and re-flash the ESP, the integration recognizes the re-flash via the ESPHome compilation date. The "Update available" badge disappears automatically, and the ESP is considered up to date again!

### 💡 Detailed Examples

Here is how `packages` and `external_components` are usually included so that Insane Updater can recognize them:

#### Example 1: Simple Package from GitHub with Version Tag
```yaml
api:
  homeassistant_services: true

insane_package_report:

packages:
  my_smart_device:
    # URL in the format user/repo
    github: jesserockz/esphome-smart-device
    # An explicit version (tag or branch) is highly recommended for updates!
    ref: v1.0.0
    # Optional: Path to the YAML file within the repo
    files:
      - smart_device.yaml
```

#### Example 2: External Component from GitHub
```yaml
api:
  homeassistant_services: true

insane_package_report:

external_components:
  - source:
      type: git
      # Full GitHub URL
      url: https://github.com/pr#1234
      # Which commit or branch should be tracked?
      ref: fix-something
    # Which components should be loaded from the repo?
    components: [ sensor, binary_sensor ]
```

#### Example 3: Combination of Both
```yaml
api:
  homeassistant_services: true

insane_package_report:

packages:
  wifi_config:
    github: my_user/my_esphome_configs
    ref: main
    files: [ wifi.yaml ]

external_components:
  # Including Insane Package Report itself!
  - source:
      type: git
      url: https://github.com/babeinlovexd/insane_package_report
      components: [ insane_package_report ]
    refresh: 1d
```

**What happens next?**
1. When clicking "Install" / "Compile", the `insane_package_report` component parses the above configuration.
2. It memorizes the repositories (e.g., `jesserockz/esphome-smart-device` with tag `v1.0.0`) and the pull request repo (`fix-something`).
3. After the ESP device boots up, it connects to Home Assistant via API.
4. After a short delay, the device fires events to Home Assistant.
5. Home Assistant intercepts these events and creates new update entities under the ESP device ("esphome-smart-device Update" and "pr#1234 Update").
6. If the repo on GitHub shows a newer release or tag, the update entity reports an available update in Home Assistant! You can then simply adjust your ESPHome YAML and re-flash.

---

## 🛠 Troubleshooting

- **No entities showing up in HA?**
  Verify that you have genuinely activated the ESPHome component via `insane_package_report:` at the root level and that the firmware has been successfully flashed onto the ESP.
- **GitHub Rate Limit Error?**
  This occurs when HA queries the GitHub API too often without a token (which happens quickly with multiple repos). Add a token to the HA integration by configuring it via the UI or by deleting and re-adding the integration.
- **When are the sensors created?**
  The sensors are transmitted to HA upon ESP startup. If the ESP is freshly booted (e.g., unplugged and plugged back in), it sends the report events to Home Assistant a few seconds after establishing the connection.
