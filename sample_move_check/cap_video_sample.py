import cv2
#import os
#import numpy as np

path1='./video/bird2/bird_c_9.mov'
path2='./video/bird2/bird_d_9.mov'

h=int(480.0)
w=int(640.0)
fps=float(30)

def params(cap):
    
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT,h)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,w)
    cap.set(cv2.CAP_PROP_FPS,fps)
    #自動補正off 露出補正・フォーカス・ホワイトバランス
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE,0)
    cap.set(cv2.CAP_PROP_AUTOFOCUS,0)
    #cap.set(cv2.CAP_PROP_AUTO_WB,0)
    
    #cap.set(cv2.CAP_PROP_BRIGHTNESS,50)
    #cap.set(cv2.CAP_PROP_CONTRAST,0)
    #cap.set(cv2.CAP_PROP_SATURATION,50)
    #cap.set(cv2.CAP_PROP_EXPOSURE,32)
    #cap.set(cv2.CAP_PROP_WB_TEMPERATURE,)
    
    #cap.set(cv2.CAP_PROP_SETTINGS, 1)
    

def main():
    
    cap1=cv2.VideoCapture(1,cv2.CAP_DSHOW)
    cap2=cv2.VideoCapture(2,cv2.CAP_DSHOW)
    
    #カメラ設定
    params(cap1)
    params(cap2)
    #動画保存
    fourcc1=cv2.VideoWriter_fourcc('m','p','4','v')   
    writer1=cv2.VideoWriter(path1,fourcc1,fps,(w,h))
    fourcc2=cv2.VideoWriter_fourcc('m','p','4','v')   
    writer2=cv2.VideoWriter(path2,fourcc2,fps,(w,h))
   
    
    while(True):
        
        # VideoCaptureから1フレーム読み込む
        '''
        ret=(True/False)
        frame=img
        '''
        ret1,frame1=cap1.read()
        ret2,frame2=cap2.read()
                
        if not ret1:
            print('no frame1')
            break
        if not ret2:
            print('no frame2')
            break
        
        #画像表示
        cv2.imshow('1',frame1)
        cv2.imshow('2',frame2)
        
        #動画保存
        writer1.write(frame1)
        writer2.write(frame2)

        #enterで終了
        key=cv2.waitKey(1)
        if key==13:
            break

    
    #動画解法
    writer1.release()
    #writer2.release()
    #カメラ解法
    cap1.release()
    cap2.release()

    cv2.destroyAllwindows()

if __name__=="__main__":
    main()