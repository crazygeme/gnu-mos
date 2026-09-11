MOS is built as a kernel package. Its userspace is not copied from any
distribution image. The package produces the generic `/boot/kernel` artifact
consumed by GRUB; all userspace files are produced by the LFS package set.
