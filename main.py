import cv2
import kivy
import time
import functools
import jnius
#import pytesseract
from plyer import tts
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from kivy.lang import builder


def acquire_permissions(permissions, timeout=30):
    """
    blocking function for acquiring storage permission

    :param permissions: list of permission strings , e.g. ["android.permission.READ_EXTERNAL_STORAGE",]
    :param timeout: timeout in seconds
    :return: True if all permissions are granted
    """

    PythonActivity = jnius.autoclass('org.kivy.android.PythonActivity')
    Compat = jnius.autoclass('android.support.v4.content.ContextCompat')
    currentActivity = jnius.cast('android.app.Activity', PythonActivity.mActivity)

    checkperm = functools.partial(Compat.checkSelfPermission, currentActivity)

    def allgranted(permissions):
        """
        helper function checks permissions
        :param permissions: list of permission strings
        :return: True if all permissions are granted otherwise False
        """
        return reduce(lambda a, b: a and b,
                    [True if p == 0 else False for p in map(checkperm, permissions)]
                    )

    haveperms = allgranted(permissions)
    if haveperms:
        # we have the permission and are ready
        return True

    # invoke the permissions dialog
    currentActivity.requestPermissions(permissions, 0)

    # now poll for the permission (UGLY but we cant use android Activity's onRequestPermissionsResult)
    t0 = time.time()
    while time.time() - t0 < timeout and not haveperms:
        # in the poll loop we could add a short sleep for performance issues?
        haveperms = allgranted(permissions)

    return haveperms


class KivyCamera(Image):
    def __init__(self, capture, fps, **kwargs):
        super(KivyCamera, self).__init__(**kwargs)
        self.capture = capture
        Clock.schedule_interval(self.update, 1.0 / fps)

    def update(self, dt):
        ret, frame = self.capture.read()
        if ret:
            # convert it to texture
            buf1 = cv2.flip(frame, 0)
            buf = buf1.tostring()
            image_texture = Texture.create(
                size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            image_texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            # display image from the texture
            self.texture = image_texture
    
    def on_touch_down(self, touch):
        ret, img = self.capture.read()
        self.capture.release()
        tts.speak(message="El pastel es una mentira. The cake is a lie")


    def on_touch_up(self, touch):
        self.capture = cv2.VideoCapture(0)


class CamApp(App):
    def build(self):
        perms = ["android.permission.CAMERA"]
        haveperms = acquire_permissions(perms)
        if(check_permission(perms)):
            self.capture = cv2.VideoCapture(0)
            self.my_camera = KivyCamera(capture=self.capture, fps=30)
        
        return self.my_camera

    def on_stop(self):
        # without this, app will not exit even if the window is closed
        self.capture.release()


if __name__ == '__main__':
    CamApp().run()
    cv2.destroyAllWindows()
