# kernel-hack-sandbox

A sandbox manager for the Linux kernel. This tool allows you to build the Linux kernel and Busybox from source and manage sandboxes for testing and development.

## Prerequisites

Ensure the following packages are installed on your system:

- Dependencies required to build the Linux kernel and Busybox
- `python3`
- `python-click`
- `qemu` (x86_64)

## Usage

### Creating a Sandbox

Use the following command to create a sandbox:

```sh
python3 ./main.py create --kernel-version <VERSION> --name <NAME>
```

Replace `<VERSION>` with the desired Linux kernel version and `<NAME>` with the name of the sandbox.

### Running a Sandbox

To run an existing sandbox, use:

```sh
python3 ./main.py run --name <NAME>
```

Replace `<NAME>` with the name of the sandbox.

### Removing a Sandbox

To remove a sandbox, use:

```sh
python3 ./main.py remove --name <NAME>
```

### Listing Sandboxes

To list all available sandboxes, use:

```sh
python3 ./main.py list
```

### Cleaning Repositories

To clean up downloaded repositories, use:

```sh
python3 ./main.py clean
```

## Configuration with `spec.toml`

Each sandbox has a `spec.toml` file located in its directory (e.g., `sandbox/<SANDBOX NAME>/spec.toml`). This file allows you to configure various settings for the sandbox. Below is an example configuration:

```toml
name = "sample"
kernel_version = "v6.10"

kernel_buildconfig = [
    "CONFIG_DEBUG_KERNEL=y",
    "CONFIG_DEBUG_INFO=y",
    "CONFIG_RELOCATABLE=n",
]

# force_rebuild = true
init = "/mnt/init"
```

### Explanation of Fields

- `name`: The name of the sandbox.
- `kernel_version`: The version of the Linux kernel to use.
- `kernel_buildconfig`: A list of additional kernel configuration options to apply during the build process.
- `force_rebuild`: (Optional) Set to `true` to force a rebuild of the kernel and root filesystem, even if they already exist.
- `init`: (Optional) Specifies the path to the init binary or script that will be executed as the first process (`PID 1`) inside the sandbox. If not set, `/bin/sh` will be used.

### Important Notes

- When building Busybox, ensure the `Build static binary` option is enabled. If this option is not enabled, a kernel panic will occur during boot.
- If the directory `sandbox/<SANDBOX NAME>/mnt` exists, it will be mounted to `/mnt` inside the sandbox.

## Example Workflow

1. Create a sandbox:

   ```sh
   python3 ./main.py create --kernel-version v6.10 --name sample
   ```

2. Edit the `sandbox/sample/spec.toml` file to customize the configuration.

3. Run the sandbox:

   ```sh
   python3 ./main.py run --name sample
   ```

4. Remove the sandbox when done:

   ```sh
   python3 ./main.py remove --name sample
   ```

## License

This project is licensed under the terms of the [LICENSE](LICENSE) file.
