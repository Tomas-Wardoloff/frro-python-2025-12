# Q-Sec: Simulador Interactivo del Protocolo de Criptografía Cuántica BB84

Este es un archivo que debe completarse con los datos utilizados en el TPI. Este archivo puede modificarse en el tiempo, no obstante siempre debe mantenerse en un estado consistente con el desarrollo.

**Importante:** Este archivo debe mantenerse en formato Markdown (.md) y sólo se tendrá en cuenta la versión disponible en GIT.

## Descripción del proyecto

En un mundo cada vez más digital, la seguridad en las comunicaciones es fundamental. La criptografía cuántica surge como una solución a las amenazas que las computadoras cuánticas representan para los sistemas criptográficos actuales como RSA, ofreciendo una seguridad garantizada por las propias leyes de la física.

**Q-Sec** es un sistema web educativo que simula el protocolo de Distribución Cuántica de Claves (QKD) **BB84**. El objetivo principal es desmitificar la criptografía cuántica, permitiendo a los usuarios ejecutar una simulación paso a paso, visualizar los resultados y entender empíricamente cómo la mecánica cuántica hace posible una comunicación segura y la detección de intrusos. El sistema proporcionará una herramienta interactiva para explorar los conceptos de la criptografía cuántica en un entorno de software robusto y funcional.

## Modelo de Dominio

![Diagrama de Modelo de Dominio](MD.png)
El modelo de dominio se centra en dos entidades principales:

*   **Usuario**: Representa a la persona que utiliza el simulador. Almacena información de autenticación como el nombre de usuario y la contraseña hasheada.
*   **SesionIntercambio**: Almacena el resultado de cada simulación ejecutada por un usuario. Contiene los parámetros de la simulación (longitud de la clave, presencia de un espía "Eve"), el resultado (si la clave fue segura o comprometida) y la clave final generada (si aplica). Cada sesión está asociada a un único usuario.

## Bosquejo de Arquitectura

![Diagrama de Arquitectura](diagrams/architecture.png)

El sistema está diseñado bajo una estricta **arquitectura de 3 capas** para separar responsabilidades y mejorar la mantenibilidad:

1.  **Capa de Presentación**: Construida con el framework **Flask**, se encarga de renderizar la interfaz de usuario web, gestionar las peticiones HTTP y mostrar los resultados de la simulación. Es el punto de entrada para el usuario.
2.  **Capa de Negocio**: Implementada en Python, contiene toda la lógica central del proyecto. Utiliza la librería **Qiskit** de IBM para simular la preparación, transmisión y medición de qubits, aplicando los principios del protocolo BB84. Aquí también se implementan las reglas de negocio, como la detección de espionaje basada en la tasa de error cuántico, y se valida con tests unitarios usando **Pytest**.
3.  **Capa de Datos**: Gestiona la persistencia de la información. Utiliza el ORM **SQLAlchemy** para mapear los objetos de negocio a una base de datos **SQLite**. Se encarga de almacenar y recuperar los datos de los usuarios y los resultados de las sesiones de intercambio.

## Requerimientos

### Funcionales

*   **RF01**: El sistema debe permitir el registro y autenticación de usuarios.
*   **RF02**: Un usuario autenticado debe poder iniciar una nueva "Sesión de Intercambio de Clave".
*   **RF03**: Al iniciar una sesión, el usuario debe poder configurar sus parámetros: la longitud de la clave inicial (ej. 64 bits) y si desea incluir un espía ("Eve") en la simulación.
*   **RF04**: El sistema debe ejecutar la simulación del protocolo BB84 completo:
    *   a. Generación de bits y bases aleatorias por parte de Alice.
    *   b. Codificación de los bits en qubits usando Qiskit.
    *   c. (Opcional) Interceptación y reenvío de qubits por parte de Eve.
    *   d. Generación de bases aleatorias y medición de qubits por parte de Bob.
    *   e. Comparación pública de bases para filtrar la clave.
    *   f. Verificación de la tasa de error para detectar a Eve.
*   **RF05**: El sistema debe almacenar en la base de datos el resultado de cada sesión: la configuración, si la clave fue segura o comprometida, y la clave final (si es segura).
*   **RF06**: El usuario debe poder ver un historial de sus sesiones de intercambio pasadas con sus resultados.

### No Funcionales

#### Portability

**Obligatorios**
- [X] El sistema debe funcionar correctamente en múltiples navegadores (Sólo Web).

#### Security

**Obligatorios**
- [X] Todas las contraseñas deben guardarse con encriptado criptográfico (SHA o equivalente). Se utilizará la librería `Werkzeug.security` para el hasheo de contraseñas.
- [X] Todas los Tokens / API Keys o similares no deben exponerse de manera pública.

#### Maintainability

**Obligatorios**
- [X] El sistema debe diseñarse con la arquitectura en 3 capas. (Ver [checklist_capas.md](checklist_capas.md))
- [X] El sistema debe utilizar control de versiones mediante GIT.
- [X] El sistema debe estar programado en Python 3.9 o superior.

#### Scalability

**Obligatorios**
- [X] El sistema debe funcionar desde una ventana normal y una de incógnito de manera independiente (Sólo Web). Se gestionará el estado del usuario mediante el sistema de sesiones de Flask, que utiliza cookies seguras.

#### Performance

**Obligatorios**
- [X] El sistema debe funcionar en un equipo hogareño estándar. La simulación completa para una clave de 128 bits debe finalizar en menos de 30 segundos.

#### Flexibility

**Obligatorios**
- [X] El sistema debe utilizar una base de datos SQL o NoSQL. Se utilizará una base de datos SQL (SQLite).

## Stack Tecnológico

### Capa de Datos

*   **Base de Datos: SQLite**
    *   *Razón*: Se eligió SQLite por su simplicidad y portabilidad. Al ser una base de datos serverless que se almacena en un único archivo, es ideal para un proyecto de esta escala, eliminando la necesidad de configurar un servidor de base de datos separado.
*   **ORM: SQLAlchemy**
    *   *Razón*: SQLAlchemy es un ORM potente y flexible que permite interactuar con la base de datos utilizando objetos de Python, lo que abstrae las consultas SQL y facilita la gestión de los datos de manera orientada a objetos, alineándose con el diseño del resto del sistema.

### Capa de Negocio

*   **Simulación Cuántica: IBM Qiskit**
    *   *Razón*: Qiskit es el framework de código abierto líder para la computación cuántica. Proporciona las herramientas necesarias para crear y manipular circuitos cuánticos, lo que lo hace perfecto para simular con precisión la preparación, transmisión y medición de qubits según el protocolo BB84.
*   **Testing: Pytest**
    *   *Razón*: Se seleccionó Pytest por su sintaxis simple y su potente motor de descubrimiento y ejecución de pruebas. Es fundamental para validar que las reglas de negocio, como el cálculo de la tasa de error y la detección de espionaje, funcionen correctamente.

### Capa de Presentación

*   **Framework Web: Flask**
    *   *Razón*: Flask es un microframework web ligero, modular y fácil de aprender. Ofrece la flexibilidad necesaria para construir la aplicación web sin imponer una estructura rígida, lo cual es ideal para este proyecto. Permite un desarrollo rápido de la interfaz de usuario y la gestión de rutas.