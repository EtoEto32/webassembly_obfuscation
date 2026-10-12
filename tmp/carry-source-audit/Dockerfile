FROM ubuntu:24.04
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends g++ cmake ninja-build git ca-certificates
COPY source/CoBRA-af44b8ad7c8ec548d431463475e93b0118e77a29 /src
RUN cmake -S /src/dependencies -B /deps -G Ninja -DCMAKE_BUILD_TYPE=Release -DCOBRA_BUILD_LLVM_PASS=OFF -DCOBRA_BUILD_TESTS=OFF -DCOBRA_ENABLE_Z3=OFF
RUN cmake --build /deps --parallel 2
RUN cmake -S /src -B /build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH=/deps/install -DCOBRA_BUILD_LLVM_PASS=OFF -DCOBRA_BUILD_TESTS=OFF
RUN cmake --build /build --parallel 2
ENTRYPOINT ["/build/tools/cobra-cli/cobra-cli"]
