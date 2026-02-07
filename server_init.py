#!/usr/bin/env python3
import subprocess
import shutil
import sys
import os


def run(cmd):
    """执行命令，遇到错误抛异常"""
    subprocess.run(cmd, shell=True, check=True)


def tty_input(prompt):
    """从终端读取输入，即使stdin被占用"""
    try:
        with open("/dev/tty", "r") as tty:
            print(prompt, end="", flush=True)
            return tty.readline().strip()
    except Exception:
        raise RuntimeError("当前环境不支持交互输入，请使用curl下载后再运行")


def check_root():
    if os.geteuid() != 0:
        print("请使用root权限运行：sudo python3 server_init.py")
        sys.exit(1)


def change_ssh_port():
    ssh_config = "/etc/ssh/sshd_config"
    backup = ssh_config + ".bak"

    port = tty_input("请输入新的SSH端口: ").strip()
    if not port.isdigit():
        print("端口号必须是数字")
        return

    shutil.copy(ssh_config, backup)
    lines = [line for line in open(ssh_config) if not line.strip().startswith("Port")]
    lines.append(f"\nPort {port}\n")
    with open(ssh_config, "w") as f:
        f.writelines(lines)

    run("systemctl restart ssh || systemctl restart sshd")
    print(f"SSH端口已修改为 {port}")
    print("请确保防火墙已放行该端口！")


def update_system():
    print("更新系统并清理...")
    run("apt update && apt upgrade -y && apt autoremove -y && apt clean")
    print("系统更新完成")


def install_ufw():
    run("apt install ufw -y && ufw enable")
    print("UFW已安装并启用")


def firewall_manage():
    action = tty_input("请输入动作 (allow/deny/delete): ").lower()
    port = tty_input("请输入端口号: ").strip()
    if action not in ("allow", "deny", "delete") or not port.isdigit():
        print("无效输入")
        return
    run(f"ufw {action} {port}/tcp")
    print(f"防火墙已 {action} {port}")


def clear_logs_cache():
    print("清理系统日志和缓存...")
    run("journalctl --vacuum-time=3d || true")
    run("rm -rf /var/log/*.log /var/cache/apt/archives/* || true")
    print("日志和缓存已清理")


def change_timezone():
    print("当前时间与时区:")
    run("timedatectl")
    print("""
请选择时区：
1. Asia/Shanghai
2. Asia/Tokyo
3. Asia/Singapore
4. UTC
5. 手动输入
0. 取消
""")
    choice = tty_input("请选择: ")
    tz_map = {"1": "Asia/Shanghai", "2": "Asia/Tokyo", "3": "Asia/Singapore", "4": "UTC"}

    if choice == "0":
        return
    if choice == "5":
        timezone = tty_input("请输入时区（如Europe/London）: ").strip()
    else:
        timezone = tz_map.get(choice)

    if not timezone:
        print("无效选择")
        return
    run(f"timedatectl set-timezone {timezone}")
    print(f"时区已修改为 {timezone}")


def install_nginx():
    run("apt install nginx -y && systemctl enable nginx && systemctl start nginx")
    print("Nginx 已安装并启动")


def uninstall_nginx():
    run("systemctl stop nginx || true && apt remove nginx -y")
    print("Nginx已卸载")


def install_nftables():
    run("apt install nftables -y && systemctl enable nftables && systemctl start nftables")
    print("nftables 已安装并启动")


def uninstall_nftables():
    run("systemctl stop nftables || true && apt remove nftables -y")
    print("nftables 已卸载")


def auto_ipv6_priority():
    gai_conf = "/etc/gai.conf"
    backup = gai_conf + ".bak"
    if os.path.exists(gai_conf):
        shutil.copy(gai_conf, backup)
    with open(gai_conf, "a") as f:
        f.write("\nprecedence ::ffff:0:0/96  100\n")
    print("已配置IPv6优先连接")


def change_current_password():
    print("修改当前用户密码")
    run("passwd")
    print("密码修改完成")


ACTIONS = {
    "1": ("更改 SSH 端口", change_ssh_port),
    "2": ("系统更新和清理", update_system),
    "3": ("安装并启用 UFW", install_ufw),
    "4": ("防火墙端口管理", firewall_manage),
    "5": ("清除系统日志和缓存", clear_logs_cache),
    "6": ("查看或修改当前时区", change_timezone),
    "7": ("安装 Nginx", install_nginx),
    "8": ("卸载 Nginx", uninstall_nginx),
    "9": ("安装 nftables", install_nftables),
    "10": ("卸载 nftables", uninstall_nftables),
    "11": ("自动优先选择 IPv6 连接", auto_ipv6_priority),
    "12": ("修改当前用户登录密码", change_current_password)
}


def show_menu():
    print("\n==============================")
    print(" Linux 服务器初始化工具")
    print("==============================")
    for k, v in sorted(ACTIONS.items(), key=lambda x: int(x[0])):
        print(f"{k}. {v[0]}")
    print("0. 退出")
    print("==============================")


def main():
    check_root()
    while True:
        show_menu()
        choice = tty_input("请选择操作: ")
        if choice == "0":
            print("已退出")
            sys.exit(0)
        action = ACTIONS.get(choice)
        if not action:
            print("无效选择")
            continue
        print(f"\n正在执行：{action[0]}")
        try:
            action[1]()
        except Exception as e:
            print(f"执行失败: {e}")
        print("执行完成\n")


if __name__ == "__main__":
    main()
