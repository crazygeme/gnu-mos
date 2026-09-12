import os, subprocess, tarfile
from pathlib import Path
w=Path(os.environ["LFS_WORKSPACE"]); s=Path(os.environ["LFS_SOURCES"]); root=Path(os.environ["LFS_SYSROOT"]); src=w/"build/vim-9.1.1590"
if not src.exists():
    with tarfile.open(s/"vim-9.1.1590.tar.gz") as f: f.extractall(w/"build", filter="data")
config_site = src / "config.site"
config_site.write_text(
    "ac_cv_sizeof_int=4\n"
    "ac_cv_sizeof_long=4\n"
    "ac_cv_sizeof_time_t=4\n"
    "ac_cv_sizeof_off_t=8\n",
    "ac_cv_c_uint32_t='unsigned int'\n",
    encoding="ascii",
)
env=os.environ.copy(); env.update({"CC":"i686-lfs-linux-gnu-gcc","AR":"i686-lfs-linux-gnu-ar","RANLIB":"i686-lfs-linux-gnu-ranlib","STRIP":"i686-lfs-linux-gnu-strip","CFLAGS":"-m32","LDFLAGS":"--sysroot="+str(root),"CONFIG_SITE":str(config_site)})
subprocess.run([str(src/"configure"),"--prefix=/usr","--with-features=normal","--disable-nls","--with-tlib=ncursesw"],cwd=src,env=env,check=True)
subprocess.run(["make","-j"+str(os.cpu_count() or 1)],cwd=src,env=env,check=True)
subprocess.run(["make","DESTDIR="+str(root),"install"],cwd=src,env=env,check=True)
