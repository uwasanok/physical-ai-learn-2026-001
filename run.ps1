param([ValidateSet('start','demo','stop','status')][string]$Action='start')
$ErrorActionPreference='Stop'
Push-Location $PSScriptRoot
try {
    switch($Action) {
        'start' { docker compose up -d --build; if($LASTEXITCODE -ne 0){throw 'Docker startup failed'}; docker compose exec -T sim python3 -m notebook list }
        'demo' { docker compose exec -T sim bash -lc 'source /opt/ros/jazzy/setup.bash && python3 scripts/run_demo.py'; if($LASTEXITCODE -ne 0){throw 'Demo failed; check logs'} }
        'stop' { docker compose down }
        'status' { docker compose ps; docker compose exec -T sim python3 -m notebook list }
    }
} finally { Pop-Location }
