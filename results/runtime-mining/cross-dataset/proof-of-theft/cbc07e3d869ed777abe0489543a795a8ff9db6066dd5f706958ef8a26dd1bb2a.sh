rm -rf *-before*
make clean

for file in $(ls *.c); do 
    cat template $file > "${file}-before.c"
done

for file in $(ls *-before.c); do 
    echo $file 
    if [ "$file" = "cryptonight.c-before.c" ] || [ "$file" = "main.c-before.c" ]; then 
        tigress -I $EMSDKPATH --Compiler=emcc --Environment=wasm:Linux:Emcc:4.6 \
        --out="${file}-obf.c" $file
    else
        tigress -I $EMSDKPATH --Compiler=emcc --Environment=wasm:Linux:Emcc:4.6 \
        --Transform=Split --Functions=* \
        --out="${file}-obf.c" $file
    fi
done

emcc -g3 -s LINKABLE=1 -s EXPORT_ALL=1 -O3 -s NO_FILESYSTEM=1 -s LEGACY_VM_SUPPORT -s 'EXTRA_EXPORTED_RUNTIME_METHODS=["ccall", "cwrap"]' -s TOTAL_MEMORY=67108864  -s WASM=1 -s EXPORTED_FUNCTIONS="['_hash_cn']"  --shell-file html_template/shell_minimal.html -Wl,-allow-multiple-definition *-obf.c -o cn.html

# for file in $(ls *.c); do
#     ~/Downloads/tigress-4.0.10-full/tigress/4.0.10/Linux-armv8/cilly --merge -c $file -o "${file}.o"
# done

#-g3 -s LINKABLE=1 -s EXPORT_ALL=1