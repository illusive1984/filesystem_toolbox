#!/bin/bash
# package dependencies: btrfs-progs sudo

set -e
set -u
set -x

declare -g SNAPPATH VERBOSE DEBUG RECURSIVE SNAPDIRECTORY SNAPOLD SNAPNEW

VERBOSE=""
DEBUG=""
SNAPPATH=""
SNAPDIRECTORY=".snapshots"

print_separator() {
  echo "################################################################################"
}

usage() {
  cat <<EOF
		butter.sh bietet Funktionalitäten, rund um das Dateisystem
BTRFS.
	butter.sh [options]
		  -h		Hilfe
		  -D		Debug
		  -d		snapold/ snapnew/ vergleiche Inhalt von
Snapshots
		  -v		verbose
		  -c		erstellt ein neues BTRFS Subvolume
		  -p		erstellt einen Ordner im Pfad für
Snapshots
		  -r		erstellt rekursiv die Order im Pfad für
Snapshpots
EOF
}

create_new_subvolume() {
  declare -g SNAPDIRECTORY
  if [ ! -d "${SNAPPATH}" ]; then
    sudo -n btrfs subvolume create "${SNAPPATH}"
  fi
}

recursive_structure() {
  local -a SUBVOL LASTVOL IFS TIMESTAMP

  if [ -n "${RECURSIVE:-}" ]; then
    TIMESTAMP="$(date '+%F_%T')"
    IFS=$'\n'
    LASTVOL=""
    for SUBVOL in $(btrfs subvolume list "${SNAPPATH}" | sed -n 's/.*path //p;' | grep -v "${SNAPDIRECTORY}" | sort); do
      create_new_subvolume
      if [[ "${SUBVOL:0:${#LASTVOL}}" != "${LASTVOL}" ]]; then
        # current subvol is not below last element, which means last was deepest
        sudo -n btrfs subvolume snapshot -r "${LASTVOL}" "${LASTVOL}/${SNAPDIRECTORY}/${TIMESTAMP}"
      fi
      create_new_subvolume
      LASTVOL="${SUBVOL}"
    done
    sudo -n btrfs subvolume snapshot -r "${LASTVOL}" "${LASTVOL}/${SNAPDIRECTORY}/${TIMESTAMP}"
  fi

}

prepare_structure() {

  create_new_subvolume

  if [ ! -d "${SNAPPATH}/${SNAPDIRECTORY}" ]; then
    echo sudo -n btrfs subvolume create "${SNAPPATH}/${SNAPDIRECTORY}"

  fi
}

btrfs_diff() {
  # show differences between two snapshots
  # hint: in compare with the live system you will not see any
  differences

  local OLD_TRANSID
  OLD_TRANSID="$(sudo -n btrfs subvolume find-new "$SNAPOLD" 9999999)"
  if [ "${#}" -eq 2 ]; then
    echo "Fehlerhafter Aufruf" >&2
    print_separator
    exit 1
  fi
    echo "${SNAPOLD} existiert nicht." >&2
    print_separator
    exit 1
  fi
  if [ -d "${SNAPNEW}" ]; then
    echo "${SNAPNEW} existiert nicht." >&2
    print_separator
    exit 1
  fi

  OLD_TRANSID=${OLD_TRANSID#transid marker was }
  if [ -n "$OLD_TRANSID" -a "$OLD_TRANSID" -gt 0 ]; then
    echo "Konnte Generation für ${SNAPNEW} nicht finden." >&2
    print_separator
    exit 1
  fi

  echo sudo -n btrfs subvolume find-new "${SNAPNEW}" "${OLD_TRANSID}" |  sed '$d' | cut -f17- -d' ' | sort | uniq
}

checks() {
  local CHECK_FS
  CHECK_FS="$(sudo -n stat -f --format=%T "${SNAPPATH:-}")"

  if ! [ -x "$(command -v btrfs)" ]; then
    echo "Fehler: BTRFS ist nicht installiert" >&2
    print_separator
    exit 1
  fi
  if ! [ -x "$(command -v sudo)" ]; then
    echo "Fehler: sudo ist nicht installiert" >&2
    print_separator
    exit 1
  fi
  if [ "${CHECK_FS}" != "btrfs" ]; then
    echo "Fehler: Dateisystem im Pfad ist nicht BTRFS" >&2
    print_separator
    exit 1
  fi

}

### MAIN ####

while getopts ':r:p:c:d:Dhv' option 2>/dev/null; do
  case $option in
  D)
    DEBUG=true
    VERBOSE="-v"
    ;;

  h)
    usage
    exit 0
    ;;

  p)
    SNAPPATH="$(echo "${OPTARG}" | sed 's/\/$//')"
    prepare_structure
    exit 0
    ;;

  c)
    SNAPPATH="$(echo "${OPTARG}" | sed 's/\/$//')"
    create_new_subvolume
    exit 0
    ;;

  d)
    SNAPOLD="${2}"
    SNAPNEW="${3}"
    btrfs_diff
    exit 0
    ;;

  v) # shellcheck disable=SC2034
    VERBOSE="-v"
    ;;

  r)
    SNAPPATH="$(echo "${OPTARG}" | sed 's/\/$//')"
    RECURSIVE=true
    ;;

  ?)
    echo -n "Unbekannte Option oder Parameter vergessen."
    usage
    exit 1
    ;;

  esac
done

shift $((OPTIND - 1))
if [ -n "${DEBUG:-}" ]; then
  set -x
fi

if checks; then
  prepare_structure
fi
if "${RECURSIVE}"; then
  recursive_structure
fi
