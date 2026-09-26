Linux-PAM 1.7.1 provides PAM libraries, headers, and authentication modules
under `/usr`. Configuration resides in `/etc/pam.d` and `/etc/security`.
The `pam_unix` module uses libxcrypt for local password authentication.
The Screen policy uses `pam_unix`; the `other` policy denies access to
services without an explicit policy. `/usr/sbin/unix_chkpwd` requires
set-user-ID root permissions to authenticate shadow passwords.
