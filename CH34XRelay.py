# -*- coding: utf-8 -*-
import serial
import time
import glob

MAX_RETRIES = 5
WAIT_SECONDS = 3

class CH341Relay:
    def __init__(self, port=None, baudrate=9600, timeout=0.5):
        """初始化串口并自动检测设备"""
        self.port = None
        if not port:
            for attempt in range(1, MAX_RETRIES + 1):
              print(f"正在检测 CH341 设备...")
              self.port = self.find_ch341_port()
              if self.port:
                  print(f"检测到 CH341 设备: {self.port}")
                  break
              else:
                  print(f"未检测到设备，第 {attempt} 次尝试，等待 {WAIT_SECONDS} 秒...")
                  time.sleep(WAIT_SECONDS)
            # else 对应 for 循环，只有在循环没有 break 时才执行（即一直没检测到设备）。
            else:
                print("未检测到 CH341 设备，检测结束。")
        else:
          self.port = port
        self.baudrate = baudrate
        self.ser = None

        if not self.port:
            print("❌ 未找到 CH341 设备，请检查连接或驱动。")
            return

        try:
            self.ser = serial.Serial(self.port, baudrate, timeout=timeout)
            print(f"✅ 已打开串口：{self.port}，波特率：{baudrate}")
        except serial.SerialException as e:
            print(f"❌ 打开串口失败：{e}")

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
            return
        data = bytes.fromhex(cmd_hex)
        self.ser.write(data)
        print(f"➡️ 发送指令: {cmd_hex}")
        time.sleep(0.05)

    def open_channel(self, ch=1, feedback=False):
        """打开指定通道"""
        cmd = f"A0 {ch:02X} {'03' if feedback else '01'} {0xA0 + ch + (3 if feedback else 1):02X}"
        self._send_cmd(cmd)
        print(f"🟢 打开第{ch}路{'(反馈)' if feedback else ''}")

    def close_channel(self, ch=1, feedback=False):
        """关闭指定通道"""
        cmd = f"A0 {ch:02X} {'02' if feedback else '00'} {0xA0 + ch + (2 if feedback else 0):02X}"
        self._send_cmd(cmd)
        print(f"🔴 关闭第{ch}路{'(反馈)' if feedback else ''}")

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
            print("✅ 串口已关闭")

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
            time.sleep(1)
