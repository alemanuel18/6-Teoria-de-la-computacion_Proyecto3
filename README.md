# Proyecto 3: simulador de máquinas de Turing

Simula máquinas deterministas de **una cinta** descritas en YAML. Por cada cadena imprime todas las descripciones instantáneas (IDs) y si termina en el estado final. Incluye los dos casos pedidos para la demostración: una reconocedora de `aⁿbⁿ` (`n ≥ 1`) y una alteradora que complementa cadenas binarias sin borrarlas.

## Preparar y ejecutar

Se requiere Python 3.10 o superior. Desde la raíz del repositorio:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m turing examples/reconocedora.yaml
.venv/bin/python -m turing examples/alteradora.yaml
```

En Windows, reemplace `.venv/bin/python` por `.venv\\Scripts\\python.exe`. Si no hay acceso a PyPI pero PyYAML 6 está instalado en el Python del sistema, cree el entorno con `python3 -m venv --system-site-packages .venv`; así se ejecutaron las pruebas en este entorno. `requirements.txt` fija el único paquete externo.

Opciones:

```bash
.venv/bin/python -m turing examples/reconocedora.yaml --max-steps 1000000
.venv/bin/python -m turing examples/alteradora.yaml --no-trace
```

`--max-steps` limita **cada cadena** (predeterminado: 100000). Si se alcanza, el resultado indica `RECHAZADA (límite de pasos alcanzado)`; esto significa que la ejecución quedó inconclusa, no que la máquina haya demostrado rechazo. `--no-trace` omite imprimir las IDs y sirve para entradas grandes. La traza completa puede generar mucho texto y tiempo de salida.

## Formato YAML

El esquema sigue el del enunciado. Ejemplo mínimo que acepta `a`:

```yaml
q_states:
  q_list: [inicio, aceptar]
  initial: inicio
  final: aceptar
alphabet: [a]
tape_alphabet: [a, null]
delta:
  - params:
      initial_state: inicio
      mem_cache_value: null
      tape_input: a
    output:
      final_state: aceptar
      mem_cache_value: null
      tape_output: a
      tape_displacement: S
simulation_strings: [a]
```

- `q_list` contiene estados únicos. `initial` y `final` deben figurar allí. `final` es terminal y de aceptación; cualquier otro estado sin transición aplicable rechaza.
- `alphabet` contiene los símbolos permitidos en las cadenas. `tape_alphabet` incluye además los símbolos de trabajo y **exactamente un** `null`, que representa el blanco. Cada símbolo es un carácter. Un `#` es un símbolo normal si se declara; el blanco es `null`.
- La memoria auxiliar empieza en `null`. Cada transición se elige por la terna `(initial_state, mem_cache_value, tape_input)` y modifica estado, memoria y celda; `tape_displacement` es `L`, `R` o `S` (izquierda, derecha o quieto). No se admiten transiciones duplicadas para una misma terna.
- `simulation_strings` es la lista de cadenas. Use `""` para la cadena vacía. Cite en YAML los números y otros valores que el parser pudiera interpretar como tipos distintos de texto; por ejemplo, `"0"`, `"1"` y estados `"0"`.
- Una entrada inválida o una configuración incoherente se informa como error antes de simular. La cinta puede extenderse indefinidamente en ambas direcciones.

Cada ID tiene la forma `izquierda[estado|memoria]símbolo_leído derecha`, sin espacios adicionales; `□` representa el blanco solo al visualizar. El índice de la cabeza está justo después de `]`. Se imprime la configuración inicial y la final, incluso si esta es de rechazo. La cinta interna guarda únicamente las celdas no blancas.

## Ejemplos incluidos

| Archivo | Comportamiento | Entradas del video |
| --- | --- | --- |
| `examples/reconocedora.yaml` | Marca pares `a`/`b` con `X`/`Y`, vuelve al inicio y verifica el resto. Reconoce `aⁿbⁿ`, `n ≥ 1`. | `aaabbb`, `aaaabbbb` aceptadas; `aabbb`, `aaabba` rechazadas. Todas miden al menos 5. |
| `examples/alteradora.yaml` | Cambia cada `0` por `1` y viceversa, preservando la longitud. Rechaza la cinta vacía; jamás borra toda una entrada no vacía. | `00000`, `11111`, `010101`, `1010101` aceptadas. Todas miden al menos 5. |

## Arquitectura

`load_machine` lee YAML con `safe_load` y `parse_machine` valida estados, alfabetos, entradas y transiciones. La tabla de transiciones es un diccionario indexado por `(estado, memoria, símbolo_leído)`, por lo que la búsqueda de cada paso es directa. `simulate` mantiene estado, memoria, posición de cabeza y un diccionario disperso `posición → símbolo`; una celda ausente es blanco. Escribe, mueve la cabeza y repite hasta alcanzar el estado final, no hallar transición o llegar al límite de pasos. El callback `on_configuration` recibe una copia independiente de la cinta en cada configuración para imprimir la traza; sin callback solo se copia la cinta en la configuración terminal. La interfaz de consola está en `turing/__main__.py`.

## Pruebas

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m tests.load_test
```

Las pruebas unitarias recorren exhaustivamente las 511 cadenas binarias de longitud 0 a 8 para **cada** ejemplo, y cubren rechazo, memoria auxiliar, movimientos `L`/`S`, borrado, blanco, límites, YAML inválido y transiciones duplicadas. La prueba de carga simula 10 000, 50 000 y 100 000 símbolos en la alteradora, además de 400 en la reconocedora. En este entorno, sin imprimir IDs, se observaron respectivamente ~0.002, ~0.010, ~0.020 y ~0.015 segundos; los tiempos dependen del equipo. Para cadenas más largas, ajuste `--max-steps`.

## Entrega

El código y las instrucciones están listos para un repositorio privado. La creación del repositorio, la invitación de docentes/auxiliares en GitHub y la grabación/publicación del video de YouTube requieren las cuentas y datos del curso del estudiante. Para el video, ejecute ambos YAML sin `--no-trace` y explique la arquitectura anterior.
