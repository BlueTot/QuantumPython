from qython import qsv, qconst, quantum, measure, parallelize, auto_execute, qif, qmemcount, printqc

x = qsv(3, 0)
x.h()

y = qsv(3, 0)
z = qconst(3, 6)

@auto_execute
@parallelize(x.states)
def process_item(state):
    with qif(state == z):
        y.store(state)
    return

n = measure(y)
print(n)
printqc()
print(qmemcount())
