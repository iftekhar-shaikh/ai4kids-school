Set-Location C:\Users\iftekhar\ai4kids
$env:OPENAI_API_KEY = [System.Environment]::GetEnvironmentVariable("OPENAI_API_KEY","User")
if ([string]::IsNullOrEmpty($env:OPENAI_API_KEY)) {
    Write-Output "NO_KEY_FOUND"
} else {
    Write-Output ("KEY_LEN=" + $env:OPENAI_API_KEY.Length)
}
python -m streamlit run ai4kids_school.py --server.headless true --server.port 8501
