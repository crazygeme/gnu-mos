tmux 3.5a uses `/etc/tmux.conf` for system configuration, followed by
the user configuration files. The system configuration is supplied by
`src/sysroot/etc/tmux.conf` and installed into the image by `./lfs setup`.

PTY write readiness reflects available buffer space. A full output buffer
is not writable; draining or flushing it wakes registered `poll` and
`select` write waiters. This supports tmux's nonblocking terminal output.

For clients using `TERM=linux`, terminal capability overrides accommodate
the MOS console's immediate line wrapping, fixed-color scroll fills, and
absence of erase-character and alternate-character-set support. tmux uses
explicit cursor positioning, space-based clearing, and ASCII borders. The
bottom-right screen cell is reserved to prevent a full-screen scroll.
The overrides do not apply to other terminal types or change the terminal
type exposed to applications inside tmux.

The console renders individual bytes rather than UTF-8 characters. ASCII
borders are supported; arbitrary Unicode text and Powerline glyphs are not.
Terminal capability changes take effect when a client attaches to tmux.

The root and ezheng user configurations define pane and window key bindings,
fzf-aware vertical navigation, colored status bars, and working-directory
labels. Status separators use ASCII `<` and `>` characters, and
`pane-border-lines simple` selects ASCII pane borders.
Pane navigation uses tmux commands directly. Vertical navigation forwards
the key when `pane_current_command` is `fzf`. Window labels display up to
three trailing path components using tmux format substitution. The status
label is `R` when the session environment contains `SSH_CONNECTION` and `L`
otherwise. Status rendering and navigation do not start shell jobs.
