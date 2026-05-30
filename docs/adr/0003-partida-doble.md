# ADR 0003: Modelo de partida doble para el wallet
**Fecha:** 2026-05-30
**Autor:** Edwar

## Contexto
Cuando empezamos el proyecto, lo primero que dijeron en el challenge fue "partida
doble". Yo no sabia bien que era, pense que era solo poner dos tablas y ya.
Pero resulta que cada vez que alguien deposita, tienes que registrar un debito
en una cuenta y un credito en otra. Si no, no hay forma de auditar despues.

Ademas, el challenge dice explicitamente que el saldo no se guarda, sino que se
calcula. Osea, si alguien pregunta "cuanto tengo?", el sistema suma todos los
creditos y resta todos los debitos en el momento.

## Opciones consideradas

### 1. Tener un campo saldo en Account
Lo mas facil: en la tabla Account pones un campo decimal llamado "balance" y
cuando alguien deposita le sumas, cuando retira le restas.

- **Pros:** Super facil, una linea de codigo, todo funciona rapido.
- **Contras:** No sabes como se llego a ese numero. Si alguien mete mano en la
  base de datos, no te enteras. Y si el servidor se cae justo cuando estabas
  actualizando el saldo, ahi quedó. Ademas el challenge no lo permite.

### 2. Partida doble con LedgerEntry
Cada transaccion crea dos filas en una tabla LedgerEntry: una con debit y otra
con credit. Y el balance se calcula restando todo.

- **Pros:** Sabes exactamente que paso en cada momento. Puedes auditar. Si algo
  falla, la transaccion atomica lo revuelta todo.
- **Contras:** Hay que escribir mas codigo. Y cada vez que alguien entre a su
  billetera, hay que hacer una suma de todos los movimientos. Puede ser lento
  si hay muchos.

### 3. Mixto: guardar el saldo pero tambien los movimientos
Tener ambas cosas: el historial de transacciones y un campo saldo actualizado.

- **Pros:** Lo mejor de ambos mundos, rapido de consultar.
- **Contras:** Puede desincronizarse. Si actualizas el balance y no el historial
  (o al reves), nunca sabes cual es el verdadero.

## Decision
Me fui por la opcion 2. Al principio me dio miedo porque era mas trabajo, pero
cuando lo implemente vi que en realidad es bastante limpio. La funcion
`transfer()` crea dos registros automaticamente y usa `select_for_update()` para
que no haya problemas si dos personas transfieren al mismo tiempo.

El balance no lo guardamos en la base de datos. Lo calculamos cada vez con una
propiedad en Python (@property) que suma los credits y resta los debits. Asi
nunca se desincroniza porque solo hay una fuente de verdad.

## Consecuencias
- Ahora cualquier movimiento esta registrado y no se puede borrar
- El balance siempre es correcto porque se calcula en vivo
- Las consultas son un poco mas lentas, pero con la cantidad de datos que
  manejamos (esto es un proyecto educativo) no se nota
- Cuando hicimos los tests con Hypothesis, justamente validamos que la suma de
  debitos siempre es igual a la suma de creditos. Si hubiera usado la opcion 1,
  no podria probar eso