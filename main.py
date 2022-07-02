import cv2
from scipy.spatial import distance
import dlib
import imutils
from imutils import face_utils
from converter import MorseToText
from collections import deque
from morselcd import lcd
import requests
final_string = ""
      



class decipher():

    def __init__(self):
        self.flag = 0
        self.openEye = 0
        self.str = ''
        self.finalString = []
        global L
        self.L = []
        self.closed = False
        self.timer = 0
       
        self.final = ''
        self.pts = deque(maxlen=512)
        self.thresh = 0.25
        self.dot = 10
        self.dash = 40
        self.detect = dlib.get_frontal_face_detector()
        self.predict = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

        (self.lStart, self.lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
        (self.rStart, self.rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
        
        
    
    def eye_aspect_ratio(self,eye):
        A = distance.euclidean(eye[1], eye[5])
        B = distance.euclidean(eye[2], eye[4])
        C = distance.euclidean(eye[0], eye[3])
        self.ear = (A + B) / (2.0 * C)
        #print(self.ear)
        return self.ear


    def calculate(self,frame):
        frame = imutils.resize(frame, width=480)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        subjects = self.detect(gray, 0)
        for subject in subjects:
            shape = self.predict(gray, subject)
            shape = face_utils.shape_to_np(shape)  # converting to NumPy Array
            leftEye = shape[self.lStart:self.lEnd]
            rightEye = shape[self.rStart:self.rEnd]
            leftEAR = self.eye_aspect_ratio(leftEye)
            rightEAR = self.eye_aspect_ratio(rightEye)
            ear = (leftEAR + rightEAR) / 2.0
            leftEyeHull = cv2.convexHull(leftEye)
            rightEyeHull = cv2.convexHull(rightEye)
            cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
            cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)

            if ear < self.thresh:  # closed eyes
                self.flag += 1
                self.pts.appendleft(self.flag)
                self.openEye = 0
            else:
                self.openEye += 1
                self.flag = 0
                self.pts.appendleft(self.flag)
            for i in range(1, len(self.pts)):
                if self.pts[i] > self.pts[i - 1]:
                    if self.pts[i] > 2 and self.pts[i] < 7:
                        print("Eyes have been closed for 15 frames!")

                        self.L.append(".")
                        lcd.morsetolcd(self.L)
                        self.pts = deque(maxlen=512)
                        break

                    elif self.pts[i] > 8 and self.pts[i] < 12:
                        print("Eyes have been closed for 40 frames!")

                        self.L.append("-")
                        lcd.morsetolcd(self.L)
                        self.pts = deque(maxlen=512)
                        break

                    elif self.pts[i] > 20:
                        print("Eyes have been closed for 45 frames!")

                        if len(self.L)>0:
                            self.L.pop()
                        else:
                            print("Nothing to remove")

                        self.pts = deque(maxlen=512)
                        break


        if (self.L != []):
            
            print(self.L)
        if self.openEye > 30:
            if (self.L != []):
                
                print(self.L)
            self.str = MorseToText(''.join(self.L))
            
            

            if self.str != None:
                print(self.str)
                self.finalString.append(self.str)
                self.final = ''.join(self.finalString)
                lcd.clear()
                lcd.morsetolcd(self.final)
                #sleep(5)
                #self.lcd.clear()
            if self.str == None:
                self.L = []
            self.L = []
            
        cv2.putText(frame, "Predicted :  " + self.final, (10, 350),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 219), 2)
        
        global final_string
        final_string= self.final
        return frame


def main():
    
    cap = cv2.VideoCapture(0)
    camera = decipher()
    
    while True:
        ret, frame = cap.read()
        frame= camera.calculate(frame)
        
        cv2.imshow("Morse_Decipher", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == (9):
            print(final_string)
            url = 'https://maker.ifttt.com/trigger/SMS_from_morsecode/with/key/csIdOV6q2qG81d07AyIVzm'
            payload = {"value1": final_string}
            headers = {}
            res = requests.post(url, data=payload, headers=headers)
        if key == (27):
            break
    lcd.clear()
    cv2.destroyAllWindows()
    cap.stop()
    

    


if __name__ == '__main__':
    main()