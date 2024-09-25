from qlib import qsv, quantum, measure

states = qsv(3, 0)
states.h()
x = states
num = measure(states)
print(num)
print(x)

