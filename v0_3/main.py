'''Imports'''

from sys import argv
import re
from qiskit_aer import Aer
from qiskit.circuit import QuantumCircuit, QuantumRegister, ClassicalRegister

'''Classes & Functions accessible by quantum script'''

class qsv: # quantum state vector class

    def __init__(self, num_bits, value): # constructor

        if type(num_bits) != int:
            raise TypeError("Number of bits must be an integer")

        if type(value) != int or not(0 <= int(value) < 2**num_bits):
            raise TypeError(f"Value must be a {num_bits}-bit non-negative integer")

        self.__num_bits = num_bits

        qreg = QuantumRegister(num_bits)
        Interpreter.qc.add_register(qreg)
        for i, bit in enumerate(bin(value)[2:].zfill(num_bits)):
            if bit == "1":
                Interpreter.qc.x(qreg[i])
        self.__qreg = qreg

    @property
    def num_bits(self):
        return self.__num_bits

    @property
    def qreg(self):
        return self.__qreg

    def h(self):
             
        for i in range(self.__num_bits):
            Interpreter.qc.h(self.__qreg[i])

def measure(qvar : qsv) -> int: # Measurement function

    if not isinstance(qvar, qsv): # Variable is not a QSV
        raise TypeError(f"Measurement cannot be performed on {type(qvar)}")
                
    creg = ClassicalRegister(qvar.num_bits)
    Interpreter.qc.add_register(creg)
    Interpreter.qc.measure(qvar.qreg, creg)

    Interpreter.cregs.append(hash(qvar))

    return Interpreter.get_measurement(hash(qvar))

'''Helper Classes & Functions'''

class QuantumState:
    def __init__(self, link):
        self.link = link

def extract(pattern, string, positions):
    p = re.compile(pattern)
    result = p.search(string)
    return [result.group(i) for i in positions]

'''Main Interpreter'''

class Interpreter:

    INDENT_SIZE = 4
    qc = QuantumCircuit()
    cregs = []
    exec_globals = {"qsv": qsv, "measure": measure}
    exec_locals = {}
    
    @classmethod
    def __exec_code(cls, code): # Run code method
        exec(code, cls.exec_globals, cls.exec_locals)

    @classmethod
    def get_measurement(cls, creg):

        sv_sim = Aer.get_backend('statevector_simulator')
        result = sv_sim.run(cls.qc).result()
        counts = list(result.get_counts(cls.qc).keys())[0][::-1].split(" ")
        print(creg, counts)
        return int(counts[cls.cregs.index(creg)], 2)
    
    def __num_indents(self, code, ln):
        for idx, char in enumerate(code[ln]):
            if char != " ":
                if idx % self.INDENT_SIZE != 0:
                    raise SyntaxError(f"Indent Error  occurred on line {ln}")
                return idx // self.INDENT_SIZE

    def __find_end_of_if_statement(self, code, start_line, indents):
        for ln in range(start_line, len(code)):
            if self.__num_indents(code, ln) <= indents and not re.match(r" *else:", code[ln]) and not re.match(r" *elif.*:", code[ln]):
                return ln

    def __find_end_of_curr_if_block(self, code, start_line, indents):
        for ln in range(start_line, len(code)):
            if self.__num_indents(code, ln) == indents:
                return ln
    
    @classmethod
    def interpret(cls, code):

        for ln, line in enumerate(code):
            
            print(ln, line)

            if False: # custom syntax
                line = line.replace(" ", "")

            else: # try to execute with python's interpreter
                cls.__exec_code(line)
        
if __name__ in "__main__":

    if len(argv) != 2:
        raise Exception("Invalid number of arguments")
    file = argv[1]
    with open(f"{file}") as f:
        code = f.read().splitlines()
    
    Interpreter.interpret(code)
