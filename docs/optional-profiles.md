# Optional restore profiles

Aplicar solo los módulos necesarios, desde la raíz del repositorio.
Ninguno se instala con Sway. Los binarios y las credenciales se restauran por
separado: los enlaces apuntan a fuentes versionadas solo cuando son archivos
de usuario.

| Perfil | Qué restaura | Activación |
| --- | --- | --- |
| [SSH access](others/ssh-access.md) | Acceso remoto por OpenSSH | Solo si se elige instalar el servidor |
| [Node.js setup](others/node-setup.md) | Node.js, npm y npx en el home | Bajo demanda |
| [XAMPP and Composer setup](others/xampp-setup.md) | Lanzadores y Composer | Bajo demanda; sin autostart de servicios |
| [XFCE recovery](xfce-recovery.md) | Sesión de recuperación y brillo | Solo al elegir una sesión XFCE |
| [Wi-Fi hotspot](wifi/hotspot.md) | Lanzador para un perfil local de NetworkManager | Manual; no se activa al arrancar |

## Plan and apply

Cada invocación trabaja sobre un único perfil. Ejemplo con XAMPP:

```sh
python3 tools/restore-profile.py xampp packages
# Revisar la simulación antes de instalar:
python3 tools/restore-profile.py xampp packages --apply
python3 tools/restore-profile.py xampp links
python3 tools/restore-profile.py xampp links --apply \
  --backup-dir "$HOME/.local/state/dotfiles-i5-5257u/link-backups/xampp-$(date +%Y%m%d-%H%M%S)"
```

El plan no instala paquetes ni cambia enlaces. La aplicación de enlaces delega
al enlazador del repositorio y registra el journal de reversión. Ante un
conflicto, respaldar y revisar el destino: no hay reemplazo forzado.
Para revertir enlaces, seguir [Configuration deployment](deployment.md#rollback).
SSH y Node no tienen manifiesto de enlaces a fuentes del repositorio: SSH usa
archivos del sistema y Node enlaza ejecutables instalados fuera del checkout.

No se añaden temporizadores ni sondeos a Sway. Que un módulo sea opcional no
demuestra ahorro de batería; para compararlo, medir la descarga con una carga
de trabajo y brillo equivalentes.
