# Documentation

## Data 
In classical computing, the fundamental data type is the binary integer, which is an array of bits. Likewise, in quantum computing, the fundamental data type is the quantum register, which is an array of qubits. In QuantumPython, there are two supported types of quantum registers:

  `qsv` : A modifiable quantum register <br/>
  `qconst` : A quantum constant

Operations that are normally available on a `qsv` like `.h()`, `.store()`, `measure()` are not possible with a `qconst`. The sole purpose of a `qconst` is to be used with `qsv`'s in arithmetic / logical operations.

`qsv`'s can be declared as follows: 
```python
<var> = qsv(<num_bits>, <initial_classical_value>)
```
`qconst`'s can be also declared in a similar fashion, with the same arguments.

## Superposition & Parallel Processing

One of the fundamental properties of `qsv`'s is that they can be in superposition, i.e. they can represent multiple states at once. As a result, `qsv`'s cannot be compared to integers in a classical sense, as one is a _collection_ of objects whilst the other is just an object. Hence, in QuantumPython, `qsv`'s are thought of as sets of quantum states, which each quantum state has a value and a probability amplitude.

Operations can be applied to `qsv`'s as well like normal integers (e.g. adding 1). When `qsv`'s are in superposition, due to the principle of linearity, the operation is applied to each state in the `qsv` all at the same time (i.e. parallel processing in a classical sense) Hence, in QuantumPython, whenever you apply any operation on a `qsv`, the `parallelize` decorator must be applied so that parallel processing is invoked.

Parallel processing in QuantumPython can be defined as so:
```python
@auto_execute
@parallelize(<set of states to process>)
def <function_name> (state):
  ...
  ...
  return
```
where the `auto_execute` decorator runs the function as soon as it is defined, and the input to the "for loop" is contained in the `parallelize` decorator.

## Hadamard Transform & Measurement

One way to put a `qsv` into superposition is through the hadamard transform operation. The syntax for this operation is as follows: `qsv.h()`

After all operations have been performed on a `qsv`, you must convert the `qsv` back into a classical integer so it can be used and printed to the terminal. This is done by the `measure` function, which chooses a random state contained within the `qsv` based on the probability of each state, and disables the variable containing the `qsv` for any further use in the program.

As a side note, `qsv`'s are _mutable_ data types, and they _cannot_ be copied using `copy` or `deepcopy` (No Cloning Theorem) 

## Conditional Logic

Conditional logic in quantum computing works similarly to classical computing, except that the `parallelize` operator must be applied first, as a `qsv` and a `qconst` cannot be directly compared if the `qsv` is in superposition. In QuantumPython, if statements can be declared by the context manager `qif`.

```python
with qif(<quantum boolean>):
  ...
```
The input to a `qif` must be a quantum boolean, which is basically a 1-bit `qsv`. Boolean expressions can also be substituted in instead, for example `qstate == qconst`

Currently, the only two boolean operators that are supported are `==` and `and`

## Entanglement

## Quantum Functions

## Additional Tools

- To view the contents of the quantum circuit being built behind the scenes, one can use the `printqc` function, which takes no arguments and returns nothing
```python
from qython import printqc
printqc()
```

- To check the number of qubits being used at a particular instance, one can use the `qmemcount` function, which takes no arguments and returns an integer
```python
from qython import qmemcount
print(qmemcount())
```
