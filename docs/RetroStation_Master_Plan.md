# RetroStation — Documento maestro del proyecto

> **Fuente de conocimiento canónica para los futuros chats y el repositorio.**<br>
> Versión: **0.2.2** · Fecha de actualización: **4 de noviembre de 2026**<br>
> Estado: **Windows 11 elegido para primer prototipo; interfaz con mando, uso sin conexión e inventario de seguridad pendientes**<br>
> Mantenimiento: evolucionará con decisiones técnicas, pruebas, incidencias y cambios de alcance.

---

## 0. Cómo utilizar este documento

**Para un chat nuevo:** adjuntar `RetroStation_Master_Plan.md` como archivo o fuente del Proyecto de ChatGPT y pedir: «Lee íntegramente el documento maestro de RetroStation. Distingue decisiones tomadas de propuestas, consulta el estado y continuemos desde el siguiente paso pendiente». Un Proyecto de ChatGPT y una carpeta de Biblioteca son cosas distintas: guardar un documento en Biblioteca **no lo incorpora automáticamente** a las fuentes del Proyecto.

**Para el repositorio:** este archivo es la única versión de referencia en `docs/RetroStation_Master_Plan.md`; versionarlo mediante Git y sincronizar deliberadamente cualquier copia añadida a ChatGPT. No asumir sincronización automática entre GitHub, Biblioteca y fuentes del Proyecto.

**Reglas para actualizarlo:**
1. Registrar cambios significativos con fecha, versión y motivo en el historial (sección 17).
2. Distinguir **[CONFIRMADO]**, **[PROPUESTA]**, **[PENDIENTE]**, **[VALIDADO]** y **[DESCARTADO]**.
3. Una prueba real del ASUS tiene prioridad frente a una predicción de rendimiento teórica.
4. Registrar riesgos y limitaciones, y no eliminar preguntas abiertas sin resolverlas.
5. Mantener el alcance de cada sprint pequeño; preservar el aprendizaje activo del usuario.

---

## 1. Visión y filosofía

**RetroStation** es una **aplicación propia** para reunir la biblioteca y el lanzamiento de emuladores existentes de distintas consolas bajo una experiencia unificada. El ASUS ROG Strix G será el primer equipo de prueba: debe funcionar de forma estable, sin conexión durante el juego y con navegación mediante mando. El núcleo se diseñará sin rutas específicas de ese portátil; la experiencia de interfaz propia se construirá por etapas, sin desarrollar los motores de emulación.

### Objetivos primarios [CONFIRMADO]

- Ejecutar **el mayor número de títulos compatible con el hardware de manera fluida y estable**; no confundir tamaño de catálogo con compatibilidad real.
- Permitir ampliar la biblioteca incorporando progresivamente copias legales de juegos.
- Navegar por la interfaz propia tipo consola/Steam Big Picture, preferiblemente con el mando sin tocar teclado o ratón **dentro de la interfaz**.
- Mostrar al menos carátulas; priorizar agilidad y funcionalidad sobre efectos gráficos superfluos.
- Operar sin conexión a Internet una vez preparado: juego, biblioteca local y metadatos previamente descargados.
- Utilizar la pantalla integrada porque el HDMI del portátil está averiado.
- Usar DualShock 4 y admitir en el futuro varios mandos para multijugador local.
- Presupuesto **0 € inicialmente** y uso del almacenamiento externo disponible de **2 TB**.
- **No** borrar Windows 11 ni instalar otro sistema operativo sin una decisión razonada y una copia de seguridad verificada.

### Objetivos de ingeniería y aprendizaje [CONFIRMADO]

- Proceso realista: descubrimiento, requisitos, decisiones técnicas, pruebas, documentación, mantenimiento y evolución.
- Aprender de forma práctica Python, automatización, Bash, Git/GitHub, bases de datos y conceptos de sistemas.
- Partir de software consolidado; **no desarrollar un emulador desde cero**.
- Desarrollar desde el inicio un núcleo Python propio que reúna configuraciones de sistemas y emuladores; ampliar después catálogo, lanzamiento, interfaz y automatizaciones según pruebas reales.
- Trabajar varias horas por semana, sin calendario rígido ni fechas inventadas.
- Usar Git y GitHub desde el primer día.
- Aspiración a compartir el repositorio para que otras personas puedan aprender o reutilizar las herramientas.

### Estilo de colaboración [CONFIRMADO]

El asistente **enseña, guía y revisa**, no sustituye el aprendizaje: explicar el propósito de comandos y archivos, proponer ejercicios, dejar al usuario ejecutar, razonar errores y justificar elecciones. No entregar soluciones completas automáticamente cuando la finalidad de una etapa sea practicar. Preguntar lo imprescindible; aprovechar todo lo ya decidido.

---

## 2. Inventario técnico inicial

| Componente | Estado confirmado |
|---|---|
| Equipo | ASUS ROG Strix G (submodelo exacto todavía por identificar) |
| CPU | Intel Core i7-9750H @ 2,60 GHz (6 núcleos/12 hilos) |
| RAM | 16 GB DDR4 |
| Gráfica integrada | Intel UHD Graphics 630 |
| Gráfica dedicada | NVIDIA GeForce GTX 1650 |
| Almacenamiento interno | SSD Micron 2200V, `Micron_2200V_MTFDHBA512TCK`, 512.110.190.592 bytes físicos; volumen C: NTFS con 121,3 GiB libres de 475,7 GiB |
| Almacenamiento externo | Unidad de 2 TB declarada como disponible, pero **no aparecía conectada/detectada** en `Get-Disk` del 17/10/2026; comprobar conexión y formato |
| Sistema operativo | Windows 11 actualmente; particionado GPT confirmado en disco 0 |
| Pantalla | Integrada, uso principal |
| HDMI | Averiado, **no planificar TV por HDMI como requisito** |
| Mandos | 1 DualShock 4 disponible; varios mandos deseables |
| Presupuesto | 0 € en la etapa inicial |

### Comprobaciones verificadas el 17/10/2026

- `Get-Disk` muestra solo un disco físico (disco 0, Micron 2200V, 512 GB, GPT).
- `Get-Volume` muestra C: NTFS (510.822.518.784 bytes; 130.259.333.120 libres, aproximadamente 121,3 GiB). El disco externo de 2 TB no aparece en este diagnóstico; **no asumir avería** sin comprobar si estaba conectado.
- `git --version`: 2.47.1.windows.2 (Git disponible).
- `py --version` no se reconoce, **pero `python --version` confirma Python 3.11.9 funcionando**. `Get-Command` devuelve `python.exe` y `python3.exe`; no hace falta instalar Python por este motivo. El lanzador `py` es opcional. Para decidir cómo crear entornos virtuales, conviene comprobar `python -m pip --version` y `python -c "import sys; print(sys.executable)"`.
- `nvidia-smi`: driver 555.97, CUDA indicado 12.5, GTX 1650 con 4096 MiB de VRAM, modo WDDM. Primera medición: **74 °C**, 5 W, ~2 % de uso, estado P8; segunda medición a las 18:28: **70 °C**, 5 W, ~3 % de uso, P8, 287 MiB de VRAM en uso. Una temperatura sostenida así con baja carga merece investigar perfiles de ventilación en Armoury Crate, polvo y temperatura CPU antes de estrés prolongado; no demuestra avería. La segunda lista ya no incluye MuMuPlayer.
- En la lista de procesos de NVIDIA figuraba MuMuPlayer además de navegador y otros procesos, posible interferencia en pruebas.

### Datos pendientes de inventario

- Versión exacta de Windows y BIOS/UEFI (driver NVIDIA 555.97 ya identificado).
- Capacidad útil y espacio libre de SSD interno y unidad externa.
- Salud y velocidades de unidades, y tipo de conexión de la unidad de 2 TB.
- Resolución/Hz de la pantalla integrada, temperaturas, ventilación y ruido.
- Bluetooth del portátil, estado del DualShock 4, y posibilidad real de conectar dos mandos.
- Copia de seguridad de datos relevantes y estado general del sistema.
- Submodelo ASUS / modelo de placa / estado de batería; no registrar seriales ni información identificativa en repositorios públicos.

**Expectativa, no promesa:** la CPU/GPU deberían ofrecer margen amplio para PS1, N64, PSP, Dreamcast, GameCube/Wii y buena parte de PS2; 3DS/Wii U/PS Vita dependen de título, emulador, controladores, drivers y configuración. La verificación siempre será juego a juego.

---

## 3. Requisitos funcionales

Identificadores para referencias en issues, pruebas y commits:

| ID | Requisito | Prioridad | Situación |
|---|---|---|---|
| RF-01 | Biblioteca local que detecte e identifique juegos y plataformas | Alta | Por diseñar |
| RF-02 | Ejecutar juegos con emuladores existentes, con configuración por sistema/juego | Alta | Por probar |
| RF-03 | Interfaz propia cómoda con navegación mediante DualShock 4 | Alta | Por diseñar y probar |
| RF-04 | Volver a la interfaz propia y cerrar cada emulador sin teclado en el flujo normal | Alta | Por probar |
| RF-05 | Usar juegos offline después de la preparación | Alta | Por validar |
| RF-06 | Carátulas y descripciones descargables y cacheadas para uso offline | Alta | Por diseñar |
| RF-07 | Configurar resolución/controles por título si hace falta | Alta | Por diseñar |
| RF-08 | Organizar catálogo por sistema, búsqueda, favoritos y filtros | Media | Por diseñar |
| RF-09 | Guardados nativos, save states donde sean compatibles, copias de seguridad y restauración | Alta | Por diseñar |
| RF-10 | Importar nuevos títulos progresivamente sin rehacer la instalación | Alta | Por diseñar |
| RF-11 | Soporte para dos o más mandos y multijugador local en sistemas compatibles | Media | Por probar |
| RF-12 | Juegos de PC nativos o por capas de compatibilidad como opción futura, no prioritaria | Baja | Pendiente |
| RF-13 | Exportación/importación de biblioteca, metadatos y partidas | Media | Pendiente |
| RF-14 | Automatizaciones de inventario, verificación, backups y configuración | Media | Pendiente |

**Notas:**
- RetroArch agrupa *cores* y ofrece una interfaz/CLI; **no aumenta la potencia del equipo** ni sustituye todos los emuladores independientes.
- «Emular un juego de PC» no es necesariamente la expresión correcta: los juegos Windows se ejecutan nativamente en Windows o, en Linux, mediante herramientas como Wine/Proton cuando proceda.
- «Controlable por mando» se aplica de entrada al flujo normal de uso; mantenimiento, instalación y depuración pueden requerir teclado.
- Carátulas/metadatos automáticos probablemente **requieran Internet durante la importación inicial**. El modo offline se logra tras almacenar lo necesario localmente.

## 4. Requisitos no funcionales y criterios de calidad

- **RNF-01 Estabilidad:** priorizar tiempos de juego sostenidos sin fallos ni audio entrecortado. No declarar compatible un juego solo porque arranca.
- **RNF-02 Rendimiento:** medir velocidad de emulación, FPS objetivo del juego, audio, compilación de shaders, carga CPU/GPU, temperatura y consumo cuando sea pertinente.
- **RNF-03 Experiencia:** acceso y regreso a la interfaz propia claros; tiempo de arranque razonable y funcionalidad offline.
- **RNF-04 Portabilidad:** scripts y núcleo Python separados de rutas específicas del SO; adaptadores para Windows y Linux; sin prometer soporte multiplataforma antes de probarlo.
- **RNF-05 Reproducibilidad:** dependencias, versiones, rutas configurables y decisiones documentadas.
- **RNF-06 Seguridad de datos:** no sobrescribir partidas, bibliotecas o carpetas sin confirmación y copia; salvaguardar ficheros personales antes de particionar/formatear.
- **RNF-07 Mantenibilidad:** módulos pequeños, pruebas automáticas de componentes propios, diagnósticos legibles y control de versiones.
- **RNF-08 Legalidad:** no suministrar, distribuir ni subir a GitHub ROMs, BIOS protegidas, claves o firmware de terceros sin derechos; trabajar con homebrew, juegos libres o volcados/autorizaciones legalmente obtenidos.

---

## 5. Plataformas, emuladores candidatos y prioridades

La tabla es de **candidatos que habrá que instalar/probar**, no una declaración de compatibilidad garantizada de todos sus juegos ni una decisión definitiva del stack.

| Sistemas deseados [CONFIRMADO] | Soluciones candidatas [PROPUESTA] | Prioridad / observación |
|---|---|---|
| NES, SNES, Mega Drive, GB, GBC, GBA, otros 8/16-bit | RetroArch + cores adecuados | Primera tanda: robustos, ideales para flujo de uso |
| Arcade, Neo Geo | RetroArch + FBNeo/MAME según juego y set | Compatibilidad ligada a versiones correctas de ROM sets |
| PlayStation 1 | RetroArch (DuckStation/SwanStation/Beetle según disponibilidad); DuckStation independiente | Primera tanda con juego objetivo |
| Nintendo 64 | RetroArch o emulador específico compatible | Primera tanda con juego objetivo |
| Dreamcast / Saturn | Flycast / RetroArch; Mednafen/Beetle Saturn, otros | Probar por juego, BIOS cuando corresponda |
| PSP | PPSSPP | Prioridad media-alta |
| Nintendo DS | melonDS y alternativas mantenidas | Considerar disposición de doble pantalla |
| Nintendo 3DS | Azahar | Prioridad media; Pokémon Ultra Sol/Luna como prueba importante |
| GameCube / Wii | Dolphin | Prioridad media-alta, incluido mapeo de Wii |
| Wii U | Cemu | Etapa posterior; soporte nativo Windows/Linux, dependiente del título |
| PlayStation 2 | PCSX2 | Prioridad media-alta; juego/BIOS y ajustes según caso |
| PS Vita | Vita3K | **Experimental**; evaluar compatibilidad título por título sin garantizarla |

### Juegos objetivo definidos [CONFIRMADO]

1. **Castlevania: Symphony of the Night** (PS1): prueba de carga, audio, botones, guardado y regreso al menú.
2. **Super Mario 64** (Nintendo 64): prueba de joystick analógico y latencia.
3. **Pokémon Ultrasol / Ultraluna** (Nintendo 3DS): prueba de un sistema relativamente exigente, doble pantalla, shaders, rendimiento sostenido y compatibilidad.

**Sugerencia:** iniciar con homebrew o contenido libre compatible y añadir los juegos objetivo cuando existan copias adecuadas obtenidas legítimamente. Registrar el origen/autorización sin guardar material protegido en Git.

### Matriz de pruebas por juego

Registrar `sistema`, `juego`, `región/versión`, `origen legal`, `emulador + versión`, `backend gráfico`, `resolución interna`, `mando`, `FPS/velocidad`, `audio`, `temperatura`, `tiempo de sesión`, `save/load`, `regreso al menú`, `fallos` y `veredicto` (`no probado`, `arranca`, `jugable con problemas`, `estable`, `incompatible`). **Estable** requiere probar una sesión real y guardar/cargar, no solo la pantalla inicial.

---

## 6. Decisiones cerradas, propuestas y preguntas abiertas

### Confirmadas

- Modelo de uso: portátil con pantalla integrada, HDMI no funcional.
- Sin compras en el inicio; existe unidad externa de 2 TB.
- Windows 11 es el punto de partida, **sin consentimiento para formatear**.
- Preferencia personal por experimentar con un Linux generalista y una capa de emulación personalizable.
- Capa propia idealmente reutilizable en varios SO, si resulta viable.
- Lenguajes y herramientas de interés: **Python**, **Bash**, SQLite, Git, GitHub y automatización. No usar Java como lenguaje principal.
- Calidad/estabilidad antes que escalado gráfico o filtros.
- Interfaz funcional, rápida, con carátulas y control por mando.
- Juego offline; biblioteca ampliable; backups/transferencia de guardados.
- Git/GitHub desde el principio; trabajo colaborativo y didáctico; horas semanales.

### Plataforma del primer prototipo y propuestas restantes

- **[CONFIRMADO]** Usar **Windows 11 actual para el primer prototipo no destructivo**; quedan pendientes mando, regreso al menú y uso sin conexión. Comparar después Linux generalista mediante prueba LiveUSB/instalación de ensayo o sistema independiente solo con copia verificada y autorización.
- **[CONFIRMADO]** La experiencia unificada será una aplicación propia que utilice emuladores existentes; no se desarrollarán motores de emulación. **[PROPUESTA]** Usar ES-DE, Playnite o RetroBat únicamente como referencias de experiencia y comparación, sin depender de ellos como interfaz principal.
- **[PROPUESTA]** Aprovechar inicialmente **Python 3.11.9 confirmado en Windows** (sin actualizar por actualizar); SQLite para el catálogo; TOML/YAML para configuración; `pytest` para pruebas cuando haya código; Bash en Linux y PowerShell bajo Windows. Elevar la versión solo si una dependencia concreta lo exige.
- **[PROPUESTA]** Mantener los ejecutables/emuladores en el SSD interno y guardar biblioteca/medios en la unidad de 2 TB si su salud y velocidad lo permiten. La ubicación definitiva de metadatos y guardados dependerá de pruebas de desconexión, respaldo y portabilidad.
- **[PROPUESTA]** Repositorio con scripts y configuración, pero **sin juegos, BIOS, firmware, credenciales, partidas privadas ni ficheros grandes**.

### Pendientes que condicionan arquitectura

1. ¿Mantener Windows, dual boot, Linux generalista como sistema principal o un sistema externo? No decidir hasta inventario + prototipo.
2. ¿Qué distribución Linux y qué solución NVIDIA se probaría? Validar compatibilidad de la GTX 1650 híbrida e integrada.
3. ¿Cuál es la ruta definitiva del almacenamiento de 2 TB, sistema de archivos y estrategia de montaje en ambos SO?
4. ¿Qué biblioteca de interfaz permite a la aplicación propia navegar con DualShock 4 y cerrar cada emulador? Elegirla tras probar alternativas y requisitos de la primera interfaz.
5. ¿Cómo gestionar BIOS y firmware propios cuando legalmente necesarios?
6. ¿Dónde residen las partidas y qué alcance tendrá la sincronización? No asumir que save states de emuladores distintos son portables.
7. ¿Cómo publicar el código? Nombre de usuario/organización, visibilidad del repositorio y licencia, cuando llegue el momento.
8. ¿Qué sistemas exigentes rinden aceptablemente en el ASUS real?

---

## 7. Arquitectura conceptual (evolutiva)

```text
                     ┌──────────────────────────┐
                     │  Interfaz RetroStation   │
                     │  propia, mando (futura)  │
                     └────────────┬─────────────┘
                                  │ juegos / acciones
                     ┌────────────▼─────────────┐
                     │  Núcleo RetroStation     │
                     │  (Python; CLI inicial)   │
                     └──┬─────────┬───────────┬─┘
                        │         │           │
                 ┌──────▼──┐ ┌────▼────┐ ┌────▼────────┐
                 │ Catálogo│ │ Lanzador│ │ Herramientas│
                 │ SQLite  │ │/adapters│ │ metadata /  │
                 │         │ │ por SO   │ │ backup/diag │
                 └────┬────┘ └────┬────┘ └────┬────────┘
                      │           │           │
               ┌──────▼───────────▼───────────▼────────┐
               │  ROMs legítimas / assets / saves       │
               │  SSD + almacenamiento externo 2 TB    │
               └────────────────────────────────────────┘
                                  │
                     ┌────────────▼───────────────┐
                     │ Emuladores existentes      │
                     │ RetroArch, Dolphin, etc.  │
                     └────────────────────────────┘
```

**Importante:** el núcleo y la CLI son cortes iniciales de **la aplicación propia**, no su interfaz final. `systems` enumera perfiles y `preview` genera argumentos sin ejecutar procesos; `launch --confirm` inicia un emulador externo desde un perfil privado con archivos fuera de Git. El usuario observó que el juego y la partida se cargaron desde la aplicación usando copias aisladas; esto no acredita una sesión estable, mando ni uso sin conexión. Catálogo SQLite e interfaz con mando siguen pendientes. Véase la [matriz de pruebas](test-matrix.md).

### Separación de responsabilidades

- **Interfaz propia:** navegación, búsqueda, carátulas, selección de juego y acciones del usuario; biblioteca gráfica por decidir.
- **Emuladores:** ejecución, renderizado, asignación de controles y guardados específicos.
- **Configuración:** rutas, perfiles por sistema/juego y parámetros de lanzamiento.
- **Núcleo en Python:** perfiles de consolas/emuladores desde el inicio; después importación incremental, base de datos, verificación y automatización.
- **Adaptadores por plataforma:** Windows/Linux; no codificar rutas absolutas de un equipo en el núcleo.
- **Almacenamiento:** separar ROMs, BIOS, assets, metadatos, logs, estado y backups. Nunca asumir que una única unidad externa equivale a una copia de seguridad.

### Propuesta de directorios del futuro repositorio

```text
retrostation/
├── README.md
├── LICENSE                # pendiente de elegir
├── .gitignore
├── pyproject.toml          # pendiente: empaquetado del núcleo Python
├── docs/
│   ├── RetroStation_Master_Plan.md
│   ├── decisions/          # ADR (Architecture Decision Records)
│   ├── test-matrix.md
│   └── setup/
├── src/retrostation/       # núcleo Python iniciado
├── tests/                  # pruebas del núcleo
├── scripts/
├── config/examples/       # ejemplos SIN rutas personales ni secretos
└── .github/               # CI/issues cuando convenga
```

**Datos que nunca deben subirse al repositorio:** carpetas de ROMs, imágenes de disco protegidas, BIOS/firmware, claves, archivos de cuentas, datos personales, partidas de terceros, bases locales pobladas, logs sensibles, descargas de carátulas con licencias incompatibles.

### Esbozo de almacenamiento separado del código

```text
RetroStationLibrary/         # ubicación real por acordar, NO en Git
├── roms/<sistema>/
├── bios/                    # privado, cuando corresponda
├── artwork/
├── metadata/
├── saves/
└── backups/
```

Guardar copias críticas en **otro soporte distinto** del que aloja los originales siempre que sea posible. Documentar mapa de rutas y no copiar el esquema a ciegas sobre carpetas existentes.

---

## 8. Alternativas de plataforma (sin elección definitiva)

| Enfoque | Ventajas | Riesgos / costes de aprendizaje | Estado |
|---|---|---|---|
| Windows 11 + RetroStation + emuladores | No destructivo, acceso inmediato a drivers y software | Integración propia de mandos y cierre aún por construir | Primer prototipo elegido; flujo con mando y offline por validar |
| Windows 11 + ES-DE / Playnite / RetroBat | Referencias de experiencia, no aplicación objetivo | No prueban por sí solas la interfaz propia | Comparación opcional |
| Linux generalista + RetroStation + emuladores | Aprendizaje Linux, Bash, proyecto portable | Drivers NVIDIA híbridos, mandos, permisos, particionado, montaje | Preferencia del usuario, por validar |
| Batocera en soporte separado | Banco de pruebas de experiencia consola | No sustituye el desarrollo de RetroStation | Alternativa de evaluación |
| Reinstalar/dual boot directamente | Flexibilidad o experiencia dedicada | Riesgo de pérdida de datos y arranque, mantenimiento adicional | **No autorizado ni prioritario** |

**ADR-001:** Windows 11 actual elegido para el primer prototipo; biblioteca de interfaz y SO final pendientes. No se ha autorizado cambiar particiones ni instalar otro sistema. Quedan por verificar control por mando, regreso al menú, uso sin conexión y copia independiente antes de experimentar con otro SO.

---

## 9. Roadmap por fases, entregables y puertas de salida

### Fase 0 — Fundación y diagnóstico [SIGUIENTE]

**Objetivo:** tener repositorio Git, inventario verificado y estrategia segura de pruebas.

**Entregables:**
- Repositorio local Git y GitHub (cuando el usuario autorice conexión/publicación); README + documento maestro + `.gitignore`.
- Inventario CPU/GPU/RAM/unidades/controladores; comprobar disponibilidad real de SSD/unidad externa.
- Mapa de datos a proteger; elección documentada de dónde guardar pruebas.
- ADR-001: Windows 11 elegido para el primer prototipo; interfaz y SO final abiertos, sin borrar Windows.

**Criterio de salida:** se puede repetir el diagnóstico sin riesgo; documentación en Git, sin archivos protegidos.

### Fase 1 — Aplicación propia y prueba mínima de emulación (vertical slice)

**Objetivo:** construir el núcleo propio que unifique perfiles de emuladores y, cuando existan configuración e interfaz verificadas, ejecutar **un** juego homebrew/libre o legítimamente obtenido con mando y volver al menú, sin Internet durante el juego.

**Entregables:**
- Núcleo Python probado que identifica sistemas/emuladores configurados; después interfaz propia evaluada, un emulador configurado y perfil del DualShock 4.
- Lanzamiento/cierre documentado; resultado de prueba y posibles errores.
- Primera matriz de compatibilidad.

**Criterio de salida:** hito principal de encender, navegar con mando, jugar y regresar al menú sin conexión de red.

### Fase 2 — Biblioteca y compatibilidad escalonada

**Objetivo:** ampliar sistemas de menor a mayor exigencia.

**Orden sugerido:** 8/16 bits → PS1/N64 → Dreamcast/PSP/DS → PS2/GameCube/Wii → 3DS/Wii U → Vita (experimental).

**Entregables:**
- Matriz documentada; perfiles por emulador, mandos y guardados.
- Pruebas con los juegos objetivo cuando se disponga de copias legítimas.
- Criterios para decidir qué plataformas incluir permanentemente.

**Criterio de salida:** cada sistema activado tiene al menos una prueba reproducible estable o una limitación documentada.

### Fase 3 — Ampliación de biblioteca y metadatos

**Objetivo:** importar progresivamente títulos, deduplicar de forma segura, mostrar carátulas y trabajar offline.

**Entregables:**
- Biblioteca estructurada, scraping controlado y caché local.
- Nuevos componentes Python (scanner en modo solo lectura, informes, normalización opcional) integrados con la aplicación.
- Si aporta valor: modelo SQLite con `games`, `platforms`, `files`, `emulator_profiles`.

**Criterio de salida:** añadir un juego compatible no rompe la biblioteca y la interfaz sigue funcionando sin Internet.

### Fase 4 — Guardados, mandos y robustez

**Objetivo:** uso cotidiano con seguridad.

**Entregables:**
- Respaldo/recuperación probados de partidas y configuración.
- Pruebas de segundo mando en sistemas apropiados.
- Comprobación de desconexión inesperada del externo, errores de ruta, crashes y permisos.

**Criterio de salida:** recuperación documentada, sin sobrescrituras silenciosas.

### Fase 5 — Portabilidad y publicación del software propio

**Objetivo:** consolidar los módulos Python ya desarrollados, con pruebas y documentación pública.

**Entregables:**
- Herramienta CLI para diagnóstico, inventario/importación, verificación, exportación, configuraciones y respaldo según necesidades reales.
- Adaptadores Windows/Linux, tests con `pytest`, formato/lint y CI cuando convenga.
- README de instalación, licencia elegida y contribuciones.

**Criterio de salida:** otra persona puede clonar el repo, preparar el entorno y ejecutar componentes propios sin disponer de ROMs comerciales.

### Fase 6 — Evolución opcional

- Interfaz web local, streaming en red doméstica, estadísticas de juego, integración de juegos de PC, sincronización entre dispositivos, recomendaciones locales, diagnóstico gráfico y automatizaciones adicionales.
- Docker y virtualización **solo si resuelven problemas reales** (pruebas/servicios auxiliares, no necesariamente ejecutar la GPU del emulador en contenedor).
- Ampliar la interfaz propia solo cuando exista evidencia de uso que lo justifique.

---

## 10. Primer sprint de trabajo: Sprint 0

**Nombre:** Inventario, seguridad y repositorio.<br>
**Duración:** varias sesiones cortas; sin fecha tope rígida.<br>
**Regla:** no ejecutar acciones destructivas, particionar ni descargar bibliotecas masivas.

### S0-01 — Inventario real del ASUS [EN CURSO]

En Windows, abrir PowerShell y recopilar solo datos técnicos no sensibles:

```powershell
# CPU y memoria
Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors
Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory

# Adaptadores gráficos
Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion

# Discos y espacio disponible
Get-Disk | Select-Object Number, FriendlyName, PartitionStyle, Size
Get-Volume | Where-Object DriveLetter | Select-Object DriveLetter, FileSystem, Size, SizeRemaining

# Git, Python y NVIDIA: informativo, no instalar todavía
where.exe git
where.exe python
nvidia-smi
```

**Notas:** si `where.exe` o `nvidia-smi` informan de que un comando no existe, no es necesariamente un fallo. No compartir números de serie ni tokens. Comprobar también salud del SSD/externo con herramientas de Windows si procede.

**Entregable:** `docs/hardware-inventory.md` (resumen sin información personal) y observaciones de almacenamiento externo.

### S0-02 — Protección de datos [PENDIENTE]

- Enumerar archivos que deban conservarse del Windows actual.
- Confirmar al menos una copia de seguridad independiente antes de probar SO nuevos o modificar particiones.
- Comprobar el espacio disponible, sistema de archivos y estabilidad de la unidad externa.
- No usar scripts que muevan o renombren ROMs originales sin modo simulación/confirmación.

### S0-03 — Git/GitHub desde el día 1 [EN CURSO]

**Actualización del 22 de octubre de 2026:** este repositorio ya existe en `main` y tiene un commit inicial. El bloque siguiente se conserva como referencia histórica para crear un repositorio nuevo; **no ejecutar `git init` ni repetir `git add` a ciegas aquí**. Revisar el estado y los archivos concretos antes de cualquier futuro commit:

```powershell
git init -b main
git status
git add README.md .gitignore docs/RetroStation_Master_Plan.md
git commit -m "docs: inicializar proyecto RetroStation"
```

**Antes de `git add`:** revisar contenido y `.gitignore` para evitar ROMs, BIOS y datos personales. `git commit` puede requerir configurar nombre/correo de Git. Crear repositorio remoto cuando se haya confirmado su privacidad/licencia; GitHub no está creado automáticamente por este documento.

### S0-04 — ADR-001 Sistema operativo y plataforma de prueba [PROTOTIPO WINDOWS ELEGIDO; SO FINAL PENDIENTE]

El propietario eligió Windows 11 actual para el **primer prototipo**, sin cambios de sistema o particiones. La decisión puede ser distinta del **SO final**; falta comprobar mando, salida al menú y uso sin conexión, y verificar una copia independiente antes de experimentar con otro sistema.

### S0-05 — Selección de juego de prueba libre/propio [PENDIENTE]

Identificar un título que se pueda usar legalmente y que ofrezca un camino simple para probar mando, guardado y regreso al menú. No añadir material protegido al repo.

### Registro inicial del sprint

| Tarea | Estado | Evidencia esperada |
|---|---|---|
| Inventario Windows | Parcial: SSD, GPU, Git y Python 3.11.9 confirmados; faltan externa y temperaturas/controles ampliados | resumen `hardware-inventory.md` |
| Comprobación de unidad 2 TB | Pendiente: no detectada en la captura | espacio y formato |
| Copia de seguridad | Por verificar | confirmación sin datos sensibles |
| Repositorio Git local | Inicializado en `main`; commit inicial existente (22-10-2026) | revisar cambios antes de un próximo commit |
| GitHub | Estado de publicación y visibilidad no verificado | confirmar decisión sobre licencia y visibilidad antes de publicar |
| ADR-001 | Windows 11 elegido para el primer prototipo; biblioteca de interfaz y SO final abiertos | [decisión](decisions/ADR-001-platform-and-frontend.md) |
| Prueba DS aislada | Arranque y partida cargada observados por el usuario tanto en melonDS independiente como desde RetroStation; no equivale al hito 1 | [matriz de pruebas](test-matrix.md) |
| Primera prueba con mando | No iniciada | evidencia de uso offline |

---

## 11. Hito 1: definición de terminado (Definition of Done)

**Escenario de aceptación — «De portátil a consola»:**

1. Encender el ASUS y abrir el entorno de juego (no es requisito todavía arrancarlo automáticamente al iniciar sesión).
2. Utilizar el DualShock 4 para navegar por la selección de sistemas/juegos.
3. Ver la carátula de al menos un título preparado.
4. Lanzar un juego con origen legal conocido y jugar una sesión de prueba estable.
5. Guardar y volver a cargar la partida cuando el emulador/título lo permita.
6. Salir del juego y regresar al menú sin tocar teclado/ratón en el flujo normal.
7. Repetir con el Wi-Fi desconectado.
8. Documentar emulador, controles, ajustes, fallos y soluciones; no perder datos al salir.

**La descarga de carátulas y preparación inicial sí puede hacerse con Internet**. La validación offline se realiza con la configuración ya lista.

---

## 12. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Cambios de SO o particiones destruyen datos | Muy alto | Copia verificable y consentimiento explícito; prototipo no destructivo |
| Fallos driver NVIDIA Optimus/híbrida en Linux | Alto | Investigar distro, probar controladores y GPU efectiva sin migrar de golpe |
| HDMI roto | Medio | Diseñar solo para pantalla integrada; no depender de salida TV |
| Temperaturas elevadas/throttling de portátil gaming antiguo | Medio-alto | Monitorizar en sesiones largas, limpiar ventilación sin intervención riesgosa |
| Unidad externa lenta, inestable o desconectada | Alto | Diagnóstico, rutas robustas, no ejecutar migraciones automáticas; respaldo separado |
| Rendimiento desigual por juego/emulador | Alto | Matriz con versiones, drivers, backend y ajustes; no prometer compatibilidad total |
| 3DS/Wii U/PS Vita no cumplen expectativas | Medio-alto | Prueba específica; tratar Vita como experimental |
| Cambiar core/emulador puede romper save states | Alto | Priorizar saves nativos y backups/versiones antes de actualizar |
| Entrada DualShock 4 y combinaciones de botones inconsistentes | Medio | Verificación de SDL/controladores/Steam Input si procede, mapa de controles por emulador |
| Metadatos/arte externos necesitan red o tienen licencias | Medio | Caché local, respetar términos de API y atribución/derechos de imágenes |
| ROM sets arcade/BIOS o firmware de origen dudoso | Alto | Usar recursos legítimos; no compartir ni versionar contenidos protegidos |
| Alcance desmedido antes de un primer juego | Alto | Sprints pequeños, vertical slice, validar antes de programar abstractions |
| Repo público contiene rutas privadas o claves | Alto | `.gitignore`, revisar diffs, ejemplos ficticios, no subir partidas ni BIOS |

---

## 13. Método de trabajo, control de versiones y GitHub

### Cadencia orientativa

- Varias horas mínimas a la semana cuando sea posible.
- Cada sesión empieza revisando **siguiente tarea pendiente** y acaba con un resultado tangible: documento, prueba, commit, incidencia o aprendizaje.
- No perseguir una fecha arbitraria ni una arquitectura de producción antes del primer juego.

### Flujo recomendado

1. Enunciar el objetivo y por qué existe.
2. Explicar herramientas antes de ejecutar comandos nuevos.
3. El usuario realiza configuración/código y aporta resultados relevantes.
4. Revisar errores, discutir alternativas y compromisos.
5. Documentar, probar y hacer commit pequeño si procede.
6. Actualizar el estado en este documento o enlaces a issues/ADR.

### Git

- Commits cortos y descriptivos: `docs:`, `feat:`, `fix:`, `test:`, `chore:`.
- Branches para funcionalidades cuando haya código real; evitar ceremonias innecesarias.
- Git versiona código y configuración, **no sustituye backups de partidas**.
- Guardar el documento maestro en `docs/`; el README apunta a él.
- Estado de GitHub: **[PENDIENTE]** verificar publicación/visibilidad y decidir licencia antes de cualquier acción remota.

### Registro ADR propuesto

Cada `docs/decisions/ADR-NNN-*.md` debe contener:

```markdown
# ADR-NNN — Título
Fecha:
Estado: Propuesto | Aceptado | Sustituido
Contexto:
Opciones evaluadas:
Decisión y justificación:
Consecuencias y riesgos:
Cómo validar / revertir:
```

**ADR-001:** SO para prototipo y estrategia de evaluación de Linux.<br>
**ADR-002:** Biblioteca de interfaz propia y mapeo de mandos.<br>
**ADR-003:** Estructura de almacenamiento y backups.<br>
**ADR-004:** Catálogo y persistencia (SQLite vs datos del núcleo).<br>
**ADR-005:** Estrategia de configuraciones multiplataforma.

---

## 14. Pruebas y validación

### Unidad (módulos propios)

- Tests para escáner de archivos, detección de extensiones y duplicados con datos ficticios.
- No permitir que los tests modifiquen bibliotecas reales.
- Validación de configuración, rutas Linux/Windows y errores de disco ausente.
- Si se construye una CLI, diseñar modo `--dry-run` para importación/movimientos.

### Integración

- Arranque de RetroArch desde CLI o interfaces compatibles.
- Emuladores independientes configurados por sistema.
- Interfaz propia detecta carátula, título y ruta.
- Detección/mapeo del mando y retorno a interfaz.
- Copias y restauraciones de saves.

### Aceptación en hardware real

- Una batería de juegos con sesión representativa y resultados reproducibles.
- Medición de FPS/velocidad real, audio, temperatura y conflictos de entrada.
- Repetición offline y tras reiniciar.

---

## 15. Guía para el siguiente chat / instrucciones de colaboración

> Estoy desarrollando **RetroStation**, una aplicación propia en Python que unifica emuladores existentes de varias consolas; el ASUS ROG Strix G es el primer equipo de prueba, no el único objetivo. Lee este documento entero y trabaja desde las decisiones y estados ya registrados. El núcleo Python, la previsualización y el lanzamiento explícito `launch --confirm` ya existen; las pruebas sintéticas y la observación del usuario con copias aisladas no completan el hito de mando y uso sin conexión. Continúa con la biblioteca y la interfaz propia controlable por mando en cortes verificables. Desarrolla los cortes que autorice y explica sus fundamentos para que pueda aprender y revisarlos; no presupongas la tecnología de interfaz ni el SO definitivo. Mantén Git y la documentación desde el primer día. No cambies ni formatees el SO, ni muevas mis datos, ni publiques el repositorio sin autorización. Prioriza estabilidad, uso offline, mando, biblioteca local y coste cero. Si hay dudas técnicas, verifica fuentes oficiales actuales. Completa Sprint 0 de hardware/seguridad antes de experimentar con sistemas operativos o instalaciones reales; el desarrollo del núcleo seguro puede avanzar en paralelo.

---

## 16. Fuentes de referencia para verificar antes de instalar

Son enlaces a documentación/proyectos, no una lista de software ya instalado ni un aval de compatibilidad universal. Verificados como recursos de referencia en octubre de 2026:

- Libretro / RetroArch, guía CLI: https://docs.libretro.com/guides/cli-intro/
- ES-DE, sitio y guía de usuario: https://www.es-de.org/ y https://gitlab.com/es-de/emulationstation-de/-/blob/master/USERGUIDE.md
- Playnite, modo fullscreen: https://api.playnite.link/docs/manual/gettingStarted/playniteFullscreenMode.html
- PCSX2, requisitos: https://pcsx2.net/docs/setup/requirements/
- Dolphin: https://dolphin-emu.org/download/
- PPSSPP: https://www.ppsspp.org/download/
- Azahar (3DS): https://www.azahar-emu.org/
- Cemu (Wii U): https://github.com/cemu-project/Cemu
- Vita3K y matriz de compatibilidad: https://vita3k.org/ y https://vita3k.org/compatibility
- Git: https://git-scm.com/docs
- Python: https://docs.python.org/3/

**Nota de actualidad:** revisar versiones, requisitos, disponibilidad y licencias cuando llegue cada instalación; no fijar descargas o configuraciones basándose solo en esta fotografía inicial.

---

## 17. Historial y continuidad

| Versión | Fecha | Resumen | Siguiente acción |
|---|---|---|---|
| 0.1.0 | 2026-10-17 | Consolidación de conversación y respuestas a 24 preguntas; hardware, alcance, decisiones, roadmap, arquitectura provisional y Sprint 0 | Recoger diagnóstico del ASUS y preparar repo Git |
| 0.1.1 | 2026-10-17 | Incorporado primer diagnóstico real de PowerShell: partición GPT, capacidad/libre SSD, Git 2.47.1, GPU/driver, fallo de comando `py`, GPU a 74 °C; sin evidencia aún del disco externo | Comprobar Python, conectar disco de 2 TB y repetir temperaturas; preparar Git |
| 0.1.2 | 2026-10-17 | Confirmado Python 3.11.9 con comando `python`; `py` opcional; segunda medición GPU 70 °C a 5 W y 3 % de uso, tras desaparecer MuMuPlayer de procesos; Git pendiente de inicializar | Verificar almacenamiento externo, revisar refrigeración sin estrés y crear primer repo Git local |
| 0.1.3 | 2026-10-22 | Ubicada la versión única en `docs/`; comprobado Git local en `main` con commit inicial; preparados README, exclusiones locales y documentos de Sprint 0. Sin nuevas pruebas del ASUS ni publicación remota | Verificar almacenamiento externo, datos a proteger, copia independiente y mando antes de elegir prototipo |
| 0.2.0 | 2026-10-22 | Cambiado el objetivo principal a aplicación propia que integra emuladores; ES-DE pasa a ser referencia opcional. El desarrollo del núcleo Python comienza en paralelo al diagnóstico, sin elegir todavía interfaz gráfica ni SO definitivo | Probar perfiles locales de sistemas; verificar después el ASUS y planificar el primer lanzamiento legal |
| 0.2.1 | 2026-11-04 | Perfiles y previsualización probados; lanzamiento explícito y recarga de la partida observados por el usuario con copias DS aisladas. El núcleo tiene pruebas sintéticas; no se verificó Python 3.11 actual | Completar inventario/backup independiente, elegir plataforma del prototipo y evaluar interfaz con mando; comprobar retorno al menú y uso sin conexión |
| 0.2.2 | 2026-11-04 | El propietario eligió Windows 11 actual como plataforma del primer prototipo, sin decidir la biblioteca de interfaz ni el SO final | Evaluar interfaz con mando y completar comprobaciones de retorno al menú, uso sin conexión y copia independiente antes de cambios del sistema |

### Último estado comprobado

- [x] Se ha definido el propósito, hardware base y prioridades.
- [x] Se han identificado familias a emular y juegos de referencia.
- [x] Se han identificado restricciones: 0 €, HDMI roto, pantalla propia, unidad externa, Windows sin formatear.
- [x] Se ha escogido filosofía didáctica y tecnologías de interés.
- [x] Diagnóstico parcial de SSD interno, driver NVIDIA y Git.
- [x] Python 3.11.9 observado el 17-10-2026; la ejecución actual de la suite en 3.11 no se ha verificado.
- [x] Repetición de medición NVIDIA: 70 °C, 5 W, ~3 % de uso; temperatura pendiente de investigar.
- [ ] Diagnóstico externo de 2 TB, refrigeración/temperaturas de CPU y mando.
- [x] Git local inicializado; los cortes del núcleo y del lanzamiento se registraron en `odd/tasks/retrostation-app-foundation.md`.
- [x] Lanzamiento aislado desde la aplicación y recarga de partida observados por el usuario; no es una prueba automatizada de jugabilidad ni del hito completo.
- [ ] Publicación/visibilidad remota y licencia por verificar.
- [ ] Protección de datos contrastada.
- [x] Windows 11 actual elegido como plataforma del primer prototipo; no determina el SO final.
- [ ] Biblioteca de interfaz propia con mando evaluada; navegación y uso sin conexión no verificados.
- [ ] Primer juego ejecutado desde la aplicación propia con mando y sin Internet.

**Próximo mensaje de trabajo sugerido:** «Continúa el núcleo de la aplicación RetroStation desde `odd/tasks/retrostation-app-foundation.md`; en paralelo completa el inventario seguro de Sprint 0 (unidad externa, mando y copia de seguridad) sin instalar software ni mover datos hasta validar la estrategia».
