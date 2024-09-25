'''Imports'''

from qiskit_aer import Aer
from qiskit.circuit import QuantumCircuit, QuantumRegister, ClassicalRegister

'''Helper Classes & Functions'''

class _ArgumentError(Exception): # Argument error
    pass

class _QuantumError(Exception): # Quantum error
    pass

class _RestrictedBuiltins(dict): # Custom dictionary to override builtins

    def __init__(self):
        self.restricted = __builtins__.__dict__.copy()

    def __getitem__(self, key):
        if key in self.restricted:  # List of restricted functions
            raise _QuantumError(f"<{key}> is disabled in quantum environments")
        return super().__getitem__(key)

'''Internal Data Types (not accessible by import)'''

class _iqs: # intermediate quantum state, used for calculations by interpreter

    def __init__(self, num_bits):
        
        self.num_bits = num_bits
        self.qreg = QuantumRegister(num_bits)
        _QuantumManager.qc.add_register(self.qreg)
   
    # And operation
    def __and__(self, other):

        # Checking types
        if all([not isinstance(other, t) for t in (qconst, qconst_inner, qstate, iqs)]):
            raise TypeError("Argument must be a qconst/qstate")

        num_bits = self.num_bits # Number of bits of the qstate (self)

        if isinstance(other, qconst): # argument is a qconst
            q2 = _QuantumManager.qconst_mapping[hash(other)]

        elif isinstance(other, qconst_inner) or isinstance(other, iqs): # argument is a qconst_inner
            q2 = other
        
        else: # argument is a qstate
            q2 = _QuantumManager.qstate_mapping[hash(other)]
            q2 = _QuantumManager.qsv_mapping[hash(q2.qsv_var)]
        
        if q2.num_bits != num_bits:
            raise TypeError("Arguments must have the same number of bits")

        output = iqs(num_bits) # Create a new intermediate quantum state for the output
        
        for i in range(num_bits): # Loop through all bits
            _QuantumManager.qc.ccx(self.qreg[i], q2.qreg[i], output.qreg[i]) # AND operation

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

    def __and__(self, other): # And method
        return other.__and__(self)

class _qstate_inner: # quantum state class, instantiated through the use of the "forall" statement
    
    def __init__(self, qsv_var): # constructor

        self.qsv_var = qsv_var

    def __and__(self, other): # And method
        
        # Checking types
        if all([not isinstance(other, t) for t in (qconst, qconst_inner, qstate, iqs)]):
            raise TypeError("Argument must be a qconst/qstate")

        num_bits = self.qsv_var.num_bits # Number of bits of the qstate (self)

        if isinstance(other, qconst): # argument is a qconst
            q2 = _QuantumManager.qconst_mapping[hash(other)]

        elif isinstance(other, qconst_inner) or isinstance(other, iqs): # argument is a qconst_inner
            q2 = other
        
        else: # argument is a qstate
            q2 = _QuantumManager.qstate_mapping[hash(other)]
            q2 = _QuantumManager.qsv_mapping[hash(q2.qsv_var)]
        
        if q2.num_bits != num_bits:
            raise TypeError("Arguments must have the same number of bits")

        output = iqs(num_bits) # Create a new intermediate quantum state for the output
        q1 = _QuantumManager.qsv_mapping[hash(self.qsv_var)]
        
        for i in range(num_bits): # Loop through all bits
            _QuantumManager.qc.ccx(q1.qreg[i], q2.qreg[i], output.qreg[i]) # AND operation

        return output # Return the IQS

class _qsv_inner: # quantum state vector class (inner workings, covered by interface)

    def __init__(self, num_bits, value): # constructor

        if type(num_bits) != int:
            raise TypeError("Number of bits must be an integer")

        if type(value) != int or not(0 <= int(value) < 2**num_bits):
            raise TypeError(f"Value must be a {num_bits}-bit non-negative integer")
        
        self.__num_bits = num_bits

        qreg = QuantumRegister(num_bits)
        _QuantumManager.qc.add_register(qreg)
        for i, bit in enumerate(bin(value)[2:].zfill(num_bits)):
            if bit == "1":
                _QuantumManager.qc.x(qreg[i])
        self.__qreg = qreg

        self.measured = False

    @property
    def num_bits(self):
        return self.__num_bits

    @property
    def qreg(self):
        return self.__qreg
    
    # Hadamard transform on qsv
    def h(self):
             
        for i in range(self.__num_bits):
            _QuantumManager.qc.h(self.__qreg[i])

class _qstate: # quantum state class (interface)

    def __init__(self, qsv_var):

        self.__inner = _qstate_inner(qsv_var)
        _QuantumManager.qstate_mapping[hash(self)] = self.__inner
    
    def __repr__(self):
        raise _QuantumError("You cannot view the state of a quantum state")

    def __and__(self, other):

        return self.__inner.__and__(other)

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
        print(_QuantumManager.qc)

    # Method to store state into qsv
    def store(self, state):

        if self.__inner.measured:
            raise _QuantumError("qsv no longer exists")

        if not(isinstance(state, qstate) or isinstance(state, iqs)):
            raise TypeError("You can only store qstates into a qsv")

        if isinstance(state, qstate): # state is a qstate
            state = _QuantumManager.qstate_mapping[hash(state)]
            state = _QuantumManager.qsv_mapping[hash(state.qsv_var)]
            _QuantumManager.qc.cx(state.qreg, self.__inner.qreg)

        else: # state is a iqs
            _QuantumManager.qc.cx(state.qreg, self.__inner.qreg)
        
        print(_QuantumManager.qc)

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

    outside_qvar = qvar
    qvar = _QuantumManager.qsv_mapping[hash(qvar)] # map to inner class

    creg = ClassicalRegister(qvar.num_bits)
    _QuantumManager.qc.add_register(creg)
    _QuantumManager.qc.measure(qvar.qreg, creg)

    _QuantumManager.cregs.append(hash(qvar))
    qvar.measured = True

    return _QuantumManager.get_measurement(hash(qvar))

def quantum(func): # Quantum function decorator

    def wrapper(*args, **kwargs): # wrapper to get the arguments of the function
        
        has_quantum_args= any([isinstance(arg, qstate) or isinstance(arg, qsv) for arg in list(args)+list(kwargs.values())])
        
        if not has_quantum_args: # all classical arguments
            return func(*args, **kwargs) # call the classical function itself

        else:
            print(f"needs to be quantum processed")

    return wrapper

'''Circuit Manager'''

class _QuantumManager:

    qc = QuantumCircuit() # quantum circuit
    cregs = [] # classical registers
    qsv_mapping = {} # mapping between interface and inner qsv data type
    qstate_mapping = {}
    qconst_mapping = {}

    @classmethod
    def get_measurement(cls, creg): # method to get measurement from quantum circuit

        sv_sim = Aer.get_backend('statevector_simulator')
        result = sv_sim.run(cls.qc).result()
        counts = list(result.get_counts(cls.qc).keys())[0][::-1].split(" ")
        print(creg, counts)
        return int(counts[cls.cregs.index(creg)], 2)
 
