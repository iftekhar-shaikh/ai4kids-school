# AI4Kids backup refresher — copies current system files to Desktop backup folder + zip
$d = "C:\Users\iftekhar\Desktop\AI4Kids_Backup_Latest"
if (Test-Path $d) { Remove-Item $d -Recurse -Force }
New-Item -ItemType Directory -Path $d | Out-Null
$files = @(
  "C:\Users\iftekhar\ai4kids\lesson_bank.html",
  "C:\Users\iftekhar\ai4kids\ai4kids_school.py",
  "C:\Users\iftekhar\ai4kids\students.json",
  "C:\Users\iftekhar\Desktop\AI4Kids_Workflow_Map.html",
  "C:\Users\iftekhar\ai4kids\HANDOFF.md"
)
foreach ($f in $files) {
  if (Test-Path $f) {
    [IO.File]::WriteAllBytes("$d\$([IO.Path]::GetFileName($f))", [IO.File]::ReadAllBytes($f))
  }
}
$zip = "$d\AI4Kids_all_in_one.zip"
Compress-Archive -Path "$d\*" -DestinationPath $zip -Force
$stamp = Get-Date -Format "yyyy-MM-dd HH:mm"
Set-Content -Path "$d\LAST_REFRESHED.txt" -Value "Backup refreshed: $stamp`nAb isse Google Drive ke 'AI4Kids Backups' folder mein drag karein."
Write-Output "Backup refreshed at $stamp -> $d"
