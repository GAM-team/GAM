# Steps to release a new GAM version
1. In a final commit before release:
    - [src/gam/__init.py](https://github.com/GAM-team/GAM/blob/main/src/gam/__init__.py) `__version___` value should be updated to the new version.
    - [src/GamUpdate.txt](https://github.com/GAM-team/GAM/blob/main/src/GamUpdate.txt) should be updated with a high-level changelog.
    - [wiki/GamUpdates.md](https://github.com/GAM-team/GAM/blob/main/wiki/GamUpdates.md) should be updated with same high-level changelog.
    - [wiki/Version-and-Help.md](https://github.com/GAM-team/GAM/blob/main/wiki/Version-and-Help.md) should be updated with current version N.NN.NN
    - [wiki/How-to-Upgrade-Legacy-GAM-to-GAM7.md](https://github.com/GAM-team/GAM/blob/main/wiki/How-to-Upgrade-Legacy-GAM-to-GAM7.md) should be updated with current version N.NN.NN
2. The [build.yaml](https://github.com/GAM-team/GAM/blob/main/.github/workflows/build.yml) Github Action for final commit should complete successfully and creating a new dated Draft release.
    - We should *NEVER* upload release files manually. Only release files automatically created and [attested](https://github.com/GAM-team/GAM/wiki/Verifying-a-GAM7-Build-is-Legitimate-and-Official#github-attestation-linuxmacoswindows) as created by the Github Action should be used.
3. Edit the Draft release:
    - Create a new tag with the format: `vN.NN.NN` where N.NN.NN is the GAM release version.
    - name the release "GAM N.NN.NN" where N.NN.NN is the GAM release version.
    - Include the changelog details for the new version in details.
    - leave "Set as pre-release" unchecked and "Set as the latest release" checked.
    - Publish the release.

# TODO: Release Process Improvements
- copying changelog between GamUpdate.txt, GamUpdates.md and release description is manual and tedious. Automate it.
- copying version string from gam/__init__.py, changelogs and release details and tag in manual and tedious. Automate it.
- See if we can block releases with binaries not uploaded by GitHub Actions to further secure release pipelines.

