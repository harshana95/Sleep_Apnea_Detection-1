import numpy as np
import cv2
from scipy import signal
import numpy.linalg as LA
import scipy.ndimage.filters as filt
import datetime
from time import sleep
import codecs, json


def findPeaks(ar):
    peaks = np.zeros(ar.shape, dtype=np.int)
    for x in range(1, len(ar) - 1):
        if (ar[x - 1] < ar[x] and ar[x] >= ar[x + 1]):
            peaks[x] = 1
    return peaks


def findTime(peaks, fs):
    time = np.nonzero(peaks)[0]

    for x in range(len(time) - 1, 1, -1):
        time[x] = (time[x] - time[x - 1]) * fs
    time[0] = 0

    return time


def printToArduino(str):
    '''test = serial.Serial()
    test.baudrate = 115200
    test.timeout = 0
    test.port = "/dev/ttyUSB0"
    test.open()
    sleep(60)
    test.write(str)'''


def mouse(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        '''print(x, y)'''


# cv2.setMouseCallback('Edges', mouse)

def pca(data):
    mean = np.mean(data, 0)
    ddd = data - mean
    [e_val, e_vec] = LA.eig(np.dot(ddd.T, ddd))
    return e_val[1], e_vec[1, :]


def mainProg(videoFileName='3.mp4', jsonFileName='sendToServer.json', framesToProcess=1000, x_1=275, y_1=246, x_2=326,
             y_2=317, smootheningParam=150, isPC=True,isTesting=True):
    if isPC:
        import matplotlib.pyplot as plt
    else:
        import serial
    if videoFileName == '0':
        cap = cv2.VideoCapture(0)
    else:
        cap = cv2.VideoCapture(videoFileName)
    if isPC:
        cv2.namedWindow('Edges')
    arr_size = framesToProcess
    arr = np.zeros(arr_size)
    cog_x_arr = np.zeros(arr_size)
    cog_y_arr = np.zeros(arr_size)
    v_x_arr = np.zeros(arr_size)
    v_y_arr = np.zeros(arr_size)
    projected = np.zeros(arr_size)
    smoothened = np.zeros(arr_size)

    if isTesting:
        manualInput=np.zeros(arr_size)
        isExhale=True

    # plt.ion()

    count = 0

    # y, x = 457, 220
    # k = 5
    # x1, y1, x2, y2 = x - k, y - k, x + k, y + k
    '''Put points here'''
    y1, x1 = y_1, x_1
    y2, x2 = y_2, x_2


    while (1):
        ret, frame = cap.read()
        if ret == True:

            gray_vid = cv2.cvtColor(frame, cv2.IMREAD_GRAYSCALE)
            edged_frame = cv2.Canny(frame, 100, 200)
            if isPC:
                cv2.imshow('Original', frame)
                cv2.rectangle(edged_frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.imshow('Edges', edged_frame)

            win = edged_frame[x1:x2, y1:y2]
            h, w = win.shape

            cog_x = np.sum(win * np.arange(w)) / np.sum(win)
            cog_y = np.sum(win * np.arange(h).reshape(h, 1)) / np.sum(win)

            cog_x_arr[1:arr_size] = cog_x_arr[:arr_size - 1]
            cog_x_arr[0] = cog_x
            cog_y_arr[1:arr_size] = cog_y_arr[:arr_size - 1]
            cog_y_arr[0] = cog_y

            v_x_arr[1:arr_size] = v_x_arr[:arr_size - 1]
            v_x_arr[0] = cog_x_arr[1] - cog_x_arr[0]
            if (np.isnan(v_x_arr[0])):
                v_x_arr[0] = v_x_arr[1]

            v_y_arr[1:arr_size] = v_y_arr[:arr_size - 1]
            v_y_arr[0] = cog_y_arr[1] - cog_y_arr[0]
            if (np.isnan(v_y_arr[0])):
                v_y_arr[0] = v_y_arr[1]

            if (count == arr_size):

                v_arr = np.concatenate((v_x_arr, v_y_arr), axis=0).reshape((arr_size, 2))
                '''print("x", v_x_arr)
                print("y", v_y_arr)
                print("arr", v_arr)'''

                for x in range(10, 100):
                    pca_eig, pca_vec = pca(v_arr[:x, :])
                    projected[x] = pca_vec[0] * v_x_arr[x] + pca_vec[1] * v_y_arr[x]

                for x in range(100, arr_size):
                    pca_eig, pca_vec = pca(v_arr[x - 100:x, :])
                    projected[x] = pca_vec[0] * v_x_arr[x] + pca_vec[1] * v_y_arr[x]

                for x in range(1, arr_size):
                    projected[x] = projected[x - 1] * 0.8 + projected[x] * 0.2

                if smootheningParam > 0:
                    smoothened = filt.gaussian_filter1d(projected, smootheningParam * np.var(projected))
                else:
                    smoothened = projected

                peaks = findPeaks(smoothened)

                if isPC:
                    if not isTesting:
                        plt.subplot(4, 1, 1)
                    else:
                        plt.subplot(2,1,1)
                    plt.plot(projected)

                    
                    if not isTesting:
                        plt.subplot(4, 1, 2)
                    else:
                        plt.subplot(2,1,2)
                    
                    plt.plot(smoothened)
                    
                    for x in range(len(peaks)):
                        if (peaks[x] == 1):
                            plt.plot(x, smoothened[x], 'g.')

                    if isTesting:

                        for x in range(len(manualInput)):
                            if manualInput[x]==1:
                                plt.plot(x,smoothened[x],'k.')

                        isExhaling=True

                        for x in range(arr_size):
                            if peaks[x]==1:
                               if not isExhaling :
                                    plt.plot(x,smoothened[x],'r*')
                                    isExhaling=True

                            if manualInput[x]==1:
                                isExhaling = not isExhaling    








                now = datetime.datetime.now()

                dictJSON = {}

                smoothened = (smoothened - np.mean(smoothened)) / np.sqrt(np.var(smoothened))
                data = []
                for x in range(len(smoothened)):
                    data.append(smoothened[x])
                dictJSON['data'] = data
                dictJSON['TimeStamp'] = now.strftime("%Y-%m-%d %H:%M")
                #                dictJSON['FPS'] = '30'

                filePathJSON = jsonFileName
                json.dump(dictJSON, codecs.open(filePathJSON, 'w', encoding='utf-8'), separators=(',', ':'),
                          sort_keys=True, indent=4)
                jsonString=json.dumps(dictJSON, sort_keys=True,indent=4, separators=(',', ': '))
                if isPC and not isTesting:
                    plt.subplot(4, 1, 3)
                fs = 1.0/24.0
                f, pow_x = signal.welch(projected, fs, nperseg=1000)
                if isPC and not isTesting:
                    plt.plot(f[0:100], pow_x[0:100])

                reportName = now.strftime("./report/rep%Y-%m-%d %H:%M.pdf")
                if isPC and not isTesting:
                    plt.subplot(4, 1, 4)
                    plt.text(0, 0, ("REPORT : " + reportName + " \nTime for a breath: " + str(findTime(peaks, 30))))

                    plt.savefig(reportName)
                if isPC:
                    plt.show()
                    return jsonString
                else:
                    return jsonString

            if isTesting:
                if(isExhale):
                    charIn = input('Is exhale? (Press enter if yes, enter a char and press enter if no)\n')
                else:
                    charIn=input('Is inhale? (Press enter if yes, enter a char and press enter if no)\n')
                if len(charIn)>0:
                    manualInput[count]=1
                    isExhale = not isExhale
                else:
                    manualInput[count]=0
            if isPC:
                k = cv2.waitKey(30) & 0xff
                if k == 27:
                    break
            count += 1
            print('frame :' + str(count)+' of '+str(arr_size)+' = '+str(100*count/arr_size)+'% complete')

        else:
            break
    cap.release()
    # cv2.destroyAllWindows()


import sys

# mainProg('3.mp4','aa.json')
if (len(sys.argv) == 1):
    print(mainProg(framesToProcess=500))
else:
    print(mainProg(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]),
             int(sys.argv[7]), bool(sys.argv[8])),bool(sys.argv[9]))
