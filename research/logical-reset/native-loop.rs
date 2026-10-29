//! Small C-API timing loop. Only fixed (i32)->i32 research functions are accepted.
//! The Python driver checks Wasmtime ABI sizes/offsets before invoking this code.
use std::{ffi::c_void, ptr, time::Instant};
type P = *mut c_void;
#[repr(C, align(16))]
struct Buffer([u8; 128]);
#[no_mangle]
pub unsafe extern "C" fn measure(api: *const usize, engine: P, module: P,
    repeats: usize, n: i32, reuse: bool, expected: i32) -> f64 {
    let a = std::slice::from_raw_parts(api, 9);
    let new_store: unsafe extern "C" fn(P,P,P)->P = std::mem::transmute(a[0]);
    let context: unsafe extern "C" fn(P)->P = std::mem::transmute(a[1]);
    let delete_store: unsafe extern "C" fn(P) = std::mem::transmute(a[2]);
    let instantiate: unsafe extern "C" fn(P,P,P,usize,P,*mut P)->P = std::mem::transmute(a[3]);
    let export: unsafe extern "C" fn(P,P,*const u8,usize,P)->bool = std::mem::transmute(a[4]);
    let call: unsafe extern "C" fn(P,P,P,usize,P,usize,*mut P)->P = std::mem::transmute(a[5]);
    let delete_error: unsafe extern "C" fn(P) = std::mem::transmute(a[6]);
    let delete_trap: unsafe extern "C" fn(P) = std::mem::transmute(a[7]);
    let delete_extern: unsafe extern "C" fn(P) = std::mem::transmute(a[8]);
    let mut store = ptr::null_mut();
    let mut ctx = ptr::null_mut();
    let mut instance = Buffer([0;128]);
    let mut ext = Buffer([0;128]);
    let mut arg = Buffer([0;128]);
    let mut result = Buffer([0;128]);
    let mut elapsed = 0.;
    // Reuse gets one instance outside timing; fresh creates and destroys each request.
    let init = |store: &mut P, ctx: &mut P, instance: &mut Buffer, ext: &mut Buffer| -> i32 {
        *store = new_store(engine,ptr::null_mut(),ptr::null_mut());
        if store.is_null() { return -1; }
        *ctx = context(*store);
        let mut trap = ptr::null_mut();
        let err = instantiate(*ctx,module,ptr::null_mut(),0,instance.0.as_mut_ptr() as P,&mut trap);
        if !err.is_null() { delete_error(err); return -2; }
        if !trap.is_null() { delete_trap(trap); return -3; }
        if !export(*ctx,instance.0.as_mut_ptr() as P,b"__request".as_ptr(),9,ext.0.as_mut_ptr() as P) { return -4; }
        if ext.0[0] != 0 { return -5; }
        0
    };
    if reuse {
        let status = init(&mut store,&mut ctx,&mut instance,&mut ext);
        if status != 0 { if !store.is_null() { delete_store(store); } return status as f64; }
    }
    let start = Instant::now();
    let mut status = 0;
    for _ in 0..repeats {
        if !reuse {
            status = init(&mut store,&mut ctx,&mut instance,&mut ext);
            if status != 0 { break; }
        }
        // wasmtime_val_t: kind at 0, numeric union at 8; extern func union at 8.
        arg.0[8..12].copy_from_slice(&n.to_ne_bytes());
        let mut trap = ptr::null_mut();
        let err = call(ctx,ext.0.as_mut_ptr().add(8) as P,arg.0.as_mut_ptr() as P,1,
                       result.0.as_mut_ptr() as P,1,&mut trap);
        if !err.is_null() { delete_error(err); status = -6; break; }
        if !trap.is_null() { delete_trap(trap); status = -7; break; }
        let observed = i32::from_ne_bytes(result.0[8..12].try_into().unwrap());
        if result.0[0] != 0 || observed != expected { status = -8; break; }
        if !reuse { delete_extern(ext.0.as_mut_ptr() as P); delete_store(store); store = ptr::null_mut(); }
    }
    if status == 0 { elapsed = start.elapsed().as_secs_f64()*1e9/(repeats as f64); }
    if !store.is_null() { delete_extern(ext.0.as_mut_ptr() as P); delete_store(store); }
    if status == 0 { elapsed } else { status as f64 }
}
