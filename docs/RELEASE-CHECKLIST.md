# Ubuntu Glove Release Checklist

Do not publish or sell the application until every applicable item is complete.

- [ ] Owner has selected the final product name, logo/icon, support address, source repository, and license/copyright owner.
- [ ] Placeholder maintainer and homepage values in `debian/control` and `debian/changelog` are replaced with real values.
- [ ] `python3 -m unittest discover -s tests -v` passes in a clean Ubuntu 26.04 environment.
- [ ] `docs/UBUNTU-GNOME-ACCEPTANCE-TEST.md` passes on the actual supported desktop profile.
- [ ] Installer upgrade has been tested with a real existing notes database; no data is removed.
- [ ] A `.deb` has been built from a clean checkout and installed/uninstalled on a test machine.
- [ ] The release archive, package, checksum manifest, SBOM, and third-party notices are generated from the same commit.
- [ ] `data/models.lock.json` is either intentionally empty or contains exact reviewed model revisions and SHA-256 values. Never ship invented hashes.
- [ ] Screen reading is tested with normal windows, a protected password field, AT-SPI disabled, portal denial, and model-gateway failure.
- [ ] No unsupported remote endpoint can be configured from settings or the CLI.
- [ ] User documentation accurately says that voice/presence capabilities are absent, or the separate module has passed its own release gates.
- [ ] A backup/export path for context notes and settings is documented and tested.
