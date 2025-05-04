import click
import subprocess
import os
import toml

REPOS_DIR = "./repos"
BUSYBOX_DIR = f"{REPOS_DIR}/busybox"
LINUX_DIR = f"{REPOS_DIR}/linux"

SANDBOX_DIR = "./sandbox"
BZIMAGE_NAME = "bzImage"
ROOTFS_NAME = "rootfs.img"
SANDBOX_SPEC_NAME = "spec.toml"
MNT_DIR_NAME = "mnt"

QEMU_ARGS = [
    f"-kernel ./{BZIMAGE_NAME}",
    f"-initrd ./{ROOTFS_NAME}",
    "-append 'rdinit=/bin/sh console=ttyS0'",
    "-serial mon:stdio",
    "-monitor telnet::5678,server,nowait",
    "-gdb tcp::3333",
]

BUSYBOX_GIT = "https://git.busybox.net/busybox.git"
LINUX_GIT = "https://github.com/torvalds/linux.git"


def linux_version_dir(version: str) -> str:
    return f"{LINUX_DIR}/{version}"


def run_shell_cmd(cmd: str, dir: str = "./") -> bool:
    print(f"\033[32m{cmd}\033[0m")
    cp = subprocess.run(cmd, shell=True, cwd=dir)
    return cp.returncode == 0


def download_busybox() -> bool:
    if os.path.exists(BUSYBOX_DIR):
        print(f'Directory "{BUSYBOX_DIR}" already exists')
        return True

    run_shell_cmd(f"mkdir -p {BUSYBOX_DIR}")
    success = run_shell_cmd(f"git clone {BUSYBOX_GIT} {BUSYBOX_DIR}")

    if not success:
        print("Failed to download busybox")
        run_shell_cmd(f"rm -rf {BUSYBOX_DIR}")

    return success


def download_linux(version: str) -> bool:
    d = linux_version_dir(version)

    if os.path.exists(d):
        print(f'Directory "{d}" already exists')
        return True

    run_shell_cmd(f"mkdir -p {d}")
    success = run_shell_cmd(f"git clone {LINUX_GIT} -b {version} --depth 1 {d}")

    if not success:
        print("Failed to download linux")
        run_shell_cmd(f"rm -rf {d}")

    return success


@click.group()
def cmd():
    pass


@cmd.command()
@click.option("--name", required=True, type=str)
@click.option("--kernel-version", required=True, type=str)
def create(
    name: str,
    kernel_version: str,
):
    sandbox_dir = f"{SANDBOX_DIR}/{name}"
    spec_path = f"{sandbox_dir}/{SANDBOX_SPEC_NAME}"

    if os.path.exists(spec_path):
        click.echo("Sandbox already exists", err=True)

    else:
        run_shell_cmd(f"mkdir -p {sandbox_dir}")
        # generate sandbox spec
        spec = f'name = "{name}"\nkernel_version = "{kernel_version}"\n'
        with open(spec_path, "w") as f:
            f.write(spec)
        click.echo(f"Sandbox spec created at {spec_path}")


@cmd.command()
@click.option("--name", required=True, type=str)
def run(name):
    sandbox_dir = f"{SANDBOX_DIR}/{name}"
    spec_path = f"{sandbox_dir}/{SANDBOX_SPEC_NAME}"

    if not os.path.exists(spec_path):
        click.echo("Sandbox spec is not exists", err=True)
        return

    # parse spec
    spec = toml.load(spec_path)
    kernel_version = spec.get("kernel_version")
    kernel_buildconfig = spec.get("kernel_buildconfig")
    force_rebuild = spec.get("force_rebuild", False)

    if not kernel_version:
        click.echo("Kernel version is not specified in the spec", err=True)
        return

    if not download_linux(kernel_version):
        click.echo("Failed to download linux", err=True)
        return

    if not download_busybox():
        click.echo("Failed to download busybox", err=True)
        return

    linux_dir = linux_version_dir(kernel_version)
    rootfs_path = f"{sandbox_dir}/{ROOTFS_NAME}"
    bzimage_path = f"{sandbox_dir}/{BZIMAGE_NAME}"
    mnt_path = f"{sandbox_dir}/{MNT_DIR_NAME}"

    if (not os.path.exists(rootfs_path)) or force_rebuild:
        copied_mnt = False

        # build busybox
        run_shell_cmd("make menuconfig", dir=BUSYBOX_DIR)
        run_shell_cmd("make install", dir=BUSYBOX_DIR)

        # include mnt dir
        if os.path.exists(mnt_path):
            run_shell_cmd(f"cp -r {mnt_path} {BUSYBOX_DIR}/_install")
            copied_mnt = True

        run_shell_cmd(
            f"find . | cpio -o --format=newc | gzip > ../{ROOTFS_NAME}",
            dir=f"{BUSYBOX_DIR}/_install",
        )
        run_shell_cmd(f"cp {BUSYBOX_DIR}/{ROOTFS_NAME} {sandbox_dir}")

        if copied_mnt:
            # remove mnt dir from busybox/_install
            run_shell_cmd(f"rm -rf {BUSYBOX_DIR}/_install/{MNT_DIR_NAME}")

    # build linux (x86_64 only)
    if (not os.path.exists(bzimage_path)) or force_rebuild:
        run_shell_cmd("make clean", dir=linux_dir)
        run_shell_cmd("cp ./arch/x86/configs/x86_64_defconfig ./.config", dir=linux_dir)

        # apply kernel buildconfig
        if kernel_buildconfig:
            with open(f"{linux_dir}/.config", "a") as f:
                for config in kernel_buildconfig:
                    f.write(f"{config}\n")
            run_shell_cmd("make olddefconfig", dir=linux_dir)
            run_shell_cmd("make localmodconfig", dir=linux_dir)
        else:
            run_shell_cmd("make menuconfig", dir=linux_dir)

        run_shell_cmd("make -j$(nproc)", dir=linux_dir)
        run_shell_cmd(f"cp {linux_dir}/arch/x86_64/boot/bzImage {sandbox_dir}")

    run_shell_cmd(
        f"qemu-system-x86_64 {' '.join(QEMU_ARGS)}",
        dir=sandbox_dir,
    )


@cmd.command()
@click.option("--name", required=True, type=str)
def remove(name):
    sandbox_dir = f"{SANDBOX_DIR}/{name}"

    if not os.path.exists(sandbox_dir):
        click.echo("Sandbox is not exists", err=True)
        return

    run_shell_cmd(f"rm -rf {sandbox_dir}")


@cmd.command()
def list():
    for file_name in os.listdir(SANDBOX_DIR):
        sandbox_dir = f"{SANDBOX_DIR}/{file_name}"
        if os.path.isdir(sandbox_dir):
            spec_path = f"{sandbox_dir}/{SANDBOX_SPEC_NAME}"
            if not os.path.exists(spec_path):
                continue

            spec = toml.load(spec_path)
            name = spec.get("name")
            kernel_version = spec.get("kernel_version")

            click.echo(f"{name} - kernel version: {kernel_version}")


@cmd.command()
def clean():
    run_shell_cmd(f"rm -rf {REPOS_DIR}")


def main():
    cmd()


if __name__ == "__main__":
    main()
