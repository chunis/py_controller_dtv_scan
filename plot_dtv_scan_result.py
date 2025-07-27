#!/usr/bin/python

# Chunis Deng (chunchengfh@gmail.com)

import matplotlib.pyplot as plt


step = 0.2  # MHz
rssi_step = -4
head = 3
unit = 3  # a group contains 3 values (max, most, average)

def plot_dtv_scan(res):
    x = []
    y1 = []
    y2 = []

    start = head + res[1] * unit
    end = head + (res[1]+res[2]) * unit

    freq_base = 863.1
    if res[0] == 2:  # CN470
        freq_base = 470.1

    freq_start = freq_base + res[1] * step
    freq_end = freq_base + (res[1]+res[2]) * step
    #print('start = %s' %start)
    #print('end = %s' %end)
    print('freq_start = %s' %round(freq_start, 1))
    print('freq_end = %s' %round(freq_end, 1))

    f = freq_start
    while f < freq_end:
        x.append(round(f, 1))
        f += step

    offset = res[1] * unit + head
    for i in range(res[2]):
        y1.append(res[i * unit + offset] * rssi_step)
        y2.append(res[i * unit + offset + 1] * rssi_step)
    print('max: ', y1)
    print('most:', y2)

    fig = plt.figure()
    plt.plot(x, y1, marker='D', markersize=5)
    plt.plot(x, y2, marker='D', markersize=5)

    plt.xlabel("Freq [MHz]")
    plt.ylabel("Signal Strength [dBm]")
    plt.title("DTV Scan Result")
    plt.legend(["max", "most"])
    plt.grid(True)  # plt.grid(axis='y')
    plt.show()


if __name__ == '__main__':
    res = [1, 20, 16]
    res += [0, 0, 0] * 20
    res += [23, 23, 0, 23, 23, 0, 22, 23, 0, 23, 23, 0, 22, 23, 0, 22, 23, 0, 22, 23, 0, 22, 23, 0, 22, 23, 0, 23, 23, 0, 22, 23, 0, 22, 23, 0, 22, 23, 0, 17, 20, 0, 17, 18, 0, 17, 18, 0]
    res += [0, 0, 0] * 44
    plot_dtv_scan(res)
