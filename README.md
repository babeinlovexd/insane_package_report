<p align="center">
  <a href="https://github.com/babeinlovexd"><img src="https://raw.githubusercontent.com/babeinlovexd/babeinlovexd/main/bxd-github-header.svg" width="520" alt="BxD / BabeinlovexD"></a>
</p>

# Insane Updater

[Deutsch](README_DE.md) · [Issues](https://github.com/babeinlovexd/insane_package_report/issues) · [Releases](https://github.com/babeinlovexd/insane_package_report/releases)

**Insane Updater** reports which GitHub packages and external components an ESPHome device uses and displays update information in Home Assistant. It consists of the ESPHome component `insane_package_report` and the Home Assistant integration `insane_updater`.

## How it works

1. During compilation, the ESPHome component reads repository URLs, refs and package types from the raw configuration.
2. After connecting to Home Assistant, the device sends `esphome.insane_package_report` events.
3. The integration associates repositories with the reporting device and creates update entities. A coordinator checks GitHub periodically.

**Updates are reported, not installed.** The integration has no install action. To update a component, adjust your ESPHome configuration when needed, rebuild and flash the device yourself.

## Installation

### Home Assistant

1. Add `https://github.com/babeinlovexd/insane_package_report` as a custom **Integration** repository in HACS and download Insane Updater.
2. Alternatively, copy [custom_components/insane_updater](custom_components/insane_updater) into Home Assistant's `config/custom_components/` directory.
3. Restart Home Assistant, then add **Insane Updater** under Settings → Devices & services.
4. Choose an update interval of 1, 3, 6, 12 or 24 hours. A GitHub token is optional; the code uses it for API requests if configured. Do not paste tokens into issues or repository files.

### ESPHome

Merge the following into each device's existing configuration. Keep any existing `api.encryption` settings in the same `api` block:

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

Compile and flash the device, connect it through ESPHome's native API, and allow it to perform Home Assistant actions/events in the integration's device settings when required.

## Version detection

- The component reports **URL, ref and type**. It does not embed the exact Git commit of every dependency.
- For `main`, `master`, `dev`, `develop` or no ref, the integration checks branch commits. For other refs it first uses the first tag returned by GitHub, then falls back to a ref commit if no tags exist. Custom branch names therefore do not have the same handling as those common branch names.
- The installed-version baseline is stored in Home Assistant and updated using the device software version and GitHub responses. A displayed baseline is not proof of the exact dependency commit flashed to the ESP.
- Checks occur at the configured interval; a new upstream commit is not necessarily reported immediately. GitHub tag order is not a semantic-version comparison.

## Configuration examples

The `components` list belongs alongside `source`, not inside it. Use a real `https://github.com/owner/repository` URL. For example, add this second entry to the existing `external_components` list:

```yaml
  - source:
      type: git
      url: https://github.com/babeinlovexd/ESPHOME-WS2805
      ref: main
    components: [ws2805]
```

The reporting component must remain enabled at the root level. Reporting a repository does not add that component's hardware configuration.

## Troubleshooting

- **No entities:** Check the root `insane_package_report:` entry, native API connection, Home Assistant event permission and firmware logs; restart the ESP to resend reports.
- **Rate limiting:** Increase the check interval or configure an API token. Inspect Home Assistant logs for the actual error.
- **Unexpected version:** Check the configured ref and the detection behavior above; re-flashing is not independently verified against all upstream dependency SHAs.
- **Changing integration options:** Use the available configuration UI; avoid deleting your integration merely to troubleshoot an API error.

## Development

ESPHome source is in [components/insane_package_report](components/insane_package_report); Home Assistant source is in [custom_components/insane_updater](custom_components/insane_updater). Tests are in [tests](tests).

---

## Builds and releases

Version: **1.3.1** ([VERSION](VERSION)). [GitHub Actions](.github/workflows/release.yml) checks each push and pull request. A tag matching `v` + `VERSION` publishes a release after all jobs succeed; manual runs provide build artifacts. [Downloads](https://github.com/babeinlovexd/insane_package_report/releases).

ESPHome CI uses dummy credentials and does not flash devices. Configure your own secrets and pin assignments before deployment.

## Contributing

Questions, bug reports and contributions are welcome. Include version, setup and reproduction steps in an [Issue](https://github.com/babeinlovexd/insane_package_report/issues). Please discuss larger changes before a pull request.

[BxD / BabeinlovexD](https://github.com/babeinlovexd) · [Website](https://babeinlovexd.de/)
