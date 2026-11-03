# Hardware and compatibility

## Target platform

| Componente | Especificación |
|---|---|
| Equipo | Apple MacBook Pro 13-inch Early 2015, MacBookPro12,1 |
| CPU | Intel Core i5-5257U, 2 núcleos / 4 hilos, 2,7 GHz |
| GPU | Intel Iris Graphics 6100, Broadwell GT3, i915 |
| RAM | 8 GB, aproximadamente 7,7 GiB utilizables |
| Pantalla | eDP-1, 2560×1600, escala entera 2 |
| Wi-Fi | Broadcom BCM43602, brcmfmac |
| Plataforma | Debian 13 amd64, kernel serie 6.12, Sway/Wayland |

`firmware-brcm80211` proporciona el firmware de brcmfmac y requiere el componente
Debian `non-free-firmware`. Mesa 25.0.7 expone OpenGL 4.6 y Vulkan 1.3.305 en
la Iris 6100. Verificar el dispositivo físico, no el loader ni llvmpipe;
[Zed setup](zed-setup.md) detalla la comprobación Vulkan.

## Storage reference

La instalación de referencia utiliza un Kingston SV300S37A240G de 240 GB por
USB 3/UAS, con raíz ext4. El SSD Apple interno de 256 GB mantiene otra instalación.
Estas rutas/discos no se particionan ni montan automáticamente desde los dotfiles.
Tras formatear, identificar los discos por el instalador, no asumir nombres sdX.

## Battery and backlight

Referencia medida el 2026-08-07: 1.407 ciclos, capacidad máxima 4.123.000 µAh
frente a 6.559.000 µAh de diseño, salud aproximada 62,9 %.
UPower distingue percentage (carga) de capacity (salud); en esta máquina
BAT0/capacity no representa correctamente la carga disponible.

Backlight: `/sys/class/backlight/intel_backlight`, rango observado 0–1388.
El perfil aplica 40 % al iniciar Sway y permite cambiarlo con F1/F2.
Las mediciones de batería y rangos deben revalidarse al cambiar batería/kernel.

## Operating policy

La configuración favorece interfaces nativas Wayland, colores opacos y servicios
a demanda. No modifica límites CPU ni controladores para simular compatibilidad.
[Restore guide](restore-guide.md), [Power and performance](optimizations.md) y
[XFCE recovery](xfce-recovery.md).
