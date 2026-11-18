---
tipo: "contexto"
cerebro: "Contenido y video"
generado: "tools/generar.py · no editar a mano: se reescribe cada día"
---

# Contexto para cualquier IA · Contenido y video

Soy Emi (Yohualli Emiliano García Milla). Este es el cerebro «Contenido y video» de mi Matriz General (https://github.com/lianfixx/MATRIZ · https://matriz.milla-abogados.workers.dev). Creación de videos y contenido: Vox Studio, Pizarra Studio, MILLA Video Studio, X, Instagram, TikTok, LinkedIn, la matriz de redes (REDES) e historias de Instagram.

## Cómo trabajar

1. La fuente de verdad es GitHub (`lianfixx`), no esta conversación ni lo que recuerdes.
2. Antes de cambiar un repositorio, lee su `AGENTS.md`, `ia/REGLAS.md` e `ia/PROTOCOLO.md`.
3. Todo cambio se registra en el mismo commit, en `CHANGELOG.md`, con la línea `Agente:`.
4. Si no puedes escribir en el repositorio, termina con un bloque «Registro pendiente para el repositorio» con la entrada completa y los cambios exactos. No digas «guardado» si no escribiste.
5. No envíes correos, no publiques, no contrates ni cambies reglas sin confirmación expresa de Emi.
6. Nada de datos de clientes (nombres, expedientes, montos) en repositorios públicos ni en la Matriz.

## Repositorios de este cerebro

### VIDEOS-IA-SKILL-MILLA (público)

https://github.com/lianfixx/VIDEOS-IA-SKILL-MILLA · último cambio: 13 nov 2026

Un método portable para producir videos de MILLA ABOGADOS: investigación, guion, conexiones, voz, imágenes, música, montaje y revisión. Incluye una skill, instrucciones para otras IAs, utilidades y un compositor nuevo.

Skills: `editor-studio`, `milla-video-studio`, `pizarra-studio`, `vox-studio`

Último registro: 13 nov 2026 · Vox Studio 0.13.1: ideas de temas desde la skill de LinkedIn · Agente: Claude Code (sesión en la nube)
Pendiente: avisar a `linkedin-pro` con fecha y commit; fusionar a `main`.

### X (público)

https://github.com/lianfixx/X · último cambio: 18 nov 2026

Skill para planear, redactar, revisar, publicar con aprobación (API oficial de X) y medir las publicaciones de @emilianomilla en X, apoyada en el código público del algoritmo de X (xai-org/x-algorithm).

Skills: `x-viral`

Último registro: 18 nov 2026 · Premium en prueba y texto largo sobre The Economist · Agente: Claude Code (sesión en la nube)
Pendiente: que Emi reescriba y apruebe, y cancele las tres opciones cortas; revisar hacia el 25/11 si conserva Premium y, si no, volver a `false`.

### HISTORIAS- (público)

https://github.com/lianfixx/HISTORIAS- · último cambio: 16 nov 2026

Método, motor y memoria para hacer las historias de Instagram de Emi con cualquier IA: la IA pregunta, propone y dibuja; Emi decide.

Skills: `historias-studio`

Último registro: 16 nov 2026 · 0.3.1 · candidato · Agente: no consta

### REDES (público)

https://github.com/lianfixx/REDES · último cambio: 18 nov 2026

La capa de decisión por encima de las skills de cada red (X, LinkedIn, TikTok, Instagram) y de video (Vox Studio, Pizarra Studio, Editor Studio, MILLA Video Studio, Historias Studio). Registra las ideas, decide en qué red y formato sale cada una, arma el calendario de todas…

Skills: `matriz-redes`

Último registro: 18 nov 2026 · Claude puede retirar sus propios borradores sin aprobar · Agente: Claude Code (sesión en la nube)
Pendiente: nada.

### Instagram (público)

https://github.com/lianfixx/Instagram · último cambio: 13 nov 2026

Skill para planear, redactar, revisar, entregar para publicar y medir los Reels, publicaciones del feed y carruseles de la cuenta personal de Emi en Instagram. Pilares: IA + Derecho en México, estilo de vida y gym y opinión política. Sirve en cualquier IA.

Skills: `instagram-studio`

Último registro: 13 nov 2026 · instagram-studio 1.0.1: correcciones de la auditoría independiente · Agente: Claude Code (sesión en la nube)
Pendiente: - Avisar a Emi y a Matriz de Redes que el Reel de Vox necesita la voz de Emi o la etiqueta.

### TikTok (público)

https://github.com/lianfixx/TikTok · último cambio: 18 nov 2026

Skill de la cuenta personal de Emi en TikTok: decide qué video hacer, para quién y cómo engancha en los primeros segundos; prepara la descripción, los hashtags, la portada y el calendario; entrega el paquete aprobado para que Emi lo publique, y mide.

Skills: `tiktok-studio`

Último registro: 17 nov 2026 · Auditoría independiente y correcciones (1.2.0) · Agente: Claude Code (sesión en la nube); revisor: otro agente de Claude Code, independiente y de solo lectura.
Pendiente: que Emi decida si la revisión mensual puede sellar la fecha y hacer commits sola; aprobación de la descripción del DOF; `archivo_sha256` del MP4 antes de entregarlo.

### LinkedIn (público)

https://github.com/lianfixx/LinkedIn · último cambio: 18 nov 2026

Skill para planear, redactar, revisar, entregar para publicar y medir lo que Emi publica en su perfil personal de LinkedIn (linkedin.com/in/emiliano-milla). Sirve en cualquier IA.

Skills: `linkedin-pro`

Último registro: 18 nov 2026 · Post de The Economist aprobado para el jueves 19 · Agente: Claude Code (sesión en la nube)
Pendiente: el enlace cuando salga el 19 a las 8:30.

## Tareas programadas

- Revisión semanal del algoritmo de X (x-viral) · Lunes 12:47 · repo `X`
- Arranque de la primera semana en X · Una vez: lunes 16 nov 2026, 08:00 · repo `X`
- Revisión semanal del nicho de historias · Domingos 18:47 · repo `HISTORIAS-`
- Radar semanal de tendencias de video · Domingos 21:23 · repo `VIDEOS-IA-SKILL-MILLA`

## Skills instaladas en Claude

- `vox-studio` · `VIDEOS-IA-SKILL-MILLA`
- `milla-video-studio` · `VIDEOS-IA-SKILL-MILLA`
- `x-viral` · `X`
- `video-vox` · `santmun/video-vox`
