#!/usr/bin/env bash
set -euo pipefail
exam_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$exam_root"
export DOTNET_ROOT="$exam_root/.tools/dotnet11"
export PATH="$DOTNET_ROOT:$PATH"
export DOTNET_CLI_TELEMETRY_OPTOUT=1
export DOTNET_NOLOGO=1
mkdir -p .tools
exam_version="$(sed -nE 's/.*"version"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/p' global.json | head -n 1)"
[[ "$exam_version" == 11.* ]] || { echo 'Expected a pinned .NET 11 SDK.' >&2; exit 1; }
exam_ready=false
if [[ -x "$DOTNET_ROOT/dotnet" ]]; then
    exam_actual="$("$DOTNET_ROOT/dotnet" --version 2>&1)" || exam_actual=''
    [[ "$exam_actual" == "$exam_version" ]] && exam_ready=true
fi
if [[ "$exam_ready" == false ]]; then
    [[ ! -d "$DOTNET_ROOT/sdk/$exam_version" ]] || { echo 'The requested SDK exists but cannot run; preserve it and diagnose.' >&2; exit 1; }
    if command -v curl >/dev/null 2>&1; then
        curl --fail --location --silent --show-error https://dot.net/v1/dotnet-install.sh -o .tools/dotnet-install.sh
    else
        wget -q https://dot.net/v1/dotnet-install.sh -O .tools/dotnet-install.sh
    fi
    bash .tools/dotnet-install.sh --version "$exam_version" --install-dir "$DOTNET_ROOT" --no-path
fi
[[ "$("$DOTNET_ROOT/dotnet" --version)" == "$exam_version" ]] || { echo 'SDK resolution failed.' >&2; exit 1; }
"$DOTNET_ROOT/dotnet" --list-runtimes | grep -qE '^Microsoft.NETCore.App 11\.0\.' || { echo 'The local .NET 11 runtime is missing.' >&2; exit 1; }
echo 'PASS: .NET 11 SDK and runtime ready'
echo 'Open a new VS Code terminal, then build or press F5 from a question source file.'
