#![no_std]
// Self-authored coverage fixtures, not third-party application benchmarks.
// Host arguments are bounded; every pointer operation stays inside BUFFER.
use core::{panic::PanicInfo, ptr};
#[panic_handler]
fn panic(_: &PanicInfo) -> ! { core::arch::wasm32::unreachable() }
static mut BUFFER: [u8; 8192] = [0; 8192];
fn base() -> *mut u8 { ptr::addr_of_mut!(BUFFER).cast() }
#[no_mangle]
pub extern "C" fn buffer_ptr() -> *mut u8 { base() }
#[link(wasm_import_module = "host")]
extern "C" { fn before(); }
#[no_mangle]
pub extern "C" fn drive() { unsafe { before() } }
#[inline(never)]
unsafe fn helper(p: *mut u8, v: u32) { ptr::write_volatile(p.add(4), v as u8); }

#[no_mangle]
#[allow(unused_variables)]
pub unsafe extern "C" fn callback(index: u32, value: u32, length: u32) {
    let p = base();
    #[cfg(case = "fixed")]
    { ptr::write_volatile(p.add(16), value as u8); }
    #[cfg(case = "indexed")]
    { ptr::write_volatile(p.add((index & 4095) as usize), value as u8); }
    #[cfg(case = "branch")]
    { if length & 1 == 0 { ptr::write_volatile(p.add(24), value as u8); }
      else { ptr::write_volatile(p.add((index & 4095) as usize), value as u8); } }
    #[cfg(case = "metadata")]
    { let x = ptr::read_volatile(p.add((index & 4095) as usize));
      ptr::write_volatile(p.add(4096), x.wrapping_add(value as u8)); }
    #[cfg(case = "loop")]
    { for i in 0..(length & 255) {
        let q = p.add(((index & 2047) + i) as usize);
        let v = ptr::read_volatile(q);
        ptr::write_volatile(q, v.wrapping_add(value as u8));
      } }
    #[cfg(case = "copy")]
    { ptr::copy(p.add(4096), p.add((index & 2047) as usize), (length & 255) as usize); }
    #[cfg(case = "fill")]
    { ptr::write_bytes(p.add((index & 2047) as usize), value as u8, (length & 255) as usize); }
    #[cfg(case = "helper")]
    { helper(p.add((index & 4095) as usize), value); }
}
