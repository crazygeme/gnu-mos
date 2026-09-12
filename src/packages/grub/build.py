import os, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]))
from package_lib import archive_source
src=archive_source("grub","grub-2.14.tar.xz","grub-2.14"); b=Path(os.environ["LFS_WORKSPACE"])/"build/grub-build"; b.mkdir(parents=True,exist_ok=True)
env = os.environ.copy()
tools = Path(os.environ["LFS_WORKSPACE"]) / "tools"
env["PATH"] = str(tools / "bin") + ":/usr/bin:/bin:" + env.get("PATH", "")
subprocess.run([str(src/"configure"),"--prefix=/usr","--target=i386","--with-platform=pc","--disable-werror"],cwd=b,env=env,check=True)
subprocess.run(["make","-j"+str(os.cpu_count() or 1)],cwd=b,env=env,check=True)
subprocess.run(["make","DESTDIR="+os.environ["LFS_SYSROOT"],"install"],cwd=b,env=env,check=True)
