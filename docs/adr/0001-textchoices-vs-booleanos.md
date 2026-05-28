# ADR 0001: TextChoices vs Booleanos para estado de usuario
**Fecha:** 2026-05-27
**Autor:** Raiza
## Contexto
El modelo User necesita representar el estado de la cuenta del usuario.
Inicialmente se consideraron campos booleanos (is_active, is_excluded, is_verified).
## Opciones consideradas
### 1. Multiples campos booleanos
- **Pros:** Sencillo de implementar.
- **Contras:** Permite estados inconsistentes (ej. is_verified=True y
  is_excluded=True). Escalar implica agregar mas columnas.
### 2. TextChoices con campo estado
- **Pros:** Un solo campo, estados mutuamente excluyentes por diseno.
  Facil de extender. Coincide con el patron de maquina de estados.
- **Contras:** Requiere logica adicional si se necesitan combinar estados.
## Decision
Se eligio TextChoices con un campo estado y cuatro valores:
pendiente_verificacion, verificado, bloqueado, autoexcluido.
## Consecuencias
- Los estados son excluyentes por diseno.
- Properties como es_verificado y esta_autoexcluido hacen el codigo legible.
- Si se necesitan permisos mas granulares, podria requerirse un sistema
  de roles adicional.