<p align="center">
  <a href="https://github.com/babeinlovexd"><img src="https://raw.githubusercontent.com/babeinlovexd/babeinlovexd/main/bxd-github-header.svg" width="520" alt="BxD / BabeinlovexD"></a>
</p>

# Insane Updater

[English](README.md) · [Fragen & Fehler](https://github.com/babeinlovexd/insane_package_report/issues) · [Releases](https://github.com/babeinlovexd/insane_package_report/releases)

**Insane Updater** meldet die von einem ESPHome-Gerät verwendeten GitHub-Pakete und externen Komponenten und zeigt Updateinformationen in Home Assistant an. Das Projekt besteht aus der ESPHome-Komponente `insane_package_report` und der Home-Assistant-Integration `insane_updater`.

## Funktionsweise

1. Beim Kompilieren liest die ESPHome-Komponente Repository-Adressen, Refs und Pakettypen aus der Rohkonfiguration.
2. Nach der Verbindung zu Home Assistant sendet das Gerät `esphome.insane_package_report`-Events.
3. Die Integration ordnet die Repositories dem Gerät zu und erstellt Update-Entitäten. Ein Coordinator fragt GitHub regelmäßig ab.

**Updates werden angezeigt, nicht installiert.** Die Integration besitzt keine Installationsaktion. Zum Aktualisieren passt du bei Bedarf deine ESPHome-Konfiguration an, kompilierst und flashst das Gerät selbst.

## Installation

### Home Assistant

1. `https://github.com/babeinlovexd/insane_package_report` in HACS als benutzerdefiniertes Repository der Kategorie **Integration** hinzufügen und Insane Updater herunterladen.
2. Alternativ [custom_components/insane_updater](custom_components/insane_updater) nach `config/custom_components/` in Home Assistant kopieren.
3. Home Assistant neu starten und **Insane Updater** unter Einstellungen → Geräte & Dienste hinzufügen.
4. Ein Prüfintervall von 1, 3, 6, 12 oder 24 Stunden wählen. Ein GitHub-Token ist optional und wird gegebenenfalls für API-Anfragen genutzt. Tokens gehören nicht in Issues oder Repository-Dateien.

### ESPHome

Diese Einträge mit der bestehenden Gerätekonfiguration zusammenführen. Vorhandene `api.encryption`-Angaben im selben `api`-Block beibehalten:

```yaml
api:
  homeassistant_services: true

external_components:
  - source:
      type: git
      url: https://github.com/babeinlovexd/insane_package_report
      ref: main
    components: [insane_package_report]
    refresh: 1d

insane_package_report:
```

Das Gerät kompilieren, flashen und über die Native API verbinden. Falls erforderlich, in den Geräteeinstellungen der ESPHome-Integration in Home Assistant das Ausführen von Aktionen/Events erlauben.

## Versionserkennung

- Gemeldet werden **URL, Ref und Typ**. Der exakte Git-Commit jeder Abhängigkeit wird nicht in die Firmware eingebettet.
- Für `main`, `master`, `dev`, `develop` oder einen leeren Ref werden Branch-Commits abgefragt. Bei anderen Refs wird zunächst der erste von GitHub gelieferte Tag verwendet; nur ohne Tags folgt ein Commit-Fallback. Eigene Branch-Namen werden deshalb nicht wie die genannten Standard-Branches behandelt.
- Die installierte Vergleichsversion wird in Home Assistant gespeichert und anhand von Geräte-Softwareversion und GitHub-Antworten fortgeschrieben. Diese Anzeige beweist nicht, welcher Abhängigkeits-Commit tatsächlich auf dem ESP installiert ist.
- Prüfungen erfolgen im gewählten Intervall, nicht zwingend unmittelbar nach einem Upstream-Commit. Die GitHub-Tagreihenfolge wird nicht als semantische Versionsnummer ausgewertet.

## Konfigurationsbeispiel

`components` steht neben `source`, nicht darin. Verwende eine echte URL nach dem Muster `https://github.com/owner/repository`. Beispielsweise kannst du diesen zweiten Eintrag zur bestehenden Liste `external_components` hinzufügen:

```yaml
  - source:
      type: git
      url: https://github.com/babeinlovexd/ESPHOME-WS2805
      ref: main
    components: [ws2805]
```

`insane_package_report:` bleibt auf der obersten Ebene aktiviert. Das Melden eines Repositories ersetzt nicht dessen eigene Hardwarekonfiguration.

## Fehlersuche

- **Keine Entitäten:** Obersten `insane_package_report:`-Eintrag, Native API, Eventberechtigung in Home Assistant und Firmware-Logs prüfen. Ein Neustart des ESP sendet die Meldungen erneut.
- **API-Limit erreicht:** Prüfintervall erhöhen oder einen API-Token konfigurieren. Den konkreten Fehler im Home-Assistant-Log prüfen.
- **Unerwartete Version:** Den Ref und das oben beschriebene Erkennungsverhalten prüfen. Ein erneutes Flashen wird nicht unabhängig gegen sämtliche Abhängigkeits-SHAs verifiziert.
- **Integrationsoptionen ändern:** Die verfügbare Konfigurationsoberfläche nutzen; die Integration nicht allein zur Fehlersuche löschen.

## Entwicklung

ESPHome-Code: [components/insane_package_report](components/insane_package_report). Home-Assistant-Code: [custom_components/insane_updater](custom_components/insane_updater). Vorhandene Tests: [tests](tests).

---

## Builds und Releases

Version: **1.3.1** ([VERSION](VERSION)). [GitHub Actions](.github/workflows/release.yml) prüft Pushes und Pull Requests. Ein Tag passend zu `v` + `VERSION` veröffentlicht das Release erst nach erfolgreichen Jobs; manuelle Läufe liefern Build-Artefakte. [Downloads](https://github.com/babeinlovexd/insane_package_report/releases).

ESPHome-CI verwendet Platzhalter-Zugangsdaten und flasht keine Geräte. Vor dem Einsatz eigene Secrets und Pinbelegung prüfen.

## Mitmachen

Fragen, Fehlerberichte und Beiträge sind willkommen. Nenne Version, Aufbau und Schritte zum Nachstellen im [Issue](https://github.com/babeinlovexd/insane_package_report/issues). Größere Änderungen besprechen wir am besten vor einem Pull Request.

[BxD / BabeinlovexD](https://github.com/babeinlovexd) · [Website](https://babeinlovexd.de/)
