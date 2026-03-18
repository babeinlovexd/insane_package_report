# Insane Updater

**Insane Updater** ist ein zweiteiliges Projekt, das dir in Home Assistant mitteilt, wenn es Updates für die in deinen ESPHome-Geräten verwendeten `packages` und `external_components` gibt. Das System greift während der Kompilierung eines ESPs die verwendeten GitHub-Repositories ab und übermittelt diese asynchron an Home Assistant. Dort wird eine dynamische Update-Entität für jedes Repository und Gerät erstellt.

---

## 🏗 Architektur

Das Projekt besteht aus zwei Hauptkomponenten:

1. **ESPHome Custom Component (`insane_package_report`)**
   Diese Komponente liest die rohe ESPHome-Konfiguration (`CORE.raw_config`) deines Geräts während der Kompilierung. Sie sucht nach `packages` und `external_components`, extrahiert deren GitHub-URLs und Refs (Tags/Branches) und brennt diese Informationen mit in die Firmware ein. Sobald der ESP mit Home Assistant verbunden ist (via Native API), feuert er die Liste seiner Repositories in Form von Home Assistant Custom Events (`esphome.insane_package_report`). Dabei wird ein asynchrones Delay zwischen jedem Event eingefügt, um zu verhindern, dass das 255-Zeichen-Limit für Events überschritten wird.

2. **Home Assistant Integration (`insane_updater`)**
   Die HA-Integration lauscht auf diese Custom Events. Wenn ein Event eintrifft, erkennt die Integration das meldende ESP-Gerät anhand seiner Device-ID in der Home Assistant Device Registry. Anschließend wird dynamisch (ohne Neustart!) eine Update-Entität (`UpdateEntity`) dem ESP-Gerät hinzugefügt. Ein `DataUpdateCoordinator` prüft einmal alle 24 Stunden per GitHub API auf neue Versionen:
   - Ist ein `ref` (z.B. Tag) konfiguriert, wird die `/tags` API geprüft, um neuere Tags zu finden.
   - Ist kein `ref` konfiguriert, wird der Commit-Hash des `default_branch` überprüft.
   Die installierten Versionen werden über den HA Storage Helper persistiert, sodass die Update-Entitäten auch nach einem Neustart von Home Assistant sofort wieder ihre korrekten Stati anzeigen.

---

## 📥 Installation

### 1. Home Assistant Integration installieren (`insane_updater`)

1. Kopiere den Ordner `insane_updater` in dein Verzeichnis `config/custom_components/` in Home Assistant.
2. Starte Home Assistant neu.
3. Gehe in Home Assistant zu **Einstellungen -> Geräte & Dienste -> Integration hinzufügen**.
4. Suche nach **Insane Updater** und füge die Integration hinzu.
5. *(Optional aber empfohlen)*: Trage im Config Flow einen **GitHub Personal Access Token** (Classic Token reicht, mit `public_repo` Rechten) ein. Dies schützt dich davor, in die GitHub API Rate Limits zu laufen.

### 2. ESPHome Component installieren (`insane_package_report`)

Kopiere den Ordner `insane_package_report` in dein ESPHome `custom_components` Verzeichnis (z. B. `config/esphome/custom_components/`).

---

## ⚙️ Konfiguration (ESPHome)

Damit dein ESPHome-Gerät seine genutzten Packages melden kann, musst du die Komponente in der YAML des jeweiligen Geräts aktivieren.

Füge folgenden Block zu deiner ESPHome-Konfiguration hinzu:

```yaml
# Aktiviert den Insane Package Report
insane_package_report:

# Beispiel für Packages und External Components in deiner YAML:
packages:
  # Dieses Repo wird von Insane Updater erkannt
  mein_paket:
    github: mein_github_user/mein_cooles_repo
    ref: v1.0.0

external_components:
  # Dieses Repo wird ebenfalls erkannt
  - source:
      type: git
      url: https://github.com/pr#1234
      ref: fix-irgendwas
```

**Was passiert nun?**
1. Beim Klicken auf "Install" / "Compile" parst die `insane_package_report`-Komponente die obige Konfiguration.
2. Sie merkt sich die Repositories `mein_github_user/mein_cooles_repo` (Tag `v1.0.0`) und das Pull-Request-Repo (`fix-irgendwas`).
3. Nach dem Start des ESP-Geräts meldet es sich per API bei Home Assistant.
4. Nach einem kurzen Delay feuert das Gerät Events an Home Assistant ab.
5. Home Assistant fängt diese Events ab und erstellt unter dem ESP-Gerät zwei neue Update-Entitäten ("mein_cooles_repo Update" und "pr#1234 Update").
6. Zeigt das Repo auf GitHub einen neueren Release oder Tag, meldet die Update-Entität ein verfügbares Update!

---

## 🛠 Fehlerbehebung

- **Es tauchen keine Entitäten in HA auf?**
  Prüfe, ob du die ESPHome-Komponente per `insane_package_report:` wirklich aktiviert hast und die Firmware erfolgreich auf den ESP geflasht wurde.
- **GitHub Rate Limit Error?**
  Dies passiert, wenn HA zu oft die GitHub API ohne Token abfragt. Füge der HA-Integration einen Token hinzu, indem du die Integration über die UI konfigurierst oder löschst und neu hinzufügst.
- **Wann werden die Sensoren erstellt?**
  Die Sensoren werden beim Start des ESPs an HA übertragen. Wird der ESP frisch gebootet (z.B. vom Strom getrennt und wieder eingesteckt), sendet er wenige Sekunden nach der Verbindung die Report-Events an Home Assistant.
