# Infraestructura del proyecto (estado: 11 jun 2026)

## kratos — workstation (la "torre")

- Acceso: `ssh stev@100.98.217.229` (tailnet, sin contraseña, BatchMode OK). Hostname `kratos`, CachyOS.
- Hardware: RTX 5070 Ti 16 GB (inferencia; 281,5 W bajo carga medidos, 63 W idle) + RTX 2060 6 GB (display) · Ryzen 9 9950X3D 16c/32t · 128 GB RAM · `/datos` 1,2 TB RAID.
- **ollama 0.24 activo en `http://100.98.217.229:11434`** (alcanzable directo por tailnet, sin túnel). API OpenAI-compatible en `/v1/chat/completions`.
- Modelos descargados: `qwen2.5:3b`, `qwen3:14b`, `gpt-oss:20b`, `qwen3:32b` (los 4 sujetos de los experimentos), además `qwen3-coder:30b`, `devstral:24b`, `qwen2.5-coder:7b`, `nomic-embed-text`.
- Rendimiento observado: hasta 24B Q4 caben en VRAM (interactivo); 32B hace offload a RAM (~35 min para 39 preguntas, hubo respuestas >80 s). No correr dos workflows contra ollama a la vez: el swap de modelos se sabotea.
- Python 3.14.5, `uv` y docker disponibles. NO se instaló nada en kratos: todo fue HTTP a ollama.

## Portátil (donde vive este repo)

- venv en `.venv/` (matplotlib, networkx, numpy, qrcode, pillow, markdown).
- RAPL existe (`/sys/class/powercap/intel-rapl-mmio`) pero no legible sin sudo → la energía del portátil quedó como estimación declarada (25 W); con sudo se puede medir de verdad.
- Servidor de la presentación: `python3 -m http.server 8123 --directory 03_Trabajos/Ponencia_Yuk_Hui/presentacion`. En la sesión original corrió con un watchdog en loop (relanza si el puerto queda libre) porque se cayó una vez.

## Vercel

- Proyecto `ponencia-yuk-hui`, scope/team `critertec-a963d21e`, cuenta `stevenvo780`.
- Deploy: `cd 03_Trabajos/Ponencia_Yuk_Hui/presentacion && vercel deploy --prod --yes --scope critertec-a963d21e`.
- La protección de despliegue se desactivó vía `PATCH https://api.vercel.com/v9/projects/ponencia-yuk-hui?slug=critertec-a963d21e` con `{"ssoProtection": null}` (token en `~/.local/share/com.vercel.cli/auth.json`). Si un redeploy reactiva 401, repetir.
- URL estable: https://ponencia-yuk-hui-critertec-a963d21e.vercel.app — el QR de la slide de cierre apunta a `/m/` de esa URL (si cambia el dominio, regenerar `assets/qr_movil.png`).

## GitHub

- Remote `origin = git@github.com:stevenvo780/FilosofiaCiudad.git`. `gh` autenticado como stevenvo780.
- **Cuidado**: `git fetch` de packs grandes se corta en esta red ("unexpected disconnect while reading sideband packet"). Workaround probado: `gh api repos/.../git/trees/<sha>?recursive=1` para listar y `gh api repos/.../git/blobs/<sha> --jq .content | base64 -d` para descargar archivos puntuales.
- Ramas remotas relevantes: `dataOrder` (de ahí salió el libro de Hui), `dev`, backups con prefijo `backup/`.

## Precios API de referencia (jun 2026, fuente oficial — NO usar memoria del modelo)

- Claude Opus 4.8: $5 entrada / $25 salida por MTok.
- Claude Sonnet 4.6: $3 / $15.
- (Un agente alucinó $15/$75 para Opus AUN TENIENDO estos valores en su prompt; el error llegó a deck y tesis y hubo que regenerar todo. Auditar siempre cifras contra fuente.)
