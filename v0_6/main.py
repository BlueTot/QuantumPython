'''Imports'''

from sys import argv
import re
from qiskit_aer import Aer
from qiskit.circuit import QuantumCircuit, QuantumRegister, ClassicalRegister

'''Helper Classes & Functions'''

class ArgumentError(Exception): # Argument error
    pass

class QuantumError(Exception): # Quantum error
    pass

def extract(pattern, string, positions): # RE extract function
    p = re.compile(pattern)
    result = p.search(string)
    return [result.group(i) for i in positions]

def get_var_name(obj): # Find all variable names with a given object
    var_names = []
    for k, v in Interpreter.exec_locals.items():
        if v is obj:
            var_names.append(k)
    return var_names

class qstate: # quantum state class, instantiated through the use of the "forall" statement
    
    def __init__(self, qsv_var): # constructor

        self.qsv_var = qsv_var


class qsv_inner: # quantum state vector class (inner workings, covered by interface)

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
    
    # Hadamard transform on qsv
    def h(self):
             
        for i in range(self.__num_bits):
            Interpreter.qc.h(self.__qreg[i])

'''Classes & Functions accessible by quantum script'''

class qsv: # quantum state vector class (interface)

    def __init__(self, num_bits, value):
        self.__inner = qsv_inner(num_bits, value)
        Interpreter.qsv_mapping[hash(self)] = self.__inner

    @property
    def num_bits(self):
        return self.__inner.num_bits
    
    # Hadamard transform on qsv
    def h(self):
        self.__inner.h()

    def __repr__(self): # try to print qsv
        raise QuantumError("You cannot view the state of a quantum state vector")

    def __copy__(self): # try to copy qsv
        raise QuantumError("No cloning theorem does not allow copying a QSV")

    def __deepcopy__(self): # try to deep copy qsv
        raise QuantumError("No cloning theorem does not allow deep-copying a QSV")

def measure(qvar : qsv) -> int: # Measurement function

    if not isinstance(qvar, qsv): # Variable is not a QSV
        raise TypeError(f"Measurement cannot be performed on {type(qvar)}")

    outside_qvar = qvar
    qvar = Interpreter.qsv_mapping[hash(qvar)] # map to inner class
                
    creg = ClassicalRegister(qvar.num_bits)
    Interpreter.qc.add_register(creg)
    Interpreter.qc.measure(qvar.qreg, creg)

    Interpreter.cregs.append(hash(qvar))

    Interpreter.remove_variable(outside_qvar) # remove interface of qsv

    return Interpreter.get_measurement(hash(qvar))

def quantum(func): # Quantum function decorator

    def wrapper(*args, **kwargs): # wrapper to get the arguments of the function
        
        has_quantum_args= any([isinstance(arg, qstate) or isinstance(arg, qsv) for arg in list(args)+list(kwargs.values())])
        
        if not has_quantum_args: # all classical arguments
            return func(*args, **kwargs) # call the classical function itself

        else:
            code = Interpreter.functions[func.__name__]
            print(f"needs to be quantum processed, code : {code}")

    return wrapper

'''Main Interpreter'''

class Interpreter:

    INDENT_SIZE = 4 # default indent size = 4 spaces
    qc = QuantumCircuit() # quantum circuit
    cregs = [] # classical registers
    exec_globals = {"qsv": qsv, "measure": measure, "quantum": quantum} # allowed default classes & functions in quantum script
    exec_locals = {} # locals for exec
    qsv_mapping = {} # mapping between interface and inner qsv data type
    functions = {} # to store function code
    
    @classmethod
    def __exec_code(cls, code): # Run code method
        exec(code, cls.exec_globals, cls.exec_locals)

    @classmethod
    def remove_variable(cls, instance): # Delete variable from locals
        for var_name in get_var_name(instance):
            cls.exec_locals.pop(var_name)

    @classmethod
    def get_measurement(cls, creg): # method to get measurement from quantum circuit

        sv_sim = Aer.get_backend('statevector_simulator')
        result = sv_sim.run(cls.qc).result()
        counts = list(result.get_counts(cls.qc).keys())[0][::-1].split(" ")
        print(creg, counts)
        return int(counts[cls.cregs.index(creg)], 2)
    
    @classmethod
    def __num_indents(cls, code, ln): # function to get number of indents on a given line
        for idx, char in enumerate(code[ln]):
            if char != " ":
                if idx % cls.INDENT_SIZE != 0:
                    raise IndentationError(f"Indent Error occurred on line {ln+1}")
                return idx // cls.INDENT_SIZE
    
    @classmethod
    def __find_end_of_if_statement(cls, code, start_line, indents):
        for ln in range(start_line, len(code)):
            if cls.__num_indents(code, ln) <= indents and not re.match(r" *else:", code[ln]) and not re.match(r" *elif.*:", code[ln]):
                return ln
    
    @classmethod
    def __find_end_of_block(cls, code, start_line, indents): # function to find end of current block
        for ln in range(start_line, len(code)):
            if cls.__num_indents(code, ln) == indents:
                return ln
    
    @classmethod
    def interpret_quantum_function(cls, code): # interpret quantum code
        '''
        Conditions for quantum function:
            - classical computation is not allowed
            - only quantum states can be modified, not qsv's
            - qsv's can be used as a reference for entanglement purposes
        '''
        pass
    
    @classmethod
    def interpret(cls, code): # interpret normal code
        
        code.append("END") # ending line to make sure custom syntax parsing works

        ln = 0
        while ln < len(code):

            line = code[ln]

            new_line = line.replace(" ", "") # remove spaces
            
            # Ending line for custom syntax parsing
            if new_line == "END":
                return
            
            # CUSTOM SYNTAX: forall <state> in <qsv>:
            elif re.match(p := r"forall(.*)in(.*):", new_line):
                
                statevar_name, qvar_name = extract(p, new_line, [1, 2])

                if qvar_name not in cls.exec_locals: # variable does not exist
                    raise NameError(f"{qvar_name} does not exist")

                qvar = cls.exec_locals[qvar_name] # get instance of qvar variable

                if not isinstance(qvar, qsv): # wrong data type
                    raise TypeError(f"forall ... in ... cannot be used with {type(qvar)} data type") 
    
                end_of_forall_statement = cls.__find_end_of_block(code, ln+1, cls.__num_indents(code, ln))
                indents = cls.__num_indents(code, ln+1)
                
                # create new quantum state variable
                cls.exec_locals[statevar_name] = qstate(qvar)

                # recursively interpret the code inside the block
                cls.interpret_quantum_function(c := [l[cls.INDENT_SIZE*indents:] for l in code[ln+1 : end_of_forall_statement]])
               
                # delete state variable upon exiting forall block
                cls.remove_variable(cls.exec_locals[statevar_name])

                # jump to code after the block
                ln = end_of_forall_statement
            
            # Quantum function decorator, indicates the start of a quantum function
            elif re.match(p :="@quantum", new_line):

                end_of_block = cls.__find_end_of_block(code, ln+2, cls.__num_indents(code, ln))
                indents = cls.__num_indents(code, ln+2)

                # store the function code and name
                function_code = code[ln+1 : end_of_block]
                function_name = extract(r"def(.*)\(.*", code[ln+1].replace(" ", ""), [1])[0]
                cls.functions[function_name] = function_code
                
                # execute via exec() to store to locals()
                cls.__exec_code("\n".join(code[ln : end_of_block]))

                ln = end_of_block # jump to code fater the block
            
            # Try to execute with python's interpreter (not allowed within a forall)
            else:
                cls.__exec_code(line)
                ln += 1
                
        
if __name__ in "__main__":

    if len(argv) != 2:
        raise ArgumentError("Invalid number of arguments")
    file = argv[1]
    with open(f"{file}") as f:
        code = f.read().splitlines()
    
    Interpreter.interpret(code)
