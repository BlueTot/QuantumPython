from qython import qsv, qconst, quantum, measure, parallelize, auto_execute

x = qsv(3, 0)
x.h()

y = qsv(3, 0)
z = qconst(3, 7)

@auto_execute
@parallelize(x.states)
def process_item(state):
    y.store(state & z)
    return

n = measure(y)
print(n)
