# Bash completion for the GNU/MOS command-line driver.
_lfs_complete()
{
    local current=${COMP_WORDS[COMP_CWORD]} command='' previous=${COMP_WORDS[COMP_CWORD-1]-}
    local options word candidate used index arch_value=false
    COMPREPLY=()

    for (( index=1; index<COMP_CWORD; index++ )); do
        word=${COMP_WORDS[index]}
        if $arch_value; then
            arch_value=false
            continue
        fi
        case "$word" in
            --arch) arch_value=true ;;
            --arch=*) ;;
            setup|build|run|status|stats) [[ -n $command ]] || command=$word ;;
            -h|--help) return 0 ;;
            --no-gui|--all|--rebuild|-r) ;;
            *)
                if [[ $command == run ]]; then
                    compopt -o default 2>/dev/null || true
                    return 0
                fi
                [[ $word == -- ]] && return 0
                ;;
        esac
    done

    if [[ $previous == --arch ]]; then
        COMPREPLY=( $(compgen -W 'x86 x64' -- "$current") )
        return 0
    fi
    if [[ $current == --arch=* ]]; then
        COMPREPLY=( $(compgen -W '--arch=x86 --arch=x64' -- "$current") )
        return 0
    fi
    case "$command" in
        '') options='setup build run status stats --arch -h --help' ;;
        build) options='--arch --all --rebuild -r --no-gui -h --help' ;;
        setup|status|stats) options='--arch --no-gui -h --help' ;;
        run) options='--arch --no-gui -h --help --' ;;
    esac

    for candidate in $options; do
        [[ $candidate == "$current"* ]] || continue
        used=false
        for (( index=1; index<COMP_CWORD; index++ )); do
            word=${COMP_WORDS[index]}
            if [[ $word == "$candidate" ]] ||
               [[ $candidate == --arch && $word == --arch=* ]] ||
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
