import os
import numpy as np
from sklearn.linear_model import SGDClassifier
from game_data import GameData

def get_data_file_names():
    data_files = []
    for dirpath, dirs, files in os.walk(os.path.join(os.path.curdir, "data")):
        for file in files:
            data_files.append(os.path.join(dirpath, file))
    return data_files


def train_on_file(sgd_classifier, filename):
    data = np.load(filename)
    if data.shape[1] != GameData.n_state_indices:
        raise ValueError("Data does not have the right shape.")

    x = data[:, 0:GameData.n_unit_indices]
    y = data[:, GameData.result_index]
    sgd_classifier.partial_fit(X=x, y=y, classes=[-1, 1])


if __name__ == '__main__':
    epochs = 10
    trainer = SGDClassifier(loss='log', fit_intercept=False)

    data_files = get_data_file_names()
    for i in range(epochs):
        for file_name in data_files:

            print("Training on file {0}".format(file_name))
            train_on_file(trainer, file_name)

    if not os.path.exists("output"):
        os.makedirs("output")
    np.save(file="output/coef", arr=trainer.coef_)

