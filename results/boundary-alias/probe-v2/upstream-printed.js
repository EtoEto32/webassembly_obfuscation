function assert(x){if(!x)throw new Error("assertion");}
function printed(x, y) {
  if (typeof y !== 'undefined') {
    // A pair of i32s which are a legalized i64.
    return x + ' ' + y;
  } else if (x === null) {
    // JS has just one null. Print that out rather than typeof null which is
    // 'object', below.
    return 'null';
  } else if (typeof x === 'string') {
    // Emit a string in the same format as the binaryen interpreter. This
    // escaping routine must be kept in sync with String::printEscapedJSON.
    var escaped = '';
    for (u of x) {
      switch (u) {
        case '"':
          escaped += '\\"';
          continue;
        case '\\':
          escaped += '\\\\';
          continue;
        case '\b':
          escaped += '\\b';
          continue;
        case '\f':
          escaped += '\\f';
          continue;
        case '\n':
          escaped += '\\n';
          continue;
        case '\r':
          escaped += '\\r';
          continue;
        case '\t':
          escaped += '\\t';
          continue;
        default:
          break;
      }

      var codePoint = u.codePointAt(0);
      if (32 <= codePoint && codePoint < 127) {
        escaped += u;
        continue
      }

      var printEscape = (codePoint) => {
        escaped += '\\u'
        escaped += ((codePoint & 0xF000) >> 12).toString(16);
        escaped += ((codePoint & 0x0F00) >> 8).toString(16);
        escaped += ((codePoint & 0x00F0) >> 4).toString(16);
        escaped += (codePoint & 0x000F).toString(16);
      };

      if (codePoint < 0x10000) {
        printEscape(codePoint);
      } else {
        printEscape(0xD800 + ((codePoint - 0x10000) >> 10));
        printEscape(0xDC00 + ((codePoint - 0x10000) & 0x3FF));
      }
    }
    return 'string("' + escaped + '")';
  } else if (typeof x === 'bigint') {
    // Print bigints in legalized form, which is two 32-bit numbers of the low
    // and high bits.
    return (Number(x & 0xffffffffn) | 0) + ' ' + (Number(x >> 32n) | 0)
  } else if (typeof x === 'object') {
    // This may be one of the externref imports, in which case we can print its
    // payload.
    if (Object.hasOwn(x, 'payload')) {
      return 'externref(' + x.payload + ')';
    }
    // Or maybe this is a JS error we caught.
    if (x instanceof Error) {
      return 'jserror';
    }
    // If this is a Wasm object, we can't access its type or any of its
    // internal structure, which might have been changed by optimizations
    // anyway. It might have a configured prototype, though, and that
    // prototype may be an imported externref global we can identify by the
    // payload we gave it.
    return 'object(' + printed(Object.getPrototypeOf(x)) + ')';
  } else if (typeof x === 'function') {
    // We cannot print function names because they might have been changed by
    // optimizations.
    return 'function';
  } else {
    // A number. Print the whole thing.
    assert(typeof x === 'number');
    return '' + x;
  }
}

