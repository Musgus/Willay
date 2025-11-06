# Scripts de Despliegue para Ubuntu Server

Esta carpeta contiene los scripts necesarios para desplegar Willay en Ubuntu Server.

## Archivos Incluidos

### `run.sh`
Script para ejecutar el backend manualmente en Ubuntu/Linux.

**Uso:**
```bash
chmod +x run.sh
./run.sh
```

Características:
- Crea entorno virtual automáticamente
- Instala/actualiza dependencias
- Ejecuta uvicorn en modo reload
- Maneja errores de instalación

### `willay-backend.service`
Archivo de configuración de systemd para ejecutar Willay como servicio.

**Instalación manual:**
```bash
sudo cp willay-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable willay-backend
sudo systemctl start willay-backend
```

**Gestión:**
```bash
# Ver estado
sudo systemctl status willay-backend

# Ver logs
sudo journalctl -u willay-backend -f

# Reiniciar
sudo systemctl restart willay-backend

# Detener
sudo systemctl stop willay-backend
```

## Instalación Recomendada

**No ejecutes estos scripts manualmente.** Usa el instalador automático desde la raíz del proyecto:

```bash
cd ..  # Volver a la raíz de Willay
sudo ./install.sh
```

El instalador se encarga de:
1. Instalar todas las dependencias del sistema
2. Configurar Ollama y descargar modelos
3. Copiar archivos a `/opt/willay`
4. Instalar el servicio systemd
5. Configurar Nginx
6. Iniciar todo automáticamente

## Troubleshooting

### run.sh no se ejecuta
```bash
# Asegúrate de que tiene permisos de ejecución
chmod +x run.sh

# Verifica que Python 3 esté instalado
python3 --version

# Instala python3-venv si falta
sudo apt install python3-venv
```

### El servicio no inicia
```bash
# Ver error específico
sudo journalctl -u willay-backend -n 50 --no-pager

# Verificar rutas en el archivo .service
sudo nano /etc/systemd/system/willay-backend.service

# Después de editar, recargar
sudo systemctl daemon-reload
sudo systemctl restart willay-backend
```

### Puerto 8000 en uso
```bash
# Ver qué proceso usa el puerto
sudo lsof -i :8000

# Matar proceso si es necesario
sudo kill -9 <PID>

# O cambiar puerto en willay-backend.service
# Línea ExecStart: ... --port 8080
```

## Documentación Completa

Para una guía completa de despliegue, consulta:
- **UBUNTU_DEPLOYMENT.md** en la raíz del proyecto
- **README.md** en la raíz del proyecto (sección Ubuntu)

## Soporte

Si encuentras problemas:
1. Verifica los logs: `sudo journalctl -u willay-backend -f`
2. Consulta UBUNTU_DEPLOYMENT.md - Sección "Solución de Problemas"
3. Abre un issue en GitHub con los logs relevantes
