"""Validate optional USB media and QEMU input configuration."""
import contextlib
import importlib.util
import os
import json
from pathlib import Path
import tempfile
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

    def test_launcher_uses_usb_input_and_optional_storage(self):
        lfs.IMAGE.touch()
        executable = self.work / "tools/qemu/bin/qemu-system-x86_64"
        executable.parent.mkdir(parents=True)
        executable.touch()
        image = self.work / "custom.img"
        image.write_bytes(b"existing data")
        for usb in (None, image):
            with self.subTest(usb=usb), \
                 patch.dict(os.environ, MOS_USB_IMAGE=str(usb) if usb else ""), \
                 patch.object(lfs, "qemu_network", return_value=contextlib.nullcontext()), \
                 patch.object(lfs, "run") as run, patch.object(lfs, "NO_GUI", False):
                lfs.qemu(["-display", "none"])
            command = run.call_args.args
            self.assertEqual(run.call_count, 1)
            self.assertIn("i8042=off", command)
            self.assertIn("qemu-xhci,id=usb,p2=8,p3=8", command)
            self.assertIn("usb-kbd,id=usb-keyboard,bus=usb.0,port=1", command)
            self.assertIn("usb-mouse,id=usb-mouse,bus=usb.0,port=2", command)
            self.assertIn("usb-audio,id=usb-audio,bus=usb.0,port=4,audiodev=audio0,buffer=65536", command)
            if usb is None:
                self.assertNotIn("-blockdev", command)
                self.assertFalse(any(arg.startswith("usb-storage,") for arg in command))
                self.assertFalse((self.work / "qemu-hd/usb-data.img").exists())
            else:
                self.assertIn(json.dumps({"driver": "file", "node-name": "usb-file", "filename": str(usb)}), command)
                self.assertIn(json.dumps({"driver": "raw", "node-name": "usbdata", "file": "usb-file"}), command)
                self.assertIn("usb-storage,id=usb-disk,bus=usb.0,port=3,drive=usbdata,removable=true", command)
            self.assertIn(f"file={lfs.IMAGE},format=raw,if=ide,index=0,media=disk", command)
            self.assertEqual(image.read_bytes(), b"existing data")

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
        with patch.object(lfs, "qemu_camera", return_value=camera), \
             patch.object(lfs, "qemu_camera_access", return_value=contextlib.nullcontext()) as access, \
             patch.object(lfs, "qemu_network", return_value=contextlib.nullcontext()), \
             patch.object(lfs, "run") as run, patch.object(lfs, "NO_GUI", True):
            lfs.qemu(["-display", "none"])
        access.assert_called_once_with(camera)
        self.assertIn(camera[0], run.call_args.args)


if __name__ == "__main__":
    unittest.main()
