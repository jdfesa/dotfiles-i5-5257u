# Uso diario

## Batería y brillo

En la barra superior de XFCE, el icono del **Gestor de energía** permite consultar
la carga de la batería. Al pulsarlo también aparece el control deslizante de brillo.

El brillo comienza al 40% en cada sesión local. Para desactivar ese ajuste, abre
**Sesión e inicio > Inicio automático de aplicaciones** y desmarca
**Brillo inicial MBP 2015**.

Las teclas de brillo del MacBook son F1 y F2. Según la configuración del teclado,
puede ser necesario usar `Fn`+F1 y `Fn`+F2.

## Consulta rápida por terminal

```bash
cat /sys/class/power_supply/BAT0/status
cat /sys/class/power_supply/BAT0/cycle_count
```

En este MacBook, `BAT0/capacity` refleja aproximadamente la **salud** de la
batería, no su carga del momento. Para consultar la carga real se debe usar
UPower:

```bash
upower -i "$(upower -e | grep battery_BAT0)" | grep -E 'state|percentage|capacity'
```

Para calcular la salud respecto de la capacidad de fábrica:

```bash
awk 'NR==FNR { actual=$1; next } { printf "%.1f%%\n", 100*actual/$1 }' \
  /sys/class/power_supply/BAT0/charge_full \
  /sys/class/power_supply/BAT0/charge_full_design
```

Los valores detallados están disponibles con:

```bash
upower -i "$(upower -e | grep BAT)"
```
