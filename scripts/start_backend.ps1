Set-Location $PSScriptRoot\..
if (!(Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
  Write-Host "已生成 .env，请先填写 OPENAI_API_KEY、MySQL、邮箱等配置后再启动。" -ForegroundColor Yellow
  exit 1
}
python -m pip install -r requirement.txt
python main.py
