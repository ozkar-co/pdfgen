# pdfgen

Markdown o HTML → PDF, con plantillas de membrete (márgenes y
marca de agua). FastAPI + UI mínima. Puerto **`:3009`**.

Familia de herramientas no-IA (`30xx`). Spec:
[`docs/diseno.md`](docs/diseno.md). Túnel: [`docs/oznet.md`](docs/oznet.md).

## Deploy (Debian)

```bash
sudo apt install -y python3-venv fonts-dejavu libpango-1.0-0 libpangoft2-1.0-0 \
  nodejs npm libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
  libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2

cd ~/Code
git clone git@github.com:ozkar-co/pdfgen.git
cd pdfgen
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
npm install -g @mermaid-js/mermaid-cli   # mmdc + Chromium (puppeteer)
./run.sh                    # prueba: 0.0.0.0:3009, Ctrl+C para salir
```

Mermaid usa `mmdc` (Node + Chromium headless) para renderizar los
bloques ```` ```mermaid ```` a SVG. Si `mmdc` no está en el `PATH`
del servicio, fija la ruta en `config.yaml` (`mermaid_cmd`) o vía
`MERMAID_CMD`. Sin Mermaid en el documento, `mmdc` no se invoca.

Servicio (`/etc/systemd/system/pdfgen.service`):

```ini
[Unit]
Description=pdfgen - Markdown/HTML a PDF
After=network.target

[Service]
User=oz
WorkingDirectory=/home/oz/Code/pdfgen
ExecStart=/home/oz/Code/pdfgen/run.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now pdfgen
.venv/bin/python scripts/smoke_test.py   # health + un PDF por plantilla
```

Túnel:

```bash
cd ~/Code/OzNet/infrastructure/cloudflare
./add-site.sh pdfgen 3009   # → https://pdfgen.ozkr.net
```

Actualizar: `git pull && sudo systemctl restart pdfgen`.

## Uso

UI: `https://pdfgen.ozkr.net/`

```bash
curl -s https://pdfgen.ozkr.net/api/templates
curl -s -X POST https://pdfgen.ozkr.net/api/pdf \
  -H 'Content-Type: application/json' \
  -d '{"content":"# Hola\n\nTexto.","format":"md","template":"forja"}' \
  -o hola.pdf
```
