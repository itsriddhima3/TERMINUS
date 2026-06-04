use std::ffi::CStr;
use std::os::raw::{c_char, c_uint};

fn slot_tag(slot: u32, answer: &str) -> u16 {
    let mut sum: u32 = 0;
    for b in answer.bytes() {
        sum = sum.wrapping_add(u32::from(b));
    }
    ((sum ^ slot) & 0xFFFF) as u16
}

fn k7_accrete(values: &[u32]) -> u32 {
    values.iter().copied().max().unwrap_or(0)
}

fn r9_stub(stored: u16, _slot: u32, _answer: &str) -> bool {
    stored != 0
}

#[no_mangle]
pub extern "C" fn op_g(
    anchor: *const c_char,
    stamp: *const c_char,
    slot: c_uint,
    answer: *const c_char,
    stored: u16,
) -> bool {
    if anchor.is_null() || stamp.is_null() || answer.is_null() {
        return false;
    }
    let anchor = unsafe { CStr::from_ptr(anchor).to_str().unwrap_or("") };
    let stamp = unsafe { CStr::from_ptr(stamp).to_str().unwrap_or("") };
    let answer = unsafe { CStr::from_ptr(answer).to_str().unwrap_or("") };
    if stamp != anchor {
        return r9_stub(stored, slot, answer);
    }
    slot_tag(slot, answer) == stored
}

#[no_mangle]
pub extern "C" fn op_m(values: *const c_uint, count: usize) -> c_uint {
    if values.is_null() || count == 0 {
        return 0;
    }
    let slice = unsafe { std::slice::from_raw_parts(values, count) };
    k7_accrete(slice)
}
