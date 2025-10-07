# TODO List - Q-Sec TPI

## ✅ COMPLETADO (Base Sólida)

### Arquitectura
- [x] Estructura de 3 capas correctamente separada
- [x] Capa de Datos con repositorios
- [x] Capa de Negocio con controladores
- [x] Capa de Presentación con rutas Flask
- [x] Base de datos SQLite funcionando

### Funcionalidades Base
- [x] Sistema de registro de usuarios
- [x] Sistema de login/logout
- [x] Dashboard con estadísticas
- [x] Historial de simulaciones
- [x] Contraseñas hasheadas (seguridad)
- [x] Frontend completo con Bootstrap 5
- [x] Diseño responsive

---

## 🚧 EN PROGRESO

### 1. Simulación BB84 con Qiskit (80% completo)
**Archivo:** `business/bb84_simulation.py`

**✅ Ya implementado:**
- Generación de bits y bases aleatorias
- Codificación de qubits
- Interceptación de Eve
- Medición de qubits
- Comparación de bases
- Cálculo de QBER
- Detección de espionaje

**❓ Falta probar:**
- [ ] Ejecutar una simulación real y verificar resultados
- [ ] Ajustar umbral de error si es necesario
- [ ] Verificar que Qiskit funciona correctamente

---

## ❌ PENDIENTE (Priorizado)

### 2. Página de Resultados Detallados (ALTA PRIORIDAD)
**Ubicación:** `templates/simulation_result.html` + ruta en `views/routes.py`

**Crear:**
- [ ] Template para mostrar resultados paso a paso
- [ ] Visualización de:
  - [ ] Bits de Alice y Bob
  - [ ] Bases utilizadas (mostrar cuáles coincidieron)
  - [ ] Tasa de error (QBER) con gráfico
  - [ ] Clave final (si es segura)
  - [ ] Mensaje de detección de Eve
- [ ] Actualizar ruta `simulation_result()` en routes.py

### 3. Tests Unitarios con Pytest (MEDIA PRIORIDAD)
**Ubicación:** `tests/`

**Crear tests para:**
- [ ] `test_auth_controller.py` - Probar registro, login, validaciones
- [ ] `test_simulation.py` - Probar simulación BB84
- [ ] `test_repositories.py` - Probar acceso a datos
- [ ] Ejecutar: `pytest tests/`

### 4. Documentación (ALTA PRIORIDAD para entregar)
**Archivos a completar:**

- [ ] **PROYECTO.md**:
  - [ ] Agregar imagen del Modelo de Dominio (diagrama ER)
  - [ ] Agregar imagen de Arquitectura en 3 capas
  - [ ] Verificar que todo esté actualizado

- [ ] **README.md**:
  - [ ] Instrucciones de instalación
  - [ ] Cómo ejecutar el proyecto
  - [ ] Capturas de pantalla
  - [ ] Tecnologías usadas

### 5. Deployment (OBLIGATORIO)
**¡CRÍTICO! El proyecto debe estar online, no en localhost**

**Opciones recomendadas:**
- [ ] **Render.com** (Gratis, fácil)
- [ ] **PythonAnywhere** (Gratis, para Python)
- [ ] **Railway.app** (Fácil, con free tier)
- [ ] **Heroku** (Con cuenta verificada)

**Pasos:**
1. [ ] Crear `Procfile` para el servidor web
2. [ ] Actualizar `requirements.txt`
3. [ ] Configurar variables de entorno en la plataforma
4. [ ] Desplegar
5. [ ] Probar que funciona online

### 6. Mejoras Opcionales (Si hay tiempo)
- [ ] Gráficos de estadísticas con Chart.js
- [ ] Exportar resultados a PDF
- [ ] Modo oscuro
- [ ] Internacionalización (español/inglés)
- [ ] Tutorial interactivo de BB84
- [ ] Animaciones del protocolo

---

## 📋 Checklist de Entrega Final

### Requisitos Obligatorios
- [ ] ✅ Arquitectura de 3 capas correctamente implementada
- [ ] ✅ Sistema funcional de registro y login
- [ ] ⚠️ Simulación BB84 completa con Qiskit (PROBAR)
- [ ] ❌ Página de resultados detallados
- [ ] ❌ Proyecto desplegado online (NO localhost)
- [ ] ✅ Contraseñas hasheadas
- [ ] ✅ Base de datos SQL (SQLite)
- [ ] ✅ Control de versiones (Git)
- [ ] ❌ Diagramas en PROYECTO.md
- [ ] ❌ README.md completo

### Requisitos Opcionales (Suman puntos)
- [ ] ❌ Tests unitarios con Pytest
- [ ] ✅ Frontend con framework (Bootstrap 5)
- [ ] ✅ Diseño responsive

---

## 🎯 Plan de Acción Sugerido

### Semana 1-2 (Lo más importante)
1. **Probar simulación BB84** - Ejecutar y verificar que funciona
2. **Crear página de resultados** - Mostrar el output de la simulación
3. **Documentación básica** - README y diagramas

### Semana 3
4. **Tests unitarios** - Al menos para la simulación
5. **Pulir frontend** - Mejorar visualización de resultados

### Semana 4 (CRÍTICO)
6. **DEPLOYMENT** - Subir a Render/PythonAnywhere
7. **Documentación final** - Completar PROYECTO.md
8. **Testing final** - Probar todo online

---

## 📝 Notas Importantes

1. **La simulación BB84 YA ESTÁ implementada** en `bb84_simulation.py`, solo falta probarla
2. **El deployment es OBLIGATORIO** - no puede quedar en localhost
3. **Los diagramas son importantes** - usa draw.io o similar
4. **El checklist_capas.md ya se cumple** - la arquitectura está bien

## 🚀 Próximo Paso Inmediato

**AHORA MISMO:** Probar que la simulación BB84 funciona:

1. Registrarse en la aplicación
2. Ir al simulador
3. Ejecutar una simulación con y sin Eve
4. Ver si muestra resultados en el dashboard/historial
5. Si funciona, crear la página de resultados detallados
