import click
import subprocess
import os

REPOS_DIR = "./repos"
BUSYBOX_DIR = f"{REPOS_DIR}/busybox"
LINUX_DIR = f"{REPOS_DIR}/linux"

SANDBOX_DIR = "./sandbox"
BZIMAGE_NAME = "bzImage"
ROOTFS_NAME = "rootfs.img"
ROOTFS_BACKUP_NAME = "rootfs_backup.img"
MNT_DIR_NAME = "mnt"

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
@click.option("--kernel-version", required=True, type=str)
@click.option("--sandbox-name", required=True, type=str)
def create_sandbox(kernel_version: str, sandbox_name: str):
    linux_dir = linux_version_dir(kernel_version)
    sandbox_dir = f"{SANDBOX_DIR}/{sandbox_name}"

    if not download_busybox():
        return

    if not download_linux(kernel_version):
        return

    if os.path.exists(sandbox_dir):
        click.echo("Sandbox already exists", err=True)
        return

    run_shell_cmd(f"mkdir -p {sandbox_dir}")

    # build busybox
    if not os.path.exists(f"{sandbox_dir}/{ROOTFS_NAME}"):
        run_shell_cmd("make menuconfig", dir=BUSYBOX_DIR)
        run_shell_cmd("make install", dir=BUSYBOX_DIR)
        run_shell_cmd(
            "find . | cpio -o --format=newc > ../rootfs.img",
            dir=f"{BUSYBOX_DIR}/_install",
        )
        run_shell_cmd(f"cp {BUSYBOX_DIR}/rootfs.img {sandbox_dir}")

    # buid linux (x86_64 only)
    if not os.path.exists(f"{sandbox_dir}/{BZIMAGE_NAME}"):
        run_shell_cmd("cp ./arch/x86/configs/x86_64_defconfig ./.config", dir=linux_dir)
        run_shell_cmd("make menuconfig", dir=linux_dir)
        run_shell_cmd("make -j$(nproc)", dir=linux_dir)
        run_shell_cmd(f"cp {linux_dir}/arch/x86_64/boot/bzImage {sandbox_dir}")


@cmd.command()
@click.option("--name", required=True, type=str)
def run_sandbox(name):
    sandbox_dir = f"{SANDBOX_DIR}/{name}"

    if not os.path.exists(sandbox_dir):
        click.echo("Sandbox is not exists", err=True)
        return

    # include ./mnt into rootfs.img
    if os.path.exists(f"{sandbox_dir}/{MNT_DIR_NAME}"):
        run_shell_cmd(f"cp ./{ROOTFS_NAME} ./{ROOTFS_BACKUP_NAME}", dir=sandbox_dir)
        run_shell_cmd(
            f"find ./{MNT_DIR_NAME} | cpio -o -H newc -A -F ./{ROOTFS_NAME}",
            dir=sandbox_dir,
        )

    run_shell_cmd(
        f'qemu-system-x86_64 -kernel ./{BZIMAGE_NAME} -initrd ./{ROOTFS_NAME} -append "rdinit=/bin/sh" -serial mon:stdio',
        dir=sandbox_dir,
    )

    if os.path.exists(f"{sandbox_dir}/{ROOTFS_BACKUP_NAME}"):
        run_shell_cmd(f"cp ./{ROOTFS_BACKUP_NAME} ./{ROOTFS_NAME}", dir=sandbox_dir)
        run_shell_cmd(f"rm ./{ROOTFS_BACKUP_NAME}", dir=sandbox_dir)


@cmd.command()
@click.option("--name", required=True, type=str)
def remove_sandbox(name):
    sandbox_dir = f"{SANDBOX_DIR}/{name}"

    if not os.path.exists(sandbox_dir):
        click.echo("Sandbox is not exists", err=True)
        return

    run_shell_cmd(f"rm -rf {sandbox_dir}")


@cmd.command()
def list_sandbox():
    for file_name in os.listdir(SANDBOX_DIR):
        if os.path.isdir(f"{SANDBOX_DIR}/{file_name}"):
            click.echo(f'"{file_name}"')


@cmd.command()
def clean_repos():
    run_shell_cmd(f"rm -rf {REPOS_DIR}")


def main():
    cmd()


if __name__ == "__main__":
    main()
