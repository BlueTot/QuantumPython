from sys import argv
import re
from qiskit_aer import Aer
from qiskit.circuit import QuantumCircuit, QuantumRegister, ClassicalRegister

class ArgumentError(Exception):
    pass

class SyntaxError(Exception):
    pass

class AssignmentError(Exception):
    pass

class VariableNotFoundError(Exception):
    pass

class DataTypeError(Exception):
    pass

class DataType:
    def __init__(self, num_bits, value):
        self.num_bits = num_bits
        self.value = value

class Integer(DataType):
    def __init__(self, num_bits, value):
        super().__init__(num_bits, value)

class QuantumStateVector(DataType):
    def __init__(self, num_bits, value):
        super().__init__(num_bits, value)

def extract(pattern, string, positions):
    p = re.compile(pattern)
    result = p.search(string)
    return [result.group(i) for i in positions]

class Interpreter:
    

    def __init__(self):

        self.__variables = {}
        self.__qc = QuantumCircuit()
        self.__cregs = []

    def get_measurement(self, creg):

        sv_sim = Aer.get_backend('statevector_simulator')
        result = sv_sim.run(self.__qc).result()
        counts = list(result.get_counts(self.__qc).keys())[0][::-1].split(" ")
        print(creg, counts)
        return int(counts[self.__cregs.index(creg)], 2)

    def interpret(self, code):

        try:
        
            for ln, line in enumerate(code):
            
                line = line.replace(" ", "")
                print(line)

                # Quantum State Vector declaration: qsv[n] <var> = ...
                if re.match(p := r"qsv\[(.*)\](.*)=\|(.*)\>", line):

                    num_bits, varname, value = extract(p, line, [1, 2, 3])
                    num_bits, value = int(num_bits), int(value)
                    print(num_bits, varname, value)

                    if not str(value).isdigit(): # value is not an integer
                        raise AssignmentError(f"QSV must be assigned a single integer when created")

                    qreg = QuantumRegister(num_bits)
                    self.__qc.add_register(qreg)
                    for i, bit in enumerate(bin(value)[2:].zfill(num_bits)):
                        if bit == "1":
                            self.__qc.x(qreg[i])
                    self.__variables[varname] = QuantumStateVector(num_bits, qreg)

                    print(self.__qc)
                
                # Hadamard Transform on QSV: qsv.h()
                elif re.match(p := r"(.*).h()", line):

                    varname = extract(p, line, [1])[0]
                    print(varname)
                    
                    if varname not in self.__variables: # Variable doesn't exist
                        raise VariableNotFoundError(f"{varname} does not exist")

                    if not isinstance(self.__variables[varname], QuantumStateVector): # Variable is not a QSV
                        raise DataTypeError(f"Hadamard transform cannot be performed on {type(self.__variables[varname])}")
                        
                    for i in range(self.__variables[varname].num_bits):
                        self.__qc.h(self.__variables[varname].value[i])

                    print(self.__qc)
                
                # Measurement operation on QSV: int[n] <var> = measure(<qsv>)
                elif re.match(p := r"int\[(.*)\](.*)=measure\((.*)\)", line):

                    num_bits, varname, qsvname = extract(p, line, [1, 2, 3])
                    num_bits = int(num_bits)
                    print(num_bits, varname, qsvname)
                    
                    if qsvname not in self.__variables: # Variable doesn't exist
                        raise VariableNotFoundError(f"{qsvname} does not exist")
                    
                    if not isinstance(self.__variables[qsvname], QuantumStateVector): # Variable is not a QSV
                        raise DataTypeError(f"Measurement cannot be performed on {type(self.__variables[qsvname])}")
                    
                    if self.__variables[qsvname].num_bits != num_bits: # Different number of bits in creg and qreg
                        raise DataTypeError(f"Measurement must be performed between an integer and QSV with the same number of bits")

                    creg = ClassicalRegister(num_bits)
                    self.__qc.add_register(creg)
                    for i in range(num_bits):
                        self.__qc.measure(self.__variables[qsvname].value[i], creg[i])
                    self.__variables[varname] = Integer(num_bits, creg)
                    self.__cregs.append(varname)

                    print(self.__qc)
                    print(self.get_measurement(varname))

                # Syntax not supported, raise an error
                else:
                    
                    raise SyntaxError(f"Syntax error occurred on line {ln+1}")

        except SyntaxError as err:
            print(err)
        
        except AssignmentError as err:
            print(err)

        except VariableNotFoundError as err:
            print(err)

        except DataTypeError as err:
            print(err)

if __name__ in "__main__":

    if len(argv) != 2:
        raise ArgumentError("Invalid number of arguments")
    file = argv[1]
    with open(f"{file}") as f:
        code = f.read().splitlines()
    
    interpreter = Interpreter()
    interpreter.interpret(code)
