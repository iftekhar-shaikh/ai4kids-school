Set-Location C:\Users\iftekhar\ai4kids
$env:OPENAI_API_KEY = [System.Environment]::GetEnvironmentVariable("OPENAI_API_KEY","User")
python prewarm_tts.py
