# FOA-SDK Windows installer launcher

`Installer/Launcher/Windows/` owns the user-facing Windows entrypoint for the installer flow.

It builds `FOA-SDK-Installer.exe`, a thin launcher that starts the existing graphical Suite Wizard receipt host:

```text
FOA-SDK-Installer.exe
  → Installer/SuiteWizard/Host/Source/suite_wizard_receipt_host.py
  → Suite Wizard review, acknowledgement, confirmation, and receipt export
```

## Boundary

The launcher does not resolve packages, copy payloads, launch game/runtime processes, request elevation, coordinate lifecycle execution, publish installation state, mutate products, mutate saves, sign artifacts, publish to the network, mutate catalogues, or promote evidence.

It only provides a user-facing executable entrypoint into the already-reviewed graphical wizard. Any later installer execution still has to pass through the capability-gated PackageEngine, admission, handoff, lifecycle, publication, registry, and editor-readiness chain.

## Build

From PowerShell on Windows with the .NET SDK installed:

```powershell
Installer/Launcher/Windows/build-foa-installer-launcher.ps1 \
  -Configuration Release \
  -RuntimeIdentifier win-x64
```

The expected output is:

```text
Installer/Launcher/Windows/artifacts/FOA-SDK-Installer.exe
```

For a self-contained binary:

```powershell
Installer/Launcher/Windows/build-foa-installer-launcher.ps1 \
  -Configuration Release \
  -RuntimeIdentifier win-x64 \
  -SelfContained
```

## Run

From the product checkout:

```powershell
Installer/Launcher/Windows/artifacts/FOA-SDK-Installer.exe
```

Or provide explicit paths:

```powershell
FOA-SDK-Installer.exe \
  --installer-root C:\path\to\FOA-SDK\Installer \
  --python C:\path\to\pythonw.exe
```

The launcher also checks `FOA_SDK_PYTHON` and bundled runtime locations under `runtime/python/pythonw.exe`.

## Smoke test

The CI-friendly smoke mode waits for the underlying host to run its native graphical smoke path and returns the host exit code:

```powershell
FOA-SDK-Installer.exe --installer-root C:\path\to\FOA-SDK\Installer --smoke-test
```

Smoke mode is explicit; normal double-click use opens the graphical wizard instead of running an automatic flow.
