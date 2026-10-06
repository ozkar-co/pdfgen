---
title: pdfgen — OzNet / tunnel
date: 2026-10-06
tags: [pdfgen, oznet, cloudflare]
status: active
---

# pdfgen — OzNet / tunnel

Fuente de verdad de rutas: `OzNet/infrastructure/cloudflare/tunnel-config.yml`.

Con el servicio corriendo en kansas `:3009`:

```bash
cd ~/Code/OzNet/infrastructure/cloudflare
./add-site.sh pdfgen 3009
# → pdfgen.ozkr.net → http://localhost:3009
```

Equivalente en YAML:

```yaml
  - hostname: pdfgen.ozkr.net
    service: http://localhost:3009
```
