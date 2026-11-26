# Costos de la API de Claude (medición)

Medido el 25/11/2026 por Claude (sesión en la nube), a pedido de Emi. Fuentes: los registros de cada corrida (Actions de `lianfixx/MATRIZ`, 600 corridas del 22 al 26/11/2026), `revisiones/*-ia.json` y la bitácora y los `ESTADO_API.json` del lector del DOF (repositorio privado `dof-trabajo`). No hay llave de administración de Claude Console en la computadora virtual, así que no se pudo cruzar con la factura; la Console es la cifra oficial.

## Lo que hoy usa la API

| Tarea | Dónde corre | Modelo | Costo medido | Al mes (estimado) | Tope |
|---|---|---|---|---|---|
| Lector del DOF por API (lunes y miércoles) | Actions de `dof-trabajo`, espacio `castorena-dof` | Sonnet 5.5 lee por lote; Opus 5.5 sintetiza; Haiku 5.5 tablas | 1.95 USD la corrida normal (552 páginas, 25/11/2026). Puesta en marcha del 23/11: unos 12.10 USD (9.07 de una corrida que cayó y 3.04 de pruebas) | 15 a 25 USD, según las páginas del DOF | 8 USD por corrida; 60 USD al mes (aviso a los 30) |
| Segunda red de privacidad de la Matriz | Actions de `MATRIZ`, espacio `matriz` | Haiku 5.5 | 0.018 USD en 4 días (58 llamadas; solo llama cuando hay líneas nuevas) | 0.15 USD | 10 USD al mes para todo el espacio `matriz` (aviso a los 5) |
| Revisión semanal de la Matriz | Actions de `MATRIZ` | Sonnet 5.5 | 0.040 USD (23/11/2026) | 0.17 USD | el mismo |
| Triaje del Guardián | Actions de `MATRIZ` | Haiku 5.5 | 0.0001 USD (primera corrida, 26/11/2026) | menos de 0.01 USD | el mismo |

**Total medido en noviembre:** unos 14.2 USD, de los que 12.1 fueron la puesta en marcha del lector del DOF. **Gasto mensual esperado en adelante:** de 16 a 26 USD, casi todo del DOF.

## Qué ahorra a la suscripción

- DOF: desde el 23/11/2026, lo que el lector por API deja íntegro ya no se relee con la suscripción; la suscripción solo cierra, verifica y redacta.
- Guardián: la API hace el triaje diario; la tarea de suscripción «Guardián · relevo si falla la API» solo entra si la API falló, repara la causa y deja la API lista.

## Cómo volver a medir

Cada corrida deja su costo: `revisiones/*-ia.json` (semanal), la línea `{"modo": "red", …, "costo_usd": …}` del paso «Segunda red» y la línea «Triaje: … costo USD …» del paso «Guardián» en los registros de «Actualizar la Matriz», y `bitacora/AAAA-MM.md` de `dof-trabajo`. La cifra oficial está en Claude Console, por espacio de trabajo.
