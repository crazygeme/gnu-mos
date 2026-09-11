import os, subprocess, tarfile
from pathlib import Path
w=Path(os.environ["LFS_WORKSPACE"]); s=Path(os.environ["LFS_SOURCES"]); root=Path(os.environ["LFS_SYSROOT"]); src=w/"build/openssl-3.5.2"
if not src.exists():
    with tarfile.open(s/"openssl-3.5.2.tar.gz") as f: f.extractall(w/"build", filter="data")
env=os.environ.copy(); env.update({"CC":"i686-lfs-linux-gnu-gcc","CFLAGS":"-m32"})
subprocess.run(["./Configure","linux-generic32","--prefix=/usr","--openssldir=/etc/ssl","shared"],cwd=src,env=env,check=True)
subprocess.run(["make","-j"+str(os.cpu_count() or 1)],cwd=src,env=env,check=True)
subprocess.run(["make","DESTDIR="+str(root),"install_sw"],cwd=src,env=env,check=True)
