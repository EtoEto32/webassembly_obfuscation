#![no_std]
use core::panic::PanicInfo;
#[panic_handler]
fn panic(_: &PanicInfo)->! { core::arch::wasm32::unreachable() }
#[link(wasm_import_module="env")]
extern "C" { fn mark(id:u32,released_value:u32); }
#[inline(always)]
fn mix(x:u32)->u32 { (x^13).wrapping_mul(1664525).wrapping_add(1013904223) }
#[inline(always)]
fn four(x:u32)->u32 { mix(mix(mix(mix(x)))) }
#[inline(always)]
fn twelve(x:u32)->u32 { four(four(four(x))) }
#[no_mangle]
pub unsafe extern "C" fn run(secret:u32,payload:u32)->u32 {
    let final_value=if secret&1 != 0 {
        let x=twelve(payload);mark(100,x>>28);mix(x)
    } else {
        let x=mix(payload);mark(100,x>>28);twelve(x)
    };
    final_value>>24
}
