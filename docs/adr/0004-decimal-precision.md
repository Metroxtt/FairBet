# ADR 0004: Manejo de Decimal y precisión financiera
**Fecha:** 2026-05-30
**Autor:** Edwar

## Contexto
Cuando empecé a programar el wallet, lo primero que hice fue usar float para los
montos. Total, 100.50 es 100.50, ¿no? Pues no. Resulta que en la primera prueba
con Hypothesis, cuando empecé a hacer operaciones con montos como 0.1 + 0.2, me
dio 0.30000000000000004. Ahi me di cuenta del problema.

## Opciones consideradas

### 1. Seguir con float
Total, son solo 2 decimales, redondeas y ya.

- **Pros:** No hay que cambiar nada.
- **Contras:** Los errores de redondeo se acumulan. Si haces 1000 operaciones,
  terminas perdiendo o ganando centavos sin querer. En un sistema real eso es
  dinero perdido o encontrado. Y el challenge lo prohibe explicitamente.

### 2. Usar Decimal de Python
Django tiene un campo DecimalField que usa el Decimal de Python internamente.
Solo habia que cambiar los campos de la base de datos.

- **Pros:** La precision es exacta. 0.1 + 0.2 es 0.3, no 0.30000000000000004.
- **Contras:** Hay que acordarse de convertir todo a Decimal antes de operar.
  Si en algun lado se te cuela un float, la cagas.

### 3. Usar enteros (centavos)
Guardar todo como enteros. 100.50 soles se guarda como 10050 centavos.

- **Pros:** No hay problemas de precision, los enteros son exactos.
- **Contras:** Todo el mundo piensa en soles, no en centavos. Al mostrar en
  pantalla hay que dividir entre 100. Y si necesitas 4 decimales (como pedia
  el challenge), ya no funciona tan limpio con centavos.

## Decisión
Elegí Decimal con max_digits=18 y decimal_places=4. El challenge pedia
exactamente eso. Ademas Django ya lo soporta nativamente con DecimalField, asi
que no habia que hacer nada raro. Eso si, en los serializers hay que asegurarse
de que los inputs se conviertan a Decimal y no a float.

## Consecuencias
- Todos los montos son exactos, no hay errores de redondeo
- Hypothesis pudo probar las invariantes financieras sin falsos positivos por
  precision
- Hay que tener cuidado al hacer json porque JSON no soporta Decimal, hay que
  convertirlo a string antes de enviarlo al frontend
- En el frontend usamos parseFloat para mostrar, pero siempre enviamos strings