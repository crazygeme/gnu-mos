export PATH=/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin
export PS1='\u@\h:\w\$ '

if [ -f "$HOME/.bashrc" ]; then
	. "$HOME/.bashrc"
fi
