# SSH access

## Restore from the local console

Instalar el servidor solo si se necesita administrar el portátil por red.
Mantener el acceso limitado a una red confiable y no publicar el puerto en el
router. En Debian, instalar el paquete puede iniciar el servicio.

```sh
python3 tools/restore-profile.py ssh packages
# Tras revisar el plan APT:
python3 tools/restore-profile.py ssh packages --apply
sudo /usr/sbin/sshd -t && sudo systemctl enable --now ssh.service
```

Desde el cliente, comprobar contra la consola la huella de la nueva clave de
host antes de confiar en ella. Para transferir la clave pública, utilizar
ssh-copy-id o instalarla desde la consola en ~/.ssh/authorized_keys (archivo
0600 y directorio 0700). No guardar claves, cuentas ni direcciones locales en
el repositorio. Probar una segunda conexión:

```sh
ssh -o BatchMode=yes -o PreferredAuthentications=publickey cuenta@portatil
```

## Optional key-only authentication

Solo si la prueba anterior funciona y hay acceso a la consola. La plantilla
desactiva acceso root y autenticación por contraseña y teclado interactivo.
Según [sshd_config](https://manpages.debian.org/trixie/openssh-server/sshd_config.5.en.html),
en Debian el drop-in se incluye al principio; comprobar que no hay una regla
anterior que lo anule. No sobrescribir una copia local existente: respaldar y
compararla primero. Copiar como archivo de root, no como enlace.

```sh
dropin=/etc/ssh/sshd_config.d/10-dotfiles-key-only.conf
if sudo test -e "$dropin" || sudo test -L "$dropin"; then
    printf '%s\n' 'Existing SSH drop-in; review before proceeding.' >&2
else
    sudo install -o root -g root -m 0644 config/ssh/10-dotfiles-key-only.conf "$dropin"
fi
sudo /usr/sbin/sshd -t && sudo /usr/sbin/sshd -T | grep -E '^(permitrootlogin|pubkeyauthentication|passwordauthentication|kbdinteractiveauthentication) '
```

Solo si la sintaxis y los valores efectivos son correctos, usar
sudo systemctl reload ssh.service. Probar otra conexión por clave antes de
cerrar la anterior. Si falla, desde la consola retirar o restaurar el drop-in,
validar con sshd -t y volver a recargar. No se modifica la política del
servidor actual al clonar o aplicar los enlaces.
