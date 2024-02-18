# kenrel-hack-sandbox

Sandbox manager for linux kernel. Build the Linux kernel and Busybox from source.

## Usage

- If you do not enable the "Build static binary" build option for Busybox, a kernel panic will occur at boot time.

```sh
python3 ./main.py create-sandbox --kernel-version <VERSION> --sandbox-name <NAME>
python3 ./main.py run-sandbox --name <NAME>
```
