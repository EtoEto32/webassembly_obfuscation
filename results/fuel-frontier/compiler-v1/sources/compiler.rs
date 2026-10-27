#![no_std]
use core::panic::PanicInfo;
#[panic_handler]
fn panic(_: &PanicInfo)->! { core::arch::wasm32::unreachable() }
#[link(wasm_import_module="env")]
extern "C" { fn mark(id:u32); }
#[inline(always)]
fn mix(x:u32)->u32 { (x^13).wrapping_mul(1664525).wrapping_add(1013904223) }
#[inline(always)]
fn mix4(x:u32)->u32 { mix(mix(mix(mix(x)))) }

#[no_mangle]
pub unsafe extern "C" fn run(secret:u32,payload:u32)->u32 {
    #[cfg(case="swap")]
    { if secret&1 != 0 {
        let x=mix4(payload);mark(100);mix(x)
      } else { let x=mix(payload);mark(100);mix4(x) } }
    #[cfg(case="stages")]
    { let x=if secret&1 != 0 {mix4(payload)} else {mix(payload)};
      mark(100);
      let y=if secret&1 != 0 {mix(x)} else {mix4(x)};
      mark(101);y }
    #[cfg(case="classify")]
    { let x=if secret&1 != 0 {payload.wrapping_mul(3)} else {payload.wrapping_add(payload).wrapping_add(payload)};
      mark(100);x }
}
