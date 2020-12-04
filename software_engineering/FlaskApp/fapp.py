from flask import *
from flask_sqlalchemy import SQLAlchemy
import cv2
import pyzbar.pyzbar as pyzbar
import threading

# set FLASK_APP=fapp (terminal command)
app = Flask(__name__)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fdatabase.sqlite3'

fdatabase = SQLAlchemy(app)
from repository import repository


@app.route('/main')
def main():
    return render_template('main.html')

@app.route('/')
def hello_world():
    # return '<h1>Welcome QR-Reader Page1</h1>'
    return render_template('index.html')

class Variable(object):
    def __init__(self):
        self.prev_data = None
        self.barcode_data = None

    def setPrev(self, prev):
        self.prev_data = prev

    def setBarcode(self, barc):
        self.barcode_data = barc

    def getPrev(self, **kwargs):
        return self.prev_data

    def getBarcode(self, **kwargs):
        return self.barcode_data


@app.route('/video')
@app.route('/video/<storename>')
def index(storename=None):
    return render_template('video.html', storename=storename)


@app.route('/camera')
def cam():
    return Response(read_cam(), mimetype='multipart/x-mixed-replace; boundary=mycam')


### CAMERA ###
camera = cv2.VideoCapture(0)  # video device number (/dev/videoX)
if not camera.isOpened():
    raise RuntimeError('Please Check device\'s Camera.')


def read_cam():
    variable = Variable()
    while True:
        ret, img = camera.read()
        ##############################
        if not ret:
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        decoded = pyzbar.decode(gray)

        for d in decoded:
            x, y, w, h = d.rect
            variable.setBarcode(d.data.decode("utf-8"))
            barcode_type = d.type
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)

            qrTemp = variable.getBarcode().split("|")
            # if(len(qrTemp) == 4):
            #     print("Fromat of Qrcode is wrong!")
            #     break
            text = '%s (%s)' % (qrTemp[0], barcode_type)
            cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_AA)

        if (variable.getBarcode() != variable.getPrev()):
            print(variable.getBarcode())
            qrData = variable.getBarcode().split("|")
            print(qrData)
            variable.setPrev(variable.getBarcode())

            dbThread = threading.Thread(target=repository.insertUserData(storename="default",
                                                                         phoneNum=qrData[0],
                                                                         mailAddress=qrData[2],
                                                                         daydate=qrData[3]))
            try:
                dbThread.start()
            except Exception as e:
                print(e)
        # yield Data
        yield (b'--mycam\r\n'
               b'Content-Type: image/jpeg\r\n\r\n'
               + cv2.imencode('.jpg', cv2.cvtColor(img, cv2.IMREAD_COLOR))[1].tobytes()
               + b'\r\n')


def main():
    app.debug = True
    app.run()
    # app.run(host='127.0.0.1', port=5000)


if __name__ == '__main__':
    main()
