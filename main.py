from operator import ge

import getData as GetData
import kc as Train
import runTrained as Run
import remote.gestureMap as GM

actions = ["good", "spin", "sit"]

if __name__ == "__main__":
    print("click any key once client is connected")
    input()

    GetData.main(actions)
    print("data collection complete, moving on to model training")
    Train.main(len(actions))
    print("training done!")
    Run.main(actions)


