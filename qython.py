'''Imports'''

from qiskit_aer import Aer
from qiskit.circuit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.compiler import transpile
from contextlib import contextmanager
import sys
import builtins

'''Helper Classes & Functions'''

# class _ArgumentError(Exception): # Argument error
#     pass

class _QuantumError(Exception): # Quantum error
    pass

class _DisallowType: # Context manager to disable classical variables and functions in the forall construct
    def __init__(self, *types, disable_builtins=None):
        self.types = types
        self.disable_builtins = disable_builtins or []
        self.original_builtins = {}
        self.enabled = False
        self.original_trace_function = sys.gettrace()

    def manual_enter(self):
        if not self.enabled:
            self.original_trace_function = sys.gettrace()
            sys.settrace(self.trace_calls)
            self.override_builtins()
            self.enabled = True

    def manual_exit(self):
        if self.enabled:
            sys.settrace(self.original_trace_function)
            self.restore_builtins()
            self.enabled = False

    def __enter__(self): # enter context manager, disable variables and functions
        self.manual_enter()
        return self

    def __exit__(self, exc_type, exc_value, traceback): # exit context manager, re-enable variables and functions
        self.manual_exit()

    def trace_calls(self, frame, event, arg):
        if event == 'call':
            return self.trace_lines
        return None

    def trace_lines(self, frame, event, arg): # check variables within local scope of function
        if event == 'line':
            local_vars = frame.f_locals.copy()
            for var_name, var_value in local_vars.items():
                if isinstance(var_value, self.types) and var_name[:2] != "__" and var_name[-2:] != "__":
                    raise _QuantumError(f"Instantiation of variable <{var_name}> of type {type(var_value).__name__} is disallowed in quantum environments")
        return self.trace_lines

    def override_builtins(self): # override the builtins dictionary

        sys.settrace(self.original_trace_function) # disable data type ban

        for name in self.disable_builtins:
            if name in builtins.__dict__:
                self.original_builtins[name] = builtins.__dict__[name]
                builtins.__dict__[name] = self.disabled_builtin(name)

        self.original_trace_function = sys.gettrace() # enable data type ban
        sys.settrace(self.trace_calls)

    def restore_builtins(self): # restore builtins
        for name, original in self.original_builtins.items():
            builtins.__dict__[name] = original

    def disabled_builtin(self, name): # raise error if function is disabled

        def disabled(*args, **kwargs):
            raise _QuantumError(f"The built-in function '{name}' is disabled.")

        return disabled

'''Internal Data Types (not accessible by import)'''

class _iqs: # intermediate quantum state, used for calculations by interpreter

    def __init__(self, __num_bits__):
        global cm
            
        cm.manual_exit()

        self.num_bits = __num_bits__
        self.qreg = QuantumRegister(self.num_bits)
        _QuantumManager.qc.add_register(self.qreg)
        
        cm.manual_enter()

    # And operation
    def __and__(self, other):
        global cm

        # Checking types
        if all([not isinstance(other, t) for t in (qconst, _qconst_inner, _qstate, _iqs)]):
            raise TypeError("Argument must be a qconst/qstate")

        if isinstance(other, qconst): # argument is a qconst
            q2 = _QuantumManager.qconst_mapping[hash(other)]

        elif isinstance(other, _qconst_inner) or isinstance(other, _iqs): # argument is a _qconst_inner
            q2 = other
        
        else: # argument is a qstate
            q2 = _QuantumManager.qstate_mapping[hash(other)]
            q2 = _QuantumManager.qsv_mapping[hash(q2.qsv_var)]
        
        if q2.num_bits != self.num_bits:
            raise TypeError("Arguments must have the same number of bits")
        
        output = _iqs(self.num_bits) # Create a new intermediate quantum state for the output
        
        cm.manual_exit()

        for i in range(self.num_bits): # Loop through all bits
            _QuantumManager.qc.ccx(self.qreg[i], q2.qreg[i], output.qreg[i]) # AND operation
        
        cm.manual_enter()

        return output # Return the IQS

class _qconst_inner: # quantum constant class, used to define qsv's that cannot be modified (constants)

    def __init__(self, num_bits, value):

        if type(num_bits) != int:
            raise TypeError("Number of bits must be an integer")

        if type(value) != int or not(0 <= int(value) < 2**num_bits):
            raise TypeError(f"Value must be a {num_bits}-bit non-negative integer")
    
        self.num_bits = num_bits

        qreg = QuantumRegister(num_bits)
        _QuantumManager.qc.add_register(qreg)
        for i, bit in enumerate(bin(value)[2:].zfill(num_bits)):
            if bit == "1":
                _QuantumManager.qc.x(qreg[i])
        self.qreg = qreg
    
    def __hash__(self):
        return id(self)

    def __and__(self, other): # And method
        return other.__and__(self)
        
    def __eq__(self, other): # Equality method
        return other.__eq__(self)

class _qstate_inner: # quantum state class, instantiated through the use of the "forall" statement
    
    def __init__(self, qsv_var): # constructor

        self.qsv_var = qsv_var

    def __and__(self, other): # And method
        global cm
        
        # Checking types
        if not isinstance(other, (qconst, _qconst_inner, _qstate, _iqs)):
            raise TypeError("Argument must be a qconst/qstate")

        if isinstance(other, qconst): # argument is a qconst
            q2 = _QuantumManager.qconst_mapping[hash(other)]

        elif isinstance(other, (_qconst_inner, _iqs)): # argument is a _qconst_inner
            q2 = other
        
        else: # argument is a qstate
            q2 = _QuantumManager.qstate_mapping[hash(other)]
            q2 = _QuantumManager.qsv_mapping[hash(q2.qsv_var)]
        
        if q2.num_bits != self.qsv_var.num_bits:
            raise TypeError("Arguments must have the same number of bits")
        
        output = _iqs(self.qsv_var.num_bits) # Create a new intermediate quantum state for the output
        q1 = _QuantumManager.qsv_mapping[hash(self.qsv_var)]
        
        cm.manual_exit()

        for i in range(self.qsv_var.num_bits): # Loop through all bits
            _QuantumManager.qc.ccx(q1.qreg[i], q2.qreg[i], output.qreg[i]) # AND operation
        
        cm.manual_enter()

        return output # Return the IQS

    def __eq__(self, other): # Equality method
        global cm

        # Checking types
        if not isinstance(other, (qconst, _qconst_inner, _qstate, _iqs)):
            raise TypeError("Argument must be a qconst/qstate")

        if isinstance(other, qconst): # argument is a qconst
            q2 = _QuantumManager.qconst_mapping[hash(other)]

        elif isinstance(other, (_qconst_inner, _iqs)): # argument is a _qconst_inner
            q2 = other
        
        else: # argument is a qstate
            q2 = _QuantumManager.qstate_mapping[hash(other)]
            q2 = _QuantumManager.qsv_mapping[hash(q2.qsv_var)]
        
        if q2.num_bits != self.qsv_var.num_bits:
            raise TypeError("Arguments must have the same number of bits")
        
        output = _iqs(1) # create the output register
        q1 = _QuantumManager.qsv_mapping[hash(self.qsv_var)]

        cm.manual_exit() # disable the context manager
        
        _QuantumManager.qc.add_register(ancilla_reg := QuantumRegister(self.qsv_var.num_bits)) # Allocate a working register

        for i in range(self.qsv_var.num_bits):
            _QuantumManager.qc.cx(q1.qreg[i], ancilla_reg[i])
            _QuantumManager.qc.cx(q2.qreg[i], ancilla_reg[i])
        _QuantumManager.qc.mcx(ancilla_reg, output.qreg, ctrl_state="0"*self.qsv_var.num_bits)
        
        cm.manual_enter() # re-enable the context manager
        
        return output

class _qsv_inner: # quantum state vector class (inner workings, covered by interface)

    def __init__(self, num_bits, value): # constructor

        if type(num_bits) != int:
            raise TypeError("Number of bits must be an integer")

        if type(value) != int or not(0 <= int(value) < 2**num_bits):
            raise TypeError(f"Value must be a {num_bits}-bit non-negative integer")
        
        self.num_bits = num_bits

        qreg = QuantumRegister(num_bits)
        _QuantumManager.qc.add_register(qreg)
        for i, bit in enumerate(bin(value)[2:].zfill(num_bits)):
            if bit == "1":
                _QuantumManager.qc.x(qreg[i])
        self.qreg = qreg

        self.measured = False

    # Hadamard transform on qsv
    def h(self):
        for i in range(self.num_bits):
            _QuantumManager.qc.h(self.qreg[i])

class _qstate: # quantum state class (interface)

    def __init__(self, qsv_var):

        self.__inner = _qstate_inner(qsv_var)
        _QuantumManager.qstate_mapping[hash(self)] = self.__inner
    
    def __hash__(self):
        return id(self)

    def __repr__(self):
        raise _QuantumError("You cannot view the state of a quantum state")

    def __and__(self, other):
        global cm

        cm.manual_exit()
        output = self.__inner.__and__(other)
        cm.manual_enter()

        return output

    def __eq__(self, other):
        global cm

        cm.manual_exit()
        output = self.__inner.__eq__(other)
        cm.manual_enter()

        return output

'''Classes & Functions accessible by import'''

class qsv: # quantum state vector class (interface)

    def __init__(self, num_bits, value):

        self.__inner = _qsv_inner(num_bits, value)
        _QuantumManager.qsv_mapping[hash(self)] = self.__inner

    @property
    def num_bits(self):

        if self.__inner.measured:
            raise _QuantumError("qsv no longer exists")

        return self.__inner.num_bits
    
    # Hadamard transform on qsv
    def h(self):

        if self.__inner.measured:
            raise _QuantumError("qsv no longer exists")

        self.__inner.h()

    # Method to store state into qsv
    def store(self, state):
        global cm

        if self.__inner.measured:
            raise _QuantumError("qsv no longer exists")

        if not(isinstance(state, _qstate) or isinstance(state, _iqs)):
            raise TypeError("You can only store qstates into a qsv")
        
        cm.manual_exit()

        if isinstance(state, _qstate): # state is a qstate
            state = _QuantumManager.qstate_mapping[hash(state)]
            state = _QuantumManager.qsv_mapping[hash(state.qsv_var)]
            _QuantumManager.qc.cx(state.qreg, self.__inner.qreg)

        else: # state is a iqs
            _QuantumManager.qc.cx(state.qreg, self.__inner.qreg)
        
        cm.manual_enter()

    @property
    def states(self):
        return [_qstate(self)]

    def __repr__(self): # try to print qsv

        if self.__inner.measured:
            raise _QuantumError("qsv no longer exists")

        raise _QuantumError("You cannot view the state of a quantum state vector")

    def __copy__(self): # try to copy qsv
        raise _QuantumError("No cloning theorem does not allow copying a QSV")

    def __deepcopy__(self): # try to deep copy qsv
        raise _QuantumError("No cloning theorem does not allow deep-copying a QSV")

class qconst: # quatnum constant class

    def __init__(self, num_bits, value):

        self.__value = value
        self.__inner = _qconst_inner(num_bits, value)
        _QuantumManager.qconst_mapping[hash(self)] = self.__inner

    def __repr__(self):
        return f"qconst({self.__value})"

    def __and__(self, other):

        return self.__inner.__and__(other)

def measure(qvar : qsv) -> int: # Measurement function

    if not isinstance(qvar, qsv): # Variable is not a QSV
        raise TypeError(f"Measurement cannot be performed on {type(qvar)}")

    # outside_qvar = qvar
    qvar = _QuantumManager.qsv_mapping[hash(qvar)] # map to inner class

    creg = ClassicalRegister(qvar.num_bits)
    _QuantumManager.qc.add_register(creg)
    _QuantumManager.qc.measure(qvar.qreg, creg)

    _QuantumManager.cregs.append(hash(qvar))
    qvar.measured = True

    return _QuantumManager.get_measurement(hash(qvar))

def quantum(func): # Quantum function decorator

    def wrapper(*args, **kwargs): # wrapper to get the arguments of the function
        
        has_quantum_args= any([isinstance(arg, _qstate) or isinstance(arg, qsv) for arg in list(args)+list(kwargs.values())])
        
        if not has_quantum_args: # all classical arguments
            return func(*args, **kwargs) # call the classical function itself

        else:
            print(f"needs to be quantum processed")

    return wrapper

def parallelize(iterable): # Forall decorator to run quantum code in parallel
    def decorator(func):
        def wrapper(*args, **kwargs):
            global cm
            with _DisallowType(int, str, float, bool, list, tuple, dict, set, 
                    disable_builtins=['print']) as cm:
                for item in iterable:
                    func(item)
        return wrapper
    return decorator

def auto_execute(func): # Decorator to auto execute functions after definition
    func()
    return func

class qif:
    
    def __init__(self, qbool): # Constructor
        global cm

        if not isinstance(qbool, (_qstate, _iqs)):
            raise TypeError("Input to a conditional must be a quantum boolean")
       
        cm.manual_exit()

        if isinstance(qbool, _qstate):
            qbool = _QuantumManager.qstate_mapping[hash(qbool)]
            qbool = _QuantumManager.qsv_mapping[hash(qbool.qsv_var)]
        
        if qbool.num_bits != 1:
            raise TypeError("Input to a conditional must be a quantum boolean")

        self.condition_register = qbool.qreg
        regs = []
        for reg in _QuantumManager.main_qc.qregs:
            if reg != self.condition_register:
                regs.extend([reg[i] for i in range(reg.size)])

        self.__qc = QuantumCircuit(regs)
        cm.manual_enter()
    
    def __enter__(self): # Upon entering context manager
        _QuantumManager.qc = self.__qc

    def __exit__(self, exc_type, exc_value, tb): # Upon exiting context manager
        global cm

        cm.manual_exit()
       
        for reg in _QuantumManager.qc.qregs:
            if reg not in _QuantumManager.main_qc.qregs:
                _QuantumManager.main_qc.add_register(reg)

        regs = []
        for reg in _QuantumManager.main_qc.qregs:
            if reg != self.condition_register:
                regs.extend([reg[i] for i in range(reg.size)])

        controlled_gate = _QuantumManager.qc.to_gate(label="custom").control(1)
        _QuantumManager.main_qc.append(controlled_gate, [self.condition_register[0]] + regs)
        _QuantumManager.qc = _QuantumManager.main_qc
        _QuantumManager.main_qc = _QuantumManager.main_qc
        
        #print(_QuantumManager.main_qc)

        cm.manual_enter()

# function that prints the quantum circuit (debugging use!)
def printqc():
    print(_QuantumManager.main_qc)

# function that returns the number of qubits being used currently
def qmemcount():
    return _QuantumManager.main_qc.num_qubits

'''Circuit Manager'''

class _QuantumManager:
    
    main_qc = QuantumCircuit() # main quantum circuit
    qc = main_qc # current circuit being built
    cregs = [] # classical registers
    qsv_mapping = {} # mapping between interface and inner qsv data type
    qstate_mapping = {}
    qconst_mapping = {}

    @classmethod
    def get_measurement(cls, creg): # method to get measurement from quantum circuit

        sv_sim = Aer.get_backend('statevector_simulator')
        transpiled_circuit = transpile(cls.qc, sv_sim)
        result = sv_sim.run(transpiled_circuit).result()
        counts = list(result.get_counts(transpiled_circuit).keys())[0][::-1].split(" ")
        #print(creg, counts)
        return int(counts[cls.cregs.index(creg)], 2)
 
