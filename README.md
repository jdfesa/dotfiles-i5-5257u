# dotfiles-i5-5257u

Configuration for **MacBookPro12,1** running Debian 13 amd64 with Sway/Wayland.
Prioritizes stability, straightforward maintenance and restoration from a local clone.

**Hardware:** Intel Core i5-5257U · Iris 6100 · 8 GB RAM · 2560×1600 display.

## Layout

```text
config/    Component configuration and symlink manifests
scripts/   Session, status bar and menu helpers
tools/     Deployment, validation and maintenance
tests/     Regression and restoration tests
docs/      Installation, operation and recovery
licenses/  Third-party component licenses
```

The laptop checkout resides at `/home/jd/dotfiles-i5-5257u`.
User configuration files are symlinked to their sources in this directory.

## Documentation

- **Getting started:** [Restore guide](docs/restore-guide.md),
  [Hardware](docs/initial-state.md) and [Dependencies](docs/dependencies.md).
- **Environment:** [Sway setup](docs/sway-setup.md), [Keybindings](docs/keybindings.md),
  [Status bar](docs/status-bar.md) and [Daily use](docs/daily-use.md).
- **Applications:** [Applications index](docs/applications.md),
  [Helium](docs/helium-setup.md) and [Zed](docs/zed-setup.md).
- **Maintenance:** [Deployment](docs/deployment.md),
  [Scripts and files](docs/scripts-and-files.md), [CHANGELOG.md](CHANGELOG.md)
  and [TODO.md](TODO.md).

## License

Original code and documentation are licensed under MIT ([LICENSE](LICENSE)).
[Third-party notices](docs/third-party-notices.md).
