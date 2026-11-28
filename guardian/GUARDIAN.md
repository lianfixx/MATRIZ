# Guardián de la Matriz · 2026-11-28

**41/100 · En riesgo**

Auditoría de seguridad y privacidad de todos los repositorios de Emi. Solo lee y aconseja. Aquí solo hay conteos: el detalle (qué repositorio, qué archivo) es privado. Cómo funciona: [docs/GUARDIAN.md](../docs/GUARDIAN.md).

Evolución: 44 → 44 → 41 → 41

Revisados: 34 repositorios (21 públicos). Acceso por API: 34 revisados, 0 sin permiso para revisar.

## 🔑 Llaves a la vista · Bien

Hallazgos: 3 bajo, 2 aviso.

- **Por qué importa:** Una llave de API o un token en un archivo deja usar tus cuentas (Claude, GitHub, Google, Cloudflare) a quien lo vea. En un repositorio público, los robots las encuentran en minutos.
- **Cómo lo arreglas:** Revoca la llave en su servicio y crea otra; guárdala como secreto (GitHub → Settings → Secrets, o ~/.config de tu box) y bórrala del archivo. Borrarla sin revocarla no basta.

## 🕵️ Secretos en el historial de Git · Bien

Hallazgos: 2 aviso.

- **Por qué importa:** Aunque ya borraste la llave, sigue en los commits anteriores y cualquiera puede verla en el historial. Lo borrado en Git no desaparece.
- **Cómo lo arreglas:** Lo único seguro es revocar la llave y crear otra. Reescribir el historial no es necesario después de revocarla (y está prohibido el force-push sin tu confirmación).

## 🪪 Credenciales expuestas y vencimientos · Revisar

Hallazgos: 1 medio, 4 bajo.

- **Por qué importa:** Archivos como .env, .pem o credentials.json guardan accesos completos; si se suben, se filtran todos juntos. Y una llave que vence sin aviso detiene tus automatizaciones.
- **Cómo lo arreglas:** Saca el archivo del repositorio, agrégalo a .gitignore y revoca lo que traía. Renueva antes del vencimiento: la Matriz te muestra la fecha en «Vencimientos».

## 👥 Quién tiene acceso a qué · Revisar

Hallazgos: 1 medio, 5 bajo.

- **Por qué importa:** Cada colaborador o llave de despliegue es una puerta. Y un repositorio sin los frenos de ia/ acepta commits sin registro y sin la revisión de secretos.
- **Cómo lo arreglas:** Quita colaboradores y llaves de despliegue que ya no uses (Settings → Collaborators / Deploy keys). Instala los frenos con el protocolo común (ia/ y registro-ia.yml).

## 📡 Qué sale de tu cuenta · Bien

Hallazgos: 2 aviso.

- **Por qué importa:** Todo lo de un repositorio público lo puede leer cualquiera, también lo que tus workflows publican. Una acción de GitHub de terceros sin versión fija puede cambiar y ejecutar código ajeno con tus secretos.
- **Cómo lo arreglas:** Vuelve privado lo que no necesita ser público. En los workflows, fija cada acción a su SHA (como ya hace la Matriz) y declara «permissions» con lo mínimo.

## 🧾 Datos de clientes y personales expuestos · En riesgo

Hallazgos: 43 crítico, 66 alto, 29 bajo.

- **Por qué importa:** Expedientes, CURP, RFC, teléfonos o nombres de clientes en un repositorio público violan el secreto profesional y la protección de datos personales, aunque sea en un archivo viejo.
- **Cómo lo arreglas:** Saca el dato del archivo (o vuelve privado el repositorio) y agrega el nombre del cliente al secreto MATRIZ_RESERVADOS. Si estuvo en el historial de un repositorio público, considéralo visto.

## 🧠 Memoria para tus IA · Bien

Hallazgos: sin hallazgos.

- **Por qué importa:** Si un AGENTS.md, CLAUDE.md o SKILL.md es demasiado largo, apunta a archivos que ya no existen o rompe el formato de la skill, la IA arranca con instrucciones a medias y nadie te avisa: el fallo es silencioso.
- **Cómo lo arreglas:** Recorta o divide el archivo (lo detallado va a referencias que se leen cuando hacen falta), corrige o quita los enlaces rotos y valida la skill con `python3 ia/check_skill.py <carpeta>`.

## 📦 Origen de tus skills · Bien

Hallazgos: sin hallazgos.

- **Por qué importa:** Una skill son instrucciones (y a veces scripts) que tu IA sigue con tus permisos. Una de terceros puede cambiar sin que lo sepas.
- **Cómo lo arreglas:** Usa skills de tus repositorios. Si una es de terceros, revisa su contenido, fija la versión (una copia en tu cuenta) y vuelve a revisarla cuando la actualices.
