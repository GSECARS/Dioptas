!ifndef VERSION
  !error "VERSION must be passed on the command line: makensis /DVERSION=X.Y.Z Dioptas_installer.nsi"
!endif

Name "Dioptas ${VERSION}"
OutFile "dist\Dioptas_Win64_${VERSION}_installer.exe"
InstallDir "$PROGRAMFILES64\Dioptas"
InstallDirRegKey HKLM "Software\Dioptas" "Install_Dir"
RequestExecutionLevel admin
Icon "dioptas\resources\icons\icon.ico"

Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Section "Dioptas"
  SetOutPath "$INSTDIR"
  File /r "dist\Dioptas_Win64_${VERSION}\*.*"

  WriteRegStr HKLM "Software\Dioptas" "Install_Dir" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Dioptas" "DisplayName" "Dioptas ${VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Dioptas" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Dioptas" "DisplayIcon" "$INSTDIR\Dioptas.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Dioptas" "Publisher" "GSECARS, University of Chicago"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Dioptas" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Dioptas" "NoRepair" 1
  WriteUninstaller "uninstall.exe"
SectionEnd

Section "Start Menu Shortcuts"
  CreateDirectory "$SMPROGRAMS\Dioptas"
  CreateShortcut "$SMPROGRAMS\Dioptas\Dioptas.lnk" "$INSTDIR\Dioptas.exe"
  CreateShortcut "$SMPROGRAMS\Dioptas\Uninstall Dioptas.lnk" "$INSTDIR\uninstall.exe"
SectionEnd

Section "Desktop Shortcut"
  CreateShortcut "$DESKTOP\Dioptas.lnk" "$INSTDIR\Dioptas.exe"
SectionEnd

Section "Uninstall"
  RMDir /r "$INSTDIR"
  Delete "$SMPROGRAMS\Dioptas\Dioptas.lnk"
  Delete "$SMPROGRAMS\Dioptas\Uninstall Dioptas.lnk"
  RMDir "$SMPROGRAMS\Dioptas"
  Delete "$DESKTOP\Dioptas.lnk"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Dioptas"
  DeleteRegKey HKLM "Software\Dioptas"
SectionEnd
