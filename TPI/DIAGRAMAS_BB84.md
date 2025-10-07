# 🎨 DIAGRAMAS VISUALES DEL PROTOCOLO BB84

## Diagrama 1: Flujo Completo sin Espía

```
ALICE                    CANAL CUÁNTICO              BOB
=====                    ==============              ===

1. PREPARACIÓN
┌─────────────┐
│ Bits: 0 1 1 │
│ Bases: + × + │
└─────────────┘
      ↓
2. CODIFICACIÓN
┌─────────────┐
│ |0⟩ |−⟩ |1⟩ │  (qubits)
└─────────────┘
      ↓
      ├─────────────────→                          ┌─────────────┐
                                                    │ Bases: × × + │
                                                    └─────────────┘
                                                           ↓
                                                    3. MEDICIÓN
                                                    ┌─────────────┐
                                                    │ ? ? 1       │
                                                    └─────────────┘

4. COMPARACIÓN PÚBLICA DE BASES
Alice: + × +
Bob:   × × +
Match: ✗ ✓ ✓  ← Solo se quedan con posiciones 2 y 3

5. CLAVE SIFTED
Alice: [1, 1]
Bob:   [1, 1]  ✅ IGUALES (sin espía)

6. VERIFICACIÓN
Muestra: posición 2
Error: 0/1 = 0%
QBER < 11% → ✅ CLAVE SEGURA

7. CLAVE FINAL: "1"
```

---

## Diagrama 2: Flujo Completo CON Espía (Eve)

```
ALICE          EVE          CANAL          BOB
=====          ===          =====          ===

1. Alice envía
|+⟩ ────────→

2. Eve intercepta y mide
                ┌───────┐
                │ Base: + │  ← ¡Eligió base incorrecta!
                └───────┘
                    ↓
                Mide: 0 (colapsa el estado)
                    ↓
                Prepara: |0⟩  ← Ya no es |+⟩
                    ↓
                ├────────→

3. Bob recibe |0⟩
                          ┌───────┐
                          │ Base: × │  ← Base correcta (igual que Alice)
                          └───────┘
                              ↓
                          Mide: + o − (50/50)
                              ↓
                          Resultado: ERROR! 🚨

4. RESULTADO
Alice esperaba: |+⟩ → Bob mide en × → obtiene |+⟩
Pero Eve cambió: |0⟩ → Bob mide en × → obtiene |+⟩ o |−⟩ (50%)

QBER sube a ~25% → ❌ ESPIONAJE DETECTADO
```

---

## Diagrama 3: Estados Cuánticos

```
BASE RECTILÍNEA (+)          BASE DIAGONAL (×)
===================          =================

    ↑                             ⤢
|0⟩ = Vertical              |+⟩ = 45°
    ↕                        |+⟩ = (|0⟩ + |1⟩)/√2
    
    ↔                             ⤡
|1⟩ = Horizontal            |−⟩ = 135°
                            |−⟩ = (|0⟩ - |1⟩)/√2


TRANSFORMACIÓN CON HADAMARD (H):

H|0⟩ = |+⟩                  H|+⟩ = |0⟩
H|1⟩ = |−⟩                  H|−⟩ = |1⟩

🔑 Hadamard convierte entre las dos bases
```

---

## Diagrama 4: Circuito Cuántico (Qiskit)

```
Ejemplo: Alice envía bit=1 en base × (diagonal)

        ┌───┐┌───┐
q_0: |0⟩┤ X ├┤ H ├  ← Prepara |−⟩
        └───┘└───┘
           ↓    ↓
         |1⟩  |−⟩

Luego Eve (si está presente):
        ┌───┐┌─┐
q_0: |−⟩┤ H ├┤M├  ← Mide (si eligió base ×)
        └───┘└╥┘
              ║
c: 0 ═════════╩═  ← Resultado clásico

Finalmente Bob:
        ┌───┐┌─┐
q_0: ?  ┤ H ├┤M├  ← Mide en su base
        └───┘└╥┘
              ║
c: 0 ═════════╩═  ← Resultado final
```

---

## Diagrama 5: Estadísticas de Error

```
SIN ESPÍA (Canal limpio)
========================
Comparación de 100 bits después de sifting:

Alice: 0110100111010010...
Bob:   0110100111010010...
       ✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓

Errores: 0-2/100
QBER: 0-2%
Estado: ✅ SEGURO


CON ESPÍA (Eve activa)
======================
Comparación de 100 bits después de sifting:

Alice: 0110100111010010...
Bob:   0111100101011010...
       ✓✓✗✓✓✗✓✗✗✓✗✓✗✓✗✓

Errores: 20-30/100
QBER: 20-30%
Estado: ❌ COMPROMETIDO

┌─────────────────────────────────────┐
│  UMBRAL DE SEGURIDAD: 11%           │
│                                     │
│  QBER < 11% → Seguro ✅             │
│  QBER ≥ 11% → Espionaje ❌          │
└─────────────────────────────────────┘
```

---

## Diagrama 6: Arquitectura de Nuestra Simulación

```
┌──────────────────────────────────────────────────────┐
│                   USUARIO (Web)                      │
└────────────────────┬─────────────────────────────────┘
                     │
                     ↓
┌──────────────────────────────────────────────────────┐
│            CAPA PRESENTACIÓN (views/)                │
│  • Formulario: key_length, has_eve                   │
│  • Muestra resultados en dashboard/historial         │
└────────────────────┬─────────────────────────────────┘
                     │
                     ↓
┌──────────────────────────────────────────────────────┐
│            CAPA NEGOCIO (business/)                  │
│  • simulation_controller.py                          │
│    - Validaciones (10 ≤ length ≤ 1000)              │
│    - Llama a bb84_simulation.py                      │
│    - Guarda en BD                                    │
│                                                      │
│  • bb84_simulation.py ← ¡AQUÍ ESTÁ LA MAGIA!        │
│    ┌────────────────────────────────────┐           │
│    │ 1. Generar bits/bases aleatorias   │           │
│    │ 2. Codificar qubits (Qiskit)       │           │
│    │ 3. Simular Eve (opcional)          │           │
│    │ 4. Bob mide                        │           │
│    │ 5. Sifting (comparar bases)        │           │
│    │ 6. Calcular QBER                   │           │
│    │ 7. Decidir: seguro o compromised   │           │
│    └────────────────────────────────────┘           │
└────────────────────┬─────────────────────────────────┘
                     │
                     ↓
┌──────────────────────────────────────────────────────┐
│       QISKIT (Simulación Cuántica)                   │
│  • QuantumCircuit: construye circuitos               │
│  • Aer: simula ejecución                             │
│  • Devuelve resultados probabilísticos               │
└────────────────────┬─────────────────────────────────┘
                     │
                     ↓
┌──────────────────────────────────────────────────────┐
│            CAPA DATOS (datos/)                       │
│  • session_repository.py                             │
│  • Guarda: result, final_key, error_rate            │
│  • BD SQLite: simulation_session                     │
└──────────────────────────────────────────────────────┘
```

---

## Diagrama 7: Ejemplo Completo Paso a Paso

```
N = 8 bits para simplificar

PASO 1: Alice genera
┌───┬───┬───┬───┬───┬───┬───┬───┐
│ 0 │ 1 │ 1 │ 0 │ 1 │ 0 │ 1 │ 1 │  Bits
├───┼───┼───┼───┼───┼───┼───┼───┤
│ + │ × │ + │ × │ + │ × │ + │ × │  Bases
└───┴───┴───┴───┴───┴───┴───┴───┘

PASO 2: Bob genera (independiente)
┌───┬───┬───┬───┬───┬───┬───┬───┐
│ × │ × │ + │ + │ + │ × │ × │ + │  Bases
└───┴───┴───┴───┴───┴───┴───┴───┘

PASO 3: Coincidencias
┌───┬───┬───┬───┬───┬───┬───┬───┐
│ ✗ │ ✓ │ ✓ │ ✗ │ ✓ │ ✓ │ ✗ │ ✗ │
└───┴───┴───┴───┴───┴───┴───┴───┘
Posiciones: 1, 2, 4, 5

PASO 4: Clave sifted (SIN EVE)
Alice: [1, 1, 1, 0]
Bob:   [1, 1, 1, 0]  ← Idénticos
QBER: 0%

PASO 5: Clave sifted (CON EVE)
Alice: [1, 1, 1, 0]
Bob:   [1, 0, 1, 1]  ← ¡Diferencias!
       ✓ ✗ ✓ ✗
QBER: 50% → ❌ ABORTADO

PASO 6: Resultado
Sin Eve → Clave final: "1110" (o parte de ella)
Con Eve → Clave rechazada, protocolo abortado
```

---

## 🎯 Conclusión Visual

```
┌─────────────────────────────────────────────────┐
│    BB84 = Seguridad Garantizada por Física     │
│                                                 │
│  Si Eve espía → Introduce errores → Detectada  │
│  Si no espía → QBER bajo → Clave segura        │
│                                                 │
│  🔐 Imposible espiar sin ser detectado 🔐      │
└─────────────────────────────────────────────────┘
```

La simulación con Qiskit replica EXACTAMENTE este comportamiento.
```
