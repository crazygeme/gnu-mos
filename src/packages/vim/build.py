import os, subprocess, tarfile
from pathlib import Path
w=Path(os.environ["LFS_WORKSPACE"]); s=Path(os.environ["LFS_SOURCES"]); root=Path(os.environ["LFS_SYSROOT"]); src=w/"build/vim-9.1.1590"
if not src.exists():
    with tarfile.open(s/"vim-9.1.1590.tar.gz") as f: f.extractall(w/"build", filter="data")
env=os.environ.copy(); env.update({"CC":"i686-lfs-linux-gnu-gcc","CFLAGS":"-m32"})
subprocess.run([str(src/"configure"),"--prefix=/usr","--with-features=small","--without-x","--disable-gui","--disable-nls"],cwd=src,env=env,check=True)
subprocess.run(["make","-j"+str(os.cpu_count() or 1)],cwd=src,env=env,check=True)
subprocess.run(["make","DESTDIR="+str(root),"install"],cwd=src,env=env,check=True)
