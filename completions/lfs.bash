# Bash completion for the GNU/MOS command-line driver.
_lfs_complete()
{
    local current=${COMP_WORDS[COMP_CWORD]} command=${COMP_WORDS[1]-}
    local options word candidate used index
    COMPREPLY=()

    if (( COMP_CWORD == 1 )); then
        options='setup build run status'
        [[ $current == -* ]] && options='-h --help'
    else
        case "$command" in
            build) options='--all --rebuild -r --no-gui -h --help' ;;
            setup|status) options='--no-gui -h --help' ;;
            run) options='--no-gui -h --help --' ;;
            *) return 0 ;;
        esac

        for (( index=2; index<COMP_CWORD; index++ )); do
            word=${COMP_WORDS[index]}
            case "$word" in
                -h|--help) return 0 ;;
                --no-gui) ;;
                *)
                    if [[ $command == run ]]; then
                        compopt -o default 2>/dev/null || true
                        return 0
                    fi
                    [[ $word == -- ]] && return 0
                    ;;
            esac
        done
    fi

    for candidate in $options; do
        [[ $candidate == "$current"* ]] || continue
        used=false
        for (( index=2; index<COMP_CWORD; index++ )); do
            word=${COMP_WORDS[index]}
            if [[ $word == "$candidate" ]] ||
               [[ $word == -r && $candidate == --rebuild ]] ||
               [[ $word == --rebuild && $candidate == -r ]]; then
                used=true
                break
            fi
        done
        $used || COMPREPLY+=("$candidate")
    done
    return 0
}

complete -F _lfs_complete lfs ./lfs
