$conns = Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue
foreach ($c in $conns) {
    Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 2
Set-Location C:\Users\iftekhar\ai4kids
$env:OPENAI_API_KEY = [System.Environment]::GetEnvironmentVariable("OPENAI_API_KEY","User")
python -m streamlit run ai4kids_school.py --server.headless true --server.port 8501
