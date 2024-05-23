import pickle
import os
import csv

if os.path.isfile('dict_Q'):
    Q = pickle.load(open('dict_Q'))
    with open("test.csv", "w") as csvfile:
        writer = csv.writer(csvfile)

        for state in Q.keys():
            writer.writerow([state[0], state[1], state[2], Q[state]['tap'], Q[state]['do_nothing']])


