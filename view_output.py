import numpy as np
from game_data import GameData

if __name__ == "__main__":
    weights = np.load("output/coef.npy").ravel().tolist()
    weights.append(0)  # false "result"
    weights.append(0)  # false "gameloop"
    print(GameData.state_to_string(weights))
