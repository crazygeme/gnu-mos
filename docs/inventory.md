# 系统枚举命令

系统镜像包含以下设备与系统信息工具。设备名称数据库由 `hwdata` 提供。

| 命令 | 软件包 | 支持的查询 |
| --- | --- | --- |
| `lsusb`、`lsusb -t`、`lsusb -v` | usbutils 019 | USB 设备、接口、拓扑和描述符 |
| `lspci`、`lspci -k`、`lspci -nn` | pciutils 3.15.0 | PCI 设备、设备编号和绑定的内核驱动 |
| `lsblk`、`lsblk -f` | util-linux 2.41.1 | 块设备、分区、文件系统及挂载点 |
| `lscpu` | util-linux 2.41.1 | CPU 数量、硬件特征和拓扑 |
| `lsmem` | util-linux 2.41.1 | 物理内存块及在线状态 |
| `lsirq` | util-linux 2.41.1 | 已注册中断及各 CPU 的累计计数 |
| `lsns` | util-linux 2.41.1 | 进程所属的命名空间 |
| `lslocks` | util-linux 2.41.1 | POSIX 字节范围锁和 BSD 文件锁 |

USB 设备通过 `/sys/bus/usb/devices` 和 `/dev/bus/usb` 发布。usbfs 支持描述符读取、输入方向的控制传输及其完成状态查询。驱动分离、输出方向的控制传输、设备重配置和通用批量、等时传输不属于该接口的支持范围。USB 类驱动通过内核控制器接口访问设备。

CPU 和内存信息由只读 sysfs 属性提供。内存块大小为 128 MiB；内存块不支持热移除。`/proc/interrupts` 提供中断计数，`/proc/locks` 提供当前文件锁的快照。
