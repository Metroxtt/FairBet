# ADR 0010: Auditoría inmutable con hash chain
**Fecha:** 2026-05-30
**Autor:** Edwar

## Contexto
El challenge pide una tabla de auditoría "append-only" donde cada movimiento
del wallet quede registrado y no se pueda modificar sin que se note. Además
pide encadenamiento por hash (hash_n = SHA256(hash_n-1 + payload_n)).
Originalmente pensé que era algo exagerado para un proyecto educativo, pero
cuando lo implementé entendí el punto.

## Opciones consideradas

### 1. Solo la tabla LedgerEntry sin hash
Registrar los movimientos pero sin encadenamiento criptográfico.

- **Pros:** Menos código, más simple, la tabla ya es de solo lectura.
- **Contras:** Si alguien con acceso a la base de datos modifica un registro
  antiguo, no hay forma de detectarlo. El campo `ON DELETE PROTECT` evita
  borrados pero no modificaciones.

### 2. LedgerEntry con hash y previous_hash
Cada entrada tiene un hash SHA-256 que se calcula en base al contenido de la
entrada más el hash de la entrada anterior. Así se forma una cadena.

- **Pros:** Si modificas cualquier entrada de la cadena, el hash deja de
  coincidir y lo detectamos al hacer la verificación.
- **Contras:** Hay que calcular el hash al guardar, y hay que recorrer toda la
  cadena para verificar. Más lento, pero es una operación que solo hace el
  admin cuando quiere auditar.

## Decisión
Elegí la opción 2. En el modelo LedgerEntry agregué dos campos: `hash` y
`previous_hash`. Cuando se crea una entrada nueva, el método `save()` calcula
el hash automáticamente antes de guardar: busca la última entrada de esa cuenta,
toma su hash como previous_hash, y genera el nuevo hash con SHA-256.

Además hice un endpoint `/api/wallet/verify-ledger/` que solo los administradores
pueden ejecutar. Recorre todas las cuentas y todas sus entradas, recalcula los
hashes y verifica que la cadena esté íntegra. Si encuentra algo raro, devuelve
un error con los detalles.

En el dashboard del operador hay un botón para ejecutar esta verificación.

## Consecuencias
- Cualquier modificación en el ledger se detecta automáticamente
- El admin puede verificar la integridad desde el dashboard con un clic
- Es un poco más lento al crear entradas, pero apenas se nota
- Cumplimos con el requisito de auditoría del challenge
- Si alguien intenta modificar un registro del 2025, el hash no va a coincidir
  y el sistema lo reporta