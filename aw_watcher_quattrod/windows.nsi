OutFile "aw-watcher-quattrod-installer.exe"
InstallDir "$LOCALAPPDATA\aw-watcher-quattrod"

RequestExecutionLevel user

Page directory
Page instfiles

Section "Install"
    SetOutPath $INSTDIR

    File "target\x86_64-pc-windows-msvc\release\aw-watcher-quattrod-installer.exe"

    EnVar::AddValue "PATH" "$INSTDIR"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\aw-watcher-quattrod.exe"

    RMDir "$INSTDIR"

    EnVar::DeleteValue "PATH" "$INSTDIR"
SectionEnd