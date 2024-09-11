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

class RestrictedBuiltins(dict): # Custom dictionary to override builtins

    def __init__(self):
        self.restricted = __builtins__.__dict__.copy()

    def __getitem__(self, key):
        if key in self.restricted:  # List of restricted functions
            raise QuantumError(f"<{key}> is disabled in quantum environments")
        return super().__getitem__(key)

'''Internal Data Types (not accessible by quantum script)'''

class iqs: # intermediate quantum state, used for calculations by interpreter

    def __init__(self, num_bits):
        
        self.num_bits = num_bits
        self.qreg = QuantumRegister(num_bits)
        Interpreter.qc.add_register(self.qreg)
   
    # And operation
    def __and__(self, other):

        # Checking types
        if all([not isinstance(other, t) for t in (qconst, qconst_inner, qstate, iqs)]):
            raise TypeError("Argument must be a qconst/qstate")

        num_bits = self.num_bits # Number of bits of the qstate (self)

        if isinstance(other, qconst): # argument is a qconst
            q2 = Interpreter.qconst_mapping[hash(other)]

        elif isinstance(other, qconst_inner) or isinstance(other, iqs): # argument is a qconst_inner
            q2 = other
        
        else: # argument is a qstate
            q2 = Interpreter.qstate_mapping[hash(other)]
            q2 = Interpreter.qsv_mapping[hash(q2.qsv_var)]
        
        if q2.num_bits != num_bits:
            raise TypeError("Arguments must have the same number of bits")

        output = iqs(num_bits) # Create a new intermediate quantum state for the output
        
        for i in range(num_bits): # Loop through all bits
            Interpreter.qc.ccx(self.qreg[i], q2.qreg[i], output.qreg[i]) # AND operation

        return output # Return the IQS

class qconst_inner: # quantum constant class, used to define qsv's that cannot be modified (constants)

    def __init__(self, num_bits, value):

        if type(num_bits) != int:
            raise TypeError("Number of bits must be an integer")

        if type(value) != int or not(0 <= int(value) < 2**num_bits):
            raise TypeError(f"Value must be a {num_bits}-bit non-negative integer")

        self.num_bits = num_bits

        qreg = QuantumRegister(num_bits)
        Interpreter.qc.add_register(qreg)
        for i, bit in enumerate(bin(value)[2:].zfill(num_bits)):
            if bit == "1":
                Interpreter.qc.x(qreg[i])
        self.qreg = qreg

    def __and__(self, other): # And method
        return other.__and__(self)

class qstate_inner: # quantum state class, instantiated through the use of the "forall" statement
    
    def __init__(self, qsv_var): # constructor

        self.qsv_var = qsv_var

    def __and__(self, other): # And method
        
        # Checking types
        if all([not isinstance(other, t) for t in (qconst, qconst_inner, qstate, iqs)]):
            raise TypeError("Argument must be a qconst/qstate")

        num_bits = self.qsv_var.num_bits # Number of bits of the qstate (self)

        if isinstance(other, qconst): # argument is a qconst
            q2 = Interpreter.qconst_mapping[hash(other)]

        elif isinstance(other, qconst_inner) or isinstance(other, iqs): # argument is a qconst_inner
            q2 = other
        
        else: # argument is a qstate
            q2 = Interpreter.qstate_mapping[hash(other)]
            q2 = Interpreter.qsv_mapping[hash(q2.qsv_var)]
        
        if q2.num_bits != num_bits:
            raise TypeError("Arguments must have the same number of bits")

        output = iqs(num_bits) # Create a new intermediate quantum state for the output
        q1 = Interpreter.qsv_mapping[hash(self.qsv_var)]
        
        for i in range(num_bits): # Loop through all bits
            Interpreter.qc.ccx(q1.qreg[i], q2.qreg[i], output.qreg[i]) # AND operation

        return output # Return the IQS

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
    
    # Method to store state into qsv
    def store(self, state):

        if not(isinstance(state, qstate) or isinstance(state, iqs)):
            raise TypeError("You can only store qstates into a qsv")

        if isinstance(state, qstate): # state is a qstate
            state = Interpreter.qstate_mapping[hash(state)]
            state = Interpreter.qsv_mapping[hash(state.qsv_var)]
            Interpreter.qc.cx(state.qreg, self.__inner.qreg)

        else: # state is a iqs
            Interpreter.qc.cx(state.qreg, self.__inner.qreg)
        
        print(Interpreter.qc)

    def __repr__(self): # try to print qsv
        raise QuantumError("You cannot view the state of a quantum state vector")

    def __copy__(self): # try to copy qsv
        raise QuantumError("No cloning theorem does not allow copying a QSV")

    def __deepcopy__(self): # try to deep copy qsv
        raise QuantumError("No cloning theorem does not allow deep-copying a QSV")

class qstate: # quantum state class (interface)

    def __init__(self, qsv_var):

        self.__inner = qstate_inner(qsv_var)
        Interpreter.qstate_mapping[hash(self)] = self.__inner
    
    def __repr__(self):
        raise QuantumERror("You cannot view the state of a quantum state")

    def __and__(self, other):

        return self.__inner.__and__(other)

class qconst:

    def __init__(self, num_bits, value):

        self.__value = value
        self.__inner = qconst_inner(num_bits, value)
        Interpreter.qconst_mapping[hash(self)] = self.__inner

    def __repr__(self):
        return f"qconst({self.__value})"

    def __and__(self, other):

        return self.__inner.__and__(other)

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
    exec_globals_stack = [{"qsv": qsv, "qconst": qconst, "measure": measure, "quantum": quantum}]
    exec_locals_stack = [{}] # locals for exec
    forall_stack = []
    qsv_mapping = {} # mapping between interface and inner qsv data type
    qstate_mapping = {}
    qconst_mapping = {}
    functions = {} # to store function code

    @classmethod
    @property
    def exec_globals(cls):
        return cls.exec_globals_stack[-1]

    @classmethod
    @property
    def exec_locals(cls):
        return cls.exec_locals_stack[-1]
    
    @classmethod
    def __exec_code(cls, code): # Run code method
        exec(code, cls.exec_globals, cls.exec_locals)

    @classmethod
    def remove_variable(cls, instance): # Delete variable from locals
        for var_name in get_var_name(instance):
            cls.exec_locals.pop(var_name)
    
    @classmethod
    def check_assigned_iqs(cls): # Check for assigned intermediate quantum states
        for varname, instance in cls.exec_locals.items():
            if isinstance(instance, iqs): # IQS assigned to a variable
                raise TypeError(f"Result from arithmetic operation directly assigned to the variable <{varname}>")

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
    def in_forall(cls):
        return len(cls.exec_globals_stack) > 1

    @classmethod
    def enter_forall(cls): # enter the forall statement

        # copy globals and locals
        new_globals, new_locals = cls.exec_globals.copy(), cls.exec_locals.copy()

        # disable all builtins within the forall
        new_globals["__builtins__"] = RestrictedBuiltins()

        # remove unallowed functions and data types
        for k, v in cls.exec_globals.items():
            if k in ("measure", "qsv", "quantum"):
                new_globals.pop(k)

        # remove unallowed built in data types
        for k, v in cls.exec_locals.items():
            if isinstance(v, (int, float, str, bool, list, dict, tuple, set)):
                new_locals.pop(k)

        cls.exec_globals_stack.append(new_globals)
        cls.exec_locals_stack.append(new_locals)

    @classmethod
    def exit_forall(cls): # exit the forall statement
        
        cls.exec_globals_stack.pop()
        cls.exec_locals_stack.pop()

    @classmethod
    def check_classical_variables(cls):
        if cls.in_forall():
            for name, instance in cls.exec_locals.items():
                if isinstance(instance, (int, float, str, bool, list, dict, tuple, set)):
                    raise QuantumError(f"{type(instance)} is not allowed in quantum environments")

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

                if qvar_name in cls.forall_stack:
                    raise QuantumError(f"forall has already been used on <{qvar_name}>")

                qvar = cls.exec_locals[qvar_name] # get instance of qvar variable

                if not isinstance(qvar, qsv): # wrong data type
                    raise TypeError(f"forall ... in ... cannot be used with {type(qvar)} data type") 
    
                end_of_forall_statement = cls.__find_end_of_block(code, ln+1, cls.__num_indents(code, ln))
                indents = cls.__num_indents(code, ln+1)
                
                # create new quantum state variable
                cls.exec_locals[statevar_name] = qstate(qvar)

                # recursively interpret the code inside the block
                cls.enter_forall()
                cls.forall_stack.append(qvar_name)
                cls.interpret(c := [l[cls.INDENT_SIZE*indents:] for l in code[ln+1 : end_of_forall_statement]])

                # delete state variable upon exiting forall block
                cls.exit_forall()
                cls.remove_variable(cls.exec_locals[statevar_name])
                cls.forall_stack.pop()

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

            cls.check_assigned_iqs()
            cls.check_classical_variables()
                
        
if __name__ in "__main__":

    if len(argv) != 2:
        raise ArgumentError("Invalid number of arguments")
    file = argv[1]
    with open(f"{file}") as f:
        code = f.read().splitlines()
    
    Interpreter.interpret(code)
