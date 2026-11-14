#!/bin/sh
# Install only the verified Composer PHAR for the optional XAMPP profile.
set -eu

case "$#" in
    0) ;;
    1) case "$1" in
           -h|--help) printf '%s\n' 'Usage: install-composer.sh' \
               'Install or update Composer 2 for the current user; requires XAMPP PHP.'
               exit 0 ;;
           *) printf '%s\n' 'Usage: install-composer.sh' >&2; exit 2 ;;
       esac ;;
    *) printf '%s\n' 'Usage: install-composer.sh' >&2; exit 2 ;;
esac
if [ "$(id -u)" -eq 0 ]; then
    printf '%s\n' 'Run this installer as your normal user, without sudo.' >&2
    exit 1
fi

php_bin=/opt/lampp/bin/php
datadir="$HOME/.local/share/composer"
target="$datadir/composer.phar"
ca=/etc/ssl/certs/ca-certificates.crt

if [ ! -x "$php_bin" ] || [ ! -r "$ca" ]; then
    printf '%s\n' 'XAMPP PHP and the Debian CA store are required.' >&2
    exit 1
fi
if ! command -v curl >/dev/null 2>&1; then
    printf '%s\n' 'curl is required.' >&2
    exit 1
fi
check_destination() {
    for dir in "$HOME/.local" "$HOME/.local/share" "$datadir"; do
        if [ -L "$dir" ] || { [ -e "$dir" ] && [ ! -d "$dir" ]; }; then
            printf 'Refusing to use this Composer data path: %s\n' "$dir" >&2
            return 1
        fi
    done
    if [ -L "$target" ] || { [ -e "$target" ] && [ ! -f "$target" ]; }; then
        printf 'Refusing to replace a symlink or non-regular file: %s\n' "$target" >&2
        return 1
    fi
}
check_destination

umask 077
work=$(mktemp -d "${TMPDIR:-/tmp}/composer-install.XXXXXX")
pending=
cleanup() {
    if [ -n "$pending" ]; then rm -f -- "$pending"; fi
    rm -rf -- "$work"
}
trap cleanup 0
trap 'exit 129' 1
trap 'exit 130' 2
trap 'exit 143' 15
download() {
    curl --disable --fail --silent --show-error --location \
        --proto '=https' --proto-redir '=https' --cacert "$ca" \
        --connect-timeout 15 --max-time 120 "$1" -o "$2"
}
run_php() {
    "$php_bin" -d "openssl.cafile=$ca" -d "curl.cainfo=$ca" "$@"
}

printf '%s\n' 'Downloading the official Composer installer and its SHA-384 checksum.'
download https://composer.github.io/installer.sig "$work/installer.sig"
download https://getcomposer.org/installer "$work/composer-setup.php"
run_php -r '
    $expected = trim(file_get_contents($argv[1]));
    $actual = hash_file("sha384", $argv[2]);
    if (!preg_match("/^[a-f0-9]{96}$/D", $expected) || !hash_equals($expected, $actual)) {
        fwrite(STDERR, "SHA-384 verification failed. The installer will not be executed.\n");
        exit(1);
    }
' "$work/installer.sig" "$work/composer-setup.php"

run_php "$work/composer-setup.php" --2 --install-dir="$work" --filename=composer.phar
run_php "$work/composer.phar" --no-plugins --no-scripts --version

check_destination
mkdir -p -- "$datadir"
pending=$(mktemp "$datadir/.composer.phar.XXXXXX")
install -m644 -- "$work/composer.phar" "$pending"
mv -fT -- "$pending" "$target"
pending=
printf 'Installed Composer to %s\n' "$target"
