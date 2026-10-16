"""Validate persistent USB media creation and QEMU input configuration."""
import contextlib
import importlib.util
import os
import json
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("usb_lfs", ROOT / "src/lfs.py")
lfs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lfs)


class USBMedia(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        overrides = patch.multiple(lfs, WORK=self.work, IMAGE=self.work / "system.img")
        overrides.start()
        self.addCleanup(overrides.stop)
        env = patch.dict(os.environ)
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("MOS_USB_IMAGE", None)
        os.environ["MOS_USB_CAMERA"] = "none"

    def test_created_filesystem_and_persistent_contents(self):
        image = lfs.qemu_usb_image()
        self.assertEqual(image.stat().st_size, 128 * 1024 * 1024)
        metadata = subprocess.check_output(
            ["debugfs", "-R", "stat /", str(image)], text=True, stderr=subprocess.DEVNULL
        )
        self.assertIn("Mode:  01777", metadata)
        with image.open("r+b") as output:
            output.seek(1080)
            self.assertEqual(output.read(2), b"\x53\xef")
            output.seek(-512, 2)
            output.write(b"persistent USB data")
        with patch.object(lfs, "run") as run:
            self.assertEqual(lfs.qemu_usb_image(), image)
            run.assert_not_called()
        with image.open("rb") as source:
            source.seek(-512, 2)
            self.assertEqual(source.read(19), b"persistent USB data")

    def test_format_failure_does_not_publish_partial_media(self):
        with patch.object(lfs, "run", side_effect=RuntimeError("format failed")):
            with self.assertRaises(RuntimeError):
                lfs.qemu_usb_image()
        self.assertFalse((self.work / "qemu-hd/usb-data.img").exists())
        self.assertEqual(list((self.work / "qemu-hd").glob("usb-data-*.img")), [])

    def test_custom_image_is_never_formatted(self):
        image = self.work / "custom.img"
        image.write_bytes(b"existing data")
        with patch.dict(os.environ, MOS_USB_IMAGE=str(image)), patch.object(lfs, "run") as run:
            self.assertEqual(lfs.qemu_usb_image(), image)
            run.assert_not_called()
        self.assertEqual(image.read_bytes(), b"existing data")
        image.unlink()
        with patch.dict(os.environ, MOS_USB_IMAGE=str(image)):
            with self.assertRaises(SystemExit):
                lfs.qemu_usb_image()

    def test_launcher_uses_usb_input_and_separate_storage(self):
        lfs.IMAGE.touch()
        executable = self.work / "tools/qemu/bin/qemu-system-x86_64"
        executable.parent.mkdir(parents=True)
        executable.touch()
        usb = self.work / "usb.img"
        with patch.object(lfs, "qemu_usb_image", return_value=usb), \
             patch.object(lfs, "qemu_network", return_value=contextlib.nullcontext()), \
             patch.object(lfs, "run") as run, patch.object(lfs, "NO_GUI", True):
            lfs.qemu(["-display", "none"])
        command = run.call_args.args
        self.assertIn("i8042=off", command)
        self.assertIn("qemu-xhci,id=usb,p2=8,p3=8", command)
        self.assertIn("usb-kbd,id=usb-keyboard,bus=usb.0,port=1", command)
        self.assertIn("usb-mouse,id=usb-mouse,bus=usb.0,port=2", command)
        self.assertIn("usb-audio,id=usb-audio,bus=usb.0,port=4,audiodev=audio0,buffer=65536", command)
        self.assertIn(json.dumps({"driver": "file", "node-name": "usb-file", "filename": str(usb)}), command)
        self.assertIn(json.dumps({"driver": "raw", "node-name": "usbdata", "file": "usb-file"}), command)
        self.assertIn("usb-storage,id=usb-disk,bus=usb.0,port=3,drive=usbdata,removable=true", command)
        self.assertIn(f"file={lfs.IMAGE},format=raw,if=ide,index=0,media=disk", command)

    def test_camera_selection_is_validated(self):
        self.assertIsNone(lfs.qemu_camera())
        with patch.dict(os.environ, MOS_USB_CAMERA="invalid-device"):
            with self.assertRaisesRegex(SystemExit, "BUS:PORT"):
                lfs.qemu_camera()
        with patch.dict(os.environ, MOS_USB_CAMERA="99999:99999"):
            with self.assertRaisesRegex(SystemExit, "unavailable"):
                lfs.qemu_camera()

    def test_camera_is_added_to_the_usb_controller(self):
        lfs.IMAGE.touch()
        executable = self.work / "tools/qemu/bin/qemu-system-x86_64"
        executable.parent.mkdir(parents=True)
        executable.touch()
        camera = ("usb-host,id=usb-camera,bus=usb.0,port=5,hostbus=3,hostport=6", Path("/dev/bus/usb/003/003"))
        with patch.object(lfs, "qemu_usb_image", return_value=self.work / "usb.img"), \
             patch.object(lfs, "qemu_camera", return_value=camera), \
             patch.object(lfs, "qemu_camera_access", return_value=contextlib.nullcontext()) as access, \
             patch.object(lfs, "qemu_network", return_value=contextlib.nullcontext()), \
             patch.object(lfs, "run") as run, patch.object(lfs, "NO_GUI", True):
            lfs.qemu(["-display", "none"])
        access.assert_called_once_with(camera)
        self.assertIn(camera[0], run.call_args.args)


if __name__ == "__main__":
    unittest.main()
