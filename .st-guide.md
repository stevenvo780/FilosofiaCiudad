# ST — Guía del Lenguaje de Lógica Formal

> Intérprete: `st` (disponible globalmente en la terminal)

## Inicio rápido

```bash
# Ejecutar un archivo .st
st run archivo.st

# REPL interactivo
st

# Ver perfiles disponibles
st --list-profiles

# Verificar sintaxis
st check archivo.st
```

## Sintaxis básica

### 1. Declarar lógica
Todo script empieza con la lógica a usar:
```st
logic classical.propositional
```

### 2. Axiomas y teoremas
```st
axiom a1 : P -> Q
axiom a2 : P
theorem t1 : Q
```

### 3. Comandos de verificación
```st
check valid (P | !P)           // ¿Es tautología?
check satisfiable (P & Q)     // ¿Tiene modelo?
check equivalent (P->Q), (!P|Q)  // ¿Son equivalentes?
derive Q from {a1, a2}        // Derivar por Modus Ponens
truth_table (P & Q -> R)      // Tabla de verdad
countermodel (P -> Q)         // Contramodelo si inválido
```

### 4. Variables con `let`
```st
let f = (P -> Q) & (Q -> R)
check valid f -> (P -> R)
```

## Operadores

| Operador | Significado | Alias español |
|----------|-------------|---------------|
| `&` | Conjunción (Y) | `y` |
| `\|` | Disyunción (O) | `o` |
| `!` | Negación | `no` |
| `->` | Implicación | `entonces` |
| `<->` | Bicondicional | `sii` |
| `forall x` | Para todo x | |
| `exists x` | Existe x | |
| `[]` | Necesariamente (modal) | |
| `<>` | Posiblemente (modal) | |

## Perfiles de lógica disponibles

- `classical.propositional` — Lógica proposicional clásica
- `classical.first_order` — Lógica de primer orden (FOL)
- `modal.k` — Lógica modal sistema K
- `paraconsistent.belnap` — Lógica paraconsistente Belnap 4-valuada
- `intuitionistic.propositional` — Lógica intuicionista
- `deontic.standard` — Lógica deóntica
- `epistemic.s5` — Lógica epistémica S5
- `temporal.ltl` — Lógica temporal lineal
- `probabilistic.basic` — Lógica probabilística
- `aristotelian.syllogistic` — Silogística aristotélica

## Capa Textual (Text Layer)

Permite vincular documentos a fórmulas lógicas:
```st
logic classical.propositional
let p1 = passage([[documento.md#seccion]])
let f1 = formalize p1 as (P & Q)
claim c1 = f1
check valid c1
```

## API programática (Node.js)

```javascript
const { evaluate, createInterpreter } = require('@stevenvo780/st-lang/api');

// Evaluación directa
const result = evaluate('logic classical.propositional\ncheck valid (P | !P)');
console.log(result.results[0].status); // 'valid'

// Intérprete con estado
const st = createInterpreter();
st.exec('logic classical.propositional');
st.exec('axiom a1 : P -> Q');
const r = st.exec('check satisfiable a1');
console.log(r.ok); // true
```

## Ejemplos completos

### Modus Ponens
```st
logic classical.propositional
axiom p1 : P -> Q
axiom p2 : P
derive Q from {p1, p2}
```

### Silogismo hipotético
```st
logic classical.propositional
axiom h1 : P -> Q
axiom h2 : Q -> R
check valid (P -> R)
```

### Lógica de primer orden
```st
logic classical.first_order
axiom all_mortal : forall x (Human(x) -> Mortal(x))
axiom socrates : Human(socrates)
derive Mortal(socrates) from {all_mortal, socrates}
```

### Lógica modal
```st
logic modal.k
check valid [](P -> Q) -> ([]P -> []Q)  // Axioma K
```

---
*ST v$(st --version 2>/dev/null || echo "unknown") — Motor de lógica formal multi-sistema*
*Docs completas: https://github.com/stevenvo780/ST*
