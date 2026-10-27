"""Local adapter for the pinned Python binding's shared-memory pointer shape."""
import wasmtime as wt
from wasmtime import _ffi as ffi

class SharedMemory(wt.SharedMemory):
    def _as_extern(self):
        # The pinned C union declares sharedmemory_t*, while the stock Python
        # method passes sharedmemory_t**. Keep the owning SharedMemory alive.
        return ffi.wasmtime_extern_t(ffi.WASMTIME_EXTERN_SHAREDMEMORY,ffi.wasmtime_extern_union(sharedmemory=self.ptr()))
