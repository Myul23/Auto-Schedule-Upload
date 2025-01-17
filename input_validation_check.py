from os.path import exists
from glob import glob
import cv2


def check_image_with_track(image_pathes: list, preprocess_flag: bool, process_flag: int, postprocess_flag: bool) -> None:
    for image_path in image_pathes:
        if not exists(image_path):
            print(image_path, "doesn't exist")
            continue

        image = cv2.imread(image_path)
        if image is None:
            print(image_path, "read fail")
            continue
        binary = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        cv2.namedWindow("Trackbar Windows")

        if not preprocess_flag:
            cv2.createTrackbar("alpha", "Trackbar Windows", 0, 255, lambda x: x)
            cv2.setTrackbarPos("alpha", "Trackbar Windows", 0)
            cv2.createTrackbar("beta", "Trackbar Windows", 0, 255, lambda x: x)
            cv2.setTrackbarPos("beta", "Trackbar Windows", 127)

        if process_flag < 1:
            cv2.createTrackbar("thresh", "Trackbar Windows", 0, 255, lambda x: x)
            cv2.setTrackbarPos("thresh", "Trackbar Windows", 50)
            cv2.createTrackbar("maxvalue", "Trackbar Windows", 127, 255, lambda x: x)
            cv2.setTrackbarPos("maxvalue", "Trackbar Windows", 255)
            cv2.createTrackbar("thresh_type", "Trackbar Windows", 0, 10, lambda x: x)
            cv2.setTrackbarPos("thresh_type", "Trackbar Windows", 0)
        elif process_flag < 2:
            cv2.createTrackbar("C", "Trackbar Windows", -15, 15, lambda x: x)
            cv2.setTrackbarPos("C", "Trackbar Windows", 4)
        else:
            cv2.createTrackbar("thresh_min", "Trackbar Windows", 0, 255, lambda x: x)
            cv2.setTrackbarPos("thresh_min", "Trackbar Windows", 100)
            cv2.createTrackbar("thresh_max", "Trackbar Windows", 0, 255, lambda x: x)
            cv2.setTrackbarPos("thresh_max", "Trackbar Windows", 200)

        if postprocess_flag:
            cv2.createTrackbar("kernel_size", "Trackbar Windows", 1, 7, lambda x: x)
            cv2.setTrackbarPos("kernel_size", "Trackbar Windows", 3)

        while True:
            if not preprocess_flag:
                alpha = cv2.getTrackbarPos("alpha", "Trackbar Windows")
                beta = cv2.getTrackbarPos("beta", "Trackbar Windows")

            if process_flag < 1:
                thresh = cv2.getTrackbarPos("thresh", "Trackbar Windows")
                maxvalue = cv2.getTrackbarPos("maxvalue", "Trackbar Windows")
                thresh_type = cv2.getTrackbarPos("thresh_type", "Trackbar Windows")
            elif process_flag < 2:
                C = cv2.getTrackbarPos("C", "Trackbar Windows")
            else:
                thresh_min = cv2.getTrackbarPos("thresh_min", "Trackbar Windows")
                thresh_max = cv2.getTrackbarPos("thresh_max", "Trackbar Windows")

            if postprocess_flag:
                kernel_size = cv2.getTrackbarPos("kernel_size", "Trackbar Windows")

            if cv2.waitKey(1) == ord("q"):
                if not preprocess_flag:
                    print(f"alpha: {alpha}")
                    print(f"beta: {beta}")

                if process_flag < 1:
                    print(f"thresh: {thresh}")
                    print(f"maxvalue: {maxvalue}")
                    print(f"thresh_type: {thresh_type}")
                elif process_flag < 2:
                    print(f"C: {C}")
                else:
                    print(f"thresh_min: {thresh_min}")
                    print(f"thresh_max: {thresh_max}")

                if postprocess_flag:
                    print(f"kernel_size: {kernel_size}")
                break

            try:
                if preprocess_flag:
                    skeleton = cv2.GaussianBlur(binary, (5, 5), 0)
                else:
                    skeleton = cv2.normalize(binary, None, alpha=alpha, beta=beta, norm_type=cv2.NORM_MINMAX)

                if process_flag < 1:
                    _, skeleton = cv2.threshold(skeleton, thresh, maxvalue, thresh_type)
                elif process_flag < 2:
                    skeleton = cv2.adaptiveThreshold(skeleton, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 7, C)
                else:
                    skeleton = cv2.Canny(skeleton, thresh_min, thresh_max)

                if postprocess_flag and kernel_size > 0:
                    k = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
                    skeleton = cv2.morphologyEx(skeleton, cv2.MORPH_CLOSE, k)

                contours, hierarachies = cv2.findContours(skeleton, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
                output = cv2.cvtColor(skeleton, cv2.COLOR_GRAY2BGR)
                for contour, hierarchy in zip(contours, hierarachies[0]):
                    if sum([h == -1 for h in hierarchy]) > 2:
                        continue

                    epsilon = 0.007 * cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, epsilon, True)

                    x, y, w, h = cv2.boundingRect(contour)
                    area = [w * h, binary.shape[0] * binary.shape[1]]
                    if len(approx) != 4 or area[0] < area[1] / 200 or area[0] > area[1] / 5:
                        continue

                    vertex = [[], []]
                    for y, x in approx.reshape(len(approx), -1):
                        vertex[0].append(x)
                        vertex[1].append(y)

                    vertex = [[min(vertex[0]), max(vertex[0])], [min(vertex[1]), max(vertex[1])]]
                    output = cv2.rectangle(output, (vertex[1][0], vertex[0][0]), (vertex[1][1], vertex[0][1]), (255, 100, 100), 5, 1)
            except:
                pass

            times = 1080 / image.shape[1]
            output = cv2.resize(output, dsize=None, fx=times, fy=times)
            cv2.imshow("Trackbar Windows", output)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    image_pathes = glob("test/sample/*")  # ["2022.09.21.jpeg"]
    check_image_with_track(image_pathes=image_pathes, preprocess_flag=False, process_flag=2, postprocess_flag=True)
