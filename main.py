import automateTraining as Automate


if __name__ == "__main__":
    print("please enter the number of skills you wish to train")
    num = input()

    with open('model\\keypoint_classifier\\keypoint_classifier_label.csv', 'w', encoding='utf-8') as f:
        f.seek(0)      # Move to the start of the file
        f.truncate(0)  # Erase everything from the start
        for i in range(int(num)):
            print("please enter the name of the skill you wish to train")
            name = input()
            f.write(name + '\n')
        f.close()
        Automate.main()
