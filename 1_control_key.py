import ctypes
import time
import random
import cv2
import mss
import numpy as np
import win32api
import win32con
import win32gui
import math
import keyboard
import numpy as np
import win32gui
import win32ui,win32con
from time import time
import cv2 as cv
import os

from pynput.keyboard import Key, Controller
# ---------------- Detect Game Window ---------------- #
def get_window_rect(window_name):
    hwnd = win32gui.FindWindow(None, window_name)
    
    if hwnd == 0:
        raise Exception(f"Window '{window_name}' not found!")
    win32gui.SetForegroundWindow(hwnd)
    rect = win32gui.GetWindowRect(hwnd)
    return {'left': rect[0], 'top': rect[1], 'width': rect[2]-rect[0], 'height': rect[3]-rect[1]}
class WindowCapture:
    w=0
    h=0
    hwnd = None

    #constructor

    def __init__(self,window_name):
        self.hwnd=win32gui.FindWindow(None,window_name)
        print('FIND WINDOW:',win32gui.FindWindow(None,window_name))
        if not self.hwnd:
            raise Exception('Window not found: {}'.format(window_name))
        
        self.w = 1920
        self.h = 1080

    def get_screenshot(self):
        
        # hwnd=None
        wDC = win32gui.GetWindowDC(self.hwnd)
        dcObj=win32ui.CreateDCFromHandle(wDC)
        cDC=dcObj.CreateCompatibleDC()
        dataBitMap = win32ui.CreateBitmap()
        dataBitMap.CreateCompatibleBitmap(dcObj,self.w,self.h)
        cDC.SelectObject(dataBitMap)
        cDC.BitBlt((0,0),(self.w,self.h),dcObj,(0,0),win32con.SRCCOPY)

        #save the screeshot
        # dataBitMap.SaveBitmapFile(cDC,'debug.bmp')
        signedIntsArray= dataBitMap.GetBitmapBits(True)
        img = np.frombuffer(signedIntsArray,dtype='uint8')
        img.shape=(self.h,self.w,4)

        #Free Resources
        dcObj.DeleteDC()
        cDC.DeleteDC()
        win32gui.ReleaseDC(self.hwnd,wDC)
        win32gui.DeleteObject(dataBitMap.GetHandle())

        img = img[...,:3]
        img = np.ascontiguousarray(img)
        return img
    

    def list_window_names(self):
        def winEnumHandler(hwnd,ctx):
            if win32gui.IsWindowVisible(hwnd):
                print(hex(hwnd),win32gui.GetWindowText(hwnd))
        win32gui.EnumWindows(winEnumHandler,None)


        
os.chdir(os.path.dirname(os.path.abspath(__file__)))
keyboard_controller = Controller()
window_name = "LEGO® - Google Chrome"
wincap = WindowCapture(window_name)
wincap.list_window_names()

monitor = get_window_rect(window_name)
loop_time = time()
while(True):
    screenshot = wincap.get_screenshot()
    
    # screenshot = np.array(screenshot)
    # screenshot = cv.cvtColor(screenshot,cv.COLOR_RGB2BGR) 
    cv.imshow("computer Vision",screenshot)

    print("FPS {}".format(time()-loop_time))
    loop_time= time()
    if cv.waitKey(1)==ord('q'):
        cv.destroyAllWindows()
        break



print('Done.')

keyboard_controller.press(Key.f2)