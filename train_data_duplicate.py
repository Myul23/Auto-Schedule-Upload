from os import remove
from os.path import exists
from pandas import read_csv

address = "better recognition/better_recognition.csv"
data = read_csv(address, sep="\t")
for index, flag in enumerate(data.before.duplicated(keep="last")):
    if not flag:
        continue

    target = data.loc[index, "image_path"]
    if exists(target):
        remove(target)
    else:
        print("Already didn't exist")
data.drop_duplicates(subset=["before"], inplace=True)

for path in data.image_path:
    if not exists(path):
        print("Doesn't exist", path)

data.to_csv(address, sep="\t", index=False)
