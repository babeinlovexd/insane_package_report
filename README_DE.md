# Insane Updater

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

Damit dein ESPHome-Gerät seine genutzten Packages melden kann, musst du die Komponente in der YAML des jeweiligen Geräts aktivieren. Zusätzlich muss die Komponente die Erlaubnis haben, Home Assistant Events abzufeuern. Hierfür muss unter `api:` der Punkt `homeassistant_services: true` aktiviert werden.

**Achtung:** Dies ist ein Dummy-Eintrag. Du musst einfach nur `insane_package_report:` ins Root-Level deiner YAML schreiben.

```yaml
api:
  # Zwingend erforderlich, damit ESPHome Events an Home Assistant senden darf!
  homeassistant_services: true

# Aktiviert den Insane Package Report (Zwingend erforderlich!)
insane_package_report:
```

### 📌 Tags vs. Branches (Smarte Updates!)

Die Integration ist extrem smart und erkennt Updates vollkommen automatisch, egal ob du mit festen Versionen oder rollierenden Branches arbeitest:

- **Tags tracken (Release Updates):**
  Gibst du eine feste Version wie `ref: v1.0.0` an, prüft die Integration auf GitHub, ob es einen neueren Release-Tag gibt (z.B. `v1.0.1`). Wenn ja, meldet dir Home Assistant "Update verfügbar".
- **Branches tracken (Commit Updates):**
  Gibst du *kein* `ref` an oder nutzt einen Branch-Namen wie `ref: main`, merkt sich die Integration exakt, welchen Commit du beim Flashen deines ESPs von GitHub heruntergeladen hast (z.B. `main (a1b2c3d)`). Sobald der Autor des Repositories neuen Code pusht, wird dir in Home Assistant sofort "Update verfügbar" angezeigt!
  Klickst du dann in ESPHome auf "Install" (oder "Clean Build") und flasht den ESP neu, erkennt die Integration anhand des ESPHome-Kompilierungsdatums, dass du neu geflasht hast. Das "Update verfügbar" verschwindet automatisch und der ESP gilt wieder als aktuell!

### 💡 Detaillierte Beispiele

Hier siehst du, wie `packages` und `external_components` üblicherweise eingebunden werden, damit Insane Updater sie erkennt:

#### Beispiel 1: Einfaches Package von GitHub mit Versions-Tag
```yaml
api:
  homeassistant_services: true

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
api:
  homeassistant_services: true

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
api:
  homeassistant_services: true

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
