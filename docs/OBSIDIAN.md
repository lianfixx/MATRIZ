# Obsidian: la Matriz en tu Mac y tu iPhone

Lo que vas a tener:

- **El grafo:** la Matriz al centro (en naranja), los siete cerebros alrededor y cada repositorio colgando de su cerebro. Un clic en un punto abre su nota.
- **La portada** (`MATRIZ`): cerebros, último movimiento y lo último que hizo cada IA.
- **La tabla** (`Repositorios`): todos tus repositorios con tres vistas: *Por cerebro*, *Lo más reciente* y *Con pendiente*.
- **Tus pendientes y notas** dentro de la nota de cada cerebro. Se escriben en el panel (https://matriz.milla-abogados.workers.dev, con tu contraseña) y llegan aquí solos en unos minutos. El archivo de cada tablero está en `tablero/` y usa el formato de tareas de Obsidian.

Tiempo: unos 15 minutos en la Mac y 5 en el iPhone. Todo viene ya configurado; solo hay que abrirlo.

## Cómo se mueve la información

```
GitHub (se actualiza solo cada día a las 06:17)
   ↓  el complemento Git de Obsidian trae los cambios al abrir y cada 10 minutos
Tu Mac (carpeta ~/Matriz)
   ↓  Obsidian Sync, cifrado de extremo a extremo
Tu iPhone
```

La Mac es el puente: el iPhone recibe lo nuevo mientras Obsidian esté abierto en la Mac. Obsidian no sube nada a GitHub: los cambios entran por el panel (pendientes, notas, proyectos nuevos), que los guarda en GitHub, y de ahí bajan a Obsidian. Así ninguna edición choca con la actualización diaria.

## En la Mac

1. **Instala Obsidian.** Descárgalo de https://obsidian.md/download y arrástralo a Aplicaciones. Es gratis.

2. **Copia la Matriz a tu Mac.** Abre Terminal (⌘ + Espacio, escribe «Terminal») y pega esta línea:

   ```bash
   git clone https://github.com/lianfixx/MATRIZ ~/Matriz
   ```

   Si macOS ofrece instalar las «herramientas de línea de comandos para desarrolladores», acepta, espera a que termine y vuelve a pegar la línea.

   La carpeta queda en tu carpeta personal, no en Documentos ni en el Escritorio, a propósito: si iCloud sincroniza esas carpetas, se mezclarían dos sincronizaciones, y Obsidian lo desaconseja.

3. **Ábrela como bóveda.** En Obsidian elige «Abrir carpeta como bóveda» y selecciona `Matriz` (en Finder, ⌘ + Shift + H te lleva a tu carpeta personal).

4. **Activa el complemento Git.** Ajustes (el engrane, abajo a la izquierda) → Complementos de la comunidad → Activar → Explorar → busca **Git** (autor: Vinzent) → Instalar → Activar.

   Ya viene configurado: trae los cambios al abrir y cada 10 minutos, y nunca sube nada. Para comprobarlo, en Ajustes → Git deben verse «Auto pull interval» en 10 y «Disable push» activado. Si no, ajústalos tú.

5. **Úsala.**
   - Abre `MATRIZ` y márcala como favorita: clic derecho en el nombre → Añadir a marcadores.
   - El grafo se abre con el icono de grafo de la barra izquierda o con ⌘ + G.
   - `Repositorios` es la tabla. Cambia de vista con el menú de arriba a la izquierda.

## En el iPhone (Obsidian Sync)

Requiere **Obsidian Sync Standard**: 4 USD al mes con facturación anual. Lo contratas tú, con tu cuenta de Obsidian.

1. **En la Mac:** Ajustes → Sincronización → inicia sesión y suscríbete.
2. **En la Mac:** en Sincronización crea una bóveda remota llamada `Matriz` y ponle una **contraseña de cifrado**. Guárdala en tu gestor de contraseñas: si se pierde, Obsidian no puede recuperarla.
3. **En la Mac:** en Sincronización → Carpetas excluidas, agrega `ia` y `tools`. No hacen falta en el teléfono.
4. **En el iPhone:** instala Obsidian desde la App Store, inicia sesión con la misma cuenta, conéctate a la bóveda remota `Matriz` y escribe la contraseña de cifrado. Si pregunta dónde guardar la bóveda, **no** elijas iCloud.
5. **En el iPhone:** Ajustes → Sincronización → desactiva «Lista de complementos de la comunidad activos» y «Complementos de la comunidad instalados». El complemento Git solo debe funcionar en la Mac; en el iPhone su propio autor lo declara inestable.

Los nombres de los menús pueden variar un poco según la versión de Obsidian.

## Tres reglas para que nunca se rompa

- **Tus notas van en `notas/`.** Obsidian guarda ahí toda nota nueva. Esa carpeta **no se sube a GitHub** (el repositorio es público); vive en tu Mac y, con Sync, en tu iPhone, cifrada y con historial de versiones.
- **No edites lo generado:** `MATRIZ_GENERAL`, `MATRIZ`, `cerebros/`, `repos/`, `contexto/` y `bitacora/` se reescriben cada día. Tampoco `tablero/` desde Obsidian: cámbialo en el panel y tus cambios se perderían o bloquearían la actualización.
- **Si el complemento Git avisa de un conflicto,** no borres nada: pídele a Claude que lo revise.

## Más adelante

Obsidian tiene un cliente sin pantalla («Obsidian Headless», en beta desde febrero de 2026) que permitiría que GitHub mande los cambios directo a Sync, sin depender de que la Mac esté abierta. Lo evaluamos cuando salga de beta.
