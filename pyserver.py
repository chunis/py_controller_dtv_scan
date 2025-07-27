#!/usr/bin/python3

# Chunis Deng (chunchengfh@gmail.com)

import sys
import socket
import subprocess
import struct
import time
import threading
from plot_dtv_scan_result import plot_dtv_scan
from mac_linkADRReq import send_mac_command_linkadrreq
import mywebhook # for continue_recv, nodes_rx_db


ns_server = "192.168.1.211:8000"
localhost = '127.0.0.1'
listen_port = 1612
scan_result_len = 243
get_freq_len = 88
gw_addr = ""
exit_demo = False

global_node_list = [
    'fe-ff-ff-ff-fd-ff-00-20',
]


def get_own_ip():
    #cmd = "ifconfig | grep inet | grep -v 'inet6' | grep -v '127.0.0.1' | awk '{print $2}' | /bin/grep 192.168"
    cmd = "ifconfig | /bin/grep inet | /bin/grep -v 'inet6' | /bin/grep 192.168 | awk '{print $2}'"
    return subprocess.check_output(cmd, shell=True).strip()


def process_scan_result(data):
    data = data.decode()
    print('got spectral scan result:')
    for x in range(len(data)):
        print(('%s ' %ord(data[x])), end = '')
    print()
    plot_dtv_scan([ord(x) for x in data])

def split_chlist(lst):
    a, b = [], []
    p = a

    for x in lst:
        p.append(x)
        if (x+1) % 16 == 0:
            p = b
    return a, b


# idx_list contains channel lists belongs different groups divided by 16
def assemble_adr_bytes_from_cross(idx_list):
    ret = []
    for slist in split_chlist(idx_list):
        if slist:
            #chmaskcntl = 0x0  # EU868 only supports chmaskcntl = 0
            chmaskcntl = (slist[0] // 16) << 4

            chmask = 0
            for chn in idx_list:
                chmask = chmask | 0x1 << (chn % 16)
            print("chmask: 0x%02x, 0x%02x, chmaskcntl: 0x%02x" %(chmask & 0xff, chmask >> 8, chmaskcntl))
            ret += [0x3, 0xff, chmask & 0xff, chmask >> 8, chmaskcntl]

    print('assemble_adr_bytes_from_cross/ret: %s' %ret)
    return ret;

def assemble_adr_bytes(idx_list):
    #chmaskcntl = (slist[0] // 16) << 4
    chmaskcntl = 0x0  # EU868 only supports chmaskcntl = 0
    chmask = 0
    for chn in idx_list:
        chmask = chmask | 0x1 << (chn % 16)
    print("chmask: 0x%02x, 0x%02x, chmaskcntl: 0x%02x" %(chmask & 0xff, chmask >> 8, chmaskcntl))
    ret = [0x3, 0xff, chmask & 0xff, chmask >> 8, chmaskcntl]
    print('assemble_adr_bytes/ret: %s' %ret)
    return ret;


def obtain_channel_list():
    while True:
        config = input('Which channel(s) do you want to enable?\n' +
                           '[1, 16] seperated by spaces, such as: "1 3 6"\n' +
                           'use "q" to back to upper menu: ')
        config = config.strip()
        if config == '' or config[0].lower() == 'q':
            return

        chanlist = config.split()
        try:
            chanlist = [int(x) for x in chanlist]
        except:
            print("Wrong input. Try again...")
        else:
            break

    obtain_adr_list = assemble_adr_bytes(chanlist)
    #print(chanlist)
    #print(obtain_adr_list)

    return obtain_adr_list


def freq_is_valid(freq_list):
    for freq in freq_list:
        try:
            freq = int(freq)
        except:
            return False
        if freq < 867100000 or freq > 900000000:
            return False
        if (freq - 867100000) % 200000:
            return False
    return True

# return a sequence of freq list from the start of freq
def freq_list_from_start(freq, step=200000, num=4):
    return [freq+step*i for i in range(num)]

# return a sequence of channel list from the start of freq
def channel_list_from_start(freq, step=200000, num=4):
    chan_start = freq - 868100000
    return [(chan_start // step) + i for i in range(num)]


current_rf_freq_hz = []
def process_get_freq(data):
    head = data[:8].decode()
    if head != 'get-freq':
        return

    global current_rf_freq_hz
    current_rf_freq_hz = []
    print('got get-freq head')

    for x in range(2):
        valid, enable, freq_hz = struct.unpack('<BBxxI', data[8+x*8:16+x*8])
        current_rf_freq_hz.append(freq_hz)
        print("valid:", valid)
        print('enable:', enable)
        print('freq_hz:', freq_hz)

    for x in range(8):
        enable, rf_chain, freq_hz = struct.unpack('<BBxxi', data[24+x*8:24+(x+1)*8])
        print('enable:', enable)
        print("rf_chain:", rf_chain)
        print('freq_hz:', freq_hz)

    for x in range(2):
        print("start freq of Rf_%s is %s" %(x, current_rf_freq_hz[x]-300000))


# rf_freq: RF central frequency in Hz
def assemble_set_freq(rfidx, rf_freq):
    if rfidx != 0 and rfidx != 1:
        print("rfidx value wrong")
        return False
    if rf_freq < 867100000 or rf_freq > 900000000:
        print("rf_freq value wrong")
        return False
    if (rf_freq - 863400000) % 200000 != 0:
        print("rf_freq value wrong")
        return False

    data = bytearray(b'set-freq')

    rfdata = [None, None]
    rfdata[  rfidx] = struct.pack('<4BI', 0x1, 0x1, 0x0, 0x0, rf_freq)
    rfdata[1-rfidx] = struct.pack('<4BI', 0x0, 0x0, 0x0, 0x0, 0x0)
    data += rfdata[0]
    data += rfdata[1]

    data1 = bytearray()
    data2 = bytearray()
    for x in range(4):
        data1 += struct.pack('<4Bi', 0x1, rfidx, 0x0, 0x0, -300000+200000*x)
        data2 += struct.pack('<4Bi', 0x0, 0x0, 0x0, 0x0, 0x0)

    ifdata = [None, None]
    ifdata[  rfidx] = data1
    ifdata[1-rfidx] = data2
    data += ifdata[0]
    data += ifdata[1]

    return data


# ask user to provide starting frequency of the 1 or 2 groups
# for example: "863500000 868100000" means below 8 channels:
#   [863.5, 863.7, 863.9, 864.1, 868.1, 868.3, 868.5, 868.7] (MHz)
def obtain_channel_freq_starting():
    while True:
        config = input('\nWhich 4 or 8 channels do you want to switch to?\n' +
                       'provide the freq of each of the starting channels\n' +
                       'For example: "863500000 868100000" means:\n' +
                       '[863.5, 863.7, 863.9, 864.1,   868.1, 868.3, 868.5, 868.7] (MHz)\n' +
                       'if you only want to switch 1 group, then provide the freq of the one you want to keep:\n' +
                           'use "q" to back to upper menu: ')
        config = config.strip()
        if config == '':
            continue
        if config[0].lower() == 'q':
            return

        freq_list = config.replace(',', ' ').split()
        if len(freq_list) != 2:
            print("Needs to provide exactly 2 freqs. try again...")
            continue
        if not freq_is_valid(freq_list):
            print("\nError: freq too big or small, or not a valid one in EU868 freq channel")
            continue

        if abs(int(freq_list[0]) - int(freq_list[1])) < 800000:
            print("WARNING: freq group overlapped")

        return [int(f) for f in freq_list]  # input is valid, so exit from the loop


def check_nodes_all_switched(nodes, freqs):
    print("node list: %s; freq list: %s" %(nodes, freqs))
    nodes_copy = nodes[:]

    while True:
        for node in nodes_copy:
            if node in mywebhook.nodes_rx_db and mywebhook.nodes_rx_db[node] in freqs:
                print("node '%s' received in freq = %s" %(node, mywebhook.nodes_rx_db[node]))
                nodes_copy.remove(node)
        if not nodes_copy:
            print("all nodes are received in the required freq list")
            break

        print('waiting...')
        time.sleep(4)


def switch_freqs(freq, idx):
    freq1 = freq
    freq2 = freq
    if idx == 0 or idx == 1:
        print("need to update freq=%s; keep rf=%s" %(freq1, idx))
    else:
        freq2 = idx  # idx is confusing here, so don't use it any more
        print("need to update freq=%s to rf=0" %freq1)
        print("need to update freq=%s to rf=1" %freq2)

    freq_list_a = freq_list_from_start(freq1)
    freq_list_b = freq_list_from_start(freq2)
    freq_list_rf0 = freq_list_from_start(current_rf_freq_hz[0] - 300000)
    freq_list_rf1 = freq_list_from_start(current_rf_freq_hz[1] - 300000)

    chan_list1 = channel_list_from_start(freq1)
    chan_list2 = channel_list_from_start(freq2)
    chan_list_rf0 = channel_list_from_start(current_rf_freq_hz[0] - 300000)
    chan_list_rf1 = channel_list_from_start(current_rf_freq_hz[1] - 300000)

    print("chan_list1 is: %s" %chan_list1)
    print("chan_list2 is: %s" %chan_list2)
    print("chan_list_rf0 is: %s" %chan_list_rf0)
    print("chan_list_rf1 is: %s" %chan_list_rf1)

    adr_list1 = assemble_adr_bytes(chan_list1)
    adr_list2 = assemble_adr_bytes(chan_list2)
    adr_list_rf0 = assemble_adr_bytes(chan_list_rf0)
    adr_list_rf1 = assemble_adr_bytes(chan_list_rf1)

    if idx == 1:
        freq_list_1 = freq_list_rf1
        obtain_adr_list_1 = adr_list_rf1
        new_freq_for_gw_1 = assemble_set_freq(0, freq1+300000)
        new_freq_for_gw_2 = assemble_set_freq(1, freq2+300000)
    else:
        freq_list_1 = freq_list_rf0
        obtain_adr_list_1 = adr_list_rf0
        new_freq_for_gw_1 = assemble_set_freq(1, freq1+300000)
        new_freq_for_gw_2 = assemble_set_freq(0, freq2+300000)

    if idx == 1:
        freq_list_2 = freq_list_rf1 + freq_list_a
        obtain_adr_list_2 = assemble_adr_bytes(chan_list_rf1 + chan_list1)
        obtain_adr_list_3 = []
    elif idx == 0:
        freq_list_2 = freq_list_rf0 + freq_list_a
        obtain_adr_list_2 = assemble_adr_bytes(chan_list_rf0 + chan_list1)
        obtain_adr_list_3 = []
    else:
        freq_list_2 = freq_list_a + freq_list_b
        obtain_adr_list_2 = assemble_adr_bytes(chan_list1)
        obtain_adr_list_3 = assemble_adr_bytes(chan_list1 + chan_list2)

    # prepare dev_eui list
    deveui_list = []
    for dev in global_node_list:
        deveui_list.append(bytes([int('0x' + t, 16) for t in dev.split('-')]))

    print("\nWe've collected below UL info:")
    for deveui, freq in mywebhook.nodes_rx_db.items():
        print('\t', deveui, '-->', freq)
    mywebhook.nodes_rx_db = {}
    print("Clean it now")

    # step 1: update node with limited channel list
    print("\nstep 1: update node with limited channel list")
    for dev_eui in deveui_list:
        send_mac_command_linkadrreq(ns_server, dev_eui, obtain_adr_list_1)

    # step 2: waiting until all nodes communicate with the limited channel list
    print("\nstep 2: waiting until all nodes communicate with the limited channel list")
    check_nodes_all_switched(global_node_list, freq_list_1)

    # step 3: update gateway with new frequency (half old, half new)
    print("\nstep 3: update gateway with new frequency")
    if new_freq_for_gw_1:
        print("send_set_freq_command(new_freq_for_gw_1)")
        send_set_freq_command(new_freq_for_gw_1)
    else:
        print("something wrong: new_freq_for_gw_1 == False")
    # waiting for 20s for gateway to restart
    time.sleep(20)

    # step 4: update node with new channel list (only half new)
    print("\nstep 4: update node with new channel list")
    for dev_eui in deveui_list:
        send_mac_command_linkadrreq(ns_server, dev_eui, obtain_adr_list_2)

    if idx == 0 or idx == 1:
        print("freq switch finished")
        return

    # step 5: waiting until all nodes communicate with the new channel list
    print("\nstep 5: waiting until all nodes communicate with the new channel list")
    print("Cleaned the saved info...")
    mywebhook.nodes_rx_db = {}
    check_nodes_all_switched(global_node_list, freq_list_a)

    # step 6: update gateway with new frequency (totally new ones)
    print("\nstep 6: update gateway with new frequency")
    if new_freq_for_gw_2:
        send_set_freq_command(new_freq_for_gw_2)

    # waiting for 20s for gateway to restart
    time.sleep(20)


    # step 7: update node with new channel list (totally new ones, or half old and half new)
    print("\nstep 7: update node with new channel list")
    chan_list2 = channel_list_from_start(idx)
    obtain_adr_list_3 = assemble_adr_bytes(chan_list1 + chan_list2)

    for dev_eui in deveui_list:
        send_mac_command_linkadrreq(ns_server, dev_eui, obtain_adr_list_3)

    # step 8: waiting until all nodes communicate with the new channel list
    print("\nstep 8: waiting until all nodes communicate with the new channel list")
    print("Cleaned the saved info...")
    mywebhook.nodes_rx_db = {}
    check_nodes_all_switched(global_node_list, freq_list_2)

    print("\nSwitch Freq function finished.\n")



def do_switch_freqs(freq_list):
    print('freq_list = %s' %freq_list)
    print('current_rf_freq_hz = %s' %current_rf_freq_hz)
    if freq_list[0] == current_rf_freq_hz[0] - 300000:
        switch_freqs(freq_list[1], 0)
    elif freq_list[0] == current_rf_freq_hz[1] - 300000:
        switch_freqs(freq_list[1], 1)
    elif freq_list[1] == current_rf_freq_hz[0] - 300000:
        switch_freqs(freq_list[0], 0)
    elif freq_list[1] == current_rf_freq_hz[1] - 300000:
        switch_freqs(freq_list[0], 1)
    else:
        switch_freqs(freq_list[0], freq_list[1])


# issue command to gateway to do the dtv scan, and return the results back
def send_scan_command():
    sock.sendto(b"dtv-scan", gw_addr)

# issue command to gateway to return its current freq settings
def send_get_freq_command():
    sock.sendto(b"get-freq", gw_addr)

def send_set_freq_command(data):
    sock.sendto(data, gw_addr)

def switch_freq_group():
    send_get_freq_command()
    time.sleep(2)  # waiting for output the response from gateway
    new_freq_list = obtain_channel_freq_starting()
    do_switch_freqs(new_freq_list)

def obtain_command():
    global exit_demo
    time.sleep(1)

    if gw_addr == '':
        print("\nWaiting for gateway to connect...")
    while not gw_addr:
        time.sleep(1)
    print("gateway (%s:%s) connected" %(gw_addr[0], gw_addr[1]))

    while True:
        print('\nMenu:')
        print('\t1. Check Spectrual Scan')
        print('\t2. Switch to new Channel(s)')
        print('\t3. Quit this demo')

        cmd = input('Your choice: ')
        if cmd.strip() == '':
            print("Error. Please choose 1, 2 or 3.")
        elif cmd.strip()[0] == 'a':  # just for internal test purpose
            data = assemble_set_freq(1, 868400000)
            if data:
                send_set_freq_command(data)
        elif cmd.strip()[0] == '0':  # just for internal test purpose
            send_get_freq_command()
        elif cmd.strip()[0] == '1':
            send_scan_command()
        elif cmd.strip()[0] == '2':
            switch_freq_group()
        elif cmd.strip()[0] == '3' or cmd.strip()[0].lower() == 'q':
            print("Exit demo, waiting for main process to terminate...")
            exit_demo = True
            sys.exit()
        else:
            print("Error. Please choose 1, 2 or 3.")
        time.sleep(1)


def main():
    global gw_addr
    global sock

    print('LoRa Application Server for demostrating Spectral Scan')
    localhost = get_own_ip()
    listen_address = (localhost, listen_port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #sock.settimeout(3)
    sock.bind(listen_address)
    print('listen on %s port %s' %listen_address)

    while True:
        if exit_demo == True:
            import requests
            requests.post('http://127.0.0.1:2222/kill')
            break
        data, address = sock.recvfrom(4096)
        if data:
            gw_addr = address
            #print('received %s bytes from %s' %(len(data), address))
            if len(data) == scan_result_len:
                process_scan_result(data)
            elif len(data) == get_freq_len:
                process_get_freq(data)
            else:
                pass  # ignore keep-alive packets


if __name__ == '__main__':
    thread_cmd = threading.Thread(target = obtain_command)
    thread_cmd.start()

    thread_webhook = threading.Thread(target = mywebhook.continue_recv)
    thread_webhook.start()

    main()
