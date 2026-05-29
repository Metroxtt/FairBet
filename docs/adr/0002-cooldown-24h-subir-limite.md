# ADR 0002: Cooldown de 24h para subir limites de deposito
**Fecha:** 2026-05-27
**Autor:** Raiza
## Contexto
La Ley 31557 exige controles de juego responsable. Los usuarios pueden
configurar limites diarios, semanales y mensuales de deposito. Se necesita
decidir cuando toma efecto un cambio de limite.
## Opciones consideradas
### 1. Cambio instantaneo (subir y bajar sin restriccion)
- **Pros:** Mejor experiencia de usuario.
- **Contras:** Permite que un usuario en un momento de euforia suba su
  limite drasticamente.
### 2. Cooldown 24h para subir; instantaneo para bajar
- **Pros:** El usuario reduce su exposicion inmediatamente. Para aumentarlo
  debe esperar 24h, introduciendo un periodo de reflexion.
- **Contras:** Peor UX para subidas legitimas.
### 3. Cooldown para ambos
- **Pros:** Simetrico.
- **Contras:** Penaliza al usuario que quiere reducir su exposicion.
## Decision
Cooldown de 24h solo para subir el limite; bajar es instantaneo.
## Consecuencias
- El usuario siempre puede bajar su limite de inmediato.
- Para subirlo debe esperar 24h desde el ultimo cambio.
- Se usa updated_at del modelo DepositLimit para verificar el tiempo.