import os, subprocess, tarfile
from pathlib import Path
w=Path(os.environ["LFS_WORKSPACE"]); s=Path(os.environ["LFS_SOURCES"]); root=Path(os.environ["LFS_SYSROOT"]); src=w/"build/openssh-10.0p1"
if not src.exists():
    with tarfile.open(s/"openssh-10.0p1.tar.gz") as f: f.extractall(w/"build", filter="data")
env=os.environ.copy(); env.update({"CC":"i686-lfs-linux-gnu-gcc","AR":"i686-lfs-linux-gnu-ar","RANLIB":"i686-lfs-linux-gnu-ranlib","STRIP":"i686-lfs-linux-gnu-strip","CFLAGS":"-m32"})
subprocess.run([str(src/"configure"),"--prefix=/usr","--sysconfdir=/etc/ssh","--disable-strip","--without-pam"],cwd=src,env=env,check=True)
subprocess.run(["make","-j"+str(os.cpu_count() or 1)],cwd=src,env=env,check=True)
subprocess.run(["make","DESTDIR="+str(root),"install"],cwd=src,env=env,check=True)
