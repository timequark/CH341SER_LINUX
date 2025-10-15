// ChangeLog 
// 1.0 - 1.1   modified to solve transmition between ch341 and ch341
// 1.1 - 1.2   Support high Linux kernel
Instructions

Note: 1.Please run followed executable programs as root privilege
      2.Current Driver support versions of linux kernel range from 2.6.25 to 3.13.x
      3.Current Driver support 32bits and 64bits linux systems

Usage:
	(load or unload linux driver of CH34x)
	//compile 
	#make
	//load ch34x chips driver
	#make load
	//unload ch34x chips driver
	#make unload
// 1.2 - 1.3 Fix some bugs			

// 加载驱动
$ insmod ch34x.ko

// 卸载驱动
$ rmmod ch34x

// 查看驱动是否加载成功
$ lsmod | grep ch34x

// 查看设备
dmesg | tail -n 10

// gate-ctl 启动
$ cd /opt/CH341SER_LINUX
$ source .venv/bin/activate
$ python3 api.py

// gate-web 启动
$ cd /opt/gate-web
$ source .venv/bin/activate
$ python3 -m http.server 8080 --directory /opt/gate-web