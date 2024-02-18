# kernel-hack-sandbox

Sandbox manager for Linux kernel. Build Linux kernel and Busybox from source.

## Required packages

- Dependent packages for build Linux kernel and Busybox
- python3
- python-click
- qemu (x86_64)

## Usage

- If you do not enable the `Build static binary` build option for Busybox, a kernel panic will occur at boot time.

```sh
python3 ./main.py create-sandbox --kernel-version <VERSION> --sandbox-name <NAME>
python3 ./main.py run-sandbox --name <NAME>
... and so on
```
