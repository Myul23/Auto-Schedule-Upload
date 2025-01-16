from os import mkdir, remove
from os.path import exists, basename, splitext
from glob import glob
from datetime import datetime, timedelta
from warnings import filterwarnings

from google_authorization import GoogleAuth

# image processing
from cv2 import (
    COLOR_BGR2GRAY,
    COLOR_BGR2RGB,
    MORPH_RECT,
    ADAPTIVE_THRESH_GAUSSIAN_C,
    THRESH_BINARY,
    MORPH_CLOSE,
    RETR_CCOMP,
    CHAIN_APPROX_SIMPLE,
)
from cv2 import (
    imread,
    cvtColor,
    getStructuringElement,
    adaptiveThreshold,
    arcLength,
    morphologyEx,
    approxPolyDP,
    boundingRect,
    findContours,
    imwrite,
)
from paddleocr import PaddleOCR


from gradio import Blocks, Row, Column, Markdown, Image, Text, Checkbox, Button, close_all

filterwarnings(action="ignore")


class Schedule_Upload(GoogleAuth):
    def __init__(self, upload_flag: bool = True):
        self.upload_flag = upload_flag

        super().__init__(self.upload_flag)
        self.__ocr = PaddleOCR(lang="korean", show_log=False)
        self.__datetime_number = {
            "MON": 0,
            "TUE": 1,
            "WED": 2,
            "THU": 3,
            "FRI": 4,
            "SAT": 5,
            "SUN": 6,
            "월": 0,
            "화": 1,
            "수": 2,
            "목": 3,
            "금": 4,
            "토": 5,
            "일": 6,
            "AM": 0,
            "PM": 12,
            # lambda x: (ord(x[0]) - 97) // 12 * 12) 1, 16
        }
        self.__datetime_number_list = list(self.__datetime_number.keys())
        self.__dump_file_name = "test.jpg"

        # * save recognition data
        self.save_folder = "better recognition"
        for folder in [self.save_folder, self.save_folder + "/images"]:
            if not exists(folder):
                mkdir(folder)
        self.save_file = self.save_folder + "/better_recognition.csv"
        self.save_folder = self.save_folder + "/images"

    def __days_boxing(self, contour) -> bool:
        try:
            epsilon = 0.007 * arcLength(contour, True)
            approx = approxPolyDP(contour, epsilon, True)

            x, y, w, h = boundingRect(contour)
            area = [w * h, self.__binary.shape[0] * self.__binary.shape[1]]
            if len(approx) != 4 or area[0] < area[1] / 200 or area[0] > area[1] / 5:
                return False

            vertex = [[], []]
            for y, x in approx.reshape(len(approx), -1):
                vertex[0].append(x)
                vertex[1].append(y)

            vertex = [[min(vertex[0]), max(vertex[0])], [min(vertex[1]), max(vertex[1])]]
            self.__crop = self.__image[vertex[0][0] : vertex[0][1], vertex[1][0] : vertex[1][1]]
            imwrite(self.__dump_file_name, self.__crop)
            return True
        except:
            print("Days Box Checking Fail")
            return False

    def construct_sentences(self, texts: list, link_flag: bool = False) -> str:
        sentence = " ".join(texts)
        # if sentence == "CGRN LIVE":
        #     sentence += " 🎖"
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

    def sorting(self, file_date: datetime, texts: list) -> list:
        # * days of week
        days = "MON"
        for idx in range(len(texts)):
            if texts[idx] in self.__datetime_number_list[:-2]:
                days = texts.pop(idx)
                break
        texts.insert(0, days)

        # * date
        date = "07/31"
        for idx in range(1, len(texts)):
            if "/" in texts[idx]:
                date = texts.pop(idx)
                break
        else:
            date = datetime.strftime(file_date + timedelta(days=self.__datetime_number[days]), "%m/%d")
        texts.insert(1, date)

        # * meridiem
        meridiem = "PM"
        for idx in range(2, len(texts)):
            if texts[idx] in ["AM", "PM"]:
                meridiem = texts.pop(idx)
                break
        texts.insert(-1, meridiem)

        # * time
        time = "9:00"
        for idx in range(2, len(texts)):
            if ":" in texts[idx]:
                time = texts.pop(idx)
                break
        else:
            self.upload_flag = False
        texts.append(time)

        return texts

    def validate_recognition(self, file_name: str, texts: list, original_image_flag: bool = False, self_close_flag: bool = False) -> list:
        self.__temp = texts
        try:
            with Blocks(analytics_enabled=False) as show:

                def save_data(texts, date, time, description, flag) -> None:
                    # * image
                    new_path = f'{self.save_folder}/{datetime.strftime(datetime.now(), "%Y.%m.%d_%H.%M.%S")}.jpg'
                    imwrite(new_path, self.__crop)

                    after = " ".join([date, description, time])
                    texts = "\t".join([new_path, texts, after, str(flag)]) + "\n"
                    if not exists(self.save_file):
                        texts = "\n".join(["\t".join(["image_path", "before", "after", "upload_flag"]), texts])
                    with open(self.save_file, "a", encoding="UTF-8") as tf:
                        tf.write(texts)
                    self.__temp = after.split()
                    self.upload_flag = flag

                    if self_close_flag:
                        show.close()
                        close_all()

                # * construct
                with Row():
                    Image(cvtColor(self.__image, COLOR_BGR2RGB), visible=original_image_flag)
                    Markdown(f"Schedule for {file_name}")
                with Row():
                    with Column():
                        Image(cvtColor(self.__crop, COLOR_BGR2RGB))
                    with Column():
                        date = Text(label="date", value=texts[0] + " " + texts[1])
                        time = Text(label="time", value=texts[-2] + " " + texts[-1])
                        description = Text(label="description", value=" ".join(texts[2:-2]))
                        flag = Checkbox(label="upload flag", value=self.upload_flag)
                with Row():
                    btn = Button("Save")

                btn.click(save_data, [Text(value=" ".join(texts), visible=False), date, time, description, flag], None, preprocess=False)
            show.launch()
        except Exception as e:
            print("Recognition Validation Fail")
            print(e)
        return self.__temp

    def __schedule_upload(self, image_path: str, contour) -> None:
        if not self.__days_boxing(contour):
            return

        try:
            # ? recognition
            result = self.__ocr.ocr(self.__dump_file_name, cls=False)
            if len(result[0]) < 3:
                return

            texts = [text for _, (text, _) in result[0]]

            file_name, _ = splitext(basename(image_path))
            date = datetime.strptime(file_name, "%Y.%m.%d")

            texts = self.sorting(date, texts)
            texts = self.validate_recognition(file_name, texts)

            # * date
            date += timedelta(days=self.__datetime_number[texts.pop(0)])

            # * time
            hour_minute = texts.pop().split(":", 1)
            date = date + timedelta(hours=int(hour_minute[0]) + self.__datetime_number[texts.pop()], minutes=int(hour_minute[1]))
            finish_date = date + timedelta(hours=3)

            sentence = self.construct_sentences(texts)

            # * construct event
            self._event["description"] = sentence
            self._event["start"] = {"dateTime": date.isoformat(), "timeZone": "Asia/Seoul"}
            self._event["end"] = {"dateTime": finish_date.isoformat(), "timeZone": "Asia/Seoul"}

            # ? upload
            if self.upload_flag:
                _ = self._service.events().insert(calendarId=self._calendarId, body=self._event).execute()
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

            k = getStructuringElement(MORPH_RECT, (7, 7))
            skeleton = morphologyEx(skeleton, MORPH_CLOSE, k)

            contours, hierarachies = findContours(skeleton, RETR_CCOMP, CHAIN_APPROX_SIMPLE)
            for contour, hierarchy in zip(contours, hierarachies[0]):
                if sum([h == -1 for h in hierarchy]) < 2:
                    self.__schedule_upload(image_path, contour)

            if exists(self.__dump_file_name):
                remove(self.__dump_file_name)
            print(image_path, "is FINISHED!!")


if __name__ == "__main__":
    image_pathes = glob("Schedules/*")  # ["2022.09.21.jpeg"]
    Schedule_Upload().scheduling(image_pathes=image_pathes)
