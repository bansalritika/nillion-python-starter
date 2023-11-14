#!/usr/bin/env bash
function __echo_red_bold {
  echo -e "\033[1;31m${1}\033[0m"
}

function __nillion_pip_install() {
  WHLPATH=$(find "$NILLION_SDK_ROOT" -iname "$1" -type f -print | head -n1)
  pip install --force-reinstall "${WHLPATH:?could not find $1 in $NILLION_SDK_ROOT}"
}

function install_py_nillion_client() {
  __nillion_pip_install "py_nillion_client-*$(uname -s)*_$(uname -m).whl"
}

function install_nada_dsl() {
  __nillion_pip_install "nada_dsl-*-any.whl"
}

function discover_sdk_bin_path() {
  BINPATH=$(find "$NILLION_SDK_ROOT" -name "$1" -type f -executable -print | head -n1)
  if ! command -v "$BINPATH" > /dev/null; then
    echo "${1} was not discovered. Check NILLION_SDK_ROOT" 1>&2
    exit 1
  fi
  echo "$BINPATH"
}

function check_for_sdk_root() {
  if [ -z "$NILLION_SDK_ROOT" -a ! -d "$NILLION_SDK_ROOT" ]; then
    echo "Error: NILLION_SDK_ROOT is not set to a directory"
    exit 1
  fi
}
