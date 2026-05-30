# ADR 0009: Controles de juego responsable
**Fecha:** 2026-05-30
**Autor:** Edwar

## Contexto
El challenge dice que tenemos que implementar controles de juego responsable
obligatorios. No es opcional. La Ley 31557 exige que los usuarios puedan
ponerse límites y autoexcluirse. Además, el mensaje de "juego responsable" tiene
que aparecer en todas las pantallas donde se pueda apostar.

## Opciones consideradas

### 1. Solo poner el mensaje de advertencia
Lo más básico: un texto que diga "Juega con responsabilidad" y ya.

- **Pros:** Fácil, rápido, una linea de HTML.
- **Contras:** No cumple con lo que pide el challenge. No hay límites reales,
  no hay autoexclusión. Es solo un cartelito.

### 2. Límites de depósito + autoexclusión + mensaje obligatorio
Implementar los tres controles que pide el challenge: límite diario/semanal/
mensual para depositar, autoexclusión temporal o indefinida, y el mensaje en
todas las pantallas de apuesta.

- **Pros:** Cumple con el challenge y con la ley peruana.
- **Contras:** Más trabajo. Hay que agregar modelos, validaciones, vistas y
  templates.

## Decisión
Fuimos por la opción 2. Además, para los límites de depósito tomamos una
decisión extra: subir el límite tiene cooldown de 24 horas, pero bajarlo es
instantáneo. Eso está documentado en el ADR 02. La idea es que si alguien está
en un momento de euforia y quiere subir su límite para meter más plata, tenga
que esperar un día y pensar si realmente lo necesita. En cambio, si quiere
bajarlo porque siente que está perdiendo el control, que pueda hacerlo ya.

Para la autoexclusión, el usuario elige un plazo (7 días, 30 días, 90 días o
indefinido) y ya no puede apostar ni depositar hasta que pase ese tiempo. Y no
puede revertirlo antes, justamente para que sirva como control real.

El mensaje de juego responsable lo metimos como un include en el base.html
y en el bet_slip.html, así aparece automáticamente en todas las pantallas de
apuesta sin tener que acordarse de ponerlo cada vez.

## Consecuencias
- Cumplimos con el requisito del challenge y con la Ley 31557
- El usuario siempre ve el mensaje de advertencia antes de apostar
- Los límites de depósito realmente limitan, no son decorativos
- La autoexclusión es efectiva porque no se puede revertir
- En los tests validamos que un usuario autoexcluido no pueda apostar ni retirar