# ADR 0011: Separación de roles: staff no puede apostar
**Fecha:** 2026-05-30
**Autor:** Edwar

## Contexto
Cuando terminamos el dashboard del operador, me pregunté: ¿un administrador
puede apostar en su propia plataforma? Al principio pensé que sí, total es un
simulador educativo. Pero luego lo pensé mejor y no tiene sentido.

El admin es el que maneja la casa. Tiene acceso a la cuenta "casa" y a las
cuentas de apuestas pendientes. Si apuesta, está apostando contra su propia
casa. En la vida real, un operador de apuestas no puede jugar en su propio
local. Sería como un cajero de banco sacando billetes de su propia caja.

## Opciones consideradas

### 1. Dejar que el staff pueda apostar normal
No poner ninguna restricción. El admin ve el dashboard y también puede apostar.

- **Pros:** No hay que tocar código, menos trabajo.
- **Contras:** No tiene lógica. El admin puede ver las cuotas antes que nadie,
  puede manipular mercados, etc. Es un conflicto de intereses.

### 2. Bloquear apuestas, depósitos y retiros para staff
Si eres staff, no puedes usar el endpoint de place_bet, ni depositar ni retirar
fichas. El bet slip directamente no se muestra en tu pantalla.

- **Pros:** Separación clara de roles. El admin gestiona, el usuario apuesta.
- **Contras:** Un poco más de código. Y si el admin quiere probar el sistema,
  tiene que crear un usuario normal aparte.

### 3. Bloquear solo apuestas, permitir depósitos
El admin no puede apostar pero sí puede depositar fichas para probar.

- **Pros:** El admin puede probar el flujo de depósitos.
- **Contras:** Sigue siendo raro que un admin tenga saldo pero no pueda usarlo.

## Decisión
Elegí la opción 2. Si eres staff:
- No puedes llamar a `/api/bets/place/`
- No puedes llamar a `/api/wallet/deposit/`
- No puedes llamar a `/api/wallet/withdraw/`
- El bet slip no se renderiza en tu pantalla

Además, en el dashboard del operador también bloqueamos que el staff se
auto-bloquee o se auto-verifique KYC. El admin tiene sus propias rutas para
gestionar usuarios.

## Consecuencias
- El sistema ahora tiene dos roles bien definidos
- La navegación se adapta según si eres staff o no
- Para probar apuestas como admin, toca crearse un usuario normal aparte
- Los endpoints de gestión (block, unblock, verify-kyc para otros usuarios)
  solo funcionan para administradores