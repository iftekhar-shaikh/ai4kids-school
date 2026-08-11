# =====================================================================
#  AI4Kids.pk - School launcher
#  Purani Streamlit band karta hai, key load karta hai, phir school kholta hai.
#  NOTE: is file mein sirf ASCII characters rakhein. PowerShell 5.1 .ps1 ko
#  ANSI samajhta hai, is liye em-dash / Urdu script parse error deta hai.
# =====================================================================
Set-Location C:\Users\iftekhar\ai4kids

# ---- 1. Purani Streamlit instance band karo -------------------------
# SIRF is app ki streamlit process. Claude / windows-mcp ko haath NAHI lagata.
$old = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object {
        $_.CommandLine -and
        $_.CommandLine -like '*streamlit*' -and
        $_.CommandLine -like '*ai4kids_school.py*' -and
        $_.CommandLine -notlike '*windows-mcp*' -and
        $_.CommandLine -notlike '*Claude*'
    }

if ($old) {
    foreach ($p in $old) {
        Write-Host ("  Purani school band ki ja rahi hai (PID {0})..." -f $p.ProcessId) -ForegroundColor Yellow
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
} else {
    Write-Host "  Koi purani instance nahi mili." -ForegroundColor DarkGray
}

# ---- 2. API key load karo -------------------------------------------
$env:OPENAI_API_KEY = [System.Environment]::GetEnvironmentVariable("OPENAI_API_KEY","User")
if ([string]::IsNullOrEmpty($env:OPENAI_API_KEY)) {
    Write-Host "  ! OPENAI_API_KEY nahi mili (ai_config.json mein key ho to theek hai)." -ForegroundColor Yellow
}

# ---- 3. Port 8501 khali hai? ----------------------------------------
$busy = Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue
if ($busy) {
    Write-Host ("  ! Port 8501 abhi bhi busy hai (PID {0})." -f $busy.OwningProcess) -ForegroundColor Yellow
    Write-Host "    Agar school na khule to woh process band karein." -ForegroundColor Yellow
}

# ---- 4. Browser tab: server tayyar hone ka intezar karo --------------
# (Pehle browser turant khulta tha aur 'can't connect' aata tha.)
Start-Job -Name OpenSchool -ScriptBlock {
    for ($i = 0; $i -lt 40; $i++) {
        Start-Sleep -Milliseconds 500
        if (Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue) {
            Start-Process "http://localhost:8501"
            break
        }
    }
} | Out-Null

# ---- 5. School chalao -----------------------------------------------
Write-Host ""
Write-Host "  AI4Kids.pk - school khul raha hai..." -ForegroundColor Green
Write-Host "  Band karne ke liye is window mein Ctrl+C dabayein." -ForegroundColor DarkGray
Write-Host ""
python -m streamlit run ai4kids_school.py
