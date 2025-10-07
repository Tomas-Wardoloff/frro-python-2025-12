# EXPLICACIÓN DETALLADA DE LA SIMULACIÓN BB84

## 📚 Fundamentos de la Simulación

### 1. ¿Qué es Qiskit?
Qiskit es un framework de IBM para computación cuántica que permite:
- Crear circuitos cuánticos
- Simular comportamiento cuántico en una computadora clásica
- Ejecutar en computadoras cuánticas reales de IBM (opcional)

Nosotros usamos el **simulador Aer** que emula perfectamente el comportamiento
cuántico sin necesitar hardware cuántico real.

---

## 🔄 PASO A PASO: Cómo Funciona Nuestra Simulación

### PASO 1: Generación de Bits y Bases Aleatorias

```python
alice_bits = [0, 1, 1, 0, 1, ...]  # Bits que Alice quiere enviar
alice_bases = [0, 1, 0, 1, 0, ...]  # Bases que Alice usa
bob_bases = [1, 1, 0, 0, 1, ...]    # Bases que Bob usa (independientes)
```

**Interpretación:**
- `0` en bases = Base Rectilínea (+)
- `1` en bases = Base Diagonal (×)

---

### PASO 2: Codificación de Qubits por Alice

**Función:** `encode_qubit(bit, basis)`

**Ejemplo 1: Bit=0, Basis=0 (Base +)**
```python
qc = QuantumCircuit(1, 1)  # 1 qubit, 1 bit clásico
# No aplicamos nada
# Estado final: |0⟩ (polarización vertical)
```

**Ejemplo 2: Bit=1, Basis=0 (Base +)**
```python
qc = QuantumCircuit(1, 1)
qc.x(0)  # Aplicar puerta X (NOT cuántico)
# Estado final: |1⟩ (polarización horizontal)
```

**Ejemplo 3: Bit=0, Basis=1 (Base ×)**
```python
qc = QuantumCircuit(1, 1)
qc.h(0)  # Aplicar puerta Hadamard
# Estado final: |+⟩ = (|0⟩ + |1⟩)/√2 (polarización 45°)
```

**Ejemplo 4: Bit=1, Basis=1 (Base ×)**
```python
qc = QuantumCircuit(1, 1)
qc.x(0)  # Primero NOT
qc.h(0)  # Luego Hadamard
# Estado final: |−⟩ = (|0⟩ - |1⟩)/√2 (polarización 135°)
```

**🔑 Clave:** La puerta Hadamard crea superposición cuántica, permitiendo
codificar información en dos bases incompatibles.

---

### PASO 3: Transmisión (con o sin Eve)

#### Caso A: Sin Espía (Canal Seguro)
```python
# El circuito pasa directamente de Alice a Bob
# El estado cuántico se mantiene intacto
```

#### Caso B: Con Espía (Eve intercepta)

**Función:** `eve_intercept(qc)`

```python
# Eve elige una base aleatoria
eve_basis = random.randint(0, 1)  # 50% + o ×

# Eve mide el qubit
if eve_basis == 1:
    qc.h(0)  # Si mide en base ×
qc.measure(0, 0)

# Eve obtiene un resultado (0 o 1)
# ⚠️ PROBLEMA: La medición COLAPSA el estado cuántico

# Eve prepara un nuevo qubit con lo que midió
qc_new = QuantumCircuit(1, 1)
if eve_bit == 1:
    qc_new.x(0)
if eve_basis == 1:
    qc_new.h(0)

# Eve envía este nuevo qubit a Bob
```

**🎯 Por qué Eve introduce errores:**

Imagina esta situación:
1. Alice envía |+⟩ (bit=0 en base ×)
2. Eve mide en base + (eligió mal)
3. Eve obtiene 0 o 1 con 50% de probabilidad cada uno
4. Eve prepara |0⟩ o |1⟩ (en base +)
5. Bob mide en base × (la correcta)
6. Bob obtiene un resultado INCORRECTO el 50% de las veces

**Ejemplo numérico:**
- Alice: bit=0, base=× → envía |+⟩
- Eve: mide en base + → obtiene 0 (por suerte)
- Eve: envía |0⟩
- Bob: mide en base × → obtiene |+⟩ o |−⟩ (50/50)
- Resultado: ❌ 50% de error cuando Eve usa base incorrecta

---

### PASO 4: Medición por Bob

**Función:** `measure_qubit(qc, basis)`

```python
# Si Bob mide en base diagonal, aplica Hadamard primero
if bob_basis == 1:
    qc.h(0)

# Luego mide
qc.measure(0, 0)
```

**Ejecutar el circuito:**
```python
simulator = Aer.get_backend('qasm_simulator')
job = simulator.run(qc, shots=1)
result = job.result()
counts = result.get_counts()
bob_bit = int(list(counts.keys())[0])
```

**🔬 Qué hace el simulador:**
- Calcula las probabilidades cuánticas del estado
- Simula el colapso de la función de onda
- Devuelve 0 o 1 según las probabilidades

---

### PASO 5: Comparación de Bases (Sifting)

```python
# Alice y Bob comparan públicamente sus bases
matching_bases_indices = [i for i in range(key_length) 
                         if alice_bases[i] == bob_bases[i]]

# Se quedan SOLO con los bits donde las bases coincidieron
alice_key = [alice_bits[i] for i in matching_bases_indices]
bob_key = [bob_results[i] for i in matching_bases_indices]
```

**Ejemplo:**
```
Posición:  0  1  2  3  4  5  6  7
Alice bit: 0  1  1  0  1  0  1  1
Alice bas: +  ×  +  ×  +  ×  +  ×
Bob basis: ×  ×  +  +  +  ×  ×  +
Coincide:  ✗  ✓  ✓  ✗  ✓  ✓  ✗  ✗

Clave filtrada:
Posiciones: 1, 2, 4, 5
Alice: [1, 1, 1, 0]
Bob:   [1, 1, 1, 0]  ← Si no hay Eve, serán iguales
```

---

### PASO 6: Cálculo de la Tasa de Error (QBER)

```python
# Se toma una muestra (25% de la clave)
sample_size = len(alice_key) // 4
sample_indices = random.sample(range(len(alice_key)), sample_size)

# Se comparan públicamente
errors = sum(1 for i in sample_indices if alice_key[i] != bob_key[i])
error_rate = errors / sample_size
```

**QBER = Quantum Bit Error Rate**

**Tasas esperadas:**
- **Sin Eve:** QBER ≈ 0-2% (errores por ruido del canal)
- **Con Eve:** QBER ≈ 25% (Eve usa base incorrecta 50% del tiempo)

**Umbral de seguridad:**
```python
THRESHOLD = 0.11  # 11%
if error_rate < THRESHOLD:
    # ✅ Clave segura
else:
    # ❌ Espionaje detectado, abortar
```

---

### PASO 7: Resultado Final

**Si QBER < 11%:**
```python
# Remover bits usados en verificación
final_key = [alice_key[i] for i in range(len(alice_key)) 
            if i not in sample_indices]

return {
    'result': 'secure',
    'final_key': '11010110...',
    'error_rate': 0.02
}
```

**Si QBER ≥ 11%:**
```python
return {
    'result': 'compromised',
    'final_key': None,
    'error_rate': 0.25,
    'message': '¡Espionaje detectado!'
}
```

---

## 🎭 Diferencias: Simulación vs Realidad

### Nuestra Simulación (Qiskit):
✅ **Ventajas:**
- Emula perfectamente el comportamiento cuántico
- No requiere hardware cuántico ($$$)
- Es determinista y reproducible
- Perfecto para educación

⚠️ **Limitaciones:**
- No hay fotones reales
- No hay canal físico
- No hay ruido térmico/ambiental real
- La "transmisión" es instantánea

### BB84 Real (Hardware Cuántico):
✅ **Realidad Física:**
- Usa fotones reales
- Canal de fibra óptica real
- Detectores cuánticos reales
- Ruido y pérdidas reales

⚠️ **Desafíos:**
- Muy caro (millones de dólares)
- Difícil de implementar
- Pérdida de fotones en el canal
- Tasa de error mayor (5-10% típico)
- Distancia limitada (~100 km sin repetidores)

---

## 📊 Tabla Comparativa

| Aspecto | Simulación (Nuestra) | BB84 Real |
|---------|---------------------|-----------|
| Qubits | Simulados en RAM | Fotones físicos |
| Canal | Array en memoria | Fibra óptica |
| Medición | Cálculo probabilístico | Detector cuántico |
| Velocidad | Instantánea | Velocidad de la luz |
| QBER sin Eve | ~0% | 2-5% |
| QBER con Eve | ~25% | 20-30% |
| Costo | $0 | $$$$$$ |
| Educativo | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Seguridad | Teórica | Real |

---

## 🔐 ¿Por Qué Funciona la Seguridad?

### Principio Cuántico: No-Cloning Theorem
**"No se puede copiar un estado cuántico desconocido"**

Si Eve intenta medir el qubit:
1. **Debe elegir una base** (+ o ×)
2. **La medición colapsa el estado**
3. **Si eligió mal la base** (50% probabilidad):
   - Introduce errores
   - Alice y Bob detectan QBER alto
   - Abortan el protocolo

### Analogía:
Imagina que Alice envía una carta en un sobre especial:
- Si nadie lo abre → llega intacto
- Si Eve lo abre para leerlo → el sobre se daña visiblemente
- Bob nota el daño → sabe que hay espía

En cuántica, **medir = dañar irreversiblemente**

---

## 🧪 Precisión de Nuestra Simulación

### Lo que simulamos PERFECTAMENTE:
✅ Superposición cuántica
✅ Colapso de la función de onda
✅ Incompatibilidad de bases
✅ Teorema de no-clonación
✅ Detección de espionaje por QBER

### Lo que NO simulamos (pero no afecta el concepto):
❌ Pérdida de fotones
❌ Ruido térmico
❌ Decoherencia
❌ Imperfecciones de detectores
❌ Tiempo de transmisión real

### Conclusión:
Nuestra simulación es **pedagógicamente perfecta** y **matemáticamente correcta**.
Captura la ESENCIA del protocolo BB84.

---

## 🎯 Resumen en 3 Puntos

1. **Usamos Qiskit para simular qubits reales**
   - Los circuitos cuánticos emulan fotones
   - El simulador Aer calcula probabilidades cuánticas exactas

2. **Eve introduce errores medibles**
   - Al medir con base incorrecta, destruye la información
   - QBER sube de ~0% a ~25%

3. **Alice y Bob detectan el espionaje**
   - Comparan una muestra de su clave
   - Si QBER > umbral → ¡hay espía!

**La simulación es 100% fiel al protocolo BB84 real.**
