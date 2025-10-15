# -*- coding: utf-8 -*-
import serial
import time
import glob
import threading
import pyudev

MAX_RETRIES = 5
WAIT_SECONDS = 3

class CH341Relay:
    def __init__(self, port=None, baudrate=9600, timeout=0.5):
        self.port = port or self.find_ch341_port()
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self._open_serial()

    def _open_serial(self):
        """打开串口"""
        if not self.port:
            print("❌ 未检测到 CH341 设备。")
            return
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            print(f"✅ 已打开串口：{self.port}")
        except serial.SerialException as e:
            print(f"⚠️ 打开串口失败：{e}")
            self.ser = None

    @staticmethod
    def find_ch341_port():
        """自动查找可用的 CH341 设备号"""
        ports = glob.glob("/dev/ttyCH341*") + glob.glob("/dev/ttyUSB*")
        if not ports:
            return None
        print("🔍 检测到串口设备：", ports)
        # 逐个尝试打开验证
        for port in ports:
            try:
                s = serial.Serial(port, 9600, timeout=0.5)
                s.close()
                print(f"✅ 串口可用：{port}")
                return port
            except Exception:
                pass
        print("⚠️ 检测到串口但无法打开。")
        return None

    def _send_cmd(self, cmd_hex):
        """发送十六进制指令"""
        if not self.ser or not self.ser.is_open:
            print("⚠️ 串口未打开，无法发送指令。")
            return False
        data = bytes.fromhex(cmd_hex)
        self.ser.write(data)
        print(f"➡️ 发送指令: {cmd_hex}")
        time.sleep(0.05)
        return True

    def reopen_if_needed(self):
        """检测设备是否仍然存在，如果消失则清理"""
        if not self.ser:
            return False
        if not self.ser.is_open:
            print("⚠️ 串口意外关闭。")
            self.ser = None
            return False
        if not glob.glob(self.port):
            print(f"⚠️ 设备 {self.port} 已被拔出。")
            self.close()
            return False
        return True
    
    def open_channel(self, ch=1, feedback=False):
        """打开指定通道"""
        if self.reopen_if_needed():
            cmd = f"A0 {ch:02X} {'03' if feedback else '01'} {0xA0 + ch + (3 if feedback else 1):02X}"
            ok = self._send_cmd(cmd)
            print(f"🟢 打开第{ch}路{'(反馈)' if feedback else ''}")
            return ok
        return False

    def close_channel(self, ch=1, feedback=False):
        """关闭指定通道"""
        if self.reopen_if_needed():
            cmd = f"A0 {ch:02X} {'02' if feedback else '00'} {0xA0 + ch + (2 if feedback else 0):02X}"
            ok = self._send_cmd(cmd)
            print(f"🔴 关闭第{ch}路{'(反馈)' if feedback else ''}")
            return ok
        return False

    def toggle_channel(self, ch=1):
        """取反开关状态并反馈"""
        cmd = f"A0 {ch:02X} 04 {0xA0 + ch + 4:02X}"
        self._send_cmd(cmd)
        print(f"🔁 取反第{ch}路开关状态")

    def query_status(self, ch=1):
        """查询通道状态"""
        cmd = f"A0 {ch:02X} 05 {0xA0 + ch + 5:02X}"
        self._send_cmd(cmd)
        print(f"📨 查询第{ch}路状态")
        time.sleep(0.2)
        data = self.ser.read_all()
        if data:
            print("返回数据:", data.hex(' ').upper())
        else:
            print("未收到反馈。")

    def close(self):
        """关闭串口"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.ser = None
            print("✅ 串口已关闭")

class CH341RelayMonitor:
    """使用 pyudev 实时监听 USB 设备插拔事件"""
    def __init__(self):
        self.relay = CH341Relay()
        self.monitor_thread = threading.Thread(target=self._monitor_usb, daemon=True)
        self.monitor_thread.start()

    def _monitor_usb(self):
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by(subsystem='tty')

        # print("🔍 正在监控 CH341 设备插拔事件...")
        # for device in monitor:
        #     try:
        #         devname = device.device_node or ""
        #         if "ttyUSB" not in devname and "ttyCH341" not in devname:
        #             continue

        #         if device.action == 'remove':
        #             print(f"❌ 检测到设备拔出: {devname}")
        #             self.relay.close()

        #         elif device.action == 'add':
        #             print(f"✅ 检测到设备插入: {devname}")
        #             time.sleep(1)  # 等系统创建节点
        #             self.relay.close()
        #             new_port = CH341Relay.find_ch341_port()
        #             if new_port:
        #                 print(f"🔁 重新连接到 {new_port}")
        #                 self.relay = CH341Relay(new_port)
        #             else:
        #                 print("⚠️ 未找到新的 CH341 设备。")
        #     except Exception as e:
        #         print(f'monitor error: {str(e)}')

        print("🔍 启动 USB 监控线程...")

        for device in iter(monitor.poll, None):
            try:
                if device.action == "remove":
                    self._on_usb_removed(device)
                elif device.action == "add":
                    self._on_usb_added(device)
            except Exception as e:
                print(f"⚠️ 监控异常: {e}")
    
    # -------------------------------------------------------
    # 插拔事件处理
    # -------------------------------------------------------
    def _on_usb_removed(self, device):
        """检测到 USB 设备拔出"""
        vendor = device.get("ID_VENDOR_ID", "")
        product = device.get("ID_MODEL_ID", "")
        if "1a86" in vendor.lower():  # 1A86 是 CH341 芯片厂商ID
            print(f"❌ 检测到设备拔出: {vendor}:{product}")
            self.relay.close()
            self.relay = None

    def _on_usb_added(self, device):
        """检测到 USB 设备插入"""
        vendor = device.get("ID_VENDOR_ID", "")
        product = device.get("ID_MODEL_ID", "")
        if "1a86" in vendor.lower():  # 1A86 是 WCH（CH341）厂商ID
            print(f"✅ 检测到设备插入: {vendor}:{product}")
            time.sleep(1)  # 等系统创建节点
            if self.relay:
                self.relay.close()
            new_port = CH341Relay.find_ch341_port()
            if new_port:
                print(f"🔁 重新连接到 {new_port}")
                self.relay = CH341Relay(new_port)
            else:
                print("⚠️ 未找到新的 CH341 设备。")
    
    def open_channel(self, ch=1, feedback=False):
        """打开指定通道"""
        if self.relay and self.relay.ser:
            return self.relay.open_channel(ch, feedback)
        return False

    def close_channel(self, ch=1, feedback=False):
        """关闭指定通道"""
        if self.relay and self.relay.ser:
            return self.relay.close_channel(ch, feedback)
        return False

# =============================
# 示例用法
# =============================
if __name__ == "__main__":
    relay = CH341Relay()  # 自动检测 /dev/ttyCH341USB0 或 /dev/ttyUSB0
    if relay.ser:
        while True:
            relay.open_channel(1)
            time.sleep(1)
            relay.close_channel(1)

