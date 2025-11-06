# Registro de Cambios - Willay

## [Actualización] - Historial de Chats + Despliegue Ubuntu

### ✨ Nuevas Características

#### 1. Sistema de Historial de Chats Funcional
- ✅ **Sidebar con historial persistente**: Ahora el historial de conversaciones se muestra correctamente en el sidebar izquierdo
- ✅ **Gestión de sesiones**: Cada conversación se guarda como una sesión independiente con:
  - Título automático (primeras palabras del primer mensaje)
  - Timestamp para ordenar cronológicamente
  - Mensajes completos de la conversación
- ✅ **Funciones implementadas**:
  - `getCurrentSession()`: Obtiene la sesión activa
  - `getAllSessions()`: Lista todas las sesiones guardadas
  - `createNewSession()`: Crea nueva conversación
  - `addMessageToSession()`: Agrega mensajes a la sesión actual
  - `loadSession()`: Carga una conversación anterior
  - `deleteSession()`: Elimina una conversación (con confirmación)
  - `renderChatHistory()`: Renderiza el sidebar con las conversaciones
  - `formatDate()`: Formatea timestamps ("Ahora", "5m", "2h", etc.)

#### 2. Despliegue Completo en Ubuntu Server
- ✅ **Script de instalación automática** (`install.sh`):
  - Instala dependencias del sistema (Python, Nginx)
  - Instala y configura Ollama
  - Descarga modelos (llama3.2, nomic-embed-text)
  - Crea servicio systemd para el backend
  - Configura Nginx como reverse proxy
  - Inicia todos los servicios automáticamente

- ✅ **Script de ejecución manual** (`backend/run.sh`):
  - Crea entorno virtual
  - Instala dependencias
  - Ejecuta uvicorn en modo reload
  - Manejo de errores

- ✅ **Archivo de servicio systemd** (`willay-backend.service`):
  - Configuración completa para ejecutar Willay como servicio
  - Auto-reinicio en caso de fallo
  - Dependencia de Ollama
  - Logs a journald

- ✅ **Documentación completa**:
  - `UBUNTU_DEPLOYMENT.md`: Guía exhaustiva de despliegue
  - `backend/README_UBUNTU.md`: Guía específica de los scripts
  - README.md actualizado con sección de Ubuntu

### 🔧 Correcciones

#### Frontend (script.js)
- **Antes**: Usaba sistema simple con array `history[]` sin persistencia
- **Ahora**: Sistema completo de sesiones con localStorage
- **Corregido**: Clases CSS inconsistentes
  - Cambiado: `chat-history-item` → `history-item`
  - Cambiado: `history-title` → `history-item-title`
  - Agregado: `history-item-date` → `history-item-date`

#### CSS (style.css)
- **Agregado**: Estilos para botón de eliminar conversación
  - `.history-delete` con efecto hover
  - Botón aparece solo al hacer hover sobre la conversación
  - Posicionamiento absoluto en esquina superior derecha
  - Efecto de escala al hacer hover

### 📁 Archivos Nuevos

```
Willay/
├── install.sh                      # Instalador automático Ubuntu (NUEVO)
├── UBUNTU_DEPLOYMENT.md            # Guía completa Ubuntu (NUEVO)
├── backend/
│   ├── run.sh                      # Script ejecución Ubuntu (NUEVO)
│   ├── willay-backend.service      # Servicio systemd (NUEVO)
│   └── README_UBUNTU.md            # Guía scripts Ubuntu (NUEVO)
```

### 📁 Archivos Modificados

```
script.js       # Sistema completo de sesiones y historial
style.css       # Estilos para botón delete y ajustes
README.md       # Sección Ubuntu y estructura actualizada
```

### 🚀 Cómo Usar

#### Historial de Chats (Windows)
1. Abre el chatbot normalmente (`index.html`)
2. El historial se muestra automáticamente en el sidebar izquierdo
3. Haz clic en una conversación para cargarla
4. Haz clic en "Nuevo Chat" para crear una nueva sesión
5. Hover sobre una conversación y haz clic en "×" para eliminarla

#### Despliegue en Ubuntu Server
```bash
# Clonar proyecto
git clone https://github.com/Musgus/Willay.git
cd Willay

# Dar permisos
chmod +x install.sh

# Instalar (ejecuta todo automáticamente)
sudo ./install.sh

# Acceder
# Frontend: http://TU_IP_SERVIDOR
# API: http://TU_IP_SERVIDOR:8000
```

#### Gestión del Servicio Ubuntu
```bash
# Ver logs en tiempo real
sudo journalctl -u willay-backend -f

# Estado del servicio
sudo systemctl status willay-backend

# Reiniciar
sudo systemctl restart willay-backend

# Detener
sudo systemctl stop willay-backend
```

### 🐛 Problemas Resueltos

1. **Historial no se mostraba**: Las funciones de renderizado no estaban implementadas
2. **Sesiones no persistían**: Faltaba integración con localStorage
3. **Clases CSS inconsistentes**: JS usaba nombres diferentes al CSS
4. **Botón delete sin estilo**: Agregados estilos completos con efectos
5. **Sin soporte Ubuntu**: Agregados scripts .sh y documentación

### 📊 Estadísticas

- **Líneas de código agregadas**: ~600
- **Archivos nuevos**: 5
- **Archivos modificados**: 3
- **Funciones nuevas en JS**: 8
- **Comandos Ubuntu documentados**: 15+

### 🔜 Próximas Mejoras Sugeridas

- [ ] Exportar/importar historial de conversaciones
- [ ] Búsqueda en historial de chats
- [ ] Tags o categorías para conversaciones
- [ ] Sincronización entre dispositivos
- [ ] Backup automático del historial
- [ ] Configuración HTTPS automática con Let's Encrypt
- [ ] Docker Compose para despliegue simplificado
- [ ] Dashboard de métricas (Prometheus + Grafana)

### 📝 Notas de Compatibilidad

- **Windows**: Scripts .bat y .ps1 funcionan sin cambios
- **Ubuntu/Linux**: Scripts .sh con permisos de ejecución requeridos
- **Navegadores**: Probado en Chrome, Edge, Firefox
- **Python**: Compatible con 3.8, 3.9, 3.10, 3.11, 3.12
- **Ollama**: Versión 0.1.0 o superior

---

**Fecha**: $(date +%Y-%m-%d)
**Versión**: 1.1.0
**Autor**: Musgus
