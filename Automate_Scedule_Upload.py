from os import remove
from os.path import exists, basename, splitext
from datetime import datetime, timedelta
from warnings import filterwarnings

from google_authorization import GoogleAuth

# image processing
from cv2 import COLOR_BGR2GRAY, ADAPTIVE_THRESH_GAUSSIAN_C, THRESH_BINARY, RETR_EXTERNAL, CHAIN_APPROX_SIMPLE
from cv2 import imread, cvtColor, adaptiveThreshold, arcLength, approxPolyDP, boundingRect, findContours, imwrite
from paddleocr import PaddleOCR

filterwarnings(action="ignore")


class Schedule_Upload(GoogleAuth):
    def __init__(self, test_flag: bool = False):
        self.test_flag = test_flag

        super().__init__(self.test_flag)
        self.__ocr = PaddleOCR(lang="korean")
        self.__datetime_number = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6, "AM": 0, "PM": 12}
        self.__dump_file_name = "test.jpg"

    def __days_boxing(self, contour) -> bool:
        try:
            epsilon = 0.007 * arcLength(contour, True)
            approx = approxPolyDP(contour, epsilon, True)

            x, y, w, h = boundingRect(contour)
            area = [w * h, self.__binary.shape[0] * self.__binary.shape[1]]
            if len(approx) != 4 or area[0] < area[1] / 100 or area[0] > area[1] / 5:
                return False

            vertex = [[], []]
            for y, x in approx.reshape(len(approx), -1):
                vertex[0].append(x)
                vertex[1].append(y)

            vertex = [[min(vertex[0]), max(vertex[0])], [min(vertex[1]), max(vertex[1])]]
            crop = self.__image[vertex[0][0] : vertex[0][1], vertex[1][0] : vertex[1][1]]
            imwrite(self.__dump_file_name, crop)
            return True
        except:
            print("Days Box Checking Fail")
            return False

    def construct_sentences(self, texts: list, link_flag: bool = False) -> str:
        sentence = " ".join(texts)
        if sentence == "CGRN LIVE":
            sentence += " 🎖"
        if link_flag:
            sentence = "\n".join(
                [
                    sentence,
                    "CHZZK: https://chzzk.naver.com/5db77759d5afd68debca65a7c47f7ab5",
                    "YouTube: https://www.youtube.com/@Cheong_Run",
                    "TwitCasting: https://twitcasting.tv/cheong_run",
                ]
            )
        return sentence

    def __schedule_upload(self, image_path: str, contour) -> None:
        if not self.__days_boxing(contour):
            return

        try:
            # ? recognition
            result = self.__ocr.ocr(self.__dump_file_name, cls=False)
            if len(result[0]) < 3:
                return

            # * date
            texts = [text for _, (text, _) in result[0]]
            file_name, _ = splitext(basename(image_path))
            date = datetime.strptime(file_name, "%Y.%m.%d") + timedelta(days=self.__datetime_number[texts.pop(0)])
            assert date == datetime.strptime(file_name.split(".", 1)[0] + "/" + texts.pop(0), "%Y/%m/%d")

            # * time
            date = date + timedelta(hours=int(texts.pop().split(":", 1)[0]) + self.__datetime_number[texts.pop()])
            sentence = self.construct_sentences(texts)

            # ? upload
            self._event["description"] = sentence
            self._event["start"] = {"dateTime": date.isoformat(), "timeZone": "Asia/Seoul"}
            self._event["end"] = {"dateTime": (date + timedelta(hours=3)).isoformat(), "timeZone": "Asia/Seoul"}
            if not self.test_flag:
                event = self._service.events().insert(calendarId=self._calendarId, body=self._event).execute()
            else:
                print(f'{self._event["start"]}:\t{self._event["description"]}')
        except Exception as e:
            print("Recognition and Upload Part Fail")
            print(e)

    def scheduling(self, image_pathes: list) -> None:
        for image_path in image_pathes:
            if not exists(image_path):
                print(image_path, "doesn't exist")
                continue

            self.__image = imread(image_path)
            if self.__image is None:
                print(image_path, "read fail")
                continue

            self.__binary = cvtColor(self.__image, COLOR_BGR2GRAY)
            skeleton = adaptiveThreshold(self.__binary, 255, ADAPTIVE_THRESH_GAUSSIAN_C, THRESH_BINARY, 7, -3)
            contours, _ = findContours(skeleton, RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)

            for contour in contours:
                self.__schedule_upload(image_path, contour)

            if exists(self.__dump_file_name):
                remove(self.__dump_file_name)
            print(image_path, "is FINISHED!!")


if __name__ == "__main__":
    image_pathes = ["test/2022.09.21.jpeg"]
    Schedule_Upload().scheduling(image_pathes=image_pathes)
